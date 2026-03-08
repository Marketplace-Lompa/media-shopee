"""
Router: /history
Endpoints de consulta e gestão do histórico de gerações.
"""
from fastapi import APIRouter, HTTPException

from history import list_entries, count_entries, delete_entry

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def get_history(limit: int = 200, offset: int = 0):
    """Retorna histórico paginado (mais recentes primeiro)."""
    entries = list_entries(limit=min(limit, 500), offset=max(offset, 0))
    total = count_entries()
    return {
        "items": entries,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete("/{entry_id}")
async def remove_entry(entry_id: str):
    """Remove uma entry do histórico e arquivo do disco."""
    removed = delete_entry(entry_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Entry não encontrada")
    return {"status": "deleted", "id": entry_id}
