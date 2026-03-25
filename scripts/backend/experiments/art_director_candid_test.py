"""
Art Director Test — Candid Lifestyle Method
Testa a receita de prompt com pesos estilo SD aplicada ao Nano Banana 2.
Usa 3 referências curadas (2 worn + 1 detail) + role_prefix + MINIMAL thinking.
"""
import sys
import uuid
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from google import genai
from google.genai import types
from config import GOOGLE_AI_API_KEY, MODEL_IMAGE, SAFETY_CONFIG, OUTPUTS_DIR

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

# ── Referências curadas (2 worn front + 1 worn detail/back) ──
REF_DIR = ROOT / "app" / "tests" / "output" / "poncho-teste"
REFS = [
    REF_DIR / "IMG_3321.jpg",       # worn front, frontal, full garment visible
    REF_DIR / "IMG_3328.jpg",       # worn 3/4, arms out, drape visible
    REF_DIR / "WhatsApp Image 2026-03-06 at 14.52.14.jpeg",  # different angle, back texture
]

SESSION_ID = f"candid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
SESSION_DIR = OUTPUTS_DIR / SESSION_ID
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# ── 3 Variações de cena brasileira ──
VARIATIONS = [
    {
        "name": "cafe_vila_madalena",
        "prompt": (
            "[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), "
            "3/4 front angle, natural head tilt. "
            "[2. SCENE] Small neighborhood café in Vila Madalena São Paulo, "
            "authentic context, (cluttered/lived-in background:0.9), mosaic tiles, potted plants. "
            "[3. MODEL HERO] Mixed-race Brazilian woman with warm olive skin and wavy dark brown hair, "
            "28yo model, leaning against rustic wooden counter holding ceramic coffee mug, "
            "(natural skin texture, visible pores, asymmetric features:1.3). "
            "[4. CAMERA] Shot on Fujifilm X-T4, 35mm f/1.4, "
            "(subtle chromatic aberration, ISO 800 noise, slight motion blur:1.2). "
            "[5. LIGHTING] Late afternoon golden hour through café window, mixed color temperature, "
            "(imperfect ambient bounce:1.1). "
            "[6. TEXTURE LOCK] (Macro-accurate crochet knit wool blend:1.5), exact thread count, "
            "proper fabric weight, (realistic light absorption on olive green and dusty rose striped yarn:1.4). "
            "[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), "
            "symmetrical face, altered clothing silhouette, over-smoothed fabric."
        ),
    },
    {
        "name": "parque_ibirapuera",
        "prompt": (
            "[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), "
            "full body shot from mid-distance, slight upward angle. "
            "[2. SCENE] Tree-lined path in Ibirapuera Park São Paulo during autumn, "
            "authentic context, (cluttered/lived-in background:0.9), fallen leaves, park benches, joggers behind. "
            "[3. MODEL HERO] Dark-skinned Afro-Brazilian woman with natural curly hair, "
            "25yo model, walking mid-stride turning to look at camera, one hand on open ruana, "
            "(natural skin texture, visible pores, asymmetric features:1.3). "
            "[4. CAMERA] Shot on Sony A7III, 50mm f/1.8, "
            "(subtle chromatic aberration, ISO 640 noise, slight motion blur:1.2). "
            "[5. LIGHTING] Overcast diffused daylight filtering through tree canopy, mixed color temperature, "
            "(imperfect ambient bounce:1.1). "
            "[6. TEXTURE LOCK] (Macro-accurate crochet knit wool blend:1.5), exact thread count, "
            "proper fabric weight, (realistic light absorption on olive green and dusty rose striped yarn:1.4). "
            "[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), "
            "symmetrical face, altered clothing silhouette, over-smoothed fabric."
        ),
    },
    {
        "name": "sala_boho_sp",
        "prompt": (
            "[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), "
            "eye-level seated shot, environmental portrait framing. "
            "[2. SCENE] Cozy boho-style living room in a São Paulo apartment, "
            "authentic context, (cluttered/lived-in background:0.9), macramé wall hanging, "
            "terracotta pots, linen sofa, warm-tone throw pillows. "
            "[3. MODEL HERO] Light-skinned Southern Brazilian woman with straight auburn hair, "
            "32yo model, sitting cross-legged on sofa wrapping ruana around shoulders, "
            "(natural skin texture, visible pores, asymmetric features:1.3). "
            "[4. CAMERA] Shot on Canon R6, 85mm f/2.0, "
            "(subtle chromatic aberration, ISO 1600 noise, slight motion blur:1.2). "
            "[5. LIGHTING] Warm tungsten table lamp mixed with blue twilight from window, "
            "mixed color temperature, (imperfect ambient bounce:1.1). "
            "[6. TEXTURE LOCK] (Macro-accurate crochet knit wool blend:1.5), exact thread count, "
            "proper fabric weight, (realistic light absorption on olive green and dusty rose striped yarn:1.4). "
            "[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), "
            "symmetrical face, altered clothing silhouette, over-smoothed fabric."
        ),
    },
]


def _detect_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def generate_candid(variation: dict, refs: list[Path], index: int) -> dict:
    """Gera uma imagem candid lifestyle com referências visuais."""
    # Carregar referências
    ref_parts = []
    _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH
    for ref_path in refs:
        img_bytes = ref_path.read_bytes()
        ref_parts.append(
            types.Part(
                inline_data=types.Blob(mime_type=_detect_mime(img_bytes), data=img_bytes),
                media_resolution=_hi_res,
            )
        )

    # Role prefix (ancora de fidelidade) + prompt candid
    role_prefix = (
        "COPY this garment from the reference photos EXACTLY — "
        "same design, colors, texture, stitch pattern, and drape. "
        "The references show the garment only, not a person to copy. "
        "Generate a NEW person wearing this exact garment in a candid lifestyle shot: "
    )
    full_prompt = role_prefix + variation["prompt"]

    content_parts = ref_parts + [types.Part(text=full_prompt)]

    print(f"\n{'='*60}")
    print(f"🎬 Gerando variação {index}: {variation['name']}")
    print(f"📐 Aspect: 4:5 | Resolution: 1K | Thinking: MINIMAL")
    print(f"📸 Refs: {len(refs)} imagens")
    print(f"{'='*60}")

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
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
            safety_settings=SAFETY_CONFIG,
        ),
    )

    # Extrair imagem
    parts = response.parts if response.parts else []
    for part in parts:
        if (
            getattr(part, "inline_data", None)
            and getattr(part.inline_data, "mime_type", None)
            and part.inline_data.mime_type.startswith("image/")
        ):
            ext = part.inline_data.mime_type.split("/")[-1]
            filename = f"candid_{variation['name']}_{index}.{ext}"
            filepath = SESSION_DIR / filename
            data = getattr(part.inline_data, "data", None)
            if data:
                filepath.write_bytes(data)
            size_kb = filepath.stat().st_size / 1024
            print(f"✅ Salvo: {filepath} ({size_kb:.1f} KB)")

            # Capturar texto da resposta (thinking trace)
            text_parts = [p.text for p in parts if hasattr(p, "text") and p.text]
            if text_parts:
                trace_path = SESSION_DIR / f"trace_{variation['name']}_{index}.txt"
                trace_path.write_text("\n".join(text_parts))
                print(f"📝 Trace salvo: {trace_path}")

            return {
                "name": variation["name"],
                "filename": filename,
                "path": str(filepath),
                "size_kb": round(size_kb, 1),
            }

    raise RuntimeError(f"Nano não retornou imagem para {variation['name']}")


def main():
    print(f"\n🎨 ART DIRECTOR — Candid Lifestyle Method")
    print(f"📁 Session: {SESSION_ID}")
    print(f"📁 Output: {SESSION_DIR}")
    print(f"🖼️  Referências: {[r.name for r in REFS]}")

    # Verificar referências
    for ref in REFS:
        if not ref.exists():
            print(f"❌ Referência não encontrada: {ref}")
            return
        print(f"  ✓ {ref.name} ({ref.stat().st_size / 1024:.0f} KB)")

    results = []
    for i, var in enumerate(VARIATIONS, 1):
        try:
            result = generate_candid(var, REFS, i)
            results.append(result)
        except Exception as e:
            print(f"❌ Falha em {var['name']}: {e}")
            results.append({"name": var["name"], "error": str(e)})

    # Resumo
    print(f"\n{'='*60}")
    print(f"📊 RESUMO — {SESSION_ID}")
    print(f"{'='*60}")
    for r in results:
        if "error" in r:
            print(f"  ❌ {r['name']}: {r['error']}")
        else:
            print(f"  ✅ {r['name']}: {r['filename']} ({r['size_kb']} KB)")
    print(f"\n📁 Outputs em: {SESSION_DIR}")


if __name__ == "__main__":
    main()
