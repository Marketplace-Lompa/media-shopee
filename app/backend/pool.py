"""
Reference Pool Manager — gerencia as imagens de referência (LoRA-like).
Organiza por tipo: modelo | roupa | cenario
Limite: POOL_MAX_REFS imagens passadas ao Nano por geração.
"""
import uuid
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from config import POOL_DIR, POOL_MAX_REFS, POOL_TYPES

# Metadata file
POOL_META = POOL_DIR / "pool.json"


def _load_meta() -> List[dict]:
    if POOL_META.exists():
        return json.loads(POOL_META.read_text())
    return []


def _save_meta(items: List[dict]):
    POOL_META.write_text(json.dumps(items, ensure_ascii=False, indent=2))


def add_reference(file_bytes: bytes, original_filename: str, ref_type: str) -> dict:
    """Adiciona uma imagem ao pool. Retorna o item criado."""
    if ref_type not in POOL_TYPES:
        raise ValueError(f"Tipo inválido: {ref_type}. Use: {POOL_TYPES}")

    item_id = str(uuid.uuid4())[:8]
    ext = Path(original_filename).suffix.lower() or ".jpg"
    filename = f"{ref_type}_{item_id}{ext}"
    dest = POOL_DIR / filename
    dest.write_bytes(file_bytes)

    item = {
        "id": item_id,
        "filename": filename,
        "type": ref_type,
        "size_kb": round(len(file_bytes) / 1024, 1),
        "added_at": datetime.now().isoformat(),
    }

    items = _load_meta()
    items.append(item)
    _save_meta(items)
    return item


def list_references(ref_type: Optional[str] = None) -> List[dict]:
    """Lista todas as refs, opcionalmente filtradas por tipo."""
    items = _load_meta()
    if ref_type:
        items = [i for i in items if i["type"] == ref_type]
    return items


def remove_reference(item_id: str) -> bool:
    """Remove uma referência pelo ID. Retorna True se removida."""
    items = _load_meta()
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        return False
    # Remove arquivo
    f = POOL_DIR / item["filename"]
    if f.exists():
        f.unlink()
    # Remove metadata
    _save_meta([i for i in items if i["id"] != item_id])
    return True


def get_pool_for_generation() -> List[bytes]:
    """
    Retorna até POOL_MAX_REFS imagens como bytes para enviar ao Nano Banana 2.
    Prioridade: roupa > modelo > cenario (a roupa é o protagonista).
    """
    items = _load_meta()

    # Ordena por prioridade: roupa primeiro, depois modelo, depois cenario
    priority = {"roupa": 0, "modelo": 1, "cenario": 2}
    items.sort(key=lambda x: priority.get(x["type"], 9))

    # Limita ao máximo configurado
    items = items[:POOL_MAX_REFS]

    result = []
    for item in items:
        f = POOL_DIR / item["filename"]
        if f.exists():
            result.append(f.read_bytes())
    return result


def get_pool_context_summary() -> str:
    """Retorna um resumo textual do pool para o agente entender o contexto."""
    items = _load_meta()
    if not items:
        return "No reference pool available."

    by_type = {"modelo": [], "roupa": [], "cenario": []}
    for item in items:
        by_type.get(item["type"], []).append(item["filename"])

    lines = ["Reference pool context:"]
    if by_type["modelo"]:
        lines.append(f"- {len(by_type['modelo'])} model reference(s): use these to maintain model identity/skin tone/body type")
    if by_type["roupa"]:
        lines.append(f"- {len(by_type['roupa'])} garment reference(s): reproduce this exact garment — fabric, color, cut, construction")
    if by_type["cenario"]:
        lines.append(f"- {len(by_type['cenario'])} scenario reference(s): match lighting, location, mood")

    return "\n".join(lines)
