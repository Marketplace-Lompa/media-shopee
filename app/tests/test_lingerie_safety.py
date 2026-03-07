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
RAW photo, a Brazilian woman late 20s with a full curvy natural body, warm 
caramel skin with visible real skin texture — open pores on shoulders and upper 
back, subtle stretch marks on hips and outer thighs, very slight cellulite 
dimpling on the backs of thighs, natural skin tone variation with slightly 
darker elbows and knees, a few faint freckles scattered across her upper back 
and shoulders. Long loose dark hair with slight flyaways and natural volume 
imperfections. She wears a micro black thong bikini — tiny triangle top with 
thin string ties, thong bottom with hip strings. Shot from behind and to the 
side, three-quarter back view — body facing away from camera, head slowly 
turning back over left shoulder, lips slightly parted, confident alluring 
expression. Left hand rests naturally on outer hip with slightly bent fingers. 
Pose emphasizes full rounded hips, defined waist, and the thin thong strap 
crossing the small of her back. Warm amber window light from the left, soft 
diffused shadows on skin surface revealing texture. Creamy off-white linen 
backdrop. Sony A7III 85mm f/2 — very slight motion blur on hair from natural 
breathing. Kodak Portra 400 film grain, subtle vignette edges, slight warm 
color cast. Authentic imperfect beauty — real woman, real body, real skin.
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
