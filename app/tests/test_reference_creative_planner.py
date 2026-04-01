from __future__ import annotations

import os
import sys
import types
from pathlib import Path


os.environ.setdefault("GOOGLE_AI_API_KEY", "test-key")

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class _Blob:
    def __init__(self, mime_type: str | None = None, data: bytes | None = None):
        self.mime_type = mime_type
        self.data = data


class _Part:
    def __init__(self, text: str | None = None, inline_data: _Blob | None = None, media_resolution=None):
        self.text = text
        self.inline_data = inline_data
        self.media_resolution = media_resolution


class _Content:
    def __init__(self, role: str | None = None, parts=None):
        self.role = role
        self.parts = parts or []


class _Simple:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Client:
    def __init__(self, *args, **kwargs):
        self.models = _Simple(generate_content=lambda *a, **k: None)


google_mod = sys.modules.get("google") or types.ModuleType("google")
genai_mod = sys.modules.get("google.genai") or types.ModuleType("google.genai")
genai_types_mod = sys.modules.get("google.genai.types") or types.ModuleType("google.genai.types")

genai_types_mod.Blob = _Blob
genai_types_mod.Part = _Part
genai_types_mod.Content = _Content
genai_types_mod.MediaResolution = _Simple(MEDIA_RESOLUTION_HIGH="high")
genai_types_mod.GenerateContentConfig = _Simple
genai_types_mod.ImageConfig = _Simple
genai_types_mod.ThinkingConfig = _Simple
genai_types_mod.SafetySetting = _Simple
genai_types_mod.HarmCategory = _Simple(
    HARM_CATEGORY_SEXUALLY_EXPLICIT="sex",
    HARM_CATEGORY_HARASSMENT="harassment",
    HARM_CATEGORY_HATE_SPEECH="hate",
    HARM_CATEGORY_DANGEROUS_CONTENT="danger",
)
genai_types_mod.HarmBlockThreshold = _Simple(BLOCK_NONE="none")
genai_types_mod.Tool = _Simple
genai_types_mod.GoogleSearch = _Simple
genai_types_mod.SearchTypes = _Simple
genai_types_mod.ImageSearch = _Simple
genai_mod.Client = _Client
genai_mod.types = genai_types_mod
google_mod.genai = genai_mod

sys.modules["google"] = google_mod
sys.modules["google.genai"] = genai_mod
sys.modules["google.genai.types"] = genai_types_mod


import agent_runtime.reference_creative_planner as planner
from agent_runtime.capture_soul import get_capture_soul
from agent_runtime.fidelity import prepare_garment_replacement_prompt
from agent_runtime.fidelity_gate import build_fidelity_repair_patch
from agent_runtime.mode_identity_soul import get_mode_identity_soul
from agent_runtime.pose_soul import get_pose_soul
from agent_runtime.styling_direction import derive_styling_context
from agent_runtime.styling_soul import get_styling_soul


def test_reference_creative_plan_fallback_never_returns_empty_prompt() -> None:
    styling_context = derive_styling_context(
        mode_id="natural",
        user_prompt="quero uma foto leve",
        garment_hint="crochet cardigan",
        image_analysis="crochet cardigan with open front and textured body",
        structural_contract={"enabled": True, "garment_subtype": "standard_cardigan", "garment_length": "hip"},
        set_detection={},
        garment_aesthetic={"vibe": "artisanal"},
        has_images=True,
    )

    plan = planner.build_reference_creative_plan_fallback(
        mode_id="natural",
        garment_hint="crochet cardigan",
        structural_contract={"enabled": True, "garment_subtype": "standard_cardigan", "garment_length": "hip"},
        set_detection={},
        image_analysis="crochet cardigan with open front and textured body",
        styling_context=styling_context,
    )

    assert plan.base_scene_prompt
    assert plan.stage2_scene_context
    assert plan.summary["fallback_applied"] == "true"
    assert "The references exist only to establish the garment's physical form." in plan.base_scene_prompt
    assert plan.debug_trace["output"]["fallback_applied"] is True


def test_planner_builds_base_prompt_without_prompt_duplication(monkeypatch) -> None:
    monkeypatch.setattr(
        planner,
        "generate_structured_json",
        lambda **kwargs: _Simple(
            parsed={
                "casting_direction": {
                    "profile_hint": "adult Brazilian woman with fresh presence",
                    "age_band": "late 20s",
                    "face_hair_presence": "clear face and natural hair silhouette",
                    "body_read": "balanced relaxed body line",
                    "expression_read": "quiet attentive expression",
                },
                "styling_direction": {
                    "product_topology": "single_piece",
                    "hero_family": "top_layer",
                    "hero_components": ["crochet cardigan"],
                    "completion_slots": ["lower_body", "footwear"],
                    "completion_strategy": "keep completion quiet",
                    "primary_completion": "simple lower-body completion",
                    "secondary_completion": "none",
                    "footwear_direction": "quiet footwear",
                    "accessories_optional": "none",
                    "outer_layer_optional": "none",
                    "finish_logic": "subordinate finishing only",
                    "direction_summary": "quiet completion around the cardigan",
                    "confidence": 0.9,
                },
                "scene_direction": {
                    "setting": "ordinary Brazilian home setting",
                    "surface_cues": "worn floor and matte wall texture",
                    "lighting_logic": "soft natural daylight",
                },
                "pose_direction": {
                    "stance": "relaxed asymmetrical stance",
                    "arm_logic": "light everyday hand behavior",
                    "garment_visibility": "keep the cardigan front visible",
                },
                "capture_direction": {
                    "framing": "medium-wide framing",
                    "angle": "fresh three-quarter view",
                    "crop_logic": "keep body and place alive together",
                    "lens_feel": "human-scaled perspective",
                },
            }
        ),
    )

    plan = planner.plan_reference_creative_flow(
        mode_id="natural",
        user_prompt="quero algo leve e real",
        scene_preference="auto_br",
        garment_hint="crochet cardigan",
        image_analysis="crochet cardigan with open front and textured body",
        structural_contract={"enabled": True, "garment_subtype": "standard_cardigan", "garment_length": "hip"},
        set_detection={},
        garment_aesthetic={"vibe": "artisanal"},
        lighting_signature={"subject_read": "soft", "background_read": "muted"},
        mode_guardrail_text="keep it ordinary and garment-first",
    )

    assert plan.fallback_applied is False
    assert plan.summary["creative_source"] == "reference_planner"
    assert "SOUL STACK FOR BASE." not in plan.base_scene_prompt
    assert "Mode styling mandate:" in plan.base_scene_prompt
    assert plan.stage2_scene_context
    assert len(plan.stage2_scene_context) <= 700
    assert plan.debug_trace["input"]["instruction_prompt"]
    assert plan.debug_trace["output"]["parsed_response_payload"]["scene_direction"]["setting"] == "ordinary Brazilian home setting"
    assert plan.debug_trace["output"]["normalized_plan"]["base_scene_prompt"] == plan.base_scene_prompt


def test_clean_text_truncates_on_word_boundary() -> None:
    text = (
        "Deep espresso brown with subtle mahogany highlights at the ends; "
        "thick, wavy texture with significant volume and a clean side part."
    )

    cleaned = planner._clean_text(text, limit=72)

    assert cleaned == "Deep espresso brown with subtle mahogany highlights at the ends"
    assert cleaned.split()[-1] == "ends"


def test_stage2_scene_context_uses_full_budget_without_mid_word_cut(monkeypatch) -> None:
    monkeypatch.setattr(
        planner,
        "generate_structured_json",
        lambda **kwargs: _Simple(
            parsed={
                "casting_direction": {
                    "profile_hint": "Brazilian woman in her early 30s with a sophisticated, urban presence.",
                    "age_band": "32 years old",
                    "face_geometry": "Strong, defined jawline with high, prominent cheekbones; straight, medium-width nose bridge; full lips with a natural rose-mauve tone; almond-shaped hazel eyes under thick, naturally arched brows.",
                    "eye_logic": "Direct, intelligent gaze with clear, aligned pupils and a warm, welcoming commercial focus.",
                    "skin_read": "Warm olive undertone with a natural satin sheen and a few subtle, authentic freckles across the bridge of the nose.",
                    "face_hair_presence": "Clean-shaven, smooth skin.",
                    "hair_logic": "Deep espresso brown with subtle mahogany highlights at the ends; thick, wavy texture (2B pattern) with significant volume; shoulder-length cut with a clean side part, tucked behind one ear to reveal the jawline.",
                    "body_frame": "Height impression of 1.75m; athletic but slender build with square, well-defined shoulders that emphasize the pullover's fit.",
                    "body_read": "Toned frame where the knit sits snugly against the torso, highlighting the waist-length hem.",
                    "expression_read": "A calm, confident closed-mouth smile that feels commercially inviting and professional.",
                    "makeup_read": "Visible matte terracotta eyeshadow, a light coat of black mascara, and a sheer nude lip tint.",
                },
                "styling_direction": {
                    "product_topology": "single_piece",
                    "hero_family": "top_layer",
                    "hero_components": ["fitted mock neck knit pullover with geometric relief"],
                    "completion_slots": ["lower_body", "footwear"],
                    "completion_strategy": "monochromatic urban sophistication",
                    "primary_completion": "High-waisted wide-leg trousers in a heavy cream wool crepe that creates a clean vertical line from the waist.",
                    "secondary_completion": "Minimalist gold stud earrings.",
                    "footwear_direction": "Pointed-toe leather mules in a matching cream tone, partially visible beneath the trouser hem.",
                    "accessories_optional": "None, keeping the focus on the knit texture.",
                    "outer_layer_optional": "None.",
                    "finish_logic": "Tucked-in appearance to emphasize the waist-length structure of the pullover.",
                    "direction_summary": "A tonal, high-end look using cream wide-leg trousers to complement the beige knit without competing with the geometric relief pattern.",
                    "confidence": 0.95,
                },
                "scene_direction": {
                    "setting": "Premium Brazilian studio environment.",
                    "surface_cues": "Seamless matte paper backdrop in a warm-cream tone to provide subtle contrast against the beige garment.",
                    "lighting_logic": "Soft, directional key light from the upper right to cast micro-shadows within the geometric relief, revealing the diamond knit texture.",
                },
                "pose_direction": {
                    "stance": "Stable, upright stance with the body rotated 20 degrees away from the lens while the head turns back to face the camera.",
                    "arm_logic": "One arm relaxed at the side, the other hand lightly touching the opposite forearm at waist level to frame the garment's hem.",
                    "garment_visibility": "The 3/4 body rotation ensures the geometric pattern is visible across the chest and down the sleeve without occlusion.",
                },
                "capture_direction": {
                    "framing": "Medium-full shot, capturing from the head to just below the knees.",
                    "angle": "Eye-level with a 20-degree subject rotation to avoid a flat frontal view.",
                    "crop_logic": "Clean vertical crop with generous head room and the subject centered horizontally.",
                    "lens_feel": "85mm prime lens compression for a flattering, distortion-free commercial look with a shallow depth of field.",
                },
            }
        ),
    )

    plan = planner.plan_reference_creative_flow(
        mode_id="catalog_clean",
        user_prompt="quero clean premium",
        scene_preference="auto_br",
        garment_hint="fitted mock neck knit pullover with geometric relief",
        image_analysis="A light beige knit pullover featuring a complex geometric relief pattern of intersecting diagonal lines forming a diamond and triangle grid.",
        structural_contract={"enabled": True, "garment_subtype": "pullover", "garment_length": "waist"},
        set_detection={},
        garment_aesthetic={"vibe": "urban"},
        lighting_signature={"subject_read": "clean"},
        mode_guardrail_text="keep product-first clarity",
    )

    assert len(plan.stage2_scene_context) <= 700
    assert "diamon." not in plan.stage2_scene_context
    assert "Presence:" in plan.stage2_scene_context
    assert "Pose:" in plan.stage2_scene_context
    assert "Capture:" in plan.stage2_scene_context
    assert "turns back to One arm" not in plan.stage2_scene_context
    assert ".." not in plan.stage2_scene_context


def test_prepare_garment_replacement_prompt_returns_structured_shell() -> None:
    prepared = prepare_garment_replacement_prompt(
        structural_contract={
            "enabled": True,
            "garment_subtype": "pullover",
            "garment_length": "waist",
            "front_opening": "closed",
            "must_keep": ["ribbed mock neck collar", "geometric diamond relief pattern"],
        },
        garment_hint="fitted mock neck knit pullover with geometric relief",
        image_analysis="fitted knit pullover with geometric diamond relief, textured ribbed mock neck, and dimensional surface pattern",
        set_detection={},
        mode_id="natural",
        source_prompt_context="base prompt context",
    )

    assert prepared.flow_mode == "garment_replacement"
    assert prepared.use_structured_shell is True
    assert prepared.include_source_prompt_context is True
    assert prepared.include_reference_item_description is True
    assert "Replace only the placeholder garment" in prepared.structured_edit_goal
    assert not prepared.structured_edit_goal.startswith("Preserve exactly:")
    assert "front closure intact" not in prepared.structured_edit_goal
    assert "front fully closed" in prepared.structured_edit_goal
    assert "geometric diamond relief" in prepared.reference_item_description
    assert "all visible non-target outfit items and accessories" in prepared.structured_preserve_clause


def test_stage1_repair_patch_no_longer_forces_catalog_composition() -> None:
    patch = build_fidelity_repair_patch(
        stage="stage1",
        gate_result={"issue_codes": ["construction_drift"]},
        structural_contract={"garment_subtype": "pullover", "front_opening": "closed"},
        set_detection={},
    )

    assert "clean catalog composition" not in patch
    assert "current mode direction" in patch


def test_catalog_clean_souls_no_longer_force_repeated_archetype() -> None:
    mode_lines = "\n".join(get_mode_identity_soul("catalog_clean"))
    pose_soul = get_pose_soul(mode_id="catalog_clean", has_images=True)
    capture_soul = get_capture_soul(mode_id="catalog_clean", has_images=True)
    styling_soul = get_styling_soul(mode_id="catalog_clean", has_images=True, garment_season="winter")

    assert "same repeated catalog woman" in mode_lines
    assert "same repeated open smile" not in pose_soul
    assert "do not collapse catalog_clean into the same open-smile expression" in pose_soul
    assert "do not recycle the exact same near-frontal centered relation every time" in capture_soul
    assert "Avoid defaulting to the same dark trouser plus ankle-boot solution" in styling_soul


def test_pose_soul_no_longer_forces_gerund_outside_lifestyle() -> None:
    natural_pose = get_pose_soul(mode_id="natural", has_images=True)
    assert "only lifestyle requires a visible ongoing action" in natural_pose


def test_planner_instruction_demands_specific_non_median_choices(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def _fake_generate_structured_json(**kwargs):
        parts = kwargs.get("parts") or []
        captured["instruction"] = str(parts[0].text if parts else "")
        return _Simple(
            parsed={
                "casting_direction": {
                    "profile_hint": "adult Brazilian woman with angular face and close-cropped curls",
                    "age_band": "mid 30s",
                    "face_hair_presence": "close-cropped curls and strong brow line",
                    "body_read": "upright but relaxed body logic",
                    "expression_read": "calm direct shopper acknowledgment",
                },
                "styling_direction": {
                    "product_topology": "single_piece",
                    "hero_family": "top_layer",
                    "hero_components": ["mock neck knit pullover"],
                    "completion_slots": ["lower_body", "footwear"],
                    "completion_strategy": "choose a specific clean completion",
                    "primary_completion": "graphite straight-leg tailoring",
                    "secondary_completion": "none",
                    "footwear_direction": "clean closed leather flats",
                    "accessories_optional": "none",
                    "outer_layer_optional": "none",
                    "finish_logic": "subordinate finish only",
                    "direction_summary": "specific quiet completion around the pullover",
                    "confidence": 0.9,
                },
                "scene_direction": {
                    "setting": "neutral studio backdrop only",
                    "surface_cues": "ice-white sweep with subtle paper warmth",
                    "lighting_logic": "soft directional studio light",
                },
                "pose_direction": {
                    "stance": "offset planted stance with one knee softened",
                    "arm_logic": "one arm relaxed and one lightly organizing the waistline",
                    "garment_visibility": "keep the full front visible",
                },
                "capture_direction": {
                    "framing": "clean full-body commercial framing",
                    "angle": "subtle three-quarter commercial relation",
                    "crop_logic": "keep the full garment readable",
                    "lens_feel": "clean neutral commercial perspective",
                },
            }
        )

    monkeypatch.setattr(planner, "generate_structured_json", _fake_generate_structured_json)

    planner.plan_reference_creative_flow(
        mode_id="catalog_clean",
        user_prompt="quero clean premium",
        scene_preference="auto_br",
        garment_hint="fitted mock neck knit pullover",
        image_analysis="fitted pullover with geometric relief",
        structural_contract={"enabled": True, "garment_subtype": "pullover", "garment_length": "waist"},
        set_detection={},
        garment_aesthetic={"vibe": "urban"},
        lighting_signature={"subject_read": "clean"},
        mode_guardrail_text="keep product-first clarity",
    )

    instruction = captured["instruction"]
    assert "Casting must make a specific choice, not a median commercial archetype." in instruction
    assert "Do not output the same polished brunette catalog woman by default." in instruction
    assert "Do not default to dark tailored trousers plus ankle boots as the universal completion" in instruction
    assert "Pose must choose one distinct commercial body solution" in instruction
