from __future__ import annotations

import os
from typing import Any, Optional, TypedDict

from agent_runtime.mode_identity_soul import get_mode_soul_statement
from agent_runtime.structural import (
    is_selfie_capture_compatible,
    is_spatially_sensitive_garment,
)


_SCENE_AFFINITY: dict[str, str] = {
    "auto_br": "",
    "indoor_br": "indoor brazilian apartment loft showroom",
    "outdoor_br": "outdoor brazilian street balcony boardwalk architecture",
}

POSE_FLEX_HINTS: dict[str, str] = {
    "controlled": "stable catalog pose with low occlusion and clear front garment readability",
    "balanced": "natural varied pose with mild movement while keeping silhouette readability",
    "dynamic": "dynamic lifestyle pose with stride, half-turn, or gesture while preserving garment geometry",
}
POSE_FLEX_MODES = {"auto", "controlled", "balanced", "dynamic"}

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


def build_affinity_prompt(
    user_prompt: Optional[str],
    mode: str,
    scene_preference: str,
) -> Optional[str]:
    parts = []
    if user_prompt and user_prompt.strip():
        parts.append(user_prompt.strip())
    mode_soul = get_mode_soul_statement(mode)
    if mode_soul:
        parts.append(mode_soul)
    scene_kw = _SCENE_AFFINITY.get(scene_preference, "")
    if scene_kw:
        parts.append(scene_kw)
    return " ".join(parts) if parts else None


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


def derive_reference_guard_config(
    *,
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
) -> tuple[str, list[str]]:
    stats = selector_stats or {}
    risk = str(stats.get("identity_reference_risk", "low") or "low").strip().lower()
    if str(fidelity_mode).strip().lower() == "estrita":
        guard = "strict"
    elif risk == "high":
        guard = "high"
    elif risk == "medium":
        guard = "strict"
    else:
        guard = "standard"
    rules = [
        "References are visual evidence for garment fidelity only.",
        "Do not copy any human identity traits from references.",
    ]
    if risk in {"medium", "high"}:
        rules.append("Prioritize detail anchors and identity-safe references over worn references when conflicts appear.")
    if risk == "high":
        rules.append("If a reference has a visible face, treat that face as forbidden content for transfer.")
    return guard, rules


def resolve_auto_pose_flex_mode(
    *,
    user_prompt: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
    mode: str = "natural",
) -> str:
    text = str(user_prompt or "").strip().lower()
    spatially_sensitive = is_spatially_sensitive_garment(
        structural_contract,
        selector_stats=selector_stats,
    )

    if any(token in text for token in ("tradicional", "catalog", "catálogo", "estavel", "estável", "parada", "static", "still")):
        return "controlled"
    if any(token in text for token in ("movimento", "dinam", "walking", "stride", "editorial", "lookbook", "fashion pose", "criativa", "creative")):
        return "dynamic"

    if str(fidelity_mode).strip().lower() == "estrita":
        return "controlled"
    if spatially_sensitive:
        return "balanced"
    return "dynamic"


def normalize_pose_flex_mode(raw_mode: Optional[str]) -> str:
    mode = str(raw_mode or "auto").strip().lower()
    if mode in POSE_FLEX_MODES:
        return mode
    return "auto"


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
    pose_flex_mode: str,
    selector_stats: Optional[dict[str, Any]] = None,
    structural_contract: Optional[dict[str, Any]] = None,
) -> ArtDirectionSelectionPolicy:
    stats = selector_stats or {}
    text = " ".join(
        part for part in [
            str(user_prompt or "").strip(),
            image_analysis_hint,
            structural_hint,
            preset,
            scene_preference,
            fidelity_mode,
            pose_flex_mode,
        ]
        if part
    ).lower()

    strict_mode = str(fidelity_mode).strip().lower() == "estrita"
    ugc_like = any(
        token in text for token in ("ugc", "cliente real", "review real", "depoimento", "social proof")
    )
    premium_like = not ugc_like and (preset in {"editorial_commercial", "catalog_clean"} or any(
        token in text for token in ("premium", "editorial", "catalog", "sofistic", "ensaio")
    ))
    outdoor_like = scene_preference == "outdoor_br" or any(
        token in text for token in ("outdoor", "balcony", "street", "boardwalk", "coastal", "architecture")
    )
    detail_sensitive_garment = any(
        token in text for token in ("crochet", "knit", "textured", "ruana", "poncho", "cape", "kimono", "modal", "pullover")
    )
    complex_garment = bool(stats.get("complex_garment"))
    wants_selfie = any(token in text for token in ("selfie", "mirror selfie", "espelho", "mirror", "provador", "fitting room"))
    wants_boutique = any(token in text for token in ("boutique", "loja", "store", "provador", "fitting room"))
    wants_creator_energy = any(token in text for token in ("influencer", "creator", "criadora", "cativante", "impactante", "expressiv", "social-commerce", "social"))
    identity_risk = str(stats.get("identity_reference_risk", "low") or "low").strip().lower()
    front_opening = str((structural_contract or {}).get("front_opening", "") or "").strip().lower()
    spatially_sensitive = is_spatially_sensitive_garment(
        structural_contract,
        set_detection=None,
        selector_stats=selector_stats,
    )
    selfie_compatible = is_selfie_capture_compatible(
        structural_contract,
        selector_stats=selector_stats,
    )
    lighting = lighting_signature if isinstance(lighting_signature, dict) else {}
    lighting_style = str(lighting.get("source_style", "") or "").strip().lower()
    light_hardness = str(lighting.get("light_hardness", "") or "").strip().lower()
    light_direction = str(lighting.get("light_direction", "") or "").strip().lower()
    integration_risk = str(lighting.get("integration_risk", "") or "").strip().lower()
    contrast_level = str(lighting.get("contrast_level", "") or "").strip().lower()
    ugc_intent = "none"
    if ugc_like:
        if wants_selfie and selfie_compatible:
            ugc_intent = "mirror_tryon"
        elif wants_boutique or wants_creator_energy:
            ugc_intent = "boutique_creator"
        elif any(token in text for token in ("review", "provando", "mostrando", "look do dia", "recomend", "depoimento")):
            ugc_intent = "friend_shot_review"
        elif any(token in text for token in ("casa", "quarto", "closet", "apartamento", "janela")):
            ugc_intent = "at_home_creator"
        elif spatially_sensitive:
            ugc_intent = "boutique_creator"
        else:
            ugc_intent = "friend_shot_review"

    scene_preferred: list[str] = []
    scene_avoid: list[str] = []
    camera_preferred: list[str] = []
    camera_avoid: list[str] = []
    lighting_preferred: list[str] = []
    lighting_avoid: list[str] = []
    casting_preferred: list[str] = []
    casting_avoid: list[str] = []
    pose_preferred: list[str] = []
    pose_avoid: list[str] = []

    if ugc_like:
        scene_avoid.extend(["br_showroom_sp", "br_bh_rooftop_lounge", "br_rio_art_loft", "br_brasilia_concrete_gallery"])
        lighting_preferred.extend(["open_shade_daylight", "cloudy_tropical", "window_daylight", "overcast_cafe", "mixed_window_lamp", "phone_practical_mixed"])
        lighting_avoid.extend(["clean_showroom"])

        casting_preferred.extend([
            "br_social_creator",
            "br_morena_clara",
            "br_nordestina",
            "br_everyday_natural",
            "br_mulata_cacheada",
            "br_cabocla",
            "br_warm_commercial",
            "br_soft_editorial",
            "br_loira_natural",
            "br_afro",
        ])
        casting_avoid.extend(["br_minimal_premium", "br_mature_elegante"])
        if strict_mode or detail_sensitive_garment:
            if selfie_compatible:
                camera_preferred.extend(["phone_front_selfie", "phone_cameraroll", "phone_direct_flash", "sony_documentary", "fujifilm_candid"])
            else:
                camera_preferred.extend(["phone_cameraroll", "sony_documentary", "fujifilm_candid", "canon_balanced"])
        else:
            camera_preferred.extend(["phone_front_selfie", "phone_cameraroll", "phone_direct_flash", "phone_clean", "sony_documentary", "fujifilm_candid", "nikon_street"])
            camera_avoid.append("canon_balanced")
        if scene_preference == "indoor_br":
            scene_preferred.extend(["br_boutique_floor", "br_fitting_room_mirror", "br_elevator_mirror", "br_condo_hallway", "br_bedroom_window", "br_curitiba_cafe"])
            if selfie_compatible:
                lighting_preferred.append("phone_flash_direct")
        elif scene_preference == "outdoor_br":
            scene_preferred.extend(["br_bairro_sidewalk", "br_salvador_colonial_street", "br_floripa_boardwalk", "br_recife_balcony"])
        else:
            scene_preferred.extend([
                "br_boutique_floor",
                "br_fitting_room_mirror",
                "br_elevator_mirror",
                "br_condo_hallway",
                "br_bedroom_window",
                "br_curitiba_cafe",
                "br_bairro_sidewalk",
                "br_salvador_colonial_street",
                "br_floripa_boardwalk",
                "br_recife_balcony",
            ])

        if wants_creator_energy:
            casting_preferred = dedupe_preserve_order([
                "br_social_creator",
                "br_morena_clara",
                "br_loira_natural",
                *casting_preferred,
            ])

        if wants_boutique:
            scene_preferred = dedupe_preserve_order([
                "br_boutique_floor",
                "br_fitting_room_mirror",
                "br_elevator_mirror",
                *scene_preferred,
            ])
            lighting_preferred = dedupe_preserve_order([
                "phone_practical_mixed",
                "phone_flash_direct",
                "window_daylight",
                *lighting_preferred,
            ])
            pose_preferred.extend(["influencer_hip_pop", "shoulder_turn_smile", "one_hand_hair_glance", "phone_low_hand_snapshot"])

        if wants_selfie and selfie_compatible:
            scene_preferred = dedupe_preserve_order([
                "br_fitting_room_mirror",
                "br_elevator_mirror",
                "br_boutique_floor",
                *scene_preferred,
            ])
            camera_preferred = dedupe_preserve_order([
                "phone_front_selfie",
                "phone_direct_flash",
                "phone_cameraroll",
                *camera_preferred,
            ])
            lighting_preferred = dedupe_preserve_order([
                "phone_flash_direct",
                "phone_practical_mixed",
                *lighting_preferred,
            ])
            pose_preferred.extend(["mirror_selfie_offset", "one_hand_hair_glance", "influencer_hip_pop"])
            pose_avoid.extend(["standing_3q_relaxed", "front_relaxed_hold"])

        if ugc_intent == "mirror_tryon":
            scene_preferred = dedupe_preserve_order([
                "br_fitting_room_mirror",
                "br_elevator_mirror",
                "br_boutique_floor",
                *scene_preferred,
            ])
            camera_preferred = dedupe_preserve_order([
                "phone_front_selfie",
                "phone_direct_flash",
                "phone_cameraroll",
                *camera_preferred,
            ])
            lighting_preferred = dedupe_preserve_order([
                "phone_flash_direct",
                "phone_practical_mixed",
                *lighting_preferred,
            ])
            pose_preferred.extend(["mirror_selfie_offset", "one_hand_hair_glance", "influencer_hip_pop", "shoulder_turn_smile"])
            pose_avoid.extend(["standing_3q_relaxed", "front_relaxed_hold"])
        elif ugc_intent == "boutique_creator":
            scene_preferred = [
                "br_boutique_floor",
                "br_fitting_room_mirror",
                "br_elevator_mirror",
            ]
            camera_preferred = dedupe_preserve_order([
                "phone_cameraroll",
                "phone_direct_flash",
                *(["phone_front_selfie"] if selfie_compatible else []),
            ])
            lighting_preferred = dedupe_preserve_order([
                "phone_practical_mixed",
                "phone_flash_direct",
                "window_daylight",
            ])
            if spatially_sensitive or front_opening == "open":
                pose_preferred = dedupe_preserve_order([
                    "phone_low_hand_snapshot",
                    "shoulder_turn_smile",
                    "doorway_pause_candid",
                    "half_turn_lookback",
                ])
                pose_avoid.extend(["mirror_selfie_offset", "walking_stride_controlled", "standing_full_shift", "front_relaxed_hold", "standing_3q_relaxed"])
            else:
                pose_preferred = dedupe_preserve_order([
                    "influencer_hip_pop",
                    "shoulder_turn_smile",
                    "one_hand_hair_glance",
                    "phone_low_hand_snapshot",
                    "mirror_selfie_offset",
                    "half_turn_lookback",
                    "casual_walkby_glance",
                    "doorway_pause_candid",
                ])
                pose_avoid.extend(["standing_full_shift", "front_relaxed_hold", "soft_wall_lean"])
        elif ugc_intent == "friend_shot_review":
            scene_preferred = dedupe_preserve_order([
                "br_boutique_floor",
                "br_condo_hallway",
                "br_curitiba_cafe",
                "br_bedroom_window",
                "br_bairro_sidewalk",
                *scene_preferred,
            ])
            camera_preferred = dedupe_preserve_order([
                "phone_cameraroll",
                "phone_clean",
                "sony_documentary",
                *camera_preferred,
            ])
            pose_preferred.extend(["phone_low_hand_snapshot", "shoulder_turn_smile", "doorway_pause_candid", "casual_walkby_glance", "half_turn_lookback", "paused_mid_step", "one_hand_hair_glance", "influencer_hip_pop"])
        elif ugc_intent == "at_home_creator":
            scene_preferred = dedupe_preserve_order([
                "br_bedroom_window",
                "br_pinheiros_living",
                "br_condo_hallway",
                *scene_preferred,
            ])
            camera_preferred = dedupe_preserve_order([
                "phone_cameraroll",
                "phone_direct_flash",
                "phone_clean",
                *camera_preferred,
            ])
            pose_preferred.extend(["one_hand_hair_glance", "phone_low_hand_snapshot", "shoulder_turn_smile", "doorway_pause_candid", "casual_walkby_glance", "influencer_hip_pop", "mirror_selfie_offset"])

    if premium_like or ((detail_sensitive_garment or strict_mode) and not ugc_like):
        camera_preferred.extend(["canon_balanced", "sony_documentary", "fujifilm_candid"])
        camera_avoid.append("phone_clean")
        casting_preferred.extend(["br_minimal_premium", "br_soft_editorial", "br_afro", "br_mature_elegante", "br_sulista"])
        if preset != "marketplace_lifestyle":
            casting_avoid.append("br_warm_commercial")

    if outdoor_like and (premium_like or detail_sensitive_garment or strict_mode):
        lighting_preferred.extend(["open_shade_daylight", "cloudy_tropical"])
        lighting_avoid.append("coastal_late_morning")
    elif premium_like or strict_mode:
        lighting_preferred.extend(["window_daylight", "clean_showroom", "mixed_window_lamp"])

    if identity_risk == "high":
        camera_preferred.insert(0, "canon_balanced")
        casting_preferred.extend(["br_mature_elegante", "br_soft_editorial"])

    if _lighting_signature_policy_enabled() and integration_risk == "high":
        camera_preferred = ["canon_balanced", "sony_documentary", *camera_preferred]
        camera_avoid.extend(["phone_clean", "fujifilm_candid"])
        if scene_preference == "outdoor_br":
            scene_preferred.extend(["br_brasilia_concrete_gallery", "br_recife_balcony", "br_floripa_boardwalk"])
            scene_avoid.extend(["br_salvador_colonial_street", "br_bh_rooftop_lounge"])
            lighting_preferred.extend(["open_shade_daylight", "cloudy_tropical"])
            lighting_avoid.extend(["golden_hour_soft", "coastal_late_morning"])
        else:
            scene_preferred.extend(["br_showroom_sp", "br_pinheiros_living", "br_rio_art_loft", "br_porto_alegre_bookstore"])
            scene_avoid.extend(["br_salvador_colonial_street", "br_bh_rooftop_lounge"])
            lighting_preferred.extend(["clean_showroom", "window_daylight", "mixed_window_lamp"])
            lighting_avoid.extend(["golden_hour_soft"])

    if _lighting_signature_policy_enabled() and lighting_style == "flat_catalog":
        camera_preferred = ["canon_balanced", "sony_documentary", *camera_preferred]
        lighting_preferred.extend(["clean_showroom", "window_daylight", "open_shade_daylight"])
        lighting_avoid.extend(["golden_hour_soft", "coastal_late_morning"])
        if scene_preference == "auto_br":
            scene_preferred.extend(["br_showroom_sp", "br_pinheiros_living", "br_brasilia_concrete_gallery"])
    elif _lighting_signature_policy_enabled() and lighting_style == "mixed_interior":
        scene_preferred.extend(["br_pinheiros_living", "br_porto_alegre_bookstore", "br_rio_art_loft"])
        lighting_preferred.extend(["mixed_window_lamp", "window_daylight"])
        lighting_avoid.extend(["coastal_late_morning"])
    elif _lighting_signature_policy_enabled() and lighting_style == "directional_natural":
        camera_preferred.extend(["sony_documentary", "canon_balanced"])
        if scene_preference != "indoor_br":
            lighting_preferred.extend(["open_shade_daylight", "golden_hour_soft"])
    elif _lighting_signature_policy_enabled() and lighting_style == "natural_diffused":
        camera_preferred.extend(["sony_documentary", "fujifilm_candid"])
        lighting_preferred.extend(["open_shade_daylight", "cloudy_tropical", "window_daylight"])

    if _lighting_signature_policy_enabled() and light_hardness == "hard":
        lighting_preferred.extend(["open_shade_daylight", "clean_showroom"])
        lighting_avoid.extend(["mixed_window_lamp"])
    elif _lighting_signature_policy_enabled() and light_hardness == "soft":
        lighting_preferred.extend(["window_daylight", "cloudy_tropical", "mixed_window_lamp"])

    if _lighting_signature_policy_enabled() and light_direction == "frontal" and integration_risk in {"medium", "high"}:
        camera_preferred = ["canon_balanced", "sony_documentary", *camera_preferred]
        lighting_avoid.extend(["golden_hour_soft"])
    elif _lighting_signature_policy_enabled() and light_direction == "side" and contrast_level == "high":
        camera_preferred.extend(["sony_documentary", "fujifilm_candid"])

    if spatially_sensitive or strict_mode:
        if pose_flex_mode == "dynamic":
            pose_preferred.extend(_BALANCED_POSE_IDS if not ugc_like else ["paused_mid_step", "casual_walkby_glance", "standing_3q_relaxed", "half_turn_lookback", "doorway_pause_candid", "shoulder_turn_smile"])
            pose_avoid.extend(["walking_stride_controlled", "twist_step_forward"])
        elif pose_flex_mode == "controlled":
            pose_preferred.extend(_STABLE_POSE_IDS if not ugc_like else ["standing_3q_relaxed", "front_relaxed_hold", "standing_full_shift", "doorway_pause_candid", "phone_low_hand_snapshot", "shoulder_turn_smile"])
            pose_avoid.extend(_MOVEMENT_POSE_IDS if not ugc_like else ["walking_stride_controlled", "twist_step_forward", "contrapposto_editorial", "mirror_selfie_offset"])
        else:
            pose_preferred.extend(_BALANCED_POSE_IDS if not ugc_like else ["standing_3q_relaxed", "paused_mid_step", "casual_walkby_glance", "half_turn_lookback", "standing_full_shift", "front_relaxed_hold", "doorway_pause_candid", "shoulder_turn_smile"])
            pose_avoid.extend(["walking_stride_controlled"])
    elif pose_flex_mode == "controlled":
        pose_preferred.extend(_STABLE_POSE_IDS if not ugc_like else ["influencer_hip_pop", "shoulder_turn_smile", "one_hand_hair_glance", "mirror_selfie_offset", "standing_3q_relaxed", "doorway_pause_candid", "phone_low_hand_snapshot", "front_relaxed_hold", "standing_full_shift"])
        pose_avoid.extend(_MOVEMENT_POSE_IDS if not ugc_like else ["walking_stride_controlled", "twist_step_forward", "contrapposto_editorial"])
    elif pose_flex_mode == "dynamic":
        pose_preferred.extend(_MOVEMENT_POSE_IDS if not ugc_like else ["mirror_selfie_offset", "influencer_hip_pop", "shoulder_turn_smile", "one_hand_hair_glance", "phone_low_hand_snapshot", "paused_mid_step", "casual_walkby_glance", "half_turn_lookback", "standing_3q_relaxed"])

    if ugc_like:
        pose_avoid.extend(["contrapposto_editorial", "soft_wall_lean"])
        if not spatially_sensitive:
            pose_avoid.extend(["front_relaxed_hold"])
        if spatially_sensitive or str((structural_contract or {}).get("front_opening", "") or "").strip().lower() == "open":
            pose_avoid.extend(["mirror_selfie_offset"])

    # Apply indoor/outdoor lighting compatibility after scene candidates are fully assembled.
    _indoor_scene_ids = {
        "br_boutique_floor",
        "br_fitting_room_mirror",
        "br_elevator_mirror",
        "br_condo_hallway",
        "br_bedroom_window",
        "br_pinheiros_living",
        "br_curitiba_cafe",
        "br_porto_alegre_bookstore",
        "br_rio_art_loft",
        "br_showroom_sp",
    }
    _outdoor_only_lighting = {"coastal_late_morning", "golden_hour_soft"}
    _top_scene_ids = dedupe_preserve_order(scene_preferred)[:3]
    if _top_scene_ids and all(sid in _indoor_scene_ids for sid in _top_scene_ids):
        lighting_avoid.extend(list(_outdoor_only_lighting))

    return {
        "preferred_scene_ids": dedupe_preserve_order(scene_preferred),
        "avoid_scene_ids": dedupe_preserve_order(scene_avoid),
        "preferred_camera_ids": dedupe_preserve_order(camera_preferred),
        "avoid_camera_ids": dedupe_preserve_order(camera_avoid),
        "preferred_lighting_ids": dedupe_preserve_order(lighting_preferred),
        "avoid_lighting_ids": dedupe_preserve_order(lighting_avoid),
        "preferred_casting_family_ids": dedupe_preserve_order(casting_preferred),
        "avoid_casting_family_ids": dedupe_preserve_order(casting_avoid),
        "preferred_pose_ids": dedupe_preserve_order(pose_preferred),
        "avoid_pose_ids": dedupe_preserve_order(pose_avoid),
        "ugc_intent": ugc_intent,
    }
