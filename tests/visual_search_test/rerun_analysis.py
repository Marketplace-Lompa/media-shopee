"""
Re-roda APENAS a análise Gemini nas referências filtradas existentes.
Não faz busca de imagens nem geração — apenas extrai o novo prompt_gerador.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Adiciona raiz do projeto ao path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from google import genai
from google.genai import types

# Importa o prompt atualizado
from test_visual_pipeline import ANALYSIS_PROMPT

OUTPUT_DIR = Path(__file__).parent / "output"
API_KEY = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")

def main():
    client = genai.Client(api_key=API_KEY)
    
    # Carrega as 5 referências filtradas
    image_parts = []
    for i in range(1, 6):
        img_path = OUTPUT_DIR / f"filtered_{i}.jpg"
        if not img_path.exists():
            print(f"⚠️  {img_path.name} não encontrada, pulando...")
            continue
        print(f"📷 Carregando {img_path.name}...")
        img_data = img_path.read_bytes()
        image_parts.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))
    
    if not image_parts:
        print("❌ Nenhuma referência encontrada!")
        return
    
    print(f"\n🧠 Enviando {len(image_parts)} referências para análise (gemini-2.5-pro)...")
    print("   Aguarde — pode levar 1-2 minutos...\n")
    
    # Monta conteúdo: imagens + prompt
    contents = image_parts + [types.Part.from_text(text=ANALYSIS_PROMPT)]
    
    # Chama Gemini 2.5 Pro
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=types.GenerateContentConfig(
                max_output_tokens=65536,
                temperature=0.7,
            )
        )
    except Exception as e:
        print(f"⚠️  Gemini 2.5 Pro falhou ({e}), tentando Flash...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                max_output_tokens=65536,
                temperature=0.7,
            )
        )
    
    raw_text = response.text
    
    # Salva resposta bruta
    raw_path = OUTPUT_DIR / "analysis_raw_v2.md"
    raw_path.write_text(raw_text, encoding="utf-8")
    print(f"📝 Resposta bruta salva: {raw_path.name}")
    
    # Extrai JSON
    json_text = raw_text
    if "```json" in json_text:
        json_text = json_text.split("```json")[1].split("```")[0]
    elif "```" in json_text:
        json_text = json_text.split("```")[1].split("```")[0]
    
    try:
        analysis = json.loads(json_text)
        
        # Salva JSON
        json_path = OUTPUT_DIR / "analysis_v2.json"
        json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ JSON salvo: {json_path.name}")
        
        # Extrai e salva prompt_gerador
        prompt = analysis.get("prompt_gerador", "")
        if prompt:
            prompt_path = OUTPUT_DIR / "prompt_gerador_v2.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            print(f"\n{'='*60}")
            print(f"🎯 PROMPT GERADOR V2 salvo: {prompt_path.name}")
            print(f"{'='*60}")
            print(f"\n{prompt[:500]}...")
            print(f"\n📏 Tamanho: {len(prompt)} caracteres, ~{len(prompt.split())} palavras")
        else:
            print("⚠️  prompt_gerador não encontrado no JSON!")
            
    except json.JSONDecodeError as e:
        print(f"⚠️  Erro ao parsear JSON: {e}")
        print("   Verifique analysis_raw_v2.md manualmente")

if __name__ == "__main__":
    main()
