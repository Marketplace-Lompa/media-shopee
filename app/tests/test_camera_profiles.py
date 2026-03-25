from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_result import _sanitize_camera_block, _MINIMAL_CAPTURE_FALLBACK


def test_sanitize_strips_skin_texture_and_devices() -> None:
    block = _sanitize_camera_block(
        "Sony A7R IV, 85mm lens. Natural late-afternoon side light highlighting fabric sheen and subtle skin texture. "
        "Visible pores and subtle peach fuzz. Crisp seam stitching.",
    ).lower()
    assert "skin texture" not in block
    assert "pores" not in block
    assert "peach fuzz" not in block
    assert "sony" not in block
    assert "85mm" not in block
    assert "lens" not in block
    assert ("fabric sheen" in block) or ("crisp seam stitching" in block)


def test_sanitize_strips_persona_signals() -> None:
    block = _sanitize_camera_block(
        "Flawless unretouched skin realism with soft natural light. "
        "Ford Models Brazil new face editorial talent. "
        "Gentle depth of field with fabric detail."
    ).lower()
    assert "ford models" not in block
    assert "new face" not in block
    assert "editorial talent" not in block
    assert "flawless unretouched" not in block
    assert "depth of field" in block or "fabric detail" in block


def test_sanitize_empty_returns_minimal_fallback() -> None:
    assert _sanitize_camera_block("") == _MINIMAL_CAPTURE_FALLBACK
    assert _sanitize_camera_block("   ") == _MINIMAL_CAPTURE_FALLBACK
    assert _sanitize_camera_block(None) == _MINIMAL_CAPTURE_FALLBACK


def test_sanitize_preserves_valid_camera_text() -> None:
    valid = "Soft natural light with gentle depth of field and warm tones."
    result = _sanitize_camera_block(valid)
    assert "natural light" in result.lower()
    assert "depth of field" in result.lower()


def test_sanitize_enforces_word_cap() -> None:
    long_text = " ".join(["word"] * 100) + "."
    result = _sanitize_camera_block(long_text)
    word_count = len(result.split())
    assert word_count <= 55  # 52 + small margin from cleanup
