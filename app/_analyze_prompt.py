"""Temporary script to analyze real prompt through the pipeline."""
import sys
import re

sys.path.insert(0, "backend")
from agent_runtime.prompt_result import finalize_prompt_agent_result

RAW_PROMPT = (
    "Replace the placeholder person in the base image completely. "
    "Do not preserve any face, skin tone, hair, body type, or age impression from the base image person or from the references. "
    "Keep the garment exactly the same: preserve the exact garment identity, shape, and texture visible in the references, maintain waist length as shown in the reference, "
    "keep the front closure intact, preserve: ribbed mock neck collar, geometric relief texture. "
    "CRITICAL — preserve the exact surface pattern geometry from the references: "
    "A light beige or camel-colored knit sweater featuring a prominent 3D geometric relief pattern of intersecting diagonal lines forming a grid of squares and triangles across the front panel. "
    "The textile is a fine-gauge knit with ribbed detailing at the mock neck, cuffs, and hem, providing a structured yet soft texture.. "
    "Do not reinterpret stripe direction, pattern angle, or pattern scale. "
    "If the pattern appears diagonal or chevron in the references, it must remain diagonal or chevron in the output. "
    "Use all references only as garment evidence for shape, fabric, stitch, color behavior, and garment geometry. "
    "Never transfer identity from references; create a fully new Brazilian woman around the locked garment. "
    "References are visual evidence for garment fidelity only. "
    "Do not copy any human identity traits from references. "
    "Do not repeat the dominant gesture from references unless the user brief explicitly requires it. "
    "Treat the garment as the locked object and redesign only the woman, the pose, the camera relation, and the environment around it. "
    "RAW photo, a medium-wide shot of Her warm golden skin shows a natural dewy sheen and subtle freckles across her nose bridge as she offers a bright, welcoming half-neutral expression. "
    "She wears the fitted beige knit mock-neck pullover from the reference, its intricate geometric relief texture catching the soft afternoon side-light to reveal the depth of the textile. "
    "The garment ribbed collar and cuffs remain crisp and structured, while the waist-length hem is loosely tucked into dark-wash straight-leg denim. "
    "Captured in a candid moment on a quiet tree-lined sidewalk in a Brazilian neighborhood, she is mid-stride with her weight shifting forward, creating a natural, unperformed energy. "
    "a woman in her 28 with high cheekbones, defined facial structure, wide-set almond eyes, soft jawline, and medium forehead. "
    "RAW photo, a medium-wide shot of Her warm golden skin shows a natural dewy sheen and subtle freckles across her nose bridge as she offers a bright, welcoming half-neutral expression. "
    "She wears the fitted beige knit mock-neck pullover from the reference, its intricate geometric relief texture catching the soft afternoon side-light to reveal the depth of the textile. "
    "The garment ribbed collar and cuffs remain crisp and structured, while the waist-length hem is loosely tucked into dark-wash straight-leg denim. "
    "Captured in a candid moment on a quiet tree-lined sidewalk in a Brazilian neighborhood, she is mid-stride with her weight shifting forward, creating a natural, unperformed energy. "
    "a woman in her 28 with high cheekbones, defined facial structure, wide-set almond eyes, soft jawline, and medium forehead, "
    "warm honey skin and light freckles on the nose bridge, shoulder-length, chocolate hair, caramel highlights, and soft waves, "
    "medium waist-to-hip ratio, waist-to-hip structure, balanced shoulders, and defined shoulders, and neutral mouth and quiet attention "
    "a woman in her 28 with high cheekbones, defined facial structure, wide-set almond eyes, soft jawline, and medium forehead, "
    "light freckles on the nose bridge, shoulder-length chocolate waves with subtle caramel highlights, "
    "natural silhouette with balanced shoulders and medium waist-to-hip ratio, and neutral mouth and quiet attention. "
    "Do not introduce any visible undershirt, layered neckline, or contrasting inner collar; the garment neckline itself must remain the only visible neckline element. "
    "Render the garment with macro-accurate knit fabric, correct fabric weight, consistent stitch definition, and realistic light absorption across the garment colors and yarn tones. "
    "Keep the result highly photorealistic with believable human skin and realistic body proportions."
)

result = finalize_prompt_agent_result(
    result={"prompt": RAW_PROMPT, "shot_type": "wide"},
    has_images=False,
    has_prompt=True,
    user_prompt="pullover bege com textura geometrica",
    structural_contract={},
    guided_brief=None,
    guided_enabled=False,
    guided_set_mode="unica",
    guided_set_detection={},
    grounding_mode="off",
    pipeline_mode="text_mode",
    aspect_ratio="4:5",
    pose="",
    grounding_pose_clause="",
    profile="features blend 'Ana' and 'Raissa'",
    scenario="bairro residencial brasileiro",
    diversity_target={
        "profile_id": "natural:natural_commercial",
        "casting_state": {
            "age": "late 20s",
            "face_structure": "high cheekbones, defined facial structure, wide-set almond eyes, soft jawline, medium forehead",
            "hair": "shoulder-length chocolate waves with subtle caramel highlights",
            "beauty_read": "warm honey skin with light freckles",
            "body": "balanced shoulder-to-hip proportions",
            "expression": "neutral mouth with quiet attention",
        },
    },
    mode_id="natural",
    framing_profile="three_quarter",
    camera_type="natural_digital",
    capture_geometry="three_quarter_eye_level",
    lighting_profile="natural_soft",
    pose_energy="relaxed",
    casting_profile="natural_commercial",
)

final = result["prompt"]
debug = result.get("prompt_compiler_debug", {})
floor = debug.get("human_surface_floor", {})
rules = debug.get("nano_output_rules", {})

print("=" * 80)
print("PROMPT FINAL:")
print("=" * 80)
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", final) if s.strip()]
for i, s in enumerate(sentences, 1):
    print(f"  [{i:02d}] {s}")

print()
print(f"Total palavras: {len(final.split())}")
print(f"Total sentenças: {len(sentences)}")
print()
print("RULES APPLIED:", rules.get("applied", []))
print()

# Check problems
problems = []
low = final.lower()

for label, phrase, max_count in [
    ("RAW photo", "raw photo", 1),
    ("a woman in her 28", "a woman in her 28", 0),
    ("a woman in her late 20s", "a woman in her late 20s", 1),
    ("half-neutral", "half-neutral", 0),
    ("from the reference", "from the reference", 0),
    ("shot of Her", "shot of her", 0),
]:
    count = low.count(phrase.lower())
    if count > max_count:
        problems.append(f'"{label}" aparece {count}x (max {max_count})')

for phrase in [
    "high cheekbones, defined facial structure",
    "wide-set almond eyes",
    "soft jawline",
    "freckles across her nose bridge",
    "freckles on the nose bridge",
    "chocolate waves",
    "caramel highlights",
    "balanced shoulders",
    "medium waist-to-hip ratio",
    "neutral mouth",
    "geometric relief texture",
    "ribbed collar and cuffs",
    "waist-length hem",
    "dark-wash straight-leg denim",
    "tree-lined sidewalk",
    "mid-stride",
]:
    count = low.count(phrase.lower())
    if count > 1:
        problems.append(f'Duplicado: "{phrase}" {count}x')

for directive in [
    "replace the placeholder",
    "do not preserve",
    "do not copy",
    "do not reinterpret",
    "do not repeat",
    "never transfer identity",
    "references are visual evidence",
    "treat the garment as the locked",
    "use all references only",
    "critical —",
    "do not introduce any visible undershirt",
    "render the garment with macro",
    "keep the result highly photorealistic",
]:
    if directive.lower() in low:
        problems.append(f'Diretiva de controle vazou: "{directive}"')

print("PROBLEMAS DETECTADOS:")
if problems:
    for p in problems:
        print(f"  ❌ {p}")
else:
    print("  ✅ Nenhum problema detectado!")

print()
val = floor.get("validation_after", {})
print(f"Validation: valid={val.get('valid')}, face_count={val.get('face_count')}")
