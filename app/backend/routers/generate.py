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
from agent_runtime.pipeline_v2 import run_pipeline_v2
from agent_runtime.pipeline_v2_support import (
    build_v2_generate_response,
    normalize_v2_options,
    persist_v2_history,
    should_use_v2,
)
from config import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_N_IMAGES,
    DEFAULT_RESOLUTION,
    OUTPUTS_DIR,
    VALID_N_IMAGES,
)
from generator import generate_images
from grounding_policy import compute_grounding_triage, normalize_grounding_strategy
from history import add_entry as history_add, purge_oldest as history_purge
from guided_mode import guided_force_grounding_floor, guided_summary, normalize_guided_brief
from job_manager import complete_job, create_job, fail_job, get_job, list_jobs, start_job, update_stage
from models import GenerateResponse, GeneratedImage
from pipeline_effectiveness import (
    assess_generated_image,
    build_reference_pack,
    classify_visual_context,
    compute_quality_contract,
    decide_grounding_mode,
    enrich_quality_with_generation,
    log_effectiveness_event,
    select_diversity_target,
)
from request_validation import validate_generation_params

router = APIRouter(prefix="/generate", tags=["generate"])


def _is_strict_reference_mode(guided_brief: Optional[dict], uploaded_bytes: List[bytes]) -> bool:
    if not uploaded_bytes or not guided_brief:
        return False
    return str(guided_brief.get("fidelity_mode", "balanceada")).strip().lower() == "estrita"


def _build_strict_reference_prompt(
    user_prompt: Optional[str],
    classifier_summary: dict[str, Any],
    guided_brief: Optional[dict],
    structural_contract: Optional[dict[str, Any]] = None,
) -> str:
    scene_cfg = (guided_brief or {}).get("scene", {}) or {}
    pose_cfg = (guided_brief or {}).get("pose", {}) or {}
    garment_cfg = (guided_brief or {}).get("garment", {}) or {}

    scene_type = str(scene_cfg.get("type", "interno")).strip().lower()
    pose_style = str(pose_cfg.get("style", "tradicional")).strip().lower()
    set_mode = str(garment_cfg.get("set_mode", "unica")).strip().lower()
    category = str(classifier_summary.get("garment_category", "general")).strip().lower()

    scene_clause = (
        "clean premium indoor composition"
        if scene_type != "externo"
        else "clean premium outdoor composition"
    )
    pose_clause = (
        "natural movement pose with full garment visibility"
        if pose_style == "criativa"
        else "standing pose"
    )
    garment_lock = (
        "Preserve exact garment geometry, drape, sleeve architecture, hem behavior, stripe scale, and stitch pattern."
        if category in {"complex_knit", "outerwear"}
        else "Preserve exact garment geometry, texture continuity, and construction details."
    )
    structural_clause = ""
    if structural_contract and structural_contract.get("enabled"):
        subtype = structural_contract.get("garment_subtype", "garment")
        front = structural_contract.get("front_opening", "unknown")
        hem = structural_contract.get("hem_shape", "unknown")
        volume = structural_contract.get("silhouette_volume", "unknown")
        sleeve = structural_contract.get("sleeve_type", "unknown")
        structural_clause = (
            f"Garment identity anchor: {subtype}, {volume} silhouette, {front} front opening, "
            f"{hem} hem behavior, {sleeve} sleeve architecture."
        )

    clauses = [
        "Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment.",
        "Direct eye contact, realistic skin texture, natural body proportions,",
        pose_clause + ",",
        "full garment clearly visible,",
        scene_clause + ",",
        "soft natural daylight.",
        garment_lock,
        structural_clause,
        "Catalog-ready minimal styling with the garment as the hero piece.",
        "Keep accessories subtle and secondary to the garment.",
    ]
    if set_mode != "conjunto":
        clauses.append(
            "Build new styling independent from the reference person's lower-body look, footwear, and props unless explicitly requested."
        )

    from agent_runtime.normalize_user_intent import normalize_user_intent
    raw_user_prompt = (user_prompt or "").strip()
    if raw_user_prompt:
        intent = normalize_user_intent(raw_user_prompt)
        clauses.append(f"Additional commercial direction: {intent['normalized']}")

    return " ".join(part.strip() for part in clauses if part and part.strip())


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

    normalized_guided = normalize_guided_brief(guided_brief)
    strict_reference_mode = _is_strict_reference_mode(normalized_guided, uploaded_bytes)
    validate_generation_params(
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        n_images=n_images,
        valid_n_images=VALID_N_IMAGES,
    )

    pool_context = ""
    pipeline_mode = "reference_mode_strict" if strict_reference_mode else ("reference_mode" if uploaded_bytes else "text_mode")
    strategy = "off" if strict_reference_mode else normalize_grounding_strategy(grounding_strategy, use_grounding)

    reference_pack = build_reference_pack(uploaded_bytes)
    analysis_images = reference_pack.get("analysis_images", [])
    curated_images = (
        reference_pack.get("strict_generation_images", [])
        if strict_reference_mode
        else reference_pack.get("generation_images", [])
    )
    reference_pack_stats = reference_pack.get("stats", {})

    # ── Art Director: triagem visual ANTES da diversidade (R3) ──────────
    # A triagem extrai garment_aesthetic que alimenta select_diversity_target()
    unified_triage_result = None
    image_analysis_text = ""
    garment_aesthetic = None
    structural_contract_for_diversity = None
    structural_hint_for_nano = None  # string para role_prefix do Nano Banana
    if uploaded_bytes:
        from agent_runtime.triage import _infer_unified_vision_triage
        try:
            unified_triage_result = _infer_unified_vision_triage(analysis_images or curated_images, prompt)
            if unified_triage_result:
                image_analysis_text = unified_triage_result.get("image_analysis", "")
                garment_aesthetic = unified_triage_result.get("garment_aesthetic")
                structural_contract_for_diversity = unified_triage_result.get("structural_contract")
                # Construir hint textual para o Nano Banana preservar silhueta
                if structural_contract_for_diversity:
                    sc = structural_contract_for_diversity
                    parts_hint = [sc.get("garment_subtype", "")]
                    if sc.get("silhouette_volume"):
                        parts_hint.append(f"{sc['silhouette_volume']} silhouette")
                    if sc.get("sleeve_type") and sc.get("sleeve_type") != "set-in":
                        parts_hint.append(f"{sc['sleeve_type']} sleeves")
                    structural_hint_for_nano = ", ".join(p for p in parts_hint if p) or None
        except Exception as e:
            print(f"Erro na triagem visual unificada antecipada: {e}")

    # Diversidade garment-aware: usa estética da peça para casting inteligente
    diversity_target = (
        {}
        if strict_reference_mode
        else select_diversity_target(
            seed_hint=prompt or "",
            guided_brief=normalized_guided,
            garment_aesthetic=garment_aesthetic,
            structural_contract=structural_contract_for_diversity,
        )
    )

    emit(
        "mode_selected",
        {
            "message": (
                "Modo de fidelidade estrita ativado"
                if strict_reference_mode
                else ("Modo com referência ativado" if uploaded_bytes else "Modo sem referência ativado")
            ),
            "pipeline_mode": pipeline_mode,
            "reference_pack_stats": reference_pack_stats,
            "model_profile_id": diversity_target.get("profile_id"),
        },
    )
    emit(
        "analyzing",
        {
            "message": (
                f"Agente analisando {len(analysis_images or curated_images)} imagem(ns) curada(s)…"
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
    agent_result: dict[str, Any] = {}

    try:
        triage = compute_grounding_triage(
            user_prompt=prompt,
            image_analysis=image_analysis_text,
            has_images=bool(uploaded_bytes),
        )
        classifier_summary = classify_visual_context(
            user_prompt=prompt,
            image_analysis=image_analysis_text,
            has_images=bool(uploaded_bytes),
            reference_pack_stats=reference_pack_stats,
        )
        if strict_reference_mode:
            decision = {
                "grounding_mode": "off",
                "trigger_reason": "strict_reference_mode",
                "reason_codes": ["strict_reference_mode"],
            }
            applied_mode = "off"
        else:
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

        if applied_mode != "off":
            emit(
                "researching",
                {
                    "message": "Pesquisando referências na web…",
                    "grounding_mode": applied_mode,
                },
            )

        if strict_reference_mode:
            from agent_runtime.normalize_user_intent import normalize_user_intent

            optimized_prompt = _build_strict_reference_prompt(
                user_prompt=prompt,
                classifier_summary=classifier_summary,
                guided_brief=normalized_guided,
                structural_contract=structural_contract_for_diversity,
            )
            strict_user_intent = normalize_user_intent(prompt or "")
            strict_tags = set(strict_user_intent.get("intent_tags", []) or [])
            strict_tags.add("strict_reference")
            strict_user_intent["intent_tags"] = sorted(strict_tags)
            agent_result = {
                "pipeline_mode": pipeline_mode,
                "prompt": optimized_prompt,
                "thinking_level": "MINIMAL",
                "thinking_reason": "strict_reference_mode",
                "shot_type": "full",
                "realism_level": 2,
                "image_analysis": image_analysis_text,
                "grounding": {
                    "requested_strategy": "off",
                    "applied_mode": "off",
                    "attempted": False,
                    "effective": False,
                    "sources": [],
                    "grounded_images_count": 0,
                    "reason_codes": ["strict_reference_mode"],
                },
                "user_intent": strict_user_intent,
                "prompt_compiler_debug": {
                    "mode": "strict_reference_mode",
                    "source": "direct_template",
                    "used_reference_count": len(curated_images or []),
                },
            }
        else:
            try:
                agent_result = run_agent(
                    user_prompt=prompt,
                    uploaded_images=analysis_images or curated_images or None,
                    pool_context=pool_context,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    use_grounding=(applied_mode != "off"),
                    grounding_mode=applied_mode,
                    grounding_context_hint=triage.get("garment_hypothesis") if applied_mode != "off" else None,
                    diversity_target=diversity_target,
                    guided_brief=normalized_guided,
                    unified_vision_triage_result=unified_triage_result,
                )
            except Exception as e:
                if applied_mode != "off":
                    print(f"[GENERATE] Fallback: rodando agente sem grounding após erro: {e}")
                    applied_mode = "off"
                    agent_result = run_agent(
                        user_prompt=prompt,
                        uploaded_images=analysis_images or curated_images or None,
                        pool_context=pool_context,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        use_grounding=False,
                        diversity_target=diversity_target,
                        guided_brief=normalized_guided,
                        unified_vision_triage_result=unified_triage_result,
                    )
                else:
                    raise
    except Exception as e:
        raise RuntimeError(f"Erro no Prompt Agent: {e}") from e

    # ONDA 1.4: Em qualquer reference_mode (strict ou normal), grounded_images
    # do grounding research podem conflitar com as referências visuais reais.
    # Apenas text_mode se beneficia de imagens grounded.
    _skip_grounded = strict_reference_mode or pipeline_mode.startswith("reference_mode")
    grounded_images = [] if _skip_grounded else list(agent_result.pop("_grounded_images", []) or [])
    pipeline_mode = agent_result.get("pipeline_mode", pipeline_mode)
    optimized_prompt = agent_result.get("prompt", "")
    thinking_level = agent_result.get("thinking_level", "MINIMAL")
    thinking_reason = agent_result.get("thinking_reason", "")
    shot_type = agent_result.get("shot_type", "auto")
    realism_level = agent_result.get("realism_level", 2)
    guided_sum = agent_result.get("guided_summary") or guided_summary(normalized_guided, shot_type)

    grounding_sources = (agent_result.get("grounding", {}) or {}).get("sources", []) or []
    grounded_images_count = int((agent_result.get("grounding", {}) or {}).get("grounded_images_count", 0) or 0)
    grounding_effective = bool(len(grounding_sources) > 0 or grounded_images_count > 0)

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
            "user_intent": agent_result.get("user_intent"),
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
            "prompt_compiler_debug": agent_result.get("prompt_compiler_debug"),
        },
    )

    session_id = str(uuid.uuid4())[:8]

    # Persistir referências em disco (paridade com stream.py) para auditoria e reuso
    reference_urls: List[str] = []
    if curated_images:
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        for idx, img_bytes in enumerate(curated_images):
            ref_filename = f"ref_curated_{idx+1}.jpg"
            (session_dir / ref_filename).write_bytes(img_bytes)
            reference_urls.append(f"/outputs/{session_id}/{ref_filename}")

    raw_images: List[dict] = []
    failed_indices: List[int] = []
    image_assessments: List[dict] = []
    reason_codes = set(
        (decision.get("reason_codes", []) or []) + 
        (quality_contract.get("reason_codes", []) or []) +
        (grounding_info.get("reason_codes", []) or [])
    )

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
                    uploaded_images=curated_images if curated_images else None,
                    grounded_images=grounded_images if grounded_images else None,
                    session_id=session_id,
                    start_index=i + 1,
                    structural_hint=structural_hint_for_nano,
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

        raw_images.extend(best_batch)
        image_assessments.append(best_assessment)
        reason_codes.update(best_assessment.get("reason_codes", []) or [])

    if not raw_images:
        raise RuntimeError("Erro no Image Generator: nenhuma imagem foi gerada.")

    quality_contract = enrich_quality_with_generation(quality_contract, image_assessments)
    reason_codes.update(quality_contract.get("reason_codes", []) or [])

    # ── Persistir no histórico ────────────────────────────────────
    grounding_eff = grounding_info.get("effective", False) if isinstance(grounding_info, dict) else False
    _base_prompt = agent_result.get("base_prompt") or None
    _camera_and_realism = agent_result.get("camera_and_realism") or None
    _camera_profile = agent_result.get("camera_profile") or None
    _grounding_mode = grounding_info.get("applied_mode") or applied_mode or None
    _reason_codes = sorted(reason_codes) if reason_codes else []
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
                references=reference_urls,
                base_prompt=_base_prompt,
                camera_and_realism=_camera_and_realism,
                camera_profile=_camera_profile,
                grounding_mode=_grounding_mode,
                reason_codes=_reason_codes,
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
            "repair_applied": False,
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
        image_analysis=agent_result.get("image_analysis") or None,
        grounding=grounding_info,
        quality_contract=quality_contract,
        fidelity_score=quality_contract.get("fidelity_score"),
        commercial_score=quality_contract.get("commercial_score"),
        diversity_score=quality_contract.get("diversity_score"),
        grounding_reliability=quality_contract.get("grounding_reliability"),
        reason_codes=sorted(reason_codes),
        repair_applied=False,
        reference_pack_stats=reference_pack_stats,
        classifier_summary=classifier_summary,
        guided_applied=bool(guided_sum),
        guided_summary=guided_sum,
        prompt_compiler_debug=agent_result.get("prompt_compiler_debug"),
        user_intent=agent_result.get("user_intent"),
    )

    emit(
        "done_partial" if failed_indices else "done",
        {"data": response.model_dump()},
    )
    return response


@router.post("", response_model=GenerateResponse)
async def generate(
    prompt: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
    resolution: str = Form(default=DEFAULT_RESOLUTION),
    n_images: int = Form(default=DEFAULT_N_IMAGES),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    guided_brief: Optional[str] = Form(default=None),
    preset: Optional[str] = Form(default=None),
    scene_preference: str = Form(default="auto_br"),
    fidelity_mode: str = Form(default="balanceada"),
    pose_flex_mode: str = Form(default="auto"),
    images: List[UploadFile] = File(default=[]),
):
    try:
        validate_generation_params(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=n_images,
            valid_n_images=VALID_N_IMAGES,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    limited_images = images[:14]
    uploaded_bytes = [await img.read() for img in limited_images]
    uploaded_filenames = [str(img.filename or "").strip() for img in limited_images]
    use_v2 = should_use_v2(preset, uploaded_bytes)
    try:
        if use_v2:
            normalized_preset, normalized_scene_preference, normalized_fidelity_mode, normalized_pose_flex_mode = normalize_v2_options(
                preset=preset,
                scene_preference=scene_preference,
                fidelity_mode=fidelity_mode,
                pose_flex_mode=pose_flex_mode,
            )
            return await asyncio.to_thread(
                _run_v2_pipeline_and_persist,
                uploaded_bytes=uploaded_bytes,
                uploaded_filenames=uploaded_filenames,
                prompt=prompt,
                preset=normalized_preset,
                scene_preference=normalized_scene_preference,
                fidelity_mode=normalized_fidelity_mode,
                pose_flex_mode=normalized_pose_flex_mode,
                n_images=n_images,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                on_stage=None,
            )
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


def _run_v2_pipeline_and_persist(
    *,
    uploaded_bytes: List[bytes],
    uploaded_filenames: Optional[List[str]],
    prompt: Optional[str],
    preset: str,
    scene_preference: str,
    fidelity_mode: str,
    pose_flex_mode: str,
    n_images: int,
    aspect_ratio: str,
    resolution: str,
    on_stage: Optional[Callable[[str, dict], None]] = None,
) -> GenerateResponse:
    """Wrapper que roda pipeline_v2, persiste historico, e retorna GenerateResponse."""
    raw = run_pipeline_v2(
        uploaded_bytes=uploaded_bytes,
        uploaded_filenames=uploaded_filenames,
        prompt=prompt,
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=pose_flex_mode,
        n_images=n_images,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        on_stage=on_stage,
    )
    persist_v2_history(
        raw,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=pose_flex_mode,
    )
    return build_v2_generate_response(
        raw,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=pose_flex_mode,
    )


@router.post("/async")
async def generate_async(
    prompt: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
    resolution: str = Form(default=DEFAULT_RESOLUTION),
    n_images: int = Form(default=DEFAULT_N_IMAGES),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    guided_brief: Optional[str] = Form(default=None),
    preset: Optional[str] = Form(default=None),
    scene_preference: str = Form(default="auto_br"),
    fidelity_mode: str = Form(default="balanceada"),
    pose_flex_mode: str = Form(default="auto"),
    images: List[UploadFile] = File(default=[]),
):
    try:
        validate_generation_params(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=n_images,
            valid_n_images=VALID_N_IMAGES,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    limited_images = images[:14]
    uploaded_bytes = [await img.read() for img in limited_images]
    uploaded_filenames = [str(img.filename or "").strip() for img in limited_images]
    use_v2 = should_use_v2(preset, uploaded_bytes)
    _prompt_short = (prompt or "")[:120].strip() or None
    job_id = create_job(
        meta={
            # ── Identificação do pipeline ──
            "pipeline_version": "v2" if use_v2 else "v1",
            # ── Parâmetros de geração ──
            "prompt": _prompt_short,
            "prompt_full": (prompt or "").strip() or None,
            "n_images": n_images,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            # ── Preset & modos (v2) ──
            "preset": preset,
            "scene_preference": scene_preference,
            "fidelity_mode": fidelity_mode,
            "pose_flex_mode": pose_flex_mode,
            # ── Grounding ──
            "grounding_strategy": grounding_strategy,
            "use_grounding": use_grounding,
            # ── Referências visuais ──
            "has_images": bool(uploaded_bytes),
            "image_count": len(uploaded_bytes),
            "image_filenames": uploaded_filenames[:10] if uploaded_filenames else [],
            # ── Guided brief ──
            "has_guided_brief": bool(guided_brief),
        }
    )

    def _worker() -> None:
        def _stage_cb(stage: str, data: dict) -> None:
            update_stage(job_id, stage, data)

        try:
            if use_v2:
                normalized_preset, normalized_scene_preference, normalized_fidelity_mode, normalized_pose_flex_mode = normalize_v2_options(
                    preset=preset,
                    scene_preference=scene_preference,
                    fidelity_mode=fidelity_mode,
                    pose_flex_mode=pose_flex_mode,
                )
                response = _run_v2_pipeline_and_persist(
                    uploaded_bytes=uploaded_bytes,
                    uploaded_filenames=uploaded_filenames,
                    prompt=prompt,
                    preset=normalized_preset,
                    scene_preference=normalized_scene_preference,
                    fidelity_mode=normalized_fidelity_mode,
                    pose_flex_mode=normalized_pose_flex_mode,
                    n_images=n_images,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    on_stage=_stage_cb,
                )
            else:
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
