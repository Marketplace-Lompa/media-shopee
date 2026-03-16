"""
Reference Pool Manager — gerencia as imagens de referência (LoRA-like).
Organiza por tipo: modelo | roupa | cenario
Limite: POOL_MAX_REFS imagens passadas ao Nano por geração.
"""
import uuid
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from config import POOL_DIR, POOL_MAX_REFS, POOL_TYPES

# Metadata file
POOL_META = POOL_DIR / "pool.json"

# CADEADO ASSÍNCRONO: Impede que dois jobs corrompam o JSON gravando ao mesmo tempo
_meta_lock = asyncio.Lock()

def _read_meta_sync() -> List[dict]:
    """Lê o JSON de forma síncrona (será chamado via Thread)"""
    if POOL_META.exists():
        try:
            content = POOL_META.read_text(encoding="utf-8")
            if not content.strip():
                return []
            return json.loads(content)
        except json.JSONDecodeError:
            # Se o arquivo corrompeu no passado, NÃO MATA o job. Retorna lista vazia.
            return []
    return []

def _write_meta_sync(items: List[dict]):
    """Grava o JSON de forma síncrona (será chamado via Thread)"""
    POOL_META.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

async def _load_meta() -> List[dict]:
    # Joga a leitura para uma Thread separada para não congelar a API
    return await asyncio.to_thread(_read_meta_sync)

async def _save_meta(items: List[dict]):
    # Joga a escrita para uma Thread separada para não congelar a API
    await asyncio.to_thread(_write_meta_sync, items)


async def add_reference(file_bytes: bytes, original_filename: str, ref_type: str) -> dict:
    """Adiciona uma imagem ao pool de forma não-bloqueante. Retorna o item criado."""
    if ref_type not in POOL_TYPES:
        raise ValueError(f"Tipo inválido: {ref_type}. Use: {POOL_TYPES}")

    item_id = str(uuid.uuid4())[:8]
    ext = Path(original_filename).suffix.lower() or ".jpg"
    filename = f"{ref_type}_{item_id}{ext}"
    dest = POOL_DIR / filename
    
    # 1. Salva a imagem no disco SEM BLOQUEAR o Event Loop
    await asyncio.to_thread(dest.write_bytes, file_bytes)

    item = {
        "id": item_id,
        "filename": filename,
        "type": ref_type,
        "size_kb": round(len(file_bytes) / 1024, 1),
        "added_at": datetime.now().isoformat(),
    }

    # 2. Bloqueia o JSON com o cadeado para evitar corrupção por concorrência
    async with _meta_lock:
        items = await _load_meta()
        items.append(item)
        await _save_meta(items)
        
    return item

async def list_references(ref_type: Optional[str] = None) -> List[dict]:
    """Lista todas as refs de forma segura e assíncrona."""
    # Colocamos lock na leitura para garantir que não lemos enquanto outro job salva
    async with _meta_lock:
        items = await _load_meta()
        
    if ref_type:
        items = [i for i in items if i["type"] == ref_type]
    return items

async def remove_reference(item_id: str) -> bool:
    """Remove uma referência pelo ID de forma assíncrona."""
    filename_to_delete = None
    
    # 1. Abre o cadeado, atualiza o JSON e descobre qual arquivo deletar
    async with _meta_lock:
        items = await _load_meta()
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return False
            
        filename_to_delete = item["filename"]
        new_items = [i for i in items if i["id"] != item_id]
        await _save_meta(new_items)
        
    # 2. Deleta a imagem do disco via Thread fora do Cadeado (mais rápido)
    if filename_to_delete:
        f = POOL_DIR / filename_to_delete
        def _delete_file():
            if f.exists():
                f.unlink()
        await asyncio.to_thread(_delete_file)
        
    return True
