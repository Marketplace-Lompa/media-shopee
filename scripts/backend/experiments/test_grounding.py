#!/usr/bin/env python3
"""
Teste Isolado — Google Search Grounding para Cenários Brasileiros.

Simula:
1. Uma peça de roupa da triagem (ex: vestido midi floral)
2. O soul de um mode (lifestyle, natural, editorial_commercial)
3. Pede ao Gemini COM GROUNDING para sugerir cenários reais brasileiros

Objetivo: ver se o grounding retorna dados úteis do mundo real (locais,
tendências, referências visuais) que enriquecem a criação do prompt.

Usage:
  python scripts/backend/experiments/test_grounding.py
  python scripts/backend/experiments/test_grounding.py --mode editorial_commercial
  python scripts/backend/experiments/test_grounding.py --mode natural --garment "jaqueta jeans oversized"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from textwrap import dedent

# ── Setup path ────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[3]
_BACKEND = _ROOT / "app" / "backend"
sys.path.insert(0, str(_BACKEND))

# Carrega .env
from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")

from google import genai
from google.genai import types

# ── Config ────────────────────────────────────────────────
API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_AI_API_KEY não encontrada no .env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-3-flash-preview"

# ── Souls dos modes (extraídos do mode_identity_soul.py) ──
MODE_SOULS = {
    "lifestyle": dedent("""
        SOUL: you are an influencer's photographer capturing a moment mid-life.
        The model is DOING something — her body language originates from an activity in progress.
        The scene is a CO-PROTAGONIST alongside the garment. The image sells a LIFESTYLE, not just clothes.
        Think aspirational but authentic — a desire that feels reachable.
        
        Scene rules:
        - The environment enters the frame as a narrative element. The location MATTERS and tells a story.
        - Invent a specific, vivid Brazilian location.
        - The setting must support the model's activity — she is doing something HERE, and the place explains WHY.
        - Anti-repetition: choose the UNEXPECTED location. Show the garment in a context the viewer never imagined.
    """),
    "natural": dedent("""
        SOUL: you are capturing a real person wearing real clothes in a real place.
        The camera is present but never performative. The scene is QUIET and supportive.
        The model feels like someone you'd actually know.
        
        Scene rules:
        - The scenario is a SUPPORTING ACTOR, never the protagonist.
        - Invent a specific, understated Brazilian everyday setting.
        - The place should feel ordinary, inhabited, and discovered in daily life.
        - Never curated, prestige-coded, or chosen for design status.
        - Avoid hospitality-coded comfort or visually flattering calm.
    """),
    "editorial_commercial": dedent("""
        SOUL: you are a fashion art director shooting for a Brazilian commercial magazine spread.
        Every frame is INTENTIONAL — the angle, the shadow, the pose, the spatial relationship.
        Nothing is accidental. The composition communicates that a creative director made deliberate choices.
        
        Scene rules:
        - Invent a specific, architecturally compelling Brazilian location.
        - Let architectural style, material contrast, light angle, and spatial geometry create editorial authority.
        - Use the depth of Brazilian architecture as authorship, never as postcard cliché.
        - The sophistication must be EARNED through composition, not through showing expensive objects.
    """),
}

# ── Garments simulados ───────────────────────────────────
DEFAULT_GARMENTS = {
    "vestido_midi_floral": dedent("""
        TRIAGEM DA PEÇA:
        - Tipo: Vestido midi
        - Corte: A-line com cintura marcada
        - Tecido: Viscose leve com elastano
        - Estampa: Floral miúdo em tons terrosos (terracota, verde musgo, off-white)
        - Caimento: Fluido, acompanha o corpo sem apertar
        - Detalhes: Decote V, mangas bufantes curtas, botões frontais decorativos
        - Ocasião: Dia a dia, passeio, brunch
        - Estação: Primavera/Verão
        - Público: Mulher 25-40 anos, classe B/C
    """),
}


def run_grounding_test(mode: str, garment_desc: str):
    """Executa o teste de grounding para cenários brasileiros."""

    soul = MODE_SOULS.get(mode)
    if not soul:
        print(f"❌ Mode '{mode}' não encontrado. Opções: {list(MODE_SOULS.keys())}")
        sys.exit(1)

    prompt = dedent(f"""
        Você é um director de arte especialista em fotografia de moda para e-commerce brasileiro (Shopee, Mercado Livre).
        
        Sua tarefa: pesquise na web e sugira 3 CENÁRIOS BRASILEIROS REAIS ideais para fotografar esta peça de roupa,
        considerando as tendências atuais de fotografia de moda, locais populares no Brasil, e o que está funcionando
        em anúncios de e-commerce brasileiros hoje.
        
        {soul}
        
        {garment_desc}
        
        Para cada cenário sugerido, inclua:
        1. LOCALIZAÇÃO ESPECÍFICA (cidade, bairro ou tipo de local real no Brasil)
        2. POR QUE este cenário funciona para esta peça e este mode
        3. HORÁRIO ideal para a luz
        4. REFERÊNCIAS VISUAIS encontradas na sua pesquisa
        5. COMO o cenário complementa a peça (contraste de cores, texturas, mood)
        
        Pesquise tendências REAIS e ATUAIS de fotografia de moda brasileira antes de responder.
        Cite fontes quando possível.
    """)

    print(f"\n{'='*60}")
    print(f"🧪 TESTE DE GROUNDING — Google Search")
    print(f"   Mode: {mode}")
    print(f"   Model: {MODEL}")
    print(f"{'='*60}")
    print(f"\n📝 Prompt enviado ({len(prompt.split())} words)")
    print(f"{'─'*60}")

    # ── Chamada COM Google Search Grounding ──
    print("\n🔍 Executando com Google Search Grounding...")
    try:
        response_grounded = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        text_grounded = response_grounded.text or "(sem texto)"
        print(f"\n✅ RESPOSTA COM GROUNDING ({len(text_grounded)} chars):")
        print(f"{'─'*60}")
        print(text_grounded)

        # ── Metadados de Grounding ──
        metadata = None
        if response_grounded.candidates and response_grounded.candidates[0].grounding_metadata:
            metadata = response_grounded.candidates[0].grounding_metadata
            print(f"\n{'─'*60}")
            print("📊 GROUNDING METADATA:")
            print(f"{'─'*60}")

            # Fontes usadas
            if metadata.grounding_chunks:
                print(f"\n🔗 Fontes consultadas ({len(metadata.grounding_chunks)}):")
                for i, chunk in enumerate(metadata.grounding_chunks, 1):
                    if chunk.web:
                        print(f"   {i}. {chunk.web.title or '(sem título)'}")
                        print(f"      URL: {chunk.web.uri}")

            # Suporte por trecho
            if metadata.grounding_supports:
                print(f"\n📎 Trechos suportados ({len(metadata.grounding_supports)}):")
                for i, support in enumerate(metadata.grounding_supports[:5], 1):
                    if support.segment and support.segment.text:
                        snippet = support.segment.text[:150]
                        scores = support.confidence_scores if support.confidence_scores else []
                        print(f"   {i}. \"{snippet}...\"")
                        if scores:
                            print(f"      Confiança: {[round(s, 3) for s in scores]}")

            # Search entry point
            if metadata.search_entry_point and metadata.search_entry_point.rendered_content:
                print(f"\n🔍 Search Entry Point: (HTML widget disponível)")
        else:
            print("\n⚠️  Sem grounding_metadata na resposta (modelo não usou busca)")

    except Exception as e:
        print(f"\n❌ Erro na chamada com grounding: {e}")
        text_grounded = ""
        metadata = None

    # ── Chamada SEM grounding (baseline) ──
    print(f"\n{'='*60}")
    print("📝 Executando SEM grounding (baseline para comparação)...")
    try:
        response_baseline = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        text_baseline = response_baseline.text or "(sem texto)"
        print(f"\n📋 RESPOSTA BASELINE ({len(text_baseline)} chars):")
        print(f"{'─'*60}")
        print(text_baseline)
    except Exception as e:
        print(f"\n❌ Erro na chamada baseline: {e}")
        text_baseline = ""

    # ── Comparação ──
    print(f"\n{'='*60}")
    print("📊 COMPARAÇÃO:")
    print(f"{'─'*60}")
    print(f"   Grounded: {len(text_grounded)} chars | Baseline: {len(text_baseline)} chars")
    print(f"   Grounded tem fontes: {'✅' if metadata and metadata.grounding_chunks else '❌'}")
    if metadata and metadata.grounding_chunks:
        print(f"   Total de fontes consultadas: {len(metadata.grounding_chunks)}")

    # ── Salvar resultados ──
    reports_dir = _ROOT / "docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_file = reports_dir / f"grounding-test-{mode}.json"

    result = {
        "mode": mode,
        "model": MODEL,
        "garment": garment_desc.strip(),
        "grounded_response": text_grounded,
        "baseline_response": text_baseline,
        "grounding_sources": [],
    }

    if metadata and metadata.grounding_chunks:
        for chunk in metadata.grounding_chunks:
            if chunk.web:
                result["grounding_sources"].append({
                    "title": chunk.web.title,
                    "url": chunk.web.uri,
                })

    out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 Resultado salvo em: {out_file}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Teste de Google Search Grounding para cenários")
    parser.add_argument("--mode", default="lifestyle", choices=list(MODE_SOULS.keys()),
                        help="Mode a testar (default: lifestyle)")
    parser.add_argument("--garment", default=None,
                        help="Descrição livre da peça (default: vestido midi floral)")
    args = parser.parse_args()

    garment_desc = args.garment or DEFAULT_GARMENTS["vestido_midi_floral"]

    run_grounding_test(args.mode, garment_desc)


if __name__ == "__main__":
    main()
