"""
Router: POST /generate/stream
SSE (Server-Sent Events) usando o túnel unificado do generation_flow.
"""
from __future__ import annotations

import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from agent_runtime.generation_flow import (
    build_generation_response_payload,
    normalize_generation_options,
    persist_generation_history,
    run_generation_flow as run_pipeline_v2,
)
from config import DEFAULT_ASPECT_RATIO, DEFAULT_N_IMAGES, DEFAULT_RESOLUTION, VALID_N_IMAGES
from request_validation import validate_generation_params

router = APIRouter(prefix="/generate", tags=["generate-stream"])


def _sse_event(stage: str, data: dict) -> str:
    payload = json.dumps({"stage": stage, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


@router.post("/stream")
async def generate_stream(
    prompt: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
    resolution: str = Form(default=DEFAULT_RESOLUTION),
    n_images: int = Form(default=DEFAULT_N_IMAGES),
    grounding_strategy: Optional[str] = Form(default=None),
    use_grounding: bool = Form(default=False),
    guided_brief: Optional[str] = Form(default=None),
    mode: Optional[str] = Form(default=None),
    scene_preference: str = Form(default="auto_br"),
    fidelity_mode: str = Form(default="balanceada"),
    pose_flex_mode: str = Form(default="auto"),
    images: List[UploadFile] = File(default=[]),
):
    # Mantidos por compatibilidade de contrato; o túnel unificado resolve a estratégia internamente.
    _ = grounding_strategy, use_grounding, guided_brief

    try:
        validate_generation_params(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            n_images=n_images,
            valid_n_images=VALID_N_IMAGES,
        )
    except ValueError as e:
        return StreamingResponse(
            iter([_sse_event("error", {"message": str(e)})]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    uploaded_bytes = []
    uploaded_filenames = []
    for img in images[:14]:
        uploaded_bytes.append(await img.read())
        uploaded_filenames.append(str(img.filename or "").strip())

    async def event_generator():
        try:
            validate_generation_params(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                n_images=n_images,
                valid_n_images=VALID_N_IMAGES,
            )
        except ValueError as e:
            yield _sse_event("error", {"message": str(e)})
            return

        collected_events: list[dict] = []
        normalized_mode, normalized_scene_preference, normalized_fidelity_mode, normalized_pose_flex_mode = (
            normalize_generation_options(
                mode=mode,
                scene_preference=scene_preference,
                fidelity_mode=fidelity_mode,
                pose_flex_mode=pose_flex_mode,
            )
        )

        def _on_stage(stage: str, data: dict) -> None:
            collected_events.append({"stage": stage, **data})

        try:
            raw = await asyncio.to_thread(
                run_pipeline_v2,
                uploaded_bytes=uploaded_bytes,
                uploaded_filenames=uploaded_filenames,
                prompt=prompt,
                mode=normalized_mode,
                scene_preference=normalized_scene_preference,
                fidelity_mode=normalized_fidelity_mode,
                pose_flex_mode=normalized_pose_flex_mode,
                n_images=n_images,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                on_stage=_on_stage,
            )
        except Exception as e:
            yield _sse_event("error", {"message": str(e)})
            return

        for evt in collected_events:
            stage = evt.pop("stage", "unknown")
            if stage not in {"done", "done_partial"}:
                yield _sse_event(stage, evt)

        persist_generation_history(
            raw,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            mode=normalized_mode,
            scene_preference=normalized_scene_preference,
            fidelity_mode=normalized_fidelity_mode,
            pose_flex_mode=normalized_pose_flex_mode,
        )
        response_data = build_generation_response_payload(
            raw,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            preset=normalized_mode,
            scene_preference=normalized_scene_preference,
            fidelity_mode=normalized_fidelity_mode,
            pose_flex_mode=normalized_pose_flex_mode,
        )
        final_stage = "done_partial" if response_data.get("failed_indices") else "done"
        yield _sse_event(final_stage, {"data": response_data})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
