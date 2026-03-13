"""
Router: POST /generate/stream
SSE (Server-Sent Events) com pipeline de efetividade V4.
"""
import asyncio
import json
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from agent import run_agent
from agent_runtime.pipeline_v2 import run_pipeline_v2
from agent_runtime.pipeline_v2_support import (
    build_v2_response_payload,
    normalize_v2_options,
    persist_v2_history,
    should_use_v2,
)
from guided_mode import guided_force_grounding_floor, guided_summary, normalize_guided_brief
from grounding_policy import compute_grounding_triage, normalize_grounding_strategy
from generator import generate_images
from history import add_entry as history_add, purge_oldest as history_purge
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
from config import DEFAULT_ASPECT_RATIO, DEFAULT_N_IMAGES, DEFAULT_RESOLUTION, VALID_ASPECT_RATIOS, VALID_RESOLUTIONS, VALID_N_IMAGES

router = APIRouter(prefix="/generate", tags=["generate-stream"])


def _sse_event(stage: str, data: dict) -> str:
    payload = json.dumps({"stage": stage, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


@router.post("/stream")
async def generate_stream(
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
    # UploadFile precisa ser lido no contexto do request
    uploaded_bytes = []
    uploaded_filenames = []
    for img in images[:14]:
        uploaded_bytes.append(await img.read())
        uploaded_filenames.append(str(img.filename or "").strip())

    use_v2 = should_use_v2(preset, uploaded_bytes)

    async def event_generator_v2():
        """SSE generator para pipeline v2."""
        collected_events: list[dict] = []
        normalized_preset, normalized_scene_preference, normalized_fidelity_mode, normalized_pose_flex_mode = normalize_v2_options(
            preset=preset,
            scene_preference=scene_preference,
            fidelity_mode=fidelity_mode,
            pose_flex_mode=pose_flex_mode,
        )

        def _on_stage(stage: str, data: dict) -> None:
            collected_events.append({"stage": stage, **data})

        try:
            raw = await asyncio.to_thread(
                run_pipeline_v2,
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
                on_stage=_on_stage,
            )
        except Exception as e:
            yield _sse_event("error", {"message": str(e)})
            return

        # Replay stage events
        for evt in collected_events:
            stage = evt.pop("stage", "unknown")
            if stage != "done":
                yield _sse_event(stage, evt)

        persist_v2_history(raw, aspect_ratio=aspect_ratio, resolution=resolution)
        response_data = build_v2_response_payload(
            raw,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            preset=normalized_preset,
            scene_preference=normalized_scene_preference,
            fidelity_mode=normalized_fidelity_mode,
            pose_flex_mode=normalized_pose_flex_mode,
        )
        yield _sse_event("done", {"data": response_data})

    if use_v2:
        return StreamingResponse(
            event_generator_v2(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    async def event_generator():
        if aspect_ratio not in VALID_ASPECT_RATIOS:
            yield _sse_event("error", {"message": f"aspect_ratio inválido. Use: {VALID_ASPECT_RATIOS}"})
            return
        if resolution not in VALID_RESOLUTIONS:
            yield _sse_event("error", {"message": f"resolution inválida. Use: {VALID_RESOLUTIONS}"})
            return
        if n_images not in VALID_N_IMAGES:
            yield _sse_event("error", {"message": f"n_images inválido. Use: {VALID_N_IMAGES}"})
            return

        session_id = str(uuid.uuid4())[:8]
        from config import OUTPUTS_DIR

        n_uploads = len(uploaded_bytes)
        pipeline_mode = "reference_mode" if n_uploads > 0 else "text_mode"
        pool_context = ""
        normalized_guided = normalize_guided_brief(guided_brief)

        reference_pack = build_reference_pack(uploaded_bytes)
        analysis_images = reference_pack.get("analysis_images", [])
        curated_images = reference_pack.get("generation_images", [])
        reference_pack_stats = reference_pack.get("stats", {})
        # Persistir apenas referências curadas efetivamente usadas no job
        reference_urls: List[str] = []
        if curated_images:
            session_dir = OUTPUTS_DIR / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            for idx, img_bytes in enumerate(curated_images):
                ref_filename = f"ref_curated_{idx+1}.jpg"
                (session_dir / ref_filename).write_bytes(img_bytes)
                reference_urls.append(f"/outputs/{session_id}/{ref_filename}")

        # ── Art Director: triagem visual ANTES da diversidade (R3) ──────────
        unified_triage_result = None
        image_analysis_text = ""
        garment_aesthetic = None
        structural_contract_for_diversity = None
        structural_hint_for_nano = None  # string para role_prefix do Nano Banana
        if n_uploads > 0:
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
        diversity_target = select_diversity_target(
            seed_hint=prompt or "",
            guided_brief=normalized_guided,
            garment_aesthetic=garment_aesthetic,
            structural_contract=structural_contract_for_diversity,
        )

        yield _sse_event("mode_selected", {
            "message": "Modo com referência ativado" if pipeline_mode == "reference_mode" else "Modo sem referência ativado",
            "pipeline_mode": pipeline_mode,
            "reference_pack_stats": reference_pack_stats,
            "model_profile_id": diversity_target.get("profile_id"),
        })

        strategy = normalize_grounding_strategy(grounding_strategy, use_grounding)
        yield _sse_event("analyzing", {
            "message": f"Agente analisando {len(analysis_images or curated_images)} imagem(ns) curada(s)…" if n_uploads > 0 else "Agente criando prompt…",
            "n_uploads": n_uploads,
        })

        applied_mode = "off"
        triage = {}
        classifier_summary = {}
        decision = {"reason_codes": [], "trigger_reason": "unknown"}

        try:
            triage = compute_grounding_triage(
                user_prompt=prompt,
                image_analysis=image_analysis_text,
                has_images=n_uploads > 0,
            )
            classifier_summary = classify_visual_context(
                user_prompt=prompt,
                image_analysis=image_analysis_text,
                has_images=n_uploads > 0,
                reference_pack_stats=reference_pack_stats,
            )
            decision = decide_grounding_mode(
                strategy=strategy,
                has_images=n_uploads > 0,
                triage=triage,
                classifier_summary=classifier_summary,
            )
            applied_mode = decision.get("grounding_mode", "off")
            if strategy == "auto" and applied_mode == "off" and guided_force_grounding_floor(
                normalized_guided, n_uploads > 0
            ):
                applied_mode = "lexical"
                decision["trigger_reason"] = "guided_floor_forced_grounding"
                decision["reason_codes"] = sorted(set((decision.get("reason_codes", []) or []) + ["guided_floor_forced_grounding"]))

            yield _sse_event("triage_done", {
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
            })

            if applied_mode != "off":
                yield _sse_event("researching", {
                    "message": "Pesquisando referências na web…",
                    "grounding_mode": applied_mode,
                })

            try:
                agent_result = await asyncio.to_thread(
                    run_agent,
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
                    print(f"[STREAM] ⚠️ Grounding failed, fallback baseline: {e}")
                    applied_mode = "off"
                    agent_result = await asyncio.to_thread(
                        run_agent,
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
            yield _sse_event("error", {"message": f"Erro no Prompt Agent: {str(e)}"})
            return

        optimized_prompt = agent_result.get("prompt", "")
        thinking_level = agent_result.get("thinking_level", "MINIMAL")
        thinking_reason = agent_result.get("thinking_reason", "")
        shot_type = agent_result.get("shot_type", "auto")
        realism_level = agent_result.get("realism_level", 2)
        pipeline_mode = agent_result.get("pipeline_mode", pipeline_mode)
        grounded_images = list(agent_result.pop("_grounded_images", []) or [])
        image_analysis = agent_result.get("image_analysis", "")
        guided_sum = agent_result.get("guided_summary") or guided_summary(normalized_guided, shot_type)

        grounding_sources = (agent_result.get("grounding", {}) or {}).get("sources", []) or []
        grounded_images_count = int((agent_result.get("grounding", {}) or {}).get("grounded_images_count", 0) or 0)
        grounding_effective = bool(len(grounding_sources) > 0 or grounded_images_count > 0)
        grounding_attempted = applied_mode != "off"

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
            "attempted": grounding_attempted,
            "effective": grounding_effective,
        }

        quality_contract = compute_quality_contract(
            prompt=optimized_prompt,
            pipeline_mode=pipeline_mode,
            classifier_summary=classifier_summary,
            grounding_info=grounding_info,
            diversity_target=diversity_target,
        )

        yield _sse_event("prompt_ready", {
            "message": "Prompt criado pelo agente",
            "prompt": optimized_prompt,
            "image_analysis": image_analysis,
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
        })

        generated_images = []
        failed_indices = []
        image_assessments = []
        reason_codes = set(
            (decision.get("reason_codes", []) or []) + 
            (quality_contract.get("reason_codes", []) or []) +
            (grounding_info.get("reason_codes", []) or [])
        )

        for i in range(n_images):
            yield _sse_event("generating", {
                "message": f"Gerando imagem {i+1}/{n_images} via Nano…",
                "current": i + 1,
                "total": n_images,
            })

            ok = False
            last_error = None
            selected_batch = None
            selected_assessment = None

            for attempt in range(2):
                try:
                    batch = await asyncio.to_thread(
                        generate_images,
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
                    selected_assessment = assess_generated_image(
                        batch[0]["path"], optimized_prompt, classifier_summary
                    )
                    ok = True
                    break
                except Exception as e:
                    last_error = e
                    print(f"[STREAM] ⚠️ generation attempt {attempt+1} failed for {i+1}/{n_images}: {e}")

            if not ok or not selected_batch or not selected_assessment:
                failed_indices.append(i + 1)
                yield _sse_event("generating", {
                    "message": f"Imagem {i+1}/{n_images} falhou após retry e será marcada como parcial.",
                    "current": i + 1,
                    "total": n_images,
                })
                continue

            best_batch = selected_batch
            best_assessment = selected_assessment

            generated_images.extend(best_batch)
            image_assessments.append(best_assessment)
            reason_codes.update(best_assessment.get("reason_codes", []) or [])

        if not generated_images:
            yield _sse_event("error", {"message": "Nenhuma imagem foi gerada."})
            return

        quality_contract = enrich_quality_with_generation(quality_contract, image_assessments)
        reason_codes.update(quality_contract.get("reason_codes", []) or [])

        response_data = {
            "session_id": session_id,
            "optimized_prompt": optimized_prompt,
            "pipeline_mode": pipeline_mode,
            "thinking_level": thinking_level,
            "thinking_reason": thinking_reason,
            "shot_type": shot_type,
            "realism_level": realism_level,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "images": generated_images,
            "failed_indices": failed_indices or None,
            "pool_refs_used": 0,
            "image_analysis": agent_result.get("image_analysis") or None,
            "grounding": grounding_info,
            "quality_contract": quality_contract,
            "fidelity_score": quality_contract.get("fidelity_score"),
            "commercial_score": quality_contract.get("commercial_score"),
            "diversity_score": quality_contract.get("diversity_score"),
            "grounding_reliability": quality_contract.get("grounding_reliability"),
            "reason_codes": sorted(reason_codes),
            "repair_applied": False,
            "reference_pack_stats": reference_pack_stats,
            "classifier_summary": classifier_summary,
            "guided_applied": bool(guided_sum),
            "guided_summary": guided_sum,
            "prompt_compiler_debug": agent_result.get("prompt_compiler_debug"),
        }

        grounding_eff = grounding_info.get("effective", False) if isinstance(grounding_info, dict) else False
        _base_prompt = agent_result.get("base_prompt") or None
        _camera_and_realism = agent_result.get("camera_and_realism") or None
        _camera_profile = agent_result.get("camera_profile") or None
        _grounding_mode = grounding_info.get("applied_mode") or applied_mode or None
        _reason_codes = sorted(reason_codes) if reason_codes else []
        for img in generated_images:
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

        log_effectiveness_event({
            "session_id": session_id,
            "category": quality_contract.get("category", "general"),
            "global_score": quality_contract.get("global_score", 0.0),
            "reason_codes": sorted(reason_codes),
            "repair_applied": False,
            "pipeline_mode": pipeline_mode,
        })

        try:
            history_purge()
        except Exception as purge_err:
            print(f"[CLEANUP] ⚠️ Falha no purge: {purge_err}")

        if failed_indices:
            yield _sse_event("done_partial", {"data": response_data})
        else:
            yield _sse_event("done", {"data": response_data})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
