from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.camera import _default_camera_realism_block, _normalize_camera_realism_block


def test_catalog_clean_default_is_neutral_about_skin_texture() -> None:
    block = _default_camera_realism_block("medium", profile="catalog_clean").lower()
    assert "pores" not in block
    assert "skin texture" not in block
    assert "sensor grain" not in block


def test_catalog_natural_default_is_neutral_about_skin_texture() -> None:
    block = _default_camera_realism_block("medium", profile="catalog_natural").lower()
    assert "pores" not in block
    assert "flyaway hairs" not in block
    assert "skin texture" not in block


def test_normalize_camera_realism_block_strips_skin_surface_treatment() -> None:
    block = _normalize_camera_realism_block(
        "Natural late-afternoon side light highlighting fabric sheen and subtle skin texture. "
        "Visible pores and subtle peach fuzz. Crisp seam stitching.",
        "medium",
        profile="catalog_natural",
    ).lower()
    assert "skin texture" not in block
    assert "pores" not in block
    assert "peach fuzz" not in block
    assert "fabric sheen" in block
    assert "crisp seam stitching" in block
