from __future__ import annotations

from typing import Any, Optional

from agent_runtime.camera import (
    _compose_prompt_with_camera,
    _extract_camera_realism_block,
    _normalize_camera_realism_block,
    _select_camera_realism_profile,
)
from agent_runtime.compiler import _compile_prompt_v2, _count_words
from agent_runtime.garment_narrative import sanitize_garment_narrative


def finalize_prompt_agent_result(
    *,
    result: dict[str, Any],
    has_images: bool,
    has_prompt: bool,
    user_prompt: Optional[str],
    structural_contract: dict[str, Any],
    guided_brief: Optional[dict[str, Any]],
    guided_enabled: bool,
    guided_set_mode: str,
    guided_set_detection: dict[str, Any],
    grounding_mode: str,
    pipeline_mode: str,
    aspect_ratio: str,
    pose: str,
    grounding_pose_clause: str,
    profile: str,
    scenario: str,
    diversity_target: Optional[dict[str, Any]],
) -> dict[str, Any]:
    base_prompt_raw = str(result.get("base_prompt", "") or "").strip()
    legacy_prompt_raw = str(result.get("prompt", "") or "").strip()
    if not base_prompt_raw:
        base_prompt_raw = legacy_prompt_raw
    if not base_prompt_raw:
        base_prompt_raw = "RAW photo, polished e-commerce catalog composition with garment-first framing."

    garment_narrative = str(result.get("garment_narrative", "") or "").strip()
    if garment_narrative:
        garment_narrative = sanitize_garment_narrative(garment_narrative, structural_contract)
        garment_words = garment_narrative.split()
        if len(garment_words) > 35:
            garment_narrative = " ".join(garment_words[:35])
            garment_words = garment_narrative.split()
        if garment_narrative:
            print(f"[AGENT] 👗 garment_narrative ({len(garment_words)}w): {garment_narrative[:120]}")

    camera_realism_raw = str(result.get("camera_and_realism", "") or "").strip()
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(legacy_prompt_raw)
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(base_prompt_raw)

    camera_profile = _select_camera_realism_profile(
        has_images=has_images,
        has_prompt=has_prompt,
        user_prompt=user_prompt,
        base_prompt=base_prompt_raw,
        camera_text=camera_realism_raw,
    )
    camera_realism = _normalize_camera_realism_block(
        camera_realism_raw,
        str(result.get("shot_type", "auto")),
        profile=camera_profile,
    )

    camera_words = _count_words(camera_realism)
    base_budget = max(80, 220 - camera_words)
    if has_images and not has_prompt:
        target_budget = 215
        base_budget = max(80, target_budget - camera_words)

    lighting_hint = (diversity_target or {}).get("lighting_hint", "") or ""
    compiled_base_prompt, compiler_debug = _compile_prompt_v2(
        prompt=base_prompt_raw,
        has_images=has_images,
        has_prompt=has_prompt,
        contract=structural_contract if has_images else None,
        guided_brief=guided_brief if guided_enabled else None,
        guided_enabled=guided_enabled,
        guided_set_detection=guided_set_detection if guided_enabled and guided_set_mode == "conjunto" else None,
        grounding_mode=grounding_mode,
        pipeline_mode=pipeline_mode,
        word_budget=base_budget,
        aspect_ratio=aspect_ratio,
        pose_hint=pose or grounding_pose_clause,
        profile_hint=profile,
        scenario_hint=scenario if (has_images and not has_prompt) else "",
        garment_narrative=garment_narrative if (has_images and not has_prompt) else "",
        lighting_hint=lighting_hint if (has_images and not has_prompt) else "",
    )

    final_prompt = _compose_prompt_with_camera(compiled_base_prompt, camera_realism)
    result["base_prompt"] = compiled_base_prompt
    result["camera_and_realism"] = camera_realism
    result["camera_profile"] = camera_profile
    result["prompt"] = final_prompt

    compiler_debug["camera_words"] = camera_words
    compiler_debug["base_budget"] = base_budget
    compiler_debug["camera_profile"] = camera_profile
    compiler_debug["final_words"] = _count_words(final_prompt)
    result["prompt_compiler_debug"] = compiler_debug
    return result
