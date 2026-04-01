from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from config import OUTPUTS_DIR

OBSERVABILITY_SCHEMA_VERSION = "v2.trace.1"


def _deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dict(current, value)
        else:
            merged[key] = value
    return merged


def write_v2_observability_report(session_id: str, payload: dict[str, Any]) -> dict[str, str]:
    report_dir = OUTPUTS_DIR / f"v2diag_{session_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.json"

    body = dict(payload)
    body.setdefault("schema_version", OBSERVABILITY_SCHEMA_VERSION)
    body["session_id"] = session_id
    body["written_at"] = int(time.time() * 1000)

    report_path.write_text(
        json.dumps(body, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "report_path": str(report_path),
        "report_url": f"/outputs/{report_dir.name}/{report_path.name}",
    }


def merge_v2_observability_report(
    session_id: str,
    patch: dict[str, Any],
) -> dict[str, str]:
    report_dir = OUTPUTS_DIR / f"v2diag_{session_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.json"

    current: dict[str, Any] = {}
    if report_path.exists():
        try:
            current = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            current = {}

    merged = _deep_merge_dict(current, patch)
    merged.setdefault("schema_version", OBSERVABILITY_SCHEMA_VERSION)
    merged["session_id"] = session_id
    merged["written_at"] = int(time.time() * 1000)
    report_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "report_path": str(report_path),
        "report_url": f"/outputs/{report_dir.name}/{report_path.name}",
    }


def persist_prompt_artifacts(
    *,
    session_id: str,
    prompts: dict[str, str],
) -> dict[str, str]:
    prompts_dir = OUTPUTS_DIR / f"v2diag_{session_id}" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    saved: dict[str, str] = {}
    for name, text in prompts.items():
        content = str(text or "").strip()
        if not content:
            continue
        filename = f"{safe_asset_slug(name, fallback='prompt')}.txt"
        target = prompts_dir / filename
        target.write_text(content, encoding="utf-8")
        saved[name] = f"/outputs/v2diag_{session_id}/prompts/{filename}"
    return saved


# ── Persistência de assets de review/diagnóstico ─────────────────────────

def guess_image_extension(image_bytes: bytes) -> str:
    """Detecta extensão de imagem a partir dos magic bytes."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "webp"
    return "jpg"


def safe_asset_slug(raw_name: str, *, fallback: str) -> str:
    """Gera slug seguro para nomes de assets."""
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
    """Persiste assets de input para review/diagnóstico pós-geração."""
    review_dir = OUTPUTS_DIR / f"v2diag_{session_id}" / "inputs"
    review_dir.mkdir(parents=True, exist_ok=True)

    def _write_group(group_name: str, items: list[bytes], names: list[str]) -> list[str]:
        group_dir = review_dir / group_name
        group_dir.mkdir(parents=True, exist_ok=True)
        urls: list[str] = []
        for idx, item in enumerate(items):
            slug = safe_asset_slug(names[idx] if idx < len(names) else "", fallback=f"{group_name}_{idx + 1}")
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
