from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.curation_policy import derive_art_direction_selection_policy


def _read(path: str) -> str:
    return (Path(__file__).resolve().parents[1] / "backend" / path).read_text(encoding="utf-8")


def test_indoor_scene_avoids_outdoor_only_lighting_in_selection_policy() -> None:
    policy = derive_art_direction_selection_policy(
        preset="ugc_real_br",
        scene_preference="indoor_br",
        image_analysis_hint="",
        structural_hint="",
        lighting_signature={},
        user_prompt="conteudo de influencer em provador",
        fidelity_mode="balanceada",
        selector_stats={},
        structural_contract={
            "front_opening": "closed",
            "garment_length": "hip",
            "sleeve_type": "set-in",
        },
    )

    avoid = set(policy["avoid_lighting_ids"])
    assert "coastal_late_morning" in avoid
    assert "golden_hour_soft" in avoid
    assert isinstance(policy["ugc_intent"], str)


def test_pipeline_v2_source_keeps_primary_and_applied_prompts_split() -> None:
    src = _read("agent_runtime/pipeline_v2.py")
    assert 'last_primary_edit_prompt = ""' in src
    assert 'last_applied_edit_prompt = ""' in src
    assert '"optimized_prompt": last_primary_edit_prompt or stage1_prompt' in src
    assert '"edit_prompt": last_applied_edit_prompt or last_primary_edit_prompt or stage1_prompt' in src


def test_user_intent_propagation_and_strict_mode_no_skip_marker() -> None:
    support_src = _read("agent_runtime/pipeline_v2_support.py")
    assert '"user_intent": raw.get("user_intent")' in support_src
    assert 'user_intent=payload.get("user_intent")' in support_src
    assert "resolved_preset = preset or raw.get(\"preset\")" in support_src
    assert "resolved_marketplace_channel = marketplace_channel or raw.get(\"marketplace_channel\")" in support_src
    assert "resolved_slot_id = slot_id or raw.get(\"slot_id\")" in support_src

    generate_src = _read("routers/generate.py")
    assert 'strict_user_intent = normalize_user_intent(prompt or "")' in generate_src
    assert '"normalizer_source": "skipped"' not in generate_src
