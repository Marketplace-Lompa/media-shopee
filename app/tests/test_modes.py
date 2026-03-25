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
    list_modes,
    preferred_shot_type_for_framing,
    preferred_shot_type_for_mode,
    resolve_mode_with_overrides,
)
from agent_runtime.diversity import build_mode_diversity_target


def test_list_modes_returns_v1_modes() -> None:
    ids = [mode.id for mode in list_modes()]
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
        {"lighting_profile": "ambient_mixed", "camera_perspective": "wide_environmental"},
    )
    assert mode.id == "natural"
    assert mode.presets.scenario_pool == "residential_daylight"
    assert mode.presets.lighting_profile == "ambient_mixed"
    assert mode.presets.camera_perspective == "wide_environmental"


def test_preferred_shot_type_follows_mode_framing_profile() -> None:
    assert preferred_shot_type_for_mode("catalog_clean") == "wide"
    assert preferred_shot_type_for_mode("editorial_commercial") == "medium"
    assert preferred_shot_type_for_framing("detail_crop") == "close-up"


def test_describe_mode_defaults_exposes_business_and_preset_context() -> None:
    text = describe_mode_defaults(get_mode("lifestyle"))
    assert "Active visual mode: Lifestyle." in text
    assert "scenario family:" in text
    assert "camera perspective:" in text
    assert "lighting:" in text


def test_build_mode_diversity_target_uses_valid_mode_preset_pool() -> None:
    target = build_mode_diversity_target(get_mode("lifestyle"))
    presets = target["preset_defaults"]
    assert presets["scenario_pool"] in {"textured_city", "nature_open_air", "neighborhood_commercial"}
    assert presets["pose_energy"] in {"candid", "dynamic"}
    assert presets["casting_profile"] in {"commercial_natural", "casual_relational"}
    assert presets["framing_profile"] in {"environmental_wide", "editorial_mid"}
    assert presets["camera_perspective"] == "wide_environmental"


def test_build_mode_diversity_target_uses_abstract_profile_and_presence_axes() -> None:
    target = build_mode_diversity_target(get_mode("natural"))
    profile_hint = str(target["profile_hint"]).lower()
    presence_energy = str(target["presence_energy"]).lower()
    presence_tone = str(target["presence_tone"]).lower()

    # Name Blending must be present
    assert "features blend" in profile_hint

    # Presence axes must be single words from the pool
    assert presence_energy in {"warm", "fresh", "grounded", "approachable"}
    assert presence_tone in {"believable", "softly-premium", "commercial", "natural"}

    # Must NOT contain legacy literal phrases
    assert "scenario_prompt" not in target
    assert "pose_prompt" not in target
    assert "lighting_hint" not in target


def test_mode_scenario_families_are_semantically_contrasted() -> None:
    assert get_mode("catalog_clean").presets.scenario_pool == "studio_minimal"
    assert get_mode("natural").presets.scenario_pool == "residential_daylight"
    assert get_mode("lifestyle").presets.scenario_pool == "textured_city"
    assert get_mode("editorial_commercial").presets.scenario_pool == "architecture_premium"
