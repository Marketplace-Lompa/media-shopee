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


import agent_runtime.generation_flow as generation_flow
from agent_runtime.editing.contracts import PreparedEditPrompt


class _FakePlan:
    base_scene_prompt = "PLANNER BASE PROMPT"
    summary = {
        "creative_source": "reference_planner",
        "base_strategy": "creative_base_then_garment_replacement",
        "replacement_strategy": "lock_person_replace_garment",
    }

    def to_dict(self) -> dict:
        return {
            "base_scene_prompt": self.base_scene_prompt,
            "summary": dict(self.summary),
            "fallback_applied": False,
        }


def test_upload_flow_uses_single_base_and_lock_person_stage2(monkeypatch, tmp_path) -> None:
    base_file = tmp_path / "base.png"
    base_file.write_bytes(b"base-image")

    selector_result = {
        "items": [],
        "stats": {"identity_reference_risk": "low", "unique_count": 2, "duplicate_count": 0},
        "selected_bytes": {
            "base_generation": [b"img-a", b"img-b"],
            "strict_single_pass": [b"img-a", b"img-b"],
            "edit_anchors": [b"anchor-a", b"anchor-b"],
            "identity_safe": [b"anchor-a", b"anchor-b"],
        },
        "selected_names": {
            "base_generation": ["a.jpg", "b.jpg"],
            "strict_single_pass": ["a.jpg", "b.jpg"],
            "edit_anchors": ["a.jpg", "b.jpg"],
            "identity_safe": ["a.jpg", "b.jpg"],
        },
        "unified_triage": {
            "garment_hint": "crochet cardigan",
            "image_analysis": "olive cardigan with textured knit body",
            "structural_contract": {"enabled": True, "garment_subtype": "standard_cardigan", "garment_length": "hip"},
            "set_detection": {},
            "lighting_signature": {},
            "garment_aesthetic": {},
        },
    }

    captured: dict[str, object] = {}

    monkeypatch.setattr(generation_flow, "validate_generation_params", lambda **kwargs: None)
    monkeypatch.setattr(generation_flow, "select_reference_subsets", lambda **kwargs: selector_result)
    monkeypatch.setattr(generation_flow, "derive_reference_guard_config", lambda **kwargs: {})
    monkeypatch.setattr(generation_flow, "derive_art_direction_selection_policy", lambda **kwargs: {})
    monkeypatch.setattr(generation_flow, "stage1_candidate_count", lambda **kwargs: 1)
    monkeypatch.setattr(generation_flow, "build_classifier_summary", lambda *args, **kwargs: {})
    monkeypatch.setattr(generation_flow, "should_use_image_grounding", lambda **kwargs: False)
    monkeypatch.setattr(generation_flow, "plan_reference_creative_flow", lambda **kwargs: _FakePlan())
    monkeypatch.setattr(generation_flow, "assess_generated_image", lambda *args, **kwargs: {})
    monkeypatch.setattr(generation_flow, "write_v2_observability_report", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        generation_flow,
        "prepare_garment_replacement_prompt",
        lambda **kwargs: PreparedEditPrompt(
            flow_mode="garment_replacement",
            edit_type="garment_replacement",
            display_prompt="replace garment only",
            model_prompt="replace garment only",
            change_summary_ptbr="Trocar a peça.",
            confidence=0.9,
            structured_edit_goal="replace garment only",
            structured_preserve_clause="keep person and scene untouched",
            reference_item_description="cardigan replacement",
            include_source_prompt_context=True,
            include_reference_item_description=True,
            use_structured_shell=True,
        ),
    )

    def fake_generate_images(**kwargs):
        captured["stage1_uploaded_images"] = list(kwargs.get("uploaded_images") or [])
        captured["stage1_prompt"] = kwargs.get("prompt")
        return [
            {
                "filename": "base.png",
                "url": "/outputs/base/base.png",
                "path": str(base_file),
                "size_kb": 1.0,
                "mime_type": "image/png",
            }
        ]

    monkeypatch.setattr(generation_flow, "generate_images", fake_generate_images)
    monkeypatch.setattr(
        generation_flow,
        "pick_best_stage1_candidate",
        lambda *args, **kwargs: (
            {
                "filename": "base.png",
                "url": "/outputs/base/base.png",
                "path": str(base_file),
                "size_kb": 1.0,
                "mime_type": "image/png",
            },
            [{"assessment": {}, "fidelity_gate": None, "index": 1}],
            1,
        ),
    )

    def fake_execute_image_edit_request(request):
        captured.setdefault("edit_requests", []).append(request)
        idx = len(captured["edit_requests"])
        return [
            {
                "filename": f"final_{idx}.png",
                "url": f"/outputs/edit/final_{idx}.png",
                "path": str(tmp_path / f"final_{idx}.png"),
                "size_kb": 1.0,
                "mime_type": "image/png",
            }
        ]

    monkeypatch.setattr(generation_flow, "execute_image_edit_request", fake_execute_image_edit_request)

    fake_agent = types.ModuleType("agent")

    def _run_agent_should_not_be_called(**kwargs):
        raise AssertionError("run_agent should not be called in upload vNext flow")

    fake_agent.run_agent = _run_agent_should_not_be_called
    sys.modules["agent"] = fake_agent

    response = generation_flow.run_generation_flow(
        uploaded_bytes=[b"img-a", b"img-b"],
        uploaded_filenames=["a.jpg", "b.jpg"],
        prompt="quero uma imagem nova",
        mode="natural",
        n_images=2,
        aspect_ratio="4:5",
        resolution="1K",
    )

    assert captured["stage1_uploaded_images"] == []
    assert captured["stage1_prompt"] == "PLANNER BASE PROMPT"
    assert len(captured["edit_requests"]) == 2
    assert all(request.lock_person is True for request in captured["edit_requests"])
    assert all(request.prepared_prompt.flow_mode == "garment_replacement" for request in captured["edit_requests"])
    assert response["stage1_prompt"] == "PLANNER BASE PROMPT"
    assert response["art_direction_summary"]["creative_source"] == "reference_planner"
    assert len(response["images"]) == 2
