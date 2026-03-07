"""
Image Generator — Nano Banana 2 (gemini-3.1-flash-image-preview).

- BLOCK_NONE em todas as categorias (moda/lingerie)
- Gera N imagens em sequência (API não suporta batch paralelo nativo)
- Aceita imagens do pool como contexto visual (LoRA-like)
- Salva outputs em app/outputs/{session_id}/
"""
import uuid
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types

from config import (
    GOOGLE_AI_API_KEY,
    MODEL_IMAGE,
    SAFETY_CONFIG,
    ROOT_DIR,
)

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

OUTPUTS_DIR = ROOT_DIR / "app" / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_images(
    prompt: str,
    thinking_level: str,
    aspect_ratio: str,
    resolution: str,
    n_images: int,
    pool_images: Optional[List[bytes]] = None,
    session_id: Optional[str] = None,
) -> List[dict]:
    """
    Gera n_images imagens com o Nano Banana 2.

    Retorna lista de dicts:
    [{"filename": str, "path": str, "size_kb": float, "mime_type": str}, ...]
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    session_dir = OUTPUTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for i in range(n_images):
        # Montar contents: começa pelas imagens do pool (contexto visual)
        content_parts = []

        if pool_images:
            for img_bytes in pool_images:
                content_parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)
                    )
                )

        # Prompt textual (sempre por último para ter peso máximo)
        content_parts.append(types.Part(text=prompt))

        response = client.models.generate_content(
            model=MODEL_IMAGE,
            contents=[types.Content(role="user", parts=content_parts)],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=resolution,
                ),
                thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
                safety_settings=SAFETY_CONFIG,
            ),
        )

        # Extrair imagem da resposta
        for part in response.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                ext = part.inline_data.mime_type.split("/")[-1]
                filename = f"gen_{session_id}_{i+1}.{ext}"
                filepath = session_dir / filename

                filepath.write_bytes(part.inline_data.data)
                size_kb = filepath.stat().st_size / 1024

                results.append({
                    "index": i + 1,
                    "filename": filename,
                    "path": str(filepath),
                    "size_kb": round(size_kb, 1),
                    "mime_type": part.inline_data.mime_type,
                })
                break  # só uma imagem por chamada

    return results
