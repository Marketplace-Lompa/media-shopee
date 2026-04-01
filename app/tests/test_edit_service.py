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


import agent_runtime.editing.executor as executor
import agent_runtime.editing.freeform_flow as freeform_flow
import agent_runtime.editing.guided_angle_flow as guided_angle_flow
from agent_runtime.editing.contracts import ImageEditExecutionRequest, PreparedEditPrompt


def test_prepare_freeform_edit_prompt_maps_agent_result(monkeypatch) -> None:
    monkeypatch.setattr(
        freeform_flow,
        "refine_edit_instruction",
        lambda **kwargs: {
            "edit_type": "background",
            "edit_delta_prompt": "Edit this image: change only the background to a light studio.",
            "preserve_clause": "Keep the model and garment unchanged.",
            "change_summary_ptbr": "Trocar o fundo para estúdio claro.",
            "confidence": 0.81,
        },
    )

    prompt = freeform_flow.prepare_freeform_edit_prompt(
        edit_instruction="trocar o fundo",
        source_image_bytes=b"source",
        source_prompt="RAW photo",
        reference_images_bytes=None,
    )

    assert prompt.edit_type == "background"
    assert prompt.display_prompt.startswith("Edit this image:")
    assert "Keep the model and garment unchanged." in prompt.display_prompt
    assert prompt.model_prompt == prompt.display_prompt
    assert prompt.flow_mode == "freeform"
    assert prompt.use_structured_shell is True
    assert prompt.include_source_prompt_context is True
    assert prompt.change_summary_ptbr == "Trocar o fundo para estúdio claro."
    assert prompt.confidence == 0.81


def test_executor_builds_structured_shell_for_freeform(monkeypatch) -> None:
    captured: dict = {}

    def fake_generate_content(*, model, contents, config):
        captured["contents"] = contents
        return _Simple(parts=[_Part(inline_data=_Blob(mime_type="image/png", data=b"png-bytes"))])

    monkeypatch.setattr(executor.client.models, "generate_content", fake_generate_content)
    monkeypatch.setattr(executor, "_prepare_reference_batch", lambda images, limit: list(images or []))
    monkeypatch.setattr(executor, "_build_retry_reference_subset", lambda images, attempt, minimum_keep: list(images))
    monkeypatch.setattr(executor, "_extract_image_from_response", lambda response, session_id, image_index, session_dir: {
        "filename": f"gen_{session_id}_{image_index}.png",
        "url": f"/outputs/{session_id}/gen_{session_id}_{image_index}.png",
        "path": str(session_dir / f"gen_{session_id}_{image_index}.png"),
        "size_kb": 12.3,
        "mime_type": "image/png",
    })
    monkeypatch.setattr(executor, "_detect_image_mime", lambda data: "image/png")

    request = ImageEditExecutionRequest(
        source_image_bytes=b"source",
        prepared_prompt=PreparedEditPrompt(
            flow_mode="freeform",
            edit_type="background",
            display_prompt="Edit this image: change only the background to an off-white studio. Keep the garment texture and the model exactly unchanged.",
            model_prompt="Edit this image: change only the background to an off-white studio. Keep the garment texture and the model exactly unchanged.",
            change_summary_ptbr="Trocar apenas o fundo.",
            confidence=0.9,
            structured_edit_goal="Edit this image: change only the background to an off-white studio.",
            structured_preserve_clause="Keep the garment texture and the model exactly unchanged.",
            reference_item_description="Soft knit scarf with tonal ribbed texture.",
            include_source_prompt_context=True,
            include_reference_item_description=True,
            use_structured_shell=True,
        ),
        aspect_ratio="4:5",
        resolution="1K",
        session_id="edittest01",
        source_prompt_context="RAW photo, premium knitwear campaign in a minimalist apartment with warm daylight.",
        reference_images_bytes=[b"ref1"],
    )

    result = executor.execute_image_edit_request(request)

    assert result[0]["url"] == "/outputs/edittest01/gen_edittest01_1.png"
    assert result[0]["_debug_transport"]["trimmed_source_prompt_context"].startswith("RAW photo")
    assert result[0]["_debug_transport"]["prepared_prompt_snapshot"]["structured_edit_goal"] == "Edit this image: change only the background to an off-white studio."
    parts = captured["contents"][0].parts
    text_parts = [part.text for part in parts if getattr(part, "text", None)]

    assert any("ORIGINAL GENERATION PROMPT CONTEXT" in text for text in text_parts)
    assert any("EDIT GOAL — APPLY ONLY THIS CHANGE" in text for text in text_parts)
    assert any("PRESERVATION RULES — DO NOT CHANGE THESE ELEMENTS" in text for text in text_parts)
    assert any("REFERENCE ITEM DESCRIPTION" in text for text in text_parts)


def test_executor_adds_non_target_outfit_preservation_for_garment_replacement(monkeypatch) -> None:
    captured: dict = {}

    def fake_generate_content(*, model, contents, config):
        captured["contents"] = contents
        return _Simple(parts=[_Part(inline_data=_Blob(mime_type="image/png", data=b"png-bytes"))])

    monkeypatch.setattr(executor.client.models, "generate_content", fake_generate_content)
    monkeypatch.setattr(executor, "_prepare_reference_batch", lambda images, limit: list(images or []))
    monkeypatch.setattr(executor, "_build_retry_reference_subset", lambda images, attempt, minimum_keep: list(images))
    monkeypatch.setattr(executor, "_extract_image_from_response", lambda response, session_id, image_index, session_dir: {
        "filename": f"gen_{session_id}_{image_index}.png",
        "url": f"/outputs/{session_id}/gen_{session_id}_{image_index}.png",
        "path": str(session_dir / f"gen_{session_id}_{image_index}.png"),
        "size_kb": 12.3,
        "mime_type": "image/png",
    })
    monkeypatch.setattr(executor, "_detect_image_mime", lambda data: "image/png")

    request = ImageEditExecutionRequest(
        source_image_bytes=b"source",
        prepared_prompt=PreparedEditPrompt(
            flow_mode="garment_replacement",
            edit_type="garment_replacement",
            display_prompt="Replace only the placeholder garment.",
            model_prompt="Replace only the placeholder garment.",
            change_summary_ptbr="Trocar a peça.",
            confidence=0.9,
            structured_edit_goal="Replace only the placeholder garment.",
            structured_preserve_clause="Keep the person and scene unchanged.",
            reference_item_description="Textured knit pullover.",
            include_source_prompt_context=True,
            include_reference_item_description=True,
            use_structured_shell=True,
        ),
        aspect_ratio="4:5",
        resolution="1K",
        session_id="editgarment01",
        source_prompt_context="Keep the current creative scene intent.",
        reference_images_bytes=[b"ref1"],
        lock_person=True,
    )

    result = executor.execute_image_edit_request(request)

    parts = captured["contents"][0].parts
    text_parts = [part.text for part in parts if getattr(part, "text", None)]

    assert any("NON-TARGET OUTFIT PRESERVATION" in text for text in text_parts)
    assert result[0]["_debug_transport"]["prepared_prompt_snapshot"]["display_prompt"] == "Replace only the placeholder garment."


def test_prepare_guided_angle_prompt_is_independent_from_freeform() -> None:
    prompt = guided_angle_flow.prepare_guided_angle_prompt(
        edit_instruction="mudar o ângulo de forma leve e comercial",
        view_intent="soft_turn",
        distance_intent="preserve",
        pose_freedom="locked",
        angle_target=None,
        preserve_framing=True,
        preserve_camera_height=True,
        preserve_distance=True,
        preserve_pose=True,
        source_shot_type="wide",
    )

    assert prompt.flow_mode == "guided_angle"
    assert prompt.use_structured_shell is False
    assert prompt.include_source_prompt_context is False
    assert "commercial fashion photograph" in prompt.display_prompt
    assert "camera angle" in prompt.display_prompt
    assert "Do not redesign the clothing" in prompt.display_prompt


def test_prepare_guided_angle_prompt_keeps_current_view_when_only_distance_changes() -> None:
    prompt = guided_angle_flow.prepare_guided_angle_prompt(
        edit_instruction="mais próximo",
        view_intent="preserve",
        distance_intent="closer",
        pose_freedom="locked",
        angle_target=None,
        preserve_framing=True,
        preserve_camera_height=True,
        preserve_distance=False,
        preserve_pose=True,
        source_shot_type="medium",
    )

    assert "current viewing angle and overall shot composition as the baseline" in prompt.display_prompt
    assert "slightly closer camera distance as the primary change" in prompt.display_prompt
    assert "without introducing a new camera angle or subject rotation" in prompt.display_prompt
    assert "subtle three-quarter camera angle" not in prompt.display_prompt
    assert "camera repositioning around the subject" not in prompt.display_prompt


def test_executor_uses_image_first_and_single_prompt_for_guided_angle(monkeypatch) -> None:
    captured: dict = {}

    def fake_generate_content(*, model, contents, config):
        captured["contents"] = contents
        return _Simple(parts=[_Part(inline_data=_Blob(mime_type="image/png", data=b"png-bytes"))])

    monkeypatch.setattr(executor.client.models, "generate_content", fake_generate_content)
    monkeypatch.setattr(executor, "_prepare_reference_batch", lambda images, limit: list(images or []))
    monkeypatch.setattr(executor, "_build_retry_reference_subset", lambda images, attempt, minimum_keep: list(images))
    monkeypatch.setattr(executor, "_extract_image_from_response", lambda response, session_id, image_index, session_dir: {
        "filename": f"gen_{session_id}_{image_index}.png",
        "url": f"/outputs/{session_id}/gen_{session_id}_{image_index}.png",
        "path": str(session_dir / f"gen_{session_id}_{image_index}.png"),
        "size_kb": 12.3,
        "mime_type": "image/png",
    })
    monkeypatch.setattr(executor, "_detect_image_mime", lambda data: "image/png")

    request = ImageEditExecutionRequest(
        source_image_bytes=b"source",
        prepared_prompt=PreparedEditPrompt(
            flow_mode="guided_angle",
            edit_type="framing",
            display_prompt="Use the attached image as the source of truth. Create a new photograph from a clean left three-quarter camera viewpoint.",
            model_prompt="Use the attached image as the source of truth. Create a new photograph from a clean left three-quarter camera viewpoint.",
            change_summary_ptbr="Mudar o angulo.",
            confidence=0.9,
            include_source_prompt_context=False,
            include_reference_item_description=False,
            use_structured_shell=False,
        ),
        aspect_ratio="4:5",
        resolution="1K",
        session_id="editangle01",
        edit_submode="angle_transform",
        source_prompt_context="RAW photo, premium knitwear campaign in a minimalist apartment with warm daylight.",
    )

    executor.execute_image_edit_request(request)

    parts = captured["contents"][0].parts
    text_parts = [part.text for part in parts if getattr(part, "text", None)]

    assert getattr(parts[0], "inline_data", None) is not None
    assert getattr(parts[1], "text", "").startswith("BASE IMAGE TO EDIT")
    assert any("clean left three-quarter camera viewpoint" in text for text in text_parts)
    assert not any("ORIGINAL GENERATION PROMPT CONTEXT" in text for text in text_parts)
    assert not any("EDIT GOAL — APPLY ONLY THIS CHANGE" in text for text in text_parts)
    assert not any("PRESERVATION RULES — DO NOT CHANGE THESE ELEMENTS" in text for text in text_parts)
