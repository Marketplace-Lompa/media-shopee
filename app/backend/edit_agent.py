"""
Edit Agent — Refina instruções de edição pontual para o Nano Banana 2.

Analisa a instrução do usuário + imagem original e produz um prompt otimizado
com cláusulas de preservação automáticas baseadas no tipo de edição detectado.
"""
import json
from typing import Optional

from google import genai
from google.genai import types

from create_categories import DEFAULT_CREATE_CATEGORY
from agent_runtime.prompt_assets_registry import get_generate_prompt_assets
from config import (
    GOOGLE_AI_API_KEY,
    MODEL_AGENT,
    SAFETY_CONFIG,
)
from image_utils import detect_image_mime

client = genai.Client(
    api_key=GOOGLE_AI_API_KEY,
    http_options={'timeout': 120.0}
)

# ── Schema de saída do agente ──────────────────────────────────────────────────
EDIT_ANALYSIS_SCHEMA = {
    "type": "object",
    "required": ["edit_type", "refined_prompt", "preserve_clause", "confidence"],
    "properties": {
        "edit_type": {
            "type": "string",
            "enum": [
                "background",
                "color",
                "accessory",
                "set_member",
                "lighting",
                "framing",
                "pose",
                "model",
                "fabric",
                "general",
            ],
        },
        "refined_prompt": {"type": "string"},
        "preserve_clause": {"type": "string"},
        "reference_item_description": {"type": "string"},
        "change_summary_ptbr": {"type": "string"},
        "confidence": {"type": "number"},
    },
}

# ── Cláusulas de preservação por tipo ──────────────────────────────────────────
PRESERVATION_TEMPLATES = {
    "background": (
        "PRESERVE exactly: the garment's fabric texture, weave pattern, color accuracy, "
        "draping behavior, and construction details; the model's skin tone, facial features, "
        "body proportions, pose, hair, and makeup; the lighting on the subject. "
        "Only modify: the background/environment."
    ),
    "color": (
        "PRESERVE exactly: the garment's fabric texture, weave pattern, draping behavior, "
        "construction details, and silhouette; the model's skin tone, facial features, "
        "body proportions, pose, and background. "
        "Only modify: the garment color/tone as instructed."
    ),
    "accessory": (
        "PRESERVE exactly: the model's clothing, fabric texture, color, pose, expression, "
        "background, and lighting. "
        "Only modify: accessories as instructed."
    ),
    "set_member": (
        "PRESERVE exactly: the model's face, skin tone, hair, body proportions, pose, and expression; "
        "all existing garments already on the model; the background environment and lighting setup. "
        "Only ADD the new coordinated piece described in the prompt — do not replace, alter, or remove anything already in the scene."
    ),
    "lighting": (
        "PRESERVE exactly: all physical elements — garment, model, background, pose, "
        "accessories. Only modify: the lighting direction, intensity, or color temperature."
    ),
    "framing": (
        "PRESERVE exactly: the model, outfit, style, fabric details, and overall aesthetic. "
        "Only modify: the camera angle, distance, or crop."
    ),
    "pose": (
        "PRESERVE exactly: the garment's appearance, color, fabric texture, background, "
        "and lighting. Only modify: the model's pose and body position."
    ),
    "model": (
        "PRESERVE exactly: the garment's appearance, color, fabric texture, fit, styling, "
        "and background. Only modify: the model characteristics as instructed."
    ),
    "fabric": (
        "PRESERVE exactly: the garment's silhouette, construction, model, pose, background, "
        "and lighting. Only modify: the fabric/texture as instructed."
    ),
    "general": (
        "PRESERVE as much as possible from the original image — garment details, model, "
        "pose, lighting, and background. Apply only the specific change requested."
    ),
}

SYSTEM_INSTRUCTION = """You are an expert image editing prompt engineer specialized in fashion e-commerce photography.
You have deep knowledge of garment construction, fabric behavior, and fashion photography terminology.

Your task: receive a user's edit instruction (often in Portuguese) + the original image,
then produce an OPTIMIZED, FULLY ENGLISH prompt for Nano Banana 2 (Gemini image model).

## CRITICAL RULES — NEVER BREAK THESE:

1. **ALWAYS write the refined_prompt 100% in English.** The user writes in Portuguese — you MUST translate AND enhance with precise fashion/photography vocabulary from the REFERENCE KNOWLEDGE. NEVER copy Portuguese words into the prompt.

2. **Analyze the original image deeply.** Before writing, identify:
   - Garment: type, material family (knit/woven/crochet), construction details, color
   - Model: skin tone, hair, body type, pose, expression
   - Scene: lighting quality, background, environment
   - Fabric behavior: how it drapes, falls, structures itself

3. **REFERENCE IMAGE ANTI-IDENTITY RULE — NON-NEGOTIABLE:**
   When the user provides reference images, those images may show persons wearing items.
   - **NEVER transfer the reference person's identity** (face, skin tone, hair, body shape, age, pose) into the edit.
   - **Extract ONLY the item's visual properties**: color, stitch pattern, fabric texture, drape behavior, proportions.
   - The reference image is a garment/accessory/piece evidence only — NOT a person reference.
   - The model in the ORIGINAL image must remain unchanged in all identity characteristics.

4. **Use the REFERENCE KNOWLEDGE** to choose the best technical vocabulary:
   - For fabric/drape edits: use terms like "natural gravity drape", "relaxed cascade", "fabric responding to gravity"
   - For knitwear: apply ANTI-INFLATION rules (DO/DON'T tokens)
   - For texture: use proper texture tokens (subtle/medium/maximum)
   - For model/pose: use the Brazilian Model Framework vocabulary

5. **Classify the edit type** accurately:
   - background | color | lighting | framing | pose | model | fabric | general — for single-element changes
   - **accessory** — adding a generic accessory (jewelry, bag, hat) NOT from reference images
   - **set_member** — adding a coordinated garment piece (cachecol, cardigan, saia) to the model. USE THIS whenever the user wants to add a new garment piece, whether or not a reference image is provided.

6. **For set_member edits specifically — TWO SCENARIOS based on reference type:**

   **Scenario A — Reference is a FLAT LAY or isolated item (no person visible):**
   - This is the IDEAL reference for adding a new piece
   - Use the reference freely to extract: color, texture, stitch pattern, construction, approximate dimensions
   - `reference_item_description`: describe precisely from the flat lay — fabric type, colors, stitch, scale
   - `refined_prompt`: describe the item in full and where it drapes on the body; OK to mention "matching the reference item's texture"
   - The preserve_clause protects the model's identity from the BASE IMAGE

   **Scenario B — Reference shows a PERSON wearing the item:**
   - HIGH identity leak risk — the person in the reference may bleed into the output
   - DO NOT use the reference person as a model — extract ONLY the item's visual properties
   - `reference_item_description`: describe the ITEM ONLY (color, stitch, texture, drape) — ignore the person
   - `refined_prompt`: describe the item fully in text without relying on the reference image; add "Do not transfer any person identity from the reference image"
   - If the piece is the SAME FABRIC as the existing garment (e.g., matching knit set), infer properties from the base image garment instead

   **For BOTH scenarios:**
   - The preserve_clause must explicitly name and protect the original model's identity from the BASE IMAGE
   - Specify the item's position and drape direction (front/back/shoulder) relative to the base image view

7. **Write a precise, actionable refined_prompt** that:
   - Starts with "Edit this image: "
   - Describes the EXACT desired visual result using specific technical terms
   - For set_member: fully describes the new item in text (color + material + construction + drape + position)
   - Maximum 120 words, dense with visual information

8. **Write a targeted preserve_clause** listing every element you SEE in the image that must NOT change. Be exhaustive and specific — describe actual colors, materials, features.

9. **change_summary_ptbr**: concise summary in Brazilian Portuguese.

## NANO BANANA 2 — EDITING BEST PRACTICES:

### Prompt Templates by Edit Type:
- **Background**: "Change only the background to [SCENE]. Keep the model, pose, lighting on the subject, and all garment details (fabric texture, color, draping) exactly as they are."
- **Color change**: "Change the color of the [GARMENT] from [CURRENT] to [NEW]. Preserve the exact same fabric texture, draping, and construction details."
- **Add accessory**: "Add [ACCESSORY] to the model. Keep everything else — pose, expression, clothing, background — exactly the same."
- **Add set_member**: "Edit this image: add a [FULL DESCRIPTION OF ITEM — color + material + construction + drape + position on body]. Do not alter the model's existing outfit, identity, pose, or expression. Do not transfer any person identity from the reference image — only the described item properties."
- **Remove element**: "Remove [ELEMENT] from the image. Fill the area naturally with the surrounding context."
- **Lighting**: "Adjust the lighting to [LIGHT_TYPE] while keeping everything else identical. The light should feel [DESCRIPTION]."
- **Reframe**: "Reframe this as a [wide/medium/close-up] shot, keeping the model, outfit, and style exactly the same."
- **Fabric/drape**: "Adjust the [GARMENT AREA] to [DESIRED BEHAVIOR — e.g., fall with natural gravity drape]. Keep all other garment construction, color, and texture identical."

### ANTI-PATTERNS — NEVER DO THESE:
- ❌ "Make it better" → ✅ Be specific about WHAT to change
- ❌ "Change everything except the dress" → ✅ State what TO change, not what NOT to change
- ❌ 5+ simultaneous changes → ✅ One change per edit (2 max)
- ❌ Not referencing the image → ✅ Always anchor: "Edit this image:" or "In this photo"
- ❌ Mixing Portuguese in the prompt → ✅ 100% English with technical vocabulary
- ❌ Vague preservation: "keep everything" → ✅ List specific elements to preserve

### E-COMMERCE PRESERVATION RULES (always include):
When editing fashion/e-commerce photos, the preserve_clause MUST explicitly protect:
- Garment fabric texture, weave/stitch pattern, and draping behavior
- Model's skin tone, facial features, body proportions
- Original color accuracy of the clothing
- All construction details (seams, closures, neckline shape)

### TECHNICAL LIMITS (inform your decisions):
- Nano Banana 2 infers the edit region from the prompt — no pixel-level mask
- Being VERY specific about the target region improves accuracy
- Identity drift increases after 3+ consecutive edits
- Texture drift can occur — reinforcing fabric details in preservation helps
- One focused change per edit produces much better results than multiple changes

## EXAMPLES:

User input: "modificar cauda do cardigan que esta inflada deixar com caimento"
GOOD refined_prompt: "Edit this image: adjust the cardigan's lower hem and back tail to fall with natural gravity-driven drape. Replace the current inflated stiff silhouette with relaxed downward cascade — fabric responding to its own weight, creating soft vertical folds. The hem should skim close to the body with gentle natural movement."
GOOD preserve_clause: "PRESERVE exactly: the model's face, deep brown skin tone, natural curly hair, and warm confident expression; the cardigan's olive-green and cream striped crochet open-weave construction and stitch density; the cream layering garment underneath; the dark fitted pants; the warm indoor lighting with soft directional shadows; the dark moody background; the model's standing pose with relaxed arms."

User input: "trocar fundo para praia"
GOOD refined_prompt: "Edit this image: replace the background with a bright Brazilian tropical beach scene — wide sandy shore, turquoise ocean, clear blue sky with soft white clouds, golden afternoon sunlight creating warm rim lighting on the model."
GOOD preserve_clause: "PRESERVE exactly: the complete garment including all fabric texture, color, and construction details; the model's face, body, pose, and expression; the garment's fit and drape on the body; the overall exposure and color temperature on the model."

User input: "mudar cor da blusa pra verde musgo"
GOOD refined_prompt: "Edit this image: change the garment color from the current shade to a deep olive moss green. Maintain the exact same fabric texture, stitch pattern, construction, and draping behavior — only the hue should change."
GOOD preserve_clause: "PRESERVE exactly: the model's face, hair, skin tone, pose, and expression; the garment's fabric texture, weave pattern, fit, and silhouette; the background scene and lighting setup; all accessories and styling."

User input: "adicionar o cachecol do conjunto na modelo." (Scenario A — flat lay reference provided, no person)
GOOD reference_item_description: "From flat lay reference: rectangular knit scarf in vertical olive green and dusty rose stripe crochet pattern, matching the main garment's color DNA. Medium-weight, ~20-25cm wide, long enough to drape over shoulders and fall to waist. Same stitch density and yarn weight as the cardigan."
GOOD refined_prompt: "Edit this image: add a matching knit scarf wrapped once around the model's neck, with the ends falling naturally down the front of her chest over the existing cardigan. The scarf features the same olive green and dusty rose vertical stripe pattern and crochet texture as the cardigan, draping with soft gravity-driven folds. Do not transfer any person identity from any reference image — extract only the described item."
GOOD preserve_clause: "PRESERVE exactly: the model's face, skin tone, and shoulder-length dark brown hair; the white crew-neck cotton t-shirt and white linen shorts; the green and pink striped cardigan's specific knit texture, stripe scale, and fit; the model's standing pose and hand placement; the minimalist light grey background and soft, even studio lighting."

Output valid JSON only."""


def refine_edit_instruction(
    edit_instruction: str,
    source_image_bytes: bytes,
    source_prompt: Optional[str] = None,
    reference_images_bytes: Optional[list] = None,
    category: str = DEFAULT_CREATE_CATEGORY,
) -> dict:
    """
    Analisa instrução de edição do usuário + imagem e retorna prompt refinado.
    """
    prompt_assets = get_generate_prompt_assets(category)
    _hi_res = types.MediaResolution.MEDIA_RESOLUTION_HIGH
    parts = [
        types.Part(
            inline_data=types.Blob(
                mime_type=detect_image_mime(source_image_bytes),
                data=source_image_bytes,
            ),
            media_resolution=_hi_res,
        ),
    ]
    # Incluir imagens de referência se fornecidas
    for ref_bytes in (reference_images_bytes or []):
        parts.append(types.Part(
            inline_data=types.Blob(
                mime_type=detect_image_mime(ref_bytes),
                data=ref_bytes,
            ),
            media_resolution=_hi_res,
        ))

    context = f'User edit instruction: "{edit_instruction}"'
    if source_prompt:
        context += f'\nOriginal generation prompt (for context): "{source_prompt[:500]}"'
    if reference_images_bytes:
        context += (
            f'\nThe user provided {len(reference_images_bytes)} reference image(s). '
            f'CRITICAL: These references may show persons wearing the item. '
            f'DO NOT transfer any person identity (face, skin tone, hair, body shape, pose) from the references. '
            f'Extract ONLY the item\'s visual properties (color, texture, stitch, drape, construction, proportions). '
            f'If the user wants to ADD the item shown in the reference to the original image, classify as set_member '
            f'and describe the item in detail in reference_item_description before writing refined_prompt.'
        )

    # Injetar REFERENCE KNOWLEDGE completo para curadoria com vocabulário técnico
    context += f'\n\n{prompt_assets.reference_knowledge}'

    parts.append(types.Part(text=context))

    try:
        response = client.models.generate_content(
            model=MODEL_AGENT,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
                max_output_tokens=2000,
                safety_settings=SAFETY_CONFIG,
                response_mime_type="application/json",
                response_json_schema=EDIT_ANALYSIS_SCHEMA,
            ),
        )

        raw_text = ""
        if response.candidates:
            for part in (response.candidates[0].content.parts or []):
                if hasattr(part, "text") and part.text:
                    raw_text += part.text

        if raw_text:
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                # Tentar reparar JSON truncado (output cortado por token limit)
                repaired = raw_text.rstrip()
                # Fechar string aberta
                if repaired.count('"') % 2 != 0:
                    repaired += '"'
                # Fechar objeto JSON
                open_braces = repaired.count('{') - repaired.count('}')
                repaired += '}' * max(0, open_braces)
                try:
                    parsed = json.loads(repaired)
                    print(f"[EDIT_AGENT] ⚠️ JSON was truncated, repaired successfully")
                except json.JSONDecodeError:
                    print(f"[EDIT_AGENT] ⚠️ JSON repair failed, raw: {raw_text[:300]}")
                    parsed = {}
        else:
            parsed = {}

    except Exception as e:
        print(f"[EDIT_AGENT] ⚠️ Agent call failed: {e}")
        parsed = {}

    edit_type = parsed.get("edit_type", "general")
    if edit_type not in PRESERVATION_TEMPLATES:
        edit_type = "general"

    refined_prompt = parsed.get("refined_prompt", f"Edit this image: apply the following modification — {edit_instruction}. Keep all other elements unchanged.")
    preserve_clause = parsed.get("preserve_clause") or PRESERVATION_TEMPLATES.get(edit_type, "")
    reference_item_description = parsed.get("reference_item_description") or ""

    # Para set_member: garantir anti-identidade no final do prompt caso o agente tenha esquecido
    if edit_type == "set_member" and reference_item_description:
        anti_identity = "Do not transfer any person identity from any reference image — extract only the described item."
        if anti_identity.lower()[:30] not in refined_prompt.lower():
            refined_prompt = f"{refined_prompt.rstrip('.')}. {anti_identity}"

    # Montar prompt final: refined + preserve
    final_prompt = f"{refined_prompt.rstrip('.')}. {preserve_clause}"
    if len(final_prompt) > 2800:
        final_prompt = final_prompt[:2800].rstrip() + "..."

    confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.5) or 0.5)))

    result = {
        "edit_type": edit_type,
        "refined_prompt": refined_prompt,
        "preserve_clause": preserve_clause,
        "reference_item_description": reference_item_description,
        "change_summary_ptbr": parsed.get("change_summary_ptbr", edit_instruction),
        "confidence": round(confidence, 3),
        "final_prompt": final_prompt,
    }

    ref_desc_log = f" | ref_item={reference_item_description[:60]}…" if reference_item_description else ""
    print(f"[EDIT_AGENT] ✏️ type={edit_type} conf={confidence:.2f}{ref_desc_log}")
    print(f"[EDIT_AGENT] Prompt ({len(final_prompt)} chars): {final_prompt[:200]}{'…' if len(final_prompt) > 200 else ''}")

    return result
