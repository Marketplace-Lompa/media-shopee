from __future__ import annotations

import sys
import types
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Stub mínimo para importar triage sem depender do SDK/config reais.
google_mod = types.ModuleType("google")
genai_mod = types.ModuleType("google.genai")
genai_types_mod = types.ModuleType("google.genai.types")
genai_mod.types = genai_types_mod
google_mod.genai = genai_mod
sys.modules.setdefault("google", google_mod)
sys.modules.setdefault("google.genai", genai_mod)
sys.modules.setdefault("google.genai.types", genai_types_mod)

gemini_client_stub = types.ModuleType("agent_runtime.gemini_client")
gemini_client_stub.generate_structured_json = lambda *args, **kwargs: {}
gemini_client_stub.generate_multimodal = lambda *args, **kwargs: {}
sys.modules.setdefault("agent_runtime.gemini_client", gemini_client_stub)

import agent_runtime.triage as triage


def test_resolve_prompt_agent_visual_triage_uses_precomputed_unified_result() -> None:
    payload = {
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
            "must_keep": ["front opening"],
        },
        "set_detection": {
            "is_garment_set": True,
            "set_pattern_score": 0.72,
            "detected_garment_roles": ["cardigan", "scarf"],
            "set_pattern_cues": ["matching knit"],
            "set_lock_mode": "off",
        },
        "look_contract": {
            "bottom_style": "calca de alfaiataria",
            "confidence": 0.8,
        },
    }

    result = triage.resolve_prompt_agent_visual_triage(
        uploaded_images=[b"fake-image"],
        user_prompt="foto premium",
        guided_enabled=True,
        guided_set_mode="conjunto",
        unified_vision_triage_result=payload,
    )

    assert result["garment_hint"] == payload["garment_hint"]
    assert result["image_analysis"] == payload["image_analysis"]
    assert result["structural_contract"]["enabled"] is True
    assert result["look_contract"]["bottom_style"] == "calca de alfaiataria"
    assert result["guided_set_detection"]["set_lock_mode"] == "generic"


def test_resolve_prompt_agent_visual_triage_prefers_external_structural_contract() -> None:
    calls = {"garment_hint": 0, "unified": 0}
    original_garment_hint = triage._infer_garment_hint
    original_unified = triage._infer_unified_vision_triage

    def fake_garment_hint(uploaded_images: list[bytes]) -> str:
        calls["garment_hint"] += 1
        return "external contract garment"

    def fail_unified(*args, **kwargs):
        calls["unified"] += 1
        raise AssertionError("unified triage should not run when structural_contract_hint is provided")

    try:
        triage._infer_garment_hint = fake_garment_hint
        triage._infer_unified_vision_triage = fail_unified

        structural_contract = {
            "enabled": True,
            "confidence": 0.88,
            "garment_subtype": "jacket",
            "sleeve_type": "set-in",
        }
        result = triage.resolve_prompt_agent_visual_triage(
            uploaded_images=[b"fake-image"],
            user_prompt="foto premium",
            guided_enabled=False,
            guided_set_mode="unica",
            structural_contract_hint=structural_contract,
        )
    finally:
        triage._infer_garment_hint = original_garment_hint
        triage._infer_unified_vision_triage = original_unified

    assert calls["garment_hint"] == 1
    assert calls["unified"] == 0
    assert result["garment_hint"] == "external contract garment"
    assert result["structural_contract"] == structural_contract


def test_resolve_prompt_agent_visual_triage_handles_no_images_guided_set_mode() -> None:
    original_set_pattern = triage._infer_set_pattern_from_images

    def fake_set_pattern(uploaded_images: list[bytes], user_prompt: str | None) -> dict:
        assert uploaded_images == []
        return {
            "is_garment_set": True,
            "set_pattern_score": 0.66,
            "detected_garment_roles": ["cardigan", "scarf"],
            "set_pattern_cues": ["matching stripes"],
            "set_lock_mode": "probable",
        }

    try:
        triage._infer_set_pattern_from_images = fake_set_pattern
        result = triage.resolve_prompt_agent_visual_triage(
            uploaded_images=[],
            user_prompt="quero conjunto",
            guided_enabled=True,
            guided_set_mode="conjunto",
        )
    finally:
        triage._infer_set_pattern_from_images = original_set_pattern

    assert result["guided_set_detection"]["is_garment_set"] is True
    assert result["guided_set_detection"]["set_lock_mode"] == "probable"
