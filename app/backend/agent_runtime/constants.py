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
    "required": ["garment_hint", "image_analysis", "structural_contract", "set_detection", "garment_aesthetic"],
    "properties": {
        "garment_hint":   {"type": "string"},
        "image_analysis": {"type": "string"},
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
3. Structure: shot_type framing → model description → garment (3D) → pose → scenario → camera → realism levers.
4. Exclude quality tags: 8K, ultra HD, masterpiece, best quality.
5. Garment is ALWAYS the visual protagonist.

OUTPUT JSON CONTRACT:
- base_prompt: shot framing + model persona (from DIVERSITY_TARGET) + garment narrative + scene. INCLUDE the model profile from DIVERSITY_TARGET here.
- garment_narrative: GARMENT-ONLY description (max 30 words). Color, pattern, texture, construction, drape. Do NOT include model/person description or scenario. This field is used by the compiler to preserve garment details when assembling the final prompt.
- camera_and_realism: ONLY camera body/lens/lighting/DOF/texture realism. NEVER put model persona or beauty descriptions here — those belong in base_prompt.
- prompt: optional legacy field; include only if needed.

OPERATING MODES:

MODE 1 — User gave a text prompt:
  Enhance and expand using the REFERENCE KNOWLEDGE provided.
  When blending user instructions with reference image reality, prioritize the visual truth.
  Ensure a highly accurate descriptive flow focusing on garment features.
MODE 2 — User sent reference images (with or without text):
  STEP 1: Analyze images. Fill "image_analysis" with HIGH-LEVEL observations IN PORTUGUESE:
    category, color(s), material family, silhouette/fit.
    Describe geometric structure only, ignoring literal texture pattern names (like zigzag, diamond).
  STEP 2: Write a continuous photographic description focusing ONLY on the garment design, fiber texture, pattern, and color.
    CRITICAL: DO NOT describe the person/model in the reference (do not mention her age, ethnicity, skin color, hair, face, or body). DO NOT describe the background or pose from the reference. Focus 100% on the clothes.
  STEP 3: In base_prompt, ALWAYS open with the DIVERSITY_TARGET new model profile BEFORE the garment.
    The reference person MUST NOT appear in base_prompt in any form — she is replaced entirely.
    Pattern: "RAW photo, [DIVERSITY_TARGET model profile]. Wearing [garment from reference]..."

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

MATERIAL:
  Woven: cotton poplin, linen, silk charmeuse, wool crepe, tweed, jacquard, brocade
  Knit: fine-gauge jersey | rib-knit | chunky cable-knit | brioche stitch | open-stitch panel
  Synthetic: mesh, tulle, velvet, vinyl/PU leather, suede, sequined
  Knitwear caution: avoid "crochet loops", "3D texture", "puffy", "bobbles" — they inflate.

CONSTRUCTION:
  Necklines: crew | V-neck | scoop | boat | square | turtleneck | cowl
  Sleeves: set-in | raglan | dolman/batwing | puff | bishop | bell | cap | flutter

BEHAVIOR:
  drapes loosely | falls straight | holds structure | clings to body | skims the body

── E-COMMERCE SHOT SYSTEM ──

WIDE (hero): Full body head-to-feet, 60-70% frame, dynamic mid-stride.
MEDIUM (detail): Waist-up, neckline + sleeve focus, 50mm bokeh.
CLOSE-UP (texture): 80%+ frame is detail, macro focus.
AUTO: choose what best showcases the garment.

── MODEL & SCENE ──

Skin realism: visible natural pores, subtle peach fuzz, unretouched feel.
Presentation: professionally styled hair, warm confident expression, engaging eye contact.
Scenarios: urban downtown | rooftop terrace | tropical park | café garden | minimalist apartment | boutique showroom
Color strategy: White→dark bg | Black→light bg | Pastels→neutral warm | Saturated→clean minimal

── REALISM ──

EXCLUDE "perfect lighting", "flawless skin", "8K masterpiece".
Anchor: DEVICE="Sony A7III, 85mm f/1.8" | SKIN="visible pores" | FABRIC="natural wear creases"
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
