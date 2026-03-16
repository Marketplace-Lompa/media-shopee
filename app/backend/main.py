"""
FastAPI app principal — Studio Local v0.1
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import (
    edit as edit_router,
    generate,
    history as history_router,
    marketplace as marketplace_router,
    pool as pool_router,
    review as review_router,
    stream,
)
from config import OUTPUTS_DIR

app = FastAPI(
    title="Studio Local — Nano Banana 2",
    description="API de geração de imagens com Prompt Agent inteligente para moda e lingerie.",
    version="0.1.0",
)

# ── CORS — permite frontend local (React :5173) e futuro domínio ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(generate.router)
app.include_router(stream.router)
app.include_router(edit_router.router)
app.include_router(marketplace_router.router)
app.include_router(pool_router.router)
app.include_router(history_router.router)
app.include_router(review_router.router)

# ── Serve imagens geradas como estático ──────────────────────────────────────
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/")
async def root():
    return {
        "service": "Studio Local — Nano Banana 2",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "POST /generate": "Gera imagens via Agent → Nano Banana 2",
            "POST /generate/stream": "SSE stream com progresso real",
            "POST /marketplace/async": "Submete fluxo marketplace (slots independentes)",
            "GET  /marketplace/jobs/{job_id}": "Polling de job do fluxo marketplace",
            "GET  /pool":     "Lista dataset pool (cadastro local)",
            "POST /pool/add": "Adiciona imagem ao pool de dataset (modelo/roupa/cenario)",
            "DELETE /pool/{id}": "Remove referência do pool",
            "GET  /history": "Histórico de gerações (paginado)",
            "DELETE /history/{id}": "Remove entry do histórico",
            "GET  /review/latest": "Revisão do último job v2",
            "GET  /review/session/{session_id}": "Revisão de um job específico",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
