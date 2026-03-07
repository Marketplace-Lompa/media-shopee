"""
Schemas Pydantic para request/response da API.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Payload do POST /generate"""
    prompt: Optional[str] = Field(
        default=None,
        description="Descrição em pt-BR (opcional — agente age mesmo sem prompt)"
    )
    aspect_ratio: str = Field(
        default="1:1",
        description="Proporção da imagem: 1:1, 3:4, 4:3, 9:16, 16:9"
    )
    resolution: str = Field(
        default="1K",
        description="Resolução: 1K (padrão), 2K, 4K"
    )
    n_images: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Número de imagens a gerar (1-4)"
    )


class GeneratedImage(BaseModel):
    """Uma imagem gerada"""
    index: int
    filename: str
    url: str          # caminho relativo servido pelo FastAPI: /outputs/{session}/{file}
    size_kb: float
    mime_type: str


class GenerateResponse(BaseModel):
    """Resposta do POST /generate"""
    optimized_prompt: str = Field(description="Prompt otimizado pelo agente")
    thinking_level: str   = Field(description="Nível de thinking decidido pelo agente")
    thinking_reason: str  = Field(description="Justificativa do thinking em pt-BR")
    shot_type: str        = Field(default="auto", description="Tipo de shot decidido pelo agente: wide, medium, close-up, auto")
    realism_level: int    = Field(default=2, description="Nível de realismo 1-3 decidido pelo agente")
    aspect_ratio: str
    resolution: str
    images: List[GeneratedImage]
    pool_refs_used: int   = Field(description="Qtd de refs do pool enviadas ao Nano")


class PoolItem(BaseModel):
    """Um item do Reference Pool"""
    id: str
    filename: str
    type: str       # modelo | roupa | cenario
    size_kb: float
    added_at: str


class PoolAddResponse(BaseModel):
    """Resposta do POST /pool/add"""
    id: str
    filename: str
    type: str
    message: str


class PoolListResponse(BaseModel):
    """Resposta do GET /pool"""
    items: List[PoolItem]
    total: int
