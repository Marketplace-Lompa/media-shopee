"""
Image Generator — Nano Banana 2 (gemini-3.1-flash-image-preview).

- BLOCK_NONE em todas as categorias (moda/lingerie)
- Gera N imagens em sequência (sync) OU em paralelo (async)
- Aceita imagens do pool como contexto visual (LoRA-like)
- Salva outputs em app/outputs/{session_id}/

Async Performance:
  - generate_images_async: dispara N candidatos em paralelo via asyncio.gather
  - edit_image_async: chamada async sem bloquear event loop
  - Escrita em disco usa asyncio.to_thread para não bloquear I/O
"""
import asyncio
import time
import uuid
import random
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

client = genai.Client(
    api_key=GOOGLE_AI_API_KEY,
    http_options={'timeout': 120_000}  # SDK espera ms → 120s
)

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
_REFERENCE_LONG_EDGE = 1024
_REFERENCE_MAX_BYTES = 900_000
_REFERENCE_QUALITIES = (88, 82, 76, 70)

# Semáforo compartilhado com gemini_client para controlar tráfego total ao Google
try:
    from agent_runtime.gemini_client import GOOGLE_API_SEMAPHORE as _API_SEM
except ImportError:
    _API_SEM = asyncio.Semaphore(10)


def _reference_role_instruction(scope: str = "garment") -> str:
    scope_text = str(scope or "garment").strip().lower()
    if scope_text == "edit":
        return (
            "REFERENCE IMAGES BELOW — ITEM/GARMENT EXTRACTION ONLY. "
            "If a reference shows a flat lay or isolated item (no person): extract its color, texture, stitch, construction directly. "
            "If a reference shows a person wearing the item: that person is IRRELEVANT — "
            "do NOT use their face, skin tone, hair, body shape, age, or pose. Extract only the item properties. "
            "The person to preserve is exclusively the one in the BASE IMAGE labeled above."
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


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc or "").strip().lower()
    return "429" in text or "quota" in text or "rate" in text or "resource exhausted" in text


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


def _build_content_parts(
    *,
    prompt: str,
    uploaded_images: List[bytes],
    grounded_images: List[bytes],
    structural_hint: Optional[str] = None,
    scope: str = "garment",
) -> List[types.Part]:
    """Constrói content_parts para geração — compartilhado entre sync e async."""
    _effective_prompt = prompt
    if uploaded_images and not any(
        kw in prompt.lower() for kw in ("user text to incorporate", "refine this user prompt")
    ):
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

    content_parts = []
    _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH

    if uploaded_images:
        content_parts.append(types.Part(text=_reference_role_instruction(scope)))
        for img_bytes in uploaded_images:
            content_parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type=_detect_image_mime(img_bytes), data=img_bytes),
                    media_resolution=_hi_res,
                )
            )

    if grounded_images:
        content_parts.append(types.Part(text=_reference_role_instruction(scope)))
        for img_bytes in grounded_images:
            content_parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type=_detect_image_mime(img_bytes), data=img_bytes),
                    media_resolution=_hi_res,
                )
            )

    content_parts.append(types.Part(text=_effective_prompt))
    return content_parts


def _build_tools(use_image_grounding: bool) -> Optional[list]:
    if not use_image_grounding:
        return None
    return [
        types.Tool(google_search=types.GoogleSearch(
            search_types=types.SearchTypes(
                image_search=types.ImageSearch()
            )
        ))
    ]


def _log_grounding_metadata(response: Any, *, prefix: str = "IMAGE_GROUNDING") -> None:
    if not response or not response.candidates:
        return
    for cand in response.candidates:
        gm = getattr(cand, "grounding_metadata", None)
        if not gm:
            continue
        queries = (
            getattr(gm, "image_search_queries", None)
            or getattr(gm, "imageSearchQueries", None)
            or getattr(gm, "web_search_queries", None)
        )
        chunks = getattr(gm, "grounding_chunks", None) or []
        if queries:
            print(f"[{prefix}] 🔍 queries: {queries}")
        if chunks:
            uris = []
            for c in chunks[:3]:
                img_chunk = getattr(c, "image", None)
                web_chunk = getattr(c, "web", None)
                uri = (
                    getattr(img_chunk, "uri", None)
                    or getattr(web_chunk, "uri", None)
                    or ""
                )
                uris.append(str(uri))
            print(f"[{prefix}] 📎 sources ({len(chunks)}): " + ", ".join(uris))


def _extract_image_from_response(response: Any, *, session_id: str, image_index: int, session_dir: Path) -> dict:
    """Extrai uma imagem da resposta do Nano e salva em disco. Retorna metadado."""
    parts = response.parts if response.parts else []
    for part in parts:
        if (
            getattr(part, "inline_data", None)
            and getattr(part.inline_data, "mime_type", None)
            and part.inline_data.mime_type.startswith("image/")
        ):
            ext = part.inline_data.mime_type.split("/")[-1]
            filename = f"gen_{session_id}_{image_index}.{ext}"
            filepath = session_dir / filename

            data = getattr(part.inline_data, "data", None)
            if data:
                filepath.write_bytes(data)
            size_kb = filepath.stat().st_size / 1024

            mime_type_val = getattr(part.inline_data, "mime_type", "image/png")
            return {
                "index": image_index,
                "filename": filename,
                "url": f"/outputs/{session_id}/{filename}",
                "path": str(filepath),
                "size_kb": round(size_kb, 1),
                "mime_type": str(mime_type_val),
            }
    raise RuntimeError(f"Nano retornou sem imagem na posição {image_index}")


# ═══════════════════════════════════════════════════════════════════════════════
# ██ ASYNC API (nova — desbloqueante, paralela)
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_images_async(
    prompt: str,
    thinking_level: str,
    aspect_ratio: str,
    resolution: str,
    n_images: int,
    pool_images: Optional[List[bytes]] = None,
    uploaded_images: Optional[List[bytes]] = None,
    grounded_images: Optional[List[bytes]] = None,
    session_id: Optional[str] = None,
    start_index: int = 1,
    structural_hint: Optional[str] = None,
    use_image_grounding: bool = False,
) -> List[dict]:
    """
    Gera n_images imagens em PARALELO via asyncio.gather + client.aio.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    session_dir = OUTPUTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    effective_thinking_level = _normalize_thinking_level(thinking_level, default="minimal")
    prepared_uploaded_images = _prepare_reference_batch(uploaded_images, limit=_MAX_REFERENCE_IMAGES)
    prepared_grounded_images = _prepare_reference_batch(grounded_images, limit=_MAX_GROUNDED_IMAGES)
    _tools = _build_tools(use_image_grounding)

    async def _generate_single(image_index: int) -> dict:
        """Gera 1 imagem com retry."""
        last_error: Optional[Exception] = None
        for attempt in range(1, _REFERENCE_RETRY_ATTEMPTS + 1):
            current_uploaded = _build_retry_reference_subset(prepared_uploaded_images, attempt, minimum_keep=2)
            current_grounded = _build_retry_reference_subset(prepared_grounded_images, attempt, minimum_keep=1)

            content_parts = _build_content_parts(
                prompt=prompt,
                uploaded_images=current_uploaded,
                grounded_images=current_grounded,
                structural_hint=structural_hint,
                scope="garment",
            )

            try:
                async with _API_SEM:
                    response = await client.aio.models.generate_content(
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
                            tools=_tools,
                        ),
                    )

                if use_image_grounding:
                    _log_grounding_metadata(response)

                # Escrita em disco via thread para não bloquear o event loop
                result = await asyncio.to_thread(
                    _extract_image_from_response,
                    response, session_id=session_id, image_index=image_index, session_dir=session_dir,
                )
                return result

            except Exception as exc:
                last_error = exc
                is_quota = _is_rate_limit_error(exc)
                is_transient = _is_transient_provider_error(exc)

                if attempt >= _REFERENCE_RETRY_ATTEMPTS or (not is_transient and not is_quota):
                    raise

                if is_quota:
                    sleep_time = (2.0 ** attempt) + random.uniform(0.5, 2.0)
                    print(f"[GENERATOR_ASYNC] ⚠️ Quota 429 (attempt={attempt}). Aguardando {sleep_time:.1f}s...")
                else:
                    sleep_time = (1.2 * attempt) + random.uniform(0.1, 0.5)
                    print(f"[GENERATOR_ASYNC] transient failure; retrying "
                          f"(attempt={attempt + 1}/{_REFERENCE_RETRY_ATTEMPTS}, refs={len(current_uploaded)})")

                await asyncio.sleep(sleep_time)

        if last_error:
            raise last_error
        raise RuntimeError(f"Nano retornou sem resposta na posição {image_index}")

    # 🚀 Dispara todos os N candidatos em paralelo
    tasks = [_generate_single(start_index + i) for i in range(n_images)]
    results = await asyncio.gather(*tasks)
    return list(results)


async def edit_image_async(
    source_image_bytes: bytes,
    edit_prompt: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    resolution: str = DEFAULT_RESOLUTION,
    thinking_level: str = "HIGH",
    session_id: Optional[str] = None,
    reference_images_bytes: Optional[List[bytes]] = None,
    use_image_grounding: bool = False,
) -> List[dict]:
    """
    Edita uma imagem existente via Nano Banana 2 — versão async.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    session_dir = OUTPUTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    effective_thinking_level = _normalize_thinking_level(thinking_level, default="high")
    prepared_reference_images = _prepare_reference_batch(reference_images_bytes, limit=_MAX_REFERENCE_IMAGES)
    _tools = _build_tools(use_image_grounding)

    last_error: Optional[Exception] = None
    for attempt in range(1, _REFERENCE_RETRY_ATTEMPTS + 1):
        current_references = _build_retry_reference_subset(prepared_reference_images, attempt, minimum_keep=2)
        _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH

        content_parts = [
            types.Part(text=(
                "BASE IMAGE TO EDIT: The image immediately below is the source to edit. "
                "LOCK the person in this image — their face, skin tone, hair, body proportions, "
                "and pose must remain exactly as shown. Do not alter the person in any way."
            )),
            types.Part(
                inline_data=types.Blob(mime_type=_detect_image_mime(source_image_bytes), data=source_image_bytes),
                media_resolution=_hi_res,
            ),
        ]
        if current_references:
            content_parts.append(types.Part(text=_reference_role_instruction("edit")))
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
            async with _API_SEM:
                response = await client.aio.models.generate_content(
                    model=MODEL_IMAGE,
                    contents=[types.Content(role="user", parts=content_parts)],
                    config=types.GenerateContentConfig(
                        response_modalities=_edit_modalities,
                        image_config=types.ImageConfig(
                            aspect_ratio=aspect_ratio,
                            image_size=resolution,
                        ),
                        thinking_config=types.ThinkingConfig(thinking_level=effective_thinking_level),  # type: ignore[arg-type]
                        safety_settings=SAFETY_CONFIG,
                        tools=_tools,
                    ),
                )

            if use_image_grounding:
                _log_grounding_metadata(response, prefix="IMAGE_GROUNDING/EDIT")

            # Extrair imagem — escrita em disco via thread
            result = await asyncio.to_thread(
                _extract_image_from_response,
                response, session_id=session_id, image_index=1, session_dir=session_dir,
            )
            return [result]

        except Exception as exc:
            last_error = exc
            is_quota = _is_rate_limit_error(exc)
            is_transient = _is_transient_provider_error(exc)

            if attempt >= _REFERENCE_RETRY_ATTEMPTS or (not is_transient and not is_quota):
                raise

            if is_quota:
                sleep_time = (2.0 ** attempt) + random.uniform(0.5, 2.0)
                print(f"[GENERATOR_ASYNC/EDIT] ⚠️ Quota 429 (attempt={attempt}). Aguardando {sleep_time:.1f}s...")
            else:
                sleep_time = (1.2 * attempt) + random.uniform(0.1, 0.5)
                print(f"[GENERATOR_ASYNC/EDIT] transient edit failure; retrying "
                      f"(attempt={attempt + 1}/{_REFERENCE_RETRY_ATTEMPTS}, refs={len(current_references)})")

            await asyncio.sleep(sleep_time)

    if last_error:
        raise last_error
    raise RuntimeError("Nano retornou sem resposta na edição (async)")


# ═══════════════════════════════════════════════════════════════════════════════
# ██ SYNC LEGACY (mantido para compatibilidade com pipeline_v2.py)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_images(
    prompt: str,
    thinking_level: str,
    aspect_ratio: str,
    resolution: str,
    n_images: int,
    pool_images: Optional[List[bytes]] = None,
    uploaded_images: Optional[List[bytes]] = None,
    grounded_images: Optional[List[bytes]] = None,
    session_id: Optional[str] = None,
    start_index: int = 1,
    structural_hint: Optional[str] = None,
    use_image_grounding: bool = False,
) -> List[dict]:
    """
    Gera n_images imagens com o Nano Banana 2 (sync — um por vez).
    Mantido para backward-compatibility com pipeline_v2.py.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    session_dir = OUTPUTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    results = []
    effective_thinking_level = _normalize_thinking_level(thinking_level, default="minimal")
    prepared_uploaded_images = _prepare_reference_batch(uploaded_images, limit=_MAX_REFERENCE_IMAGES)
    prepared_grounded_images = _prepare_reference_batch(grounded_images, limit=_MAX_GROUNDED_IMAGES)
    _tools = _build_tools(use_image_grounding)

    for i in range(n_images):
        image_index = start_index + i

        response = None
        last_error: Optional[Exception] = None
        for attempt in range(1, _REFERENCE_RETRY_ATTEMPTS + 1):
            current_uploaded = _build_retry_reference_subset(prepared_uploaded_images, attempt, minimum_keep=2)
            current_grounded = _build_retry_reference_subset(prepared_grounded_images, attempt, minimum_keep=1)

            content_parts = _build_content_parts(
                prompt=prompt,
                uploaded_images=current_uploaded,
                grounded_images=current_grounded,
                structural_hint=structural_hint,
                scope="garment",
            )

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
                        tools=_tools,
                    ),
                )
                if use_image_grounding:
                    _log_grounding_metadata(response)
                break
            except Exception as exc:
                last_error = exc
                is_quota = _is_rate_limit_error(exc)
                is_transient = _is_transient_provider_error(exc)

                if attempt >= _REFERENCE_RETRY_ATTEMPTS or (not is_transient and not is_quota):
                    raise

                if is_quota:
                    sleep_time = (2.0 ** attempt) + random.uniform(0.5, 2.0)
                    print(f"[GENERATOR] ⚠️ Quota 429 (attempt={attempt}). Aguardando {sleep_time:.1f}s...")
                else:
                    sleep_time = (1.2 * attempt) + random.uniform(0.1, 0.5)
                    print(f"[GENERATOR] transient failure; retrying "
                          f"(attempt={attempt + 1}/{_REFERENCE_RETRY_ATTEMPTS}, refs={len(current_uploaded)})")

                time.sleep(sleep_time)

        if response is None:
            if last_error:
                raise last_error
            raise RuntimeError(f"Nano retornou sem resposta na posição {image_index}")

        result = _extract_image_from_response(
            response, session_id=session_id, image_index=image_index, session_dir=session_dir,
        )
        results.append(result)

    return results


def edit_image(
    source_image_bytes: bytes,
    edit_prompt: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    resolution: str = DEFAULT_RESOLUTION,
    thinking_level: str = "HIGH",
    session_id: Optional[str] = None,
    reference_images_bytes: Optional[List[bytes]] = None,
    use_image_grounding: bool = False,
) -> List[dict]:
    """
    Edita uma imagem existente via Nano Banana 2 (sync).
    Mantido para backward-compatibility com pipeline_v2.py.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    session_dir = OUTPUTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    effective_thinking_level = _normalize_thinking_level(thinking_level, default="high")
    prepared_reference_images = _prepare_reference_batch(reference_images_bytes, limit=_MAX_REFERENCE_IMAGES)
    _tools = _build_tools(use_image_grounding)

    response = None
    last_error: Optional[Exception] = None
    for attempt in range(1, _REFERENCE_RETRY_ATTEMPTS + 1):
        current_references = _build_retry_reference_subset(prepared_reference_images, attempt, minimum_keep=2)
        _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH

        content_parts = [
            types.Part(text=(
                "BASE IMAGE TO EDIT: The image immediately below is the source to edit. "
                "LOCK the person in this image — their face, skin tone, hair, body proportions, "
                "and pose must remain exactly as shown. Do not alter the person in any way."
            )),
            types.Part(
                inline_data=types.Blob(mime_type=_detect_image_mime(source_image_bytes), data=source_image_bytes),
                media_resolution=_hi_res,
            ),
        ]
        if current_references:
            content_parts.append(
                types.Part(text=_reference_role_instruction("edit"))
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
                    thinking_config=types.ThinkingConfig(thinking_level=effective_thinking_level),  # type: ignore[arg-type]
                    safety_settings=SAFETY_CONFIG,
                    tools=_tools,
                ),
            )
            if use_image_grounding:
                _log_grounding_metadata(response, prefix="IMAGE_GROUNDING/EDIT")
            break
        except Exception as exc:
            last_error = exc
            is_quota = _is_rate_limit_error(exc)
            is_transient = _is_transient_provider_error(exc)

            if attempt >= _REFERENCE_RETRY_ATTEMPTS or (not is_transient and not is_quota):
                raise

            if is_quota:
                sleep_time = (2.0 ** attempt) + random.uniform(0.5, 2.0)
                print(f"[GENERATOR/EDIT] ⚠️ Quota 429 (attempt={attempt}). Aguardando {sleep_time:.1f}s...")
            else:
                sleep_time = (1.2 * attempt) + random.uniform(0.1, 0.5)
                print(f"[GENERATOR] transient edit failure; retrying "
                      f"(attempt={attempt + 1}/{_REFERENCE_RETRY_ATTEMPTS}, refs={len(current_references)})")

            time.sleep(1.2 * attempt)

    if response is None:
        if last_error:
            raise last_error
        raise RuntimeError("Nano retornou sem resposta na edição")

    result = _extract_image_from_response(
        response, session_id=session_id, image_index=1, session_dir=session_dir,
    )
    return [result]
