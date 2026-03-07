"""
Router: GET/POST/DELETE /pool
Gerencia o Reference Pool (LoRA-like).
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from models import PoolAddResponse, PoolListResponse, PoolItem
from pool import add_reference, list_references, remove_reference
from config import POOL_TYPES

router = APIRouter(prefix="/pool", tags=["pool"])


@router.get("", response_model=PoolListResponse)
async def list_pool(type: str = None):
    """Lista imagens do pool, opcionalmente filtradas por tipo."""
    if type and type not in POOL_TYPES:
        raise HTTPException(400, f"Tipo inválido. Use: {POOL_TYPES}")
    items = list_references(ref_type=type)
    return PoolListResponse(
        items=[PoolItem(**i) for i in items],
        total=len(items),
    )


@router.post("/add", response_model=PoolAddResponse)
async def add_to_pool(
    type: str = Form(..., description="modelo | roupa | cenario"),
    file: UploadFile = File(...),
):
    """Adiciona uma imagem de referência ao pool."""
    if type not in POOL_TYPES:
        raise HTTPException(400, f"Tipo inválido. Use: {POOL_TYPES}")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "Arquivo vazio.")

    item = add_reference(
        file_bytes=content,
        original_filename=file.filename,
        ref_type=type,
    )
    return PoolAddResponse(
        id=item["id"],
        filename=item["filename"],
        type=item["type"],
        message=f"Referência adicionada ao pool como '{type}'.",
    )


@router.delete("/{item_id}")
async def delete_from_pool(item_id: str):
    """Remove uma referência do pool pelo ID."""
    removed = remove_reference(item_id)
    if not removed:
        raise HTTPException(404, f"Item '{item_id}' não encontrado no pool.")
    return {"message": f"Referência '{item_id}' removida com sucesso."}


@router.get("/types")
async def pool_types():
    """Retorna os tipos válidos de referência."""
    return {"types": POOL_TYPES}
