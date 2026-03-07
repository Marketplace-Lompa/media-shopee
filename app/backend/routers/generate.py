"""
Router: POST /generate
Orquestra Agent → Generator → Response.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from models import GenerateRequest, GenerateResponse, GeneratedImage
from agent import run_agent
from generator import generate_images
from pool import get_pool_for_generation, get_pool_context_summary
from config import VALID_ASPECT_RATIOS, VALID_RESOLUTIONS, VALID_N_IMAGES

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResponse)
async def generate(
    prompt: Optional[str]    = Form(default=None),
    aspect_ratio: str        = Form(default="1:1"),
    resolution: str          = Form(default="1K"),
    n_images: int            = Form(default=1),
    images: List[UploadFile] = File(default=[]),
):
    """
    Gera imagens via pipeline: Prompt Agent → Nano Banana 2.

    - prompt: opcional — agente atua mesmo sem prompt
    - images: imagens de referência para análise (até 14, conforme doc Nano)
    - aspect_ratio: 1:1 (default), 3:4, 4:3, 9:16, 16:9
    - resolution: 1K (default), 2K, 4K
    - n_images: 1-4
    """
    # Validações
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise HTTPException(400, f"aspect_ratio inválido. Use: {VALID_ASPECT_RATIOS}")
    if resolution not in VALID_RESOLUTIONS:
        raise HTTPException(400, f"resolution inválida. Use: {VALID_RESOLUTIONS}")
    if n_images not in VALID_N_IMAGES:
        raise HTTPException(400, f"n_images inválido. Use: {VALID_N_IMAGES}")

    # Ler imagens enviadas pelo usuário
    uploaded_bytes = []
    for img in images[:14]:  # Doc Nano: máximo 14 imagens de entrada por request
        uploaded_bytes.append(await img.read())

    # Contexto do pool
    pool_images = get_pool_for_generation()
    pool_context = get_pool_context_summary()

    # Etapa 1: Prompt Agent decide prompt + thinking
    try:
        agent_result = run_agent(
            user_prompt=prompt,
            uploaded_images=uploaded_bytes if uploaded_bytes else None,
            pool_context=pool_context,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )
    except Exception as e:
        raise HTTPException(500, f"Erro no Prompt Agent: {str(e)}")

    optimized_prompt  = agent_result.get("prompt", "")
    thinking_level    = agent_result.get("thinking_level", "MINIMAL")
    thinking_reason   = agent_result.get("thinking_reason", "")
    shot_type         = agent_result.get("shot_type", "auto")
    realism_level     = agent_result.get("realism_level", 2)

    # Etapa 2: Gerar imagens
    session_id = str(uuid.uuid4())[:8]
    try:
        raw_images = generate_images(
            prompt=optimized_prompt,
            thinking_level=thinking_level,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=n_images,
            pool_images=pool_images if pool_images else None,
            uploaded_images=uploaded_bytes if uploaded_bytes else None,  # envio casado
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(500, f"Erro no Image Generator: {str(e)}")

    return GenerateResponse(
        optimized_prompt=optimized_prompt,
        thinking_level=thinking_level,
        thinking_reason=thinking_reason,
        shot_type=shot_type,
        realism_level=realism_level,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        images=[GeneratedImage(**img) for img in raw_images],
        pool_refs_used=len(pool_images),
    )
