import re

from agent_runtime.compiler import _count_words, _truncate_by_sentence, _SENTENCE_SPLIT_RE

_CAMERA_REALISM_KEYWORDS = (
    "sony", "canon", "nikon", "f/", "mm", "lens", "bokeh", "depth of field",
    "lighting", "light", "golden hour", "pores", "skin", "fabric",
    "creases", "grain", "noise", "realism", "realistic"
)

_CAMERA_REALISM_PROFILE_DEFAULTS: dict[str, str] = {
    "catalog_clean": (
        "Captured with a full-frame digital camera, clean daylight-balanced lighting, "
        "controlled depth of field, {framing}, accurate textile detail, and a polished commercial finish."
    ),
    "catalog_natural": (
        "Captured with a full-frame digital camera, natural available light, gentle depth of field, "
        "{framing}, believable garment drape, and a natural commercial finish."
    ),
    "editorial_analog": (
        "Captured on Fujifilm GFX 100S medium format with Kodak Portra 400 film rendering, soft natural light, "
        "controlled shallow depth of field, {framing}, subtle film grain, mild lens halation, "
        "and realistic textile detail."
    ),
}

_ANALOG_EDITORIAL_HINTS = (
    "editorial",
    "film",
    "analog",
    "portra",
    "fujifilm",
    "gfx",
    "leica",
    "halation",
    "chromatic aberration",
)

_NATURAL_CATALOG_HINTS = (
    "natural light",
    "ambient light",
    "candid",
    "lifestyle",
    "street style",
    "street",
    "outdoor",
    "documentary",
)

# Signals that indicate a model-persona sentence was mis-routed by Gemini into
# the camera_and_realism field instead of base_prompt.  Used by
# _normalize_camera_realism_block to strip those sentences out at the source.
# Keep specific multi-word phrases to avoid false-positives on valid camera text.
_CAMERA_PERSONA_STRIP_SIGNALS = (
    "features blend",       # name-blend formula
    "brazilian beauty",     # typical Gemini mis-route phrase
    "authentic beauty",
    "radiant authentic",
    "flawless unretouched", # DIVERSITY_TARGET skin-realism anchor
    "ford models",
    "vogue brasil",
    "farm rio",
    "lança perfume",
    "editorial talent",     # casting-tier token (≠ "editorial" alone, valid in camera)
    "lookbook model",
    "new face",             # "Ford Models Brazil new face"
    "casting aesthetic",
)

_SKIN_TEXTURE_CLEANUPS = (
    (re.compile(r"(?i)\bvisible\s+natural\s+skin\s+pores\b"), ""),
    (re.compile(r"(?i)\bvisible\s+pores\b"), ""),
    (re.compile(r"(?i)\bsubtle\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\bauthentic\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\bunretouched\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\btrue-to-life\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\bskin\s+texture\b"), ""),
    (re.compile(r"(?i)\bsoft\s+flyaway\s+hairs\b"), ""),
    (re.compile(r"(?i)\bsubtle\s+peach\s+fuzz\b"), ""),
    (re.compile(r"(?i)\bpeach\s+fuzz\b"), ""),
)





def _extract_camera_realism_block(text: str, max_sentences: int = 2) -> str:
    """
    Extrai sentenças de câmera/realismo de um prompt legado.
    """
    if not text or not text.strip():
        return ""

    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    selected: list[str] = []
    for sent in sentences:
        low = sent.lower()
        if any(token in low for token in _CAMERA_REALISM_KEYWORDS):
            cleaned = sent.strip()
            if cleaned:
                selected.append(cleaned)
        if len(selected) >= max_sentences:
            break
    return " ".join(selected).strip()


def _camera_framing_label(shot_type: str) -> str:
    framing = "catalog framing"
    if shot_type == "wide":
        framing = "full-body catalog framing"
    elif shot_type == "medium":
        framing = "waist-up catalog framing"
    elif shot_type == "close-up":
        framing = "close-up detail framing"
    return framing


def _select_camera_realism_profile(
    *,
    has_images: bool,
    has_prompt: bool,
    user_prompt: str,
    base_prompt: str,
    camera_text: str,
) -> str:
    """
    Seleciona perfil de realismo de forma determinística:
    - Se houver sinal editorial/analog explícito, usa editorial_analog.
    - Com referências e sem texto, privilegia catalog_natural.
    - Em prompts naturais/lifestyle, usa catalog_natural.
    - Caso contrário, catalog_clean.
    """
    haystack = " ".join([
        str(user_prompt or ""),
        str(base_prompt or ""),
        str(camera_text or ""),
    ]).lower()

    if any(token in haystack for token in _ANALOG_EDITORIAL_HINTS):
        return "editorial_analog"
    if has_images and not has_prompt:
        return "catalog_natural"
    if any(token in haystack for token in _NATURAL_CATALOG_HINTS):
        return "catalog_natural"
    return "catalog_clean"


def _default_camera_realism_block(shot_type: str, profile: str = "catalog_clean") -> str:
    framing = _camera_framing_label(shot_type)
    template = _CAMERA_REALISM_PROFILE_DEFAULTS.get(
        profile,
        _CAMERA_REALISM_PROFILE_DEFAULTS["catalog_clean"],
    )
    return template.format(framing=framing)


def _normalize_camera_realism_block(
    camera_text: str,
    shot_type: str,
    profile: str = "catalog_clean",
) -> str:
    text = re.sub(r"\s+", " ", (camera_text or "").strip())
    if not text:
        return _default_camera_realism_block(shot_type, profile=profile)

    # ─── Pass 1: targeted prefix substitution ───────────────────────────────────
    # Gemini sometimes generates "flawless unretouched skin realism with visible pores"
    # where the prefix is persona content but the suffix is valid camera realism.
    # Strip the persona prefix, keep the camera-valid suffix after "with".
    _PERSONA_PREFIX_RE = re.compile(
        r"(?i)(?:flawless\s+unretouched\s+skin\s+realism\s+with\s*"
        r"|radiant\s+authentic\s+Brazilian\s+beauty\s+with\s*"
        r"|authentic\s+Brazilian\s+beauty\s+with\s*)",
        re.I,
    )
    text = _PERSONA_PREFIX_RE.sub("", text)

    # ─── Pass 2: clause-level stripping (comma-separated) ───────────────────────
    # Gemini occasionally produces a single comma-run without sentence breaks.
    # Split on commas and drop any clause that contains a strong persona signal.
    _clauses = [c.strip() for c in re.split(r",\s*", text) if c.strip()]
    _clean_clauses = [
        c for c in _clauses
        if not any(sig in c.lower() for sig in _CAMERA_PERSONA_STRIP_SIGNALS)
    ]
    if _clean_clauses:
        text = ", ".join(_clean_clauses)
        # Restore sentence terminator if the original had one
        if re.search(r"[.!?]\s*$", (camera_text or "")):
            text = text.rstrip(",.") + "."

    # ─── Pass 3: sentence-level stripping ───────────────────────────────────────
    # Split on sentence boundaries, discard any sentence containing a persona signal.
    _persona_clean = [
        s for s in re.split(r"(?<=[.!?])\s+", text)
        if not any(sig in s.lower() for sig in _CAMERA_PERSONA_STRIP_SIGNALS)
    ]
    if _persona_clean:                      # at least one real camera sentence survived
        text = " ".join(_persona_clean)
    # else: keep text as-is to avoid total loss; word-cap below will trim

    # ─── Pass 4: strip skin-surface treatment from the base camera block ───────
    # Skin texture is a secondary finish decision, not a base capture requirement.
    for pattern, replacement in _SKIN_TEXTURE_CLEANUPS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"(?i)\b(and|with)\s*(?:,)?\s*(?=[,.])", "", text)
    text = re.sub(r"\s*,\s*,+", ", ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,.])", r"\1", text)
    text = re.sub(r",\s*(and\s*)?(?=[.!?]|$)", "", text)

    # Protege concisão sem cortar o bloco em fragmentos quebrados.
    if _count_words(text) > 52:
        text, _ = _truncate_by_sentence(text, 52)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = _default_camera_realism_block(shot_type, profile=profile)
    elif profile == "editorial_analog":
        low = text.lower()
        if not any(token in low for token in _ANALOG_EDITORIAL_HINTS):
            text = f"{text} subtle film grain and mild lens halation"
    if not text.endswith((".", "!", "?")):
        text += "."
    return text


def _compose_prompt_with_camera(base_prompt: str, camera_block: str) -> str:
    base = re.sub(r"\s+", " ", (base_prompt or "").strip())
    camera = re.sub(r"\s+", " ", (camera_block or "").strip())
    if not base:
        return camera
    if not camera:
        return base
    if camera.lower() in base.lower():
        return base
    separator = "" if base.endswith((".", "!", "?")) else "."
    return f"{base}{separator} {camera}".strip()
