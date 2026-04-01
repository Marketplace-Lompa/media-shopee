from __future__ import annotations

import importlib
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
        self.models = _Simple(generate_content=lambda *a, **k: _Simple(parts=[]))


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


def test_generate_images_attaches_transport_debug(monkeypatch) -> None:
    if "generator" in sys.modules:
        sys.modules.pop("generator")
    generator = importlib.import_module("generator")

    monkeypatch.setattr(generator.client.models, "generate_content", lambda *args, **kwargs: _Simple(parts=[]))
    monkeypatch.setattr(
        generator,
        "_extract_image_from_response",
        lambda response, session_id, image_index, session_dir: {
            "filename": f"gen_{image_index}.png",
            "url": f"/outputs/{session_id}/gen_{image_index}.png",
            "path": str(session_dir / f"gen_{image_index}.png"),
            "size_kb": 1.0,
            "mime_type": "image/png",
        },
    )

    result = generator.generate_images(
        prompt="clean commercial knitwear base",
        thinking_level="MINIMAL",
        aspect_ratio="4:5",
        resolution="1K",
        n_images=1,
        uploaded_images=[],
        grounded_images=[],
        session_id="transporttest01",
        structural_hint="waist-length knit pullover",
        use_image_grounding=False,
    )

    assert result[0]["_debug_transport"]["generator_effective_prompt"] == "clean commercial knitwear base"
    assert result[0]["_debug_transport"]["generator_text_blocks"] == ["clean commercial knitwear base"]
    assert result[0]["_debug_transport"]["uploaded_reference_count"] == 0
    assert result[0]["_debug_transport"]["grounded_reference_count"] == 0
