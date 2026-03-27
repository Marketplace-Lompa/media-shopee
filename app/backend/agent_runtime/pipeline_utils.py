"""
Utilidades compartilhadas para pipelines de geração.

Funções de IO, slug, detecção de formato — usadas tanto pelo
pipeline V2 quanto pela futura orquestração unificada.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from config import OUTPUTS_DIR


def guess_image_extension(image_bytes: bytes) -> str:
    """Detecta extensão de imagem por magic bytes."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "webp"
    return "jpg"


def safe_asset_slug(raw_name: str, *, fallback: str) -> str:
    """Gera slug seguro a partir de um filename."""
    name = str(raw_name or "").strip().lower()
    stem = Path(name).stem if name else fallback
    slug = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return slug[:48] or fallback


def persist_review_inputs(
    *,
    session_id: str,
    uploaded_bytes: list[bytes],
    uploaded_filenames: list[str],
    selected_bytes: dict[str, Any],
    selected_names: dict[str, Any],
) -> dict[str, list[str]]:
    """Salva inputs de referência no disco para auditoria/review."""
    review_dir = OUTPUTS_DIR / f"v2diag_{session_id}" / "inputs"
    review_dir.mkdir(parents=True, exist_ok=True)

    def _write_group(group_name: str, items: list[bytes], names: list[str]) -> list[str]:
        group_dir = review_dir / group_name
        group_dir.mkdir(parents=True, exist_ok=True)
        urls: list[str] = []
        for idx, item in enumerate(items):
            slug = safe_asset_slug(
                names[idx] if idx < len(names) else "",
                fallback=f"{group_name}_{idx + 1}",
            )
            ext = guess_image_extension(item)
            filename = f"{idx + 1:02d}_{slug}.{ext}"
            target = group_dir / filename
            target.write_bytes(item)
            urls.append(f"/outputs/v2diag_{session_id}/inputs/{group_name}/{filename}")
        return urls

    original_urls = _write_group("original_references", uploaded_bytes, uploaded_filenames)
    base_generation_urls = _write_group(
        "base_generation",
        list(selected_bytes.get("base_generation", []) or []),
        list(selected_names.get("base_generation", []) or []),
    )
    edit_anchor_urls = _write_group(
        "edit_anchors",
        list(selected_bytes.get("edit_anchors", []) or []),
        list(selected_names.get("edit_anchors", []) or []),
    )
    identity_safe_urls = _write_group(
        "identity_safe",
        list(selected_bytes.get("identity_safe", []) or []),
        list(selected_names.get("identity_safe", []) or []),
    )
    return {
        "original_references": original_urls,
        "base_generation": base_generation_urls,
        "edit_anchors": edit_anchor_urls,
        "identity_safe": identity_safe_urls,
    }
