"""
Router Marketplace:
- POST /marketplace/async
- GET  /marketplace/jobs/{job_id}
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agent_runtime.marketplace_orchestrator import run_marketplace_orchestration
from config import DEFAULT_ASPECT_RATIO, DEFAULT_RESOLUTION, REFERENCE_GENERATION_MAX
from job_manager import complete_job, create_job, fail_job, get_job, start_job, update_stage
from request_validation import (
    normalize_marketplace_channel,
    normalize_marketplace_operation,
    validate_generation_params,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.post("/async")
async def marketplace_async(
    marketplace_channel: str = Form(...),
    operation: str = Form(...),
    prompt: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
    resolution: str = Form(default=DEFAULT_RESOLUTION),
    preset: Optional[str] = Form(default="catalog_clean"),
    scene_preference: str = Form(default="indoor_br"),
    fidelity_mode: str = Form(default="balanceada"),
    pose_flex_mode: str = Form(default="controlled"),
    base_images: List[UploadFile] = File(default=[]),
    color_images: List[UploadFile] = File(default=[]),
):
    try:
        normalized_channel = normalize_marketplace_channel(marketplace_channel)
        normalized_operation = normalize_marketplace_operation(operation)
        # Cada slot roda com n_images=1 internamente; validamos parâmetros de saída aqui.
        validate_generation_params(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=1,
            valid_n_images=[1],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    limited_base = base_images[:REFERENCE_GENERATION_MAX]
    limited_color = color_images[:REFERENCE_GENERATION_MAX]
    base_images_bytes = [await item.read() for item in limited_base]
    base_filenames = [str(item.filename or "").strip() for item in limited_base]
    color_images_bytes = [await item.read() for item in limited_color]
    color_filenames = [str(item.filename or "").strip() for item in limited_color]

    if not base_images_bytes:
        raise HTTPException(status_code=400, detail="base_images é obrigatório e deve conter ao menos 1 imagem")
    if normalized_operation == "color_variations" and not color_images_bytes:
        raise HTTPException(
            status_code=400,
            detail="color_images é obrigatório quando operation=color_variations",
        )

    job_id = create_job(
        meta={
            "pipeline_version": "marketplace_v1",
            "marketplace_channel": normalized_channel,
            "marketplace_operation": normalized_operation,
            "prompt": (prompt or "")[:120].strip() or None,
            "prompt_full": (prompt or "").strip() or None,
            "n_images": 1,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "preset": preset,
            "scene_preference": scene_preference,
            "fidelity_mode": fidelity_mode,
            "pose_flex_mode": pose_flex_mode,
            "has_images": bool(base_images_bytes),
            "image_count": len(base_images_bytes),
            "image_filenames": base_filenames[:10],
            "color_count": len(color_images_bytes),
            "color_filenames": color_filenames[:10],
        }
    )

    def _worker() -> None:
        def _stage_cb(stage: str, event: dict) -> None:
            update_stage(job_id, stage, event)

        try:
            response = run_marketplace_orchestration(
                marketplace_channel=normalized_channel,
                operation=normalized_operation,
                base_images_bytes=base_images_bytes,
                base_filenames=base_filenames,
                color_images_bytes=color_images_bytes,
                color_filenames=color_filenames,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                preset=preset,
                scene_preference=scene_preference,
                fidelity_mode=fidelity_mode,
                pose_flex_mode=pose_flex_mode,
                on_stage=_stage_cb,
            )
            summary = response.get("summary") or {}
            completed_slots = int(summary.get("completed_slots", 0) or 0)
            failed_slots = int(summary.get("failed_slots", 0) or 0)
            if completed_slots <= 0:
                fail_job(job_id, "Nenhum slot foi gerado com sucesso no fluxo Marketplace")
                return
            stage = "done_partial" if failed_slots > 0 else "done"
            complete_job(job_id, response, stage=stage)
        except Exception as exc:
            fail_job(job_id, str(exc))

    start_job(job_id, _worker)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
async def get_marketplace_job(job_id: str):
    return get_job(job_id)
