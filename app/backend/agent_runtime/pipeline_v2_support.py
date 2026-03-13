from __future__ import annotations

from typing import Any, Optional

from history import add_entry as history_add, purge_oldest as history_purge
from models import GenerateResponse, GeneratedImage

VALID_PRESETS = {"catalog_clean", "marketplace_lifestyle", "premium_lifestyle"}
VALID_SCENE_PREFS = {"auto_br", "indoor_br", "outdoor_br"}
VALID_FIDELITY_MODES = {"balanceada", "estrita"}
VALID_POSE_FLEX_MODES = {"auto", "controlled", "balanced", "dynamic"}


def should_use_v2(preset: Optional[str], uploaded_bytes: list[bytes]) -> bool:
    return preset is not None and preset in VALID_PRESETS and bool(uploaded_bytes)


def normalize_v2_options(
    *,
    preset: Optional[str],
    scene_preference: str,
    fidelity_mode: str,
    pose_flex_mode: Optional[str] = None,
) -> tuple[str, str, str, str]:
    return (
        preset if preset in VALID_PRESETS else "marketplace_lifestyle",
        scene_preference if scene_preference in VALID_SCENE_PREFS else "auto_br",
        fidelity_mode if fidelity_mode in VALID_FIDELITY_MODES else "balanceada",
        pose_flex_mode if pose_flex_mode in VALID_POSE_FLEX_MODES else "auto",
    )


def persist_v2_history(raw: dict[str, Any], *, aspect_ratio: str, resolution: str) -> None:
    session_id = str(raw.get("session_id", "") or "")
    if not session_id:
        return

    art_direction_summary = raw.get("art_direction_summary") or {}
    camera_profile = art_direction_summary.get("camera_profile") if isinstance(art_direction_summary, dict) else None
    reference_urls = list(raw.get("review_reference_urls", []) or [])

    for img in raw.get("images", []) or []:
        try:
            history_add(
                session_id=session_id,
                filename=img["filename"],
                url=img["url"],
                prompt=raw.get("optimized_prompt", ""),
                thinking_level="MINIMAL",
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                references=reference_urls,
                base_prompt=raw.get("stage1_prompt"),
                camera_profile=camera_profile,
            )
        except Exception as hist_err:
            print(f"[HISTORY] v2 persist error: {hist_err}")
    try:
        history_purge()
    except Exception:
        pass


def build_v2_response_payload(
    raw: dict[str, Any],
    *,
    aspect_ratio: str,
    resolution: str,
    preset: str,
    scene_preference: str,
    fidelity_mode: str,
    pose_flex_mode: str,
) -> dict[str, Any]:
    return {
        "session_id": raw.get("session_id"),
        "optimized_prompt": raw.get("optimized_prompt", ""),
        "pipeline_mode": raw.get("pipeline_mode", "reference_mode_strict"),
        "pipeline_version": "v2",
        "thinking_level": "MINIMAL",
        "thinking_reason": "pipeline_v2",
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "images": raw.get("images", []),
        "failed_indices": raw.get("failed_indices"),
        "pool_refs_used": 0,
        "art_direction_summary": raw.get("art_direction_summary"),
        "preset": preset,
        "scene_preference": scene_preference,
        "fidelity_mode": fidelity_mode,
        "pose_flex_mode": raw.get("pose_flex_mode", pose_flex_mode),
        "pose_flex_guideline": raw.get("pose_flex_guideline"),
        "generation_time": raw.get("generation_time"),
        "reference_pack_stats": raw.get("selector_stats"),
        "repair_applied": raw.get("repair_applied"),
        "reason_codes": raw.get("reason_codes"),
        "debug_report_url": raw.get("report_url"),
        "debug_report_path": raw.get("report_path"),
    }


def build_v2_generate_response(
    raw: dict[str, Any],
    *,
    aspect_ratio: str,
    resolution: str,
    preset: str,
    scene_preference: str,
    fidelity_mode: str,
    pose_flex_mode: str,
) -> GenerateResponse:
    payload = build_v2_response_payload(
        raw,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=pose_flex_mode,
    )
    return GenerateResponse(
        session_id=payload.get("session_id"),
        optimized_prompt=payload.get("optimized_prompt", ""),
        pipeline_mode=payload.get("pipeline_mode", "reference_mode_strict"),
        thinking_level="MINIMAL",
        thinking_reason="pipeline_v2",
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        images=[GeneratedImage(**img) for img in raw.get("images", [])],
        failed_indices=payload.get("failed_indices") or None,
        pipeline_version="v2",
        art_direction_summary=payload.get("art_direction_summary"),
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=payload.get("pose_flex_mode"),
        pose_flex_guideline=payload.get("pose_flex_guideline"),
        generation_time=payload.get("generation_time"),
        reference_pack_stats=payload.get("reference_pack_stats"),
        repair_applied=payload.get("repair_applied"),
        reason_codes=payload.get("reason_codes"),
        debug_report_url=payload.get("debug_report_url"),
        debug_report_path=payload.get("debug_report_path"),
    )
