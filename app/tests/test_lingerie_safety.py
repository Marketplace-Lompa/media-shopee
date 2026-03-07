#!/usr/bin/env python3
"""
Micro-tarefa 0d — Teste de permissividade máxima para ensaio de lingerie.

Valida:
  ✅ SAFETY_CONFIG BLOCK_NONE funciona para conteúdo de moda íntima
  ✅ Prompt de catálogo profissional não é bloqueado
  ✅ Resultado tem qualidade de catálogo (não cai em modo genérico)

Contexto:
  Projeto de e-commerce de moda/lingerie. BLOCK_NONE é necessário para
  evitar falsos positivos em biquínis, lingeries, decotes, costas expostas.
  Nenhuma regra do TOS do Google é violada — é conteúdo de catálogo comercial.

Uso:
  cd /Users/lompa-marketplace/Documents/MEDIA-SHOPEE
  python app/tests/test_lingerie_safety.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Setup ────────────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    print("❌ ERRO: GOOGLE_AI_API_KEY não encontrada no .env")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client(api_key=api_key)

# ── Safety config — BLOCK_NONE (catálogo de moda íntima) ─────────────────────
# Necessário para evitar falsos positivos em lingerie, biquíni, decotes,
# costas expostas. Não viola TOS — conteúdo comercial de catálogo.
SAFETY_CONFIG = [
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",         threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",        threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",  threshold="BLOCK_NONE"),
]

# ── Prompt de catálogo profissional ───────────────────────────────────────────
PROMPT_CATALOGO = """
A professional lingerie catalog photo of a Brazilian woman in her late 20s 
with a voluptuous curvy figure, warm brown skin, and loose dark wavy hair 
past her shoulders. She wears an elegant ivory lace bralette and matching 
high-waist brief — the lace has a delicate floral pattern with scalloped 
edges, semi-sheer fabric over a nude lining. She stands in a three-quarter 
pose with her weight shifted to her left hip, one hand resting lightly on 
her waist, gazing slightly off-camera with a natural relaxed expression. 
Studio setup: warm diffused natural light from a large window on her right 
side, creating soft shadows that define her silhouette. Clean off-white 
muslin backdrop. Shot on Sony A7III with 85mm f/1.8 lens, shallow depth 
of field softening the background. Slight natural grain, organic composition 
slightly off-center. Fashion editorial catalog quality — tasteful, confident, 
commercial.
"""

# ── Teste ─────────────────────────────────────────────────────────────────────
def test_lingerie_catalog():
    print("\n🧪 TESTE: Lingerie Catalog — BLOCK_NONE safety config")
    print("   Modelo  : gemini-3.1-flash-image-preview")
    print("   Safety  : BLOCK_NONE em todas as categorias")
    print("   Thinking: HIGH | Resolução: 1K | Proporção: 3:4\n")

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[PROMPT_CATALOGO.strip()],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="3:4",
                    image_size="1K",
                ),
                thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
                safety_settings=SAFETY_CONFIG,
            ),
        )

        # Checar se houve bloqueio de safety
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason
            if finish_reason and "SAFETY" in str(finish_reason):
                print(f"   ⚠️  Geração bloqueada por safety: {finish_reason}")
                print("   → Safety config pode não estar sendo aplicada corretamente")
                return False

        # Extrair imagem
        for part in response.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                ext = part.inline_data.mime_type.split("/")[-1]
                caminho = OUTPUT_DIR / f"test_lingerie_catalog.{ext}"
                with open(caminho, "wb") as f:
                    f.write(part.inline_data.data)
                tamanho_kb = caminho.stat().st_size / 1024
                print(f"   ✅ Imagem gerada sem bloqueio: {caminho.name} ({tamanho_kb:.1f} KB)")
                print(f"   📁 {caminho}")
                print(f"\n   ✅ Safety BLOCK_NONE confirmado — conteúdo de catálogo passou sem restrição")
                return caminho

        print("   ❌ Resposta sem imagem (possivelmente bloqueada silenciosamente)")
        print("   Texto da resposta:", response.text[:200] if response.text else "(vazio)")
        return False

    except Exception as e:
        err = str(e)
        if "SAFETY" in err or "safety" in err.lower():
            print(f"   ⚠️  Bloqueado por safety (confirma que BLOCK_NONE não está ativo): {err[:200]}")
        else:
            print(f"   ❌ Erro: {err[:300]}")
        return False


if __name__ == "__main__":
    resultado = test_lingerie_catalog()

    if resultado:
        print(f"\nAbrir para validar:")
        print(f"  open '{resultado}'")
        sys.exit(0)
    else:
        sys.exit(1)
