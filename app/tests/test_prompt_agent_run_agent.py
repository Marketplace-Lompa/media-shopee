from __future__ import annotations

import sys
import types
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class _Blob:
    def __init__(self, mime_type: str | None = None, data: bytes | None = None):
        self.mime_type = mime_type
        self.data = data


class _Part:
    def __init__(self, text: str | None = None, inline_data: _Blob | None = None):
        self.text = text
        self.inline_data = inline_data


# Stub mínimo para permitir import do agent sem SDK/config reais.
google_mod = sys.modules.get("google") or types.ModuleType("google")
genai_mod = sys.modules.get("google.genai") or types.ModuleType("google.genai")
genai_types_mod = sys.modules.get("google.genai.types") or types.ModuleType("google.genai.types")
genai_types_mod.Blob = _Blob
genai_types_mod.Part = _Part
genai_mod.types = genai_types_mod
google_mod.genai = genai_mod
sys.modules["google"] = google_mod
sys.modules["google.genai"] = genai_mod
sys.modules["google.genai.types"] = genai_types_mod

gemini_client_stub = sys.modules.get("agent_runtime.gemini_client") or types.ModuleType("agent_runtime.gemini_client")
gemini_client_stub.generate_with_system_instruction = lambda *args, **kwargs: None
gemini_client_stub.generate_structured_json = lambda *args, **kwargs: {}
gemini_client_stub.generate_multimodal = lambda *args, **kwargs: {}
sys.modules["agent_runtime.gemini_client"] = gemini_client_stub

import agent


class _FakeResponse:
    def __init__(self, parsed: dict):
        self.parsed = parsed


def test_run_agent_text_mode_keeps_category_and_compiles_prompt() -> None:
    captured: dict = {}

    def fake_generate_with_system_instruction(*, parts, system_instruction, schema, temperature, max_tokens):
        captured["parts"] = parts
        captured["system_instruction"] = system_instruction
        return _FakeResponse(
            {
                "base_prompt": "RAW photo, premium fashion catalog shot of a knit top with realistic fabric texture.",
                "garment_narrative": "soft knit top with refined texture and clean silhouette",
                "camera_and_realism": "85mm lens, realistic studio lighting, natural skin texture",
                "thinking_level": "HIGH",
                "shot_type": "medium",
                "realism_level": 2,
            }
        )

    original_generate = agent.generate_with_system_instruction
    try:
        agent.generate_with_system_instruction = fake_generate_with_system_instruction
        result = agent.run_agent(
            user_prompt="quero uma foto premium de ecommerce para essa blusa",
            uploaded_images=None,
            pool_context="",
            aspect_ratio="4:5",
            resolution="1536",
            category="fashion",
        )
    finally:
        agent.generate_with_system_instruction = original_generate

    assert result["category"] == "fashion"
    assert result["pipeline_mode"] == "text_mode"
    assert result["prompt"]
    assert captured["system_instruction"]
    assert "<MODE>" in captured["parts"][-1].text
    assert "<OUTPUT_PARAMETERS>" in captured["parts"][-1].text


def test_run_agent_text_mode_does_not_call_visual_triage_without_images() -> None:
    def fake_generate_with_system_instruction(*, parts, system_instruction, schema, temperature, max_tokens):
        return _FakeResponse(
            {
                "prompt": "RAW photo, a commercially natural model wearing an olive green linen dress in a believable urban setting.",
                "thinking_level": "MINIMAL",
                "shot_type": "medium",
                "realism_level": 2,
            }
        )

    def fail_visual_triage(**kwargs):
        raise AssertionError("visual triage must not run in text_mode without images")

    original_generate = agent.generate_with_system_instruction
    original_triage = agent.resolve_prompt_agent_visual_triage
    try:
        agent.generate_with_system_instruction = fake_generate_with_system_instruction
        agent.resolve_prompt_agent_visual_triage = fail_visual_triage
        result = agent.run_agent(
            user_prompt="vestido verde oliva para ecommerce",
            uploaded_images=None,
            pool_context="",
            aspect_ratio="4:5",
            resolution="1536",
            category="fashion",
        )
    finally:
        agent.generate_with_system_instruction = original_generate
        agent.resolve_prompt_agent_visual_triage = original_triage

    assert result["pipeline_mode"] == "text_mode"
    assert result["structural_contract"]["enabled"] is False
    assert result["image_analysis"] == ""


def test_run_agent_reference_mode_consumes_precomputed_triage() -> None:
    def fake_generate_with_system_instruction(*, parts, system_instruction, schema, temperature, max_tokens):
        return _FakeResponse(
            {
                "base_prompt": "RAW photo, premium fashion catalog shot of a knit top with realistic fabric texture.",
                "garment_narrative": "soft knit top with refined texture and clean silhouette",
                "camera_and_realism": "85mm lens, realistic studio lighting, natural skin texture",
                "thinking_level": "HIGH",
                "shot_type": "medium",
                "realism_level": 2,
            }
        )

    precomputed_triage = {
        "garment_hint": "textured knit cardigan",
        "image_analysis": "Olive knit cardigan with visible texture and soft drape.",
        "structural_contract": {
            "enabled": True,
            "confidence": 0.91,
            "garment_subtype": "standard_cardigan",
            "sleeve_type": "set-in",
            "sleeve_length": "long",
            "front_opening": "open",
            "hem_shape": "straight",
            "garment_length": "hip",
            "silhouette_volume": "regular",
            "must_keep": ["front opening", "long sleeves"],
        },
        "set_detection": {
            "is_garment_set": False,
            "set_pattern_score": 0.0,
            "detected_garment_roles": [],
            "set_pattern_cues": [],
            "set_lock_mode": "off",
        },
        "look_contract": {
            "bottom_style": "calca de alfaiataria",
            "bottom_color": "preto",
            "color_family": "neutros escuros",
            "season": "transicional",
            "occasion": "casual-urbano",
            "forbidden_bottoms": ["saia plissada chiffon"],
            "accessories": "brincos simples",
            "style_keywords": ["estruturado"],
            "confidence": 0.8,
        },
    }

    original_generate = agent.generate_with_system_instruction
    try:
        agent.generate_with_system_instruction = fake_generate_with_system_instruction
        result = agent.run_agent(
            user_prompt="foto premium com a peca fiel",
            uploaded_images=[b"fake-image-bytes"],
            pool_context="",
            aspect_ratio="4:5",
            resolution="1536",
            category="fashion",
            unified_vision_triage_result=precomputed_triage,
        )
    finally:
        agent.generate_with_system_instruction = original_generate

    assert result["category"] == "fashion"
    assert result["pipeline_mode"] == "reference_mode"
    assert result["image_analysis"] == "Olive knit cardigan with visible texture and soft drape."
    assert result["structural_contract"]["enabled"] is True


def test_run_agent_reference_mode_upgrades_legacy_diversity_target_to_latent_states() -> None:
    captured: dict = {}

    def fake_generate_with_system_instruction(*, parts, system_instruction, schema, temperature, max_tokens):
        captured["parts"] = parts
        return _FakeResponse(
            {
                "prompt": "RAW photo, a Brazilian woman wearing the referenced cardigan in a believable refined interior.",
                "thinking_level": "HIGH",
                "shot_type": "medium",
                "realism_level": 2,
            }
        )

    precomputed_triage = {
        "garment_hint": "textured knit cardigan",
        "image_analysis": "Olive knit cardigan with visible texture and soft drape.",
        "structural_contract": {
            "enabled": True,
            "confidence": 0.91,
            "garment_subtype": "standard_cardigan",
            "sleeve_type": "set-in",
            "sleeve_length": "long",
            "front_opening": "open",
            "hem_shape": "straight",
            "garment_length": "hip",
            "silhouette_volume": "regular",
            "must_keep": ["front opening", "long sleeves"],
        },
        "set_detection": {
            "is_garment_set": False,
            "set_pattern_score": 0.0,
            "detected_garment_roles": [],
            "set_pattern_cues": [],
            "set_lock_mode": "off",
        },
        "look_contract": {},
    }
    legacy_diversity_target = {
        "profile_id": "legacy_profile_1",
        "profile_prompt": "late 20s, warm Brazilian commercial model",
        "scenario_id": "legacy_scene_1",
        "scenario_prompt": "believable residential interior",
        "pose_id": "legacy_pose_1",
        "pose_prompt": "relaxed standing pose",
        "age_range": "25-34",
        "scene_type": "interno",
        "pose_style": "tradicional",
        "lighting_hint": "soft daylight from a window",
    }

    original_generate = agent.generate_with_system_instruction
    try:
        agent.generate_with_system_instruction = fake_generate_with_system_instruction
        result = agent.run_agent(
            user_prompt="foto premium com a peca fiel",
            uploaded_images=[b"fake-image-bytes"],
            pool_context="",
            aspect_ratio="4:5",
            resolution="1536",
            category="fashion",
            diversity_target=legacy_diversity_target,
            unified_vision_triage_result=precomputed_triage,
            mode="natural",
        )
    finally:
        agent.generate_with_system_instruction = original_generate

    context = captured["parts"][-1].text
    assert "GARMENT-ONLY REFERENCE MODE:" in context
    assert "CASTING LATENT STATE" in context
    assert "SCENE LATENT STATE" in context
    assert "CAPTURE LATENT STATE" in context
    assert "POSE LATENT STATE" in context
    assert "STYLING LATENT STATE" in context
    assert "skin direction:" not in context
    assert "hair language:" not in context
    assert "face impression:" not in context
    assert "do not over-specify phenotype in garment-reference mode" in context
    assert result["diversity_target"]["casting_state"]["age"] == "late 20s to early 30s"
    assert result["diversity_target"]["legacy_profile_id"] == "legacy_profile_1"


def test_run_agent_reference_mode_without_prompt_auto_builds_modern_diversity_target() -> None:
    captured: dict = {}

    def fake_generate_with_system_instruction(*, parts, system_instruction, schema, temperature, max_tokens):
        captured["parts"] = parts
        return _FakeResponse(
            {
                "prompt": "RAW photo, a commercially believable Brazilian woman wearing the referenced garment in a refined clean setting.",
                "thinking_level": "HIGH",
                "shot_type": "medium",
                "realism_level": 2,
            }
        )

    precomputed_triage = {
        "garment_hint": "olive knit cardigan",
        "image_analysis": "Olive knit cardigan with visible texture and soft drape.",
        "structural_contract": {
            "enabled": True,
            "confidence": 0.91,
            "garment_subtype": "standard_cardigan",
            "sleeve_type": "set-in",
            "sleeve_length": "long",
            "front_opening": "open",
            "hem_shape": "straight",
            "garment_length": "hip",
            "silhouette_volume": "regular",
            "must_keep": ["front opening", "long sleeves"],
        },
        "set_detection": {
            "is_garment_set": False,
            "set_pattern_score": 0.0,
            "detected_garment_roles": [],
            "set_pattern_cues": [],
            "set_lock_mode": "off",
        },
        "look_contract": {},
    }

    original_generate = agent.generate_with_system_instruction
    try:
        agent.generate_with_system_instruction = fake_generate_with_system_instruction
        result = agent.run_agent(
            user_prompt=None,
            uploaded_images=[b"fake-image-bytes"],
            pool_context="",
            aspect_ratio="4:5",
            resolution="1536",
            category="fashion",
            unified_vision_triage_result=precomputed_triage,
            mode="natural",
        )
    finally:
        agent.generate_with_system_instruction = original_generate

    context = captured["parts"][-1].text
    assert "GARMENT-ONLY REFERENCE MODE:" in context
    assert "CASTING LATENT STATE" in context
    assert "SCENE LATENT STATE" in context
    assert "POSE LATENT STATE" in context
    assert result["diversity_target"]["profile_hint"]
    assert result["diversity_target"]["casting_state"]["age"]
    assert result["diversity_target"]["scene_state"]["world_family"]
