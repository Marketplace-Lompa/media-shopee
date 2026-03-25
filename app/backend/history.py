"""
Gerenciamento de histórico de gerações.
Persistência simples em JSON + cleanup automático de sessões antigas.
"""
import json
import shutil
import time
from pathlib import Path
from typing import Any, Optional

import os

from config import OUTPUTS_DIR

_custom = os.getenv("HISTORY_PATH")
HISTORY_FILE = Path(_custom) if _custom else OUTPUTS_DIR / "history.json"

# ── Limite de sessões ─────────────────────────────────────────────

MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "50"))


def _load() -> list[dict[str, Any]]:
    """Carrega histórico do JSON."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict[str, Any]]) -> None:
    """Salva histórico no JSON."""
    HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_entry(
    session_id: str,
    filename: str,
    url: str,
    prompt: str,
    thinking_level: Optional[str] = None,
    shot_type: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    grounding_effective: bool = False,
    references: Optional[list[str]] = None,
    source_session_id: Optional[str] = None,
    edit_instruction: Optional[str] = None,
    # ── Metadata de auditoria ─────────────────────────────────────
    base_prompt: Optional[str] = None,
    camera_and_realism: Optional[str] = None,
    camera_profile: Optional[str] = None,
    grounding_mode: Optional[str] = None,
    reason_codes: Optional[list[str]] = None,
    # ── Parâmetros de geração (observabilidade) ───────────────────
    preset: Optional[str] = None,
    scene_preference: Optional[str] = None,
    fidelity_mode: Optional[str] = None,
    pose_flex_mode: Optional[str] = None,
    pipeline_mode: Optional[str] = None,
    optimized_prompt: Optional[str] = None,
    mode: Optional[str] = None,
    # ── Marketplace ───────────────────────────────────────────────
    marketplace_channel: Optional[str] = None,
    marketplace_operation: Optional[str] = None,
    slot_id: Optional[str] = None,
) -> dict[str, Any]:
    """Adiciona uma entrada ao histórico e retorna a entry criada."""
    # ID legível e referenciável: "{session_id}:{slot_id}" (marketplace)
    # ou "{session_id}:t{timestamp_s}" (geração padrão — único por imagem)
    _id_suffix = slot_id if slot_id else f"t{int(time.time())}"
    entry = {
        "id": f"{session_id}:{_id_suffix}",
        "session_id": session_id,
        "filename": filename,
        "url": url,
        "prompt": prompt,
        "thinking_level": thinking_level,
        "shot_type": shot_type,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "grounding_effective": grounding_effective,
        "references": references or [],
        "created_at": int(time.time() * 1000),
        # Auditoria — fallback None para compatibilidade com entries antigas
        "base_prompt": base_prompt or None,
        "camera_and_realism": camera_and_realism or None,
        "camera_profile": camera_profile or None,
        "grounding_mode": grounding_mode or None,
        "reason_codes": reason_codes or [],
        # Parâmetros de geração (observabilidade)
        "preset": preset or None,
        "scene_preference": scene_preference or None,
        "fidelity_mode": fidelity_mode or None,
        "pose_flex_mode": pose_flex_mode or None,
        "pipeline_mode": pipeline_mode or None,
        "optimized_prompt": optimized_prompt or None,
        "mode": mode or None,
        # Marketplace
        "marketplace_channel": marketplace_channel or None,
        "marketplace_operation": marketplace_operation or None,
        "slot_id": slot_id or None,
    }
    if source_session_id:
        entry["source_session_id"] = source_session_id
    if edit_instruction:
        entry["edit_instruction"] = edit_instruction
    entries = _load()
    entries.insert(0, entry)  # mais recente primeiro
    _save(entries)
    return entry


def list_entries(limit: int = 200, offset: int = 0) -> list[dict[str, Any]]:
    """Retorna lista paginada do histórico (mais recentes primeiro)."""
    entries = _load()
    return entries[offset : offset + limit]


def count_entries() -> int:
    """Retorna total de entries."""
    return len(_load())


def delete_entry(entry_id: str) -> bool:
    """Remove uma entry do histórico e arquivo do disco."""
    entries = _load()
    to_remove = None
    for e in entries:
        if e["id"] == entry_id:
            to_remove = e
            break

    if not to_remove:
        return False

    # Tenta remover arquivo do disco
    url = to_remove.get("url", "")
    if url.startswith("/outputs/"):
        filepath = OUTPUTS_DIR.parent / url.lstrip("/")
        if filepath.exists():
            filepath.unlink(missing_ok=True)

    entries = [e for e in entries if e["id"] != entry_id]
    _save(entries)
    return True


def purge_oldest() -> int:
    """
    Remove sessões mais antigas quando total de sessões excede MAX_SESSIONS.
    Retorna número de sessões removidas.
    """
    entries = _load()

    # Coletar sessões únicas em ordem (mais recente primeiro)
    seen_sessions: list[str] = []
    for e in entries:
        sid = e.get("session_id", "")
        if sid and sid not in seen_sessions:
            seen_sessions.append(sid)

    if len(seen_sessions) <= MAX_SESSIONS:
        return 0

    # Sessões a manter (as MAX_SESSIONS mais recentes)
    keep_sessions = set(seen_sessions[:MAX_SESSIONS])
    remove_sessions = set(seen_sessions[MAX_SESSIONS:])

    # Filtrar entries
    new_entries = [e for e in entries if e.get("session_id", "") in keep_sessions]
    _save(new_entries)

    # Remover pastas do disco relacionadas ao session_id
    removed = 0
    for sid in remove_sessions:
        # Pipeline v2 cria múltiplas pastas com o ID (ex: v2base_{sid}, v2edit_{sid}_1)
        for d in OUTPUTS_DIR.glob(f"*{sid}*"):
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
                removed += 1
                
        print(f"[CLEANUP] 🗑️  Removed session artifacts for {sid}")

    print(f"[CLEANUP] Purged {removed} sessions, kept {len(keep_sessions)}")
    return removed
