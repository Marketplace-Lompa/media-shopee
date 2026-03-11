"""
Test: grounding focado em poses de produto
Verifica se Gemini retorna páginas de anúncio com fotos de modelo
e se o scraping extrai imagens utilizáveis.

Uso:
  python api/scripts/test_pose_grounding.py "blusa morcego"
  python api/scripts/test_pose_grounding.py "kimono cardigan"
"""
import sys
import os
import re
import requests
from io import BytesIO
from urllib.parse import urljoin, urlencode

# carrega .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google import genai
from google.genai import types
from PIL import Image

API_KEY = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌  GOOGLE_AI_API_KEY não encontrada no .env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-3-flash-preview"

GARMENT = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "blusa morcego listrada"
print(f"\n{'='*60}")
print(f"TESTE DE POSE GROUNDING: '{GARMENT}'")
print(f"{'='*60}\n")

# ── 1. Query focada em poses de anúncio ──────────────────────────
pose_prompt = (
    f"I need to find real product listing photos showing a model wearing: {GARMENT}.\n\n"
    "Use Google Search to find e-commerce product pages (Shopee, Mercado Livre, "
    "fashion retail sites, lookbook pages) that show a model wearing this type of garment.\n\n"
    "Focus on finding pages with:\n"
    "- Real model photos from product listings\n"
    "- Multiple pose angles (front, side, back)\n"
    "- Professional e-commerce photography\n\n"
    "Return a brief description of the best pose angles and styling you found. "
    "Do NOT use markdown."
)

print("📡 Chamando Gemini com query de poses...")
response = client.models.generate_content(
    model=MODEL,
    contents=pose_prompt,
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=512,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
)

# ── 2. Inspecionar metadata ──────────────────────────────────────
print("\n📊 METADATA:")
sources = []
queries = []
try:
    candidate = response.candidates[0]
    gm = getattr(candidate, "grounding_metadata", None)
    print(f"  Metadata present: {gm is not None}")
    if gm:
        queries = list(getattr(gm, "web_search_queries", None) or [])
        print(f"  Queries feitas ({len(queries)}):")
        for q in queries:
            print(f"    · {q}")
        chunks = getattr(gm, "grounding_chunks", None) or []
        print(f"  Sources ({len(chunks)}):")
        for i, chunk in enumerate(chunks[:8]):
            web = getattr(chunk, "web", None)
            if web:
                title = getattr(web, "title", "?")
                uri = getattr(web, "uri", "?")
                sources.append({"title": title, "uri": uri})
                print(f"    [{i+1}] {title}")
                print(f"         {uri[:100]}...")
except Exception as e:
    print(f"  ⚠️  Erro ao ler metadata: {e}")

# ── 3. Texto sintetizado ─────────────────────────────────────────
text = ""
try:
    for part in (response.parts or []):
        if hasattr(part, "text") and part.text:
            text += part.text
except Exception:
    pass
text = text.strip()
print(f"\n📝 TEXTO RETORNADO ({len(text)} chars):")
print(text[:600] + ("..." if len(text) > 600 else ""))

# ── 4. Tentar raspar imagens das fontes ─────────────────────────
print(f"\n🖼️  TENTANDO RASPAR IMAGENS ({len(sources)} sources)...")

def _is_useful(url: str) -> bool:
    low = url.lower()
    blocked = ("logo", "icon", "avatar", "sprite", "placeholder", "thumb", "banner", "ad", "pixel")
    if any(t in low for t in blocked):
        return False
    return (
        low.endswith((".jpg", ".jpeg", ".png", ".webp")) or
        "image" in low or "img" in low
    )

def _scrape_image_urls(page_url: str, limit: int = 15) -> list[str]:
    try:
        r = requests.get(page_url, timeout=10, headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        })
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print(f"    ⚠️  Falha ao acessar página: {e}")
        return []

    # Extrai src e srcset de tags <img>
    found = []
    seen = set()
    for m in re.finditer(r'<img[^>]+>', html, re.IGNORECASE):
        tag = m.group(0)
        for attr in ("src", "data-src", "data-lazy-src"):
            val_m = re.search(rf'{attr}=["\']([^"\']+)["\']', tag, re.IGNORECASE)
            if val_m:
                u = val_m.group(1).strip()
                if u.startswith("//"):
                    u = "https:" + u
                elif u.startswith("/"):
                    u = urljoin(page_url, u)
                if u not in seen and u.startswith("http"):
                    seen.add(u)
                    found.append(u)
        if len(found) >= limit:
            break
    return found

def _try_download(url: str) -> tuple[bool, str]:
    """Retorna (sucesso, motivo_falha)"""
    try:
        r = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (compatible)"
        })
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "image" not in ctype:
            return False, f"Content-Type={ctype}"
        data = r.content
        if len(data) < 18_000:
            return False, f"muito pequena ({len(data)}b)"
        if len(data) > 6_000_000:
            return False, f"muito grande ({len(data)//1024}kb)"
        with Image.open(BytesIO(data)) as img:
            w, h = img.size
            if min(w, h) < 320:
                return False, f"resolução baixa ({w}x{h})"
            ratio = h / w if w > 0 else 0
            portrait = ratio >= 1.2
            print(f"      → {w}x{h} {'[RETRATO ✓]' if portrait else '[PAISAGEM]'} {len(data)//1024}kb")
        return True, "ok"
    except Exception as e:
        return False, str(e)

total_downloaded = 0
for i, src in enumerate(sources[:4]):
    uri = src["uri"]
    title = src["title"]
    print(f"\n  Source [{i+1}]: {title}")
    print(f"  URL: {uri[:80]}...")

    img_urls = _scrape_image_urls(uri, limit=20)
    useful = [u for u in img_urls if _is_useful(u)]
    print(f"  → {len(img_urls)} imagens encontradas, {len(useful)} parecem úteis")

    downloaded = 0
    for url in useful[:10]:
        ok, reason = _try_download(url)
        if ok:
            downloaded += 1
            total_downloaded += 1
            if downloaded >= 3:
                break
        # else: silent skip

    print(f"  ✅ {downloaded} imagens baixadas com sucesso" if downloaded else "  ❌ Nenhuma imagem aproveitável")

# ── 5. Resumo ────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("RESUMO DO TESTE:")
print(f"  Queries geradas:      {len(queries)}")
print(f"  Sources retornados:   {len(sources)}")
print(f"  Imagens aproveitáveis: {total_downloaded}")
print()
if total_downloaded >= 2:
    print("✅ VIÁVEL: grounding retorna imagens utilizáveis como referência de pose")
elif total_downloaded == 1:
    print("⚠️  PARCIAL: apenas 1 imagem — fontes não ideais para poses")
elif sources:
    print("❌ FONTES OK mas scraping falhou (bot protection / JS rendering)")
else:
    print("❌ SEM FONTES: Gemini não retornou sources de e-commerce")
print(f"{'='*60}\n")
