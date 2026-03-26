from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.capture_engine import select_capture_state
from agent_runtime.mode_profile import resolve_operational_profile


def test_select_capture_state_returns_complete_latent_capture_coordinates() -> None:
    state = select_capture_state(
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_eye_level",
        mode_id="natural",
        user_prompt="vestido midi feminino de linho verde oliva para ecommerce",
        seed_hint="natural:test",
    )

    assert state["framing_intent"] == "three_quarter"
    assert state["camera_family"] == "natural_digital"
    assert state["geometry_intent"] == "three_quarter_eye_level"
    assert state["capture_feel"]
    assert state["lens_language"]
    assert state["subject_separation"]
    assert state["body_relation"]
    assert state["angle_logic"]
    assert state["garment_priority"]
    assert state["capture_signature"]


def test_select_capture_state_changes_priority_with_garment_type() -> None:
    dress = select_capture_state(
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_slight_angle",
        mode_id="natural",
        user_prompt="vestido midi feminino com manga bufante e saia evasê",
        seed_hint="dress",
    )
    blazer = select_capture_state(
        framing_profile="three_quarter",
        camera_type="commercial_full_frame",
        capture_geometry="three_quarter_eye_level",
        mode_id="catalog_clean",
        user_prompt="blazer feminino estruturado com lapela clássica e ombros marcados",
        seed_hint="blazer",
    )

    assert dress["garment_priority"] != blazer["garment_priority"]


def test_select_capture_state_uses_operational_profile_to_bias_capture_language() -> None:
    strict_catalog = resolve_operational_profile(mode_id="catalog_clean").to_dict()
    editorial = resolve_operational_profile(mode_id="editorial_commercial").to_dict()

    catalog = select_capture_state(
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        mode_id="catalog_clean",
        user_prompt="vestido midi feminino para ecommerce",
        seed_hint="same-seed",
        operational_profile=strict_catalog,
    )
    fashion = select_capture_state(
        framing_profile="editorial_mid",
        camera_type="editorial_fashion",
        capture_geometry="editorial_mid_low_angle",
        mode_id="editorial_commercial",
        user_prompt="vestido midi feminino para ecommerce",
        seed_hint="same-seed",
        operational_profile=editorial,
    )

    assert any(token in catalog["capture_feel"] for token in ("controlled", "clean", "neutral"))
    assert any(token in fashion["capture_feel"] for token in ("fashion", "editorial", "intentional"))
