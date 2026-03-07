#!/usr/bin/env python3
"""
Micro-tarefa 0a — Teste da API do Nano Banana 2 (gemini-3.1-flash-image-preview).

Valida:
  ✅ Autenticação com API key
  ✅ Geração de imagem simples (1K, 9:16, thinking MINIMAL)
  ✅ Safety settings BLOCK_NONE funcionando
  ✅ Imagem salva em app/tests/output/

Uso:
  cd /Users/lompa-marketplace/Documents/MEDIA-SHOPEE
  python app/tests/test_nano.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Setup ────────────────────────────────────────────────────────────────────
# Carrega .env da raiz do projeto
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    print("❌ ERRO: GOOGLE_AI_API_KEY não encontrada no .env")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Safety config (projeto de moda/lingerie) ─────────────────────────────────
SAFETY_CONFIG = [
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",         threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",        threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",  threshold="BLOCK_NONE"),
]

# ── Teste ─────────────────────────────────────────────────────────────────────
def test_nano_geracao_simples():
    print("\n🧪 TESTE: Nano Banana 2 — geração simples")
    print("   Modelo : gemini-3.1-flash-image-preview")
    print("   Thinking: MINIMAL | Resolução: 1K | Proporção: 9:16\n")

    client = genai.Client(api_key=api_key)

    prompt = (
        "A RAW photo of a Brazilian woman in her late 20s with warm brown skin "
        "and natural wavy dark hair, wearing a white cotton short-sleeve blouse "
        "with a relaxed fit. She stands slightly off-center, mid-stride on a "
        "São Paulo cobblestone sidewalk at golden hour. Shot on Sony A7III, "
        "85mm lens, natural bokeh, slight grain. Organic composition."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="9:16",
                    image_size="1K",
                ),
                thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
                safety_settings=SAFETY_CONFIG,
            ),
        )

        # Extrair imagem da resposta
        imagem_salva = None
        for part in response.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                ext = part.inline_data.mime_type.split("/")[-1]  # jpeg, png, webp
                caminho = OUTPUT_DIR / f"test_nano_output.{ext}"
                with open(caminho, "wb") as f:
                    f.write(part.inline_data.data)
                imagem_salva = caminho
                break

        if imagem_salva:
            tamanho_kb = imagem_salva.stat().st_size / 1024
            print(f"   ✅ Imagem gerada: {imagem_salva.name} ({tamanho_kb:.1f} KB)")
            print(f"   📁 Salva em: {imagem_salva}")
            return True
        else:
            print("   ❌ Resposta sem imagem.")
            print("   Resposta raw:", response)
            return False

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


if __name__ == "__main__":
    ok = test_nano_geracao_simples()
    sys.exit(0 if ok else 1)
