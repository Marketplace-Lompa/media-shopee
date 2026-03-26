"""
Router: POST /edit/stream  |  POST /edit/async  |  GET /edit/jobs/{job_id}
SSE e async para edição pontual de imagens existentes via Nano Banana 2.
Pipeline simplificado (sem grounding/triage/quality contract).
"""
import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List

from agent_runtime.editing.contracts import ImageEditExecutionRequest
from agent_runtime.editing.executor import execute_image_edit_request
from agent_runtime.editing.freeform_flow import prepare_freeform_edit_prompt
from agent_runtime.editing.guided_angle_flow import prepare_guided_angle_prompt
from generator import OUTPUTS_DIR
from history import add_entry as history_add
from config import DEFAULT_ASPECT_RATIO, DEFAULT_RESOLUTION
from job_manager import create_job, start_job, update_stage, complete_job, fail_job, get_job

router = APIRouter(prefix="/edit", tags=["edit-stream"])


def _resolve_source_path(source_url: str) -> Path:
    """Resolve source_url para caminho absoluto no disco."""
    relative_path = source_url.lstrip("/")
    if relative_path.startswith("outputs/"):
        return OUTPUTS_DIR.parent / relative_path
    return Path(relative_path)


def _sse_event(stage: str, data: dict) -> str:
    payload = json.dumps({"stage": stage, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def _resolve_edit_input_mode(
    *,
    input_mode: Optional[str],
    edit_submode: Optional[str],
) -> str:
    normalized_mode = str(input_mode or "").strip().lower()
    if normalized_mode in {"freeform", "guided_angle"}:
        return normalized_mode
    if str(edit_submode or "").strip().lower() == "angle_transform":
        return "guided_angle"
    return "freeform"


@router.post("/stream")
async def edit_stream(
    source_url: str = Form(...),
    edit_instruction: str = Form(...),
    source_prompt: Optional[str] = Form(default=None),
    source_session_id: Optional[str] = Form(default=None),
    input_mode: Optional[str] = Form(default=None),
    aspect_ratio: Optional[str] = Form(default=None),
    resolution: Optional[str] = Form(default=None),
    edit_submode: Optional[str] = Form(default=None),
    view_intent: Optional[str] = Form(default=None),
    distance_intent: Optional[str] = Form(default=None),
    pose_freedom: Optional[str] = Form(default=None),
    angle_target: Optional[str] = Form(default=None),
    preserve_framing: Optional[bool] = Form(default=True),
    preserve_camera_height: Optional[bool] = Form(default=True),
    preserve_distance: Optional[bool] = Form(default=True),
    preserve_pose: Optional[bool] = Form(default=True),
    source_shot_type: Optional[str] = Form(default=None),
    free_text: Optional[str] = Form(default=None),
    images: List[UploadFile] = File(default=[]),
):
    async def event_generator():
        session_id = str(uuid.uuid4())[:8]

        # ── 1. Carregar imagem original do disco ──────────────────────
        yield _sse_event("editing", {
            "message": "Carregando imagem original…",
            "session_id": session_id,
        })

        # source_url ex: "/outputs/a3b8d1b6/gen_a3b8d1b6_1.png"
        # Precisamos resolver para path absoluto
        relative_path = source_url.lstrip("/")
        if relative_path.startswith("outputs/"):
            file_path = OUTPUTS_DIR.parent / relative_path  # app/outputs/...
        else:
            file_path = Path(relative_path)

        if not file_path.exists():
            yield _sse_event("error", {
                "message": f"Imagem original não encontrada: {source_url}",
            })
            return

        try:
            source_bytes = file_path.read_bytes()
        except Exception as e:
            yield _sse_event("error", {"message": f"Erro ao ler imagem: {e}"})
            return

        # Ler imagens de referência anexadas
        ref_images_bytes = []
        for img_file in images:
            try:
                ref_data = await img_file.read()
                if ref_data:
                    ref_images_bytes.append(ref_data)
            except Exception:
                pass  # ignora referências com erro

        # ── 2. Edit Agent — refinar instrução de edição ───────────────
        yield _sse_event("editing", {
            "message": "Agente analisando instrução de edição…",
            "session_id": session_id,
        })

        try:
            resolved_input_mode = _resolve_edit_input_mode(
                input_mode=input_mode,
                edit_submode=edit_submode,
            )
            if resolved_input_mode == "guided_angle":
                prepared_prompt = await asyncio.to_thread(
                    prepare_guided_angle_prompt,
                    edit_instruction=edit_instruction,
                    view_intent=view_intent,
                    distance_intent=distance_intent,
                    pose_freedom=pose_freedom,
                    angle_target=angle_target,
                    preserve_framing=bool(preserve_framing),
                    preserve_camera_height=bool(preserve_camera_height),
                    preserve_distance=bool(preserve_distance),
                    preserve_pose=bool(preserve_pose),
                    source_shot_type=source_shot_type,
                )
            else:
                prepared_prompt = await asyncio.to_thread(
                    prepare_freeform_edit_prompt,
                    edit_instruction=edit_instruction,
                    source_image_bytes=source_bytes,
                    source_prompt=source_prompt,
                    reference_images_bytes=ref_images_bytes if ref_images_bytes else None,
                )
        except Exception as e:
            yield _sse_event("error", {
                "message": f"Erro no Edit Agent: {str(e)}",
            })
            return

        final_prompt = prepared_prompt.display_prompt or edit_instruction
        edit_type = prepared_prompt.edit_type or "general"
        change_summary = prepared_prompt.change_summary_ptbr or edit_instruction

        yield _sse_event("prompt_ready", {
            "message": "Prompt de edição pronto",
            "prompt": final_prompt,
            "edit_type": edit_type,
            "change_summary": change_summary,
            "confidence": prepared_prompt.confidence,
        })

        # ── 3. Gerar imagem editada via Nano Banana 2 ─────────────────
        yield _sse_event("generating", {
            "message": "Gerando imagem editada via Nano…",
            "current": 1,
            "total": 1,
        })

        used_ar = aspect_ratio or DEFAULT_ASPECT_RATIO
        used_res = resolution or DEFAULT_RESOLUTION

        try:
            batch = await asyncio.to_thread(
                execute_image_edit_request,
                ImageEditExecutionRequest(
                    source_image_bytes=source_bytes,
                    prepared_prompt=prepared_prompt,
                    aspect_ratio=used_ar,
                    resolution=used_res,
                    session_id=session_id,
                    source_session_id=source_session_id,
                    source_prompt_context=(
                        source_prompt if prepared_prompt.include_source_prompt_context else None
                    ),
                    reference_images_bytes=ref_images_bytes if ref_images_bytes else [],
                    edit_submode=("angle_transform" if resolved_input_mode == "guided_angle" else edit_submode),
                    source_shot_type=source_shot_type,
                ),
            )
        except Exception as e:
            yield _sse_event("error", {
                "message": f"Erro na geração de edição: {str(e)}",
            })
            return

        # ── 4. Salvar no histórico ────────────────────────────────────
        images_out = []
        for img_info in batch:
            history_add(
                session_id=session_id,
                filename=img_info["filename"],
                url=img_info["url"],
                prompt=final_prompt,
                optimized_prompt=final_prompt,
                shot_type="edit",
                aspect_ratio=used_ar,
                resolution=used_res,
                source_session_id=source_session_id,
                edit_instruction=edit_instruction,
            )
            images_out.append({
                "url": img_info["url"],
                "filename": img_info["filename"],
                "size_kb": img_info.get("size_kb", 0),
                "mime_type": img_info.get("mime_type", "image/png"),
            })

        # ── 5. SSE done ──────────────────────────────────────────────
        yield _sse_event("done", {
            "message": "Edição concluída",
            "session_id": session_id,
            "source_session_id": source_session_id,
            "edit_submode": edit_submode,
            "edit_type": edit_type,
            "change_summary": change_summary,
            "optimized_prompt": final_prompt,
            "edit_instruction": edit_instruction,
            "images": images_out,
            "aspect_ratio": used_ar,
            "resolution": used_res,
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Async (polling) ───────────────────────────────────────────────────────────

@router.post("/async")
async def edit_async(
    source_url: str = Form(...),
    edit_instruction: str = Form(...),
    source_prompt: Optional[str] = Form(default=None),
    source_session_id: Optional[str] = Form(default=None),
    input_mode: Optional[str] = Form(default=None),
    aspect_ratio: Optional[str] = Form(default=None),
    resolution: Optional[str] = Form(default=None),
    edit_submode: Optional[str] = Form(default=None),
    view_intent: Optional[str] = Form(default=None),
    distance_intent: Optional[str] = Form(default=None),
    pose_freedom: Optional[str] = Form(default=None),
    angle_target: Optional[str] = Form(default=None),
    preserve_framing: Optional[bool] = Form(default=True),
    preserve_camera_height: Optional[bool] = Form(default=True),
    preserve_distance: Optional[bool] = Form(default=True),
    preserve_pose: Optional[bool] = Form(default=True),
    source_shot_type: Optional[str] = Form(default=None),
    free_text: Optional[str] = Form(default=None),
    images: List[UploadFile] = File(default=[]),
):
    """Submete edição de imagem como job assíncrono. Retorna job_id para polling."""
    # Ler bytes das referências na thread do FastAPI (await obrigatório antes do worker)
    ref_images_bytes: List[bytes] = []
    for img_file in images:
        try:
            data = await img_file.read()
            if data:
                ref_images_bytes.append(data)
        except Exception:
            pass

    # Resolver caminho da imagem fonte antes do worker (pode lançar erro cedo)
    file_path = _resolve_source_path(source_url)
    if not file_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Imagem original não encontrada: {source_url}")

    source_bytes = file_path.read_bytes()

    used_ar = aspect_ratio or DEFAULT_ASPECT_RATIO
    used_res = resolution or DEFAULT_RESOLUTION

    job_id = create_job(meta={
        "type": "edit",
        "edit_instruction": edit_instruction[:80],
        "source_url": source_url,
        "aspect_ratio": used_ar,
        "resolution": used_res,
        "ref_count": len(ref_images_bytes),
        "edit_submode": edit_submode,
    })

    def _worker() -> None:
        session_id = str(uuid.uuid4())[:8]
        try:
            update_stage(job_id, "editing", {"message": "Agente analisando instrução de edição…"})
            resolved_input_mode = _resolve_edit_input_mode(
                input_mode=input_mode,
                edit_submode=edit_submode,
            )
            if resolved_input_mode == "guided_angle":
                prepared_prompt = prepare_guided_angle_prompt(
                    edit_instruction=edit_instruction,
                    view_intent=view_intent,
                    distance_intent=distance_intent,
                    pose_freedom=pose_freedom,
                    angle_target=angle_target,
                    preserve_framing=bool(preserve_framing),
                    preserve_camera_height=bool(preserve_camera_height),
                    preserve_distance=bool(preserve_distance),
                    preserve_pose=bool(preserve_pose),
                    source_shot_type=source_shot_type,
                )
            else:
                prepared_prompt = prepare_freeform_edit_prompt(
                    edit_instruction=edit_instruction,
                    source_image_bytes=source_bytes,
                    source_prompt=source_prompt,
                    reference_images_bytes=ref_images_bytes if ref_images_bytes else None,
                )
            update_stage(job_id, "generating", {"message": "Gerando imagem editada via Nano…", "current": 1, "total": 1})
            batch = execute_image_edit_request(
                ImageEditExecutionRequest(
                    source_image_bytes=source_bytes,
                    prepared_prompt=prepared_prompt,
                    aspect_ratio=used_ar,
                    resolution=used_res,
                    session_id=session_id,
                    source_session_id=source_session_id,
                    source_prompt_context=(
                        source_prompt if prepared_prompt.include_source_prompt_context else None
                    ),
                    reference_images_bytes=ref_images_bytes if ref_images_bytes else [],
                    edit_submode=("angle_transform" if resolved_input_mode == "guided_angle" else edit_submode),
                    source_shot_type=source_shot_type,
                )
            )

            images_out = []
            for img_info in batch:
                history_add(
                    session_id=session_id,
                    filename=img_info["filename"],
                    url=img_info["url"],
                    prompt=prepared_prompt.display_prompt,
                    optimized_prompt=prepared_prompt.display_prompt,
                    shot_type="edit",
                    aspect_ratio=used_ar,
                    resolution=used_res,
                    source_session_id=source_session_id,
                    edit_instruction=edit_instruction,
                )
                images_out.append({
                    "url": img_info["url"],
                    "filename": img_info["filename"],
                    "size_kb": img_info.get("size_kb", 0),
                    "mime_type": img_info.get("mime_type", "image/png"),
                })

            complete_job(job_id, {
                "session_id": session_id,
                "images": images_out,
                "edit_instruction": edit_instruction,
                "edit_type": prepared_prompt.edit_type,
                "change_summary": prepared_prompt.change_summary_ptbr,
                "optimized_prompt": prepared_prompt.display_prompt,
                "aspect_ratio": used_ar,
                "resolution": used_res,
                "source_session_id": source_session_id,
                "edit_submode": "angle_transform" if resolved_input_mode == "guided_angle" else edit_submode,
            })

        except Exception as exc:
            fail_job(job_id, str(exc))

    start_job(job_id, _worker)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
async def get_edit_job(job_id: str):
    """Polling de status para jobs de edição assíncronos."""
    return get_job(job_id)
