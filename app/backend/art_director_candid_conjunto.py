"""
Art Director Test — Candid Lifestyle: CONJUNTO (ruana + cachecol)
Referências selecionadas para mostrar AMBAS as peças do set.
"""
import sys
import uuid
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types
from config import GOOGLE_AI_API_KEY, MODEL_IMAGE, SAFETY_CONFIG, OUTPUTS_DIR

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

# ── Referências curadas para CONJUNTO ──
# Prioridade: fotos que mostram cachecol + ruana juntos
REF_DIR = Path(__file__).parent.parent / "tests" / "output" / "poncho-teste"
REFS = [
    # Mostra cachecol enrolado no pescoço + ruana nos ombros — melhor ref do set
    REF_DIR / "WhatsApp Image 2026-03-06 at 14.52.15 (3).jpeg",
    # Close-up do cachecol amarrado + ruana aberta — textura clara de ambas peças
    REF_DIR / "WhatsApp Image 2026-03-06 at 14.52.15 (4).jpeg",
    # Ruana cruzada com cachecol visível no pescoço — shape completo
    REF_DIR / "IMG_3329.jpg",
    # Frontal ruana aberta — referência de silhueta cocoon
    REF_DIR / "IMG_3321.jpg",
]

SESSION_ID = f"conjunto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
SESSION_DIR = OUTPUTS_DIR / SESSION_ID
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# ── Role prefix para CONJUNTO ──
ROLE_PREFIX = (
    "COPY this MATCHING SET from the reference photos EXACTLY — "
    "the set contains TWO pieces made from the same crochet knit fabric: "
    "(1) an open-front ruana/poncho wrap and (2) a matching scarf/neck wrap. "
    "Both pieces share the same olive green and dusty rose horizontal striped pattern, "
    "same crochet stitch texture, same yarn weight. "
    "The model MUST wear BOTH pieces together as a coordinated set. "
    "The references show the garments only, not a person to copy. "
    "Generate a NEW person wearing this exact matching set in a candid lifestyle shot: "
)

# ── 3 Variações ──
VARIATIONS = [
    {
        "name": "feira_beco_batman",
        "prompt": (
            "[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), "
            "3/4 front angle, model adjusting scarf with one hand. "
            "[2. SCENE] Colorful graffiti alley Beco do Batman in Vila Madalena São Paulo, "
            "authentic context, (cluttered/lived-in background:0.9), street art walls, cobblestone. "
            "[3. MODEL HERO] Mixed-race Brazilian woman with warm brown skin and loose curly hair, "
            "26yo model, standing casually near graffiti wall, one hand adjusting the matching scarf "
            "around her neck while the ruana drapes open on shoulders, "
            "(natural skin texture, visible pores, asymmetric features:1.3). "
            "[4. CAMERA] Shot on Fujifilm X-T4, 35mm f/1.4, "
            "(subtle chromatic aberration, ISO 800 noise, slight motion blur:1.2). "
            "[5. LIGHTING] Late afternoon directional sun creating warm-cool contrast with shadow side, "
            "mixed color temperature, (imperfect ambient bounce:1.1). "
            "[6. TEXTURE LOCK] Two-piece matching set: (Macro-accurate crochet knit wool blend:1.5) "
            "for BOTH the open-front ruana wrap AND the neck scarf. "
            "Exact thread count, proper fabric weight on both pieces. "
            "(Realistic light absorption on olive green and dusty rose striped yarn:1.4). "
            "The scarf and ruana MUST share identical stitch pattern, stripe width, and color palette. "
            "[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), "
            "symmetrical face, altered clothing silhouette, over-smoothed fabric, "
            "mismatched scarf texture, different knit pattern between pieces."
        ),
    },
    {
        "name": "metro_paulista",
        "prompt": (
            "[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), "
            "environmental portrait, slightly below eye level looking up. "
            "[2. SCENE] Avenida Paulista sidewalk São Paulo on overcast day, "
            "authentic context, (cluttered/lived-in background:0.9), "
            "MASP columns visible behind, urban foot traffic. "
            "[3. MODEL HERO] Afro-Brazilian woman with short natural TWA hair, "
            "30yo model, mid-stride crossing street, scarf loosely wrapped around neck, "
            "ruana flowing behind with movement, confident smile, "
            "(natural skin texture, visible pores, asymmetric features:1.3). "
            "[4. CAMERA] Shot on iPhone 15 Pro, 24mm, "
            "(subtle chromatic aberration, ISO 500 noise, slight motion blur:1.2). "
            "[5. LIGHTING] Overcast flat daylight with cool blue cast, "
            "mixed color temperature from nearby warm shop lights, (imperfect ambient bounce:1.1). "
            "[6. TEXTURE LOCK] Two-piece matching set: (Macro-accurate crochet knit wool blend:1.5) "
            "for BOTH the open-front ruana wrap AND the coordinating neck scarf. "
            "Exact thread count, proper fabric weight on both pieces. "
            "(Realistic light absorption on olive green and dusty rose striped yarn:1.4). "
            "The scarf and ruana MUST share identical stitch pattern, stripe width, and color palette. "
            "[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), "
            "symmetrical face, altered clothing silhouette, over-smoothed fabric, "
            "mismatched scarf texture, different knit pattern between pieces."
        ),
    },
    {
        "name": "varanda_manha",
        "prompt": (
            "[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), "
            "seated close-up from waist up, eye level, shallow depth of field. "
            "[2. SCENE] Apartment balcony in Pinheiros São Paulo during cool morning, "
            "authentic context, (cluttered/lived-in background:0.9), "
            "ceramic coffee cup on small table, plants, city skyline soft in bokeh. "
            "[3. MODEL HERO] Light-skinned Brazilian woman of Italian descent with dark straight hair, "
            "34yo model, seated in rattan chair with scarf bundled cozy at neck "
            "and ruana wrapped around her like a blanket, holding warm mug, eyes half-closed, "
            "(natural skin texture, visible pores, asymmetric features:1.3). "
            "[4. CAMERA] Shot on Sony A7C, 55mm f/1.8, "
            "(subtle chromatic aberration, ISO 1200 noise, slight motion blur:1.2). "
            "[5. LIGHTING] Early morning cool blue ambient with warm tungsten spill from inside, "
            "mixed color temperature, (imperfect ambient bounce:1.1). "
            "[6. TEXTURE LOCK] Two-piece matching set: (Macro-accurate crochet knit wool blend:1.5) "
            "for BOTH the open-front ruana wrap AND the matching neck scarf. "
            "Exact thread count, proper fabric weight on both pieces. "
            "(Realistic light absorption on olive green and dusty rose striped yarn:1.4). "
            "The scarf and ruana MUST share identical stitch pattern, stripe width, and color palette. "
            "[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), "
            "symmetrical face, altered clothing silhouette, over-smoothed fabric, "
            "mismatched scarf texture, different knit pattern between pieces."
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


def generate_conjunto(variation: dict, refs: list[Path], index: int) -> dict:
    """Gera uma imagem candid lifestyle com o conjunto ruana + cachecol."""
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

    full_prompt = ROLE_PREFIX + variation["prompt"]
    content_parts = ref_parts + [types.Part(text=full_prompt)]

    print(f"\n{'='*60}")
    print(f"🎬 Gerando variação {index}: {variation['name']}")
    print(f"📐 Aspect: 4:5 | Resolution: 1K | Thinking: MINIMAL")
    print(f"📸 Refs: {len(refs)} imagens (foco no CONJUNTO)")
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

    parts = response.parts if response.parts else []
    for part in parts:
        if (
            getattr(part, "inline_data", None)
            and getattr(part.inline_data, "mime_type", None)
            and part.inline_data.mime_type.startswith("image/")
        ):
            ext = part.inline_data.mime_type.split("/")[-1]
            filename = f"conjunto_{variation['name']}_{index}.{ext}"
            filepath = SESSION_DIR / filename
            data = getattr(part.inline_data, "data", None)
            if data:
                filepath.write_bytes(data)
            size_kb = filepath.stat().st_size / 1024
            print(f"✅ Salvo: {filepath} ({size_kb:.1f} KB)")
            return {
                "name": variation["name"],
                "filename": filename,
                "path": str(filepath),
                "size_kb": round(size_kb, 1),
            }

    raise RuntimeError(f"Nano não retornou imagem para {variation['name']}")


def main():
    print(f"\n🎨 ART DIRECTOR — Conjunto Ruana + Cachecol (Candid Lifestyle)")
    print(f"📁 Session: {SESSION_ID}")
    print(f"📁 Output: {SESSION_DIR}")
    print(f"🖼️  Referências: {[r.name for r in REFS]}")

    for ref in REFS:
        if not ref.exists():
            print(f"❌ Referência não encontrada: {ref}")
            return
        print(f"  ✓ {ref.name} ({ref.stat().st_size / 1024:.0f} KB)")

    results = []
    for i, var in enumerate(VARIATIONS, 1):
        try:
            result = generate_conjunto(var, REFS, i)
            results.append(result)
        except Exception as e:
            print(f"❌ Falha em {var['name']}: {e}")
            results.append({"name": var["name"], "error": str(e)})

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
