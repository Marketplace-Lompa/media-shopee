import re

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT RESPONSE SCHEMA — enforced pela API do Gemini
# ═══════════════════════════════════════════════════════════════════════════════
AGENT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["base_prompt", "camera_and_realism", "thinking_level", "shot_type", "realism_level"],
    "properties": {
        "base_prompt": {
            "type": "string",
            "description": "Main prompt body focused on garment, model, pose, and scene. Must start with 'RAW photo,' and should avoid camera metadata."
        },
        "camera_and_realism": {
            "type": "string",
            "description": "Camera and realism clause only (device/lens/light/skin/fabric realism). Keep concise and affirmative."
        },
        "prompt": {
            "type": "string",
            "description": "Legacy field for backward compatibility. When present, full prompt in one string."
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
# SYSTEM INSTRUCTION — concisa, comportamental (regras + modos)
# ═══════════════════════════════════════════════════════════════════════════════
SYSTEM_INSTRUCTION = """
You are an expert prompt engineer for Nano Banana 2 (gemini-3.1-flash-image-preview).
You specialize in Brazilian e-commerce fashion catalog photography.
Your output MUST match the provided JSON schema exactly.

CORE RULES:
1. Always write prompts in English, narrative paragraph, max 200 words.
2. Always start base_prompt with "RAW photo," to trigger photorealism.
3. Structure: shot_type framing → model description → garment (3D: Material + Construction + Behavior) → pose → scenario → lighting → realism levers.
4. Garment is ALWAYS the visual protagonist. Describe it with physical precision: fiber type, weave/knit structure, drape behavior under gravity, light interaction.
5. Write like a photographer directing a real shoot — continuous narrative, not keyword lists.

ANTI-PATTERNS (hard forbidden):
- NO keyword lists or comma-separated tags. Write flowing narrative paragraphs.
- NO quality tags: 8K, ultra HD, masterpiece, best quality, high quality, award-winning, professional photo.
- NO quality-tag negative prompts ("no ugly, no blurry, no bad anatomy").
- Structural guardrails ("Never transfer identity", "do not clone pose") are ALLOWED — they are semantic rules, not keyword soup. Describe what IS whenever possible.
- NO anatomical perfection: "perfect face", "symmetrical features", "flawless skin", "perfect body".
- NO generic beauty: "stunning", "gorgeous", "beautiful". Use physics: "golden-hour rim light catching fabric texture".
- NO vague materials: "nice fabric", "quality material". Use specific: "brushed-back fleece cotton" or "fine-gauge rib-knit".

OUTPUT JSON CONTRACT:
- base_prompt: shot framing + model persona (from DIVERSITY_TARGET) + garment narrative (3D) + pose + scene + lighting. INCLUDE the model profile from DIVERSITY_TARGET here.
- garment_narrative: GARMENT-ONLY description (max 30 words). Color, pattern, texture, construction, drape behavior. Do NOT include model/person description or scenario. Used by compiler to preserve garment details.
- camera_and_realism: ONLY camera body/lens/lighting/DOF/texture realism. NEVER put model persona or beauty descriptions here — those belong in base_prompt.
- prompt: optional legacy field; include only if needed.

OPERATING MODES:

MODE 1 — User gave a text prompt:
  You are TRANSLATING user intent into a technically precise photographic prompt.
  STEP 1: Identify the garment type, model request, and scene intent (even if vague or in Portuguese).
  STEP 2: Map casual/Portuguese terms to technical English using REFERENCE KNOWLEDGE.
    Examples: "tricot" → "flat-knit cotton pullover", "moletom" → "brushed-back fleece sweatshirt",
    "rua bonita" → specific Brazilian urban scene with time-of-day lighting,
    "foto profissional" → specific camera body + lens + realism level.
  STEP 3: Apply 3D garment description: Material (fiber + weave/knit) + Construction (seams, closures, silhouette) + Behavior (how it drapes, moves, catches light).
  STEP 4: Add appropriate realism levers and camera settings for the shot type.
  STEP 5: If user didn't specify shot_type, infer from context (full outfit = wide, garment detail = medium, texture = close-up).
  Output MUST be a complete photographic direction, never a paraphrase of the user's words.

MODE 2 — User sent reference images (with or without text):
  FIDELITY LOCK: The reference image is the ABSOLUTE AUTHORITY for the garment.
  STEP 1: Analyze images. Fill "image_analysis" with HIGH-LEVEL observations IN PORTUGUESE:
    category, color(s), material family, silhouette/fit.
    Describe geometric structure only, ignoring literal texture pattern names (like zigzag, diamond).
  STEP 2: Write a continuous photographic description focusing ONLY on the garment: fiber texture, construction details, color, drape behavior. Max 2 sentences of text reinforcement. NEVER contradict what the image shows. NEVER add construction details not visible in the reference.
    CRITICAL: DO NOT describe the person/model in the reference (do not mention her age, ethnicity, skin color, hair, face, or body). DO NOT describe the background or pose from the reference. Focus 100% on the clothes.
  STEP 3: In base_prompt, ALWAYS open with the DIVERSITY_TARGET new model profile BEFORE the garment.
    The reference person MUST NOT appear in base_prompt in any form — she is replaced entirely.
    Pattern: "RAW photo, [DIVERSITY_TARGET model profile]. Wearing [garment from reference]..."
  When user adds text (e.g., "mude o cenário para café"), change ONLY what they requested. Everything else comes from the image.

MODE 3 — No prompt or images:
  Generate a creative, commercially attractive catalog prompt using pool context and REFERENCE KNOWLEDGE.
  Apply full 3D garment description, Brazilian model diversity, and e-commerce composition rules.

REALISM CALIBRATION (maps to realism_level):
  1 (Clean catalog): Controlled studio-like lighting, minimal imperfections, commercial clean. Use for flat catalog, Mercado Livre compliance.
  2 (Natural professional): Subtle natural light variation, visible skin texture, natural fabric wear creases. Default for e-commerce.
  3 (Organic/UGC): Phone-like capture feel, ambient imperfections, moment-between-poses energy, environmental grain. Use for UGC presets.

THINKING LEVEL:
  HIGH: complex knitwear, crochet, multi-layer, macro texture, 3+ pieces, sequins/metallic, lace over lining.
  MINIMAL: solid fabrics, simple garments, clean lifestyle shots.

Consult the [REFERENCE KNOWLEDGE] block in user content for garment vocabulary, Brazilian term mapping,
scenario library, realism levers, and shot composition templates.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE KNOWLEDGE — injetada no conteúdo do usuário, NÃO na system instruction
# ═══════════════════════════════════════════════════════════════════════════════
REFERENCE_KNOWLEDGE = """
[REFERENCE KNOWLEDGE — consult when building prompt]

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
Foto profissional → Sony A7III + 85mm f/1.8 + natural light | Foto casual → phone-like capture, ambient light

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
  Knitwear caution: avoid "crochet loops", "3D texture", "puffy", "bobbles" — they inflate in generation.

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

── SHOT COMPOSITION RULES ──

WIDE (hero): Full body head-to-feet, garment fills 60-70% frame.
  Model in dynamic mid-stride or confident standing stance. Full scenario visible.
  Camera: 50mm lens, f/2.8, eye-level or slightly below for presence. Include ambient environment.
MEDIUM (detail): Waist-up or hip-up framing, focus on neckline + sleeve + texture detail.
  Model with engaged expression, natural hand placement. Soft background separation.
  Camera: 85mm lens, f/1.8, chest-level, shallow DOF isolates garment detail.
CLOSE-UP (texture): 80%+ of frame is garment surface. Macro-level detail.
  Show weave/knit structure, button craftsmanship, stitch pattern, fabric grain, color depth.
  Camera: 100mm macro lens, f/2.8, tight crop, fiber-level sharpness.
AUTO: Select the shot that best showcases the garment's primary selling point.

── MODEL & SCENE ──

Skin realism: visible natural pores on nose bridge and cheeks, subtle peach fuzz on jawline, unretouched skin texture.
Presentation: professionally styled hair appropriate to garment vibe, warm confident expression, natural eye contact.
Scenarios (Brazilian-specific):
  URBAN: cobblestone street in historic center | modern downtown with glass facades | colorful colonial building wall |
    rooftop terrace with city skyline | tree-lined boulevard with dappled light
  NATURE: tropical park with palm trees | botanical garden path | beach boardwalk at golden hour |
    lush green hillside | waterfront promenade
  INDOOR: minimalist apartment with natural window light | café with warm ambient glow |
    boutique showroom with neutral walls | bright loft with exposed brick
Color strategy: White garment → dark or saturated background | Black garment → light neutral background |
  Pastels → warm neutral tones | Saturated colors → clean, minimal background

── REALISM LEVERS ──

1. DEVICE+LENS: Specify real camera body and lens. "Sony A7III, 85mm f/1.8" — never "professional camera".
2. NATURAL LIGHT: "afternoon side-light filtering through sheer curtain" — never "perfect studio lighting".
3. ORGANIC COMPOSITION: Slight asymmetry, model offset to rule-of-thirds. Not dead center.
4. SURFACE TEXTURE: "visible pores on nose bridge", "natural fabric wear creases at elbow fold".
5. MOMENT NOT POSE: "caught adjusting collar" or "mid-laugh with eyes crinkling" — never "perfect pose".
6. IMPERFECT DEPTH: "foreground plant leaf slightly soft" adds photographic dimension.
7. CAPTURE ARTIFACTS: "subtle natural lens vignette", "barely perceptible chromatic fringe at high-contrast edges".
Anchor phrase: DEVICE="Sony A7III, 85mm f/1.8" | SKIN="visible pores, peach fuzz" | FABRIC="natural wear creases, thread texture"
"""

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

# MT4 — Catalog-safe micro-variation stances for force_cover_defaults mode.
# All five keep the model standing with full garment visibility; only the body
# angle, weight distribution, or arm position varies to break rigidity across
# consecutive reference-mode generations.
_CATALOG_STANCE_POOL = [
    "balanced frontal stance, arms natural, garment front fully readable",
    "subtle 3/4 angle toward camera, weight on back foot, front panel clear",
    "gentle step forward, relaxed arms, confident gaze, garment fully visible",
    "contrapposto hip shift, relaxed shoulders, catalog-clean front reveal",
    "slight body turn with direct eye contact, clean garment silhouette",
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
