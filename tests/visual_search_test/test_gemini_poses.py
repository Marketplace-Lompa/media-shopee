"""
Teste Gemini puro (sem grounding): poses ideais para moda por identidade visual.
Modos: clean, natural/lifestyle, premium
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_KEY = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_AI_API_KEY não encontrada")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# ── Importa as identidades reais dos modes do código ──
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "backend"))
from agent_runtime.mode_identity_soul import _MODE_IDENTITY_SOULS

# Monta o bloco de identidade real
modes_text = ""
for mode_id, soul_lines in _MODE_IDENTITY_SOULS.items():
    modes_text += f"\n### MODE: `{mode_id}`\n"
    for line in soul_lines:
        modes_text += f"{line}\n"

prompt = f"""Você é um poeta visual que entende moda como linguagem emocional.

Eu tenho 4 modos visuais para fotografar roupas. Cada modo já tem uma identidade
definida — sua ALMA, suas regras, seus anti-padrões. Estou te passando a identidade
completa de cada um abaixo.

Com base NESSA identidade real, NÃO quero descrições técnicas. Quero que você
descreva o que cada modo É como sentimento, como estado de espírito, como atmosfera
invisível.

Pense assim: se cada modo fosse uma pessoa, como ela respira? Como ela entra numa
sala? O que ela sente quando ninguém está olhando?

## IDENTIDADES REAIS DOS MODES:
{modes_text}
---

Para CADA modo, responda:

1. **Se fosse um sentimento**, qual seria? Descreva em uma frase poética.
2. **Se fosse uma hora do dia**, qual e por quê?
3. **Se fosse um som**, o que a pessoa ouviria?
4. **A respiração** — a modelo respira como? Rápido, lento, fundo, contido?
5. **O silêncio** — que tipo de silêncio existe nessa foto? Confortável? Tenso? Vazio? Cheio?
6. **A temperatura emocional** — quente, fria, morna? A pele arrepia ou relaxa?
7. **O que a mulher nessa foto SABE sobre si mesma** que não precisa dizer pra ninguém?
8. **Em uma palavra** — a essência destilada.

NÃO mencione câmeras, lentes, iluminação, fundo, cenário, cores ou qualquer referência técnica.
Apenas abstração pura. Sentimento. Estado interno. Derivado da identidade real que te passei.

Responda em português brasileiro, com linguagem poética mas precisa.
"""

print("🧠 Gemini Flash — Alma dos 3 Modos")
print("=" * 60)
print("   Abstração pura — sentimento, não técnica")
print("=" * 60)

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        max_output_tokens=8192,
        temperature=0.8,
    ),
)

# Debug de resposta
text = None
try:
    text = response.text
except Exception as e:
    print(f"⚠️ response.text falhou: {e}")

if not text:
    # Fallback: extrair de candidates
    print("⚠️ response.text vazio, tentando extrair de candidates...")
    try:
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text = (text or "") + part.text
    except Exception as e:
        print(f"❌ Falha ao extrair: {e}")

if not text:
    print("❌ Resposta completamente vazia. Possível rate limit.")
    print(f"   response: {response}")
    sys.exit(1)

print(f"\n{text}")

# Salva
output_path = Path(__file__).parent / "output_agentic" / "alma_dos_modes.md"
output_path.parent.mkdir(exist_ok=True)
output_path.write_text(text, encoding="utf-8")
print(f"\n💾 Salvo em: {output_path}")
print(f"📏 {len(text)} chars, ~{len(text.split())} palavras")

