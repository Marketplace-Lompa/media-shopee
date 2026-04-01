"""
Pipeline de Persona Visual — SEM Playwright
Usa Google Search Grounding + URL Context para discovery,
Gemini Pro para síntese da persona, e gera prompt final consolidado.

Arquitetura:
  Fase 1 → Discovery (Google Search grounding)
  Fase 2 → Leitura profunda (URL Context em páginas encontradas)
  Fase 3 → Síntese da persona (brand book JSON)
  Fase 4 → Prompt final consolidado em inglês
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── Setup ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from google import genai
from google.genai import types

OUTPUT_DIR = Path(__file__).parent / "output_grounded"
OUTPUT_DIR.mkdir(exist_ok=True)

API_KEY = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_AI_API_KEY não encontrada no .env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# ═══════════════════════════════════════════════════════════
# FASE 1 — DISCOVERY COM GOOGLE SEARCH GROUNDING
# ═══════════════════════════════════════════════════════════

DISCOVERY_PROMPT = """Você é um trend scout especializado em moda feminina brasileira para e-commerce.

Pesquise no Google informações ATUAIS e RECENTES sobre CADA UM dos tópicos abaixo.

REGRA CRÍTICA DE FONTES — você DEVE buscar e incluir URLs destas 3 plataformas OBRIGATORIAMENTE:
1. **Shopee Brasil** (shopee.com.br) — lojas de moda feminina mais vendidas, fotos de anúncios reais, estética visual que converte, categorias de roupas femininas
2. **Mercado Livre** (mercadolivre.com.br) — anúncios de moda feminina, lojas oficiais, fotos de produto, tendências de busca
3. **Shein Brasil** (shein.com, shein.com.br) — lookbooks, fotos de produto, styling, tendências de moda casual acessível

REGRA DE MÍNIMO: Você DEVE retornar no mínimo 2 URLs de CADA uma dessas 3 plataformas (total mínimo: 6 URLs de marketplaces).
Pode complementar com artigos de moda, editoriais (FFW, Vogue Brasil) ou blogs — mas a BASE são os 3 marketplaces acima.

TÓPICOS PARA PESQUISAR:
1. **Estética visual dominante** em fotos de produto de moda feminina na Shopee, Mercado Livre e Shein (como as fotos são compostas, fundo, pose, enquadramento)
2. **Poses de modelo para e-commerce** mais usadas nessas plataformas (mãos, peso corporal, ângulo do corpo, expressão facial)
3. **Paletas de cor de roupa** em alta — cores que mais aparecem em anúncios populares de moda casual feminina em 2025/2026
4. **Iluminação e cenários** usados em fotos de moda nessas plataformas — luz natural vs estúdio, fundos mais usados
5. **Tipo físico e styling** das modelos em anúncios reais (biotipo, cabelo, maquiagem, acessórios)

RESPONDA em JSON com esta estrutura:
{
  "tendencias_visuais": {
    "estetica_dominante": "descrição detalhada da estética visual que domina Shopee, ML e Shein para moda feminina casual brasileira",
    "poses_populares": ["lista de poses mais usadas em fotos de produto nos marketplaces"],
    "iluminacao_tendencia": "tipo de luz predominante em fotos de produto nos marketplaces",
    "cenarios_tendencia": ["lista de cenários/fundos mais usados em fotos reais de e-commerce"],
    "paleta_cores": ["cores dominantes em anúncios de moda feminina 2025/2026"],
    "biotipos_representados": "descrição dos biotipos e styling mais vistos em anúncios reais de Shopee, ML e Shein"
  },
  "urls_referencia": [
    {"url": "URL real da plataforma", "tipo": "shopee|mercadolivre|shein|editorial|artigo", "relevancia": "por que é relevante"}
  ],
  "insights_chave": [
    "insight 1 extraído dos marketplaces",
    "insight 2...",
    "insight 3..."
  ]
}
"""


# ═══════════════════════════════════════════════════════════
# FASE 2 — LEITURA PROFUNDA COM URL CONTEXT
# ═══════════════════════════════════════════════════════════

def build_deep_read_prompt(urls_info: list, trends_summary: str) -> str:
    """Monta prompt para leitura profunda das URLs encontradas."""
    urls_text = "\n".join([
        f"- {u.get('url', '')} ({u.get('tipo', 'referência')})"
        for u in urls_info[:10]  # Máximo 10 URLs
    ])
    
    return f"""Você é um diretor de arte de moda brasileira.

Contexto de tendências já identificadas:
{trends_summary}

Agora, acesse e leia as seguintes URLs para extrair DETALHES VISUAIS CONCRETOS:
{urls_text}

Para cada URL que conseguir acessar, extraia:
1. **Descrições visuais detalhadas** de modelos, poses, roupas e cenários
2. **Linguagem fotográfica** (tipos de lente, iluminação, composição)
3. **Padrões de styling** (como as roupas são usadas, acessórios, maquiagem)
4. **Tipo físico das modelos** (biotipo, tom de pele, cabelo, traços faciais)
5. **Mood/energia** da fotografia (casual, sofisticada, energética, sensual)

RESPONDA em JSON:
{{
  "leituras": [
    {{
      "url": "...",
      "acessivel": true/false,
      "descricao_visual": "descrição detalhada do que foi encontrado",
      "modelos_descritas": "detalhes físicos das modelos vistas",
      "fotografia": "análise técnica da fotografia",
      "styling": "detalhes de moda e styling"
    }}
  ],
  "sintese_visual": "síntese consolidada de todos os sinais visuais encontrados"
}}
"""


# ═══════════════════════════════════════════════════════════
# FASE 3 — SÍNTESE DA PERSONA (BRAND BOOK)
# ═══════════════════════════════════════════════════════════

PERSONA_PROMPT = """Você é um diretor criativo de uma marca de moda brasileira.

Com base em TODOS os sinais visuais e tendências coletados abaixo, 
crie uma PERSONA VISUAL ORIGINAL e FICTÍCIA para ser a modelo/embaixadora 
de uma marca de moda casual brasileira voltada para e-commerce (Shopee, Instagram Shopping).

A persona NÃO deve se parecer com nenhuma pessoa real específica — 
ela é uma SÍNTESE ORIGINAL dos padrões identificados.

DADOS COLETADOS:
{dados}

RESPONDA em JSON com esta estrutura COMPLETA (TODOS os campos são obrigatórios):

{{
  "casting_profile": {{
    "idade_aparente": "faixa etária (ex: 23-27 anos)",
    "altura_aparente": "altura estimada",
    "biotipo_detalhado": "descrição completa do tipo físico",
    "energia_geral": "como ela se apresenta, que energia transmite"
  }},
  
  "face_geometry": {{
    "formato_rosto": "formato detalhado",
    "olhos": "formato, cor, distância, expressividade",
    "sobrancelhas": "espessura, arco, cor, personalidade",
    "nariz": "formato, proporção",
    "labios": "formato, volume, contorno",
    "macas_do_rosto": "proeminência, formato",
    "linha_do_maxilar": "definição, suavidade",
    "orelhas": "visibilidade, proporção"
  }},
  
  "body_profile": {{
    "proporcao_ombro_cintura_quadril": "relação entre as três medidas",
    "tronco_vs_pernas": "proporção relativa",
    "definicao_muscular": "nível de definição",
    "postura_natural": "como ela naturalmente se segura",
    "silhueta_geral": "descrição da silhueta de corpo inteiro"
  }},
  
  "skin_profile": {{
    "tom_exato": "descrição precisa do tom de pele",
    "subtom": "quente/frio/neutro/oliva",
    "textura": "lisa/porosa/aveludada etc",
    "brilho_natural": "matte/semi-matte/luminosa/dewy",
    "marcas_naturais": "sardas, pintas, bronzeado etc",
    "como_reage_a_luz": "como a pele interage com luz"
  }},
  
  "hair_profile": {{
    "textura_do_fio": "liso/ondulado/cacheado/crespo",
    "volume_e_densidade": "fino/médio/volumoso/muito denso",
    "comprimento_exato": "onde termina em relação ao corpo",
    "cor_com_nuances": "cor base + reflexos + variações",
    "brilho": "fosco/saudável/muito brilhante",
    "como_cai": "como emoldura o rosto e cai nos ombros",
    "estilo_natural": "como ela usa normalmente"
  }},
  
  "pose_library": {{
    "pose_hero": "pose principal para foto de destaque",
    "pose_casual": "pose relaxada do dia-a-dia",
    "pose_confiante": "pose de empoderamento",
    "pose_movimento": "pose com sensação de movimento",
    "maos_padrao": "onde as mãos ficam naturalmente",
    "distribuicao_peso": "como distribui o peso corporal"
  }},
  
  "styling_rules": {{
    "estetica_geral": "minimalista/maximalista/casual/sofisticada",
    "pecas_signature": ["peças que definem o estilo dela"],
    "paleta_de_cores": ["cores que ela mais usa"],
    "acessorios_padrao": "nível e tipo de acessórios",
    "calcado_preferido": "tipos de calçado",
    "makeup_padrao": "estilo de maquiagem default"
  }},
  
  "camera_rules": {{
    "lente_preferida": "lente e abertura padrão",
    "angulo_camera": "posição da câmera em relação à modelo",
    "composicao": "regra de composição preferida",
    "orientacao": "formato da imagem (9:16, 1:1 etc)"
  }},
  
  "lighting_rules": {{
    "tipo_principal": "tipo de luz padrão",
    "direcao": "de onde vem a luz principal",
    "temperatura": "quente/neutra/fria",
    "contraste": "suave/médio/alto",
    "fill_light": "intensidade da luz de preenchimento"
  }},
  
  "scenario_rules": {{
    "cenario_padrao": "cenário default",
    "fundo": "tipo e cor de fundo",
    "elementos": "elementos visuais permitidos",
    "paleta_ambiente": "cores do ambiente"
  }},
  
  "negative_rules": [
    "lista do que NUNCA fazer com esta persona"
  ],

  "prompt_gerador": "PROMPT LONGO E ULTRA-DETALHADO EM INGLÊS, párgrafo único contínuo, NO MÍNIMO 250 palavras, pronto para gerar imagem no Nano Banana Pro. NÃO inclua nomes fictícios — refira-se à modelo apenas como 'a Brazilian model' ou 'the model'. Estrutura OBRIGATÓRIA na ordem: (1) tipo de foto e orientação, (2) ROSTO com mínimo 3 frases detalhando formato, olhos, nariz, lábios, sobrancelhas, maxilar, (3) PELE com mínimo 2 frases detalhando tom, subtom, textura, brilho, (4) CABELO com mínimo 2 frases detalhando textura, volume, cor, como cai, (5) CORPO com mínimo 2 frases detalhando biotipo, proporções, altura, (6) POSE completa, (7) EXPRESSÃO e olhar, (8) ROUPA e styling, (9) CÂMERA lente e abertura, (10) ILUMINAÇÃO, (11) CENÁRIO. O prompt deve incorporar TODOS os detalhes extraídos dos campos acima."
}}
"""


# ═══════════════════════════════════════════════════════════
# EXECUÇÃO
# ═══════════════════════════════════════════════════════════

def save_json(data, filename):
    """Salva JSON formatado."""
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  💾 Salvo: {path.name}")
    return path

def save_text(text, filename):
    """Salva texto."""
    path = OUTPUT_DIR / filename
    path.write_text(text, encoding="utf-8")
    print(f"  💾 Salvo: {path.name}")
    return path

def extract_json(text: str) -> dict:
    """Extrai JSON de resposta que pode conter markdown."""
    clean = text
    if "```json" in clean:
        clean = clean.split("```json")[1].split("```")[0]
    elif "```" in clean:
        clean = clean.split("```")[1].split("```")[0]
    return json.loads(clean.strip())


def run_phase_1():
    """Fase 1 — Discovery com Google Search grounding."""
    print("\n" + "="*60)
    print("🔍 FASE 1: DISCOVERY COM GOOGLE SEARCH")
    print("="*60)
    print("  Pesquisando tendências atuais de moda brasileira...")
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=DISCOVERY_PROMPT,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            max_output_tokens=16384,
            temperature=0.7,
        ),
    )
    
    raw_text = response.text
    save_text(raw_text, "fase1_discovery_raw.md")
    
    # Extrair grounding metadata
    metadata = getattr(response.candidates[0], 'grounding_metadata', None)
    if metadata:
        chunks = getattr(metadata, 'grounding_chunks', []) or []
        sources = [{"url": c.web.uri, "title": c.web.title} for c in chunks if hasattr(c, 'web') and c.web]
        save_json(sources, "fase1_sources.json")
        print(f"  📎 {len(sources)} fontes de grounding encontradas")
    
    # Parse JSON
    try:
        discovery = extract_json(raw_text)
        save_json(discovery, "fase1_discovery.json")
        urls = discovery.get("urls_referencia", [])
        insights = discovery.get("insights_chave", [])
        print(f"  🔗 {len(urls)} URLs de referência encontradas")
        print(f"  💡 {len(insights)} insights extraídos")
        return discovery
    except json.JSONDecodeError:
        print("  ⚠️  Não conseguiu parsear JSON, usando texto bruto")
        return {"raw": raw_text, "urls_referencia": [], "insights_chave": []}


def run_phase_2(discovery: dict):
    """Fase 2 — Leitura profunda com URL Context."""
    print("\n" + "="*60)
    print("📖 FASE 2: LEITURA PROFUNDA COM URL CONTEXT")
    print("="*60)
    
    urls = discovery.get("urls_referencia", [])
    trends = json.dumps(discovery.get("tendencias_visuais", {}), ensure_ascii=False, indent=2)
    
    if not urls:
        print("  ⚠️  Sem URLs para ler, usando apenas insights do discovery")
        return {"leituras": [], "sintese_visual": trends}
    
    print(f"  Lendo {min(len(urls), 10)} URLs com URL Context...")
    
    prompt = build_deep_read_prompt(urls, trends)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(url_context=types.UrlContext())],
                max_output_tokens=16384,
                temperature=0.5,
            ),
        )
        
        raw_text = response.text
        save_text(raw_text, "fase2_deep_read_raw.md")
        
        try:
            deep_read = extract_json(raw_text)
            save_json(deep_read, "fase2_deep_read.json")
            leituras = deep_read.get("leituras", [])
            acessiveis = [l for l in leituras if l.get("acessivel", False)]
            print(f"  📄 {len(acessiveis)}/{len(leituras)} URLs acessíveis e lidas")
            return deep_read
        except json.JSONDecodeError:
            print("  ⚠️  Parse JSON falhou, usando texto bruto")
            return {"leituras": [], "sintese_visual": raw_text[:3000]}
    
    except Exception as e:
        print(f"  ⚠️  URL Context falhou ({e}), prosseguindo com discovery")
        return {"leituras": [], "sintese_visual": trends}


def run_phase_3(discovery: dict, deep_read: dict):
    """Fase 3 — Síntese da persona."""
    print("\n" + "="*60)
    print("🧬 FASE 3: SÍNTESE DA PERSONA")
    print("="*60)
    
    # Consolida todos os dados coletados
    dados_consolidados = {
        "tendencias": discovery.get("tendencias_visuais", {}),
        "insights": discovery.get("insights_chave", []),
        "leituras_profundas": deep_read.get("leituras", []),
        "sintese_visual": deep_read.get("sintese_visual", ""),
    }
    
    dados_text = json.dumps(dados_consolidados, ensure_ascii=False, indent=2)
    prompt = PERSONA_PROMPT.format(dados=dados_text)
    
    print("  Gerando persona com gemini-2.5-pro...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=65536,
                temperature=0.8,
            ),
        )
    except Exception as e:
        print(f"  ⚠️  Gemini Pro falhou ({e}), tentando Flash...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=65536,
                temperature=0.8,
            ),
        )
    
    raw_text = response.text
    save_text(raw_text, "fase3_persona_raw.md")
    
    try:
        persona = extract_json(raw_text)
        save_json(persona, "fase3_persona.json")
        
        print(f"  👤 Persona criada com sucesso")
        
        # Extrai e salva prompt final
        prompt_final = persona.get("prompt_gerador", "")
        if prompt_final:
            save_text(prompt_final, "prompt_final.txt")
            word_count = len(prompt_final.split())
            print(f"  🎯 Prompt final: {len(prompt_final)} chars, ~{word_count} palavras")
        
        return persona
        
    except json.JSONDecodeError as e:
        print(f"  ⚠️  Parse JSON falhou: {e}")
        save_text(raw_text, "fase3_persona_fallback.md")
        return {"raw": raw_text}


def main():
    start = time.time()
    
    print("="*60)
    print("🚀 PIPELINE GROUNDED: Discovery → Leitura → Persona")
    print("="*60)
    print(f"   Modelo Discovery: gemini-2.5-flash + Google Search")
    print(f"   Modelo Leitura:   gemini-2.5-flash + URL Context")
    print(f"   Modelo Síntese:   gemini-2.5-pro")
    print(f"   Output:           {OUTPUT_DIR}")
    print(f"   Início:           {datetime.now().strftime('%H:%M:%S')}")
    
    # Fase 1 — Discovery
    discovery = run_phase_1()
    
    # Fase 2 — Leitura profunda
    deep_read = run_phase_2(discovery)
    
    # Fase 3 — Síntese da persona
    persona = run_phase_3(discovery, deep_read)
    
    elapsed = time.time() - start
    
    print("\n" + "="*60)
    print(f"✅ PIPELINE COMPLETO em {elapsed:.0f}s")
    print("="*60)
    
    # Mostra prompt final se disponível
    prompt_path = OUTPUT_DIR / "prompt_final.txt"
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8")
        print(f"\n{'─'*60}")
        print("🎯 PROMPT FINAL (primeiros 600 chars):")
        print(f"{'─'*60}")
        print(prompt[:600] + "..." if len(prompt) > 600 else prompt)
        print(f"\n📏 Total: {len(prompt)} chars, ~{len(prompt.split())} palavras")
    
    print(f"\n📁 Todos os artefatos em: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
