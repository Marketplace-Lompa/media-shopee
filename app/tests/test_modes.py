from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.modes import (
    DEFAULT_TEXT_MODE,
    describe_mode_defaults,
    get_mode,
    get_mode_profile,
    list_modes,
    list_operational_mode_profiles,
    preferred_shot_type_for_framing,
    preferred_shot_type_for_mode,
    resolve_operational_mode_profile,
    resolve_mode_with_overrides,
)
from agent_runtime.diversity import (
    build_mode_diversity_target,
    harmonize_diversity_target_for_mode,
)


def test_list_modes_returns_v1_modes() -> None:
    ids = [mode.id for mode in list_modes()]
    assert ids == [
        "catalog_clean",
        "natural",
        "lifestyle",
        "editorial_commercial",
    ]


def test_list_operational_mode_profiles_matches_mode_registry() -> None:
    ids = [profile.mode_id for profile in list_operational_mode_profiles()]
    assert ids == [
        "catalog_clean",
        "natural",
        "lifestyle",
        "editorial_commercial",
    ]


def test_get_mode_falls_back_to_default() -> None:
    mode = get_mode("nao_existe")
    assert mode.id == DEFAULT_TEXT_MODE


def test_resolve_mode_with_overrides_changes_only_targeted_presets() -> None:
    mode = resolve_mode_with_overrides(
        "natural",
        {"lighting_profile": "directional_daylight", "camera_type": "commercial_full_frame"},
    )
    assert mode.id == "natural"
    assert mode.presets.scenario_pool == "neighborhood_commercial"
    assert mode.presets.lighting_profile == "directional_daylight"
    assert mode.presets.camera_type == "commercial_full_frame"


def test_preferred_shot_type_follows_mode_framing_profile() -> None:
    assert preferred_shot_type_for_mode("catalog_clean") == "wide"
    assert preferred_shot_type_for_mode("editorial_commercial") == "medium"
    assert preferred_shot_type_for_framing("detail_crop") == "close-up"


def test_describe_mode_defaults_exposes_business_and_preset_context() -> None:
    text = describe_mode_defaults(get_mode("lifestyle"))
    assert "Active visual mode: Lifestyle." in text
    assert "scenario direction:" in text or "scenario constraint:" in text
    assert "camera type:" in text
    assert "capture geometry:" in text
    assert "lighting:" in text


def test_build_mode_diversity_target_uses_valid_mode_preset_pool() -> None:
    target = build_mode_diversity_target(get_mode("lifestyle"))
    presets = target["preset_defaults"]
    assert presets["scenario_pool"] in {
        "textured_city", "nature_open_air", "neighborhood_commercial",
        "beach_coastal", "market_feira", "tropical_garden",
        "cafe_bistro", "rooftop_terrace",
    }
    assert presets["pose_energy"] in {"candid", "relaxed"}
    assert presets["casting_profile"] == "natural_commercial"
    assert presets["framing_profile"] in {"environmental_wide", "three_quarter"}
    assert presets["camera_type"] in {"natural_digital", "phone_social"}
    assert presets["capture_geometry"] in {
        "environmental_wide_observer",
        "three_quarter_slight_angle",
        "three_quarter_eye_level",
    }


def test_natural_pool_prefers_natural_digital_capture_language() -> None:
    target = build_mode_diversity_target(get_mode("natural"))
    presets = target["preset_defaults"]
    assert presets["camera_type"] == "natural_digital"
    assert presets["scenario_pool"] in {
        "residential_daylight", "neighborhood_commercial",
        "nature_open_air", "curated_interior",
        "tropical_garden", "cafe_bistro", "hotel_pousada",
    }
    assert presets["pose_energy"] in {"relaxed", "candid"}


def test_build_mode_diversity_target_uses_abstract_profile_and_presence_axes() -> None:
    target = build_mode_diversity_target(get_mode("natural"))
    profile_hint = str(target["profile_hint"]).lower()
    presence_energy = str(target["presence_energy"]).lower()
    presence_tone = str(target["presence_tone"]).lower()
    casting_state = target["casting_state"]
    scene_state = target["scene_state"]
    capture_state = target["capture_state"]
    pose_state = target["pose_state"]
    styling_state = target["styling_state"]
    coordination_state = target["coordination_state"]
    operational_profile = target["operational_profile"]

    # Name Blending must be present
    assert "features blend" in profile_hint

    # Presence axes must be single words from the pool
    assert presence_energy in {"warm", "fresh", "grounded", "approachable"}
    assert presence_tone in {"believable", "softly-premium", "commercial", "natural"}
    assert casting_state["age"]
    assert casting_state["face_structure"]
    assert casting_state["hair"]
    assert casting_state["signature"]
    assert scene_state["world_family"] in {
        "residential_daylight", "neighborhood_commercial",
        "nature_open_air", "curated_interior",
        "tropical_garden", "cafe_bistro", "hotel_pousada",
    }
    assert scene_state["microcontext"]
    assert scene_state["material_language"]
    assert scene_state["scene_signature"]
    assert capture_state["framing_intent"] in {"three_quarter", "full_body"}
    assert capture_state["camera_family"] == "natural_digital"
    assert capture_state["capture_feel"]
    assert capture_state["garment_priority"]
    assert capture_state["capture_signature"]
    assert pose_state["stance_logic"]
    assert pose_state["surface_direction"]
    assert pose_state["pose_signature"]
    assert styling_state["completion_level"]
    assert styling_state["footwear_strategy"]
    assert styling_state["look_finish"]
    assert styling_state["styling_signature"]
    assert coordination_state["master_intent"]
    assert coordination_state["presence_world_fusion"]
    assert coordination_state["camera_body_fusion"]
    assert coordination_state["coordination_signature"]
    assert operational_profile["mode_id"] == "natural"
    assert operational_profile["engine_weights"]["scene"] > 0
    assert operational_profile["surface_budget"]["subject"] >= 1
    assert operational_profile["guardrail_profile"] == "natural_commercial"
    assert operational_profile["applied_preset_id"] is None

    # Must NOT contain legacy literal phrases
    assert "scenario_prompt" not in target
    assert "pose_prompt" not in target
    assert "lighting_hint" not in target


def test_resolve_operational_mode_profile_keeps_mode_authority_above_patch() -> None:
    profile = resolve_operational_mode_profile("catalog_clean", "soft_wall_daylight")
    base = get_mode_profile("catalog_clean")

    assert profile.mode_id == "catalog_clean"
    assert profile.applied_preset_id == "soft_wall_daylight"
    assert profile.engine_weights.capture > base.engine_weights.scene
    assert profile.guardrail_profile == base.guardrail_profile


def test_mode_scenario_families_are_semantically_contrasted() -> None:
    assert get_mode("catalog_clean").presets.scenario_pool == "studio_minimal"
    assert get_mode("natural").presets.scenario_pool == "neighborhood_commercial"
    assert get_mode("lifestyle").presets.scenario_pool == "textured_city"
    assert get_mode("editorial_commercial").presets.scenario_pool == "architecture_premium"


def test_catalog_clean_pool_is_intentionally_strict() -> None:
    target = build_mode_diversity_target(get_mode("catalog_clean"))
    presets = target["preset_defaults"]
    assert presets["scenario_pool"] == "studio_minimal"
    assert presets["pose_energy"] == "static"
    assert presets["framing_profile"] == "full_body"
    assert presets["camera_type"] == "commercial_full_frame"
    assert presets["capture_geometry"] == "full_body_neutral"
    assert presets["lighting_profile"] == "studio_even"


def test_catalog_clean_defaults_include_complete_styling_guidance() -> None:
    text = describe_mode_defaults(get_mode("catalog_clean"))
    assert "commercially complete" in text
    assert "avoid barefoot" in text


def test_natural_defaults_include_brazil_anchor_and_name_blending_guidance() -> None:
    text = describe_mode_defaults(get_mode("natural"))
    assert "believable for Brazil" in text
    assert "name blending" in text
    assert "never expose preset terminology" in text
    assert "footwear" in text


def test_harmonize_diversity_target_for_mode_upgrades_legacy_reference_shape_without_dropping_metadata() -> None:
    legacy = {
        "profile_id": "legacy_profile_1",
        "profile_prompt": "late 20s, warm Brazilian commercial model",
        "scenario_id": "legacy_scene_1",
        "scenario_prompt": "believable residential interior",
        "pose_id": "legacy_pose_1",
        "pose_prompt": "relaxed standing pose",
        "age_range": "35-44",
        "scene_type": "interno",
        "pose_style": "tradicional",
        "lighting_hint": "soft daylight from a window",
        "diversity_score": 0.78,
    }

    target = harmonize_diversity_target_for_mode(
        get_mode("natural"),
        legacy,
        user_prompt="vestido de linho verde oliva para ecommerce",
    )

    assert target["profile_hint"]
    assert target["casting_state"]["age"] == "late 30s to early 40s"
    assert target["scene_state"]["world_family"] in {
        "residential_daylight", "neighborhood_commercial",
        "nature_open_air", "curated_interior",
        "tropical_garden", "cafe_bistro", "hotel_pousada",
    }
    assert target["capture_state"]["camera_family"] == "natural_digital"
    assert target["pose_state"]["pose_signature"]
    assert target["styling_state"]["look_finish"]
    assert target["coordination_state"]["master_intent"]
    assert target["operational_profile"]["mode_id"] == "natural"
    assert target["lighting_hint"] == "soft daylight from a window"
    assert target["legacy_profile_id"] == "legacy_profile_1"
    assert target["legacy_profile_prompt"] == "late 20s, warm Brazilian commercial model"
    assert target["profile_prompt"] == "late 20s, warm Brazilian commercial model"
