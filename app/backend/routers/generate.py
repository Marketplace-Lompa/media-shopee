"""
Router: POST /generate
Pipeline com suporte a jobs assíncronos (submit + polling).
"""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Callable, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agent import run_agent
from history import add_entry as history_add, purge_oldest as history_purge
from config import VALID_ASPECT_RATIOS, VALID_N_IMAGES, VALID_RESOLUTIONS
from generator import generate_images
from grounding_policy import compute_grounding_triage, normalize_grounding_strategy
from guided_mode import guided_force_grounding_floor, guided_summary, normalize_guided_brief
from job_manager import complete_job, create_job, fail_job, get_job, list_jobs, start_job, update_stage
from models import GenerateResponse, GeneratedImage
from pipeline_effectiveness import (
    assess_generated_image,
    build_reference_pack,
    build_repair_prompt,
    classify_visual_context,
    compute_quality_contract,
    decide_grounding_mode,
    enrich_quality_with_generation,
    log_effectiveness_event,
    select_diversity_target,
)

router = APIRouter(prefix="/generate", tags=["generate"])


def _run_generate_pipeline(
    *,
    prompt: Optional[str],
    aspect_ratio: str,
    resolution: str,
    n_images: int,
    grounding_strategy: Optional[str],
    use_grounding: bool,
    guided_brief: Optional[str],
    uploaded_bytes: List[bytes],
    on_stage: Optional[Callable[[str, dict], None]] = None,
) -> GenerateResponse:
    def emit(stage: str, data: dict) -> None:
        if on_stage:
            try:
                on_stage(stage, data)
            except Exception:
                pass

    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(f"aspect_ratio inválido. Use: {VALID_ASPECT_RATIOS}")
    if resolution not in VALID_RESOLUTIONS:
        raise ValueError(f"resolution inválida. Use: {VALID_RESOLUTIONS}")
    if n_images not in VALID_N_IMAGES:
        raise ValueError(f"n_images inválido. Use: {VALID_N_IMAGES}")

    pool_context = "POOL_RUNTIME_DISABLED"
    pipeline_mode = "reference_mode" if uploaded_bytes else "text_mode"
    strategy = normalize_grounding_strategy(grounding_strategy, use_grounding)
    normalized_guided = normalize_guided_brief(guided_brief)

    reference_pack = build_reference_pack(uploaded_bytes)
    analysis_images = reference_pack.get("analysis_images", [])
    generation_images = reference_pack.get("generation_images", [])
    reference_pack_stats = reference_pack.get("stats", {})
    diversity_target = select_diversity_target(seed_hint=prompt or "", guided_brief=normalized_guided)

    emit(
        "mode_selected",
        {
            "message": "Modo com referência ativado" if uploaded_bytes else "Modo sem referência ativado",
            "pipeline_mode": pipeline_mode,
            "reference_pack_stats": reference_pack_stats,
            "model_profile_id": diversity_target.get("profile_id"),
        },
    )
    emit(
        "analyzing",
        {
            "message": (
                f"Agente analisando {len(analysis_images)} imagem(ns) curada(s)…"
                if uploaded_bytes
                else "Agente criando prompt…"
            ),
            "n_uploads": len(uploaded_bytes),
        },
    )

    triage: dict[str, Any] = {}
    classifier_summary: dict[str, Any] = {}
    decision: dict[str, Any] = {"grounding_mode": "off", "trigger_reason": "unknown", "reason_codes": []}
    applied_mode = "off"

    try:
        baseline_result = run_agent(
            user_prompt=prompt,
            uploaded_images=analysis_images if analysis_images else None,
            pool_context=pool_context,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            use_grounding=False,
            diversity_target=diversity_target,
            guided_brief=normalized_guided,
        )
        baseline_structural = baseline_result.get("structural_contract") if isinstance(
            baseline_result.get("structural_contract"), dict
        ) else None
        triage = compute_grounding_triage(
            user_prompt=prompt,
            image_analysis=baseline_result.get("image_analysis", ""),
            has_images=bool(uploaded_bytes),
        )
        classifier_summary = classify_visual_context(
            user_prompt=prompt,
            image_analysis=baseline_result.get("image_analysis", ""),
            has_images=bool(uploaded_bytes),
            reference_pack_stats=reference_pack_stats,
        )
        decision = decide_grounding_mode(
            strategy=strategy,
            has_images=bool(uploaded_bytes),
            triage=triage,
            classifier_summary=classifier_summary,
        )
        applied_mode = decision.get("grounding_mode", "off")

        if strategy == "auto" and applied_mode == "off" and guided_force_grounding_floor(
            normalized_guided, bool(uploaded_bytes)
        ):
            applied_mode = "lexical"
            decision["trigger_reason"] = "guided_floor_forced_grounding"
            decision["reason_codes"] = sorted(
                set((decision.get("reason_codes", []) or []) + ["guided_floor_forced_grounding"])
            )

        emit(
            "triage_done",
            {
                "message": "Triage de grounding concluído",
                "requested_strategy": strategy,
                "pipeline_mode": triage.get("pipeline_mode", pipeline_mode),
                "grounding_mode": applied_mode,
                "grounding_score": triage.get("grounding_score"),
                "garment_hypothesis": triage.get("garment_hypothesis"),
                "complexity_score": classifier_summary.get("complexity_score", triage.get("complexity_score")),
                "hint_confidence": classifier_summary.get("confidence", triage.get("hint_confidence")),
                "trigger_reason": decision.get("trigger_reason", triage.get("trigger_reason")),
                "classifier_summary": classifier_summary,
                "reason_codes": decision.get("reason_codes", []),
            },
        )

        if applied_mode == "off":
            agent_result = baseline_result
        else:
            emit(
                "researching",
                {
                    "message": "Pesquisando referências na web…",
                    "grounding_mode": applied_mode,
                },
            )
            try:
                agent_result = run_agent(
                    user_prompt=prompt,
                    uploaded_images=analysis_images if analysis_images else None,
                    pool_context=pool_context,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    use_grounding=True,
                    grounding_mode=applied_mode,
                    grounding_context_hint=triage.get("garment_hypothesis"),
                    diversity_target=diversity_target,
                    guided_brief=normalized_guided,
                    structural_contract_hint=baseline_structural,
                )
            except Exception:
                agent_result = baseline_result
                applied_mode = "off"
    except Exception as e:
        raise RuntimeError(f"Erro no Prompt Agent: {e}") from e

    grounded_images = list(agent_result.pop("_grounded_images", []) or [])
    pipeline_mode = agent_result.get("pipeline_mode", pipeline_mode)
    optimized_prompt = agent_result.get("prompt", "")
    thinking_level = agent_result.get("thinking_level", "MINIMAL")
    thinking_reason = agent_result.get("thinking_reason", "")
    shot_type = agent_result.get("shot_type", "auto")
    realism_level = agent_result.get("realism_level", 2)
    guided_sum = agent_result.get("guided_summary") or guided_summary(normalized_guided, shot_type)

    grounding_sources = (agent_result.get("grounding", {}) or {}).get("sources", []) or []
    grounded_images_count = int((agent_result.get("grounding", {}) or {}).get("grounded_images_count", 0) or 0)
    grounding_effective = bool(len(grounding_sources) >= 2 or grounded_images_count >= 1)

    grounding_info = {
        **(agent_result.get("grounding", {}) or {}),
        "requested_strategy": strategy,
        "applied_mode": applied_mode,
        "pipeline_mode": triage.get("pipeline_mode", pipeline_mode),
        "grounding_score": triage.get("grounding_score"),
        "complexity_score": classifier_summary.get("complexity_score", triage.get("complexity_score")),
        "garment_hypothesis": triage.get("garment_hypothesis"),
        "garment_hint": triage.get("garment_hint"),
        "hint_confidence": classifier_summary.get("confidence", triage.get("hint_confidence")),
        "trigger_reason": decision.get("trigger_reason", triage.get("trigger_reason")),
        "attempted": applied_mode != "off",
        "effective": grounding_effective,
    }

    quality_contract = compute_quality_contract(
        prompt=optimized_prompt,
        pipeline_mode=pipeline_mode,
        classifier_summary=classifier_summary,
        grounding_info=grounding_info,
        diversity_target=diversity_target,
    )

    emit(
        "prompt_ready",
        {
            "message": "Prompt criado pelo agente",
            "prompt": optimized_prompt,
            "image_analysis": agent_result.get("image_analysis", ""),
            "thinking_level": thinking_level,
            "shot_type": shot_type,
            "pipeline_mode": pipeline_mode,
            "grounding": grounding_info,
            "quality_contract": quality_contract,
            "classifier_summary": classifier_summary,
            "reference_pack_stats": reference_pack_stats,
            "guided_applied": bool(guided_sum),
            "guided_summary": guided_sum,
        },
    )

    session_id = str(uuid.uuid4())[:8]
    raw_images: List[dict] = []
    failed_indices: List[int] = []
    image_assessments: List[dict] = []
    repair_applied = False
    reason_codes = set((decision.get("reason_codes", []) or []) + (quality_contract.get("reason_codes", []) or []))

    for i in range(n_images):
        emit(
            "generating",
            {
                "message": f"Gerando imagem {i+1}/{n_images} via Nano…",
                "current": i + 1,
                "total": n_images,
            },
        )
        ok = False
        last_error: Optional[Exception] = None
        selected_batch = None
        selected_assessment = None

        for _attempt in range(2):
            try:
                batch = generate_images(
                    prompt=optimized_prompt,
                    thinking_level=thinking_level,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    n_images=1,
                    uploaded_images=generation_images if generation_images else None,
                    grounded_images=grounded_images if grounded_images else None,
                    session_id=session_id,
                    start_index=i + 1,
                )
                selected_batch = batch
                selected_assessment = assess_generated_image(batch[0]["path"], optimized_prompt, classifier_summary)
                ok = True
                break
            except Exception as e:
                last_error = e

        if not ok or not selected_batch or not selected_assessment:
            failed_indices.append(i + 1)
            print(f"[GENERATE] ⚠️ Failed image {i+1}/{n_images}: {last_error}")
            continue

        best_batch = selected_batch
        best_assessment = selected_assessment

        if not selected_assessment.get("pass", False):
            repair_prompt = build_repair_prompt(
                optimized_prompt,
                classifier_summary,
                list(reason_codes.union(set(selected_assessment.get("reason_codes", []) or []))),
            )
            img_path = Path(selected_batch[0]["path"])
            first_bytes = img_path.read_bytes() if img_path.exists() else b""
            first_score = float(selected_assessment.get("candidate_score", 0.0) or 0.0)
            try:
                repaired_batch = generate_images(
                    prompt=repair_prompt,
                    thinking_level=thinking_level,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    n_images=1,
                    uploaded_images=generation_images if generation_images else None,
                    grounded_images=grounded_images if grounded_images else None,
                    session_id=session_id,
                    start_index=i + 1,
                )
                repaired_assessment = assess_generated_image(repaired_batch[0]["path"], repair_prompt, classifier_summary)
                repaired_score = float(repaired_assessment.get("candidate_score", 0.0) or 0.0)
                if repaired_score >= first_score:
                    best_batch = repaired_batch
                    best_assessment = repaired_assessment
                    repair_applied = True
                elif first_bytes:
                    img_path.write_bytes(first_bytes)
            except Exception as repair_err:
                print(f"[GENERATE] ⚠️ repair failed for image {i+1}: {repair_err}")
                if first_bytes:
                    img_path.write_bytes(first_bytes)

        raw_images.extend(best_batch)
        image_assessments.append(best_assessment)
        reason_codes.update(best_assessment.get("reason_codes", []) or [])

    if not raw_images:
        raise RuntimeError("Erro no Image Generator: nenhuma imagem foi gerada.")

    quality_contract = enrich_quality_with_generation(quality_contract, image_assessments)
    reason_codes.update(quality_contract.get("reason_codes", []) or [])

    # ── Persistir no histórico ────────────────────────────────────
    grounding_eff = grounding_info.get("effective", False) if isinstance(grounding_info, dict) else False
    for img in raw_images:
        try:
            history_add(
                session_id=session_id,
                filename=img["filename"],
                url=img["url"],
                prompt=optimized_prompt,
                thinking_level=thinking_level,
                shot_type=shot_type,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                grounding_effective=grounding_eff,
            )
        except Exception as hist_err:
            print(f"[HISTORY] ⚠️ Falha ao persistir: {hist_err}")

    try:
        history_purge()
    except Exception as purge_err:
        print(f"[CLEANUP] ⚠️ Falha no purge: {purge_err}")

    log_effectiveness_event(
        {
            "session_id": session_id,
            "category": quality_contract.get("category", "general"),
            "global_score": quality_contract.get("global_score", 0.0),
            "reason_codes": sorted(reason_codes),
            "repair_applied": repair_applied,
            "pipeline_mode": pipeline_mode,
        }
    )

    response = GenerateResponse(
        session_id=session_id,
        optimized_prompt=optimized_prompt,
        pipeline_mode=pipeline_mode,
        thinking_level=thinking_level,
        thinking_reason=thinking_reason,
        shot_type=shot_type,
        realism_level=realism_level,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        images=[GeneratedImage(**img) for img in raw_images],
        failed_indices=failed_indices or None,
        pool_refs_used=0,
        grounding=grounding_info,
        quality_contract=quality_contract,
        fidelity_score=quality_contract.get("fidelity_score"),
        commercial_score=quality_contract.get("commercial_score"),
        diversity_score=quality_contract.get("diversity_score"),
        grounding_reliability=quality_contract.get("grounding_reliability"),
        reason_codes=sorted(reason_codes),
        repair_applied=repair_applied,
        reference_pack_stats=reference_pack_stats,
        classifier_summary=classifier_summary,
        guided_applied=bool(guided_sum),
        guided_summary=guided_sum,
    )

    emit(
        "done_partial" if failed_indices else "done",
        {"data": response.model_dump()},
    )
    return response


@router.post("", response_model=GenerateResponse)
async def generate(
    prompt: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default="1:1"),
    resolution: str = Form(default="1K"),
    n_images: int = Form(default=1),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    guided_brief: Optional[str] = Form(default=None),
    images: List[UploadFile] = File(default=[]),
):
    uploaded_bytes = [await img.read() for img in images[:14]]
    try:
        return await asyncio.to_thread(
            _run_generate_pipeline,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=n_images,
            grounding_strategy=grounding_strategy,
            use_grounding=use_grounding,
            guided_brief=guided_brief,
            uploaded_bytes=uploaded_bytes,
            on_stage=None,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.post("/async")
async def generate_async(
    prompt: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default="1:1"),
    resolution: str = Form(default="1K"),
    n_images: int = Form(default=1),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    guided_brief: Optional[str] = Form(default=None),
    images: List[UploadFile] = File(default=[]),
):
    uploaded_bytes = [await img.read() for img in images[:14]]
    job_id = create_job(meta={"n_images": n_images, "has_images": bool(uploaded_bytes)})

    def _worker() -> None:
        def _stage_cb(stage: str, data: dict) -> None:
            update_stage(job_id, stage, data)

        try:
            response = _run_generate_pipeline(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                n_images=n_images,
                grounding_strategy=grounding_strategy,
                use_grounding=use_grounding,
                guided_brief=guided_brief,
                uploaded_bytes=uploaded_bytes,
                on_stage=_stage_cb,
            )
            stage = "done_partial" if response.failed_indices else "done"
            complete_job(job_id, response.model_dump(), stage=stage)
        except Exception as e:
            fail_job(job_id, str(e))

    start_job(job_id, _worker)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
async def get_generate_job(job_id: str):
    return get_job(job_id)


@router.get("/jobs")
async def list_generate_jobs(limit: int = 20):
    return list_jobs(limit=limit)
