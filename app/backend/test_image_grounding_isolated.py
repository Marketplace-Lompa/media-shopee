"""
Teste isolado: Google Image Search grounding com gemini-3.1-flash-image-preview.
Roda com imagem de ref do poncho-ruana e loga queries + sources do grounding.
"""
import os, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
ENV_FILE = ROOT.parent.parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(ROOT))

from google import genai
from google.genai import types
from config import MODEL_IMAGE, SAFETY_CONFIG, GOOGLE_AI_API_KEY
from image_utils import detect_image_mime as _detect_image_mime

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

SAMPLES_DIR = ROOT.parent / "tests" / "samples" / "poncho-ruana-listras"
OUTPUT_DIR = ROOT.parent / "outputs" / "test_img_grounding_v2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Carregar 1 ref do poncho
ref_path = SAMPLES_DIR / "IMG_3324.jpg"
ref_bytes = ref_path.read_bytes()
print(f"[REF] {ref_path.name} — {len(ref_bytes) // 1024}KB")

prompt = (
    "Before generating, search for images of: 'crochet ruana chevron diagonal stripes artisanal handmade' "
    "to understand the exact pattern geometry of this garment type. "
    "Use the retrieved image context to ensure pattern fidelity in your generation. "
    "Then generate: ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment. "
    "Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible. "
    "Clean premium indoor composition, soft natural daylight. "
    "Preserve exact garment geometry, texture continuity, and construction details. "
    "Garment identity: artisanal crochet ruana wrap with diagonal chevron stripes radiating from center panel, "
    "olive green and pink color palette, open front, wide sleeves. "
    "Non-negotiable structure guards: open-front ruana silhouette, wide batwing sleeves, knee-length hem. "
    "Treat the garment as the fixed object and build the model, camera, and background around it."
)

_tools = [
    types.Tool(google_search=types.GoogleSearch(
        search_types=types.SearchTypes(
            image_search=types.ImageSearch()
        )
    ))
]

_hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH
content_parts = [
    types.Part(text="These are reference images of the garment — use only for garment identity, not model identity."),
    types.Part(
        inline_data=types.Blob(mime_type=_detect_image_mime(ref_bytes), data=ref_bytes),
        media_resolution=_hi_res,
    ),
    types.Part(text=prompt),
]

print(f"\n[TEST] Chamando {MODEL_IMAGE} com image_search grounding ativo...")
print(f"[TEST] Prompt length: {len(prompt)} chars\n")

response = client.models.generate_content(
    model=MODEL_IMAGE,
    contents=[types.Content(role="user", parts=content_parts)],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        temperature=1.0,
        image_config=types.ImageConfig(
            aspect_ratio="4:5",
            image_size="1K",
        ),
        safety_settings=SAFETY_CONFIG,
        tools=_tools,
    ),
)

# ── Grounding metadata ─────────────────────────────────────────────────────
print("=" * 60)
print("GROUNDING METADATA")
print("=" * 60)

grounding_found = False
if response.candidates:
    for i, cand in enumerate(response.candidates):
        gm = getattr(cand, "grounding_metadata", None)
        if gm:
            grounding_found = True
            print(f"  ✅ grounding_metadata PRESENTE (candidate {i})")

            queries = getattr(gm, "image_search_queries", None) or getattr(gm, "web_search_queries", None)
            if queries:
                print(f"\n  🔍 Queries geradas ({len(queries)}):")
                for q in queries:
                    print(f"     • {q}")
            else:
                print("  ⚠️  Nenhuma query encontrada")

            chunks = getattr(gm, "grounding_chunks", None) or []
            if chunks:
                print(f"\n  📎 Sources retornados ({len(chunks)}):")
                for j, chunk in enumerate(chunks):
                    # Dump completo do chunk para inspecionar estrutura real do SDK
                    print(f"\n     [{j+1}] chunk type: {type(chunk).__name__}")
                    print(f"          repr: {repr(chunk)[:300]}")
            else:
                print("  ⚠️  grounding_chunks: vazio (model usou contexto internamente sem expor sources)")

            # Atributos disponíveis
            all_attrs = {a: getattr(gm, a, None) for a in dir(gm) if not a.startswith("_")}
            non_none = {k: v for k, v in all_attrs.items() if v is not None and v != [] and v != {}}
            print(f"\n  📋 Campos não-nulos em grounding_metadata: {list(non_none.keys())}")
        else:
            print(f"  ❌ grounding_metadata: None (candidate {i})")

if not grounding_found:
    print("  ❌ Nenhum candidate com grounding_metadata")

# ── Output image ───────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("OUTPUT IMAGE")
print("=" * 60)

image_saved = False
parts_resp = response.parts if response.parts else []
for part in parts_resp:
    if getattr(part, "inline_data", None) and getattr(part.inline_data, "mime_type", "").startswith("image/"):
        ext = part.inline_data.mime_type.split("/")[-1]
        out_path = OUTPUT_DIR / f"grounding_test_result.{ext}"
        out_path.write_bytes(part.inline_data.data)
        size_kb = len(part.inline_data.data) // 1024
        print(f"  ✅ Imagem salva: {out_path}")
        print(f"     Tamanho: {size_kb}KB")
        image_saved = True
        break

if not image_saved:
    print("  ❌ Nenhuma imagem retornada")
    # Log texto se houver
    for part in parts_resp:
        if getattr(part, "text", None):
            print(f"  📝 Texto retornado: {part.text[:200]}")

print("\n[TEST] Concluído.")
