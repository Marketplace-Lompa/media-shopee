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

# ── Grounding ──────────────────────────────────────────────────────────────────
def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


ENABLE_GROUNDING = os.getenv("ENABLE_GROUNDING", "true").strip().lower() == "true"
DEFAULT_GROUNDING_STRATEGY = os.getenv("DEFAULT_GROUNDING_STRATEGY", "auto").strip().lower()
if DEFAULT_GROUNDING_STRATEGY not in {"auto", "on", "off"}:
    DEFAULT_GROUNDING_STRATEGY = "auto"

GROUNDING_THRESHOLD_LOW = _env_float("GROUNDING_THRESHOLD_LOW", 0.45)
GROUNDING_THRESHOLD_HIGH = _env_float("GROUNDING_THRESHOLD_HIGH", 0.65)
AUTO_FULL_COMPLEXITY_THRESHOLD = _env_float("AUTO_FULL_COMPLEXITY_THRESHOLD", 0.60)

# ── Quality contract + reference pack ─────────────────────────────────────────
QUALITY_MIN_FIDELITY = _env_float("QUALITY_MIN_FIDELITY", 0.62)
QUALITY_MIN_COMMERCIAL = _env_float("QUALITY_MIN_COMMERCIAL", 0.60)
REFERENCE_ANALYSIS_MAX = _env_int("REFERENCE_ANALYSIS_MAX", 6)
REFERENCE_GENERATION_MAX = _env_int("REFERENCE_GENERATION_MAX", 14)

# ── Diversity scheduler ────────────────────────────────────────────────────────
DIVERSITY_WINDOW = _env_int("DIVERSITY_WINDOW", 30)
DIVERSITY_MAX_SHARE = _env_float("DIVERSITY_MAX_SHARE", 0.40)

# ── Pool de referências ───────────────────────────────────────────────────────
POOL_TYPES = ["modelo", "roupa", "cenario"]
POOL_MAX_REFS = 8   # máximo de imagens passadas como contexto visual ao Nano

# ── Safety — BLOCK_NONE (projeto de moda/lingerie) ────────────────────────────
# Necessário para evitar falsos positivos em lingerie, biquíni,
# decotes, costas expostas. Não viola TOS — conteúdo comercial de catálogo.
SAFETY_CONFIG = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,         threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,        threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,  threshold=types.HarmBlockThreshold.BLOCK_NONE),
]
