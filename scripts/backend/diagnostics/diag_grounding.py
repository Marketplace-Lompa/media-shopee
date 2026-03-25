"""Diagnóstico isolado de grounding: testa Google Search + DuckDuckGo separadamente."""
import os, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "app" / "backend"
ENV_FILE = ROOT / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from google import genai
from google.genai import types
from config import MODEL_AGENT, SAFETY_CONFIG, GOOGLE_AI_API_KEY
from agent_runtime.grounding import _duckduckgo_search, _build_forced_grounding_queries

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

# ── TEST 1: Gemini Google Search ──
print("=" * 60)
print(f"TEST 1: Gemini Google Search (model={MODEL_AGENT})")
print("=" * 60)

search_prompt = (
    "You are a fashion expert. I have a garment that is: striped crochet ruana wrap.\n\n"
    "Use Google Search to find:\n"
    "1. The EXACT garment type name in Portuguese AND English\n"
    "2. The correct silhouette terminology\n"
    "3. How this garment drapes on the body\n\n"
    "You MUST search the web. Return plain text only, max 2 paragraphs."
)

try:
    response = client.models.generate_content(
        model=MODEL_AGENT,
        contents=[types.Content(role="user", parts=[types.Part(text=search_prompt)])],
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=512,
            safety_settings=SAFETY_CONFIG,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    candidates = getattr(response, "candidates", None)
    if candidates and len(candidates) > 0:
        candidate = candidates[0]
        gm = getattr(candidate, "grounding_metadata", None)
        print(f"  Metadata present: {gm is not None}")
        if gm:
            queries = list(getattr(gm, "web_search_queries", None) or [])
            print(f"  Search queries: {queries}")
            chunks = getattr(gm, "grounding_chunks", None)
            if chunks:
                print(f"  Sources: {len(chunks)}")
                for i, chunk in enumerate(chunks[:5]):
                    web = getattr(chunk, "web", None)
                    if web:
                        print(f"    [{i+1}] {getattr(web, 'title', '?')} → {getattr(web, 'uri', '?')}")
            else:
                print("  Sources: none")
                # Check all attributes of grounding_metadata
                print(f"  gm attrs: {[a for a in dir(gm) if not a.startswith('_')]}")
        else:
            print("  grounding_metadata is None")
            # Check candidate attributes
            print(f"  candidate attrs: {[a for a in dir(candidate) if not a.startswith('_')]}")

        # Print response text
        text = ""
        for part in (candidate.content.parts or []):
            if hasattr(part, "text") and part.text:
                text += part.text
        print(f"\n  Response text ({len(text)} chars):")
        print(f"  {text[:300]}")
    else:
        print("  No candidates in response")
        print(f"  Response: {response}")

except Exception as e:
    print(f"  ERROR: {e}")
    import traceback; traceback.print_exc()


# ── TEST 2: DuckDuckGo ──
print(f"\n{'=' * 60}")
print("TEST 2: DuckDuckGo search")
print("=" * 60)

queries = _build_forced_grounding_queries(None, "striped crochet ruana wrap", "lexical")
print(f"  Queries: {queries}")

for q in queries:
    try:
        results = _duckduckgo_search(q, limit=3)
        print(f"\n  Query: {q}")
        print(f"  Results: {len(results)}")
        for r in results[:3]:
            print(f"    - {r.get('title', '?')}: {r.get('uri', '?')}")
    except Exception as e:
        print(f"\n  Query: {q}")
        print(f"  ERROR: {e}")
