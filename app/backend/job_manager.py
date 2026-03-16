"""
Gerenciador local de jobs assíncronos (in-memory).
Inclui observabilidade completa: logs visuais no terminal + meta rico.

Proteções de produção:
  - Timeout rígido por job (JOB_TIMEOUT_S) — mata zumbis automaticamente.
  - Semáforo de concorrência (MAX_CONCURRENT) — rejeita excedente com 429.
  - Reaper periódico — varre jobs órfãos a cada 30s.
"""
from __future__ import annotations

import json
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock, Semaphore
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException

# ── Configuração ───────────────────────────────────────────────────────────────
MAX_CONCURRENT = 3          # máx. jobs rodando ao mesmo tempo
JOB_TIMEOUT_S  = 180        # 3 minutos — nenhum job pode ultrapassar isso
REAPER_INTERVAL_S = 30      # intervalo do varredura de órfãos

_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_CONCURRENT + 1, thread_name_prefix="gen-job")
_LOCK = Lock()
_SEMAPHORE = Semaphore(MAX_CONCURRENT)
_JOBS: Dict[str, Dict[str, Any]] = {}
_FUTURES: Dict[str, Future] = {}   # rastreia a Future de cada job

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
    with _LOCK:
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
    with _LOCK:
        row = _JOBS.get(job_id)
        if not row:
            return
        row.update(fields)
        row["updated_at"] = _now_ms()


def start_job(job_id: str, worker: Callable[[], Any]) -> None:
    """
    Submete o job ao executor com:
      1. Semáforo — bloqueia se já há MAX_CONCURRENT rodando (evita colapso).
      2. Timeout — se worker() não retornar em JOB_TIMEOUT_S, marca como failed.
    """

    # Checar se já temos muitos jobs em execução; rejeitar se a fila está cheia
    # (acquire com timeout=0 = não-bloqueante)
    if not _SEMAPHORE.acquire(blocking=False):
        active_count = MAX_CONCURRENT  # todos os slots ocupados
        err_msg = (
            f"Servidor ocupado: {active_count}/{MAX_CONCURRENT} jobs simultâneos. "
            "Aguarde um finalizar antes de submeter outro."
        )
        _update(job_id, status="error", error=err_msg, stage="error",
                event={"stage": "error", "message": err_msg})
        print(f"\n[JOB 🚫 REJECTED] {job_id} — fila cheia ({active_count}/{MAX_CONCURRENT})\n")
        return

    def _runner() -> None:
        started_at = _now_ms()
        try:
            # Registrar timestamp de início
            with _LOCK:
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

            # ── Executar worker com timeout rígido ─────────────────────
            worker_future: Future = ThreadPoolExecutor(max_workers=1).submit(worker)
            try:
                worker_future.result(timeout=JOB_TIMEOUT_S)
            except TimeoutError:
                worker_future.cancel()
                timeout_msg = f"Job ultrapassou o limite de {JOB_TIMEOUT_S}s e foi cancelado automaticamente."
                _update(job_id, status="error", error=timeout_msg, stage="timeout",
                        event={"stage": "timeout", "message": timeout_msg})
                _log_job_failed(job_id, started_at, timeout_msg)
                return
            except Exception as e:
                _update(job_id, status="error", error=str(e), stage="error",
                        event={"stage": "error", "message": str(e)})
                _log_job_failed(job_id, started_at, str(e))
                return

        except Exception as e:
            _update(job_id, status="error", error=str(e))
            _log_job_failed(job_id, started_at, str(e))
        finally:
            # Sempre liberar o semáforo — slot volta a ficar disponível
            _SEMAPHORE.release()
            # Limpar referência da future
            with _LOCK:
                _FUTURES.pop(job_id, None)

    future = _EXECUTOR.submit(_runner)
    with _LOCK:
        _FUTURES[job_id] = future


def update_stage(job_id: str, stage: str, event: dict) -> None:
    _update(job_id, status="running", stage=stage, event=event)


def complete_job(job_id: str, response: dict, stage: str = "done") -> None:
    with _LOCK:
        row = _JOBS.get(job_id)
        started_at = (row or {}).get("started_at") if row else None
    _update(job_id, status="done", response=response, stage=stage, event={"stage": stage})
    _log_job_done(job_id, started_at, stage)


def fail_job(job_id: str, error: str) -> None:
    with _LOCK:
        row = _JOBS.get(job_id)
        started_at = (row or {}).get("started_at") if row else None
    _update(job_id, status="error", error=error, stage="error", event={"stage": "error", "message": error})
    _log_job_failed(job_id, started_at, error)


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


# ── Reaper: varredura periódica de jobs órfãos ─────────────────────────────────

def _reap_orphans() -> None:
    """Varre jobs que estão 'running' há mais de JOB_TIMEOUT_S e os marca como failed."""
    now = _now_ms()
    orphans: list[tuple[str, int]] = []

    with _LOCK:
        for jid, row in _JOBS.items():
            if row["status"] not in ("queued", "running"):
                continue
            started = row.get("started_at") or row.get("created_at", 0)
            elapsed_s = (now - started) / 1000
            if elapsed_s > JOB_TIMEOUT_S:
                orphans.append((jid, int(elapsed_s)))

    for jid, elapsed in orphans:
        msg = f"Job órfão detectado ({elapsed}s sem resposta). Cancelado pelo reaper."
        _update(jid, status="error", error=msg, stage="orphan_timeout",
                event={"stage": "orphan_timeout", "message": msg})
        print(f"\n[REAPER 💀] {jid} — rodando há {elapsed}s, marcado como failed\n")

        # Tentar cancelar a future se ainda existir
        with _LOCK:
            future = _FUTURES.pop(jid, None)
        if future and not future.done():
            future.cancel()


def _reaper_loop() -> None:
    """Loop infinito do reaper em background daemon thread."""
    while True:
        try:
            _reap_orphans()
        except Exception as e:
            print(f"[REAPER ⚠️] Erro no reaper: {e}")
        time.sleep(REAPER_INTERVAL_S)


# Iniciar reaper como daemon thread (morre junto com o processo principal)
_reaper_thread = threading.Thread(target=_reaper_loop, daemon=True, name="job-reaper")
_reaper_thread.start()
