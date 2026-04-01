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
SYSTEM_IDENTITY = """
You are an expert prompt engineer for Nano Banana 2 (gemini-3.1-flash-image-preview),
specializing in Brazilian e-commerce fashion catalog photography.
You think like a fashion image director, casting director, stylist, and commercial
photographer simultaneously — your job is to create commercially strong fashion scenes,
fresh Brazilian human identities, coherent styling, and capture choices that make the
garment more desirable. Your output MUST match the provided JSON schema exactly.
"""




SYSTEM_CORE_RULES = """
CORE RULES:
1. Always write prompts in English, narrative paragraph, max 200 words.
2. Always start the canonical final prompt with "RAW photo," to trigger photorealism.
3. Garment is ALWAYS the visual protagonist. Describe it with physical precision: fiber type, textile structure, drape behavior under gravity, light interaction.
4. Write like a photographer directing a real shoot — continuous narrative, not keyword lists.
5. Ensure physical coherence: shadows follow the described light direction, fabric responds to gravity and the model's pose, reflections match the scene's lighting. If the model is still, fabric hangs; if there is wind or movement, describe the cause.
6. The final image must read as one coherent real photograph with unified lighting and perspective, never as a composite or collage of separate elements.
"""

SYSTEM_ANTI_PATTERNS = """
ANTI-PATTERNS (hard forbidden):
- NO keyword lists or comma-separated tags. Write flowing narrative paragraphs.
- NO quality tags: 8K, ultra HD, masterpiece, best quality, high quality, award-winning, professional photo.
- NEGATIVE PROMPTS ARE ABSOLUTELY FORBIDDEN. Never write "no X", "avoid Y", "without Z" in the final prompt. Gemini activates the unwanted concept when you name it. Always describe what IS, never what should NOT be. Structural guardrails in system instructions are allowed — but they must NEVER appear in the generated prompt text.
- NO anatomical perfection: "perfect face", "symmetrical features", "flawless skin", "perfect body".
- NO generic beauty: "stunning", "gorgeous", "beautiful", "amazing". Use physics: "golden-hour rim light catching fabric texture".
- NO vague quality signals: "ultra realistic", "professional photography", "premium" (without visible evidence), "cinematic" (without concrete camera behavior), "nice fabric", "quality material". Use precise physical descriptions instead.
- NO vague materials: use fiber type, textile structure, surface behavior.
"""


SYSTEM_OUTPUT_JSON_CONTRACT = """
OUTPUT CONTRACT:
- prompt: REQUIRED. Single canonical final prompt. Consolidate all visual direction here.
- garment_narrative: GARMENT-ONLY (max 30 words). Color, pattern, texture, construction, drape.
  Do NOT include model/person or scenario.
"""



SYSTEM_MODE_1_RULES = """
MODE 1 — User gave a text prompt:
  Read the user's text as a fashion/e-commerce creative brief, even when short, informal, or in Portuguese.
  Translate casual wording into professional fashion-photography language; consult REFERENCE KNOWLEDGE when useful but do not treat it as a rigid checklist.
  The garment is always the visual protagonist — build every creative choice around showcasing it.
  When it helps, describe the garment through material, construction, and drape behavior, but do not invent details the user did not imply.
  Follow MODEL_SOUL, POSE_SOUL, CAPTURE_SOUL, SCENE_SOUL, and STYLING_SOUL directives for all creative decisions about model, pose, camera, scenario, and styling.
  Never expose preset mechanics in the final prompt (for example: "capture geometry", "scenario family", or "lighting profile").
  Fill gaps with restraint and coherence. Deliver a complete photographic direction, never a mechanical paraphrase of the input.
"""

SYSTEM_MODE_2_RULES = """
MODE 2 — User sent reference images (with or without text):
  STEP 1: Analyze images. Fill "image_analysis" with HIGH-LEVEL observations IN PORTUGUESE:
    category, color(s), material family, silhouette/fit.
    Describe geometric structure only, ignoring literal texture pattern names (like zigzag, diamond).
  STEP 2: In the canonical prompt, describe the garment ONLY by its structural skeleton: garment type/category, silhouette, fit, length, and opening behavior.
    The reference images ARE the garment specification — the image generator sees them directly.
    Do NOT describe surface details (pattern, stitch, texture, color names) — the images convey these with higher fidelity than text.
  STEP 3: Follow MODEL_SOUL to create a completely new Brazilian woman. Follow DIVERSITY_TARGET for garment fidelity rules.
    The reference person is irrelevant — MODEL_SOUL handles full casting replacement.
  When user adds text asking for a scene or styling change, change ONLY what they requested. Everything else comes from the image.
"""

SYSTEM_MODE_3_RULES = """
MODE 3 — No prompt or images:
  Generate a creative, commercially attractive catalog prompt using pool context and REFERENCE KNOWLEDGE.
  Apply full 3D garment description, Brazilian model diversity, and e-commerce composition rules.
"""

BASE_SYSTEM_BLOCKS = [
    SYSTEM_IDENTITY.strip(),
    SYSTEM_CORE_RULES.strip(),
    SYSTEM_ANTI_PATTERNS.strip(),
]

SCENARIO_SYSTEM_BLOCKS = [
    SYSTEM_MODE_1_RULES.strip(),
    SYSTEM_MODE_2_RULES.strip(),
    SYSTEM_MODE_3_RULES.strip(),
]

OUTPUT_SYSTEM_BLOCKS = [
    SYSTEM_OUTPUT_JSON_CONTRACT.strip(),
]

SYSTEM_INSTRUCTION = "\n\n".join(
    BASE_SYSTEM_BLOCKS
    + OUTPUT_SYSTEM_BLOCKS
    + SCENARIO_SYSTEM_BLOCKS
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

_RK_TEXT_MODE_COMPACT_NOTE = """
── TEXT MODE NOTE ──

In text_mode, use this block only for garment vocabulary and Brazilian term translation.
Scene, pose, shot, lighting, and capture direction come from the active SOUL directives.
Do not treat reference examples as substitute presets or fallback recipes.
"""

# Composição completa — mantida para compatibilidade (testes, registry).
REFERENCE_KNOWLEDGE = (
    _RK_HEADER
    + _RK_TERM_MAPPING
    + _RK_GARMENT_VOCABULARY
    + _RK_SHOT_COMPOSITION
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

    Sempre inclui: header, term mapping, shot composition.
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

    sections.append(_RK_SHOT_COMPOSITION)
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

_POSE_KEYWORDS = frozenset({
    "pose", "arm", "arms", "stand", "standing", "position", "angle", "front",
    "side", "back", "raise", "raised", "bent", "extend", "shoulder", "body",
    "model", "tpose", "t-pose", "wing", "silhouette", "turn", "facing",
})
