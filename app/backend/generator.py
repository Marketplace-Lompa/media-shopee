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


def _detect_image_mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def generate_images(
    prompt: str,
    thinking_level: str,
    aspect_ratio: str,
    resolution: str,
    n_images: int,
    pool_images: Optional[List[bytes]] = None,       # compat legado (ignorado em runtime)
    uploaded_images: Optional[List[bytes]] = None,   # imagens enviadas pelo usuário
    grounded_images: Optional[List[bytes]] = None,   # refs visuais coletadas no grounding full
    session_id: Optional[str] = None,
    start_index: int = 1,
    structural_hint: Optional[str] = None,           # e.g. "poncho/ruana, cocoon silhouette, no sleeves"
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
        image_index = start_index + i
        # Montar content_parts:
        # 1. Imagens do usuário (autoridade da peça)
        # 2. Refs visuais de grounding (silhueta/caimento)
        # 3. Prompt textual (sempre por último — maior peso semântico)
        content_parts = []

        # Per-part media_resolution=HIGH faz o Nano Banana processar as referências
        # com mais tokens/detalhes, melhorando fidelidade de garment.
        # Nota: media_resolution no GenerateContentConfig causa 400 no Nano Banana —
        # DEVE ser per-part (no objeto Part) para funcionar com image gen models.
        _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH

        if uploaded_images:
            for img_bytes in uploaded_images:
                content_parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type=_detect_image_mime(img_bytes), data=img_bytes),
                        media_resolution=_hi_res,
                    )
                )

        if grounded_images:
            for img_bytes in grounded_images[:3]:
                content_parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type=_detect_image_mime(img_bytes), data=img_bytes),
                        media_resolution=_hi_res,
                    )
                )

        # M4: Object fidelity labeling para Nano Banana.
        # As fotos de referência são rotuladas como OBJECT REFERENCE (peça de roupa),
        # NÃO como character reference. Isso ativa object fidelity no Nano
        # e evita character consistency (copiar a pessoa).
        # O Nano gera a modelo por conta própria — não precisamos descrever físico.
        _effective_prompt = prompt
        if uploaded_images and not any(
            kw in prompt.lower() for kw in ("user text to incorporate", "refine this user prompt")
        ):
            # Referência visual continua sendo a autoridade principal.
            # structural_hint entra só como ancora curta para reduzir drift de subtype.
            _role_prefix = (
                "COPY this garment from the reference photos EXACTLY — "
                "same design, colors, texture, stitch pattern, and drape. "
            )
            if structural_hint:
                _role_prefix += f"Honor this garment identity: {structural_hint}. "
            _role_prefix += (
                "The references show the garment only, not a person to copy. "
                "Generate a new fashion model wearing this garment in a catalog-worthy editorial look: "
            )
            _effective_prompt = _role_prefix + prompt

        # Prompt textual (sempre por último para ter peso máximo)
        content_parts.append(types.Part(text=_effective_prompt))

        response = client.models.generate_content(
            model=MODEL_IMAGE,
            contents=[types.Content(role="user", parts=content_parts)],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            temperature=1.0,
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution,
            ),
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level) if thinking_level else None, # type: ignore
            safety_settings=SAFETY_CONFIG,
        ),
        )

        # Extrair imagem da resposta
        image_found = False
        parts = response.parts if response.parts else []
        for part in parts:
            if getattr(part, "inline_data", None) and getattr(part.inline_data, "mime_type", None) and part.inline_data.mime_type.startswith("image/"): # type: ignore
                ext = part.inline_data.mime_type.split("/")[-1] # type: ignore
                filename = f"gen_{session_id}_{image_index}.{ext}"
                filepath = session_dir / filename

                data = getattr(part.inline_data, "data", None)
                if data:
                    filepath.write_bytes(data)
                size_kb = filepath.stat().st_size / 1024

                mime_type_val = getattr(part.inline_data, "mime_type", "image/png")
                results.append({
                    "index": image_index,
                    "filename": filename,
                    "url": f"/outputs/{session_id}/{filename}",
                    "path": str(filepath),
                    "size_kb": round(size_kb, 1),
                    "mime_type": str(mime_type_val),
                })
                image_found = True
                break  # só uma imagem por chamada
        if not image_found:
            raise RuntimeError(f"Nano retornou sem imagem na posição {image_index}")

    return results


def edit_image(
    source_image_bytes: bytes,
    edit_prompt: str,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    session_id: Optional[str] = None,
    reference_images_bytes: Optional[List[bytes]] = None,
) -> List[dict]:
    """
    Edita uma imagem existente via Nano Banana 2.
    Envia [imagem original + referências opcionais + prompt de edição] e retorna a imagem editada.

    Returns lista com 1 dict:
    [{"filename": str, "url": str, "path": str, "size_kb": float, "mime_type": str}]
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    session_dir = OUTPUTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Montar content: imagem original + referências + prompt de edição
    # Per-part media_resolution=HIGH para fidelidade máxima na edição
    _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH
    content_parts = [
        types.Part(
            inline_data=types.Blob(mime_type=_detect_image_mime(source_image_bytes), data=source_image_bytes),
            media_resolution=_hi_res,
        ),
    ]
    # Adicionar imagens de referência (se houver)
    for ref_bytes in (reference_images_bytes or []):
        content_parts.append(
            types.Part(
                inline_data=types.Blob(mime_type=_detect_image_mime(ref_bytes), data=ref_bytes),
                media_resolution=_hi_res,
            )
        )
    content_parts.append(types.Part(text=edit_prompt))

    response = client.models.generate_content(
        model=MODEL_IMAGE,
        contents=[types.Content(role="user", parts=content_parts)],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution,
            ),
            safety_settings=SAFETY_CONFIG,
        ),
    )

    results = []
    parts = response.parts if response.parts else []
    for part in parts:
        if (
            getattr(part, "inline_data", None)
            and getattr(part.inline_data, "mime_type", None)
            and part.inline_data.mime_type.startswith("image/")
        ):
            ext = part.inline_data.mime_type.split("/")[-1]
            filename = f"edit_{session_id}_1.{ext}"
            filepath = session_dir / filename

            data = getattr(part.inline_data, "data", None)
            if data:
                filepath.write_bytes(data)
            size_kb = filepath.stat().st_size / 1024

            mime_type_val = getattr(part.inline_data, "mime_type", "image/png")
            results.append({
                "index": 1,
                "filename": filename,
                "url": f"/outputs/{session_id}/{filename}",
                "path": str(filepath),
                "size_kb": round(size_kb, 1),
                "mime_type": str(mime_type_val),
            })
            break

    if not results:
        raise RuntimeError("Nano retornou sem imagem na edição")

    return results
