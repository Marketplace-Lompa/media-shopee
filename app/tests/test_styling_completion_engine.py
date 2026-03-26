from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.styling_completion_engine import select_styling_completion_state
from agent_runtime.mode_profile import resolve_operational_profile


def test_select_styling_completion_state_returns_complete_latent_styling_coordinates() -> None:
    state = select_styling_completion_state(
        mode_id="natural",
        framing_profile="full_body",
        scenario_pool="residential_daylight",
        user_prompt="vestido midi feminino de linho verde oliva para ecommerce",
        seed_hint="natural:test",
    )

    assert state["completion_level"]
    assert state["footwear_strategy"]
    assert state["accessory_restraint"]
    assert state["look_finish"]
    assert state["styling_interference"]
    assert state["hero_balance"]
    assert state["footwear_required"] is True
    assert state["styling_signature"]


def test_select_styling_completion_state_changes_with_mode_and_garment() -> None:
    dress = select_styling_completion_state(
        mode_id="natural",
        framing_profile="full_body",
        scenario_pool="neighborhood_commercial",
        user_prompt="vestido midi feminino com manga bufante e saia evasê",
        seed_hint="dress",
    )
    blazer = select_styling_completion_state(
        mode_id="catalog_clean",
        framing_profile="full_body",
        scenario_pool="studio_minimal",
        user_prompt="blazer feminino estruturado com lapela clássica e ombros marcados",
        seed_hint="blazer",
    )

    assert dress["footwear_strategy"] != blazer["footwear_strategy"]
    assert dress["look_finish"] != blazer["look_finish"]


def test_select_styling_completion_state_allows_barefoot_only_when_brief_explicitly_requests_it() -> None:
    state = select_styling_completion_state(
        mode_id="natural",
        framing_profile="full_body",
        scenario_pool="residential_daylight",
        user_prompt="vestido midi de linho descalço para ecommerce",
        seed_hint="barefoot",
    )

    assert state["footwear_required"] is False


def test_select_styling_completion_state_uses_operational_profile_to_bias_finish() -> None:
    catalog = select_styling_completion_state(
        mode_id="catalog_clean",
        framing_profile="full_body",
        scenario_pool="studio_minimal",
        user_prompt="vestido midi feminino para ecommerce",
        seed_hint="same-seed",
        operational_profile=resolve_operational_profile(mode_id="catalog_clean").to_dict(),
    )
    editorial = select_styling_completion_state(
        mode_id="editorial_commercial",
        framing_profile="editorial_mid",
        scenario_pool="architecture_premium",
        user_prompt="vestido midi feminino para ecommerce",
        seed_hint="same-seed",
        operational_profile=resolve_operational_profile(mode_id="editorial_commercial").to_dict(),
    )

    assert any(token in catalog["look_finish"] for token in ("clean", "quiet", "commercial"))
    assert any(token in editorial["look_finish"] for token in ("fashion", "refined", "intentional", "editorial"))
