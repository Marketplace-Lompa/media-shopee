#!/usr/bin/env python3
"""
Teste isolado: Pipeline Visual Search → Análise → Geração
Playwright (busca) → Gemini 2.5 Pro (análise) → Gemini 3.1 Flash Image (geração)

Uso:
    python tests/visual_search_test/test_visual_pipeline.py
    python tests/visual_search_test/test_visual_pipeline.py --skip-generation
    python tests/visual_search_test/test_visual_pipeline.py --query "influencer moda"
"""

import asyncio
import argparse
import json
import os
import sys
import re
from pathlib import Path
from urllib.parse import quote

# ─── Project Setup ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from google import genai
from google.genai import types
from playwright.async_api import async_playwright
from PIL import Image
import io
import httpx

# ─── Config ─────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
ANALYSIS_MODEL = "gemini-2.5-pro"           # Cérebro — análise profunda
GENERATION_MODEL = "gemini-3.1-flash-image-preview"  # Mãos — geração

# Queries otimizadas: fotos profissionais/editoriais de moda brasileira
# Evitam "espelho/selfie" (baixa qualidade) e "shopee/look" (pins com texto)
SEARCH_QUERIES = [
    "modelo brasileira moda casual editorial corpo inteiro",
    "brazilian fashion photography street style women",
    "lookbook feminino brasil roupa casual urbana",
    "influenciadora brasileira foto profissional moda",
]
DEFAULT_QUERY = SEARCH_QUERIES[0]
DOWNLOAD_POOL = 15   # Baixar mais candidatas para filtrar
REF_COUNT = 5         # Manter as N melhores após filtragem


# ─── Prompt de Análise Estruturado ──────────────────────────
ANALYSIS_PROMPT = """Você é um diretor de arte especializado em e-commerce brasileiro e 
fotografia de moda para plataformas como Shopee, TikTok Shop e Instagram Shopping.

Analise cada uma das fotos de referência fornecidas e extraia um perfil visual 
COMPLETO e EXTREMAMENTE DETALHADO nos seguintes 7 eixos.

## 1. MODELO — Características Físicas
- Faixa etária aparente (ex: "22-26 anos")
- Biotipo (magra, curvilínea, atlética, plus-size)
- Tom de pele (claro rosado, claro oliva, médio dourado, moreno, retinto)
- Tipo de cabelo: textura (liso, ondulado, cacheado, crespo), comprimento, cor
- Traços faciais predominantes (formato do rosto, sobrancelhas, nariz, lábios)
- Altura aparente relativa ao enquadramento

## 2. POSE — Linguagem Corporal
- Posição do corpo (frontal, 3/4, perfil, de costas, rotação exata estimada)
- Distribuição de peso (perna dianteira, traseira, centralizado)
- Posição de cada mão (cintura, bolso, segurando objeto, cabelo, livre, apoiada)
- Inclinação da cabeça (reta, leve inclinação lateral, queixo para cima/baixo)
- Posição dos ombros (relaxados, elevados, um mais alto, projetados para frente)
- Expressão das pernas (cruzadas, afastadas, uma à frente, ângulo dos pés)
- Tensão muscular geral (relaxada/fluida vs. posada/estruturada)

## 3. EXPRESSÃO E OLHAR
- Tipo de expressão (sorriso aberto com dentes, sorriso sutil/fechado, séria, confiante, provocativa)
- Direção do olhar (direto na câmera, lateral 45°, para baixo, distante, por cima do ombro)
- Energia/vibe (acessível/girl-next-door, sofisticada, divertida/playful, sensual sutil, casual relaxada)
- Intensidade do olhar (suave, magnético, descontraído)

## 4. CÂMERA E ENQUADRAMENTO
- Distância (full body dos pés à cabeça, 3/4 joelho para cima, cintura para cima, busto, close-up rosto)
- Ângulo vertical (nível dos olhos, levemente abaixo olhando para cima, de cima olhando para baixo)
- Ângulo horizontal (frontal, 3/4, perfil)
- Orientação (vertical/portrait 9:16, horizontal/landscape 16:9, quadrado 1:1)
- Regra de composição (centralizado, regra dos terços, off-center, espaço negativo)
- Lente aparente (wide-angle, 50mm equivalente, telefoto comprimida)
- Estimativa de abertura pelo bokeh (f/1.4 forte bokeh, f/2.8 moderado, f/5.6+ tudo em foco)

## 5. ILUMINAÇÃO
- Tipo principal (natural janela lateral, natural outdoor, ring light, softbox, flash direto, golden hour, neon)
- Direção da luz principal (frontal, lateral 45°, lateral 90°, contraluz, de cima, de baixo)
- Luz de preenchimento (presente/ausente, intensidade)
- Intensidade (suave/difusa envolvente, dura/contrastada com sombras definidas)
- Temperatura de cor (quente dourada ~3000K, neutra ~5500K, fria azulada ~7000K)
- Reflexos especculares visíveis (olhos, pele, cabelo, roupa)
- Ratio estimado (luz principal vs sombra)

## 6. CENÁRIO E AMBIENTE
- Local identificável (quarto, sala de estar, rua, calçada, loja, estúdio, praia, café, jardim)
- Tipo de background (limpo desfocado, bokeh urbano, parede lisa colorida, ambiente real com contexto)
- Elementos visuais no fundo (plantas, móveis, espelho, prateleiras, nenhum)
- Profundidade de campo aplicada ao cenário (forte bokeh f/1.4, moderado, tudo nítido)
- Paleta de cores do ambiente (tons quentes terrosos, neutros, pastel, vibrante urbano)
- Piso visível (tipo, cor)

## 7. STYLING E MODA
- Descrição da roupa principal (tipo, corte, fit: ajustado/oversized/regular)
- Como está vestida (com nó, manga dobrada, camisa aberta sobre top, tucked-in, untucked)
- Trail de tecido/caimento visível
- Acessórios visíveis com detalhe (brinco tipo/tamanho, colar, anel, óculos, bolsa modelo/cor, relógio)
- Calçado (tipo, cor, salto)
- Paleta de cores do look completo
- Makeup visível (natural no-makeup, glam, batom cor, sombra, blush)
- Unhas (cor, formato, se visíveis)

---

INSTRUÇÕES DE FORMATO:
1. Analise CADA imagem individualmente como "ref_1", "ref_2", etc.
2. Depois de todas as análises individuais, forneça uma SÍNTESE CONSOLIDADA 
   descrevendo o PADRÃO VISUAL COMUM — o que se repete entre as referências.
3. A síntese deve ser um PROMPT DESCRITIVO pronto para ser usado como referência 
   de geração de uma nova modelo fictícia que capture a essência do que foi analisado.
4. Responda em JSON com a seguinte estrutura:

```json
{
  "analises_individuais": [
    {
      "ref": "ref_1",
      "modelo": {...},
      "pose": {...},
      "expressao": {...},
      "camera": {...},
      "iluminacao": {...},
      "cenario": {...},
      "styling": {...}
    }
  ],
  "sintese_padrao_visual": {
    "modelo_tipica": "...",
    "pose_predominante": "...",
    "expressao_predominante": "...",
    "camera_predominante": "...",
    "iluminacao_predominante": "...",
    "cenario_predominante": "...",
    "styling_predominante": "..."
  },
  "prompt_gerador": "PROMPT LONGO E ULTRA-DETALHADO para gerar uma imagem fotorrealística. OBRIGATÓRIO seguir esta estrutura na ordem, SEM PULAR NENHUM item:\n    1. ABERTURA: tipo de foto, orientação, plataforma destino\n    2. ROSTO (OBRIGATÓRIO - mínimo 3 frases): formato do rosto, formato e cor dos olhos, distância entre olhos, formato do nariz, espessura e formato dos lábios, maçãs do rosto, linha do maxilar, sobrancelhas (espessura, arco, cor)\n    3. PELE (OBRIGATÓRIO - mínimo 2 frases): tom exato (subtom quente/frio/neutro), textura (porosa, lisa, aveludada), brilho natural, sardas/pintas se houver, nível de bronzeado\n    4. CABELO (OBRIGATÓRIO - mínimo 2 frases): textura do fio (liso/ondulado/cacheado/crespo), volume e densidade, comprimento exato, cor com nuances, brilho, como cai no rosto e ombros\n    5. CORPO (OBRIGATÓRIO - mínimo 2 frases): biotipo detalhado, proporção ombro-cintura-quadril, comprimento do torso vs pernas, definição muscular, altura aparente\n    6. POSE: posição do corpo, mãos, pernas, distribuição de peso, tensão muscular\n    7. EXPRESSÃO: tipo, direção do olhar, energia/vibe\n    8. ROUPA E STYLING: descrição completa do look\n    9. CÂMERA: lente, abertura, ângulo, composição\n    10. ILUMINAÇÃO: tipo, direção, temperatura, ratio\n    11. CENÁRIO: fundo, cores, elementos\n    O prompt deve ter NO MÍNIMO 200 palavras. Cada item acima deve ser uma frase completa, não apenas uma palavra-chave. Baseie-se na síntese das referências analisadas."
}
```

Seja CIRURGICAMENTE ESPECÍFICO — cada detalhe impacta diretamente a qualidade da geração final.
NÃO omita nenhum campo, mesmo que precise estimar.
"""


# ═══════════════════════════════════════════════════════════
# PRÉ-FILTRO: TRIAGEM RÁPIDA COM GEMINI FLASH
# ═══════════════════════════════════════════════════════════
PREFILTER_PROMPT = """Avalie esta imagem para uso como REFERÊNCIA VISUAL de moda e-commerce profissional.
Responda APENAS com um JSON no formato:
{"score": <1-10>, "motivo": "<razão curta>", "tem_texto": <true/false>, "rosto_visivel": <true/false>, "corpo_visivel": "<full/parcial/nao>", "tipo": "<editorial/lifestyle/selfie/produto/outro>"}

Critérios de pontuação (1=péssima, 10=perfeita):
- 9-10: Foto editorial/profissional ou lifestyle de alta qualidade. Modelo com rosto visível, corpo inteiro ou 3/4, sem texto, boa iluminação, enquadramento limpo
- 7-8: Foto boa, talvez com pequeno defeito (corte ligeiro, fundo distraído)
- 5-6: Qualidade média — selfie de espelho aceitável, ou rosto parcialmente visível
- 3-4: Selfie de espelho com celular cobrindo rosto, ou foto com texto moderado
- 1-2: Colagem, muito texto sobreposto, sem pessoa, ou imagem de produto sem modelo

BONIFICAÇÃO (score +2):
- Foto tirada por terceiro (não selfie)
- Iluminação profissional ou natural bem aproveitada
- Enquadramento editorial (regra dos terços, espaço negativo)

DESCLASSIFICAÇÃO IMEDIATA (score ≤ 2):
- Imagem com texto grande sobreposto (banners, promoções, títulos)
- Collage/mosaico de múltiplas fotos
- Imagem de produto sem modelo vestindo
- Captura de tela de rede social com interface visível
- Imagem de baixíssima resolução ou muito pixelada
"""


async def pre_filter_images(images: list[dict], keep: int = 5) -> list[dict]:
    """Filtra imagens usando Gemini Flash para manter só as melhores."""
    print(f"\n{'='*60}")
    print(f"🔬 ETAPA 1.5: PRÉ-FILTRO (Gemini Flash)")
    print(f"{'='*60}")
    print(f"   Candidatas: {len(images)}")
    print(f"   Manter: {keep} melhores\n")

    client = genai.Client(api_key=GEMINI_API_KEY)
    scored = []

    for img_data in images:
        try:
            pil_img = Image.open(img_data["path"])
            # Redimensionar para triagem rápida (512px max)
            max_dim = 512
            if max(pil_img.size) > max_dim:
                ratio = max_dim / max(pil_img.size)
                new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
                pil_img = pil_img.resize(new_size, Image.LANCZOS)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[PREFILTER_PROMPT, pil_img],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=256,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            # Extrair JSON da resposta (já deve vir puro com response_mime_type)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                score = result.get("score", 0)
                motivo = result.get("motivo", "?")
                tem_texto = result.get("tem_texto", False)
                rosto = result.get("rosto_visivel", False)
                corpo = result.get("corpo_visivel", "nao")
            else:
                score = 3
                motivo = "resposta sem JSON"
                tem_texto = True
                rosto = False
                corpo = "nao"

            emoji = "✅" if score >= 7 else "⚠️" if score >= 4 else "❌"
            print(f"   {emoji} ref_{img_data['index']}: {score}/10 | rosto={rosto} corpo={corpo} texto={tem_texto} | {motivo}")

            scored.append({
                **img_data,
                "filter_score": score,
                "filter_detail": {
                    "motivo": motivo,
                    "tem_texto": tem_texto,
                    "rosto_visivel": rosto,
                    "corpo_visivel": corpo,
                },
            })

        except Exception as e:
            print(f"   ⚠️  ref_{img_data['index']}: erro no filtro — {str(e)[:100]}")
            scored.append({**img_data, "filter_score": 0, "filter_detail": {"motivo": str(e)[:100]}})

    # Ordenar por score e manter as melhores
    scored.sort(key=lambda x: x["filter_score"], reverse=True)
    kept = scored[:keep]

    # Renomear arquivos para refletir a nova ordem (filtered_1, filtered_2...)
    final = []
    for i, img in enumerate(kept, 1):
        old_path = Path(img["path"])
        new_path = OUTPUT_DIR / f"filtered_{i}.jpg"
        # Copiar (não mover, manter original para debug)
        pil_img = Image.open(old_path)
        if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")
        pil_img.save(str(new_path), "JPEG", quality=90)
        final.append({**img, "path": str(new_path), "filtered_index": i})

    print(f"\n   📦 Selecionadas: {len(final)}/{len(images)} (score mínimo: {kept[-1]['filter_score'] if kept else 0}/10)")

    # Salvar relatório de filtragem
    filter_report = OUTPUT_DIR / "filter_report.json"
    filter_report.write_text(
        json.dumps([{"ref": s["index"], "score": s["filter_score"], **s.get("filter_detail", {})} for s in scored], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"   📄 Relatório: {filter_report.name}")

    return final


# ═══════════════════════════════════════════════════════════
# ETAPA 1: BUSCA VIA PLAYWRIGHT
# ═══════════════════════════════════════════════════════════
async def search_images(query: str, count: int = 15) -> list[dict]:
    """Busca imagens no Google Images via Playwright headless."""
    print(f"\n{'='*60}")
    print(f"🔍 ETAPA 1: BUSCA DE REFERÊNCIAS")
    print(f"{'='*60}")
    print(f"   Query: '{query}'")
    print(f"   Alvo:  {count} imagens\n")

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
        )
        page = await context.new_page()

        # ── Navegar para Google Images ──
        search_url = (
            f"https://www.google.com/search?q={quote(query)}"
            f"&tbm=isch&hl=pt-BR&gl=br"
        )
        print(f"   Navegando: {search_url[:80]}...")
        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # ── Lidar com dialogo de consentimento ──
        for selector in [
            'button:has-text("Aceitar tudo")',
            'button:has-text("Accept all")',
            'button:has-text("Concordo")',
            'button[id*="agree"]',
            'button[aria-label*="Accept"]',
        ]:
            try:
                btn = page.locator(selector)
                if await btn.count() > 0:
                    await btn.first.click()
                    print("   ✅ Dialog de consentimento aceito")
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                continue

        # ── Screenshot para debug ──
        debug_path = OUTPUT_DIR / "debug_search_page.png"
        await page.screenshot(path=str(debug_path), full_page=False)
        print(f"   📸 Screenshot salvo: {debug_path.name}")

        # ── Extrair URLs de imagens via JavaScript ──
        image_data = await page.evaluate("""
            () => {
                const results = [];
                // Tenta múltiplas estratégias para pegar URLs de imagem
                
                // Estratégia 1: thumbnails com data-src
                document.querySelectorAll('img[data-src]').forEach(img => {
                    const url = img.getAttribute('data-src');
                    if (url && url.startsWith('http') && !url.includes('google') && !url.includes('gstatic')) {
                        results.push({ url, strategy: 'data-src', w: img.naturalWidth, h: img.naturalHeight });
                    }
                });
                
                // Estratégia 2: img com src http direto
                document.querySelectorAll('img[src^="http"]').forEach(img => {
                    const url = img.src;
                    if (!url.includes('google') && !url.includes('gstatic') && !url.includes('youtube')) {
                        results.push({ url, strategy: 'src', w: img.naturalWidth, h: img.naturalHeight });
                    }
                });
                
                // Estratégia 3: extrair do atributo data-ou (original URL em Google Images)
                document.querySelectorAll('[data-ou]').forEach(el => {
                    const url = el.getAttribute('data-ou');
                    if (url && url.startsWith('http')) {
                        results.push({ url, strategy: 'data-ou', w: 0, h: 0 });
                    }
                });
                
                // Estratégia 4: links para imagens dentro de anchors
                document.querySelectorAll('a[href*="imgurl="]').forEach(a => {
                    const match = a.href.match(/imgurl=([^&]+)/);
                    if (match) {
                        results.push({ url: decodeURIComponent(match[1]), strategy: 'imgurl', w: 0, h: 0 });
                    }
                });
                
                // Deduplica por URL
                const seen = new Set();
                return results.filter(r => {
                    if (seen.has(r.url)) return false;
                    seen.add(r.url);
                    return true;
                });
            }
        """)

        print(f"   Encontradas {len(image_data)} URLs de imagem")
        for i, img in enumerate(image_data[:3]):
            print(f"   [{i}] {img['strategy']}: {img['url'][:80]}...")

        # ── Se Google Images falhou, tentar Pinterest ──
        if len(image_data) < 3:
            print(f"\n   ⚠️  Poucas imagens no Google. Tentando Pinterest...")
            pinterest_url = f"https://br.pinterest.com/search/pins/?q={quote(query)}"
            await page.goto(pinterest_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            # Screenshot debug Pinterest
            await page.screenshot(path=str(OUTPUT_DIR / "debug_pinterest.png"))

            pinterest_data = await page.evaluate("""
                () => {
                    const results = [];
                    document.querySelectorAll('img[src*="pinimg.com"]').forEach(img => {
                        let url = img.src;
                        // Trocar thumbnail por versão maior
                        url = url.replace(/\\/[0-9]+x\\//, '/736x/');
                        url = url.replace('/236x/', '/736x/');
                        results.push({ url, strategy: 'pinterest', w: img.naturalWidth, h: img.naturalHeight });
                    });
                    const seen = new Set();
                    return results.filter(r => {
                        if (seen.has(r.url)) return false;
                        seen.add(r.url);
                        return true;
                    });
                }
            """)
            image_data.extend(pinterest_data)
            print(f"   Pinterest: +{len(pinterest_data)} imagens encontradas")

        # ── Download das imagens ──
        print(f"\n   Baixando top {count} imagens...")
        downloaded = 0

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            for img_info in image_data:
                if downloaded >= count:
                    break

                url = img_info["url"]
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    content = resp.content
                    content_type = resp.headers.get("content-type", "")

                    # Verificar se é imagem válida com tamanho mínimo (10KB)
                    if len(content) < 10_000:
                        continue
                    if "image" not in content_type and not content[:4] in [
                        b"\xff\xd8\xff",  # JPEG
                        b"\x89PNG",       # PNG
                        b"GIF8",          # GIF
                        b"RIFF",          # WebP
                    ]:
                        continue

                    # Tentar abrir com PIL para validar
                    try:
                        pil_img = Image.open(io.BytesIO(content))
                        pil_img.verify()
                        # Reabrir após verify (verify invalida o objeto)
                        pil_img = Image.open(io.BytesIO(content))
                        w, h = pil_img.size
                        if w < 200 or h < 200:
                            continue
                    except Exception:
                        continue

                    downloaded += 1
                    img_path = OUTPUT_DIR / f"ref_{downloaded}.jpg"

                    # Converter para JPEG se necessário e salvar
                    pil_img = Image.open(io.BytesIO(content))
                    if pil_img.mode in ("RGBA", "P"):
                        pil_img = pil_img.convert("RGB")
                    pil_img.save(str(img_path), "JPEG", quality=90)

                    results.append({
                        "index": downloaded,
                        "path": str(img_path),
                        "url": url,
                        "size_kb": img_path.stat().st_size / 1024,
                        "dimensions": f"{w}x{h}",
                        "strategy": img_info["strategy"],
                    })
                    print(f"   ✅ ref_{downloaded}.jpg | {w}x{h} | {img_path.stat().st_size/1024:.0f}KB | via {img_info['strategy']}")

                except Exception as e:
                    continue

        await browser.close()

    print(f"\n   📦 Total baixado: {len(results)}/{count} imagens")
    return results


# ═══════════════════════════════════════════════════════════
# ETAPA 2: ANÁLISE COM GEMINI 2.5 PRO
# ═══════════════════════════════════════════════════════════
async def analyze_references(images: list[dict]) -> str:
    """Analisa referências visuais usando Gemini 2.5 Pro."""
    print(f"\n{'='*60}")
    print(f"🧠 ETAPA 2: ANÁLISE VISUAL (Gemini 2.5 Pro)")
    print(f"{'='*60}")
    print(f"   Modelo: {ANALYSIS_MODEL}")
    print(f"   Imagens: {len(images)}")
    print(f"   Prompt: {len(ANALYSIS_PROMPT)} chars\n")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Montar conteúdo: prompt + imagens
    contents = [ANALYSIS_PROMPT]
    for img_data in images:
        pil_img = Image.open(img_data["path"])
        # Redimensionar se muito grande (para não estourar tokens)
        max_dim = 1024
        if max(pil_img.size) > max_dim:
            ratio = max_dim / max(pil_img.size)
            new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
            pil_img = pil_img.resize(new_size, Image.LANCZOS)
        contents.append(pil_img)

    # Tentar com Pro primeiro, fallback para Flash se indisponível
    models_to_try = [ANALYSIS_MODEL, "gemini-2.5-flash"]
    response = None

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                print(f"   ⏳ Tentativa {attempt+1}/3 com {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=65536,
                    ),
                )
                print(f"   ✅ Resposta recebida de {model_name}!")
                break
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str or "overloaded" in err_str.lower():
                    wait = (attempt + 1) * 10
                    print(f"   ⚠️  {model_name} indisponível. Aguardando {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    print(f"   ❌ Erro inesperado: {err_str[:200]}")
                    break
        if response:
            break
        print(f"   ⚠️  {model_name} esgotou tentativas. Tentando próximo modelo...")

    if not response:
        print("   ❌ Todos os modelos falharam!")
        return ""

    analysis_text = response.text

    # Salvar análise bruta
    analysis_path = OUTPUT_DIR / "analysis_raw.md"
    analysis_path.write_text(analysis_text, encoding="utf-8")
    print(f"   ✅ Análise bruta salva: {analysis_path.name} ({len(analysis_text)} chars)")

    # Tentar extrair JSON da resposta
    json_match = re.search(r'```json\s*(.*?)\s*```', analysis_text, re.DOTALL)
    if json_match:
        try:
            analysis_json = json.loads(json_match.group(1))
            json_path = OUTPUT_DIR / "analysis.json"
            json_path.write_text(json.dumps(analysis_json, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"   ✅ JSON estruturado salvo: {json_path.name}")

            # Extrair e salvar o prompt gerador separadamente
            if "prompt_gerador" in analysis_json:
                prompt_path = OUTPUT_DIR / "prompt_gerador.txt"
                prompt_path.write_text(analysis_json["prompt_gerador"], encoding="utf-8")
                print(f"   ✅ Prompt gerador salvo: {prompt_path.name}")
        except json.JSONDecodeError:
            print(f"   ⚠️  JSON encontrado mas inválido. Usando texto bruto.")
    else:
        print(f"   ⚠️  Resposta não contém JSON. Verifique analysis_raw.md")

    return analysis_text


# ═══════════════════════════════════════════════════════════
# ETAPA 3: GERAÇÃO COM GEMINI 3.1 FLASH IMAGE (OPCIONAL)
# ═══════════════════════════════════════════════════════════
async def generate_image(analysis: str) -> Path | None:
    """Gera imagem baseada na análise visual."""
    print(f"\n{'='*60}")
    print(f"🎨 ETAPA 3: GERAÇÃO DE IMAGEM (Gemini 3.1 Flash Image)")
    print(f"{'='*60}")
    print(f"   Modelo: {GENERATION_MODEL}\n")

    # Extrair prompt_gerador do JSON se disponível
    prompt_section = analysis
    json_match = re.search(r'"prompt_gerador"\s*:\s*"(.*?)"', analysis, re.DOTALL)
    if json_match:
        prompt_section = json_match.group(1)
        print(f"   Usando prompt_gerador extraído ({len(prompt_section)} chars)")
    else:
        # Usar últimos 2000 chars como fallback (provavelmente contém a síntese)
        prompt_section = analysis[-2000:]
        print(f"   Usando síntese do final da análise (fallback)")

    generation_prompt = f"""Gere uma foto fotorrealista estilo selfie de espelho / outfit of the day para 
anúncio de e-commerce na Shopee Brasil.

A modelo deve ser uma mulher brasileira FICTÍCIA de 24 anos vestindo um vestido 
casual floral midi. NÃO reproduza nenhuma pessoa real.

Use EXATAMENTE este estilo visual como referência de pose, iluminação, 
enquadramento e vibe (extraído de análise de blogueiras brasileiras reais):

{prompt_section}

Requisitos técnicos:
- Foto vertical (9:16 ou 3:4)
- Resolução aparente de smartphone de alta qualidade
- Cores vibrantes e naturais
- Sem marca d'água, sem texto
- A roupa deve ser o foco principal
- Expressão natural e acessível
"""

    client = genai.Client(api_key=GEMINI_API_KEY)

    print("   ⏳ Gerando imagem (pode levar 10-20s)...")

    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=generation_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img_bytes = part.inline_data.data
                output_path = OUTPUT_DIR / "generated_result.png"
                
                # Salvar imagem
                pil_img = Image.open(io.BytesIO(img_bytes))
                pil_img.save(str(output_path), "PNG")
                
                print(f"   ✅ Imagem gerada: {output_path.name} ({pil_img.width}x{pil_img.height})")
                return output_path
            elif part.text:
                text_path = OUTPUT_DIR / "generation_response.txt"
                text_path.write_text(part.text, encoding="utf-8")
                print(f"   📝 Resposta de texto: {part.text[:300]}...")

    except Exception as e:
        print(f"   ❌ Erro na geração: {e}")
        error_path = OUTPUT_DIR / "generation_error.txt"
        error_path.write_text(str(e), encoding="utf-8")

    return None


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
async def main():
    parser = argparse.ArgumentParser(description="Pipeline Visual Search → Análise → Geração")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Query de busca")
    parser.add_argument("--count", type=int, default=REF_COUNT, help="Quantidade de referências finais")
    parser.add_argument("--pool", type=int, default=DOWNLOAD_POOL, help="Pool de download antes do filtro")
    parser.add_argument("--skip-generation", action="store_true", help="Pular etapa de geração")
    parser.add_argument("--skip-filter", action="store_true", help="Pular pré-filtro")
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 PIPELINE: Visual Search → Análise → Geração")
    print("=" * 60)
    print(f"   Query:     {args.query}")
    print(f"   Refs:      {args.count}")
    print(f"   Geração:   {'Sim' if not args.skip_generation else 'Não'}")
    print(f"   Output:    {OUTPUT_DIR}")
    print(f"   Análise:   {ANALYSIS_MODEL}")
    print(f"   Geração:   {GENERATION_MODEL}")

    if not GEMINI_API_KEY:
        print("\n❌ GOOGLE_AI_API_KEY não encontrado no .env!")
        sys.exit(1)

    # ── Etapa 1: Busca (pool grande) ──
    images = await search_images(args.query, args.pool)
    if not images:
        print("\n❌ Nenhuma imagem encontrada. Verifique debug_search_page.png")
        sys.exit(1)

    # ── Etapa 1.5: Pré-filtro (manter só as melhores) ──
    if not args.skip_filter:
        images = await pre_filter_images(images, keep=args.count)
        if not images:
            print("\n❌ Nenhuma imagem passou no filtro de qualidade!")
            sys.exit(1)

    # ── Etapa 2: Análise ──
    analysis = await analyze_references(images)

    # ── Preview da análise ──
    print(f"\n{'='*60}")
    print("📋 PREVIEW DA ANÁLISE:")
    print("=" * 60)
    # Mostrar primeiros 2000 chars
    preview = analysis[:2000]
    print(preview)
    if len(analysis) > 2000:
        print(f"\n... [truncado — total: {len(analysis)} chars]")
        print(f"    Veja completo em: output/analysis_raw.md")

    # ── Etapa 3: Geração (opcional) ──
    result_path = None
    if not args.skip_generation:
        result_path = await generate_image(analysis)

    # ── Resumo final ──
    print(f"\n{'='*60}")
    print("📁 ARQUIVOS GERADOS:")
    print("=" * 60)
    for f in sorted(OUTPUT_DIR.iterdir()):
        size = f.stat().st_size / 1024
        emoji = "🖼️" if f.suffix in (".jpg", ".png") else "📄"
        print(f"   {emoji} {f.name:<30} {size:>8.0f} KB")

    print(f"\n✅ Pipeline completo!")
    if result_path:
        print(f"   Resultado final: {result_path}")


if __name__ == "__main__":
    asyncio.run(main())
