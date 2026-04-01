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


def test_finalize_prompt_agent_result_reference_mode_softens_casting_surface_minimum() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a charismatic Brazilian woman wearing the referenced knit top in a believable refined interior.",
            "shot_type": "medium",
        },
        has_images=True,
        has_prompt=True,
        user_prompt="foto premium com a peca fiel",
        structural_contract={
            "enabled": True,
            "garment_subtype": "knit_top",
        },
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="reference_mode",
        aspect_ratio="4:5",
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Juliana' and 'Raissa'",
        scenario="",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "skin": "deep rich brown skin",
                "face_structure": "balanced attractive facial planes with natural asymmetry and expressive eyes",
                "hair": "a rounded afro with natural shape and charismatic texture",
                "expression": "subtle engaging smile",
                "presence": "charismatic Brazilian creator presence",
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

    low = result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "late 20s" in low
    assert "deep rich brown skin" not in low
    assert "rounded afro" not in low
    assert "casting_surface" in used_sources


def test_finalize_prompt_agent_result_injects_casting_objective_from_block() -> None:
    result = finalize_prompt_agent_result(
        result={
            "base_prompt": (
                "RAW photo, a woman in a knit pullover. "
                "<CASTING_DIRECTION>\n"
                "[Job-specific casting direction for this specific job]\n"
                "- casting_checklist: defined facial structure, medium forehead, almond eyes, straight nose, soft jawline\n"
                "- age_logic: late 20s\n"
                "- face_geometry: defined facial structure with high cheekbones\n"
                " </CASTING_DIRECTION>\n"
                "The garment should stay detailed."
            ),
            "camera_and_realism": "",
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        scenario="minimal studio interior",
        diversity_target={},
        mode_id="catalog_clean",
        framing_profile="three_quarter",
        camera_type="commercial",
        capture_geometry="three_quarter",
        lighting_profile="studio_even",
        pose_energy="relaxed",
        casting_profile="clean_commercial",
    )

    text = result["prompt"]
    low = text.lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "a woman in her late 20s with" in low or "she has" in low or "she appears" in low
    assert "casting_surface" in used_sources or "nano_finalize" in used_sources
    assert "defined facial structure" in low
    assert "almond eyes" in low


def test_finalize_prompt_agent_result_reference_mode_strips_control_directives_and_remains_pure_nano() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, Replace the placeholder person in the base image completely. "
                "Do not preserve any face, skin tone, hair, body type, or age impression from the base image person or from the references. "
                "Keep the garment exactly the same: preserve the exact garment identity, shape, and texture visible in the references. "
                "CRITICAL — preserve the exact surface pattern geometry from the references. "
                "RAW photo, a Brazilian woman in her late 20s with a defined facial structure and warm commercial presence."
                " She has deep-set almond eyes and a gentle closed-mouth smile."
            ),
            "shot_type": "wide",
        },
        has_images=True,
        has_prompt=True,
        user_prompt="pullover gráfico",
        structural_contract={"enabled": True, "garment_subtype": "knit_pullover"},
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="reference_mode",
        aspect_ratio="4:5",
        pose="",
        grounding_pose_clause="",
        profile="",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "chestnut shoulder-length waves",
                "presence": "balanced shoulders and waist",
                "expression": "gentle smile",
            },
            "pose_state": {
                "weight_shift": "weight shifted naturally to one side",
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

    low = result["prompt"].lower()
    assert "replace the placeholder person" not in low
    assert "do not preserve any face" not in low
    assert "critical — preserve" not in low
    # Com o rescue gate, "RAW photo" sobrevive pois a sentence mista não é dump.
    assert "raw photo" in low
    assert "late 20s" in low
    assert "almond eyes" in low
    assert "weight shifted" in low


def test_finalize_prompt_agent_result_reference_mode_keeps_casting_surface_minimum() -> None:
    result = finalize_prompt_agent_result(
        result={
            "base_prompt": "RAW photo, a woman wearing a knit pullover in a refined interior.",
            "shot_type": "medium",
        },
        has_images=True,
        has_prompt=True,
        user_prompt="foto premium do pullover com rosto brasileiro",
        structural_contract={"enabled": True, "garment_subtype": "knit_pullover"},
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="reference_mode",
        aspect_ratio="4:5",
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Juliana' and 'Raissa'",
        scenario="urban lobby residential",
        diversity_target={
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "chestnut-brown shoulder-length waves",
                "presence": "balanced shoulders and waist with relaxed stance",
                "expression": "gentle warm smile",
                "beauty_read": "luminous freckles and natural skin texture",
            },
            "profile_id": "natural:natural_commercial",
        },
        mode_id="natural",
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    low = result["prompt"].lower()
    marker_hits = [
        "late 20s",
        "defined facial structure",
        "chestnut",
        "shoulders",
        "waist",
        "gentle warm smile",
        "freckles",
    ]
    assert sum(1 for token in marker_hits if token in low) >= 4
    assert "casting checklist" not in result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
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


def test_finalize_prompt_agent_result_natural_adds_body_casting_trait() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a Brazilian woman wearing an olive green linen midi dress in a minimalist studio.",
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
        scenario="studio minimal",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure with high cheekbones",
                "hair": "chocolate shoulder-length waves",
                "presence": "balanced shoulders and relaxed posture",
                "expression": "neutral mouth with quiet attention",
                "beauty_read": "subtle freckles",
                "body": "balanced shoulder-to-hip proportions with a calm torso stance",
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

    low = result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "casting_surface" in used_sources
    assert "shoulder-to-hip" in low
    assert result["prompt_compiler_debug"]["coordination_diagnostics"]["casting_surface_metric"]["body"] is True


def test_finalize_prompt_agent_result_natural_prefers_5_casting_traits_when_state_present() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman with warm natural presence, "
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
        pose="",
        grounding_pose_clause="",
        profile="features blend 'Ana' and 'Lia Costa'",
        scenario="studio minimal",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "heart-shaped face",
                "hair": "chocolate shoulder-length waves",
                "presence": "balanced shoulders and waist",
                "expression": "neutral mouth and quiet attention",
                "beauty_read": "warm honey skin with light freckles",
                "body": "compact athletic frame with medium waist-to-hip ratio",
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

    low = result["prompt"].lower()
    assert "heart-shaped face" in low
    assert "chocolate" in low
    assert "shoulder-length" in low
    assert "waves" in low
    assert "quiet attention" in low
    assert "warm honey" in low
    assert "compact athletic frame" in low


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
    # Com o rescue gate, a sentence mista preserva pose e cenário.
    assert diagnostics["specific_pose_present"] is True
    assert diagnostics["scene_surface_present"] is True


def test_finalize_prompt_agent_result_adds_coordination_bridge_when_prompt_is_decomposed() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her late 20s with a balanced oval face and soft medium-brown waves "
                "wearing an olive green linen midi dress in a minimalist studio. "
                "She stands with a subtle weight shift. "
                "Calçado discreto e adequado ao look completa a produção."
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
                "footwear_family": "soft_flat",
                "footwear_strategy": "soft flat footwear with a clean low-profile outline and restrained contrast",
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

    assert "soft flat footwear with a clean low-profile outline and restrained contrast" in result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "styling_completion" in used_sources


def test_finalize_prompt_agent_result_text_mode_renders_footwear_from_family_when_strategy_is_missing() -> None:
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
                "footwear_family": "closed_clean",
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

    assert "closed footwear" in result["prompt"].lower()
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

    assert "adequate footwear" not in result["prompt"].lower()
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


def test_finalize_prompt_agent_result_natural_mode_strip_terminal_scene_residue() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her late 20s with defined facial structure wearing a long-sleeved knit pullover. "
                "Quiet residential lobby."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="A Brazilian fashion model with a warm, naturally commercial presence; features blend 'Ana' and 'Lia Costa'.",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "shoulder-length chocolate waves",
            },
            "pose_state": {
                "weight_shift": "weight shifted naturally",
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

    low = result["prompt"].lower()
    assert "quiet residential lobby" not in low
    # Com o rescue gate, "RAW photo" sobrevive pois a sentence mista não é dump.
    assert "raw photo" in low
    rules = result["prompt_compiler_debug"]["nano_output_rules"]
    assert "natural_terminal_scene_residue" in rules["applied"]


def test_finalize_prompt_agent_result_natural_mode_avoids_scene_overload() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her late 20s with defined facial structure wearing a long-sleeved knit pullover. "
                "She is in a residential lobby with polished concrete floor and diffuse afternoon light. "
                "A quiet residential lobby with a broad monstera leaf in the background. "
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="A Brazilian fashion model with a warm, naturally commercial presence; features blend 'Ana' and 'Lia Costa'.",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "shoulder-length chestnut waves",
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

    low = result["prompt"].lower()
    assert low.count("residential lobby") <= 1
    assert low.count("polished concrete floor") <= 1
    assert low.count("diffuse") <= 1
    rules = result["prompt_compiler_debug"]["nano_output_rules"]
    assert "natural_scene_surface_dedupe" in rules["applied"] or "natural_environment_simplification" in rules["applied"]


def test_finalize_prompt_agent_result_natural_mode_softens_expression() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman with almond eyes wearing a knit pullover in a soft interior. "
                "She has a gentle closed-mouth smile and a friendly smile while looking toward the camera."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="A Brazilian fashion model with a warm, naturally commercial presence; features blend 'Ana' and 'Lia Costa'.",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "shoulder-length chocolate waves",
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

    low = result["prompt"].lower()
    assert "smile" not in low
    assert "attention" in low
    rules = result["prompt_compiler_debug"]["nano_output_rules"]
    assert "natural_expression_soften" in rules["applied"]


def test_finalize_prompt_agent_result_natural_enforces_detailed_face_and_body_casting() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman with a warm commercial presence wearing a knit pullover."
            ),
            "shot_type": "medium",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "heart-shaped face with high cheekbones, wide-set almond eyes and a soft jawline",
                "hair": "shoulder-length chestnut waves with caramel highlights",
                "presence": "balanced shoulder-to-hip balance and calm torso posture",
                "expression": "neutral mouth with quiet attentive expression",
                "beauty_read": "warm honey skin with light freckles",
                "body": "natural Brazilian silhouette with medium waist-to-hip ratio and relaxed stance",
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

    low = result["prompt"].lower()
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "casting_surface" in used_sources
    assert "heart-shaped" in low
    assert "wide-set almond eyes" in low
    assert "shoulder-length" in low
    assert "chestnut" in low
    assert "waves" in low
    assert "waist-to-hip" in low
    assert "freckles" in low
    assert "neutral mouth" in low


def test_finalize_prompt_agent_result_natural_refills_sparse_casting_with_rich_defaults() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman wearing a knit pullover."
            ),
            "shot_type": "medium",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "chestnut waves",
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

    low = result["prompt"].lower()
    assert "high cheekbones" in low
    assert "wide-set almond eyes" in low
    assert "soft jawline" in low
    assert "waist-to-hip" in low
    assert "neutral mouth" in low
    assert "warm honey skin" in low
    assert "freckles" not in low
    used_sources = {item["source"] for item in result["prompt_compiler_debug"]["used_clauses"]}
    assert "casting_surface" in used_sources


def test_finalize_prompt_agent_result_natural_cleans_abstract_human_artifacts() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman with warm commercial presence wearing a knit pullover. "
                "A vibrant Brazilian woman with chocolate waves and a honey-tan glow, captured in a candid, warm moment. "
                "She has body with Athletic-lean, structured shoulders, Engaged, bright-eyed, relaxed, Sun-kissed and healthy. "
                "She appears as a woman in her late 20s with a face with heart-shaped face, high cheekbones, and wide-set almond eyes. "
                "Her warm honey skin has light freckles across her nose bridge and a soft, relaxed smile."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "heart-shaped face with high cheekbones, wide-set almond eyes and soft jawline",
                "hair": "chestnut shoulder-length waves",
                "beauty_read": "warm honey skin with light freckles",
                "body": "balanced shoulder-to-hip proportions with a calm torso and relaxed posture",
                "expression": "neutral mouth with quiet attention",
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

    low = result["prompt"].lower()
    assert "warm commercial presence" not in low
    assert "vibrant brazilian woman" not in low
    assert "she has body with" not in low
    assert "athletic-lean" not in low
    assert "replace the placeholder person" not in low
    assert "late 20s" in low
    assert "high cheekbones" in low
    assert "wide-set almond eyes" in low
    assert "quiet attention" in low
    floor_debug = result["prompt_compiler_debug"]["human_surface_floor"]
    assert floor_debug["validation_after"].get("valid") is True
    metrics = floor_debug["validation_after"].get("metrics", {})
    assert metrics.get("face_count", 0) >= 4
    assert metrics.get("skin_count", 0) >= 1
    assert metrics.get("hair_count", 0) >= 1
    assert metrics.get("expression_count", 0) >= 1


def test_finalize_prompt_agent_result_natural_scrubs_extreme_dump_surface() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "Replace the placeholder person in the base image completely. "
                "Do not preserve any face, skin tone, hair, body type, or age impression from the base image person or from the references. "
                "Keep the garment exactly the same: preserve the exact garment identity, shape, and texture visible in the references, maintain waist length as shown in the reference, "
                "keep the front closure intact, preserve: ribbed mock neck collar, geometric 3D textured front panel. "
                "CRITICAL — preserve the exact surface pattern geometry from the references: "
                "A slim-fit, long-sleeved pullover in a warm beige or nude tone, featuring a prominent 3D geometric surface pattern. "
                "RAW photo, a medium-wide shot captures a vibrant 28-year-old Brazilian woman with a heart-shaped face and high cheekbones. "
                "Her deep honey-tan skin has a natural satin finish with light freckles across her nose, her voluminous 3A dark chocolate curls with caramel tips fall softly to her shoulders. "
                "She has body with Athletic-lean, structured shoulders, Engaged, bright-eyed, relaxed, Sun-kissed and healthy. "
                "She appears as a woman in her late 20s with a face with heart-shaped face, high cheekbones, almond eyes, and defined facial structure, "
                "skin with warm honey skin with light freckles, shoulder-length chocolate waves with subtle caramel highlights hair, "
                "an natural silhouette with balanced shoulders and medium waist-to-hip ratio body-and-frame, and a neutral mouth and quiet attention expression "
                "Do not introduce any visible undershirt, layered neckline, or contrasting inner collar; the garment neckline itself must remain the only visible neckline element."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "heart-shaped face with high cheekbones, wide-set almond eyes and a soft jawline",
                "hair": "shoulder-length chocolate waves with subtle caramel highlights",
                "beauty_read": "warm honey skin with light freckles",
                "body": "balanced shoulder-to-hip proportions with a calm torso and relaxed posture",
                "expression": "neutral mouth with quiet attention",
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

    low = result["prompt"].lower()
    assert "replace the placeholder person" not in low
    assert "a vibrant brazilian woman" not in low
    assert "do not preserve any face" not in low
    assert "do not introduce any visible undershirt" not in low
    assert "vibrant" not in low
    assert "voluminous" not in low
    assert "athletic-lean" not in low
    assert "bright-eyed" not in low
    assert "sun-kissed" not in low
    assert "late 20s" in low
    assert "heart-shaped" in low
    assert "high cheekbones" in low
    assert "wide-set almond eyes" in low
    assert "soft jawline" in low
    assert "neutral mouth" in low
    assert "quiet attention" in low
    floor_debug = result["prompt_compiler_debug"]["human_surface_floor"]
    assert floor_debug["validation_after"]["valid"] is True


def test_finalize_prompt_agent_result_natural_mode_preserves_garment_signature_but_normalizes_generic_terms() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her late 20s with almond eyes wearing a fitted warm beige knit pullover. "
                "The front panel has a prominent geometric relief pattern with diagonal chevron stitches and texture."
            ),
            "shot_type": "wide",
            "garment_narrative": "long-sleeved knit pullover in 3D diagonal geometric relief",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
        structural_contract={"enabled": True},
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="text_mode",
        aspect_ratio="4:5",
        pose="",
        grounding_pose_clause="",
        profile="A Brazilian fashion model with a warm, naturally commercial presence; features blend 'Ana' and 'Lia Costa'.",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "shoulder-length chocolate waves",
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

    low = result["prompt"].lower()
    assert "geometric relief pattern" in low
    assert "chevron" in low
    assert "fitted" not in low
    assert "warm beige" not in low
    rules = result["prompt_compiler_debug"]["nano_output_rules"]
    assert "natural_garment_normalization" in rules["applied"]


def test_finalize_prompt_agent_result_ensures_internal_state_labels_not_in_final_prompt() -> None:
    result = finalize_prompt_agent_result(
        result={
            "base_prompt": (
                "RAW photo, <CASTING_DIRECTION> CASTING CHECKLIST: heart-shaped face, wide-set almond eyes </CASTING_DIRECTION> "
                "A Brazilian woman with warm honey skin and gentle closed-mouth smile. "
                "mode_id: natural_commercial, profile_hint: natural profile, casting_state: keep"
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="",
        scenario="residential lobby",
        diversity_target={"profile_id": "natural:natural_commercial"},
        mode_id="natural",
        framing_profile="three_quarter",
        camera_type="natural_digital",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    low = result["prompt"].lower()
    assert "casting checklist" not in low
    assert "casting_direction" not in low
    assert "<casting_direction>" not in low
    assert "profile_hint" not in low
    assert "casting_state" not in low
    assert "mode_id" not in low


def test_finalize_prompt_agent_result_any_mode_enforces_human_surface_floor_with_fallback() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a Brazilian woman in a muted studio while wearing a knit sweater.",
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="knit sweater clean shot",
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
        scenario="minimal studio",
        diversity_target={"profile_id": "catalog_clean:polished_commercial"},
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    low = result["prompt"].lower()
    rules = result["prompt_compiler_debug"]["nano_output_rules"]
    assert "human_surface_floor" in rules["applied"]
    assert "late 20s" in low
    assert "high cheekbones" in low
    assert "wide-set almond eyes" in low
    assert "neutral mouth" in low
    assert "shoulder-length" in low or "chocolate" in low
    assert "warm honey skin" in low
    assert "freckles" not in low


def test_finalize_prompt_agent_result_mode_influences_human_surface_without_abstract_terms() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman with warm Brazilian presence and natural commercial presence, "
                "wearing a knit sweater in an elegant interior."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="knit sweater editorial",
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
        scenario="elegant interior",
        diversity_target={"profile_id": "lifestyle:urban_daily"},
        mode_id="lifestyle",
        framing_profile="three_quarter",
        camera_type="lifestyle_natural",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="lifestyle",
    )

    low = result["prompt"].lower()
    assert "warm Brazilian presence" not in low
    assert "natural commercial presence" not in low
    assert "commercial presence" not in low


def test_finalize_prompt_agent_result_human_surface_keeps_single_age_clause() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in her late 20s with relaxed posture and warm natural presence. "
                "She is in her mid 30s in the second light sentence."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="clean lifestyle shot",
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
        scenario="urban apartment",
        diversity_target={"profile_id": "lifestyle:urban_daily"},
        mode_id="lifestyle",
        framing_profile="full_body",
        camera_type="lifestyle_digital",
        capture_geometry="full_body_neutral",
        lighting_profile="natural_soft",
        pose_energy="relaxed",
        casting_profile="lifestyle",
    )

    low = result["prompt"].lower()
    assert "late 20s" in low
    assert "mid 30s" not in low
    floor_debug = result["prompt_compiler_debug"]["human_surface_floor"]
    assert floor_debug["validation_after"]["age_single"] is True


def test_finalize_prompt_agent_result_natural_prefers_casting_age_over_numeric_prompt_age() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, an athletic-looking Brazilian woman, 28-year-old with almond eyes "
                "wearing a knit pullover in neutral light."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure, high cheekbones, wide-set almond eyes, medium forehead, soft jawline",
                "hair": "shoulder-length chocolate waves with subtle caramel highlights",
                "beauty_read": "warm honey skin with light freckles",
                "body": "balanced shoulder-to-hip proportions with a calm torso and relaxed posture",
                "expression": "neutral mouth with quiet attention",
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

    low = result["prompt"].lower()
    assert "late 20s" in low
    assert "28-year-old" not in low
    assert "28 year old" not in low
    assert "heart-shaped" in low or "defined facial structure" in low
    assert "high cheekbones" in low
    assert "soft jawline" in low
    assert "neutral mouth" in low
    floor_debug = result["prompt_compiler_debug"]["human_surface_floor"]
    assert floor_debug["validation_after"].get("age_single") is True


def test_finalize_prompt_agent_result_natural_compacts_duplicate_human_dump_sentences() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, Replace the placeholder person in the base image completely. "
                "A Brazilian woman with warm commercial presence wearing a knit pullover. "
                "A Brazilian woman with a warm, naturally commercial presence. "
                "She appears as a woman in her late 20s with a heart-shaped face, high cheekbones, and wide-set almond eyes, and a defined facial structure. "
                "She has body with Athletic-lean, structured shoulders, Engaged, bright-eyed, relaxed, Sun-kissed and healthy. "
                "She appears as a woman in her late 20s with a face with heart-shaped face, high cheekbones, wide-set almond eyes, and a soft jawline. "
                "She has a gentle closed-mouth smile and quiet attention."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover grafismo clean",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "heart-shaped face with high cheekbones, wide-set almond eyes and soft jawline",
                "hair": "shoulder-length chocolate waves",
                "beauty_read": "warm honey skin with light freckles",
                "body": "balanced shoulder-to-hip proportions with a calm torso and relaxed posture",
                "expression": "neutral mouth with quiet attention",
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

    low = result["prompt"].lower()
    assert low.count("she appears as a woman") <= 1
    assert "a brazilian woman with warm commercial presence" not in low
    assert "a vibrant brazilian woman" not in low
    assert "3a" not in low
    assert "athletic-lean" not in low
    assert "voluminous" not in low
    assert "smile" not in low
    assert "late 20s" in low
    assert low.count("late 20s") == 1
    assert "high cheekbones" in low
    assert "wide-set almond eyes" in low
    assert "soft jawline" in low
    assert "neutral mouth" in low
    assert "quiet attention" in low
    floor_debug = result["prompt_compiler_debug"]["human_surface_floor"]
    assert floor_debug["validation_after"]["valid"] is True
    assert floor_debug["validation_after"]["face_count"] >= 4


def test_finalize_prompt_agent_result_natural_polishes_duplicate_human_surface_fragments() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a medium-wide shot of Her warm golden skin shows a natural dewy sheen and subtle freckles "
                "across her nose bridge as she offers a bright, welcoming half-neutral expression. "
                "She wears the fitted beige knit mock-neck pullover from the reference. "
                "Captured in a candid moment, she is mid-stride with her weight shifting forward. "
                "a woman in her 28 with high cheekbones, defined facial structure, wide-set almond eyes, soft jawline, and medium forehead. "
                "RAW photo, a medium-wide shot of Her warm golden skin shows a natural dewy sheen and subtle freckles "
                "across her nose bridge as she offers a bright, welcoming half-neutral expression. "
                "a woman in her 28 with high cheekbones, defined facial structure, wide-set almond eyes, soft jawline, and medium forehead."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover bege natural",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="bairro residencial",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "high cheekbones, defined facial structure, wide-set almond eyes, soft jawline, medium forehead",
                "hair": "shoulder-length chocolate waves with subtle caramel highlights",
                "beauty_read": "warm honey skin with light freckles",
                "body": "balanced shoulder-to-hip proportions",
                "expression": "neutral mouth with quiet attention",
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

    low = result["prompt"].lower()
    assert "from the reference" not in low
    assert "half-neutral" not in low
    assert "a woman in her 28" not in low
    assert low.count("a woman in her late 20s") <= 1
    assert low.count("raw photo, a medium-wide shot showing her") <= 1


def test_finalize_prompt_agent_result_human_surface_floor_reports_rehydration_validation() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a woman wearing a knit pullover in a neat studio."
            ),
            "shot_type": "wide",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="knit pullover editorial",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="studio",
        diversity_target={"profile_id": "catalog_clean:polished_commercial"},
        mode_id="catalog_clean",
        framing_profile="full_body",
        camera_type="commercial_full_frame",
        capture_geometry="full_body_neutral",
        lighting_profile="studio_even",
        pose_energy="static",
        casting_profile="polished_commercial",
    )

    floor_debug = result["prompt_compiler_debug"]["human_surface_floor"]
    assert isinstance(floor_debug, dict)
    assert floor_debug["applied"] is True
    before = floor_debug["validation_before"]
    after = floor_debug["validation_after"]
    assert isinstance(before, dict)
    assert isinstance(after, dict)
    assert before.get("valid") is False
    assert after.get("valid") is True


def test_finalize_prompt_agent_result_sparse_prompt_does_not_leak_compiler_casting_fragment() -> None:
    result = finalize_prompt_agent_result(
        result={
            "prompt": "RAW photo, a Brazilian woman wearing a knit pullover.",
            "shot_type": "medium",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="pullover cinza com grafismo",
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
        profile="features blend 'Ana' and 'Raissa'",
        scenario="residential lobby",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "casting_state": {
                "age": "late 20s",
                "face_structure": "defined facial structure",
                "hair": "chestnut waves",
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

    low = result["prompt"].lower()
    assert "defined facial structure, chestnut waves residential lobby" not in low
    assert "a brazilian woman wearing a knit pullover. late 20s" not in low
    assert "a woman in her late 20s with" in low
    after = result["prompt_compiler_debug"]["human_surface_floor"]["validation_after"]
    after_metrics = after.get("metrics", {})
    assert after_metrics.get("face_count", 0) >= 4
    assert after_metrics.get("skin_count", 0) >= 1
    assert after_metrics.get("hair_count", 0) >= 1
    assert after_metrics.get("body_count", 0) >= 1
    assert after_metrics.get("expression_count", 0) >= 1
