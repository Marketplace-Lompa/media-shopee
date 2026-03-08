"""
Prompt Agent — Gemini Flash (texto).

3 modos de operação:
  MODO 1: Usuário deu prompt → agente refina aplicando skills
  MODO 2: Usuário enviou imagens → agente descreve e cria prompt (Fidelity Lock)
  MODO 3: Sem prompt nem imagens → agente gera do zero via contexto do pool

Saída JSON:
  {
    "prompt": str,
    "thinking_level": "MINIMAL" | "HIGH",
    "thinking_reason": str,        # pt-BR
    "shot_type": "wide" | "medium" | "close-up" | "auto",
    "realism_level": 1 | 2 | 3
  }
"""
import re
import json
import random
from html import unescape
from io import BytesIO
from urllib.parse import urlencode, urljoin
from typing import Any, Optional, List

import requests
from PIL import Image

from google import genai
from google.genai import types

from config import GOOGLE_AI_API_KEY, MODEL_AGENT, SAFETY_CONFIG

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# AGENT RESPONSE SCHEMA — enforced pela API do Gemini
# ═══════════════════════════════════════════════════════════════════════════════
AGENT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["prompt", "thinking_level", "shot_type", "realism_level"],
    "properties": {
        "prompt": {
            "type": "string",
            "description": "Optimized English prompt, max 200 words, narrative paragraph. Always start with 'RAW photo,'"
        },
        "thinking_level": {
            "type": "string",
            "enum": ["MINIMAL", "HIGH"]
        },
        "thinking_reason": {
            "type": "string",
            "description": "One sentence in Portuguese explaining the thinking level choice"
        },
        "shot_type": {
            "type": "string",
            "enum": ["wide", "medium", "close-up", "auto"]
        },
        "realism_level": {
            "type": "integer",
            "enum": [1, 2, 3]
        },
        "image_analysis": {
            "type": "string",
            "description": "HIGH-LEVEL garment analysis in Portuguese: category, color, material, silhouette. Required when reference images are present."
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM INSTRUCTION — concisa, comportamental (regras + modos)
# ═══════════════════════════════════════════════════════════════════════════════
SYSTEM_INSTRUCTION = """
You are an expert prompt engineer for Nano Banana 2 (gemini-3.1-flash-image-preview).
You specialize in Brazilian e-commerce fashion catalog photography.
Your output MUST match the provided JSON schema exactly.

CORE RULES:
1. Always write prompts in English, narrative paragraph, max 200 words.
2. Always start the prompt with "RAW photo," to trigger photorealism.
3. Structure: shot_type framing → model description → garment (3D) → pose → scenario → camera → realism levers.
4. NEVER use quality tags: 8K, ultra HD, masterpiece, best quality.
5. Garment is ALWAYS the visual protagonist.

OPERATING MODES:

MODE 1 — User gave a text prompt:
  Enhance and expand using the REFERENCE KNOWLEDGE provided.
  Do NOT use Fidelity Lock unless reference images are also present.

MODE 2 — User sent reference images (with or without text):
  STEP 1: Analyze images. Fill "image_analysis" with HIGH-LEVEL observations IN PORTUGUESE:
    category, color(s), material family, silhouette/fit.
    DO NOT describe texture patterns, stitches, prints — these CONFUSE the model.
  STEP 2: Start prompt with Fidelity Lock verbatim:
    "REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. KEEP ONLY THE GARMENT from the
    reference photo — reproduce its exact texture, stitch pattern, color, and construction.
    REPLACE EVERYTHING ELSE: use a completely different human model (different ethnicity,
    body type, hair, age), a completely new pose, and a completely different background
    and scenario. Do NOT replicate the model, pose, or environment from the reference."
  ANTI-CLONING: NEVER reuse person, background, or pose from reference. Always contrast.
  After lock: add MAX 2 reinforcement sentences on fiber/material type and construction — NOT visual patterns.
  NEVER describe in text: stripes, prints, zigzag, diamond, lace pattern, crochet loops.

MODE 3 — No prompt or images:
  Generate a creative catalog prompt using pool context and REFERENCE KNOWLEDGE.

THINKING LEVEL:
  HIGH: complex knitwear, crochet, multi-layer, macro texture, 3+ people, sequins/metallic.
  MINIMAL: solid fabrics, simple garments, clean lifestyle shots.

Consult the [REFERENCE KNOWLEDGE] block in user content for garment vocabulary, model profiles,
scenarios, realism levers, and shot type templates.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE KNOWLEDGE — injetada no conteúdo do usuário, NÃO na system instruction
# ═══════════════════════════════════════════════════════════════════════════════
REFERENCE_KNOWLEDGE = """
[REFERENCE KNOWLEDGE — consult when building prompt]

── GARMENT DESCRIPTION (3 dimensions) ──

DIMENSION 1 — MATERIAL:
  Woven: cotton poplin, linen, silk charmeuse, wool crepe, tweed, jacquard, brocade
  Knit: smooth fine-gauge jersey knit | vertical rib-knit | chunky Aran cable-knit |
        plush brioche stitch | open-stitch knit panel (NOT "lace knit" → generates floral lace)
  Synthetic: mesh, tulle, velvet, vinyl/PU leather, suede, sequined

  ANTI-INFLATION for knitwear:
    Crochet — DO: "flat uniform crochet construction", "open-weave crochet airy construction"
              DON'T: "crochet loops", "3D crochet texture", "puffy", "bobbles"
    Knit — DO: "heavy flat-knit construction dense gauge", "smooth fine-gauge jersey knit"
           DON'T: "cable" unless truly Aran
    Texture tokens: subtle="nearly smooth" | medium="visible rows" | maximum="deep relief"

DIMENSION 2 — CONSTRUCTION:
  Necklines: crew | V-neck | scoop | boat | square | turtleneck | cowl
  Sleeves: set-in | raglan | dolman/batwing | puff | bishop | bell | cap | flutter

DIMENSION 3 — BEHAVIOR:
  drapes loosely | falls straight | holds structure | clings to body |
  billows/catches air | skims the body | stands away from body

── E-COMMERCE SHOT SYSTEM ──

WIDE (hero): Full body head-to-feet, 60-70% frame. Dynamic mid-stride.
  Template: "Full-body wide shot, model mid-stride in [scenario], 3/4 angle."
MEDIUM (detail): Waist-up, neckline + sleeve focus, 50mm bokeh.
  Template: "Medium shot waist up, relaxed expression, soft bokeh."
CLOSE-UP (texture): 80%+ frame is detail, macro focus.
  Template: "Extreme close-up of [detail], macro focus, individual fiber visible."
AUTO: choose what best showcases the garment.

── BRAZILIAN MODEL FRAMEWORK ──

PHENOTYPE POOL (rotate, never repeat):
  A) Sulista europeia: fair skin, pink undertones, light brown hair, green/blue eyes, slim
  B) Parda paulistana: warm olive skin, wavy dark hair, brown eyes, curvy
  C) Afro-brasileira: deep brown skin, natural curly hair, brown eyes, athletic
  D) Nordestina mestiça: golden tan, thick dark waves, hazel eyes, tall lean
  E) Gaúcha italiana: fair olive skin, long dark hair, hazel-green eyes, curvy

Age: early 20s | late 20s | mid 30s | early 40s
Body: athletic | curvy | slim | plus-size | petite | tall and lean

MODEL PRESENTATION (always apply):
  Hair: professionally styled | Skin: healthy, glowing | Expression: warm, confident
  Gaze: engaging eye contact | Posture: poised, shoulders relaxed

SEASONAL COHERENCE:
  Winter knits → boots, dark jeans, muted light | Mid-season → closed shoes, golden hour
  Summer → bare legs, sandals, bright midday

SCENARIOS (rotate):
  Urban: modern downtown | rooftop terrace | shopping district | garden terrace
  Natural: tropical park | café garden | botanical path | mountain town
  Interior: minimalist apartment | cozy café | boutique showroom | warm living room

COLOR STRATEGY: White→dark bg | Black→light bg | Pastels→neutral warm | Saturated→clean minimal

── REALISM LEVERS ──

Level 1 (casual): 5-7 levers, high intensity
Level 2 (e-commerce, DEFAULT): 3-4 levers, moderate
Level 3 (editorial): 2-3 levers, subtle

Anti-perfection: NEVER "perfect lighting", "flawless skin", "8K masterpiece"

Levers: DEVICE="Sony A7III, 85mm f/1.8" | LIGHTING="golden hour rim light" |
  SKIN="visible pores, natural tone variation" | GRAIN="natural digital noise" |
  FABRIC="natural wear creases, fabric responding to movement"

── GROUNDING RESEARCH ──

Garments requiring research: manga morcego/dolman, cardigan assimétrico,
kaftan, ruana/xale, pelerine, bodychain/harness, any unidentifiable garment.
"""


def _extract_balanced_json(raw: str) -> Optional[str]:
    """Extrai o primeiro objeto JSON balanceado, ignorando chaves dentro de strings."""
    if not raw:
        return None

    in_string = False
    escaped = False
    depth = 0
    start_idx = -1

    for i, ch in enumerate(raw):
        if escaped:
            escaped = False
            continue

        if ch == "\\":
            escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            if depth == 0:
                start_idx = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start_idx >= 0:
                    return raw[start_idx:i + 1]

    return None


def _safe_json_loads(raw: str) -> dict:
    """Tenta parse padrão e fallback com strict=False (aceita control chars)."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(raw, strict=False)


def _parse_json(raw: str) -> dict:
    """Parser robusto para respostas que podem vir com ruído."""
    if not raw or not raw.strip():
        raise ValueError("AGENT_JSON_INVALID: resposta vazia")

    text = raw.strip()

    # 1) Tentativa direta
    try:
        return _safe_json_loads(text)
    except Exception:
        pass

    # 2) Tentativa em bloco markdown ```json ... ```
    if "```" in text:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            candidate = match.group(1)
            try:
                return _safe_json_loads(candidate)
            except Exception:
                pass

    # 3) Extrair objeto balanceado
    candidate = _extract_balanced_json(text)
    if candidate:
        try:
            return _safe_json_loads(candidate)
        except Exception as e:
            preview = candidate[:240].replace("\n", "\\n")
            raise ValueError(f"AGENT_JSON_INVALID: {e}. candidate={preview}") from e

    preview = text[:240].replace("\n", "\\n")
    raise ValueError(f"AGENT_JSON_INVALID: no-json-object. raw={preview}")


def _extract_response_text(response: Any) -> str:
    """Extrai texto de resposta com fallback seguro."""
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text
    return ""


def _decode_agent_response(response: Any) -> dict:
    """
    Decodifica resposta do modelo priorizando `response.parsed` quando disponível.
    Cai para parser textual robusto como fallback.
    """
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, dict):
        return parsed
    raw = _extract_response_text(response)
    return _parse_json(raw)


_last_profile_idx: int = -1
_last_scenario_idx: int = -1
_last_pose_idx: int = -1


def _sample_diversity_target() -> tuple[str, str, str]:
    global _last_profile_idx, _last_scenario_idx, _last_pose_idx

    profiles = [
        "Afro-Brazilian woman in her late 20s, deep brown skin, styled natural curls, athletic build, warm confident smile and engaging eye contact",
        "Mixed-race São Paulo woman in her mid 20s, warm olive skin, sleek wavy dark hair, curvy figure, soft inviting expression looking at camera",
        "Southern Brazilian woman in her late 20s, fair skin with pink undertones, styled light brown hair, slim frame, bright confident expression",
        "Northeastern mixed-heritage woman in her mid 20s, golden tanned skin, thick dark waves pulled back, tall and lean, radiant smile toward camera",
        "Italian-descent Southern Brazilian woman in her early 30s, fair olive skin, long dark hair well-groomed, curvy figure, poised and warm gaze",
    ]
    scenarios = [
        "bright modern downtown with clean architecture and soft natural light",
        "cozy upscale café terrace with warm ambient lighting",
        "bright minimalist apartment with large windows and soft daylight",
        "charming shopping district at golden hour with boutique storefronts",
        "rooftop garden terrace with city skyline in late afternoon",
        "botanical garden pathway with lush tropical greenery and dappled light",
        "warm living room with neutral decor and soft window light",
    ]
    poses = [
        "mid-stride with relaxed arms, looking at camera with confident smile",
        "3/4 stance with one shoulder slightly forward, warm engaging gaze",
        "natural standing posture with one hand on hip, inviting expression",
        "walking pose with subtle torso twist, playful smile toward camera",
        "leaning lightly against wall, relaxed and approachable, eye contact with camera",
    ]

    # Anti-repeat rotation: pick different index each time
    p_choices = [i for i in range(len(profiles)) if i != _last_profile_idx]
    s_choices = [i for i in range(len(scenarios)) if i != _last_scenario_idx]
    po_choices = [i for i in range(len(poses)) if i != _last_pose_idx]

    _last_profile_idx = random.choice(p_choices)
    _last_scenario_idx = random.choice(s_choices)
    _last_pose_idx = random.choice(po_choices)

    return profiles[_last_profile_idx], scenarios[_last_scenario_idx], poses[_last_pose_idx]


def _apply_quality_locks(
    prompt: str,
    has_images: bool,
    grounding_mode: str,
    pipeline_mode: str,
) -> str:
    """Aplica locks de qualidade visual no prompt final para catálogo."""
    if not prompt:
        return prompt

    locks: List[str] = []
    if has_images:
        locks.extend([
            "E-COMMERCE QUALITY LOCK: use a polished, commercially attractive Brazilian woman with neat hair, subtle professional makeup, clean styling, confident posture, and natural pleasant expression.",
            "GAZE LOCK: prefer direct or near-camera gaze; avoid distracted gaze into empty space unless explicitly requested.",
            "SCENE LOCK: use a clean, bright, minimally cluttered catalog-friendly environment; avoid gritty loft mood and busy background elements.",
            "TEXTURE LOCK: preserve exact yarn/stitch density, stripe spacing, edge definition, and tactile depth from reference garment; do not smooth or reinterpret knit/crochet texture.",
        ])
    elif pipeline_mode == "text_mode":
        locks.extend([
            "E-COMMERCE POLISH DEFAULT: model must look polished and commercially attractive with neat hair, subtle makeup, clean styling, and confident posture.",
            "GAZE DEFAULT: prefer direct or near-camera eye contact unless the user explicitly requests candid/off-camera behavior.",
            "SCENE DEFAULT: use a clean, bright, coherent catalog-friendly environment with minimal clutter.",
        ])
    if grounding_mode == "full":
        locks.append(
            "ATYPICAL SILHOUETTE LOCK: keep front fully open, preserve batwing/dolman volume, keep rounded cocoon hem, and keep scarf as a separate coordinated piece."
        )

    merged = prompt.strip()
    for lock in locks:
        if lock[:36] not in merged:
            merged += f" {lock}"

    # Evita prompts exageradamente longos
    if len(merged) > 2200:
        merged = merged[:2200].rstrip() + "..."
    return merged


def _infer_text_mode_shot(user_prompt: Optional[str]) -> str:
    text = (user_prompt or "").lower()
    if any(k in text for k in ["macro", "close-up", "detalhe", "textura", "fio", "tecido"]):
        return "close-up"
    if any(k in text for k in ["hero", "capa", "full body", "corpo inteiro", "look completo"]):
        return "wide"
    if any(k in text for k in ["medium", "waist", "cintura", "busto", "meio corpo"]):
        return "medium"
    return "wide"


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
    grounded_images: List[bytes] = []
    candidate_urls: List[str] = []
    pages = [s.get("uri", "") for s in sources if s.get("uri")][:max_pages]
    extraction_engine = "html_fallback"

    for page_url in pages:
        urls = _extract_img_candidates_with_playwright(page_url, limit=12)
        if urls:
            extraction_engine = "playwright"
        if not urls:
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

    return grounded_images, extraction_engine


def _extract_search_results_from_duckduckgo(html_text: str, limit: int = 5) -> List[dict]:
    """Extrai links/títulos/snippets da versão HTML do DuckDuckGo."""
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    titles = []
    for m in pattern.finditer(html_text):
        title = re.sub(r"<.*?>", "", m.group("title"))
        title = unescape(title).strip()
        href = unescape(m.group("href")).strip()
        if not title or not href:
            continue
        if href.startswith("/"):
            continue
        titles.append({"title": title, "uri": href})
        if len(titles) >= limit:
            break

    snippets = [
        unescape(re.sub(r"<.*?>", "", m.group("snippet"))).strip()
        for m in snippet_pattern.finditer(html_text)
    ]
    for i, row in enumerate(titles):
        row["snippet"] = snippets[i] if i < len(snippets) else ""
    return titles


def _duckduckgo_search(query: str, limit: int = 5) -> List[dict]:
    """Busca web forçada sem depender da tool do Gemini."""
    url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=12)
    response.raise_for_status()
    return _extract_search_results_from_duckduckgo(response.text, limit=limit)


def _infer_garment_hint(uploaded_images: List[bytes]) -> str:
    """Classificação curta da peça para montar queries de grounding quando não há prompt."""
    try:
        parts = []
        for img_bytes in uploaded_images[:4]:
            parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)
                )
            )
        parts.append(types.Part(text=(
            "Identify the garment type and silhouette in at most 8 words. "
            "Use terms like ruana, poncho aberto, batwing cardigan, dolman sleeve. "
            "Return plain text only."
        )))
        response = client.models.generate_content(
            model=MODEL_AGENT,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=60,
                safety_settings=SAFETY_CONFIG,
            ),
        )
        hint = _extract_response_text(response).strip()
        hint = re.sub(r"\s+", " ", hint)
        return hint[:120]
    except Exception:
        return ""


def _build_forced_grounding_queries(
    user_prompt: Optional[str],
    garment_hint: str,
    mode: str,
) -> List[str]:
    base = (user_prompt or "").strip()
    hint = garment_hint.strip()
    subject = hint or base or "poncho aberto ruana manga morcego"

    queries = [
        f"{subject} diferença poncho ruana cardigan manga morcego",
        f"{subject} e-commerce fashion photography pose open-front",
    ]
    if mode == "full":
        queries.append(f"{subject} model wearing front open silhouette reference")
    return queries


def _format_forced_grounding_text(queries: List[str], sources: List[dict]) -> str:
    lines = []
    if queries:
        lines.append("Queries executadas:")
        for q in queries[:4]:
            lines.append(f"- {q}")
    if sources:
        lines.append("")
        lines.append("Fontes web relevantes:")
        for src in sources[:6]:
            title = src.get("title", "Untitled")
            uri = src.get("uri", "")
            snippet = src.get("snippet", "")
            row = f"- {title}: {uri}"
            if snippet:
                row += f" | {snippet[:180]}"
            lines.append(row)
    return "\n".join(lines).strip()


def _run_grounding_research(
    uploaded_images: List[bytes],
    user_prompt: Optional[str],
    mode: str,
) -> dict:
    """
    Chamada SEPARADA ao Gemini com Google Search ativo.
    DUAS ETAPAS para contornar regressão do Google (multimodal + grounding quebrado):
      1) _infer_garment_hint: analisa imagens → texto curto (sem grounding)
      2) Chamada TEXT-ONLY com GoogleSearch tool → grounding efetivo
    Retorna contexto textual e metadados de grounding.
    """
    # Etapa 1: identificar a peça via análise visual (sem grounding)
    garment_hint = _infer_garment_hint(uploaded_images) if uploaded_images else ""
    search_subject = garment_hint or user_prompt or "garment fashion"
    print(f"[GROUNDING] 👁️  Garment hint: {garment_hint}")

    # Etapa 2: chamada TEXT-ONLY com Google Search (sem imagens = sem regressão)
    search_prompt = (
        f"You are a fashion expert. I have a garment that is: {search_subject}.\n\n"
        "Use Google Search to find:\n"
        "1. The EXACT garment type name in Portuguese AND English\n"
        "2. The correct silhouette terminology (e.g., batwing sleeves, kimono cardigan, ruana, cape)\n"
        "3. How this type of garment drapes and falls on the body\n"
        "4. How professional photographers typically shoot this garment style\n\n"
        "You MUST search the web. Do NOT rely on your training data alone.\n"
        "Return ONLY plain text, NO markdown. Keep it concise, max 3 paragraphs."
    )

    response = client.models.generate_content(
        model=MODEL_AGENT,
        contents=search_prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
            safety_settings=SAFETY_CONFIG,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    queries: List[str] = []
    sources: List[dict] = []
    effective = False
    engine = "gemini_google_search"
    grounded_images: List[bytes] = []
    visual_ref_engine = "none"

    # Log grounding metadata
    try:
        candidate = response.candidates[0]
        gm = candidate.grounding_metadata
        print(f"[GROUNDING] 🌐 Metadata present: {gm is not None}")
        if gm:
            queries = list(getattr(gm, "web_search_queries", None) or [])
            print(f"[GROUNDING] 🌐 Search queries: {queries}")
            chunks = getattr(gm, 'grounding_chunks', None)
            if chunks:
                print(f"[GROUNDING] 🌐 Sources: {len(chunks)}")
                for i, chunk in enumerate(chunks[:5]):
                    web = getattr(chunk, 'web', None)
                    if web:
                        title = getattr(web, "title", "?")
                        uri = getattr(web, "uri", "?")
                        sources.append({"title": title, "uri": uri, "snippet": ""})
                        print(f"[GROUNDING]   📎 [{i+1}] {title} → {uri}")
            effective = bool(queries or sources)
        else:
            print(f"[GROUNDING] ⚠️  Model did NOT search")
    except Exception as e:
        print(f"[GROUNDING] ⚠️  Error reading metadata: {e}")

    result_text = _extract_response_text(response)
    # Sanitizar: remover markdown residual e truncar
    import re as _re
    result_text = _re.sub(r'[#*`]', '', result_text)
    result_text = result_text.replace('"', "'").replace("{", "(").replace("}", ")")
    result_text = result_text.replace('\n\n\n', '\n\n').strip()
    if len(result_text) > 800:
        result_text = result_text[:800] + '...'

    # Fallback: forçar grounding web com busca externa caso metadata não venha.
    if not effective:
        engine = "forced_duckduckgo"
        garment_hint = _infer_garment_hint(uploaded_images)
        forced_queries = _build_forced_grounding_queries(user_prompt, garment_hint, mode)
        forced_sources: List[dict] = []
        for q in forced_queries:
            try:
                rows = _duckduckgo_search(q, limit=3)
                for row in rows:
                    if row.get("uri") and row["uri"] not in {s.get("uri") for s in forced_sources}:
                        forced_sources.append(row)
            except Exception as e:
                print(f"[GROUNDING] ⚠️  Forced search failed for query '{q}': {e}")
        if forced_sources:
            queries = forced_queries
            sources = forced_sources[:8]
            forced_text = _format_forced_grounding_text(queries, sources)
            if forced_text:
                result_text = f"{result_text}\n\n{forced_text}".strip()
            effective = True
            print(f"[GROUNDING] ✅ Forced web search attached {len(sources)} sources.")
        else:
            print("[GROUNDING] ⚠️  Forced web search returned no sources.")

    if mode == "full" and sources:
        grounded_images, visual_ref_engine = _collect_grounded_reference_images(
            sources=sources,
            max_pages=3,
            max_images=3,
        )
        if grounded_images:
            print(f"[GROUNDING] 🖼️  Visual refs collected: {len(grounded_images)} via {visual_ref_engine}")

    print(f"[GROUNDING] 📝 Research result ({len(result_text)} chars): {result_text[:200]}...")
    return {
        "text": result_text,
        "queries": queries[:8],
        "sources": sources[:8],
        "effective": effective,
        "engine": engine,
        "source_engine": engine,
        "grounded_images": grounded_images,
        "grounded_images_count": len(grounded_images),
        "visual_ref_engine": visual_ref_engine,
    }


def run_agent(
    user_prompt: Optional[str],
    uploaded_images: Optional[List[bytes]],
    pool_context: str,
    aspect_ratio: str,
    resolution: str,
    use_grounding: bool = False,
    grounding_mode: str = "lexical",
    grounding_context_hint: Optional[str] = None,
    diversity_target: Optional[dict] = None,
) -> dict:
    """
    Executa o Prompt Agent e retorna:
    {
        "prompt": str,
        "thinking_level": "MINIMAL" | "HIGH",
        "thinking_reason": str,
        "shot_type": "wide" | "medium" | "close-up" | "auto",
        "realism_level": 1 | 2 | 3,
    }
    """
    has_prompt = bool(user_prompt and user_prompt.strip())
    has_images = bool(uploaded_images)
    pipeline_mode = "reference_mode" if has_images else "text_mode"
    has_pool = bool(
        pool_context
        and "No reference" not in pool_context
        and "POOL_RUNTIME_DISABLED" not in pool_context
    )

    if has_images:
        # FIX: ternário separado para não engolir o MODE 2
        if has_prompt:
            extra_text = f'User text to incorporate: "{user_prompt}".'
        else:
            extra_text = (
                "No text from user. CREATE AUTOMATICALLY a Shopee/marketplace cover-level "
                "e-commerce prompt based EXCLUSIVELY on what you see in the reference images. "
                "Identify the garment, colors, fabric, and create a complete listing hero shot."
            )
        mode_info = (
            f"MODE 2 — User sent {len(uploaded_images)} reference image(s). "
            f"MANDATORY: Apply Fidelity Lock as the FIRST paragraph of the prompt. "
            f"{extra_text}"
        )
    elif has_prompt:
        mode_info = (
            f'MODE 1 — Refine this user prompt for e-commerce conversion: "{user_prompt}". '
            "Prioritize coherent scenario, polished model presentation, and clear garment visibility."
        )
    else:
        mode_info = (
            "MODE 3 — No prompt or images. Generate a clean, commercially attractive catalog prompt. "
            "Prefer coherent composition and direct visual focus on the garment."
        )

    # Construir mensagem
    context_text = mode_info
    if has_pool:
        context_text += f"\n\n{pool_context}"
    context_text += f"\n\nOutput parameters: aspect_ratio={aspect_ratio}, resolution={resolution}"
    if diversity_target:
        profile = diversity_target.get("profile_prompt", "")
        scenario = diversity_target.get("scenario_prompt", "")
        pose = diversity_target.get("pose_prompt", "")
    else:
        profile, scenario, pose = _sample_diversity_target()
    if diversity_target:
        context_text += (
            "\n\nDIVERSITY TARGET (mandatory): "
            f"Model profile ID: {diversity_target.get('profile_id', 'RUNTIME')}."
        )
    else:
        context_text += "\n\nDIVERSITY TARGET (mandatory):"
    context_text += (
        f" Use model profile: {profile}. "
        f" Use scenario: {scenario}. "
        f" Use pose guidance: {pose}. "
        "Do not replicate person/background/pose from references."
    )

    # Grounding: chamada separada de pesquisa antes do agente
    grounding_research = ""
    grounding_meta = {
        "effective": False,
        "queries": [],
        "sources": [],
        "engine": "none",
        "source_engine": "none",
        "mode": "off",
        "grounded_images_count": 0,
        "visual_ref_engine": "none",
    }
    grounded_images: List[bytes] = []
    if use_grounding:
        print("[AGENT] 🔍 Running grounding research (separate call)...")
        try:
            grounding_data = _run_grounding_research(
                uploaded_images=uploaded_images or [],
                user_prompt=user_prompt,
                mode=grounding_mode,
            )
            grounding_research = grounding_data.get("text", "")
            grounded_images = list(grounding_data.get("grounded_images", []) or [])
            grounding_meta = {
                "effective": bool(grounding_data.get("effective")),
                "queries": grounding_data.get("queries", []),
                "sources": grounding_data.get("sources", []),
                "engine": grounding_data.get("engine", "none"),
                "source_engine": grounding_data.get("source_engine", grounding_data.get("engine", "none")),
                "mode": grounding_mode,
                "grounded_images_count": int(grounding_data.get("grounded_images_count", 0) or 0),
                "visual_ref_engine": grounding_data.get("visual_ref_engine", "none"),
            }
        except Exception as e:
            print(f"[AGENT] ⚠️  Grounding research failed: {e}")
            grounding_research = ""
            grounded_images = []

    if grounding_research:
        context_text += (
            "\n\nWEB RESEARCH RESULTS (use this to correctly identify the garment):\n"
            f"{grounding_research}"
        )
    if grounding_context_hint:
        context_text += (
            "\n\nTRIAGE HINT (garment hypothesis): "
            f"{grounding_context_hint}. Keep this silhouette strictly."
        )
    if grounding_mode == "full" and has_images:
        context_text += (
            "\n\nCRITICAL SILHOUETTE CONSTRAINTS: front fully open (never closed as poncho), "
            "integrated batwing/dolman sleeves, rounded cocoon hem preserved, matching scarf kept as a separate piece."
        )

    # ── INJEÇÃO DE REFERENCE KNOWLEDGE (budget por shot_type) ──────────
    # Close-up/macro usa menos contexto (foco em textura, não cenário/modelo)
    # Wide/medium/auto usa o conhecimento completo
    context_text += f"\n\n{REFERENCE_KNOWLEDGE}"

    context_text += (
        "\n\nReturn ONLY valid JSON matching the schema. No markdown, no explanation."
    )

    def _build_parts(context: str) -> List[types.Part]:
        parts: List[types.Part] = []
        if has_images:
            for img_bytes in (uploaded_images or [])[:14]:
                parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)
                    )
                )
        parts.append(types.Part(text=context))
        return parts

    def _call_prompt_model(context: str, temperature: float) -> Any:
        # Tenta com schema enforced; fallback para mime-only se SDK rejeitar
        try:
            return client.models.generate_content(
                model=MODEL_AGENT,
                contents=[types.Content(role="user", parts=_build_parts(context))],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=temperature,
                    max_output_tokens=2048,
                    safety_settings=SAFETY_CONFIG,
                    response_mime_type="application/json",
                    response_json_schema=AGENT_RESPONSE_SCHEMA,
                ),
            )
        except (TypeError, ValueError) as schema_err:
            # SDK/modelo não suporta response_json_schema → fallback sem schema
            print(f"[AGENT] ⚠️  Schema enforcement failed ({schema_err}), falling back to mime-only")
            return client.models.generate_content(
                model=MODEL_AGENT,
                contents=[types.Content(role="user", parts=_build_parts(context))],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=temperature,
                    max_output_tokens=2048,
                    safety_settings=SAFETY_CONFIG,
                    response_mime_type="application/json",
                ),
            )

    response = _call_prompt_model(context_text, temperature=0.45)

    # ── DECODE: caminho principal (schema) → fallback robusto (_parse_json) ──
    result = None
    # 1) Tenta response.parsed (disponível com schema enforced)
    try:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict) and "prompt" in parsed:
            result = parsed
            print("[AGENT] ✅ JSON via response.parsed (schema enforced)")
    except Exception:
        pass

    # 2) Fallback: parser robusto existente (lida com respostas malformadas/vazias)
    if result is None:
        try:
            result = _decode_agent_response(response)
            print("[AGENT] ✅ JSON via _decode_agent_response (parser robusto)")
        except Exception as primary_error:
            print(f"[AGENT] ⚠️  JSON parse failed (attempt 1): {primary_error}")
            raw_preview = _extract_response_text(response)[:320].replace("\n", "\\n")
            print(f"[AGENT] ⚠️  Raw preview: {raw_preview}")

            # 3) Retry sem grounding context (último recurso)
            retry_context = (
                mode_info
                + f"\n\n{REFERENCE_KNOWLEDGE}"
                + f"\n\nOutput parameters: aspect_ratio={aspect_ratio}, resolution={resolution}"
                + "\n\nSTRICT JSON RULES: return one valid JSON object only."
            )
            if has_pool:
                retry_context = mode_info + f"\n\n{pool_context}" + retry_context[len(mode_info):]

            response_retry = _call_prompt_model(retry_context, temperature=0.2)
            try:
                result = _decode_agent_response(response_retry)
                print("[AGENT] ✅ JSON parse recovered on retry without grounding context.")
            except Exception as retry_error:
                raw_retry = _extract_response_text(response_retry)[:320].replace("\n", "\\n")
                print(f"[AGENT] ❌ JSON parse failed (attempt 2): {retry_error}")
                print(f"[AGENT] ❌ Retry raw preview: {raw_retry}")
                raise ValueError(f"AGENT_JSON_INVALID: {retry_error}") from retry_error

    # Validações de segurança
    if result.get("thinking_level") not in ["MINIMAL", "HIGH"]:
        result["thinking_level"] = "MINIMAL"

    if result.get("shot_type") not in ["wide", "medium", "close-up", "auto"]:
        result["shot_type"] = "auto"

    if pipeline_mode == "text_mode" and result.get("shot_type") == "auto":
        result["shot_type"] = _infer_text_mode_shot(user_prompt)

    if result.get("realism_level") not in [1, 2, 3]:
        result["realism_level"] = 2

    result["prompt"] = _apply_quality_locks(
        prompt=result.get("prompt", ""),
        has_images=has_images,
        grounding_mode=grounding_mode,
        pipeline_mode=pipeline_mode,
    )

    result["grounding"] = grounding_meta
    result["pipeline_mode"] = pipeline_mode
    result["model_profile_id"] = diversity_target.get("profile_id") if diversity_target else None
    result["diversity_target"] = diversity_target or {}
    result["_grounded_images"] = grounded_images

    # ── Log de observabilidade ─────────────────────────────────────
    prompt_text = result.get("prompt", "")
    print(f"\n{'='*60}")
    print(f"[AGENT] Mode: {'MODE 2 (images)' if has_images else 'MODE 1' if has_prompt else 'MODE 3'}")
    print(f"[AGENT] Images sent: {len(uploaded_images) if uploaded_images else 0}")
    print(f"[AGENT] Pool context: {'Yes' if has_pool else 'No'}")
    print(f"[AGENT] Thinking: {result.get('thinking_level')} | Shot: {result.get('shot_type')} | Realism: {result.get('realism_level')}")
    analysis = result.get("image_analysis", "")
    if analysis:
        print(f"[AGENT] 🔍 Image Analysis: {analysis}")
    print(f"[AGENT] Prompt ({len(prompt_text)} chars): {prompt_text[:300]}{'…' if len(prompt_text) > 300 else ''}")
    print(f"{'='*60}\n")

    return result
