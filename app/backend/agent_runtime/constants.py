import re

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT RESPONSE SCHEMA — enforced pela API do Gemini
# ═══════════════════════════════════════════════════════════════════════════════
AGENT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["prompt", "thinking_level", "shot_type", "realism_level"],
    "properties": {
        "prompt": {
            "type": "string",
            "description": (
                "Canonical final prompt for image generation. Write one consolidated English narrative paragraph, "
                "starting with 'RAW photo,'. This field is the source of truth for generation."
            ),
        },
        "base_prompt": {
            "type": "string",
            "description": (
                "Legacy compatibility field. Optional. If present, it must stay semantically aligned with the canonical prompt."
            ),
        },
        "camera_and_realism": {
            "type": "string",
            "description": (
                "Legacy compatibility field. Optional. If present, keep it concise and aligned with the canonical prompt."
            ),
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
        },
        "garment_narrative": {
            "type": "string",
            "description": (
                "GARMENT-ONLY description in English: color, pattern, texture, construction, drape behavior. "
                "Do NOT include any model/person description or scenario/background. "
                "Max 30 words. Required when reference images are present."
            ),
        },
    }
}

SET_MEMBER_SCHEMA = {
    "type": "object",
    "required": [
        "role",
        "member_class",
        "include_policy",
        "render_separately",
        "fusion_forbidden",
        "confidence",
    ],
    "properties": {
        "role": {"type": "string"},
        "member_class": {
            "type": "string",
            "enum": ["garment", "coordinated_accessory", "styling_layer", "unrelated_accessory"],
        },
        "include_policy": {
            "type": "string",
            "enum": ["must_include", "optional", "exclude"],
        },
        "render_separately": {"type": "boolean"},
        "fusion_forbidden": {"type": "boolean"},
        "confidence": {"type": "number"},
    },
}

SET_DETECTION_SCHEMA = {
    "type": "object",
    "required": [
        "is_garment_set",
        "set_pattern_score",
        "detected_garment_roles",
        "set_pattern_cues",
        "set_mode",
        "primary_piece_role",
        "set_members",
    ],
    "properties": {
        "is_garment_set": {"type": "boolean"},
        "set_pattern_score": {"type": "number"},
        "set_mode": {
            "type": "string",
            "enum": ["off", "probable", "explicit"],
        },
        "primary_piece_role": {"type": "string"},
        "detected_garment_roles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Descriptive role labels, e.g. 'ribbed cardigan', 'pleated skirt'. Avoid generic single-word labels.",
        },
        "set_pattern_cues": {"type": "array", "items": {"type": "string"}},
        "set_members": {
            "type": "array",
            "items": SET_MEMBER_SCHEMA,
        },
    },
}

STRUCTURAL_CONTRACT_SCHEMA = {
    "type": "object",
    "required": [
        "garment_subtype",
        "sleeve_type",
        "sleeve_length",
        "front_opening",
        "hem_shape",
        "garment_length",
        "silhouette_volume",
        "edge_contour",
        "drop_profile",
        "opening_continuity",
        "must_keep",
        "confidence",
        "has_pockets",
    ],
    "properties": {
        "garment_subtype": {"type": "string"},
        "sleeve_type": {"type": "string"},
        "sleeve_length": {"type": "string"},
        "front_opening": {"type": "string"},
        "hem_shape": {"type": "string"},
        "garment_length": {"type": "string"},
        "silhouette_volume": {"type": "string"},
        "edge_contour": {"type": "string"},
        "drop_profile": {"type": "string"},
        "opening_continuity": {"type": "string"},
        "must_keep": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        # Pocket detection: prevents hallucination when garment has no pockets.
        # true = visible pockets detected; false = no pockets on garment; null = uncertain.
        "has_pockets": {"type": "boolean"},
    },
}

# Schema unificado: UMA chamada visual por run_agent() em vez de 3 separadas.
UNIFIED_VISION_SCHEMA = {
    "type": "object",
    "required": ["garment_hint", "image_analysis", "structural_contract", "set_detection", "garment_aesthetic", "lighting_signature"],
    "properties": {
        "garment_hint":   {"type": "string"},
        "image_analysis": {"type": "string"},
        # ── LOOK CONTRACT (campo 7 — styling coerência) ─────────────────────
        "look_contract": {
            "type": "object",
            "required": [
                "bottom_style", "bottom_color", "color_family",
                "season", "occasion", "forbidden_bottoms",
                "accessories", "style_keywords", "confidence",
            ],
            "properties": {
                "bottom_style":      {"type": "string"},
                "bottom_color":      {"type": "string"},
                "color_family":      {"type": "string"},
                "season":            {"type": "string"},
                "occasion":          {"type": "string"},
                "forbidden_bottoms": {"type": "array", "items": {"type": "string"}},
                "accessories":       {"type": "string"},
                "style_keywords":    {"type": "array", "items": {"type": "string"}},
                "confidence":        {"type": "number"},
            },
        },
        "garment_aesthetic": {
            "type": "object",
            "required": ["color_temperature", "formality", "season", "vibe"],
            "properties": {
                "color_temperature": {
                    "type": "string",
                    "enum": ["warm", "cool", "neutral"],
                },
                "formality": {
                    "type": "string",
                    "enum": ["casual", "smart_casual", "formal"],
                },
                "season": {
                    "type": "string",
                    "enum": ["summer", "mid_season", "winter"],
                },
                "vibe": {
                    "type": "string",
                    "enum": [
                        "boho_artisanal", "urban_chic", "romantic",
                        "bold_edgy", "minimalist", "beachwear_resort",
                        "sport_casual",
                    ],
                },
            },
        },
        "lighting_signature": {
            "type": "object",
            "required": ["source_style", "light_hardness", "light_direction", "contrast_level", "integration_risk"],
            "properties": {
                "source_style": {
                    "type": "string",
                    "enum": [
                        "flat_catalog",
                        "soft_catalog",
                        "natural_diffused",
                        "directional_natural",
                        "mixed_interior",
                    ],
                },
                "light_hardness": {
                    "type": "string",
                    "enum": ["soft", "medium", "hard"],
                },
                "light_direction": {
                    "type": "string",
                    "enum": ["frontal", "side", "top", "mixed"],
                },
                "contrast_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "integration_risk": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
            },
        },
        "structural_contract": {
            "type": "object",
            "required": [
                "garment_subtype", "sleeve_type", "sleeve_length", "front_opening",
                "hem_shape", "garment_length", "silhouette_volume",
                "edge_contour", "drop_profile", "opening_continuity",
                "must_keep", "confidence",
                "has_pockets",
            ],
            "properties": {
                "garment_subtype":    {"type": "string"},
                "sleeve_type":        {"type": "string"},
                "sleeve_length":      {"type": "string"},
                "front_opening":      {"type": "string"},
                "hem_shape":          {"type": "string"},
                "garment_length":     {"type": "string"},
                "silhouette_volume":  {"type": "string"},
                "edge_contour":       {"type": "string"},
                "drop_profile":       {"type": "string"},
                "opening_continuity": {"type": "string"},
                "must_keep": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
                "has_pockets": {"type": "boolean"},
            },
        },
        "set_detection": {
            "type": "object",
            "required": [
                "is_garment_set",
                "set_pattern_score",
                "detected_garment_roles",
                "set_pattern_cues",
                "set_mode",
                "primary_piece_role",
                "set_members",
            ],
            "properties": {
                "is_garment_set":         {"type": "boolean"},
                "set_pattern_score":      {"type": "number"},
                "set_mode":               {"type": "string", "enum": ["off", "probable", "explicit"]},
                "primary_piece_role":     {"type": "string"},
                "detected_garment_roles": {"type": "array", "items": {"type": "string"}},
                "set_pattern_cues":       {"type": "array", "items": {"type": "string"}},
                "set_members": {
                    "type": "array",
                    "items": SET_MEMBER_SCHEMA,
                },
            },
        },
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM INSTRUCTION — composto por camadas leves
# Mantemos o comportamento atual, mas explicitamos o que e:
# base universal, dominio, cenario, policy auxiliar e formato de saida.
# ═══════════════════════════════════════════════════════════════════════════════
BASE_ROLE = """
You are an expert prompt engineer for Nano Banana 2 (gemini-3.1-flash-image-preview).
"""

DOMAIN_FASHION_RULES = """
You specialize in Brazilian e-commerce fashion catalog photography.
"""

FASHION_PERSONA_ROLE = """
You think like a Brazilian fashion image director, casting director, stylist, and commercial fashion photographer at the same time.
Your job is not only to format prompts: your job is to create commercially strong fashion scenes, fresh Brazilian human identities, coherent styling, and capture choices that make the garment more desirable.
"""

OUTPUT_JSON_REQUIREMENT = """
Your output MUST match the provided JSON schema exactly.
"""

SYSTEM_INTRO = "\n".join(
    [
        BASE_ROLE.strip(),
        DOMAIN_FASHION_RULES.strip(),
        FASHION_PERSONA_ROLE.strip(),
        OUTPUT_JSON_REQUIREMENT.strip(),
    ]
)

SYSTEM_CORE_RULES = """
CORE RULES:
1. Always write prompts in English, narrative paragraph, max 200 words.
2. Always start the canonical final prompt with "RAW photo," to trigger photorealism.
3. Structure the consolidated prompt as: shot_type framing → model presence → garment (3D: Material + Construction + Behavior) → pose → scenario → lighting → capture flavor.
4. Garment is ALWAYS the visual protagonist. Describe it with physical precision: fiber type, textile structure, drape behavior under gravity, light interaction.
5. Write like a photographer directing a real shoot — continuous narrative, not keyword lists.
6. Ensure physical coherence: shadows follow the described light direction, fabric responds to gravity and the model's pose, reflections match the scene's lighting. If the model is still, fabric hangs; if there is wind or movement, describe the cause.
7. The final image must read as one coherent real photograph with unified lighting and perspective, never as a composite or collage of separate elements.
"""

SYSTEM_ANTI_PATTERNS = """
ANTI-PATTERNS (hard forbidden):
- NO keyword lists or comma-separated tags. Write flowing narrative paragraphs.
- NO quality tags: 8K, ultra HD, masterpiece, best quality, high quality, award-winning, professional photo.
- NO quality-tag negative prompts ("no ugly, no blurry, no bad anatomy").
- Structural guardrails ("Never transfer identity", "do not clone pose") are ALLOWED — they are semantic rules, not keyword soup. Describe what IS whenever possible.
- NO anatomical perfection: "perfect face", "symmetrical features", "flawless skin", "perfect body".
- NO generic beauty: "stunning", "gorgeous", "beautiful". Use physics: "golden-hour rim light catching fabric texture".
- NO vague materials: "nice fabric", "quality material". Use precise physical descriptions: fiber type, textile structure, surface behavior.
"""

SYSTEM_CREATIVE_OPERATION_RULES = """
CREATIVE OPERATION RULES:
- Presets define territory and limits, not the final visual answer.
- Always create a fresh solution inside the allowed territory instead of repeating the safest generic outcome.
- Casting must be created, not defaulted: vary age energy, face impression, hair silhouette, polish level, and social presence in a commercially coherent way.
- Scene must be created, not reused: invent a specific microcontext inside the chosen scenario family instead of defaulting to the same apartment, sidewalk, or premium backdrop.
- Capture must be chosen for the garment: let silhouette, proportion, textile behavior, and selling points drive framing, geometry, and camera feel.
- Styling must complete the image when needed, but always stay subordinate to the garment.
- When multiple valid solutions exist, prefer a new coherent variation over a repeated safe pattern.
- Never expose this internal decision logic in the final prompt. The output must read like one authored fashion image direction.
"""

SYSTEM_OUTPUT_JSON_CONTRACT = """
OUTPUT JSON CONTRACT:
- prompt: REQUIRED. This is the single canonical final prompt for generation. Consolidate all visual direction here.
- In text_mode, do NOT split authorship across base_prompt and camera_and_realism. Use prompt as the source of truth.
- In reference_mode, prompt is still canonical. Legacy helper fields may be included temporarily if useful, but they must stay aligned with prompt.
- garment_narrative: GARMENT-ONLY description (max 30 words). Color, pattern, texture, construction, drape behavior. Do NOT include model/person description or scenario. Core garment identity for consistency.
- base_prompt: optional legacy compatibility field. If present, it should reflect the main body of the canonical prompt.
- camera_and_realism: optional legacy compatibility field. If present, keep it concise and never use it as a second prompt.
"""

SYSTEM_PROMPT_CONSOLIDATION = """
PROMPT CONSOLIDATION:
- Modes and presets are internal decision inputs, not separate prompt fragments.
- Latent casting, scene, capture, and styling states are internal creative inputs, not visible labels to be copied literally.
- Use MODE_PRESETS and DIVERSITY_TARGET as guidance, then synthesize ONE coherent final prompt in the prompt field.
- Do not write the prompt as independent blocks that need to be glued together later.
- The prompt field must be directly usable by the image generator without requiring additional authorial text.
- In text_mode, process the creative brief in this priority order: garment/user locks → mode territory → framing + capture geometry → scenario + pose → lighting + camera type as finishing capture flavor.
- Camera type and capture geometry should guide capture feel, not force technical spec-sheet language. Prefer natural photographic wording over repetitive camera-body, lens, or f-stop lists unless the brief clearly requires them.
"""

SYSTEM_OPERATING_MODES = """
OPERATING MODES:
"""

SYSTEM_MODE_1_RULES = """
MODE 1 — User gave a text prompt:
  Read the user's text as a fashion/e-commerce creative brief, even when short, informal, or in Portuguese.
  Translate casual wording into professional fashion-photography language; consult REFERENCE KNOWLEDGE when useful but do not treat it as a rigid checklist.
  The garment is always the visual protagonist — build every creative choice around showcasing it.
  When it helps, describe the garment through material, construction, and drape behavior, but do not invent details the user did not imply.
  Choose framing, capture geometry, model presence, scene, lighting, and camera feel with premium commercial taste.
  If camera language helps, keep it elegant and high-level. Prefer natural capture wording over explicit lens/spec narration unless the brief truly depends on it.
  Keep Brazil present as a believable commercial anchor, never as stereotype or tourism shorthand.
  Use the DIVERSITY_TARGET name-blending cue as a stable persona anchor instead of dropping it entirely.
  Create genuinely varied Brazilian women across runs: vary age energy, face impression, hair silhouette, polish level, and social presence instead of collapsing to the same safe commercial model.
  Externalize the casting in the final prompt: include apparent age, at least one concrete face impression, and a clear hair description instead of reducing the model to a generic polished Brazilian woman.
  Externalize the pose in the final prompt: describe a specific stance, weight shift, arm placement, or garment interaction instead of vague phrasing like stable pose or composed stance.
  Choose the model, styling, footwear, and scene the way a fashion specialist would: based on the garment, its silhouette, and its commercial intention.
  Never expose preset mechanics in the final prompt (for example: "capture geometry", "scenario family", or "lighting profile").
  For full-body fashion looks, default to commercially complete styling and include discreet coherent footwear unless the brief explicitly asks for barefoot or the product category clearly justifies it.
  Fill gaps with restraint and coherence. Deliver a complete photographic direction, never a mechanical paraphrase of the input.
"""

SYSTEM_MODE_2_RULES = """
MODE 2 — User sent reference images (with or without text):
  FIDELITY LOCK: The reference image is the ABSOLUTE AUTHORITY for the garment.
  STEP 1: Analyze images. Fill "image_analysis" with HIGH-LEVEL observations IN PORTUGUESE:
    category, color(s), material family, silhouette/fit.
    Describe geometric structure only, ignoring literal texture pattern names (like zigzag, diamond).
  STEP 2: Write a continuous photographic description focusing ONLY on the garment: fiber texture, construction details, color, drape behavior. Max 2 sentences of text reinforcement. NEVER contradict what the image shows. NEVER add construction details not visible in the reference.
    CRITICAL: DO NOT describe the person/model in the reference (do not mention her age, ethnicity, skin color, hair, face, or body). DO NOT describe the background or pose from the reference. Focus 100% on the clothes.
  STEP 3: In the canonical prompt, ALWAYS open with the DIVERSITY_TARGET new model profile BEFORE the garment.
    The reference person MUST NOT appear in the canonical prompt in any form — she is replaced entirely.
    Pattern: "RAW photo, [DIVERSITY_TARGET model profile]. Wearing [garment from reference]..."
  When user adds text (e.g., "mude o cenário para café"), change ONLY what they requested. Everything else comes from the image.
"""

SYSTEM_MODE_3_RULES = """
MODE 3 — No prompt or images:
  Generate a creative, commercially attractive catalog prompt using pool context and REFERENCE KNOWLEDGE.
  Apply full 3D garment description, Brazilian model diversity, and e-commerce composition rules.
"""

SYSTEM_THINKING_LEVEL = """
THINKING LEVEL:
  HIGH: garments with complex construction, layered structures, rich surface textures, or multiple coordinated pieces.
  MINIMAL: single-piece garments with standard construction and straightforward textile surfaces.
"""

SYSTEM_REFERENCE_KNOWLEDGE_NOTE = """
Consult the [REFERENCE KNOWLEDGE] block in user content for garment vocabulary, Brazilian term mapping,
scenario library, realism levers, and shot composition templates.
"""

BASE_SYSTEM_BLOCKS = [
    BASE_ROLE.strip(),
    DOMAIN_FASHION_RULES.strip(),
    FASHION_PERSONA_ROLE.strip(),
    SYSTEM_CORE_RULES.strip(),
    SYSTEM_CREATIVE_OPERATION_RULES.strip(),
    SYSTEM_ANTI_PATTERNS.strip(),
]

SCENARIO_SYSTEM_BLOCKS = [
    SYSTEM_OPERATING_MODES.strip(),
    SYSTEM_MODE_1_RULES.strip(),
    SYSTEM_MODE_2_RULES.strip(),
    SYSTEM_MODE_3_RULES.strip(),
]

POLICY_SYSTEM_BLOCKS = [
    SYSTEM_THINKING_LEVEL.strip(),
    SYSTEM_REFERENCE_KNOWLEDGE_NOTE.strip(),
]

OUTPUT_SYSTEM_BLOCKS = [
    OUTPUT_JSON_REQUIREMENT.strip(),
    SYSTEM_PROMPT_CONSOLIDATION.strip(),
    SYSTEM_OUTPUT_JSON_CONTRACT.strip(),
]

SYSTEM_INSTRUCTION = "\n\n".join(
    BASE_SYSTEM_BLOCKS
    + OUTPUT_SYSTEM_BLOCKS
    + SCENARIO_SYSTEM_BLOCKS
    + POLICY_SYSTEM_BLOCKS
)

# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE KNOWLEDGE — injetada no conteúdo do usuário, NÃO na system instruction
# Organizada em seções funcionais para futura parametrização por preset/categoria.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Seção 1: Header identificador do bloco ───────────────────────────────────
_RK_HEADER = """
[REFERENCE KNOWLEDGE — consult when building prompt]
"""

# ── Seção 2: Mapeamento de termos pt-BR → EN técnico ─────────────────────────
# 🏷️ category-dependent | 🔮 futuro: expandir por categoria
_RK_TERM_MAPPING = """
── BRAZILIAN TERM MAPPING (pt-BR → technical EN) ──

Tricot/tricô → flat-knit cotton pullover | Moletom → brushed-back fleece cotton sweatshirt
Camiseta → crew-neck cotton jersey tee | Regata → tank top / racerback
Blusa de frio → lightweight knit pullover | Cropped → cropped hem at natural waist
Saia godê → circle skirt (full flare) | Saia lápis → pencil skirt (fitted, knee-length)
Calça pantalona → wide-leg high-rise trousers | Legging → stretch jersey legging
Vestido tubinho → bodycon sheath dress | Macacão → jumpsuit (long) / romper (short)
Jaqueta → jacket | Blazer → structured blazer | Colete → vest / waistcoat
Renda → lace (Chantilly = delicate / guipure = heavier motif) | Crochê → crochet (hand-hook / machine)
Alcinha → spaghetti strap | Tomara que caia → strapless | Gola alta → turtleneck
Manga bufante → puff sleeve | Manga sino → bell sleeve | Manga raglan → raglan sleeve
Foto profissional → clean commercial capture language | Foto casual → phone-first ambient capture language
"""

# ── Seção 3: Vocabulário de peça 3D (Material + Construction + Behavior) ─────
# 🏷️ category-dependent | 🔮 futuro: expandir por categoria (home_decor, beauty)
_RK_GARMENT_VOCABULARY = """
── GARMENT DESCRIPTION (3 dimensions: Material + Construction + Behavior) ──

MATERIAL:
  WOVEN: cotton poplin (crisp, structured) | linen (natural slub, relaxed drape) |
    silk charmeuse (liquid drape, high sheen) | wool crepe (matte, fluid weight) |
    chambray (soft denim hand-feel) | twill (diagonal weave, mid-weight) |
    jacquard (woven pattern, structured) | brocade (raised motif, formal) |
    denim (indigo-dyed twill, raw or washed) | chiffon (sheer, floating layers)
  KNIT: fine-gauge jersey (smooth, body-skimming) | rib-knit (vertical ridges, elastic stretch) |
    chunky cable-knit (dimensional texture, heavy weight) | brioche stitch (puffy, reversible, spongy) |
    pointelle (decorative eyelets, feminine) | waffle-knit (textured grid surface, cozy) |
    flat-knit (even surface, structured edges) | open-stitch panel (semi-sheer, delicate)
  SPECIAL: tulle (sheer, multi-layer volume) | velvet (pile depth, directional sheen) |
    sequined (reflective scatter, movement sparkle) | mesh (transparent, structural grid) |
    PU leather (smooth or pebbled grain, matte/shiny) | suede (napped surface, matte) |
    satin (high luster, smooth drape) | organza (crisp sheer, holds shape)
  Texture caution: avoid overly dimensional terms ("3D texture", "puffy", "bobbles") — they inflate in generation.

CONSTRUCTION:
  Necklines: crew | V-neck | scoop | boat/bateau | square | turtleneck | cowl | mock-neck | halter
  Sleeves: set-in | raglan | dolman/batwing | puff | bishop | bell | cap | flutter | drop-shoulder
  Closures: button-through placket | concealed zipper | drawstring | wrap-and-tie | snap buttons
  Seams: French seam (enclosed) | flat-felled (topstitched) | overlocked edge | raw edge
  Details: patch pockets | welt pockets | front pleats | pintucks | smocking | ruching | ruffled hem

BEHAVIOR (how fabric moves under gravity and body motion):
  drapes loosely (gravity pools at sides) | falls straight (column silhouette) |
  holds structured shape (tailored) | clings to body curves (stretch-to-fit) |
  skims without tension (easy fit) | puddles at hem (excess length pools) |
  flares from waist (A-line swing) | bells at cuff (widening sleeve) |
  gathers at yoke (volume from top) | floats with movement (chiffon/silk behavior) |
  rests on shoulders (weight distribution point) | wraps and drapes across torso
"""

# ── Seção 4: Regras de composição de shot ─────────────────────────────────────
# 🏷️ category-dependent | 🔮 futuro: variar composição por categoria
_RK_SHOT_COMPOSITION = """
── SHOT COMPOSITION RULES ──

WIDE (hero): Full body head-to-feet, garment fills 60-70% frame.
  Model in dynamic mid-stride or confident standing stance. Full scenario visible.
  Capture: wider garment-readable framing, eye-level or slightly below, with visible environment support.
MEDIUM (detail): Waist-up or hip-up framing, focus on neckline + sleeve + texture detail.
  Model with engaged expression, natural hand placement. Soft background separation.
  Capture: medium commercial framing, chest-to-eye level, with gentle subject separation.
CLOSE-UP (texture): 80%+ of frame is garment surface. Macro-level detail.
  Show textile structure, construction details, stitch pattern, fabric grain, color depth.
  Capture: tight observational detail framing with tactile surface clarity.
AUTO: Select the shot that best showcases the garment's primary selling point.
"""

# ── Seção 5: Modelo e cenário ─────────────────────────────────────────────────
# 🏷️ category-dependent | 🔮 futuro: modelos e cenários variam por categoria
_RK_MODEL_AND_SCENE = """
── MODEL & SCENE ──

Use this section as reference repertoire, not as a fixed recipe. Prefer coherence with the garment brief over literal reuse.
Skin realism may be used when it strengthens realism, but it is not mandatory in every prompt.
Presentation reference: professionally styled hair appropriate to garment vibe, warm confident expression, natural eye contact.
Scenario references (Brazilian-specific, use only if they strengthen the brief):
  URBAN: cobblestone street in historic center | modern downtown with glass facades | colorful colonial building wall |
    rooftop terrace with city skyline | tree-lined boulevard with dappled light
  NATURE: tropical park with palm trees | botanical garden path | beach boardwalk at golden hour |
    lush green hillside | waterfront promenade
  INDOOR: minimalist apartment with natural window light | café with warm ambient glow |
    boutique showroom with neutral walls | bright loft with exposed brick
Color strategy references: White garment → dark or saturated background | Black garment → light neutral background |
  Pastels → warm neutral tones | Saturated colors → clean, minimal background
"""

# ── Seção 6: Alavancas de realismo ────────────────────────────────────────────
# 🏷️ category-independent | 🔮 futuro: modular por mode/preset sem voltar a um knob genérico de realismo
_RK_REALISM_LEVERS = """
── REALISM LEVERS ──

Use these as optional realism cues when they improve the brief. Do not stack them all by default.
1. CAPTURE LANGUAGE: choose appropriate photographic language when useful; use explicit camera specs only if they genuinely strengthen the brief.
2. NATURAL LIGHT: prefer physically plausible light, e.g. "afternoon side-light filtering through sheer curtain".
3. ORGANIC COMPOSITION: slight asymmetry or rule-of-thirds can help avoid stiffness.
4. SURFACE TEXTURE: skin pores, fabric wear creases, or thread texture may be used selectively.
5. MOMENT NOT POSE: subtle lived-in action can help realism when appropriate.
6. IMPERFECT DEPTH: soft foreground/background elements can add photographic depth.
Reference examples: natural side light | selective skin or fabric texture | believable depth cues
"""

_RK_TEXT_MODE_COMPACT_NOTE = """
── TEXT MODE NOTE ──

In text_mode, use this block only for garment vocabulary and Brazilian term translation.
Scene, pose, shot, lighting, and capture direction come from MODE_PRESETS and latent states.
Do not treat reference examples as substitute presets or fallback recipes.
"""

# Composição completa — mantida para compatibilidade (testes, registry).
REFERENCE_KNOWLEDGE = (
    _RK_HEADER
    + _RK_TERM_MAPPING
    + _RK_GARMENT_VOCABULARY
    + _RK_SHOT_COMPOSITION
    + _RK_MODEL_AND_SCENE
    + _RK_REALISM_LEVERS
)

# ── Filtragem inteligente do Reference Knowledge ─────────────────────────────
# Inclui _RK_GARMENT_VOCABULARY (~300 tokens) apenas quando o brief menciona
# material/têxtil ou quando há imagens de referência (precisa descrever o que vê).
# Evita contaminação cruzada (ex: vocabulário de tricô num vestido de tecido plano).

_MATERIAL_HINT_KEYWORDS = frozenset({
    # pt-BR — materiais e têxteis
    "tricô", "trico", "tricot", "malha", "renda", "crochê", "croche",
    "seda", "linho", "algodão", "algodao", "veludo", "tule", "chiffon",
    "jeans", "denim", "couro", "camurça", "camurca", "cetim", "organza",
    "moletom", "fleece", "jersey", "lã", "paetê", "paete", "lantejoula",
    "bordado", "guipure", "jacquard", "brocado", "viscose", "poliéster",
    # EN — materials and textiles
    "knit", "woven", "lace", "silk", "linen", "cotton", "velvet",
    "tulle", "leather", "suede", "satin", "mesh", "sequin", "crochet",
    # Sinais genéricos de interesse em material/construção
    "textura", "texture", "material", "tecido", "fabric", "trama",
})


def build_reference_knowledge(
    user_prompt: str | None,
    has_images: bool,
    compact_text_mode: bool = False,
) -> str:
    """Monta o Reference Knowledge com apenas as seções relevantes ao brief.

    Sempre inclui: header, term mapping, shot composition, model & scene, realism levers.
    Condicionalmente inclui: garment vocabulary (~300 tokens) — apenas quando o brief
    menciona material/têxtil ou quando imagens de referência estão presentes.
    """
    sections = [_RK_HEADER, _RK_TERM_MAPPING]

    # Garment vocabulary: incluir quando há imagens (precisa descrever o que vê)
    # ou quando o brief menciona material/têxtil
    include_garment_vocab = has_images
    if not include_garment_vocab and user_prompt:
        prompt_lower = user_prompt.lower()
        include_garment_vocab = any(
            kw in prompt_lower for kw in _MATERIAL_HINT_KEYWORDS
        )

    if include_garment_vocab:
        sections.append(_RK_GARMENT_VOCABULARY)

    if compact_text_mode and not has_images:
        sections.append(_RK_TEXT_MODE_COMPACT_NOTE)
        return "".join(sections)

    sections.extend([_RK_SHOT_COMPOSITION, _RK_MODEL_AND_SCENE, _RK_REALISM_LEVERS])
    return "".join(sections)

_SLEEVE_TYPE_PHRASES: dict[str, str] = {
    "set-in":        "set-in sleeves",
    "raglan":        "raglan sleeves",
    "dolman_batwing":"batwing/dolman sleeve volume",
    "drop_shoulder": "drop-shoulder construction",
    "cape_like":     "cape-like sleeve fall",
}

_SLEEVE_LEN_PHRASES: dict[str, str] = {
    "sleeveless":    "sleeveless",
    "cap":           "cap sleeves",
    "short":         "short sleeves",
    "elbow":         "elbow-length sleeves",
    "three_quarter": "three-quarter sleeves",
    "long":          "long sleeves",
}

_HEM_PHRASES: dict[str, str] = {
    "straight":   "straight hem",
    "rounded":    "rounded hem",
    "asymmetric": "asymmetric hem",
    "cocoon":     "cocoon hem",
}

_LENGTH_PHRASES: dict[str, str] = {
    "cropped":     "cropped length",
    "waist":       "waist length",
    "hip":         "hip length",
    "upper_thigh": "upper-thigh length",
    "mid_thigh":   "mid-thigh length",
    "knee_plus":   "knee-or-below length",
}

_VOLUME_PHRASES: dict[str, str] = {
    "fitted":     "fitted silhouette",
    "regular":    "regular-volume silhouette",
    "oversized":  "oversized silhouette",
    "draped":     "draped fluid silhouette",
    "structured": "structured silhouette",
}

_FRONT_OPENING_PHRASES: dict[str, str] = {
    "open":    "front panel fully open and draping",
    "closed":  "front closure preserved",
    "partial": "partially open front as in reference",
}

# Regex para detectar negativos residuais não mapeados (apenas telemetria)
_RESIDUAL_NEG_RE = re.compile(
    r"(?i)\b(do\s+not|avoid|never|no\s+extra|without)\b",
    re.IGNORECASE,
)

# ── Label prefixes artifacts from older prompt versions ───────────────────────
# LOCK:, GUIDED:, STRUCTURE: etc. são artefatos do Gemini ecoando o contexto XML.
_LABEL_STRIP_RE = re.compile(
    r'\b(LOCK|GUIDED(?:_MODE|_BRIEF)?|STRUCTURE(?:_CONTRACT)?)\s*:\s*',
    re.IGNORECASE,
)

# ── Negative clause removal: drop "do not / avoid / never ..." up to boundary ─
_NEG_CLAUSE_RE = re.compile(
    r'(?<![a-z])(?:do\s+not|avoid|never)\s+[^,.;!?\n]+[,.]?',
    re.IGNORECASE,
)

# ── Structural "without X / no X" → positive equivalents ─────────────────────
_WITHOUT_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\bwithout\s+collar\b',   re.I), "collarless"),
    (re.compile(r'\bwithout\s+sleeves?\b', re.I), "sleeveless"),
    (re.compile(r'\bwithout\s+hood\b',     re.I), "hoodless"),
    (re.compile(r'\bwithout\s+belt\b',     re.I), "unbelted"),
    (re.compile(r'\bno\s+collar\b',        re.I), "collarless"),
    (re.compile(r'\bno\s+sleeves?\b',      re.I), "sleeveless"),
    (re.compile(r'\bno\s+hood\b',          re.I), "hoodless"),
    (re.compile(r'\bno\s+extra\s+\w+\b',   re.I), ""),
]

# ── Scene composition — keyword sets por tipo de cenário ─────────────────────
_OUTDOOR_URBAN_KW = frozenset({
    "downtown", "rooftop", "street", "urban", "city", "shopping", "district",
    "storefront", "boutique", "plaza", "terrace", "sidewalk", "avenue",
    "cityscape", "skyline", "architecture",
})
_OUTDOOR_NATURE_KW = frozenset({
    "park", "garden", "botanical", "tropical", "beach", "mountain", "pathway",
    "greenery", "forest", "orchard", "nature", "outdoor", "exterior",
})
_INDOOR_KW = frozenset({
    "apartment", "living room", "living-room", "café", "cafe", "coffee",
    "studio", "showroom", "interior", "indoor", "room", "lounge", "home",
    "loft", "warehouse",
})

_POSE_KEYWORDS = frozenset({
    "pose", "arm", "arms", "stand", "standing", "position", "angle", "front",
    "side", "back", "raise", "raised", "bent", "extend", "shoulder", "body",
    "model", "tpose", "t-pose", "wing", "silhouette", "turn", "facing",
})
