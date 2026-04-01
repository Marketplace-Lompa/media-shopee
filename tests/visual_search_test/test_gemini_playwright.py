"""
Teste Agentic: Gemini + Playwright Headless
─────────────────────────────────────────────
Fluxo:
  1. Gemini gera queries otimizadas pra Pinterest e Instagram
  2. Playwright navega, fecha modais, extrai pins/posts
  3. Baixa 5 imagens reais de cada plataforma
  4. Gemini analisa as imagens baixadas e gera insights visuais
"""
import asyncio
import urllib.request
import json
import os
import sys
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

OUTPUT_DIR = Path(__file__).parent / "output_agentic"
IMAGES_DIR = OUTPUT_DIR / "images"
OUTPUT_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

API_KEY = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ GOOGLE_AI_API_KEY não encontrada no .env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)


def extract_json(text: str) -> dict:
    """Extrai JSON de resposta que pode conter markdown."""
    clean = text
    if "```json" in clean:
        clean = clean.split("```json")[1].split("```")[0]
    elif "```" in clean:
        clean = clean.split("```")[1].split("```")[0]
    return json.loads(clean.strip())


def save_json(data, filename):
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  💾 {path.name}")
    return path


# ═══════════════════════════════════════════════════════════
# FASE 1 — GEMINI GERA QUERIES
# ═══════════════════════════════════════════════════════════

def fase_1_gerar_queries():
    """Gemini gera queries otimizadas para Pinterest e Instagram."""
    print("\n" + "=" * 60)
    print("🧠 FASE 1: GEMINI → Gerar queries de busca")
    print("=" * 60)

    prompt = """Você é um trend scout de moda feminina brasileira para e-commerce.

Gere queries de busca otimizadas para encontrar referências visuais de moda casual feminina brasileira.

Para PINTEREST (busca pública, sem login):
- Gere 3 queries em português que retornem pins com fotos de modelos brasileiras usando roupas casuais
- Foque em: looks reais, street style brasileiro, e-commerce fashion
- Use termos que o Pinterest indexa bem

Para INSTAGRAM (perfis públicos de marcas):
- Liste 3 perfis de marcas brasileiras de moda feminina acessível/casual que tenham fotos de produto de alta qualidade
- Foque em marcas que vendem em marketplaces (Shopee, ML) ou fast fashion
- NÃO liste influencers pessoais — apenas @marcas com muitas fotos de produto

RESPONDA em JSON:
{
  "pinterest_queries": ["query1", "query2", "query3"],
  "instagram_profiles": [
    {"handle": "@marca", "motivo": "por que essa marca é relevante"}
  ]
}"""

    print("  Pedindo queries ao Gemini...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            max_output_tokens=4096,
            temperature=0.7,
        ),
    )

    data = extract_json(response.text)
    save_json(data, "fase1_queries.json")

    print(f"  📌 Pinterest queries: {data.get('pinterest_queries', [])}")
    print(f"  📷 Instagram profiles: {[p['handle'] for p in data.get('instagram_profiles', [])]}")

    return data


# ═══════════════════════════════════════════════════════════
# FASE 2 — PLAYWRIGHT NAVEGA E EXTRAI
# ═══════════════════════════════════════════════════════════

async def dismiss_pinterest_modal(page):
    """Fecha modal de login do Pinterest."""
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
    except:
        pass
    try:
        await page.evaluate("""
            () => {
                document.querySelectorAll('[data-test-id="loginForm"], [role="dialog"], .Modal, .Closeup').forEach(el => el.remove());
                document.querySelectorAll('[data-test-id="modal-overlay"], .OverlayBackground').forEach(el => el.remove());
                document.querySelectorAll('div[style*="position: fixed"]').forEach(el => {
                    if (el.textContent.includes('login') || el.textContent.includes('Entrar') || el.textContent.includes('Criar conta') || el.textContent.includes('Email')) {
                        el.remove();
                    }
                });
                document.body.style.overflow = 'auto';
            }
        """)
        await page.wait_for_timeout(300)
    except:
        pass


async def dismiss_instagram_modal(page):
    """Fecha modal de login/cadastro do Instagram."""
    try:
        close_btn = await page.query_selector('[aria-label="Fechar"], [aria-label="Close"]')
        if close_btn:
            await close_btn.click()
            await page.wait_for_timeout(300)
    except:
        pass
    try:
        await page.evaluate("""
            () => {
                document.querySelectorAll('[role="dialog"], [role="presentation"]').forEach(el => {
                    if (el.textContent.includes('Cadastre-se') || el.textContent.includes('Entrar') || el.textContent.includes('login')) {
                        el.remove();
                    }
                });
                document.querySelectorAll('div[style*="position: fixed"]').forEach(el => el.remove());
                document.body.style.overflow = 'auto';
            }
        """)
        await page.wait_for_timeout(300)
    except:
        pass


async def extrair_pinterest(page, queries: list) -> list:
    """Navega no Pinterest e extrai imagens."""
    print("\n  🔴 PINTEREST — Extraindo...")
    all_images = []

    for i, query in enumerate(queries):
        print(f"    🔍 [{i+1}/{len(queries)}] '{query}'")
        try:
            url = f"https://br.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(2000)
            await dismiss_pinterest_modal(page)

            # Screenshot limpo
            ss_path = str(OUTPUT_DIR / f"pinterest_{i+1}.png")
            await page.screenshot(path=ss_path, full_page=False)

            # Extrai imagens via JS (sem filtro restritivo)
            images = await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img[src*="pinimg"]');
                    return Array.from(imgs).slice(0, 20).map(img => ({
                        src: img.src,
                        alt: img.alt || '',
                        width: img.naturalWidth,
                        height: img.naturalHeight
                    }));
                }
            """)

            # Converte pra resolução original
            for img in images:
                img["src_original"] = img["src"].replace("/236x/", "/originals/").replace("/564x/", "/originals/")
                img["query"] = query
                img["plataforma"] = "pinterest"

            all_images.extend(images)
            print(f"      ✅ {len(images)} imagens extraídas")

        except Exception as e:
            print(f"      ❌ Erro: {e}")

    return all_images


async def extrair_instagram(page, profiles: list) -> list:
    """Navega em perfis do Instagram e extrai imagens."""
    print("\n  📷 INSTAGRAM — Extraindo...")
    all_images = []

    for i, profile in enumerate(profiles):
        handle = profile.get("handle", "").lstrip("@")
        print(f"    👤 [{i+1}/{len(profiles)}] @{handle}")
        try:
            url = f"https://www.instagram.com/{handle}/"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)
            await dismiss_instagram_modal(page)

            # Screenshot limpo
            ss_path = str(OUTPUT_DIR / f"instagram_{i+1}.png")
            await page.screenshot(path=ss_path, full_page=False)

            # Verifica redirecionamento pra login
            if "accounts/login" in page.url:
                print(f"      ⚠️ Redirecionou pro login, tentando voltar...")
                # Tenta navegar direto sem trailing slash
                await page.goto(f"https://www.instagram.com/{handle}", wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)
                await dismiss_instagram_modal(page)
                if "accounts/login" in page.url:
                    print(f"      ❌ Login obrigatório")
                    # Mesmo com login wall, tenta extrair OG meta tags
                    ss_path2 = str(OUTPUT_DIR / f"instagram_{i+1}.png")
                    await page.screenshot(path=ss_path2, full_page=False)

            # Extrai imagens do grid
            images = await page.evaluate("""
                () => {
                    const data = {};
                    // Meta tags
                    const ogDesc = document.querySelector('meta[property="og:description"]');
                    data.og_description = ogDesc ? ogDesc.content : '';
                    
                    // Imagens do grid (excluindo profile pic e ícones)
                    const imgs = document.querySelectorAll('img');
                    data.images = Array.from(imgs)
                        .filter(img => {
                            const src = img.src || '';
                            return (src.includes('instagram') || src.includes('cdninstagram') || src.includes('fbcdn'))
                                && img.naturalWidth > 150
                                && !src.includes('profile')
                                && !src.includes('s150x150');
                        })
                        .slice(0, 15)
                        .map(img => ({
                            src: img.src,
                            alt: img.alt || '',
                            width: img.naturalWidth,
                            height: img.naturalHeight
                        }));
                    
                    return data;
                }
            """)

            profile_images = images.get("images", [])
            for img in profile_images:
                img["handle"] = handle
                img["plataforma"] = "instagram"
                img["og_description"] = images.get("og_description", "")

            all_images.extend(profile_images)
            print(f"      ✅ {len(profile_images)} imagens | OG: {images.get('og_description', '')[:80]}...")

        except Exception as e:
            print(f"      ❌ Erro: {e}")

    return all_images


async def fase_2_playwright(queries: dict):
    """Fase 2 — Playwright navega Pinterest + Instagram."""
    print("\n" + "=" * 60)
    print("🌐 FASE 2: PLAYWRIGHT → Navegar e extrair")
    print("=" * 60)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = await context.new_page()

        # Pinterest
        pinterest_queries = queries.get("pinterest_queries", [])
        pinterest_images = await extrair_pinterest(page, pinterest_queries)

        await browser.close()

    # Instagram em contexto SEPARADO (evita cookies do Pinterest)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = await context.new_page()

        instagram_profiles = queries.get("instagram_profiles", [])
        instagram_images = await extrair_instagram(page, instagram_profiles)

        await browser.close()

    result = {
        "pinterest": {"total": len(pinterest_images), "images": pinterest_images},
        "instagram": {"total": len(instagram_images), "images": instagram_images},
    }
    save_json(result, "fase2_extracao.json")

    return result


# ═══════════════════════════════════════════════════════════
# FASE 3 — DOWNLOAD DAS TOP 5 IMAGENS
# ═══════════════════════════════════════════════════════════

def download_image(url: str, filepath: str) -> bool:
    """Baixa uma imagem via urllib."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Referer": "https://www.pinterest.com/",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if len(content) > 5000:
                with open(filepath, "wb") as f:
                    f.write(content)
                return True
    except Exception as e:
        print(f"      ⚠️ Falha download: {e}")
    return False


async def fase_3_download(extracao: dict):
    """Baixa as top 5 imagens de cada plataforma."""
    print("\n" + "=" * 60)
    print("⬇️  FASE 3: DOWNLOAD → Top 5 imagens de cada plataforma")
    print("=" * 60)

    downloaded = {"pinterest": [], "instagram": []}

    if True:  # block scope (replaced aiohttp session)
        # Pinterest — top 5 com alt text mais rico
        pin_images = extracao["pinterest"]["images"]
        pin_sorted = sorted(pin_images, key=lambda x: len(x.get("alt", "")), reverse=True)
        pin_top = pin_sorted[:5]

        print(f"\n  📌 Pinterest — baixando {len(pin_top)} imagens...")
        for i, img in enumerate(pin_top):
            url = img.get("src_original") or img.get("src", "")
            if not url:
                continue
            ext = "jpg"
            filepath = str(IMAGES_DIR / f"pinterest_{i+1}.{ext}")
            ok = download_image(url, filepath)
            if ok:
                downloaded["pinterest"].append({
                    "file": filepath,
                    "alt": img.get("alt", ""),
                    "query": img.get("query", ""),
                    "src": url,
                })
                size_kb = os.path.getsize(filepath) / 1024
                print(f"    ✅ pinterest_{i+1}.jpg ({size_kb:.0f}KB) — {img.get('alt', '')[:60]}...")
            else:
                # Tenta URL menor se original falhou
                fallback = img.get("src", "")
                if fallback and fallback != url:
                    ok = download_image(fallback, filepath)
                    if ok:
                        downloaded["pinterest"].append({
                            "file": filepath,
                            "alt": img.get("alt", ""),
                            "query": img.get("query", ""),
                            "src": fallback,
                        })
                        size_kb = os.path.getsize(filepath) / 1024
                        print(f"    ✅ pinterest_{i+1}.jpg (fallback, {size_kb:.0f}KB)")

        # Instagram — top 5
        insta_images = extracao["instagram"]["images"]
        insta_sorted = sorted(insta_images, key=lambda x: x.get("width", 0), reverse=True)
        insta_top = insta_sorted[:5]

        print(f"\n  📷 Instagram — baixando {len(insta_top)} imagens...")
        for i, img in enumerate(insta_top):
            url = img.get("src", "")
            if not url:
                continue
            filepath = str(IMAGES_DIR / f"instagram_{i+1}.jpg")
            ok = download_image(url, filepath)
            if ok:
                downloaded["instagram"].append({
                    "file": filepath,
                    "alt": img.get("alt", ""),
                    "handle": img.get("handle", ""),
                    "src": url,
                })
                size_kb = os.path.getsize(filepath) / 1024
                print(f"    ✅ instagram_{i+1}.jpg ({size_kb:.0f}KB) — @{img.get('handle', '')}")
            else:
                print(f"    ❌ instagram_{i+1}.jpg — falhou")

    save_json(downloaded, "fase3_downloaded.json")
    total = len(downloaded["pinterest"]) + len(downloaded["instagram"])
    print(f"\n  📊 Total baixado: {total} imagens ({len(downloaded['pinterest'])} pin + {len(downloaded['instagram'])} insta)")

    return downloaded


# ═══════════════════════════════════════════════════════════
# FASE 4 — GEMINI ANALISA AS IMAGENS
# ═══════════════════════════════════════════════════════════

def fase_4_analise(downloaded: dict):
    """Gemini analisa as imagens baixadas e gera insights visuais."""
    print("\n" + "=" * 60)
    print("🧠 FASE 4: GEMINI → Analisar imagens baixadas")
    print("=" * 60)

    # Prepara imagens pra enviar ao Gemini
    parts = []
    image_meta = []

    all_files = downloaded.get("pinterest", []) + downloaded.get("instagram", [])
    
    if not all_files:
        print("  ⚠️ Nenhuma imagem baixada pra analisar")
        return {"erro": "sem imagens"}

    for item in all_files:
        filepath = item.get("file", "")
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    img_bytes = f.read()
                parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                plataforma = "Pinterest" if "pinterest" in filepath else "Instagram"
                parts.append(types.Part.from_text(
                    text=f"[{plataforma}] Alt: {item.get('alt', 'sem descrição')[:100]}"
                ))
                image_meta.append(item)
            except Exception as e:
                print(f"  ⚠️ Erro lendo {filepath}: {e}")

    if not parts:
        print("  ⚠️ Nenhuma imagem válida pra enviar ao Gemini")
        return {"erro": "sem imagens válidas"}

    print(f"  📤 Enviando {len(image_meta)} imagens ao Gemini...")

    analysis_prompt = """Você é um diretor de arte de moda brasileira para e-commerce.

Analise TODAS as imagens que recebeu. Elas são referências visuais reais extraídas do Pinterest e Instagram de marcas brasileiras.

Para CADA imagem, extraia:
1. Tipo da foto (produto, lookbook, lifestyle, street style)
2. Descrição da modelo (biotipo, idade aparente, tom de pele, cabelo)
3. Roupa e styling (peças, cores, fit, acessórios)
4. Pose e expressão
5. Iluminação (tipo, direção, temperatura)
6. Cenário/fundo
7. Qualidade comercial (nota 1-10 pra conversão em e-commerce)

Depois, gere uma SÍNTESE consolidada com:
- Padrões visuais dominantes
- Persona-modelo ideal (síntese de todas as referências)
- Recomendações de estética para e-commerce brasileiro

RESPONDA em JSON:
{
  "analise_individual": [
    {
      "imagem": "pinterest_1 ou instagram_1",
      "tipo_foto": "...",
      "modelo": "...",
      "roupa": "...",
      "pose": "...",
      "iluminacao": "...",
      "cenario": "...",
      "nota_comercial": 8
    }
  ],
  "sintese": {
    "padroes_dominantes": "...",
    "persona_ideal": "...",
    "recomendacoes_ecommerce": "..."
  },
  "prompt_gerador": "PROMPT EM INGLÊS, 250+ palavras, para gerar a foto ideal baseada nessas referências. Sem nomes fictícios."
}"""

    parts.append(types.Part.from_text(text=analysis_prompt))

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=types.Content(parts=parts),
            config=types.GenerateContentConfig(
                max_output_tokens=16384,
                temperature=0.7,
            ),
        )

        raw = response.text
        (OUTPUT_DIR / "fase4_analise_raw.md").write_text(raw, encoding="utf-8")

        try:
            analysis = extract_json(raw)
            save_json(analysis, "fase4_analise.json")

            # Salva prompt final
            prompt_final = analysis.get("prompt_gerador", "")
            if prompt_final:
                (OUTPUT_DIR / "prompt_final.txt").write_text(prompt_final, encoding="utf-8")
                print(f"  🎯 Prompt final: {len(prompt_final)} chars, ~{len(prompt_final.split())} palavras")

            n_analises = len(analysis.get("analise_individual", []))
            print(f"  📊 {n_analises} imagens analisadas")
            print(f"  🧬 Síntese gerada com sucesso")

            return analysis
        except json.JSONDecodeError:
            print("  ⚠️ Falha parse JSON — texto bruto salvo")
            return {"raw": raw}

    except Exception as e:
        print(f"  ❌ Erro Gemini: {e}")
        return {"erro": str(e)}


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

async def main():
    import traceback
    start = time.time()

    print("=" * 60)
    print("🚀 PIPELINE AGENTIC: Gemini + Playwright Headless")
    print("=" * 60)
    print(f"   Fase 1: Gemini gera queries (Flash + Grounding)")
    print(f"   Fase 2: Playwright navega Pinterest + Instagram")
    print(f"   Fase 3: Download top 5 imagens de cada")
    print(f"   Fase 4: Gemini analisa imagens (Flash + Vision)")
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Início: {datetime.now().strftime('%H:%M:%S')}")

    try:
        # Fase 1 — Gemini gera queries (usa cache se disponível)
        cache_path = OUTPUT_DIR / "fase1_queries.json"
        if cache_path.exists():
            print("\n  ♻️  Fase 1: Usando queries cacheadas de fase1_queries.json")
            queries = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"  📌 Pinterest queries: {queries.get('pinterest_queries', [])}")
            profiles = queries.get('instagram_profiles', [])
            handles = [p['handle'] if isinstance(p, dict) else p for p in profiles]
            print(f"  📷 Instagram profiles: {handles}")
        else:
            queries = fase_1_gerar_queries()

        # Fase 2 — Playwright navega e extrai
        extracao = await fase_2_playwright(queries)

        # Fase 3 — Download das imagens
        downloaded = await fase_3_download(extracao)

        # Fase 4 — Gemini analisa
        analysis = fase_4_analise(downloaded)

        elapsed = time.time() - start

        print("\n" + "=" * 60)
        print(f"✅ PIPELINE COMPLETO em {elapsed:.0f}s")
        print("=" * 60)

        # Mostra prompt final
        prompt_path = OUTPUT_DIR / "prompt_final.txt"
        if prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8")
            print(f"\n{'─' * 60}")
            print("🎯 PROMPT FINAL:")
            print(f"{'─' * 60}")
            print(prompt[:800] + "..." if len(prompt) > 800 else prompt)
            print(f"\n📏 Total: {len(prompt)} chars, ~{len(prompt.split())} palavras")

        # Lista imagens baixadas
        imgs = list(IMAGES_DIR.glob("*.jpg"))
        if imgs:
            print(f"\n📁 {len(imgs)} imagens em: {IMAGES_DIR}/")
            for img in sorted(imgs):
                size = img.stat().st_size / 1024
                print(f"   {img.name} ({size:.0f}KB)")

        print(f"\n📁 Artefatos em: {OUTPUT_DIR}/")

    except Exception as e:
        print(f"\n💥 ERRO FATAL: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
