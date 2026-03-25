from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_result import finalize_prompt_agent_result


def test_finalize_prompt_agent_result_enriches_prompt_fields() -> None:
    result = finalize_prompt_agent_result(
        result={
            "base_prompt": "RAW photo, premium fashion catalog shot of a knit top.",
            "camera_and_realism": "85mm lens, realistic studio lighting",
            "shot_type": "medium",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="foto premium",
        structural_contract={},
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="text_mode",
        aspect_ratio="4:5",
        pose="standing pose",
        grounding_pose_clause="",
        profile="profile anchor",
        scenario="studio scene",
        diversity_target=None,
    )

    assert result["prompt"]
    assert result["camera_and_realism"]
    assert result["prompt_compiler_debug"]["final_words"] > 0


def test_finalize_prompt_agent_result_does_not_duplicate_model_presence_when_profile_hint_exists() -> None:
    result = finalize_prompt_agent_result(
        result={
            "base_prompt": "RAW photo, a Brazilian fashion model with a warm commercial presence wearing an olive green linen dress.",
            "camera_and_realism": "Sony A7III, 85mm lens, soft natural light, visible pores.",
            "shot_type": "medium",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="vestido verde para ecommerce",
        structural_contract={},
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="text_mode",
        aspect_ratio="4:5",
        pose="relaxed stance",
        grounding_pose_clause="",
        profile="A Brazilian fashion model with a warm, naturally commercial presence; features blend 'Ana' and 'Lia Costa'.",
        scenario="residential interior",
        diversity_target={"profile_id": "natural:commercial_natural"},
        mode_id="natural",
        framing_profile="three_quarter",
        camera_perspective="standard_prime",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="commercial_natural",
    )

    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "quality_model" not in used_sources
    assert "model_profile" not in used_sources
    assert "quality_gaze" in used_sources
    assert "quality_scene" in used_sources
    assert "sony" not in result["camera_and_realism"].lower()
    assert "85mm" not in result["camera_and_realism"].lower()
    assert "golden hour side light" not in result["prompt"].lower()
    assert "gentle bokeh background" not in result["prompt"].lower()


def test_finalize_prompt_agent_result_sanitizes_draped_wrap_narrative() -> None:
    result = finalize_prompt_agent_result(
        result={
            "base_prompt": "RAW photo, premium fashion catalog shot of a knit top.",
            "camera_and_realism": "85mm lens, realistic studio lighting",
            "shot_type": "medium",
            "garment_narrative": "striped crochet cocoon shrug with open front and ribbed collar",
        },
        has_images=True,
        has_prompt=False,
        user_prompt=None,
        structural_contract={
            "enabled": True,
            "garment_subtype": "ruana_wrap",
            "sleeve_type": "cape_like",
            "must_keep": ["continuous neckline-to-front edge"],
        },
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="reference_mode",
        aspect_ratio="4:5",
        pose="standing pose",
        grounding_pose_clause="",
        profile="profile anchor",
        scenario="studio scene",
        diversity_target={"lighting_hint": "soft daylight"},
    )

    assert result["prompt"]
    assert result["prompt_compiler_debug"]["base_budget"] > 0
