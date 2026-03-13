"""
Image Generator — Nano Banana 2 (gemini-3.1-flash-image-preview).

- BLOCK_NONE em todas as categorias (moda/lingerie)
- Gera N imagens em sequência (API não suporta batch paralelo nativo)
- Aceita imagens do pool como contexto visual (LoRA-like)
- Salva outputs em app/outputs/{session_id}/
"""
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types
from PIL import Image, ImageOps

from config import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_RESOLUTION,
    GOOGLE_AI_API_KEY,
    MODEL_IMAGE,
    SAFETY_CONFIG,
    ROOT_DIR,
    EDIT_IMAGE_ONLY_MODALITY,
)
from image_utils import detect_image_mime as _detect_image_mime

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

OUTPUTS_DIR = ROOT_DIR / "app" / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

_TRANSIENT_PROVIDER_ERRORS = (
    "server disconnected without sending a response",
    "remoteprotocolerror",
    "connection reset",
    "temporarily unavailable",
    "timed out",
    "timeout",
    "503",
    "502",
    "500",
)
_REFERENCE_RETRY_ATTEMPTS = 3
_MAX_REFERENCE_IMAGES = 4
_MAX_GROUNDED_IMAGES = 3
_REFERENCE_LONG_EDGE = 2048
_REFERENCE_MAX_BYTES = 1_900_000
_REFERENCE_QUALITIES = (90, 86, 82, 78)


def _reference_role_instruction(scope: str = "garment") -> str:
    scope_text = str(scope or "garment").strip().lower()
    if scope_text == "edit":
        return (
            "REFERENCE ROLE MAP: GARMENT ONLY. "
            "Allowed transfer: garment geometry, fabric behavior, stitch/texture, and palette. "
            "Forbidden transfer: face, body, skin tone, hair, age impression, pose, and background layout."
        )
    return (
        "REFERENCE ROLE MAP: GARMENT ONLY. "
        "Use references as material and construction evidence. "
        "Do not reuse human identity from references; create a different person following the prompt rules."
    )




def _normalize_thinking_level(level: Optional[str], *, default: str) -> str:
    token = str(level or "").strip().lower()
    if token in {"minimal", "high"}:
        return token
    if token in {"low", "min"}:
        return "minimal"
    if token in {"strong", "max"}:
        return "high"
    return default


def _is_transient_provider_error(exc: Exception) -> bool:
    text = str(exc or "").strip().lower()
    return any(token in text for token in _TRANSIENT_PROVIDER_ERRORS)


def _prepare_reference_image(image_bytes: bytes) -> bytes:
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in {"RGB", "L"}:
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if "A" in img.getbands():
                    bg.paste(img, mask=img.getchannel("A"))
                else:
                    bg.paste(img.convert("RGB"))
                img = bg
            else:
                img = img.convert("RGB")

            w, h = img.size
            long_edge = max(w, h)
            if long_edge > _REFERENCE_LONG_EDGE:
                scale = _REFERENCE_LONG_EDGE / float(long_edge)
                resized = (
                    max(1, int(round(w * scale))),
                    max(1, int(round(h * scale))),
                )
                img = img.resize(resized, Image.Resampling.LANCZOS)

            for quality in _REFERENCE_QUALITIES:
                out = BytesIO()
                img.save(
                    out,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                    progressive=True,
                )
                data = out.getvalue()
                if len(data) <= _REFERENCE_MAX_BYTES or quality == _REFERENCE_QUALITIES[-1]:
                    return data
    except Exception:
        return image_bytes
    return image_bytes


def _prepare_reference_batch(
    images: Optional[List[bytes]],
    *,
    limit: int,
) -> List[bytes]:
    prepared: List[bytes] = []
    if not images:
        return prepared
    for raw in images:
        if raw is None:
            continue
        prepared.append(_prepare_reference_image(bytes(raw)))
        if len(prepared) >= limit:
            break
    return prepared


def _build_retry_reference_subset(images: List[bytes], attempt: int, *, minimum_keep: int) -> List[bytes]:
    if attempt <= 1 or len(images) <= minimum_keep:
        return images
    keep = max(minimum_keep, len(images) - (attempt - 1))
    return images[:keep]


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
    effective_thinking_level = _normalize_thinking_level(thinking_level, default="minimal")
    prepared_uploaded_images = _prepare_reference_batch(uploaded_images, limit=_MAX_REFERENCE_IMAGES)
    prepared_grounded_images = _prepare_reference_batch(grounded_images, limit=_MAX_GROUNDED_IMAGES)

    for i in range(n_images):
        image_index = start_index + i
        # M4: Object fidelity labeling para Nano Banana.
        # As fotos de referência são rotuladas como OBJECT REFERENCE (peça de roupa),
        # NÃO como character reference. Isso ativa object fidelity no Nano
        # e evita character consistency (copiar a pessoa).
        # O Nano gera a modelo por conta própria — não precisamos descrever físico.
        _effective_prompt = prompt
        if prepared_uploaded_images and not any(
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
                "Never replicate any face, skin tone, body type, or hairstyle from reference people. "
                "Treat all visible people in references as anonymous mannequins for garment transfer only. "
                "Generate a new and unique Brazilian fashion model identity wearing this garment in a catalog-worthy editorial look: "
            )
            _effective_prompt = _role_prefix + prompt

        response = None
        last_error: Optional[Exception] = None
        for attempt in range(1, _REFERENCE_RETRY_ATTEMPTS + 1):
            current_uploaded = _build_retry_reference_subset(prepared_uploaded_images, attempt, minimum_keep=2)
            current_grounded = _build_retry_reference_subset(prepared_grounded_images, attempt, minimum_keep=1)

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

            if current_uploaded:
                content_parts.append(types.Part(text=_reference_role_instruction("garment")))
                for img_bytes in current_uploaded:
                    content_parts.append(
                        types.Part(
                            inline_data=types.Blob(mime_type=_detect_image_mime(img_bytes), data=img_bytes),
                            media_resolution=_hi_res,
                        )
                    )

            if current_grounded:
                content_parts.append(types.Part(text=_reference_role_instruction("garment")))
                for img_bytes in current_grounded:
                    content_parts.append(
                        types.Part(
                            inline_data=types.Blob(mime_type=_detect_image_mime(img_bytes), data=img_bytes),
                            media_resolution=_hi_res,
                        )
                    )

            # Prompt textual (sempre por último para ter peso máximo)
            content_parts.append(types.Part(text=_effective_prompt))

            try:
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
                        thinking_config=types.ThinkingConfig(thinking_level=effective_thinking_level),  # type: ignore[arg-type]
                        safety_settings=SAFETY_CONFIG,
                    ),
                )
                break
            except Exception as exc:
                last_error = exc
                if attempt >= _REFERENCE_RETRY_ATTEMPTS or not _is_transient_provider_error(exc):
                    raise
                print(
                    "[GENERATOR] transient image-generation failure; retrying "
                    f"(attempt={attempt + 1}/{_REFERENCE_RETRY_ATTEMPTS}, refs={len(current_uploaded)})"
                )
                time.sleep(1.2 * attempt)

        if response is None:
            if last_error:
                raise last_error
            raise RuntimeError(f"Nano retornou sem resposta na posição {image_index}")

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
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    resolution: str = DEFAULT_RESOLUTION,
    thinking_level: str = "HIGH",
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
    effective_thinking_level = _normalize_thinking_level(thinking_level, default="high")
    prepared_reference_images = _prepare_reference_batch(reference_images_bytes, limit=_MAX_REFERENCE_IMAGES)

    response = None
    last_error: Optional[Exception] = None
    for attempt in range(1, _REFERENCE_RETRY_ATTEMPTS + 1):
        current_references = _build_retry_reference_subset(prepared_reference_images, attempt, minimum_keep=2)
        _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH
        content_parts = [
            types.Part(
                inline_data=types.Blob(mime_type=_detect_image_mime(source_image_bytes), data=source_image_bytes),
                media_resolution=_hi_res,
            ),
        ]
        # Adicionar imagens de referência COM object fidelity labeling.
        # M4: As referências são para GARMENT ONLY — o Nano Banana NÃO deve
        # copiar a pessoa que aparece nas fotos, apenas a textura e construção da peça.
        if current_references:
            content_parts.append(
                types.Part(
                    text=(
                        _reference_role_instruction("edit")
                    )
                )
            )
            for ref_bytes in current_references:
                content_parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type=_detect_image_mime(ref_bytes), data=ref_bytes),
                        media_resolution=_hi_res,
                    )
                )
        content_parts.append(types.Part(text=edit_prompt))

        try:
            _edit_modalities = ["IMAGE"] if EDIT_IMAGE_ONLY_MODALITY else ["TEXT", "IMAGE"]
            response = client.models.generate_content(
                model=MODEL_IMAGE,
                contents=[types.Content(role="user", parts=content_parts)],
                config=types.GenerateContentConfig(
                    response_modalities=_edit_modalities,
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size=resolution,
                    ),
                    thinking_config=types.ThinkingConfig(thinking_level=effective_thinking_level), # type: ignore[arg-type]
                    safety_settings=SAFETY_CONFIG,
                ),
            )
            break
        except Exception as exc:
            last_error = exc
            if attempt >= _REFERENCE_RETRY_ATTEMPTS or not _is_transient_provider_error(exc):
                raise
            print(
                "[GENERATOR] transient edit failure; retrying "
                f"(attempt={attempt + 1}/{_REFERENCE_RETRY_ATTEMPTS}, refs={len(current_references)})"
            )
            time.sleep(1.2 * attempt)

    if response is None:
        if last_error:
            raise last_error
        raise RuntimeError("Nano retornou sem resposta na edição")

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
