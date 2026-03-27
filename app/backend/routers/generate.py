"""
Router: POST /generate
Pipeline com suporte a jobs assíncronos (submit + polling).
"""
from __future__ import annotations

import asyncio
from typing import Callable, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agent_runtime.generation_flow import (
    build_generation_response,
    normalize_generation_options,
    persist_generation_history,
    run_generation_flow as run_pipeline_v2,
)
from create_categories import normalize_create_category
from config import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_N_IMAGES,
    DEFAULT_RESOLUTION,
    VALID_N_IMAGES,
)
from job_manager import complete_job, create_job, fail_job, get_job, list_jobs, start_job, update_stage
from models import GenerateResponse
from request_validation import validate_generation_params

router = APIRouter(prefix="/generate", tags=["generate"])


_LEGACY_PRESET_TO_MODE = {
    "catalog_clean": "catalog_clean",
    "marketplace_lifestyle": "natural",
    "premium_lifestyle": "editorial_commercial",
    "ugc_real_br": "lifestyle",
}


def _resolve_requested_mode(mode: Optional[str], preset: Optional[str]) -> Optional[str]:
    normalized_mode = str(mode or "").strip()
    if normalized_mode:
        return normalized_mode
    normalized_preset = str(preset or "").strip().lower()
    if not normalized_preset:
        return None
    return _LEGACY_PRESET_TO_MODE.get(normalized_preset, normalized_preset)


@router.post("", response_model=GenerateResponse)
async def generate(
    category: Optional[str] = Form(default=None),
    prompt: Optional[str] = Form(default=None),
    mode: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
    resolution: str = Form(default=DEFAULT_RESOLUTION),
    n_images: int = Form(default=DEFAULT_N_IMAGES),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    guided_brief: Optional[str] = Form(default=None),
    preset: Optional[str] = Form(default=None),
    scene_preference: str = Form(default="auto_br"),
    fidelity_mode: str = Form(default="balanceada"),

    images: List[UploadFile] = File(default=[]),
):
    try:
        normalized_category = normalize_create_category(category)
        validate_generation_params(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=n_images,
            valid_n_images=VALID_N_IMAGES,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    limited_images = images[:14]
    uploaded_bytes = [await img.read() for img in limited_images]
    uploaded_filenames = [str(img.filename or "").strip() for img in limited_images]
    requested_mode = _resolve_requested_mode(mode, preset)
    normalized_mode, normalized_scene_preference, normalized_fidelity_mode = normalize_generation_options(
        mode=requested_mode,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
    )
    try:
        return await asyncio.to_thread(
            _run_v2_pipeline_and_persist,
            category=normalized_category,
            uploaded_bytes=uploaded_bytes,
            uploaded_filenames=uploaded_filenames,
            prompt=prompt,
            mode=normalized_mode,
            scene_preference=normalized_scene_preference,
            fidelity_mode=normalized_fidelity_mode,

            n_images=n_images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            on_stage=None,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e


def _run_v2_pipeline_and_persist(
    *,
    category: str,
    uploaded_bytes: List[bytes],
    uploaded_filenames: Optional[List[str]],
    prompt: Optional[str],
    mode: str,
    scene_preference: str,
    fidelity_mode: str,

    n_images: int,
    aspect_ratio: str,
    resolution: str,
    on_stage: Optional[Callable[[str, dict], None]] = None,
) -> GenerateResponse:
    """Wrapper que roda pipeline_v2, persiste historico, e retorna GenerateResponse."""
    raw = run_pipeline_v2(
        uploaded_bytes=uploaded_bytes,
        uploaded_filenames=uploaded_filenames,
        prompt=prompt,
        mode=mode,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,

        n_images=n_images,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        on_stage=on_stage,
    )
    persist_generation_history(
        raw,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        mode=mode,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,

    )
    return build_generation_response(
        raw,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        preset=mode,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,

    ).model_copy(update={"category": category})


@router.post("/async")
async def generate_async(
    category: Optional[str] = Form(default=None),
    prompt: Optional[str] = Form(default=None),
    mode: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
    resolution: str = Form(default=DEFAULT_RESOLUTION),
    n_images: int = Form(default=DEFAULT_N_IMAGES),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    guided_brief: Optional[str] = Form(default=None),
    preset: Optional[str] = Form(default=None),
    scene_preference: str = Form(default="auto_br"),
    fidelity_mode: str = Form(default="balanceada"),

    images: List[UploadFile] = File(default=[]),
):
    try:
        normalized_category = normalize_create_category(category)
        validate_generation_params(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=n_images,
            valid_n_images=VALID_N_IMAGES,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    limited_images = images[:14]
    uploaded_bytes = [await img.read() for img in limited_images]
    uploaded_filenames = [str(img.filename or "").strip() for img in limited_images]
    requested_mode = _resolve_requested_mode(mode, preset)
    normalized_mode, normalized_scene_preference, normalized_fidelity_mode = normalize_generation_options(
        mode=requested_mode,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
    )
    _prompt_short = (prompt or "")[:120].strip() or None
    job_id = create_job(
        meta={
            # ── Identificação do pipeline ──
            "pipeline_version": "v2",
            "category": normalized_category,
            # ── Parâmetros de geração ──
            "prompt": _prompt_short,
            "prompt_full": (prompt or "").strip() or None,
            "n_images": n_images,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "mode": normalized_mode,
            "preset": preset,
            "scene_preference": scene_preference,
            "fidelity_mode": fidelity_mode,

            # ── Grounding ──
            "grounding_strategy": grounding_strategy,
            "use_grounding": use_grounding,
            # ── Referências visuais ──
            "has_images": bool(uploaded_bytes),
            "image_count": len(uploaded_bytes),
            "image_filenames": uploaded_filenames[:10] if uploaded_filenames else [],
            # ── Guided brief ──
            "has_guided_brief": bool(guided_brief),
        }
    )

    def _worker() -> None:
        def _stage_cb(stage: str, data: dict) -> None:
            update_stage(job_id, stage, data)

        try:
            response = _run_v2_pipeline_and_persist(
                category=normalized_category,
                uploaded_bytes=uploaded_bytes,
                uploaded_filenames=uploaded_filenames,
                prompt=prompt,
                mode=normalized_mode,
                scene_preference=normalized_scene_preference,
                fidelity_mode=normalized_fidelity_mode,

                n_images=n_images,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                on_stage=_stage_cb,
            )
            stage = "done_partial" if response.failed_indices else "done"
            complete_job(job_id, response.model_dump(), stage=stage)
        except Exception as e:
            fail_job(job_id, str(e))

    start_job(job_id, _worker)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
async def get_generate_job(job_id: str):
    return get_job(job_id)


@router.get("/jobs")
async def list_generate_jobs(limit: int = 20):
    return list_jobs(limit=limit)
