"""
Política de grounding (auto/on/off) + triage por score.
"""
from __future__ import annotations

from typing import Optional

from config import (
    DEFAULT_GROUNDING_STRATEGY,
    ENABLE_GROUNDING,
    GROUNDING_THRESHOLD_HIGH,
    GROUNDING_THRESHOLD_LOW,
)

_ATYPICAL_KEYWORDS = [
    "ruana",
    "poncho",
    "open-front",
    "frente aberta",
    "batwing",
    "dolman",
    "manga morcego",
    "kimono",
    "kaftan",
    "pelerine",
    "cocoon",
    "mullet",
    "assimetr",
    "xale",
]
_TEXTURE_KEYWORDS = [
    "crochê",
    "croche",
    "tricot",
    "tricô",
    "knit",
    "stitch",
    "ponto",
    "textura",
    "listra",
]
_AMBIGUOUS_TERMS = [
    ("poncho", "cardigan"),
    ("poncho", "ruana"),
    ("cape", "cardigan"),
    ("xale", "cardigan"),
]
_TEMPORAL_KEYWORDS = [
    "tendência",
    "tendencia",
    "trend",
    "season",
    "primavera",
    "verão",
    "verao",
    "outono",
    "inverno",
    "2024",
    "2025",
    "2026",
    "coleção",
    "colecao",
]
_SIMPLE_GARMENT_KEYWORDS = [
    "camiseta",
    "t-shirt",
    "camisa",
    "blusa básica",
    "blusa basica",
    "calça",
    "calca",
    "short",
    "saia",
    "vestido reto",
    "regata",
    "moletom",
]


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def normalize_grounding_strategy(
    grounding_strategy: Optional[str],
    use_grounding_legacy: bool,
) -> str:
    strategy = (grounding_strategy or "").strip().lower()
    if strategy in {"auto", "on", "off"}:
        return strategy
    if use_grounding_legacy:
        return "on"
    if DEFAULT_GROUNDING_STRATEGY in {"auto", "on", "off"}:
        return DEFAULT_GROUNDING_STRATEGY
    return "auto"


def compute_grounding_triage(
    user_prompt: Optional[str],
    image_analysis: Optional[str],
    has_images: bool,
) -> dict:
    prompt_text = (user_prompt or "").strip()
    analysis_text = (image_analysis or "").strip()
    text = f"{prompt_text} {analysis_text}".lower()
    pipeline_mode = "reference_mode" if has_images else "text_mode"

    atypical_hits = sum(1 for k in _ATYPICAL_KEYWORDS if k in text)
    texture_hits = sum(1 for k in _TEXTURE_KEYWORDS if k in text)
    ambiguous_hits = sum(1 for a, b in _AMBIGUOUS_TERMS if a in text and b in text)
    temporal_hits = sum(1 for k in _TEMPORAL_KEYWORDS if k in text)
    simple_hits = sum(1 for k in _SIMPLE_GARMENT_KEYWORDS if k in text)

    atypical_shape = 1.0 if atypical_hits > 0 else 0.0

    texture_risk = _clamp(
        0.12 * min(texture_hits, 4)
        + (0.16 if has_images else 0.0)
    )
    name_ambiguity = _clamp(
        0.14
        + 0.28 * min(ambiguous_hits, 2)
        + (0.2 if atypical_hits > 0 else 0.0)
    )
    temporal_signal = _clamp(0.3 * min(temporal_hits, 2))

    silhouette_confidence = 0.9
    if has_images:
        silhouette_confidence -= 0.12
    if not prompt_text and has_images:
        silhouette_confidence -= 0.12
    if atypical_hits > 0:
        silhouette_confidence -= 0.28
    if ambiguous_hits > 0:
        silhouette_confidence -= 0.16
    if simple_hits > 0:
        silhouette_confidence += 0.06
    silhouette_confidence = _clamp(silhouette_confidence)

    if has_images:
        complexity_score = _clamp(
            0.18
            + (0.34 if atypical_hits > 0 else 0.0)
            + 0.14 * min(texture_hits, 3) / 3
            + (0.20 if ambiguous_hits > 0 else 0.0)
            + (0.08 if simple_hits == 0 else 0.0)
        )
    else:
        complexity_score = _clamp(
            0.04
            + (0.24 if atypical_hits > 0 else 0.0)
            + (0.22 if ambiguous_hits > 0 else 0.0)
            + temporal_signal
            + 0.08 * min(texture_hits, 2) / 2
        )

    if has_images and complexity_score >= GROUNDING_THRESHOLD_HIGH:
        recommended_mode = "full"
    elif complexity_score >= GROUNDING_THRESHOLD_LOW:
        recommended_mode = "lexical"
    else:
        recommended_mode = "off"

    if has_images and recommended_mode == "off":
        # Em fluxo com referência, se há indício de atipicidade/incerteza,
        # nunca deixar auto em OFF.
        if atypical_hits > 0:
            recommended_mode = "lexical"
        elif silhouette_confidence < 0.82 and (texture_hits > 0 or ambiguous_hits > 0):
            recommended_mode = "lexical"

    if not has_images and recommended_mode == "off":
        if temporal_hits > 0 or atypical_hits > 0 or ambiguous_hits > 0:
            recommended_mode = "lexical"

    hint_confidence = _clamp(
        0.88
        - (0.24 if atypical_hits > 0 else 0.0)
        - 0.16 * min(ambiguous_hits, 2)
        - (0.08 if temporal_hits > 0 else 0.0)
        + (0.06 if simple_hits > 0 else 0.0)
    )

    garment_hypothesis = (analysis_text or prompt_text or "garment with unclear silhouette").strip()
    if len(garment_hypothesis) > 120:
        garment_hypothesis = garment_hypothesis[:120].rstrip() + "..."

    if recommended_mode == "full":
        trigger_reason = "high_complexity_atypical_reference"
    elif recommended_mode == "lexical" and has_images and atypical_hits > 0:
        trigger_reason = "atypical_reference_floor"
    elif recommended_mode == "lexical" and not has_images and temporal_hits > 0:
        trigger_reason = "temporal_or_trend_prompt"
    elif recommended_mode == "lexical":
        trigger_reason = "ambiguous_or_uncertain_garment"
    else:
        trigger_reason = "simple_or_high_confidence_case"

    return {
        "pipeline_mode": pipeline_mode,
        "garment_hypothesis": garment_hypothesis,
        "garment_hint": garment_hypothesis,
        "hint_confidence": round(hint_confidence, 3),
        "silhouette_confidence": round(silhouette_confidence, 3),
        "atypical_shape": round(atypical_shape, 3),
        "texture_risk": round(texture_risk, 3),
        "name_ambiguity": round(name_ambiguity, 3),
        "temporal_signal": round(temporal_signal, 3),
        "complexity_score": round(complexity_score, 3),
        "grounding_score": round(complexity_score, 3),
        "recommended_mode": recommended_mode,
        "trigger_reason": trigger_reason,
    }


def resolve_grounding_mode(strategy: str, recommended_mode: str) -> str:
    if not ENABLE_GROUNDING:
        return "off"
    if strategy == "off":
        return "off"
    if strategy == "on":
        return "full" if recommended_mode == "full" else "lexical"
    return recommended_mode
