"""
Router: /review
Revisao de jobs v2 dentro da aplicacao, usando o proprio report do job.
"""
from fastapi import APIRouter, HTTPException

from review_engine import latest_reviewable_session_id, review_job_session

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/latest")
async def get_latest_review(refresh: bool = False):
    session_id = latest_reviewable_session_id()
    if not session_id:
        raise HTTPException(status_code=404, detail="Nenhum job revisavel encontrado")
    try:
        return review_job_session(session_id, refresh=refresh)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/session/{session_id}")
async def get_review_by_session(session_id: str, refresh: bool = False):
    try:
        return review_job_session(session_id, refresh=refresh)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
