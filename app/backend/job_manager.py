"""
Gerenciador local de jobs assíncronos (in-memory).
"""
from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException

_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gen-job")
_LOCK = Lock()
_JOBS: Dict[str, Dict[str, Any]] = {}


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_job(meta: Optional[dict] = None) -> str:
    job_id = str(uuid.uuid4())[:12]
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",  # queued | running | done | error
            "created_at": _now_ms(),
            "updated_at": _now_ms(),
            "stage": None,
            "event": None,
            "response": None,
            "error": None,
            "meta": meta or {},
        }
    return job_id


def _update(job_id: str, **fields: Any) -> None:
    with _LOCK:
        row = _JOBS.get(job_id)
        if not row:
            return
        row.update(fields)
        row["updated_at"] = _now_ms()


def start_job(job_id: str, worker: Callable[[], Any]) -> None:
    def _runner() -> None:
        _update(job_id, status="running")
        try:
            worker()
        except Exception as e:
            _update(job_id, status="error", error=str(e))

    _EXECUTOR.submit(_runner)


def update_stage(job_id: str, stage: str, event: dict) -> None:
    _update(job_id, status="running", stage=stage, event=event)


def complete_job(job_id: str, response: dict, stage: str = "done") -> None:
    _update(job_id, status="done", response=response, stage=stage, event={"stage": stage})


def fail_job(job_id: str, error: str) -> None:
    _update(job_id, status="error", error=error, stage="error", event={"stage": "error", "message": error})


def get_job(job_id: str) -> dict:
    with _LOCK:
        row = _JOBS.get(job_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
        return dict(row)


def list_jobs(limit: int = 20) -> dict:
    with _LOCK:
        rows = sorted(_JOBS.values(), key=lambda x: x.get("updated_at", 0), reverse=True)
        rows = rows[: max(1, min(100, limit))]
        return {"items": [dict(r) for r in rows], "total": len(_JOBS)}
