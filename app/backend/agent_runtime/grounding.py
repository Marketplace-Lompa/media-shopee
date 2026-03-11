import re
import math
import json
from urllib.parse import urlencode
from html import unescape
from typing import List, Optional, Any

import requests
from google import genai
from google.genai import types

from agent_runtime.constants import _POSE_KEYWORDS
from agent_runtime.parser import _extract_response_text
from agent_runtime.structural import _neg_to_pos

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


def _extract_pose_clause(grounding_text: str) -> str:
    """Extrai 1 instrução de pose compacta e direta do texto de grounding.

    Pontua sentenças por densidade de palavras-chave de pose e retorna a melhor,
    já convertida para linguagem fotográfica positiva do Imagen (máx 25 palavras).
    """
    sentences = re.split(r'(?<=[.!?\n])\s+', grounding_text)
    best = ""
    best_score = 0
    for sent in sentences:
        words = sent.lower().split()
        if not (5 <= len(words) <= 50):
            continue
        score = sum(1 for w in words if w.rstrip("s,.:") in _POSE_KEYWORDS)
        if score > best_score:
            best_score = score
            best = sent.strip()

    if not best or best_score < 2:
        return ""

    # Comprimir para ≤ 25 palavras e limpar resíduos
    words = best.split()
    if len(words) > 25:
        best = " ".join(words[:25])

    # Garantir linguagem positiva (sem "avoid", "don't", etc.)
    best = _neg_to_pos(best)
    # Remover marcadores de lista/cabeçalho
    best = re.sub(r'^[\-\*\d\.\:]+\s*', '', best).strip()
    return best


def _run_grounding_research(
    uploaded_images: List[bytes],
    user_prompt: Optional[str],
    mode: str,
    garment_hint_override: str = "",
) -> dict:
    """
    Chamada SEPARADA ao Gemini com Google Search ativo.
    DUAS ETAPAS para contornar regressão do Google (multimodal + grounding quebrado):
      1) garment_hint: reutilizado da triagem unificada (ou fallback via _infer_garment_hint)
      2) Chamada TEXT-ONLY com GoogleSearch tool → grounding efetivo
    Retorna contexto textual e metadados de grounding.
    """
    from agent_runtime.triage import _infer_garment_hint
    from agent_runtime.gemini_client import generate_text_with_tools
    from agent_runtime.visual_refs import _collect_grounded_reference_images

    # Etapa 1: reutiliza hint da triagem unificada se disponível; senão infere separadamente.
    if garment_hint_override:
        garment_hint = garment_hint_override
        print(f"[GROUNDING] 👁️  Garment hint (from unified triage): {garment_hint}")
    else:
        garment_hint = _infer_garment_hint(uploaded_images) if uploaded_images else ""
        print(f"[GROUNDING] 👁️  Garment hint (fallback infer): {garment_hint}")
    search_subject = garment_hint or user_prompt or "garment fashion"

    # Etapa 2: chamada TEXT-ONLY com Google Search (sem imagens = sem regressão)
    search_prompt = (
        f"You are a fashion expert. I have a garment that is: {search_subject}.\n\n"
        "Use Google Search to find:\n"
        "1. The EXACT garment type name in Portuguese AND English\n"
        "2. The correct silhouette terminology (e.g., batwing sleeves, kimono cardigan, ruana, cape)\n"
        "3. How this type of garment drapes and falls on the body\n"
        "4. How professional photographers typically shoot this garment style\n\n"
        "You MUST search the web to return fresh results. Rely entirely on external references.\n"
        "Return ONLY plain text, NO markdown. Keep it concise, max 3 paragraphs."
    )

    response = generate_text_with_tools(
        parts=[types.Part(text=search_prompt)],
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.3,
        max_tokens=1024,
    )

    queries: List[str] = []
    sources: List[dict] = []
    effective = False
    engine = "gemini_google_search"
    grounded_images: List[bytes] = []
    visual_ref_engine = "none"

    # Log grounding metadata
    try:
        candidates = getattr(response, "candidates", None)
        if candidates and len(candidates) > 0:
            candidate = candidates[0]
            gm = getattr(candidate, "grounding_metadata", None)
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

    # DuckDuckGo fallback removido — scraping HTML é instável, retorna zero resultados,
    # e adiciona latência sem valor. Quando Gemini Google Search não retorna metadata,
    # o structural contract (conf ~0.95) já é suficiente para fidelidade de garment.
    if not effective:
        print("[GROUNDING] ℹ️  Google Search não retornou metadata — seguindo sem grounding externo.")

    if mode == "full" and sources:
        grounded_images, visual_ref_engine = _collect_grounded_reference_images(
            sources=sources,
            max_pages=3,
            max_images=3,
        )
        if grounded_images:
            print(f"[GROUNDING] 🖼️  Visual refs collected: {len(grounded_images)} via {visual_ref_engine}")

    reason_codes = []
    has_web_sources = len(sources) > 0 or len(grounded_images) > 0

    if has_web_sources:
        effective = True
        reason_codes.append("grounding_effective_sources")
    else:
        # MT7: sem fontes úteis, grounding é inefetivo e NÃO deve contaminar
        # o prompt final com texto especulativo/internal knowledge.
        effective = False
        if result_text:
            reason_codes.append("grounding_internal_suppressed")
            print("[GROUNDING] ⚠️  No external sources. Suppressing internal grounding text.")
        reason_codes.append("grounding_no_sources")
        result_text = ""
        engine = "none"

    print(f"[GROUNDING] �� Research result ({len(result_text)} chars): {result_text[:200]}...")
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
        "pose_clause": _extract_pose_clause(result_text) if effective else "",
        "reason_codes": reason_codes,
    }
