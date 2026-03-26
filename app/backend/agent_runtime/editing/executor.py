from __future__ import annotations

import random
import time
import uuid
from typing import Optional

from google.genai import types

from config import EDIT_IMAGE_ONLY_MODALITY, MODEL_IMAGE, SAFETY_CONFIG
from generator import (
    OUTPUTS_DIR,
    _MAX_REFERENCE_IMAGES,
    _REFERENCE_RETRY_ATTEMPTS,
    _build_retry_reference_subset,
    _build_tools,
    _detect_image_mime,
    _extract_image_from_response,
    _is_rate_limit_error,
    _is_transient_provider_error,
    _log_grounding_metadata,
    _normalize_thinking_level,
    _prepare_reference_batch,
    _reference_role_instruction,
    client,
)

from agent_runtime.editing.contracts import ImageEditExecutionRequest

_SOURCE_PROMPT_CONTEXT_MAX_CHARS = 700


def _trim_source_prompt_context(source_prompt: Optional[str]) -> str:
    text = str(source_prompt or "").strip()
    if not text:
        return ""
    if len(text) <= _SOURCE_PROMPT_CONTEXT_MAX_CHARS:
        return text
    return text[:_SOURCE_PROMPT_CONTEXT_MAX_CHARS].rstrip() + "..."


def _build_base_image_instruction(lock_person: bool) -> str:
    if lock_person:
        return (
            "BASE IMAGE TO EDIT: The image immediately below is the source to edit. "
            "LOCK the person in this image — their face, skin tone, hair, body proportions, "
            "and pose must remain exactly as shown. Do not alter the person in any way."
        )
    return (
        "BASE IMAGE TO EDIT: The image immediately below is the source to edit. "
        "LOCK ONLY THE GARMENT in this image — preserve its exact shape, color, texture, "
        "construction, length, and silhouette. The person wearing the garment is a PLACEHOLDER "
        "and MUST be fully replaced with a completely different model. Do not preserve any "
        "facial features, skin tone, hair, body type, or pose from this base image person."
    )


def _build_guided_angle_base_instruction() -> str:
    return (
        "BASE IMAGE TO EDIT: The image immediately below is the source of truth for the same person, same outfit, "
        "same colors, same proportions, and same styling. Preserve person identity and garment fidelity, "
        "but create a new camera viewpoint of this same subject."
    )


def _build_content_parts(
    *,
    request: ImageEditExecutionRequest,
    current_references: list[bytes],
) -> list[types.Part]:
    hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH
    is_guided_angle = request.prepared_prompt.flow_mode == "guided_angle"
    base_instruction = (
        _build_guided_angle_base_instruction()
        if is_guided_angle
        else _build_base_image_instruction(request.lock_person)
    )
    source_image_part = types.Part(
        inline_data=types.Blob(
            mime_type=_detect_image_mime(request.source_image_bytes),
            data=request.source_image_bytes,
        ),
        media_resolution=hi_res,
    )
    parts = (
        [source_image_part, types.Part(text=base_instruction)]
        if is_guided_angle
        else [types.Part(text=base_instruction), source_image_part]
    )

    if current_references:
        parts.append(types.Part(text=_reference_role_instruction("edit")))
        for ref_bytes in current_references:
            parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type=_detect_image_mime(ref_bytes),
                        data=ref_bytes,
                    ),
                    media_resolution=hi_res,
                )
            )

    if request.prepared_prompt.include_source_prompt_context:
        source_prompt_context = _trim_source_prompt_context(request.source_prompt_context)
        if source_prompt_context:
            parts.append(
                types.Part(
                    text=(
                        "ORIGINAL GENERATION PROMPT CONTEXT — semantic guidance only. "
                        "Use it to preserve the original scene logic and aesthetic intent when useful, "
                        "but do not treat it as a script to copy verbatim.\n"
                        f"{source_prompt_context}"
                    )
                )
            )

    if (
        request.prepared_prompt.include_reference_item_description
        and request.prepared_prompt.reference_item_description
    ):
        parts.append(
            types.Part(
                text=(
                    "REFERENCE ITEM DESCRIPTION — use only as item evidence, never as person identity:\n"
                    f"{request.prepared_prompt.reference_item_description}"
                )
            )
        )

    if request.prepared_prompt.use_structured_shell:
        parts.append(
            types.Part(
                text=(
                    "EDIT GOAL — APPLY ONLY THIS CHANGE:\n"
                    f"{request.prepared_prompt.structured_edit_goal}"
                )
            )
        )
        parts.append(
            types.Part(
                text=(
                    "PRESERVATION RULES — DO NOT CHANGE THESE ELEMENTS:\n"
                    f"{request.prepared_prompt.structured_preserve_clause}"
                )
            )
        )
    else:
        parts.append(types.Part(text=request.prepared_prompt.model_prompt))

    return parts


def execute_image_edit_request(request: ImageEditExecutionRequest) -> list[dict]:
    session_id = request.session_id or str(uuid.uuid4())[:8]
    session_dir = OUTPUTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    effective_thinking_level = _normalize_thinking_level(request.thinking_level, default="high")
    prepared_reference_images = _prepare_reference_batch(
        request.reference_images_bytes,
        limit=_MAX_REFERENCE_IMAGES,
    )
    tools = _build_tools(request.use_image_grounding)

    response = None
    last_error: Optional[Exception] = None
    for attempt in range(1, _REFERENCE_RETRY_ATTEMPTS + 1):
        current_references = _build_retry_reference_subset(
            prepared_reference_images,
            attempt,
            minimum_keep=2,
        )
        content_parts = _build_content_parts(
            request=request,
            current_references=current_references,
        )
        try:
            edit_modalities = ["IMAGE"] if EDIT_IMAGE_ONLY_MODALITY else ["TEXT", "IMAGE"]
            response = client.models.generate_content(
                model=MODEL_IMAGE,
                contents=[types.Content(role="user", parts=content_parts)],
                config=types.GenerateContentConfig(
                    response_modalities=edit_modalities,
                    image_config=types.ImageConfig(
                        aspect_ratio=request.aspect_ratio,
                        image_size=request.resolution,
                    ),
                    thinking_config=types.ThinkingConfig(
                        thinking_level=effective_thinking_level
                    ),
                    safety_settings=SAFETY_CONFIG,
                    tools=tools,
                ),
            )
            if request.use_image_grounding:
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
                print(f"[EDIT_EXECUTOR] ⚠️ Quota 429 (attempt={attempt}). Aguardando {sleep_time:.1f}s...")
            else:
                sleep_time = (1.2 * attempt) + random.uniform(0.1, 0.5)
                print(
                    "[EDIT_EXECUTOR] transient edit failure; retrying "
                    f"(attempt={attempt + 1}/{_REFERENCE_RETRY_ATTEMPTS}, refs={len(current_references)})"
                )
            time.sleep(sleep_time)

    if response is None:
        if last_error:
            raise last_error
        raise RuntimeError("Nano retornou sem resposta na edição")

    result = _extract_image_from_response(
        response,
        session_id=session_id,
        image_index=1,
        session_dir=session_dir,
    )
    return [result]
