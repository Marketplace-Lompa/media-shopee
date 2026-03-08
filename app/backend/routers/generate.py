"""
Router: POST /generate
Pipeline síncrono com camada de efetividade V4.
"""
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from models import GenerateResponse, GeneratedImage
from agent import run_agent
from grounding_policy import compute_grounding_triage, normalize_grounding_strategy
from generator import generate_images
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
from config import VALID_ASPECT_RATIOS, VALID_RESOLUTIONS, VALID_N_IMAGES

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResponse)
async def generate(
    prompt: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default="1:1"),
    resolution: str = Form(default="1K"),
    n_images: int = Form(default=1),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    images: List[UploadFile] = File(default=[]),
):
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise HTTPException(400, f"aspect_ratio inválido. Use: {VALID_ASPECT_RATIOS}")
    if resolution not in VALID_RESOLUTIONS:
        raise HTTPException(400, f"resolution inválida. Use: {VALID_RESOLUTIONS}")
    if n_images not in VALID_N_IMAGES:
        raise HTTPException(400, f"n_images inválido. Use: {VALID_N_IMAGES}")

    uploaded_bytes = []
    for img in images[:14]:
        uploaded_bytes.append(await img.read())

    pool_context = "POOL_RUNTIME_DISABLED"
    pipeline_mode = "reference_mode" if uploaded_bytes else "text_mode"
    strategy = normalize_grounding_strategy(grounding_strategy, use_grounding)

    reference_pack = build_reference_pack(uploaded_bytes)
    analysis_images = reference_pack.get("analysis_images", [])
    generation_images = reference_pack.get("generation_images", [])
    reference_pack_stats = reference_pack.get("stats", {})
    diversity_target = select_diversity_target(seed_hint=prompt or "")

    triage = {}
    classifier_summary = {}
    decision = {"grounding_mode": "off", "trigger_reason": "unknown", "reason_codes": []}
    try:
        baseline_result = run_agent(
            user_prompt=prompt,
            uploaded_images=analysis_images if analysis_images else None,
            pool_context=pool_context,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            use_grounding=False,
            diversity_target=diversity_target,
        )
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
        if applied_mode == "off":
            agent_result = baseline_result
        else:
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
                )
            except Exception:
                agent_result = baseline_result
                applied_mode = "off"
    except Exception as e:
        raise HTTPException(500, f"Erro no Prompt Agent: {str(e)}")

    grounded_images = list(agent_result.pop("_grounded_images", []) or [])
    pipeline_mode = agent_result.get("pipeline_mode", pipeline_mode)
    optimized_prompt = agent_result.get("prompt", "")
    thinking_level = agent_result.get("thinking_level", "MINIMAL")
    thinking_reason = agent_result.get("thinking_reason", "")
    shot_type = agent_result.get("shot_type", "auto")
    realism_level = agent_result.get("realism_level", 2)

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

    session_id = str(uuid.uuid4())[:8]
    raw_images = []
    failed_indices = []
    image_assessments = []
    repair_applied = False
    reason_codes = set((decision.get("reason_codes", []) or []) + (quality_contract.get("reason_codes", []) or []))

    for i in range(n_images):
        ok = False
        last_error = None
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
                repaired_assessment = assess_generated_image(
                    repaired_batch[0]["path"], repair_prompt, classifier_summary
                )
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
        raise HTTPException(500, "Erro no Image Generator: nenhuma imagem foi gerada.")

    quality_contract = enrich_quality_with_generation(quality_contract, image_assessments)
    reason_codes.update(quality_contract.get("reason_codes", []) or [])

    log_effectiveness_event({
        "session_id": session_id,
        "category": quality_contract.get("category", "general"),
        "global_score": quality_contract.get("global_score", 0.0),
        "reason_codes": sorted(reason_codes),
        "repair_applied": repair_applied,
        "pipeline_mode": pipeline_mode,
    })

    return GenerateResponse(
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
    )
