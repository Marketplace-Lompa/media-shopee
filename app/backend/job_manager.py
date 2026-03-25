"""
Gerenciador local de jobs assíncronos (in-memory).
Inclui observabilidade completa: logs visuais no terminal + meta rico.

Proteções de produção:
  - Timeout rígido por job (JOB_TIMEOUT_S) — mata zumbis automaticamente.
  - Semáforo de concorrência (MAX_CONCURRENT) — rejeita excedente com 429.
  - asyncio.Task nativo (sem ThreadPoolExecutor) para workers async.
  - Fallback sync via asyncio.to_thread para workers legados (sync def).
"""
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException

# ── Configuração ───────────────────────────────────────────────────────────────
MAX_CONCURRENT = 3          # máx. jobs rodando ao mesmo tempo
JOB_TIMEOUT_S  = 600        # 10 minutos — pipeline_v2 roda triage completo por slot

_LOCK = asyncio.Lock()
_SEMAPHORE: Optional[asyncio.Semaphore] = None
_JOBS: Dict[str, Dict[str, Any]] = {}
_TASKS: Dict[str, asyncio.Task] = {}


def _get_semaphore() -> asyncio.Semaphore:
    global _SEMAPHORE
    if _SEMAPHORE is None:
        _SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT)
    return _SEMAPHORE


# ── Parâmetros que aparecem no log visual do terminal ──────────────
_LOG_META_KEYS = [
    "pipeline_version",
    "marketplace_channel",
    "marketplace_operation",
    "preset",
    "n_images",
    "aspect_ratio",
    "resolution",
    "scene_preference",
    "fidelity_mode",
    "pose_flex_mode",
    "grounding_strategy",
    "use_grounding",
    "has_images",
    "image_count",
    "image_filenames",
    "color_count",
    "color_filenames",
    "has_guided_brief",
    "prompt",
]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _format_job_banner(job_id: str, meta: dict) -> str:
    """Monta um banner visual bonito com os parâmetros do job."""
    lines: list[str] = []
    w = 56  # largura interna

    lines.append(f"╔{'═' * w}╗")
    title = f"🚀 JOB STARTED: {job_id}"
    lines.append(f"║  {title:<{w - 2}}║")
    lines.append(f"╠{'═' * w}╣")

    for key in _LOG_META_KEYS:
        if key not in meta:
            continue
        val = meta[key]
        # Formatar valores especiais
        if key == "image_filenames" and isinstance(val, list):
            val_str = ", ".join(val[:5])
            if len(val) > 5:
                val_str += f" (+{len(val) - 5})"
        elif isinstance(val, bool):
            val_str = "Sim" if val else "Não"
        elif isinstance(val, str) and len(val) > 50:
            val_str = val[:47] + "..."
        else:
            val_str = str(val)

        label = key.replace("_", " ").title()
        row = f"{label}: {val_str}"
        lines.append(f"║  {row:<{w - 2}}║")

    lines.append(f"╚{'═' * w}╝")
    return "\n".join(lines)


def _log_job_done(job_id: str, started_at: Optional[int], stage: str) -> None:
    elapsed = ""
    if started_at:
        duration_s = (time.time() * 1000 - started_at) / 1000
        if duration_s >= 60:
            mins = int(duration_s // 60)
            secs = duration_s % 60
            elapsed = f" | duração: {mins}m{secs:.1f}s"
        else:
            elapsed = f" | duração: {duration_s:.1f}s"
    icon = "✅" if stage in ("done", "done_partial") else "⚠️"
    suffix = " (parcial)" if stage == "done_partial" else ""
    print(f"\n[JOB {icon} DONE{suffix}] {job_id}{elapsed}\n")


def _log_job_failed(job_id: str, started_at: Optional[int], error: str) -> None:
    elapsed = ""
    if started_at:
        duration_s = (time.time() * 1000 - started_at) / 1000
        elapsed = f" | duração: {duration_s:.1f}s"
    # Truncar erro para log
    err_short = error[:200] + "..." if len(error) > 200 else error
    print(f"\n[JOB ❌ FAILED] {job_id}{elapsed}\n  └─ {err_short}\n")


# ── CRUD de jobs ───────────────────────────────────────────────────────────────

def create_job(meta: Optional[dict] = None) -> str:
    job_id = str(uuid.uuid4())[:12]
    # Sync lock simples para create_job (chamado da route sync-safe)
    _JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",  # queued | running | done | error
        "created_at": _now_ms(),
        "started_at": None,
        "updated_at": _now_ms(),
        "stage": None,
        "event": None,
        "response": None,
        "error": None,
        "meta": meta or {},
    }
    return job_id


def _update(job_id: str, **fields: Any) -> None:
    row = _JOBS.get(job_id)
    if not row:
        return
    row.update(fields)
    row["updated_at"] = _now_ms()


def start_job(job_id: str, worker: Callable[[], Any]) -> None:
    """
    Submete o job como asyncio.Task:
      - Se worker é async def → roda direto no event loop
      - Se worker é sync def → roda via asyncio.to_thread
      - Semáforo controla concorrência
      - asyncio.wait_for impõe timeout rígido
    """
    sem = _get_semaphore()

    async def _runner() -> None:
        started_at = _now_ms()
        row = _JOBS.get(job_id)
        meta = (row or {}).get("meta", {})
        if row:
            row["started_at"] = started_at

        # Log visual no terminal
        try:
            banner = _format_job_banner(job_id, meta)
            print(f"\n{banner}\n")
        except Exception:
            print(f"\n[JOB 🚀 STARTED] {job_id}\n")

        _update(job_id, status="running")

        try:
            async with sem:
                if inspect.iscoroutinefunction(worker):
                    await asyncio.wait_for(worker(), timeout=JOB_TIMEOUT_S)
                else:
                    # Worker sync → roda em thread para não bloquear o event loop
                    await asyncio.wait_for(
                        asyncio.to_thread(worker),
                        timeout=JOB_TIMEOUT_S,
                    )
        except asyncio.TimeoutError:
            timeout_msg = f"Job ultrapassou o limite de {JOB_TIMEOUT_S}s e foi cancelado automaticamente."
            _update(job_id, status="error", error=timeout_msg, stage="timeout",
                    event={"stage": "timeout", "message": timeout_msg})
            _log_job_failed(job_id, started_at, timeout_msg)
        except Exception as e:
            _update(job_id, status="error", error=str(e), stage="error",
                    event={"stage": "error", "message": str(e)})
            _log_job_failed(job_id, started_at, str(e))
        finally:
            _TASKS.pop(job_id, None)

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_runner(), name=f"job-{job_id}")
    except RuntimeError:
        # Sem event loop ativo — fallback sync
        import concurrent.futures
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        pool.submit(asyncio.run, _runner())
        return

    _TASKS[job_id] = task


def update_stage(job_id: str, stage: str, event: dict) -> None:
    _update(job_id, status="running", stage=stage, event=event)


def complete_job(job_id: str, response: dict, stage: str = "done") -> None:
    row = _JOBS.get(job_id)
    started_at = (row or {}).get("started_at") if row else None
    _update(job_id, status="done", response=response, stage=stage, event={"stage": stage})
    _log_job_done(job_id, started_at, stage)


def fail_job(job_id: str, error: str) -> None:
    row = _JOBS.get(job_id)
    started_at = (row or {}).get("started_at") if row else None
    _update(job_id, status="error", error=error, stage="error", event={"stage": "error", "message": error})
    _log_job_failed(job_id, started_at, error)


def get_job(job_id: str) -> dict:
    row = _JOBS.get(job_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
    return dict(row)


def list_jobs(limit: int = 20) -> dict:
    rows = sorted(_JOBS.values(), key=lambda x: x.get("updated_at", 0), reverse=True)
    rows = rows[: max(1, min(100, limit))]
    return {"items": [dict(r) for r in rows], "total": len(_JOBS)}
