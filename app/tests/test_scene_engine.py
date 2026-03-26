from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.scene_engine import select_scene_state
from agent_runtime.mode_profile import resolve_operational_profile


def test_select_scene_state_returns_complete_latent_world_coordinates() -> None:
    state = select_scene_state(
        scenario_pool="neighborhood_commercial",
        mode_id="natural",
        user_prompt="vestido midi feminino de linho verde oliva para ecommerce",
        seed_hint="natural:test",
    )

    assert state["world_family"] == "neighborhood_commercial"
    assert state["microcontext"]
    assert state["emotional_register"]
    assert state["material_language"]
    assert state["background_density"]
    assert state["brazil_anchor"]
    assert state["scene_signature"]


def test_select_scene_state_is_conditioned_by_known_scenario_pool() -> None:
    residential = select_scene_state(
        scenario_pool="residential_daylight",
        mode_id="natural",
        user_prompt="vestido de linho para ecommerce",
        seed_hint="residential",
    )
    editorial = select_scene_state(
        scenario_pool="architecture_premium",
        mode_id="editorial_commercial",
        user_prompt="blazer estruturado para ecommerce",
        seed_hint="architecture",
    )

    assert residential["world_family"] == "residential_daylight"
    assert editorial["world_family"] == "architecture_premium"
    assert residential["scene_signature"] != editorial["scene_signature"]


def test_select_scene_state_uses_operational_profile_to_bias_density() -> None:
    strict_catalog = resolve_operational_profile(mode_id="catalog_clean").to_dict()
    permissive_lifestyle = resolve_operational_profile(mode_id="lifestyle").to_dict()

    catalog = select_scene_state(
        scenario_pool="studio_minimal",
        mode_id="catalog_clean",
        user_prompt="vestido de linho para ecommerce",
        seed_hint="same-seed",
        operational_profile=strict_catalog,
    )
    lifestyle = select_scene_state(
        scenario_pool="textured_city",
        mode_id="lifestyle",
        user_prompt="vestido de linho para ecommerce",
        seed_hint="same-seed",
        operational_profile=permissive_lifestyle,
    )

    assert any(token in catalog["background_density"] for token in ("low", "restrained", "absent"))
    assert any(token in lifestyle["background_density"] for token in ("medium", "active", "airy", "textured"))
