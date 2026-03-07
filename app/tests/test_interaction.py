#!/usr/bin/env python3
"""
Micro-tarefa 0c — Teste de INTERAÇÃO entre Flash (agente) e Nano Banana 2 (gerador).

Fluxo:
  1. Flash recebe pedido em pt-BR
  2. Flash devolve JSON com prompt otimizado + parâmetros de API
  3. Nano Banana 2 gera a imagem com esse prompt e parâmetros
  4. Imagem salva em app/tests/output/test_interaction_output.*

Valida:
  ✅ Pipeline agent → generator funcionando end-to-end
  ✅ Parâmetros do Flash são passados corretamente ao Nano
  ✅ Imagem final condiz com o pedido original

Uso:
  cd /Users/lompa-marketplace/Documents/MEDIA-SHOPEE
  python app/tests/test_interaction.py
"""

import os
import sys
import json
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

# ── Safety config ─────────────────────────────────────────────────────────────
SAFETY_CONFIG = [
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",         threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",        threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",  threshold="BLOCK_NONE"),
]

# ── System instruction do agente ─────────────────────────────────────────────
SYSTEM_INSTRUCTION = """
You are a specialized prompt engineer for Nano Banana 2 (gemini-3.1-flash-image-preview).
Receive a request in Brazilian Portuguese and return ONLY a JSON object (no markdown):

{
  "prompt": "<optimized English prompt, max 150 words, narrative style>",
  "aspect_ratio": "<1:1 | 9:16 | 16:9 | 3:4>",
  "resolution": "<1K (default) | 2K | 4K>",
  "thinking_level": "<MINIMAL | MEDIUM | HIGH>",
  "thinking_reason": "<one line in Portuguese>"
}

Rules:
- Prompt: English only, narrative paragraph, include model + garment + pose + scenario + camera + lighting + realism markers
- NO quality tags (8K, masterpiece, ultra HD)
- Garment is the protagonist
- Thinking HIGH for complex textures (crochet, lace, Aran), text in image, or multi-element layouts
- Thinking MEDIUM for standard fashion shots
- Thinking MINIMAL for simple scenes, catalog, ghost mannequin
- Resolution 1K is the default — use 2K only for final hero renders or macro texture shots, 4K only when explicitly requested
"""

# ── Etapa 1: Flash gera prompt otimizado ─────────────────────────────────────
def chamar_agente(pedido_usuario: str) -> dict | None:
    print(f"\n🤖 AGENTE (Flash) recebeu: \"{pedido_usuario[:70]}...\"")

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[pedido_usuario],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=1024,
            ),
        )

        raw = response.text.strip()

        # Remove markdown ```json ... ``` se vier
        if "```" in raw:
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if match:
                raw = match.group(1)
            else:
                # Tenta extrair qualquer bloco { } do texto
                match2 = re.search(r"\{.*\}", raw, re.DOTALL)
                if match2:
                    raw = match2.group(0)
        elif not raw.startswith("{"):
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                raw = match.group(0)

        resultado = json.loads(raw)
        print(f"   ✅ Prompt gerado ({len(resultado.get('prompt','').split())} palavras)")
        print(f"   📐 {resultado.get('aspect_ratio')} | {resultado.get('resolution')} | thinking: {resultado.get('thinking_level')}")
        print(f"   💬 {resultado.get('thinking_reason')}")
        return resultado

    except Exception as e:
        print(f"   ❌ Agente falhou: {e}")
        return None


# ── Etapa 2: Nano Banana gera imagem ─────────────────────────────────────────
def gerar_imagem(params: dict) -> Path | None:
    prompt = params.get("prompt", "")
    aspect_ratio = params.get("aspect_ratio", "9:16")
    resolution = params.get("resolution", "1K")
    thinking = params.get("thinking_level", "MINIMAL")

    print(f"\n🎨 GERADOR (Nano Banana 2) gerando...")
    print(f"   Prompt: \"{prompt[:100]}...\"")

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=resolution,
                ),
                thinking_config=types.ThinkingConfig(thinking_level=thinking),
                safety_settings=SAFETY_CONFIG,
            ),
        )

        for part in response.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                ext = part.inline_data.mime_type.split("/")[-1]
                caminho = OUTPUT_DIR / f"test_interaction_output.{ext}"
                with open(caminho, "wb") as f:
                    f.write(part.inline_data.data)
                tamanho_kb = caminho.stat().st_size / 1024
                print(f"   ✅ Imagem gerada: {caminho.name} ({tamanho_kb:.1f} KB)")
                print(f"   📁 {caminho}")
                return caminho

        print("   ❌ Resposta sem imagem.")
        return None

    except Exception as e:
        print(f"   ❌ Gerador falhou: {e}")
        return None


# ── Pipeline completo ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    pedido = (
        "Quero uma foto hero para Shopee capa de uma blusa de crochê branca de ponto aberto, "
        "modelo brasileira morena, na faixa dos 25 anos, pose dinâmica com braços abertos, "
        "cenário urbano de São Paulo, calçadão ao entardecer."
    )

    print("=" * 60)
    print("TESTE DE INTERAÇÃO: Flash Agent → Nano Banana 2")
    print("=" * 60)

    # Etapa 1
    params = chamar_agente(pedido)
    if not params:
        print("\n❌ Pipeline interrompido na etapa 1 (Flash)")
        sys.exit(1)

    # Etapa 2
    imagem = gerar_imagem(params)
    if not imagem:
        print("\n❌ Pipeline interrompido na etapa 2 (Nano Banana)")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETO — Interação Flash → Nano funcionando")
    print("=" * 60)
    print(f"\nAbra a imagem para validar visualmente:")
    print(f"  open '{imagem}'")
    sys.exit(0)
