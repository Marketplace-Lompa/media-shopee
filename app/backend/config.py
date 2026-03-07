"""
Configurações globais da aplicação.
Centraliza API key, safety settings e valores padrão.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from google.genai import types

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent.parent     # MEDIA-SHOPEE/
BACKEND_DIR = Path(__file__).parent               # app/backend/
POOL_DIR = ROOT_DIR / "app" / "pool"              # app/pool/
OUTPUTS_DIR = ROOT_DIR / "app" / "outputs"        # app/outputs/
POOL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ── API Key ───────────────────────────────────────────────────────────────────
load_dotenv(ROOT_DIR / ".env")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
if not GOOGLE_AI_API_KEY:
    raise RuntimeError("GOOGLE_AI_API_KEY não encontrada no .env")

# ── Modelos ───────────────────────────────────────────────────────────────────
MODEL_AGENT   = "gemini-3-flash-preview"            # Prompt Agent (texto)
MODEL_IMAGE   = "gemini-3.1-flash-image-preview"    # Nano Banana 2 (imagem)

# ── Defaults de geração ───────────────────────────────────────────────────────
DEFAULT_ASPECT_RATIO = "1:1"
DEFAULT_RESOLUTION   = "1K"
DEFAULT_N_IMAGES     = 1

VALID_ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]
VALID_RESOLUTIONS   = ["1K", "2K", "4K"]
VALID_N_IMAGES      = [1, 2, 3, 4]

# Thinking é SEMPRE decidido pelo agente — nunca exposto ao usuário
# Valores válidos (MEDIUM não existe no modelo de imagem):
VALID_THINKING_LEVELS = ["MINIMAL", "HIGH"]

# ── Pool de referências ───────────────────────────────────────────────────────
POOL_TYPES = ["modelo", "roupa", "cenario"]
POOL_MAX_REFS = 8   # máximo de imagens passadas como contexto visual ao Nano

# ── Safety — BLOCK_NONE (projeto de moda/lingerie) ────────────────────────────
# Necessário para evitar falsos positivos em lingerie, biquíni,
# decotes, costas expostas. Não viola TOS — conteúdo comercial de catálogo.
SAFETY_CONFIG = [
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",         threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",        threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",  threshold="BLOCK_NONE"),
]
