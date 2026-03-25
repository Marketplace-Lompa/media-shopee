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
    assert result["camera_profile"]
    assert result["prompt_compiler_debug"]["final_words"] > 0


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
    assert result["prompt_compiler_debug"]["camera_profile"]
    assert result["prompt_compiler_debug"]["base_budget"] > 0
