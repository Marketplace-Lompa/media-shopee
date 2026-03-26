from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.coordination_engine import select_coordination_state
from agent_runtime.mode_profile import resolve_operational_profile


def test_select_coordination_state_returns_unified_art_direction_coordinates() -> None:
    state = select_coordination_state(
        mode_id="catalog_clean",
        casting_state={"presence": "polished commercial presence"},
        scene_state={"emotional_register": "clean premium restraint", "background_density": "very low interference"},
        capture_state={"capture_feel": "clean commercial precision", "subject_separation": "soft subject separation"},
        pose_state={"gesture_intention": "quiet premium composure", "stance_logic": "rooted catalog stance"},
        styling_state={"look_finish": "quiet premium catalog finish", "hero_balance": "garment remains the hero while the look feels resolved"},
    )

    assert state["master_intent"] == "quiet premium catalog clarity"
    assert state["presence_world_fusion"]
    assert state["camera_body_fusion"]
    assert state["styling_world_balance"]
    assert state["garment_priority_rule"]
    assert state["visual_tension"]
    assert state["synthesis_rule"]
    assert state["bridge_clause"]
    assert state["coordination_signature"]


def test_select_coordination_state_reads_operational_profile_and_preset_scope() -> None:
    profile = resolve_operational_profile(
        mode_id="natural",
        preset_patch="urban_sidewalk_morning",
    ).to_dict()
    state = select_coordination_state(
        mode_id="natural",
        casting_state={"presence": "relatable everyday Brazilian presence"},
        scene_state={"emotional_register": "calm everyday polish", "background_density": "controlled domestic detail"},
        capture_state={"capture_feel": "natural digital commercial feel", "subject_separation": "gentle natural depth"},
        pose_state={"gesture_intention": "relaxed human presence", "stance_logic": "grounded relaxed stance with breathable body space"},
        styling_state={"look_finish": "natural complete look without overstyling", "hero_balance": "garment remains the hero while the look feels resolved"},
        operational_profile=profile,
    )

    assert state["guardrail_profile"] == "natural_commercial"
    assert state["preset_scope"] == "scene-first"
    assert "scene-first bias" in state["synthesis_rule"]
    assert "setting may lead" in state["bridge_clause"].lower()
