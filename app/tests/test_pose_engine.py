from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.pose_engine import select_pose_state
from agent_runtime.mode_profile import resolve_operational_profile


def test_select_pose_state_returns_complete_latent_pose_coordinates() -> None:
    state = select_pose_state(
        pose_energy="relaxed",
        framing_profile="three_quarter",
        scenario_pool="residential_daylight",
        mode_id="natural",
        user_prompt="vestido midi feminino de linho verde oliva para ecommerce",
        seed_hint="natural:test",
    )

    assert state["pose_family"] == "relaxed"
    assert state["stance_logic"]
    assert state["weight_shift"]
    assert state["arm_logic"]
    assert state["torso_orientation"]
    assert state["head_direction"]
    assert state["gesture_intention"]
    assert state["garment_interaction"]
    assert state["surface_direction"]
    assert state["pose_signature"]


def test_select_pose_state_changes_surface_direction_with_garment_type() -> None:
    dress = select_pose_state(
        pose_energy="relaxed",
        framing_profile="three_quarter",
        scenario_pool="residential_daylight",
        mode_id="natural",
        user_prompt="vestido midi feminino com manga bufante e saia evasê",
        seed_hint="dress",
    )
    blazer = select_pose_state(
        pose_energy="static",
        framing_profile="full_body",
        scenario_pool="studio_minimal",
        mode_id="catalog_clean",
        user_prompt="blazer feminino estruturado com lapela clássica e ombros marcados",
        seed_hint="blazer",
    )

    assert dress["surface_direction"] != blazer["surface_direction"]


def test_select_pose_state_uses_operational_profile_to_bias_pose_family_expression() -> None:
    strict_catalog = resolve_operational_profile(mode_id="catalog_clean").to_dict()
    lifestyle = resolve_operational_profile(mode_id="lifestyle").to_dict()

    catalog = select_pose_state(
        pose_energy="static",
        framing_profile="full_body",
        scenario_pool="studio_minimal",
        mode_id="catalog_clean",
        user_prompt="vestido midi feminino para ecommerce",
        seed_hint="same-seed",
        operational_profile=strict_catalog,
    )
    lived = select_pose_state(
        pose_energy="candid",
        framing_profile="three_quarter",
        scenario_pool="textured_city",
        mode_id="lifestyle",
        user_prompt="vestido midi feminino para ecommerce",
        seed_hint="same-seed",
        operational_profile=lifestyle,
    )

    assert any(token in catalog["gesture_intention"] for token in ("quiet", "controlled", "catalog"))
    assert any(token in lived["gesture_intention"] for token in ("candid", "approachable", "motion", "lived-in"))
