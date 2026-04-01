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
from agent_runtime.fidelity import prepare_garment_replacement_prompt
from agent_runtime.styling_direction import derive_styling_context


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
    assert plan.summary["fallback_applied"] == "true"
    assert "BASE GENERATION STAGE" in plan.base_scene_prompt


def test_planner_builds_base_prompt_with_soul_stack(monkeypatch) -> None:
    monkeypatch.setattr(planner, "build_reference_edit_art_direction", lambda **kwargs: "SOUL STACK FOR BASE.")
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
    assert "SOUL STACK FOR BASE." in plan.base_scene_prompt
    assert "Mode styling mandate:" in plan.base_scene_prompt


def test_prepare_garment_replacement_prompt_returns_structured_shell() -> None:
    prepared = prepare_garment_replacement_prompt(
        structural_contract={"enabled": True, "garment_subtype": "standard_cardigan", "garment_length": "hip"},
        garment_hint="crochet cardigan",
        image_analysis="olive cardigan with textured knit body",
        set_detection={},
        mode_id="natural",
        source_prompt_context="base prompt context",
    )

    assert prepared.flow_mode == "garment_replacement"
    assert prepared.use_structured_shell is True
    assert prepared.include_source_prompt_context is True
    assert prepared.include_reference_item_description is True
    assert "Replace only the placeholder garment" in prepared.structured_edit_goal
