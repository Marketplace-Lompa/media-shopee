#!/usr/bin/env python3
"""
Micro-tarefa 0b — Teste da API do Gemini 3.1 Flash (texto — agente de prompt).

Valida:
  ✅ Autenticação com API key
  ✅ Chamada de texto simples (chat single-turn)
  ✅ Chamada com system_instruction (base do Prompt Agent)
  ✅ Retorno JSON estruturado com parâmetros de geração

Uso:
  cd /Users/lompa-marketplace/Documents/MEDIA-SHOPEE
  python app/tests/test_flash.py
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

# ── System instruction do Prompt Agent (versão mínima para teste) ─────────────
SYSTEM_INSTRUCTION = """
You are a specialized prompt engineer for Nano Banana 2 (gemini-3.1-flash-image-preview).
Your job is to receive a brief request in Brazilian Portuguese and return a JSON object with:

{
  "prompt": "<optimized English prompt for Nano Banana 2, max 150 words>",
  "aspect_ratio": "<1:1 | 9:16 | 16:9 | 3:4>",
  "resolution": "<1K (default) | 2K | 4K>",
  "thinking_level": "<MINIMAL | MEDIUM | HIGH>"
}

Rules:
- Thinking HIGH for complex textures (crochet, lace, Aran), text in image, or multi-element layouts
- Thinking MEDIUM for standard fashion shots
- Thinking MINIMAL for simple scenes, catalog, ghost mannequin
- Resolution 1K is the default — use 2K only for final hero renders or macro texture shots, 4K only when explicitly requested
- Prompt must be in English, narrative and descriptive (not keyword list)
- Include: model description, garment, pose, scenario, camera, lighting, realism markers
- NO quality tags (8K, masterpiece, ultra HD)
- Garment must be the protagonist
- Return ONLY the JSON object, no markdown, no extra text
"""

# ── Testes ────────────────────────────────────────────────────────────────────
def test_flash_texto_simples():
    print("\n🧪 TESTE 1: Gemini 3.1 Flash — chamada de texto simples")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=["Responda apenas: 'API OK'"],
        )
        texto = response.text.strip()
        if "API OK" in texto or "api ok" in texto.lower():
            print(f"   ✅ Flash respondeu: '{texto}'")
            return True
        else:
            print(f"   ✅ Flash respondeu (texto livre): '{texto[:100]}'")
            return True
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


def test_flash_prompt_agent():
    print("\n🧪 TESTE 2: Gemini 3.1 Flash — Prompt Agent com system instruction")

    client = genai.Client(api_key=api_key)

    user_request = (
        "Quero uma foto hero para Shopee de uma blusa de crochê branca, "
        "modelo brasileira morena, pose dinâmica em cenário urbano de São Paulo."
    )

    print(f"   Input: \"{user_request[:60]}...\"")

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[user_request],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=1024,
            ),
        )

        raw = response.text.strip()

        # Tentar parsear como JSON
        # Remove possível markdown ```json ... ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        resultado = json.loads(raw)

        print("   ✅ JSON retornado:")
        print(f"      prompt        : {resultado.get('prompt', '')[:80]}...")
        print(f"      aspect_ratio  : {resultado.get('aspect_ratio')}")
        print(f"      resolution    : {resultado.get('resolution')}")
        print(f"      thinking_level: {resultado.get('thinking_level')}")
        print(f"      thinking_reason: {resultado.get('thinking_reason')}")
        return resultado

    except json.JSONDecodeError as e:
        print(f"   ⚠️  Resposta não é JSON puro. Raw:\n{raw[:300]}")
        print(f"   Erro JSON: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return None


if __name__ == "__main__":
    ok1 = test_flash_texto_simples()
    resultado_agent = test_flash_prompt_agent()
    ok2 = resultado_agent is not None

    print("\n" + "─" * 50)
    print(f"  Teste 1 (texto simples): {'✅' if ok1 else '❌'}")
    print(f"  Teste 2 (prompt agent): {'✅' if ok2 else '❌'}")

    sys.exit(0 if (ok1 and ok2) else 1)
