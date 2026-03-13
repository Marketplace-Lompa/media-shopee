"""
Router: POST /edit/stream
SSE para edição pontual de imagens existentes via Nano Banana 2.
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

from edit_agent import refine_edit_instruction
from generator import edit_image, OUTPUTS_DIR
from history import add_entry as history_add
from config import DEFAULT_ASPECT_RATIO, DEFAULT_RESOLUTION

router = APIRouter(prefix="/edit", tags=["edit-stream"])


def _sse_event(stage: str, data: dict) -> str:
    payload = json.dumps({"stage": stage, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


@router.post("/stream")
async def edit_stream(
    source_url: str = Form(...),
    edit_instruction: str = Form(...),
    source_prompt: Optional[str] = Form(default=None),
    source_session_id: Optional[str] = Form(default=None),
    aspect_ratio: Optional[str] = Form(default=None),
    resolution: Optional[str] = Form(default=None),
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
            agent_result = await asyncio.to_thread(
                refine_edit_instruction,
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

        final_prompt = agent_result.get("final_prompt", edit_instruction)
        edit_type = agent_result.get("edit_type", "general")
        change_summary = agent_result.get("change_summary_ptbr", edit_instruction)

        yield _sse_event("prompt_ready", {
            "message": "Prompt de edição pronto",
            "prompt": final_prompt,
            "edit_type": edit_type,
            "change_summary": change_summary,
            "confidence": agent_result.get("confidence", 0.5),
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
                edit_image,
                source_image_bytes=source_bytes,
                edit_prompt=final_prompt,
                aspect_ratio=used_ar,
                resolution=used_res,
                session_id=session_id,
                reference_images_bytes=ref_images_bytes if ref_images_bytes else None,
            )
        except Exception as e:
            yield _sse_event("error", {
                "message": f"Erro na geração de edição: {str(e)}",
            })
            return

        # ── 4. Salvar no histórico ────────────────────────────────────
        images_out = []
        for img_info in batch:
            entry = history_add(
                session_id=session_id,
                filename=img_info["filename"],
                url=img_info["url"],
                prompt=final_prompt,
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
