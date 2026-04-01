from __future__ import annotations

from io import BytesIO
from pathlib import Path
import importlib
import sys

from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_result import finalize_prompt_agent_result


class _FakeImageResponse:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple, dict]] = []

    def generate_content(self, *args: object, **kwargs: object) -> object:
        self.calls.append((args, kwargs))
        return object()


def _fake_client() -> object:
    class _Client:
        def __init__(self) -> None:
            self.models = _FakeImageResponse()

    return _Client()


def _load_generator_with_key(monkeypatch) -> object:
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "unit-test-key")

    backend_dir = Path(__file__).resolve().parents[1] / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    if "generator" in sys.modules:
        sys.modules.pop("generator")
    return importlib.import_module("generator")


def _dummy_image_bytes() -> bytes:
    with BytesIO() as buf:
        image = Image.new("RGB", (64, 64), (250, 235, 220))
        image.save(buf, format="PNG")
        return buf.getvalue()


def test_final_prompt_payload_reaches_generator_without_internal_labels(capsys, monkeypatch) -> None:
    generator = _load_generator_with_key(monkeypatch)
    fake_client = _fake_client()
    generator.client = fake_client
    generator._extract_image_from_response = lambda *args, **kwargs: {
        "index": 1,
        "filename": "mock.png",
        "url": "/outputs/session/mock.png",
        "path": "/tmp/mock.png",
        "size_kb": 1.0,
        "mime_type": "image/png",
    }

    agent_result = finalize_prompt_agent_result(
        result={
            "prompt": (
                "RAW photo, a Brazilian woman in late 20s "
                "CASTING CHECKLIST: features blend"
            ),
            "shot_type": "three_quarter",
        },
        has_images=False,
        has_prompt=True,
        user_prompt=None,
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
        profile="A Brazilian commercial prompt profile",
        scenario="quiet living room",
        diversity_target={
            "casting_state": {
                "age": "late 20s to early 30s",
                "face_structure": "heart-shaped face with high cheekbones",
                "hair": "shoulder-length chocolate brown waves with caramel ends",
                "presence": "natural Brazilian presence",
                "expression": "neutral mouth, relaxed off-camera attention",
            },
            "profile_id": "natural:natural_commercial",
        },
        mode_id="natural",
        framing_profile="three_quarter",
        camera_type="natural",
        capture_geometry="three_quarter_eye_level",
        lighting_profile="soft",
        pose_energy="relaxed",
        casting_profile="natural_commercial",
    )

    final_prompt = agent_result["prompt"]

    source_image = _dummy_image_bytes()
    generator.edit_image(
        source_image_bytes=source_image,
        edit_prompt=final_prompt,
        aspect_ratio="4:5",
        resolution="1K",
        thinking_level="HIGH",
        reference_images_bytes=[],
        use_image_grounding=False,
        lock_person=False,
    )

    assert fake_client.models.calls, "Cliente fake não foi chamado."
    _, call_kwargs = fake_client.models.calls[0]
    content = call_kwargs["contents"][0]
    payload_parts = [str(part.text or "") for part in content.parts if getattr(part, "text", None)]
    payload = " ".join(payload_parts).lower()
    assert "casting checklist" not in payload
    assert "profile_hint" not in payload
    assert "casting_state" not in payload
    assert "late 20s" in payload
    assert "high cheekbones" in payload
    assert "shoulder-length chocolate brown waves" in payload
    assert "natural brazilian presence" in payload
    assert "off-camera" in payload

    logs = capsys.readouterr().out
    assert "[GENERATOR_DEBUG] stage=edit_image attempt=1" in logs
    assert "lock_person=False" in logs
    assert "prompt=" in logs

    final_low = final_prompt.lower()
    assert "castingsurface" not in final_low
    assert "casting_direction" not in final_low
