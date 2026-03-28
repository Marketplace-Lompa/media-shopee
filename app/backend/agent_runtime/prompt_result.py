from __future__ import annotations

import re
from typing import Any, Optional

from agent_runtime.compiler import (
    _compile_prompt_v2,
    _count_words,
    _truncate_by_sentence,
    _SENTENCE_SPLIT_RE,
)
from agent_runtime.garment_narrative import sanitize_garment_narrative


# ─── Sanitização de camera_and_realism (ex-camera.py) ───────────────────────
# Essas funções existem apenas para LIMPAR o output do Gemini quando ele
# vaza persona, skin texture ou menciona câmeras/lentes específicas no campo
# camera_and_realism. Não definem templates nem tomam decisões criativas.
# A direção de captura vem da combinação entre estado latente de captura,
# CAPTURE_SOUL e MODE_PRESETS. Essas funções abaixo apenas limpam vazamentos
# ruins do output do Gemini; elas não tomam decisões criativas.

_CAMERA_REALISM_KEYWORDS = (
    "sony", "canon", "nikon", "f/", "mm", "lens", "bokeh", "depth of field",
    "lighting", "light", "golden hour", "pores", "skin", "fabric",
    "creases", "grain", "noise", "realism", "realistic",
)

_CAMERA_PERSONA_STRIP_SIGNALS = (
    "features blend",
    "brazilian beauty",
    "authentic beauty",
    "radiant authentic",
    "flawless unretouched",
    "ford models",
    "vogue brasil",
    "farm rio",
    "lança perfume",
    "editorial talent",
    "lookbook model",
    "new face",
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

_PERSONA_PREFIX_RE = re.compile(
    r"(?i)(?:flawless\s+unretouched\s+skin\s+realism\s+with\s*"
    r"|radiant\s+authentic\s+Brazilian\s+beauty\s+with\s*"
    r"|authentic\s+Brazilian\s+beauty\s+with\s*)",
    re.I,
)

# Strip de dispositivos/lentes específicas — o Gemini às vezes menciona
# marcas e especificações técnicas que engessam a geração de imagem.
_DEVICE_STRIP_PATTERNS = (
    re.compile(r"(?i)\bSony\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\bCanon\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\bNikon\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\bFujifilm\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\b\d+mm\s+lens[^,.]*[,.]"),
    re.compile(r"(?i)\bSony\s+[A-Z0-9]+"),
    re.compile(r"(?i)\bCanon\s+[A-Z0-9]+"),
    re.compile(r"(?i)\bNikon\s+[A-Z0-9]+"),
    re.compile(r"(?i)\bFujifilm\s+[A-Z0-9]+"),
    re.compile(r"(?i)\b\d+mm\b"),
    re.compile(r"(?i)\blens\b"),
)

# Fallback mínimo quando o Gemini não gera nenhum texto de captura.
# Sem template longo — os presets no MODE_PRESETS já deram a direção.
_MINIMAL_CAPTURE_FALLBACK = "Commercially clean capture with natural finish."

_FOOTWEAR_KEYWORDS = (
    "shoe", "shoes", "heel", "heels", "sandal", "sandals", "loafer", "loafers",
    "flat", "flats", "pump", "pumps", "boot", "boots", "sneaker", "sneakers",
    "mule", "mules", "espadrille", "espadrilles", "footwear",
)

_BAREFOOT_EXCEPTION_KEYWORDS = (
    "barefoot", "descalço", "descalca", "descalça", "sem sapato", "sem sapatos",
    "beachwear", "swimwear", "bikini", "lingerie", "sleepwear", "pajama", "pyjama",
    "loungewear", "robe",
)

_AGE_SURFACE_RE = re.compile(
    r"(?i)\b(?:\d{2})[-\s]?year[-\s]?old\b|\b(?:in her|his)\s+(?:early|mid|late|mid-to-late)[-\s]+\d{2}s\b|\b(?:early|mid|late|mid-to-late)[-\s]+\d{2}s\b"
)
_FACE_SURFACE_PATTERNS = (
    re.compile(r"(?i)\bface\b"),
    re.compile(r"(?i)\bfacial\b"),
    re.compile(r"(?i)\bjaw(?:line)?\b"),
    re.compile(r"(?i)\bcheek(?:bone|bones)?\b"),
    re.compile(r"(?i)\bchin\b"),
    re.compile(r"(?i)\bbrow(?:s)?\b"),
    re.compile(r"(?i)\bsmile lines\b"),
    re.compile(r"(?i)\beyes\b"),
    re.compile(r"(?i)\boval\b"),
)
_HAIR_SURFACE_PATTERNS = (
    re.compile(r"(?i)\bhair\b"),
    re.compile(r"(?i)\bwaves?\b"),
    re.compile(r"(?i)\bwavy\b"),
    re.compile(r"(?i)\bcurls?\b"),
    re.compile(r"(?i)\bcurly\b"),
    re.compile(r"(?i)\bbob\b"),
    re.compile(r"(?i)\bponytail\b"),
    re.compile(r"(?i)\bafro\b"),
    re.compile(r"(?i)\bbrunette\b"),
    re.compile(r"(?i)\bchestnut\b"),
    re.compile(r"(?i)\bespresso-brown\b"),
)
_GENERIC_POSE_PATTERNS = (
    "stable pose",
    "composed stance",
    "commercially-focused pose",
    "stable catalog stance",
    "stable, commercially-focused pose",
)
_SPECIFIC_POSE_MARKERS = (
    "one hand", "hand lightly", "grazing", "weight shift", "weight placement", "mid-step",
    "torso turn", "torso angle", "arm", "shoulder angle", "head direction", "stance with",
)
_SCENE_COORDINATION_MARKERS = (
    "studio", "interior", "window", "street", "sidewalk", "backdrop", "neighborhood", "apartment", "set",
)
_COORDINATION_BRIDGE_MARKERS = (
    "while", "keeping", "ensuring", "creating", "so that", "maintaining", "paired with", "matched to",
)
_CAPTURE_DISTANCE_MARKERS = (
    "full-body shot", "full body shot", "wide shot", "medium shot", "medium-wide shot",
    "close-up", "closeup", "waist-up", "waist up", "framed from", "observer viewpoint",
)
_CAPTURE_ANGLE_MARKERS = (
    "eye-level", "eye level", "low-angle", "low angle", "high-angle", "high angle",
    "three-quarter", "three quarter", "slight-angle", "slight angle", "from below",
    "from above", "camera height", "viewed from",
)
_CAPTURE_SPACE_MARKERS = (
    "background", "foreground", "breathing room", "falloff", "depth separation",
    "subject separation", "depth", "against", "set against", "behind her", "behind him",
)


def _ensure_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return ""
    if cleaned.endswith((".", "!", "?")):
        return cleaned
    return f"{cleaned}."


def _join_human_bits(parts: list[str]) -> str:
    cleaned = [str(part or "").strip() for part in parts if str(part or "").strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _sentence_surface_key(text: str) -> str:
    normalized = re.sub(r"(?i)^raw photo,\s*", "", str(text or "").strip())
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip(" .,!?:;").lower()
    return normalized


def _extract_camera_realism_block(text: str, max_sentences: int = 2) -> str:
    """Extrai sentenças de câmera/realismo de um prompt legado."""
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


def _sanitize_camera_block(camera_text: str) -> str:
    """
    Sanitiza o campo camera_and_realism gerado pelo Gemini.
    Remove vazamentos de persona, skin texture, e mencões a câmeras específicas.
    Não aplica templates nem toma decisões criativas.
    """
    text = re.sub(r"\s+", " ", (camera_text or "").strip())
    if not text:
        return _MINIMAL_CAPTURE_FALLBACK

    # Pass 0: strip device/lens mentions
    for pat in _DEVICE_STRIP_PATTERNS:
        text = pat.sub("", text)
    text = re.sub(r"\s*,\s*,+", ", ", text)
    text = re.sub(r"^\s*,\s*", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    if not text:
        return _MINIMAL_CAPTURE_FALLBACK

    # Pass 1: targeted prefix substitution
    text = _PERSONA_PREFIX_RE.sub("", text)

    # Pass 2: clause-level stripping (comma-separated)
    _clauses = [c.strip() for c in re.split(r",\s*", text) if c.strip()]
    _clean_clauses = [
        c for c in _clauses
        if not any(sig in c.lower() for sig in _CAMERA_PERSONA_STRIP_SIGNALS)
    ]
    if _clean_clauses:
        text = ", ".join(_clean_clauses)
        if re.search(r"[.!?]\s*$", (camera_text or "")):
            text = text.rstrip(",.") + "."

    # Pass 3: sentence-level stripping
    _persona_clean = [
        s for s in re.split(r"(?<=[.!?])\s+", text)
        if not any(sig in s.lower() for sig in _CAMERA_PERSONA_STRIP_SIGNALS)
    ]
    if _persona_clean:
        text = " ".join(_persona_clean)

    # Pass 4: strip skin-surface treatment
    for pattern, replacement in _SKIN_TEXTURE_CLEANUPS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"(?i)\b(and|with)\s*(?:,)?\s*(?=[,.])", "", text)
    text = re.sub(r"\s*,\s*,+", ", ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,.])", r"\1", text)
    text = re.sub(r",\s*(and\s*)?(?=[.!?]|$)", "", text)

    # Word cap (concisão)
    if _count_words(text) > 52:
        text, _ = _truncate_by_sentence(text, 52)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return _MINIMAL_CAPTURE_FALLBACK

    if not text.endswith((".", "!", "?")):
        text += "."
    return text


def _compose_prompt_with_camera(base_prompt: str, camera_block: str) -> str:
    """Concatena base_prompt + camera block sanitizado."""
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


def _maybe_enforce_text_mode_footwear(
    *,
    prompt_text: str,
    user_prompt: Optional[str],
    framing_profile: str,
    mode_id: str,
    shot_type: str = "",
    styling_state: Optional[dict[str, Any]] = None,
) -> tuple[str, Optional[str]]:
    """Guardrail leve: evita full-body fashion descalço por omissão no text_mode."""
    normalized_shot = str(shot_type or "").strip().lower()
    low_prompt = prompt_text.lower()
    full_body_surface = any(
        marker in low_prompt
        for marker in ("full-body", "full body", "head-to-toe", "head to toe", "feet visible")
    )
    if not (
        framing_profile == "full_body"
        and (normalized_shot == "wide" or full_body_surface)
    ):
        return prompt_text, None
    low_user = str(user_prompt or "").lower()
    joined = f"{low_prompt} {low_user}"

    if any(token in joined for token in _FOOTWEAR_KEYWORDS):
        return prompt_text, None
    if any(token in joined for token in _BAREFOOT_EXCEPTION_KEYWORDS):
        return prompt_text, None

    if mode_id == "catalog_clean":
        clause = "She is styled with discreet footwear appropriate to the look to keep the styling commercially complete without competing with the garment."
    elif mode_id == "natural":
        clause = "She is styled with everyday non-premium footwear that feels ordinary, practical, and natural for her day without competing with the garment."
    elif mode_id == "lifestyle":
        clause = "She is styled with footwear that feels chosen for her activity and setting — it tells you where she was going and what she was doing, not just that the look is commercially complete."
    else:
        clause = "She is styled with discreet commercially coherent footwear that keeps the look complete without competing with the garment."

    base = re.sub(r"\s+", " ", prompt_text.strip())
    if not base:
        return clause, "styling_completion"
    separator = "" if base.endswith((".", "!", "?")) else "."
    return f"{base}{separator} {clause}".strip(), "styling_completion"


def _has_casting_surface(text: str) -> tuple[bool, bool, bool]:
    has_age = bool(_AGE_SURFACE_RE.search(text))
    has_face = any(pattern.search(text) for pattern in _FACE_SURFACE_PATTERNS)
    has_hair = any(pattern.search(text) for pattern in _HAIR_SURFACE_PATTERNS)
    return has_age, has_face, has_hair


def _maybe_enforce_casting_surface(
    *,
    prompt_text: str,
    casting_state: Optional[dict[str, Any]] = None,
    reference_mode: bool = False,
) -> tuple[str, Optional[str]]:
    state = casting_state or {}
    if not state:
        return prompt_text, None

    has_age, has_face, has_hair = _has_casting_surface(prompt_text)
    age = str(state.get("age", "") or "").strip()
    face = str(state.get("face_structure", "") or "").strip()
    hair = str(state.get("hair", "") or "").strip()
    presence = str(state.get("presence", "") or "").strip()
    expression = str(state.get("expression", "") or "").strip()

    if reference_mode:
        if has_age or has_face or has_hair:
            return prompt_text, None
        clause = ""
        if age and presence:
            clause = f"She appears in her {age} with {presence}"
        elif age:
            clause = f"She appears in her {age}"
        elif presence:
            clause = f"She has {presence}"
        elif expression:
            clause = f"She has a {expression}"
        if not clause:
            return prompt_text, None
        if not clause.endswith("."):
            clause += "."
        base = re.sub(r"\s+", " ", prompt_text.strip())
        separator = "" if base.endswith((".", "!", "?")) else "."
        return f"{base}{separator} {clause}".strip(), "casting_surface"

    if has_age and has_face and has_hair:
        return prompt_text, None

    age_fragment = f"in her {age}" if (not has_age and age) else ""
    face_fragment = face if (not has_face and face) else ""
    hair_fragment = hair if (not has_hair and hair) else ""

    if not any((age_fragment, face_fragment, hair_fragment)):
        return prompt_text, None

    if face_fragment and not re.match(r"(?i)^(a|an|the)\b", face_fragment):
        face_fragment = f"a {face_fragment}"

    if age_fragment and face_fragment and hair_fragment:
        clause = f"She appears {age_fragment}, with {face_fragment} and {hair_fragment}"
    elif age_fragment and face_fragment:
        clause = f"She appears {age_fragment}, with {face_fragment}"
    elif age_fragment and hair_fragment:
        clause = f"She appears {age_fragment}, with {hair_fragment}"
    elif age_fragment:
        clause = f"She appears {age_fragment}"
    elif face_fragment and hair_fragment:
        clause = f"She has {face_fragment}, with {hair_fragment}"
    elif face_fragment:
        clause = f"She has {face_fragment}"
    else:
        clause = f"Her hair reads as {hair_fragment}"

    if not clause.endswith("."):
        clause += "."

    base = re.sub(r"\s+", " ", prompt_text.strip())
    separator = "" if base.endswith((".", "!", "?")) else "."
    return f"{base}{separator} {clause}".strip(), "casting_surface"


def _has_specific_pose_surface(text: str) -> bool:
    low = text.lower()
    if any(marker in low for marker in _SPECIFIC_POSE_MARKERS):
        return True
    if any(pattern in low for pattern in _GENERIC_POSE_PATTERNS):
        return False
    if any(token in low for token in ("standing", "stance", "pose", "posed")):
        return False
    return False


def _maybe_enforce_pose_surface(
    *,
    prompt_text: str,
    pose_state: Optional[dict[str, Any]] = None,
) -> tuple[str, Optional[str]]:
    state = pose_state or {}
    if not state:
        return prompt_text, None
    if _has_specific_pose_surface(prompt_text):
        return prompt_text, None

    surface_direction = str(state.get("surface_direction", "") or "").strip()
    weight_shift = str(state.get("weight_shift", "") or "").strip()
    arm_logic = str(state.get("arm_logic", "") or "").strip()
    torso_orientation = str(state.get("torso_orientation", "") or "").strip()
    head_direction = str(state.get("head_direction", "") or "").strip()
    gesture_intention = str(state.get("gesture_intention", "") or "").strip()
    if not any((surface_direction, weight_shift, arm_logic, torso_orientation)):
        return prompt_text, None

    clauses: list[str] = []
    if weight_shift or arm_logic or torso_orientation:
        pose_bits = [bit for bit in (weight_shift, arm_logic, torso_orientation) if bit]
        primary = ", ".join(pose_bits[:3])
        if primary:
            clauses.append(f"Her body is directed through {primary}")
    elif surface_direction:
        clauses.append(f"Her pose is resolved {surface_direction}")

    if head_direction:
        clauses.append(f"Her head keeps {head_direction}")
    if gesture_intention:
        clauses.append(f"The overall gesture reads as {gesture_intention}")

    clause = ". ".join(c.strip() for c in clauses if c.strip())
    if not clause:
        return prompt_text, None
    if not clause.endswith("."):
        clause += "."

    base = re.sub(r"\s+", " ", prompt_text.strip())
    separator = "" if base.endswith((".", "!", "?")) else "."
    return f"{base}{separator} {clause}".strip(), "pose_surface"


def _has_specific_capture_surface(text: str) -> bool:
    low = str(text or "").lower()
    has_distance = any(marker in low for marker in _CAPTURE_DISTANCE_MARKERS)
    has_angle = any(marker in low for marker in _CAPTURE_ANGLE_MARKERS)
    has_space = any(marker in low for marker in _CAPTURE_SPACE_MARKERS)
    return sum((has_distance, has_angle, has_space)) >= 2


def _maybe_enforce_capture_surface(
    *,
    prompt_text: str,
    capture_state: Optional[dict[str, Any]] = None,
) -> tuple[str, Optional[str]]:
    state = capture_state or {}
    if not state:
        return prompt_text, None
    if _has_specific_capture_surface(prompt_text):
        return prompt_text, None

    body_relation = str(state.get("body_relation", "") or "").strip()
    angle_logic = str(state.get("angle_logic", "") or "").strip()
    subject_separation = str(state.get("subject_separation", "") or "").strip()
    lens_language = str(state.get("lens_language", "") or "").strip()
    if not any((body_relation, angle_logic, subject_separation)):
        return prompt_text, None

    clauses: list[str] = []
    lower_lens = lens_language.lower()
    if lens_language and ("perspective" in lower_lens or "viewpoint" in lower_lens):
        clauses.append(f"Seen through {lower_lens}")

    relation_bits = []
    if body_relation:
        relation_bits.append(body_relation.lower())
    if angle_logic:
        relation_bits.append(angle_logic.lower().replace(" relation", ""))
    if subject_separation:
        relation_bits.append(subject_separation.lower())
    if relation_bits:
        clauses.append(f"the framing holds {_join_human_bits(relation_bits[:3])}")

    clause = ", ".join(part.strip() for part in clauses if part.strip())
    clause = re.sub(r"\s+", " ", clause).strip(" ,")
    if not clause:
        return prompt_text, None
    if not clause.endswith("."):
        clause += "."

    base = re.sub(r"\s+", " ", prompt_text.strip())
    separator = "" if base.endswith((".", "!", "?")) else "."
    return f"{base}{separator} {clause}".strip(), "capture_surface"


def _coordination_diagnostics(prompt_text: str) -> dict[str, Any]:
    low = prompt_text.lower()
    has_age, has_face, has_hair = _has_casting_surface(prompt_text)
    return {
        "casting_surface_present": bool(has_age and has_face and has_hair),
        "specific_pose_present": _has_specific_pose_surface(prompt_text),
        "capture_surface_present": _has_specific_capture_surface(prompt_text),
        "scene_surface_present": any(marker in low for marker in _SCENE_COORDINATION_MARKERS),
        "styling_surface_present": any(token in low for token in _FOOTWEAR_KEYWORDS),
        "bridge_language_present": any(marker in low for marker in _COORDINATION_BRIDGE_MARKERS),
        "decomposition_risk": not any(marker in low for marker in _COORDINATION_BRIDGE_MARKERS),
    }


def _maybe_enforce_coordination_bridge(
    *,
    prompt_text: str,
    coordination_state: Optional[dict[str, Any]] = None,
) -> tuple[str, Optional[str]]:
    state = coordination_state or {}
    if not state:
        return prompt_text, None

    diagnostics = _coordination_diagnostics(prompt_text)
    if not diagnostics.get("decomposition_risk"):
        return prompt_text, None

    clause = str(state.get("bridge_clause", "") or "").strip()
    if not clause:
        return prompt_text, None

    base = re.sub(r"\s+", " ", prompt_text.strip())
    separator = "" if base.endswith((".", "!", "?")) else "."
    return f"{base}{separator} {clause}".strip(), "coordination_bridge"


def _maybe_promote_catalog_garment_lead(
    *,
    prompt_text: str,
    garment_narrative: str,
    mode_id: str,
) -> tuple[str, Optional[str]]:
    if mode_id != "catalog_clean":
        return prompt_text, None

    garment_text = str(garment_narrative or "").strip()
    base = re.sub(r"\s+", " ", prompt_text.strip())
    if not garment_text or not base:
        return prompt_text, None

    lowered = base.lower()
    if garment_text.lower() in lowered[:220]:
        return prompt_text, None

    lead = (
        f"RAW photo, premium clean catalog image with the garment as the absolute hero: {garment_text}."
    )
    if lowered.startswith("raw photo,"):
        remainder = base[len("RAW photo,"):].strip()
    else:
        remainder = base

    rebuilt = f"{lead} {remainder}".strip()
    return rebuilt, "catalog_garment_lead"


def _maybe_refine_catalog_surface(
    *,
    prompt_text: str,
    mode_id: str,
    garment_narrative: str,
) -> tuple[str, list[str]]:
    if mode_id != "catalog_clean":
        return prompt_text, []

    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(prompt_text.strip()) if s.strip()]
    if len(sentences) < 2:
        return prompt_text, []

    changed_sources: list[str] = []
    refined: list[str] = []
    shot_refined = False
    garment_refined = False
    garment_hint = str(garment_narrative or "").strip().lower()

    for sentence in sentences:
        low = sentence.lower()

        if not shot_refined and "shot of a" in low and "woman" in low:
            subject_match = re.search(
                r"(?i)\bshot of a\s+(.+?)(?:\s+(?:standing|posed)\s+against\s+(.+?))?(?:[.!?]|$)",
                sentence,
            )
            subject = subject_match.group(1).strip() if subject_match else "polished Brazilian commercial woman"
            backdrop_match = re.search(
                r"(?i)\b(?:standing|posed)\s+against\s+(.+?)(?:[.!?]|$)",
                sentence,
            )
            backdrop = backdrop_match.group(1).strip() if backdrop_match else "a seamless neutral studio backdrop"
            refined.append(
                _ensure_sentence(
                    f"A full-body studio catalog shot on a {subject} against {backdrop}"
                )
            )
            changed_sources.append("catalog_surface_shot")
            shot_refined = True
            continue

        if (
            not garment_refined
            and (low.startswith("she wears ") or low.startswith("she is wearing "))
            and garment_hint
            and any(token in low for token in ("pullover", "sweater", "knit", "cardigan", "shirt", "dress", "blazer", "jacket"))
        ):
            refined.append(
                "The garment is rendered with accurate knit weight, clear surface definition, and even commercial studio readability."
            )
            changed_sources.append("catalog_surface_garment")
            garment_refined = True
            continue

        refined.append(_ensure_sentence(sentence))

    rebuilt = " ".join(part for part in refined if part).strip()
    if not rebuilt or rebuilt == prompt_text.strip():
        return prompt_text, []
    return rebuilt, changed_sources


def _maybe_refine_catalog_nano_surface(
    *,
    prompt_text: str,
    mode_id: str,
    has_images: bool,
) -> tuple[str, list[str]]:
    if mode_id != "catalog_clean" or not has_images:
        return prompt_text, []

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prompt_text.strip()) if s.strip()]
    if not sentences:
        return prompt_text, []

    changed_sources: list[str] = []
    refined: list[str] = []
    seen_keys: set[str] = set()
    deterministic_surface_markers = (
        "native edge-to-edge composition",
        "full-bleed composition",
        "background continuity across the full frame",
    )

    for idx, sentence in enumerate(sentences):
        working = sentence.strip()
        low = working.lower()

        if any(marker in low for marker in deterministic_surface_markers):
            changed_sources.append("catalog_nano_surface_mechanical_clause")
            continue

        if idx > 0:
            stripped = re.sub(r"(?i)^raw photo,\s*", "", working).strip()
            if stripped != working:
                changed_sources.append("catalog_nano_surface_mid_raw_photo")
            working = stripped

        softened = re.sub(r"(?i)\s+from the reference\b", "", working).strip()
        if softened != working:
            changed_sources.append("catalog_nano_surface_reference_phrase")
        working = softened

        softened = re.sub(
            r"(?i)\bwith\s+an?\s+[a-zà-ÿ-]+-inspired phenotype\b,?\s*",
            "with ",
            working,
        ).strip()
        if softened != working:
            changed_sources.append("catalog_nano_surface_region_label")
        working = softened

        softened = re.sub(
            r"(?i)\bcontinuous neckline-to-front edge\b",
            "clean uninterrupted front edge",
            working,
        ).strip()
        if softened != working:
            changed_sources.append("catalog_nano_surface_structural_softening")
        working = softened

        if working and working[0].islower():
            working = working[0].upper() + working[1:]

        key = _sentence_surface_key(working)
        if key and key in seen_keys:
            changed_sources.append("catalog_nano_surface_duplicate_sentence")
            continue
        if key:
            seen_keys.add(key)
        refined.append(_ensure_sentence(working))

    rebuilt = " ".join(part for part in refined if part).strip()
    if not rebuilt or rebuilt == prompt_text.strip():
        return prompt_text, []
    return rebuilt, changed_sources


def _dedupe_surface_sentences(prompt_text: str) -> tuple[str, bool]:
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(prompt_text.strip()) if s.strip()]
    if len(sentences) < 2:
        return prompt_text, False

    refined: list[str] = []
    seen_keys: set[str] = set()
    changed = False

    for sentence in sentences:
        key = _sentence_surface_key(sentence)
        if key and key in seen_keys:
            changed = True
            continue
        if key:
            seen_keys.add(key)
        refined.append(_ensure_sentence(sentence))

    rebuilt = " ".join(part for part in refined if part).strip()
    if not rebuilt:
        return prompt_text, False
    return rebuilt, changed


# ─── Finalizador principal ──────────────────────────────────────────────────

def finalize_prompt_agent_result(
    *,
    result: dict[str, Any],
    has_images: bool,
    has_prompt: bool,
    user_prompt: Optional[str],
    structural_contract: dict[str, Any],
    guided_brief: Optional[dict[str, Any]],
    guided_enabled: bool,
    guided_set_mode: str,
    guided_set_detection: dict[str, Any],
    grounding_mode: str,
    pipeline_mode: str,
    aspect_ratio: str,
    pose: str,
    grounding_pose_clause: str,
    profile: str,
    scenario: str,
    diversity_target: Optional[dict[str, Any]],
    mode_id: str = "",
    framing_profile: str = "",
    camera_type: str = "",
    capture_geometry: str = "",
    lighting_profile: str = "",
    pose_energy: str = "",
    casting_profile: str = "",
) -> dict[str, Any]:
    canonical_prompt_raw = str(result.get("prompt", "") or "").strip()
    base_prompt_raw = str(result.get("base_prompt", "") or "").strip()
    resolved_shot_type = str(result.get("shot_type", "auto") or "auto")
    if mode_id == "catalog_clean" and framing_profile == "full_body":
        resolved_shot_type = "wide"
        result["shot_type"] = "wide"
    if pipeline_mode == "text_mode":
        prompt_source_raw = canonical_prompt_raw or base_prompt_raw
    else:
        prompt_source_raw = base_prompt_raw or canonical_prompt_raw
    if not prompt_source_raw:
        prompt_source_raw = "RAW photo, polished e-commerce catalog composition with garment-first framing."

    garment_narrative = str(result.get("garment_narrative", "") or "").strip()
    if garment_narrative:
        garment_narrative = sanitize_garment_narrative(garment_narrative, structural_contract)
        garment_words = garment_narrative.split()
        if len(garment_words) > 35:
            garment_narrative = " ".join(garment_words[:35])
            garment_words = garment_narrative.split()
        if garment_narrative:
            print(f"[AGENT] 👗 garment_narrative ({len(garment_words)}w): {garment_narrative[:120]}")

    # ── Captura: no text_mode o prompt consolidado é a fonte canônica.
    # O campo camera_and_realism permanece apenas para compatibilidade.
    if pipeline_mode == "text_mode":
        camera_realism = ""
        camera_words = 0
        base_budget = 220
    else:
        camera_realism_raw = str(result.get("camera_and_realism", "") or "").strip()
        if not camera_realism_raw:
            camera_realism_raw = _extract_camera_realism_block(canonical_prompt_raw)
        if not camera_realism_raw:
            camera_realism_raw = _extract_camera_realism_block(prompt_source_raw)

        camera_realism = _sanitize_camera_block(camera_realism_raw)
        camera_words = _count_words(camera_realism)
        base_budget = max(80, 220 - camera_words)
        if has_images and not has_prompt:
            target_budget = 215
            base_budget = max(80, target_budget - camera_words)

    lighting_hint = (diversity_target or {}).get("lighting_hint", "") or ""
    compiled_base_prompt, compiler_debug = _compile_prompt_v2(
        prompt=prompt_source_raw,
        has_images=has_images,
        has_prompt=has_prompt,
        contract=structural_contract if has_images else None,
        guided_brief=guided_brief if guided_enabled else None,
        guided_enabled=guided_enabled,
        guided_set_detection=guided_set_detection if guided_enabled and guided_set_mode == "conjunto" else None,
        grounding_mode=grounding_mode,
        pipeline_mode=pipeline_mode,
        word_budget=base_budget,
        aspect_ratio=aspect_ratio,
        pose_hint=pose or grounding_pose_clause,
        profile_hint=profile,
        scenario_hint=scenario,
        garment_narrative=garment_narrative,
        lighting_hint=lighting_hint,
        shot_type=resolved_shot_type,
        framing_profile=framing_profile,
        pose_energy=pose_energy,
        casting_profile=casting_profile,
        mode_id=mode_id,
    )

    final_prompt = (
        compiled_base_prompt
        if pipeline_mode == "text_mode"
        else _compose_prompt_with_camera(compiled_base_prompt, camera_realism)
    )
    if pipeline_mode in ("text_mode", "reference_mode"):
        soul_driven_mode = mode_id in {"natural", "lifestyle", "editorial_commercial"}
        casting_state = (diversity_target or {}).get("casting_state") or {}
        pose_state = (diversity_target or {}).get("pose_state") or {}
        styling_state = (diversity_target or {}).get("styling_state") or {}
        coordination_state = (diversity_target or {}).get("coordination_state") or {}
        final_prompt, casting_source = _maybe_enforce_casting_surface(
            prompt_text=final_prompt,
            casting_state=casting_state,
            reference_mode=bool(has_images),
        )
        if casting_source:
            compiler_debug["used_clauses"].append(
                {
                    "text": "casting surface minimum",
                    "source": casting_source,
                }
            )
        final_prompt, pose_source = _maybe_enforce_pose_surface(
            prompt_text=final_prompt,
            pose_state=pose_state,
        )
        if pose_source:
            compiler_debug["used_clauses"].append(
                {
                    "text": "pose surface minimum",
                    "source": pose_source,
                }
            )
        if not soul_driven_mode:
            final_prompt, capture_source = _maybe_enforce_capture_surface(
                prompt_text=final_prompt,
                capture_state=(diversity_target or {}).get("capture_state") or {},
            )
            if capture_source:
                compiler_debug["used_clauses"].append(
                    {
                        "text": "capture surface minimum",
                        "source": capture_source,
                    }
                )
        final_prompt, coordination_source = _maybe_enforce_coordination_bridge(
            prompt_text=final_prompt,
            coordination_state=coordination_state,
        )
        if coordination_source:
            compiler_debug["used_clauses"].append(
                {
                    "text": "coordination bridge",
                    "source": coordination_source,
                }
            )
        final_prompt, styling_source = _maybe_enforce_text_mode_footwear(
            prompt_text=final_prompt,
            user_prompt=user_prompt,
            framing_profile=framing_profile,
            mode_id=mode_id,
            shot_type=resolved_shot_type,
            styling_state=styling_state,
        )
        if styling_source:
            compiler_debug["used_clauses"].append(
                {
                    "text": "commercially complete footwear guardrail",
                    "source": styling_source,
                }
            )
        final_prompt, garment_lead_source = _maybe_promote_catalog_garment_lead(
            prompt_text=final_prompt,
            garment_narrative=garment_narrative,
            mode_id=mode_id,
        )
        if garment_lead_source:
            compiler_debug["used_clauses"].append(
                {
                    "text": "catalog garment-first lead",
                    "source": garment_lead_source,
                }
            )
        final_prompt, catalog_surface_sources = _maybe_refine_catalog_surface(
            prompt_text=final_prompt,
            mode_id=mode_id,
            garment_narrative=garment_narrative,
        )
        for source in catalog_surface_sources:
            compiler_debug["used_clauses"].append(
                {
                    "text": "catalog surface refinement",
                    "source": source,
                }
            )
        final_prompt, catalog_nano_sources = _maybe_refine_catalog_nano_surface(
            prompt_text=final_prompt,
            mode_id=mode_id,
            has_images=has_images,
        )
        for source in catalog_nano_sources:
            compiler_debug["used_clauses"].append(
                {
                    "text": "catalog nano surface refinement",
                    "source": source,
                }
            )
        final_prompt, deduped = _dedupe_surface_sentences(final_prompt)
        if deduped:
            compiler_debug["used_clauses"].append(
                {
                    "text": "surface sentence deduplication",
                    "source": "surface_dedup",
                }
            )
    result["base_prompt"] = final_prompt if pipeline_mode == "text_mode" else compiled_base_prompt
    result["camera_and_realism"] = camera_realism
    result["mode"] = mode_id or None
    result["prompt"] = final_prompt

    compiler_debug["camera_words"] = camera_words
    compiler_debug["base_budget"] = base_budget
    compiler_debug["final_words"] = _count_words(final_prompt)
    compiler_debug["coordination_diagnostics"] = _coordination_diagnostics(final_prompt)
    result["prompt_compiler_debug"] = compiler_debug
    return result
