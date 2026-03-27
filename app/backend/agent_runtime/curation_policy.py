from __future__ import annotations

import os
from typing import Any, Optional, TypedDict

from agent_runtime.mode_profile import get_mode_profile
from agent_runtime.structural import (
    is_selfie_capture_compatible,
    is_spatially_sensitive_garment,
)


_SCENE_AFFINITY: dict[str, str] = {
    "auto_br": "",
    "indoor_br": "indoor_br",
    "outdoor_br": "outdoor_br",
}


_STABLE_POSE_IDS = [
    "front_relaxed_hold",
    "standing_full_shift",
    "soft_wall_lean",
    "hand_adjust_neckline",
    "standing_3q_relaxed",
    "contrapposto_editorial",
]
_BALANCED_POSE_IDS = [
    "standing_3q_relaxed",
    "front_relaxed_hold",
    "standing_full_shift",
    "soft_wall_lean",
    "hand_adjust_neckline",
    "paused_mid_step",
    "half_turn_lookback",
    "contrapposto_editorial",
]
_MOVEMENT_POSE_IDS = [
    "paused_mid_step",
    "half_turn_lookback",
    "walking_stride_controlled",
    "twist_step_forward",
]

_CATALOG_SCENES = ["br_showroom_sp", "br_brasilia_concrete_gallery"]
_INDOOR_COMMERCIAL_SCENES = ["br_pinheiros_living", "br_rio_art_loft", "br_porto_alegre_bookstore"]
_OUTDOOR_COMMERCIAL_SCENES = ["br_recife_balcony", "br_floripa_boardwalk", "br_salvador_colonial_street"]
_UGC_INDOOR_SCENES = ["br_boutique_floor", "br_fitting_room_mirror", "br_elevator_mirror", "br_bedroom_window"]
_UGC_OUTDOOR_SCENES = ["br_bairro_sidewalk", "br_recife_balcony"]

_PREMIUM_CASTING = ["br_minimal_premium", "br_soft_editorial", "br_afro", "br_mature_elegante"]
_NATURAL_CASTING = ["br_everyday_natural", "br_warm_commercial", "br_morena_clara", "br_afro"]
_UGC_CASTING = ["br_social_creator", "br_everyday_natural", "br_loira_natural", "br_morena_clara"]

_COMMERCIAL_CAMERAS = ["canon_balanced", "sony_documentary"]
_NATURAL_CAMERAS = ["sony_documentary", "fujifilm_candid", "canon_balanced"]
_PHONE_CAMERAS = ["phone_cameraroll", "phone_clean", "phone_direct_flash"]

_CATALOG_LIGHTING = ["clean_showroom", "window_daylight"]
_NATURAL_LIGHTING = ["window_daylight", "open_shade_daylight", "cloudy_tropical"]
_EDITORIAL_LIGHTING = ["window_daylight", "mixed_window_lamp", "open_shade_daylight"]
_UGC_LIGHTING = ["phone_practical_mixed", "phone_flash_direct", "window_daylight"]


class IdentityGuard(TypedDict):
    strength: str
    risk: str
    forbid_identity_transfer: bool
    forbid_pose_clone: bool
    forbid_composition_clone: bool
    prioritize_identity_safe_refs: bool
    rules: list[str]


class SceneConstraints(TypedDict):
    context_rigidity: str
    backdrop_mode: str
    allow_context_invention: bool
    environment_competition: str


class PoseConstraints(TypedDict):
    movement_budget: str
    frontality_bias: str
    occlusion_tolerance: str
    gesture_range: str
    silhouette_priority: str


class CaptureConstraints(TypedDict):
    camera_language: str
    framing_priority: str
    angle_bias: str
    depth_context: str


class ArtDirectionSelectionPolicy(TypedDict):
    preferred_scene_ids: list[str]
    avoid_scene_ids: list[str]
    preferred_camera_ids: list[str]
    avoid_camera_ids: list[str]
    preferred_lighting_ids: list[str]
    avoid_lighting_ids: list[str]
    preferred_casting_family_ids: list[str]
    avoid_casting_family_ids: list[str]
    preferred_pose_ids: list[str]
    avoid_pose_ids: list[str]
    ugc_intent: str
    identity_guard: IdentityGuard
    scene_constraints: SceneConstraints
    pose_constraints: PoseConstraints
    capture_constraints: CaptureConstraints
    movement_budget: str
    frontality_bias: str
    occlusion_tolerance: str


def _lighting_signature_policy_enabled() -> bool:
    raw = os.getenv("ENABLE_LIGHTING_SIGNATURE_POLICY", "true").strip().lower()
    return raw != "false"


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = str(item or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def apply_selection_policy(
    allowed_ids: list[str],
    *,
    preferred_ids: Optional[list[str]] = None,
    avoid_ids: Optional[list[str]] = None,
) -> list[str]:
    ids = dedupe_preserve_order([item for item in allowed_ids if item])
    preferred = [item for item in dedupe_preserve_order(preferred_ids or []) if item in ids]
    avoided = set(dedupe_preserve_order(avoid_ids or []))

    if preferred:
        ids = preferred
    elif avoided and len(ids) > 1:
        pruned = [item for item in ids if item not in avoided]
        if pruned:
            ids = pruned
    return ids


def _mode_guardrail_profile(mode: Optional[str]) -> str:
    return get_mode_profile(mode).guardrail_profile


def _movement_budget_from_guardrail(
    *,
    guardrail_profile: str,
    strict_mode: bool,
    spatially_sensitive: bool,
) -> str:
    """Derive movement budget from guardrail_profile (Soul-First)."""
    if guardrail_profile == "strict_catalog" or strict_mode:
        return "low"
    if spatially_sensitive:
        return "medium"
    if guardrail_profile == "lifestyle_permissive":
        return "medium-high"
    if guardrail_profile == "editorial_controlled":
        return "medium"
    return "medium"


def _frontality_bias_from_guardrail(*, guardrail_profile: str, scene_preference: str) -> str:
    if guardrail_profile == "strict_catalog":
        return "front"
    if guardrail_profile == "editorial_controlled":
        return "slight_angle"
    if guardrail_profile == "natural_commercial":
        return "slight_angle"
    if scene_preference == "outdoor_br":
        return "free"
    return "slight_angle"


def _occlusion_tolerance_from_guardrail(
    *,
    guardrail_profile: str,
    strict_mode: bool,
    spatially_sensitive: bool,
) -> str:
    if guardrail_profile == "strict_catalog" or strict_mode or spatially_sensitive:
        return "low"
    if guardrail_profile == "lifestyle_permissive":
        return "medium"
    return "medium"


def _ugc_intent(
    *,
    text: str,
    spatially_sensitive: bool,
    selfie_compatible: bool,
) -> str:
    ugc_like = any(token in text for token in ("ugc", "cliente real", "review real", "depoimento", "social proof"))
    if not ugc_like:
        return "none"
    if any(token in text for token in ("selfie", "mirror selfie", "espelho", "mirror")) and selfie_compatible:
        return "mirror_tryon"
    if any(token in text for token in ("boutique", "loja", "store", "provador", "fitting room", "creator", "influencer")):
        return "boutique_creator"
    if any(token in text for token in ("casa", "quarto", "closet", "apartamento", "janela")):
        return "at_home_creator"
    if spatially_sensitive:
        return "boutique_creator"
    return "friend_shot_review"


def build_affinity_prompt(
    user_prompt: Optional[str],
    mode: str,
    scene_preference: str,
) -> Optional[str]:
    del mode, scene_preference
    prompt = str(user_prompt or "").strip()
    return prompt or None


def derive_reference_budget(
    *,
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
    identity_risk: str,
) -> dict[str, int]:
    stats = selector_stats or {}
    raw_count = int(stats.get("raw_count", 0) or 0)
    complex_garment = bool(stats.get("complex_garment"))
    strict_mode = str(fidelity_mode).strip().lower() == "estrita"

    stage1_max = 4
    stage2_max = 4 if strict_mode else 3

    if complex_garment and raw_count >= 6:
        stage1_max = 3
        stage2_max = 4 if strict_mode else 3
    elif identity_risk in {"medium", "high"}:
        stage2_max = min(stage2_max, 3)

    return {
        "stage1_max_refs": stage1_max,
        "stage2_max_refs": stage2_max,
        "judge_max_refs": 4,
    }


def derive_reference_guard_bundle(
    *,
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
    mode: Optional[str] = None,
) -> IdentityGuard:
    stats = selector_stats or {}
    risk = str(stats.get("identity_reference_risk", "low") or "low").strip().lower()
    guardrail_profile = _mode_guardrail_profile(mode)
    strict_mode = str(fidelity_mode).strip().lower() == "estrita" or guardrail_profile == "strict_catalog"

    if strict_mode:
        strength = "strict"
    elif risk == "high":
        strength = "high"
    elif risk == "medium":
        strength = "strict"
    else:
        strength = "standard"

    rules = [
        "References are visual evidence for garment fidelity only.",
        "Do not copy any human identity traits from references.",
    ]
    if guardrail_profile != "strict_catalog":
        rules.append(
            "Do not repeat the dominant gesture from references unless the user brief explicitly requires it."
        )
    if risk in {"medium", "high"}:
        rules.append(
            "Prioritize detail anchors and identity-safe references over worn references when conflicts appear."
        )
    if risk == "high":
        rules.append("If a reference has a visible face, treat that face as forbidden content for transfer.")

    return {
        "strength": strength,
        "risk": risk,
        "forbid_identity_transfer": True,
        "forbid_pose_clone": True,
        "forbid_composition_clone": guardrail_profile != "strict_catalog",
        "prioritize_identity_safe_refs": risk in {"medium", "high"},
        "rules": rules,
    }


def derive_reference_guard_config(
    *,
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
    mode: Optional[str] = None,
) -> tuple[str, list[str]]:
    bundle = derive_reference_guard_bundle(
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
        mode=mode,
    )
    return bundle["strength"], bundle["rules"]




def stage1_candidate_count(
    *,
    fidelity_mode: str,
    selector_stats: Optional[dict[str, Any]],
) -> int:
    if str(fidelity_mode).strip().lower() == "estrita":
        return 2
    if bool((selector_stats or {}).get("complex_garment")):
        return 2
    return 1


def derive_art_direction_selection_policy(
    *,
    preset: str,
    scene_preference: str,
    image_analysis_hint: str,
    structural_hint: str,
    lighting_signature: Optional[dict[str, Any]] = None,
    user_prompt: Optional[str],
    fidelity_mode: str,
    selector_stats: Optional[dict[str, Any]] = None,
    structural_contract: Optional[dict[str, Any]] = None,
) -> ArtDirectionSelectionPolicy:
    stats = selector_stats or {}
    text = " ".join(
        part
        for part in [
            str(user_prompt or "").strip(),
            image_analysis_hint,
            structural_hint,
            preset,
            scene_preference,
            fidelity_mode,
        ]
        if part
    ).lower()

    guardrail_profile = _mode_guardrail_profile(preset)
    strict_mode = str(fidelity_mode).strip().lower() == "estrita" or guardrail_profile == "strict_catalog"
    spatially_sensitive = is_spatially_sensitive_garment(
        structural_contract,
        set_detection=None,
        selector_stats=selector_stats,
    )
    selfie_compatible = is_selfie_capture_compatible(
        structural_contract,
        selector_stats=selector_stats,
    )
    ugc_intent = _ugc_intent(
        text=text,
        spatially_sensitive=spatially_sensitive,
        selfie_compatible=selfie_compatible,
    )
    ugc_like = ugc_intent != "none"
    lighting = lighting_signature if isinstance(lighting_signature, dict) else {}
    lighting_style = str(lighting.get("source_style", "") or "").strip().lower()
    integration_risk = str(lighting.get("integration_risk", "") or "").strip().lower()

    movement_budget = _movement_budget_from_guardrail(
        guardrail_profile=guardrail_profile,
        strict_mode=strict_mode,
        spatially_sensitive=spatially_sensitive,
    )
    frontality_bias = _frontality_bias_from_guardrail(
        guardrail_profile=guardrail_profile,
        scene_preference=scene_preference,
    )
    occlusion_tolerance = _occlusion_tolerance_from_guardrail(
        guardrail_profile=guardrail_profile,
        strict_mode=strict_mode,
        spatially_sensitive=spatially_sensitive,
    )

    if guardrail_profile == "strict_catalog":
        preferred_scene_ids = list(_CATALOG_SCENES)
        avoid_scene_ids = dedupe_preserve_order(_UGC_INDOOR_SCENES + _UGC_OUTDOOR_SCENES + _OUTDOOR_COMMERCIAL_SCENES)
        preferred_camera_ids = list(_COMMERCIAL_CAMERAS)
        avoid_camera_ids = list(_PHONE_CAMERAS)
        preferred_lighting_ids = list(_CATALOG_LIGHTING)
        avoid_lighting_ids = ["golden_hour_soft", "coastal_late_morning", "phone_practical_mixed", "phone_flash_direct"]
        preferred_casting_family_ids = list(_PREMIUM_CASTING)
        avoid_casting_family_ids = ["br_social_creator", "br_warm_commercial"]
        preferred_pose_ids = list(_STABLE_POSE_IDS)
        avoid_pose_ids = list(_MOVEMENT_POSE_IDS)
        scene_constraints: SceneConstraints = {
            "context_rigidity": "locked",
            "backdrop_mode": "studio_minimal",
            "allow_context_invention": False,
            "environment_competition": "low",
        }
        pose_constraints: PoseConstraints = {
            "movement_budget": "low",
            "frontality_bias": "front",
            "occlusion_tolerance": "low",
            "gesture_range": "quiet",
            "silhouette_priority": "high",
        }
        capture_constraints: CaptureConstraints = {
            "camera_language": "clean_commercial",
            "framing_priority": "full_body_readability",
            "angle_bias": "front_or_neutral",
            "depth_context": "minimal",
        }
    elif ugc_like:
        preferred_scene_ids = list(_UGC_INDOOR_SCENES if scene_preference != "outdoor_br" else _UGC_OUTDOOR_SCENES)
        avoid_scene_ids = list(_CATALOG_SCENES)
        preferred_camera_ids = list(_PHONE_CAMERAS + _NATURAL_CAMERAS[:1])
        avoid_camera_ids = ["canon_balanced"] if ugc_intent == "mirror_tryon" else []
        preferred_lighting_ids = list(_UGC_LIGHTING)
        avoid_lighting_ids = ["clean_showroom"]
        preferred_casting_family_ids = list(_UGC_CASTING)
        avoid_casting_family_ids = ["br_minimal_premium", "br_mature_elegante"]
        preferred_pose_ids = list(_BALANCED_POSE_IDS)
        avoid_pose_ids = list(_MOVEMENT_POSE_IDS if spatially_sensitive else ["contrapposto_editorial"])
        scene_constraints = {
            "context_rigidity": "guided",
            "backdrop_mode": "ugc_local",
            "allow_context_invention": False,
            "environment_competition": "medium",
        }
        pose_constraints = {
            "movement_budget": "medium",
            "frontality_bias": "slight_angle",
            "occlusion_tolerance": "medium",
            "gesture_range": "everyday",
            "silhouette_priority": "high" if spatially_sensitive else "medium",
        }
        capture_constraints = {
            "camera_language": "phone_or_documentary",
            "framing_priority": "commercial_readability",
            "angle_bias": "natural_observer",
            "depth_context": "lived_in",
        }
    elif guardrail_profile == "lifestyle_permissive":
        preferred_scene_ids = list(_OUTDOOR_COMMERCIAL_SCENES if scene_preference == "outdoor_br" else _INDOOR_COMMERCIAL_SCENES + _OUTDOOR_COMMERCIAL_SCENES[:1])
        avoid_scene_ids = list(_CATALOG_SCENES)
        preferred_camera_ids = list(_NATURAL_CAMERAS)
        avoid_camera_ids = []
        preferred_lighting_ids = list(_NATURAL_LIGHTING)
        avoid_lighting_ids = ["clean_showroom"]
        preferred_casting_family_ids = list(_NATURAL_CASTING)
        avoid_casting_family_ids = []
        preferred_pose_ids = list(_BALANCED_POSE_IDS if spatially_sensitive else _MOVEMENT_POSE_IDS + _BALANCED_POSE_IDS[:2])
        avoid_pose_ids = [] if not spatially_sensitive else ["walking_stride_controlled", "twist_step_forward"]
        scene_constraints = {
            "context_rigidity": "open",
            "backdrop_mode": _SCENE_AFFINITY.get(scene_preference, "auto_br"),
            "allow_context_invention": True,
            "environment_competition": "medium",
        }
        pose_constraints = {
            "movement_budget": "high" if not spatially_sensitive else "medium",
            "frontality_bias": "free",
            "occlusion_tolerance": "medium",
            "gesture_range": "open",
            "silhouette_priority": "high" if spatially_sensitive else "medium",
        }
        capture_constraints = {
            "camera_language": "natural_commercial",
            "framing_priority": "readability_with_context",
            "angle_bias": "observer_or_slight_angle",
            "depth_context": "ambient",
        }
    else:
        preferred_scene_ids = list(_OUTDOOR_COMMERCIAL_SCENES if scene_preference == "outdoor_br" else _INDOOR_COMMERCIAL_SCENES)
        avoid_scene_ids = list(_CATALOG_SCENES) if scene_preference == "outdoor_br" else []
        preferred_camera_ids = list(_COMMERCIAL_CAMERAS if guardrail_profile == "editorial_controlled" else _NATURAL_CAMERAS)
        avoid_camera_ids = []
        preferred_lighting_ids = list(_EDITORIAL_LIGHTING if guardrail_profile == "editorial_controlled" else _NATURAL_LIGHTING)
        avoid_lighting_ids = ["clean_showroom"] if guardrail_profile != "editorial_controlled" else []
        preferred_casting_family_ids = list(_PREMIUM_CASTING if guardrail_profile == "editorial_controlled" else _NATURAL_CASTING)
        avoid_casting_family_ids = []
        preferred_pose_ids = list(_BALANCED_POSE_IDS)
        avoid_pose_ids = ["walking_stride_controlled", "twist_step_forward"] if spatially_sensitive else []
        scene_constraints = {
            "context_rigidity": "guided",
            "backdrop_mode": _SCENE_AFFINITY.get(scene_preference, "auto_br"),
            "allow_context_invention": True,
            "environment_competition": "low" if guardrail_profile == "natural_commercial" else "medium",
        }
        pose_constraints = {
            "movement_budget": movement_budget,
            "frontality_bias": frontality_bias,
            "occlusion_tolerance": occlusion_tolerance,
            "gesture_range": "controlled" if guardrail_profile == "editorial_controlled" else "human",
            "silhouette_priority": "high" if spatially_sensitive else "medium",
        }
        capture_constraints = {
            "camera_language": "fashion_controlled" if guardrail_profile == "editorial_controlled" else "natural_commercial",
            "framing_priority": "product_first",
            "angle_bias": "slight_angle" if guardrail_profile == "editorial_controlled" else "observer",
            "depth_context": "restrained",
        }

    if _lighting_signature_policy_enabled() and lighting_style == "flat_catalog":
        preferred_camera_ids = dedupe_preserve_order(["canon_balanced", *preferred_camera_ids])
        preferred_lighting_ids = dedupe_preserve_order(["clean_showroom", "window_daylight", *preferred_lighting_ids])
        avoid_lighting_ids = dedupe_preserve_order(["golden_hour_soft", "coastal_late_morning", *avoid_lighting_ids])
    elif _lighting_signature_policy_enabled() and integration_risk == "high":
        preferred_camera_ids = dedupe_preserve_order(["canon_balanced", "sony_documentary", *preferred_camera_ids])
        avoid_camera_ids = dedupe_preserve_order(["phone_clean", "fujifilm_candid", *avoid_camera_ids])

    identity_guard = derive_reference_guard_bundle(
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
        mode=preset,
    )

    return {
        "preferred_scene_ids": dedupe_preserve_order(preferred_scene_ids),
        "avoid_scene_ids": dedupe_preserve_order(avoid_scene_ids),
        "preferred_camera_ids": dedupe_preserve_order(preferred_camera_ids),
        "avoid_camera_ids": dedupe_preserve_order(avoid_camera_ids),
        "preferred_lighting_ids": dedupe_preserve_order(preferred_lighting_ids),
        "avoid_lighting_ids": dedupe_preserve_order(avoid_lighting_ids),
        "preferred_casting_family_ids": dedupe_preserve_order(preferred_casting_family_ids),
        "avoid_casting_family_ids": dedupe_preserve_order(avoid_casting_family_ids),
        "preferred_pose_ids": dedupe_preserve_order(preferred_pose_ids),
        "avoid_pose_ids": dedupe_preserve_order(avoid_pose_ids),
        "ugc_intent": ugc_intent,
        "identity_guard": identity_guard,
        "scene_constraints": scene_constraints,
        "pose_constraints": pose_constraints,
        "capture_constraints": capture_constraints,
        "movement_budget": pose_constraints["movement_budget"],
        "frontality_bias": pose_constraints["frontality_bias"],
        "occlusion_tolerance": pose_constraints["occlusion_tolerance"],
    }
