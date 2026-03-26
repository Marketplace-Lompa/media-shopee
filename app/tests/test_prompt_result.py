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
    assert result["camera_and_realism"] == ""
    assert result["prompt_compiler_debug"]["final_words"] > 0


def test_finalize_prompt_agent_result_accepts_prompt_as_canonical_text_mode_field() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a Brazilian fashion model with a relaxed commercial presence wearing an olive green linen midi dress in a believable residential interior.",
            "shot_type": "medium",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="vestido verde oliva para ecommerce",
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
        scenario="believable residential interior with low clutter",
        diversity_target={"profile_id": "natural:natural_commercial"},
        mode_id="natural",
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    assert result["prompt"].startswith("RAW photo,")
    assert result["base_prompt"].startswith("RAW photo,")
    assert result["base_prompt"] == result["prompt"]
    assert result["camera_and_realism"] == ""
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
        diversity_target={"profile_id": "natural:natural_commercial"},
        mode_id="natural",
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "quality_model" not in used_sources
    assert "model_profile" not in used_sources
    assert "quality_gaze" not in used_sources
    assert "quality_scene" not in used_sources
    assert "frame_occupancy" not in used_sources
    assert result["camera_and_realism"] == ""
    assert "golden hour side light" not in result["prompt"].lower()
    assert "gentle bokeh background" not in result["prompt"].lower()


def test_finalize_prompt_agent_result_text_mode_skips_gaze_when_presence_already_exists() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a woman with a warm, commercially natural presence standing in a believable residential interior "
                "wearing an olive green linen midi dress."
            ),
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
        diversity_target={"profile_id": "natural:natural_commercial"},
        mode_id="natural",
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "quality_gaze" not in used_sources


def test_finalize_prompt_agent_result_text_mode_enforces_casting_surface_minimum() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a polished Brazilian woman wearing an olive green linen midi dress in a minimalist studio.",
            "shot_type": "wide",
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
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Ana' and 'Lia Costa'",
        scenario="studio minimal",
        diversity_target={
            "profile_id": "catalog_clean:polished_commercial",
            "casting_state": {
                "age": "early 40s",
                "face_structure": "refined angular cheekbones with a composed jawline",
                "hair": "a sleek jaw-length dark bob with a clean center part",
            },
        },
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    low = result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "early 40s" in low
    assert "cheekbones" in low or "jawline" in low
    assert "bob" in low or "hair" in low
    assert "casting_surface" in used_sources


def test_finalize_prompt_agent_result_text_mode_enforces_specific_pose_surface() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a polished Brazilian woman standing in a minimalist studio wearing an olive green linen midi dress in a stable, commercially-focused pose.",
            "shot_type": "wide",
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
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Ana' and 'Lia Costa'",
        scenario="studio minimal",
        diversity_target={
            "profile_id": "catalog_clean:polished_commercial",
            "pose_state": {
                "surface_direction": "with a grounded stance, a subtle weight shift through one leg, and arms kept quiet so the full silhouette remains clear",
                "gesture_intention": "quiet premium composure",
            },
        },
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    low = result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "weight shift" in low
    assert "arms kept quiet" in low
    assert "pose_surface" in used_sources


def test_finalize_prompt_agent_result_text_mode_skips_casting_fallback_when_age_face_and_hair_already_exist() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her mid-20s with a balanced oval face and soft medium-brown waves "
                "wearing an olive green linen midi dress in a minimalist studio."
            ),
            "shot_type": "wide",
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
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Ana' and 'Lia Costa'",
        scenario="studio minimal",
        diversity_target={
            "profile_id": "catalog_clean:polished_commercial",
            "casting_state": {
                "age": "mid-to-late 20s",
                "face_structure": "balanced oval face with subtle smile lines",
                "hair": "soft medium-brown waves over the shoulders",
            },
        },
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "casting_surface" not in used_sources


def test_finalize_prompt_agent_result_records_coordination_diagnostics() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her late 20s with a balanced oval face and soft medium-brown waves "
                "wearing an olive green linen midi dress in a minimalist studio, while shifting her weight slightly to one side."
            ),
            "shot_type": "wide",
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
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Ana' and 'Lia Costa'",
        scenario="studio minimal",
        diversity_target={"profile_id": "catalog_clean:polished_commercial"},
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    diagnostics = result["prompt_compiler_debug"]["coordination_diagnostics"]
    assert diagnostics["casting_surface_present"] is True
    assert diagnostics["specific_pose_present"] is True
    assert diagnostics["scene_surface_present"] is True
    assert diagnostics["bridge_language_present"] is True


def test_finalize_prompt_agent_result_adds_coordination_bridge_when_prompt_is_decomposed() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her late 20s with a balanced oval face and soft medium-brown waves "
                "wearing an olive green linen midi dress in a minimalist studio. "
                "She stands with a subtle weight shift. "
                "Discreet tan leather sandals complete the look."
            ),
            "shot_type": "wide",
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
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Ana' and 'Lia Costa'",
        scenario="studio minimal",
        diversity_target={
            "profile_id": "catalog_clean:polished_commercial",
            "coordination_state": {
                "bridge_clause": "The restrained setting, grounded stance, and clean capture work together to keep the garment visually primary.",
            },
        },
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    low = result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "work together" in low
    assert "coordination_bridge" in used_sources
    diagnostics = result["prompt_compiler_debug"]["coordination_diagnostics"]
    assert diagnostics["bridge_language_present"] is True
    assert diagnostics["decomposition_risk"] is False
def test_finalize_prompt_agent_result_text_mode_adds_footwear_guardrail_for_full_body_natural() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a full-body natural commercial shot of a woman standing on a quiet neighborhood sidewalk "
                "wearing an olive green linen midi dress."
            ),
            "shot_type": "wide",
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
        scenario="neighborhood commercial",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "styling_state": {
                "footwear_required": True,
                "footwear_strategy": "minimal tan leather sandals",
                "look_finish": "natural complete look without overstyling",
            },
        },
        mode_id="natural",
        framing_profile="full_body",
        camera_type="natural_digital",
        capture_geometry="full_body_neutral",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    assert "minimal tan leather sandals" in result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "styling_completion" in used_sources


def test_finalize_prompt_agent_result_text_mode_respects_explicit_barefoot_brief() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a full-body natural commercial shot of a woman standing indoors "
                "wearing an olive green linen midi dress."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="vestido verde descalço para ecommerce",
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
        diversity_target={"profile_id": "natural:natural_commercial"},
        mode_id="natural",
        framing_profile="full_body",
        camera_type="natural_digital",
        capture_geometry="full_body_neutral",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    assert "sandals" not in result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "styling_completion" not in used_sources


def test_finalize_prompt_agent_result_text_mode_skips_compiler_tail_when_base_already_covers_scene_and_expression() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a full-body commercial catalog shot of a model with a composed expression "
                "standing in a minimalist studio with a neutral backdrop, wearing an olive green linen midi dress."
            ),
            "shot_type": "wide",
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
        pose="stable catalog stance",
        grounding_pose_clause="",
        profile="A Brazilian fashion model with a polished commercial presence; features blend 'Ana' and 'Lia Costa'.",
        scenario="studio minimal",
        diversity_target={"profile_id": "catalog_clean:polished_commercial"},
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "quality_scene" not in used_sources
    assert "frame_occupancy" not in used_sources


def test_finalize_prompt_agent_result_catalog_clean_skips_gaze_tail_in_text_mode() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a full-body commercial catalog shot of a woman standing in a minimalist studio "
                "with a neutral backdrop, wearing an olive green linen midi dress."
            ),
            "shot_type": "wide",
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
        pose="stable catalog stance",
        grounding_pose_clause="",
        profile="A Brazilian fashion model with a polished commercial presence; features blend 'Ana' and 'Lia Costa'.",
        scenario="studio minimal",
        diversity_target={"profile_id": "catalog_clean:polished_commercial"},
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "quality_gaze" not in used_sources


def test_finalize_prompt_agent_result_text_mode_never_reintroduces_gaze_tail_for_sparse_prompt() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a Brazilian woman wearing an olive green linen midi dress.",
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
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Ana' and 'Lia Costa'",
        scenario="residential interior",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "balanced oval face with soft natural asymmetry",
                "hair": "loose dark-brown waves with natural movement",
            },
            "pose_state": {
                "surface_direction": "with a grounded stance, a soft weight shift, and relaxed arms that keep the waistline readable",
            },
        },
        mode_id="natural",
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "quality_gaze" not in used_sources
    assert "casting_surface" in used_sources
    assert "pose_surface" in used_sources


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
    assert result["camera_and_realism"]
    assert result["prompt_compiler_debug"]["base_budget"] > 0
