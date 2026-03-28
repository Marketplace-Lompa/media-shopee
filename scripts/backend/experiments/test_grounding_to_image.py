#!/usr/bin/env python3
"""
Teste Isolado — Grounding → Nano Banana 2 (imagem).

Pega um cenário sugerido pelo grounding e gera uma imagem real
com o Nano Banana 2 (gemini-3.1-flash-image-preview).

Usage:
  python scripts/backend/experiments/test_grounding_to_image.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from io import BytesIO

_ROOT = Path(__file__).resolve().parents[3]
_BACKEND = _ROOT / "app" / "backend"
sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from google import genai
from google.genai import types
from PIL import Image

# ── Config ────────────────────────────────────────────────
API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_AI_API_KEY não encontrada")
    sys.exit(1)

client = genai.Client(api_key=API_KEY, http_options={'timeout': 120_000})
MODEL_IMAGE = "gemini-3.1-flash-image-preview"

SAFETY = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,         threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,        threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,  threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# ── Prompt montado com dados do grounding ─────────────────
# Cenário 2 do teste anterior: Galpão Botânico Industrial — CEASA Curitiba
PROMPT = """
A professional lifestyle e-commerce photograph, 9:16 vertical format, shot on Sony A7IV with 35mm f/1.8 lens.

SUBJECT: A Brazilian woman, mid-20s, morena clara with shoulder-length wavy dark brown hair, warm olive skin.
She wears a midi A-line dress with a V-neckline, short puff sleeves, and decorative front buttons.
The dress is made of lightweight, fluid viscose fabric with a small floral print in earthy tones — terracotta, moss green, and off-white.
The fabric drapes softly, following her body without clinging.

SCENE — Galpão Botânico Industrial, Pavilhão de Flores do CEASA Curitiba:
She is mid-activity — carrying a large Monstera deliciosa leaf, walking through the flower pavilion.
The environment is a raw industrial warehouse repurposed for plants — exposed concrete floor,
corrugated metal roof with industrial skylights letting in diffused cool light.
Rows of tropical plants in black plastic pots on metal shelving units.
The contrast between the feminine, fluid dress and the brutal industrial architecture
makes the garment feel modern and urban. She is "the independent woman who decorates her home with style."
Wooden crates, stacked terracotta pots, and scattered green leaves on the concrete floor add lived texture.

LIGHTING: Diffused cool light from industrial skylights, early morning 7-9am.
The overcast-like quality highlights the moss green tones in the floral print without blowing out colors.
Subtle rim light from a side opening catches the fluid movement of the viscose fabric.

MOOD: Aspirational urban lifestyle. She is a modern Brazilian woman who brings nature into her city apartment.
The industrial grit makes the delicate dress feel contemporary, not precious.

TECHNICAL: Sharp focus on the dress and model, shallow depth of field (f/2.0),
the monstera leaf she carries adds a strong graphic element. Cool-neutral color temperature.
No text, no watermark. Brazilian woman, naturally beautiful, mid-stride with confident body language.
"""

def main():
    print(f"\n{'='*60}")
    print(f"🎨 TESTE — Grounding → Nano Banana 2")
    print(f"   Model: {MODEL_IMAGE}")
    print(f"   Cenário: Galpão Botânico Industrial, CEASA Curitiba (PR)")
    print(f"{'='*60}")
    print(f"\n📝 Prompt ({len(PROMPT.split())} words)")
    print(f"{'─'*60}")

    start = time.time()
    print("\n⏳ Gerando imagem com Nano Banana 2...")

    try:
        response = client.models.generate_content(
            model=MODEL_IMAGE,
            contents=PROMPT,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                safety_settings=SAFETY,
            ),
        )
    except Exception as e:
        print(f"\n❌ Erro na geração: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"   ⏱️  Tempo: {elapsed:.1f}s")

    # ── Extrai imagem ─────────────────────────────
    image_saved = False
    text_parts = []
    out_dir = _ROOT / "docs" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img = Image.open(BytesIO(part.inline_data.data))
                out_path = out_dir / "grounding-nano-lifestyle-ceasa.png"
                img.save(str(out_path), format="PNG")
                print(f"\n✅ Imagem salva: {out_path}")
                print(f"   Resolução: {img.size[0]}x{img.size[1]}")
                image_saved = True
            elif part.text:
                text_parts.append(part.text)

    if text_parts:
        print(f"\n💬 Texto do modelo:")
        for t in text_parts:
            print(f"   {t[:300]}")

    if not image_saved:
        print("\n⚠️  Nenhuma imagem retornada pelo modelo")
        if response.candidates:
            print(f"   Finish reason: {response.candidates[0].finish_reason}")
            print(f"   Parts count: {len(response.candidates[0].content.parts)}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
