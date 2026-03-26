from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.casting_engine import select_brazilian_casting_profile
from agent_runtime.mode_profile import resolve_operational_profile


def test_select_brazilian_casting_profile_returns_complete_identity_state() -> None:
    state = select_brazilian_casting_profile(
        seed_hint="natural:test",
        user_prompt="vestido midi feminino de linho verde oliva para ecommerce",
        preferred_family_ids=["br_everyday_natural", "br_social_creator"],
        commit=False,
        operational_profile=resolve_operational_profile(mode_id="natural").to_dict(),
    )

    assert state["family_id"]
    assert state["age"]
    assert state["skin"]
    assert state["face_structure"]
    assert state["hair"]
    assert state["presence"]
    assert state["signature"]


def test_select_brazilian_casting_profile_uses_operational_profile_to_bias_family() -> None:
    catalog = select_brazilian_casting_profile(
        seed_hint="same-seed",
        user_prompt="vestido midi feminino para ecommerce",
        commit=False,
        operational_profile=resolve_operational_profile(mode_id="catalog_clean").to_dict(),
    )
    natural = select_brazilian_casting_profile(
        seed_hint="same-seed",
        user_prompt="vestido midi feminino para ecommerce",
        commit=False,
        operational_profile=resolve_operational_profile(mode_id="natural").to_dict(),
    )

    assert catalog["family_id"] in {"br_minimal_premium", "br_warm_commercial", "br_afro_modern", "br_mature_elegant"}
    assert natural["family_id"] in {
        "br_everyday_natural",
        "br_everyday_afro",
        "br_everyday_mature",
        "br_social_creator",
        "br_social_afro",
        "br_social_mature",
        "br_warm_commercial",
    }
