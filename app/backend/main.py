"""
FastAPI app principal — Studio Local v0.1
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import generate, pool as pool_router
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
app.include_router(pool_router.router)

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
            "GET  /pool":     "Lista reference pool",
            "POST /pool/add": "Adiciona referência ao pool (modelo/roupa/cenario)",
            "DELETE /pool/{id}": "Remove referência do pool",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
