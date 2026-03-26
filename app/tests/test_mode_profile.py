from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.mode_profile import get_mode_profile, resolve_operational_profile
from agent_runtime.preset_patch import get_preset_patch, list_preset_patches


def test_get_mode_profile_returns_structured_regime_for_catalog_clean() -> None:
    profile = get_mode_profile("catalog_clean")

    assert profile.mode_id == "catalog_clean"
    assert profile.engine_weights.capture > profile.engine_weights.scene
    assert profile.invention_budget < 0.3
    assert profile.surface_budget.scene <= 1
    assert profile.guardrail_profile == "strict_catalog"
    assert profile.hard_rules


def test_resolve_operational_profile_applies_preset_patch_without_replacing_mode() -> None:
    resolved = resolve_operational_profile(
        mode_id="natural",
        preset_patch="urban_sidewalk_morning",
    )

    assert resolved.mode_id == "natural"
    assert resolved.applied_preset_id == "urban_sidewalk_morning"
    assert resolved.preset_scope == "scene-first"
    assert resolved.engine_weights.scene > get_mode_profile("natural").engine_weights.scene
    assert resolved.engine_weights.capture > get_mode_profile("natural").engine_weights.capture
    assert "studio backdrop" in resolved.exclusions


def test_preset_patch_registry_exposes_only_allowed_scope_values() -> None:
    patch = get_preset_patch("confident_stride")

    assert patch is not None
    assert patch.scope == "pose-first"
    assert "editorial_commercial" in patch.allowed_modes
    assert list_preset_patches()
