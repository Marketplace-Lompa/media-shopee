import re
import requests
from typing import List, Optional
from urllib.parse import urljoin
from io import BytesIO
import os

from PIL import Image

_GROUNDING_VISUAL_ENGINE = os.environ.get("GROUNDING_VISUAL_IMAGES", "off").strip().lower()

def _extract_img_candidates_from_html(page_url: str, html_text: str, limit: int = 16) -> List[str]:
    urls: List[str] = []
    seen = set()

    direct_pattern = re.compile(
        r'<img[^>]+(?:src|data-src|data-original|data-lazy-src)=["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    srcset_pattern = re.compile(
        r'<img[^>]+srcset=["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    def _push(url: str):
        if not url:
            return
        u = url.strip()
        if not u or u.startswith("data:"):
            return
        if u.startswith("//"):
            u = f"https:{u}"
        elif u.startswith("/"):
            u = urljoin(page_url, u)
        elif not u.startswith("http://") and not u.startswith("https://"):
            u = urljoin(page_url, u)
        if u in seen:
            return
        seen.add(u)
        urls.append(u)

    for match in direct_pattern.finditer(html_text):
        _push(match.group(1))
        if len(urls) >= limit:
            return urls

    for match in srcset_pattern.finditer(html_text):
        candidates = [c.strip() for c in match.group(1).split(",")]
        for candidate in candidates:
            _push(candidate.split(" ")[0])
            if len(urls) >= limit:
                return urls

    return urls

def _extract_img_candidates_with_playwright(page_url: str, limit: int = 16) -> List[str]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return []

    urls: List[str] = []
    seen = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(page_url, timeout=6000, wait_until="domcontentloaded")
            rows = page.eval_on_selector_all(
                "img",
                "els => els.map(el => ({src: el.getAttribute('src') || '', srcset: el.getAttribute('srcset') || ''}))",
            )
            browser.close()

        def _push(url: str):
            if not url:
                return
            u = url.strip()
            if not u or u.startswith("data:"):
                return
            if u.startswith("//"):
                u = f"https:{u}"
            elif u.startswith("/"):
                u = urljoin(page_url, u)
            elif not u.startswith("http://") and not u.startswith("https://"):
                u = urljoin(page_url, u)
            if u in seen:
                return
            seen.add(u)
            urls.append(u)

        for row in rows:
            _push(row.get("src", ""))
            srcset = row.get("srcset", "")
            if srcset:
                for candidate in srcset.split(","):
                    _push(candidate.strip().split(" ")[0])
            if len(urls) >= limit:
                break
    except Exception:
        return []
    return urls[:limit]

def _is_probably_useful_image(url: str) -> bool:
    low = url.lower()
    blocked_tokens = ("logo", "icon", "avatar", "sprite", "placeholder", "thumb")
    if any(token in low for token in blocked_tokens):
        return False
    return low.endswith((".jpg", ".jpeg", ".png", ".webp", ".avif")) or "image" in low or "img" in low

def _download_image_bytes(url: str, timeout: int = 8) -> Optional[bytes]:
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        })
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "image" not in ctype:
            return None
        data = r.content
        if len(data) < 18_000 or len(data) > 6_000_000:
            return None
        with Image.open(BytesIO(data)) as img:
            w, h = img.size
            if min(w, h) < 320:
                return None
        return data
    except Exception:
        return None

def _collect_grounded_reference_images(
    sources: List[dict],
    max_pages: int = 3,
    max_images: int = 3,
) -> tuple[List[bytes], str]:
    """
    Coleta imagens de referência das fontes do grounding.

    Engine controlada por GROUNDING_VISUAL_IMAGES (env):
      off        (padrão) → retorna vazio; sem I/O de rede para imagens
      html       → requests leve; sem Chromium
      playwright → Playwright sync + fallback html (comportamento original)
    """
    engine = _GROUNDING_VISUAL_ENGINE  # "off" | "html" | "playwright"

    if engine == "off":
        print(f"[GROUNDING] 🖼️  Visual image collection: disabled (GROUNDING_VISUAL_IMAGES=off)")
        return [], "visual_disabled"

    grounded_images: List[bytes] = []
    candidate_urls: List[str] = []
    pages = [s.get("uri", "") for s in sources if s.get("uri")][:max_pages]
    extraction_engine = "html_scrape"

    for page_url in pages:
        urls: List[str] = []

        if engine == "playwright":
            urls = _extract_img_candidates_with_playwright(page_url, limit=12)
            if urls:
                extraction_engine = "playwright"

        if not urls:
            # Fonte leve: requests + regex (sem Chromium)
            try:
                html = requests.get(page_url, timeout=8).text
                urls = _extract_img_candidates_from_html(page_url, html, limit=12)
            except Exception:
                urls = []

        for url in urls:
            if _is_probably_useful_image(url) and url not in candidate_urls:
                candidate_urls.append(url)
        if len(candidate_urls) >= 36:
            break

    for image_url in candidate_urls:
        img_bytes = _download_image_bytes(image_url, timeout=8)
        if not img_bytes:
            continue
        grounded_images.append(img_bytes)
        if len(grounded_images) >= max_images:
            break

    print(f"[GROUNDING] 🖼️  Visual image collection: engine={extraction_engine}, found={len(grounded_images)}")
    return grounded_images, extraction_engine
