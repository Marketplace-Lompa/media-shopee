"""
Resolver de casting para diversidade real de modelos humanas.

Esta camada sintetiza uma direção ORIGINAL de casting para o job atual usando
peça, mode e envelope comercial do projeto. Ela não substitui a model_soul:
apenas adiciona direção concreta, anti-colapso e market fit sem grounding no
hot path.
"""
from __future__ import annotations

from typing import Any, Optional

from google.genai import types

from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.mode_identity_soul import get_mode_identity_soul
from agent_runtime.model_soul import get_model_soul
from agent_runtime.parser import _decode_agent_response, try_repair_truncated_json

_NATURAL_PRESTIGE_DRIFT_TOKENS = (
    "architect",
    "designer",
    "curator",
    "gallery",
    "brutalist",
    "academic",
    "intellectual",
    "premium",
    "luxury",
    "pinterest",
    "fashion-forward",
    "corporate",
)

_SOCIAL_COMMERCE_DRIFT_TOKENS = (
    "linkedin",
    "travel blogger",
    "luxury",
    "high-end",
    "quiet luxury",
    "pinterest",
    "office",
    "professional-chic",
    "tastemaker",
)

_CASTING_MIN_SURFACE_FIELDS = 5
_CASTING_MIN_STATES = ("age", "face_structure", "hair", "presence", "expression", "beauty_read", "body")

# 3 variantes rotativas para natural (o mode mais suscetível à convergência).
# Seleção determinística por hash do garment_hint — nenhum LLM envolvido.
_CASTING_FALLBACK_VARIANTS_NATURAL = [
    {
        "age": "mid 20s",
        "face_structure": "round-to-oval face with soft wide cheekbones, full lips and warm expressive eyes",
        "hair": "loose wavy dark-brown hair at shoulder length, slight natural frizz and warm movement",
        "presence": "relaxed wide frame with warm hip-forward posture and comfortable energy",
        "expression": "open and slightly distracted warmth, mouth neutral and eyes alive",
        "beauty_read": "warm light-brown skin with natural sheen, soft unevenness and real-life texture",
        "body": "full-shoulder medium-waist silhouette, soft and proportionate with natural curve presence",
    },
    {
        "age": "early 30s",
        "face_structure": "long-oval face with defined jawline, narrow nose bridge and calm direct eyes",
        "hair": "natural coily 4A hair worn loose and voluminous at crown-length, rich dark brown",
        "presence": "upright lean posture with quiet confidence and contained stillness",
        "expression": "composed attention with soft jaw and unhurried focus",
        "beauty_read": "deep warm-brown skin with matte natural finish and clean health read",
        "body": "lean-to-medium frame with long torso, defined shoulders and balanced hip line",
    },
    {
        "age": "late 20s",
        "face_structure": "heart-shaped face with high cheekbones, soft pointed chin and full arched brows",
        "hair": "curly type-3A auburn-tinted hair at mid-back, light and springy with natural movement",
        "presence": "mid-height with active shoulder energy and light social readiness",
        "expression": "subtle private smile, eyes slightly downcast and naturally lived-in",
        "beauty_read": "medium olive-golden skin with light freckle scatter and warm healthy glow",
        "body": "petite-to-medium build with natural waist definition and easy proportioned stance",
    },
]

# Fallback base — usado por todos os modes como ponto de partida
_CASTING_FALLBACK_STATE = {
    "age": "late 20s",
    "face_structure": "heart or oval face geometry with high cheekbones, soft jawline and balanced mouth",
    "hair": "natural hair with clear texture and movement, color and length appropriate for a Brazilian woman",
    "presence": "balanced shoulder and waist proportions with natural stance",
    "expression": "neutral mouth with quiet, attentive expression",
    "beauty_read": "warm honey skin with clean natural texture and subtle realistic sheen",
    "body": "natural Brazilian silhouette with balanced shoulder-to-hip proportions, medium waist-to-hip ratio and calm torso posture",
}
_CASTING_WEAK_VALUES = {"", "none", "unknown", "not specified", "undefined", "to be defined"}


def _select_natural_fallback_variant(garment_hint: str) -> dict[str, str]:
    """Seleciona uma das 3 variantes de fallback natural por hash do garment_hint.
    Determinístico: mesma peça → mesma variante. Sem LLM."""
    seed = abs(hash(garment_hint.strip().lower())) if garment_hint.strip() else 0
    return dict(_CASTING_FALLBACK_VARIANTS_NATURAL[seed % len(_CASTING_FALLBACK_VARIANTS_NATURAL)])


def _build_wearer_logic(contract: dict[str, Any], aesthetic: dict[str, Any]) -> str:
    """Converte campos estruturais da peça em 1 linha de wearer logic. Python puro, sem LLM."""
    subtype = str(contract.get("garment_subtype") or "").lower().strip()
    volume = str(contract.get("silhouette_volume") or "").lower().strip()
    length = str(contract.get("garment_length") or "").lower().strip()
    formality = str(aesthetic.get("formality") or "").lower().strip()
    vibe = str(aesthetic.get("vibe") or "").lower().strip()
    season = str(aesthetic.get("season") or "").lower().strip()

    parts: list[str] = []

    # Formalidade → presença e postura
    if formality in ("formal", "semi-formal", "elegant"):
        parts.append("upright presence and visible structure")
    elif formality in ("casual", "streetwear", "relaxed"):
        parts.append("easy relaxed stance")
    elif formality in ("sporty", "athletic"):
        parts.append("active body energy")

    # Volume da silhueta → fisicalidade
    if volume in ("fitted", "slim", "body-con"):
        parts.append("clearly defined waist and hip ratio")
    elif volume in ("oversized", "boxy", "loose"):
        parts.append("easy broad-shoulder naturalness")
    elif volume in ("flared", "full", "voluminous"):
        parts.append("confident hip and waist proportion")

    # Comprimento → proporção visível
    if length in ("mini", "micro"):
        parts.append("long lean leg impression")
    elif length in ("maxi", "floor-length"):
        parts.append("tall fluid presence")
    elif length in ("midi", "knee-length"):
        parts.append("balanced mid-length proportion")

    # Vibe → temperatura emocional
    if any(k in vibe for k in ("sensual", "bold", "sultry")):
        parts.append("warm visual magnetism")
    elif any(k in vibe for k in ("playful", "fun", "colorful")):
        parts.append("light expressive personality")
    elif any(k in vibe for k in ("minimal", "clean", "structured")):
        parts.append("calm geometric presence")

    # Sazonalidade → textura de pele visível
    if season in ("summer", "spring"):
        parts.append("healthy exposed skin read")
    elif season in ("winter", "autumn"):
        parts.append("layered grounded warmth")

    if not parts:
        return ""
    return "Garment wearer profile: " + ", ".join(parts) + "."


def _build_casting_fallback_direction(mode_id: str, *, user_prompt: str = "", garment_hint: str = "") -> dict[str, Any]:
    """Retorna direção de casting determinística quando o fluxo principal falha."""
    mode = str(mode_id or "").strip().lower() or "natural"

    # Natural: variante rotativa por hash da peça — quebra a convergência no fallback
    if mode == "natural":
        fallback_state = _select_natural_fallback_variant(garment_hint)
    else:
        fallback_state = dict(_CASTING_FALLBACK_STATE)

    if mode == "catalog_clean":
        fallback_state.update(
            {
                "age": "late 20s",
                "face_structure": "oval-to-heart face with polished cheekbone definition and soft balanced jawline",
                "hair": "neat natural hair with clean movement and commercial polish",
                "presence": "well-lit commercial confidence with calm shoulders and upright posture",
                "expression": "approachable neutral expression with gentle focus",
                "beauty_read": "clean skin tone and subtle realistic shine",
                "body": "clean body proportions with defined shoulders and waist balance",
            }
        )
    elif mode == "lifestyle":
        fallback_state.update(
            {
                "face_structure": "clear contemporary face with high cheekbones, soft jawline and open eye line",
                "expression": "friendly attention with social confidence",
                "presence": "active posture with contemporary movement readiness",
                "body": "athletic-smooth silhouette with balanced shoulders and hips",
            }
        )
    elif mode == "editorial_commercial":
        fallback_state.update(
            {
                "face_structure": "editorial-ready face geometry with strong cheekbone contour and poised jawline",
                "expression": "firm but warm focus with controlled softness",
                "body": "architectural silhouette with elegant shoulder and waist alignment",
            }
        )

    # Reforça sinais de identidade sem inventar persona específica.
    chosen_label = "deterministic_native_casting_guardrail"
    chosen_direction = {
        "label": chosen_label,
        "age_logic": fallback_state["age"],
        "face_geometry": fallback_state["face_structure"],
        "skin_logic": fallback_state["beauty_read"],
        "hair_logic": fallback_state["hair"],
        "body_logic": fallback_state["body"],
        "presence_logic": fallback_state["presence"],
        "expression_logic": fallback_state["expression"],
        "makeup_logic": "minimal and natural",
        "beauty_logic": fallback_state["beauty_read"],
        "platform_presence": "social-commerce native commercial presence",
        "commercial_read": "commercially attractive, approachably Brazilian",
        "distinction_markers": ["high cheekbones", "soft jawline", "neutral mouth"],
        "rationale": "fallback deterministic cast for missing LLM direction",
    }

    profile_hint = (
        "A realistic Brazilian model in a natural commercial look: "
        f"{fallback_state['age']} with {fallback_state['face_structure']}, "
        f"{fallback_state['hair']}, and {fallback_state['body']}."
    )
    if garment_hint:
        profile_hint = f"{garment_hint}: " + profile_hint
    if user_prompt:
        profile_hint = f"User intent ({user_prompt[:80]}): " + profile_hint

    return {
        "research_signals": [
            "ensure realistic Brazilian commercial attractiveness",
            "preserve garment priority and avoid reference identity reuse",
            "keep model details photorealistic and balanced",
            "avoid age inflation and prestige-coded defaults",
            "use creative facial and body geometry without inventing real identity",
        ],
        "market_fit_summary": "fallback profile for a commercially viable, high-trust Brazilian social-commerce model",
        "candidate_directions": [chosen_direction],
        "chosen_label": chosen_label,
        "chosen_direction": chosen_direction,
        "profile_hint": profile_hint,
        "casting_state": fallback_state,
        "anti_collapse_signals": [
            "do_not_invoke_unknown_identity",
            "no_premium_stale_archetypes",
            "no_aging_up_or_down_beyond_request",
            "no_reference_identity_reuse",
            "no_premium_lifestyle_drift",
        ],
        "confidence": 0.61,
        "fallback_applied": True,
    }


_CANDIDATE_SCHEMA = {
    "type": "object",
    "required": [
        "label",
        "age_logic",
        "face_geometry",
        "skin_logic",
        "hair_logic",
        "body_logic",
        "presence_logic",
        "expression_logic",
        "makeup_logic",
        "beauty_logic",
        "platform_presence",
        "commercial_read",
        "distinction_markers",
        "rationale",
    ],
    "properties": {
        "label": {"type": "string"},
        "age_logic": {"type": "string"},
        "face_geometry": {"type": "string"},
        "skin_logic": {"type": "string"},
        "hair_logic": {"type": "string"},
        "body_logic": {"type": "string"},
        "presence_logic": {"type": "string"},
        "expression_logic": {"type": "string"},
        "makeup_logic": {"type": "string"},
        "beauty_logic": {"type": "string"},
        "platform_presence": {"type": "string"},
        "commercial_read": {"type": "string"},
        "distinction_markers": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
}

CASTING_DIRECTION_SCHEMA = {
    "type": "object",
    "required": [
        "research_signals",
        "market_fit_summary",
        "candidate_directions",
        "chosen_label",
        "chosen_direction",
        "profile_hint",
        "casting_state",
        "anti_collapse_signals",
        "confidence",
    ],
    "properties": {
        "research_signals": {"type": "array", "items": {"type": "string"}},
        "market_fit_summary": {"type": "string"},
        "candidate_directions": {"type": "array", "items": _CANDIDATE_SCHEMA},
        "chosen_label": {"type": "string"},
        "chosen_direction": _CANDIDATE_SCHEMA,
        "profile_hint": {"type": "string"},
        "casting_state": {
            "type": "object",
            "required": ["age", "face_structure", "hair", "presence", "expression", "beauty_read", "body"],
            "properties": {
                "age": {"type": "string"},
                "face_structure": {"type": "string"},
                "hair": {"type": "string"},
                "presence": {"type": "string"},
                "expression": {"type": "string"},
                "beauty_read": {"type": "string"},
                "body": {"type": "string"},
            },
        },
        "anti_collapse_signals": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
}


def _clean_text(value: Any, *, limit: int = 220) -> str:
    return " ".join(str(value or "").strip().split())[:limit].strip()


def _clean_list(values: Any, *, limit: int = 6, item_limit: int = 120) -> list[str]:
    items = []
    for value in values or []:
        cleaned = _clean_text(value, limit=item_limit)
        if cleaned:
            items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def _normalize_candidate(raw: Optional[dict[str, Any]]) -> dict[str, Any]:
    payload = raw or {}
    return {
        "label": _clean_text(payload.get("label"), limit=60),
        "age_logic": _clean_text(payload.get("age_logic"), limit=90),
        "face_geometry": _clean_text(payload.get("face_geometry"), limit=140),
        "skin_logic": _clean_text(payload.get("skin_logic"), limit=140),
        "hair_logic": _clean_text(payload.get("hair_logic"), limit=160),
        "body_logic": _clean_text(payload.get("body_logic"), limit=140),
        "presence_logic": _clean_text(payload.get("presence_logic"), limit=140),
        "expression_logic": _clean_text(payload.get("expression_logic"), limit=140),
        "makeup_logic": _clean_text(payload.get("makeup_logic"), limit=140),
        "beauty_logic": _clean_text(payload.get("beauty_logic"), limit=140),
        "platform_presence": _clean_text(payload.get("platform_presence"), limit=140),
        "commercial_read": _clean_text(payload.get("commercial_read"), limit=140),
        "distinction_markers": _clean_list(payload.get("distinction_markers"), limit=4, item_limit=80),
        "rationale": _clean_text(payload.get("rationale"), limit=180),
    }


def _derive_casting_state(candidate: dict[str, Any]) -> dict[str, str]:
    return {
        "age": _clean_text(candidate.get("age_logic"), limit=60),
        "face_structure": _clean_text(candidate.get("face_geometry"), limit=140),
        "hair": _clean_text(candidate.get("hair_logic"), limit=160),
        "presence": _clean_text(candidate.get("presence_logic"), limit=140),
        "expression": _clean_text(candidate.get("expression_logic"), limit=140),
        "beauty_read": _clean_text(candidate.get("beauty_logic"), limit=140),
        "body": _clean_text(candidate.get("body_logic"), limit=140),
    }


def _is_casting_state_value_weak(value: Any) -> bool:
    normalized = _clean_text(value, limit=240).lower()
    return not normalized or normalized in _CASTING_WEAK_VALUES


def _enforce_casting_state_minimum(state: dict[str, str]) -> tuple[dict[str, str], bool]:
    """Garante que o state tenha atributos físicos mínimos para direcionamento de casting."""
    normalized_state = {
        key: _clean_text(state.get(key), limit=160)
        for key in _CASTING_MIN_STATES
    }

    had_minimum = 0
    for key in _CASTING_MIN_STATES:
        if not _is_casting_state_value_weak(normalized_state.get(key, "")):
            had_minimum += 1

    used_fallback = False
    if had_minimum < _CASTING_MIN_SURFACE_FIELDS:
        for key in _CASTING_MIN_STATES:
            if had_minimum >= _CASTING_MIN_SURFACE_FIELDS:
                break
            if _is_casting_state_value_weak(normalized_state.get(key, "")):
                fallback_value = _CASTING_FALLBACK_STATE.get(key)
                if fallback_value:
                    normalized_state[key] = fallback_value
                    had_minimum += 1
                    used_fallback = True
        # Se ainda não alcançou mínimo por qualquer motivo, completa com o restante do estado base.
        if had_minimum < _CASTING_MIN_SURFACE_FIELDS:
            for key in _CASTING_MIN_STATES:
                if had_minimum >= _CASTING_MIN_SURFACE_FIELDS:
                    break
                if _is_casting_state_value_weak(normalized_state.get(key, "")):
                    normalized_state[key] = normalized_state[key] or _CASTING_FALLBACK_STATE.get(key, "")
                    had_minimum += 1
                    used_fallback = True

    return normalized_state, used_fallback


def _derive_profile_hint(candidate: dict[str, Any]) -> str:
    parts = [
        _clean_text(candidate.get("age_logic"), limit=60),
        _clean_text(candidate.get("face_geometry"), limit=90),
        _clean_text(candidate.get("hair_logic"), limit=100),
        _clean_text(candidate.get("beauty_logic"), limit=80),
        _clean_text(candidate.get("platform_presence"), limit=80),
    ]
    return _clean_text(", ".join(part for part in parts if part), limit=240)


def _normalize_casting_direction(payload: Optional[dict[str, Any]]) -> dict[str, Any]:
    raw = payload or {}
    candidates = [
        normalized
        for normalized in (_normalize_candidate(item) for item in (raw.get("candidate_directions") or []))
        if normalized.get("label")
    ][:3]

    chosen_label = _clean_text(raw.get("chosen_label"), limit=60)
    chosen_direction = _normalize_candidate(raw.get("chosen_direction") if isinstance(raw.get("chosen_direction"), dict) else {})
    if not chosen_direction.get("label") and chosen_label:
        for candidate in candidates:
            if candidate.get("label") == chosen_label:
                chosen_direction = candidate
                break
    if not chosen_direction.get("label") and candidates:
        chosen_direction = candidates[0]
    if not chosen_label and chosen_direction.get("label"):
        chosen_label = chosen_direction["label"]

    raw_casting_state = raw.get("casting_state") if isinstance(raw.get("casting_state"), dict) else {}
    casting_state = {
        "age": _clean_text(raw_casting_state.get("age"), limit=60),
        "face_structure": _clean_text(raw_casting_state.get("face_structure"), limit=140),
        "hair": _clean_text(raw_casting_state.get("hair"), limit=160),
        "presence": _clean_text(raw_casting_state.get("presence"), limit=140),
        "expression": _clean_text(raw_casting_state.get("expression"), limit=140),
        "beauty_read": _clean_text(raw_casting_state.get("beauty_read"), limit=140),
        "body": _clean_text(raw_casting_state.get("body"), limit=140),
    }
    if not any(casting_state.values()):
        casting_state = _derive_casting_state(chosen_direction)
    confidence = max(0.0, min(1.0, float(raw.get("confidence") or 0.0)))
    casting_state, _fallback_applied = _enforce_casting_state_minimum(casting_state)
    if _fallback_applied:
        confidence = max(confidence, 0.52)

    profile_hint = _clean_text(raw.get("profile_hint"), limit=240) or _derive_profile_hint(chosen_direction)
    if _fallback_applied and not profile_hint:
        profile_hint = "New Brazilian female model profile with clear face, hair, and body coherence."

    return {
        "research_signals": _clean_list(raw.get("research_signals"), limit=8, item_limit=160),
        "market_fit_summary": _clean_text(raw.get("market_fit_summary"), limit=180),
        "candidate_directions": candidates,
        "chosen_label": chosen_label,
        "chosen_direction": chosen_direction,
        "profile_hint": profile_hint,
        "casting_state": casting_state,
        "anti_collapse_signals": _clean_list(raw.get("anti_collapse_signals"), limit=6, item_limit=120),
        "confidence": confidence,
        "fallback_applied": _fallback_applied,
    }


def _get_mode_casting_mandate(mode_id: Optional[str]) -> str:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return (
            "Choose a commercially appealing woman whose face, body, and garment readability are immediately clear. "
            "She should feel brand-safe, attractive, and trustworthy for mainstream Brazilian ecommerce. "
            "Differentiate within that high-conversion band rather than escaping into severity, anonymity, or maturity inflation."
        )
    if normalized == "natural":
        return (
            "Choose a woman who feels real and lightly unproduced, but still beautiful, warm, contemporary, and commercially desirable. "
            "Natural means less staged and less beauty-set-up, not older, drained, severe, prestige-coded, or anti-beauty. "
            "She should still read as someone who could convert fashion in Shopee, TikTok, or Instagram through approachable attractiveness, not rarefied taste signaling."
        )
    if normalized == "lifestyle":
        return (
            "Choose a woman whose social presence feels active, contemporary, and creator-native. "
            "She should feel attractive, memorable, and commercially strong in social-commerce life, not generic, corporate, or conceptually austere."
        )
    if normalized == "editorial_commercial":
        return (
            "Choose a woman with stronger visual character and sharper fashion authority, while keeping clear desirability and sellability. "
            "Editorial-commercial strength should come from distinctive beauty and presence, not from aging her up or making her severe by default."
        )
    return (
        "Choose a commercially effective, attractive, high-trust Brazilian woman for mainstream social-commerce. "
        "Differentiate her clearly, but keep her inside a believable, desirable, creator-friendly market band."
    )


def _get_market_fit_band(mode_id: Optional[str]) -> str:
    normalized = str(mode_id or "natural").strip().lower()
    base = (
        "NON-NEGOTIABLE MARKET BAND:\n"
        "- The woman must feel commercially strong for Brazilian social-commerce fashion imagery.\n"
        "- She must read as clearly adult, attractive, trustworthy, memorable, and socially native.\n"
        "- Keep the center of gravity in the mainstream high-conversion creator/seller/presenter band for Shopee, TikTok, and Instagram.\n"
        "- Keep her closer to a product-led creator, presenter, or seller than to a luxury lifestyle blogger, office-professional archetype, or niche taste-maker.\n"
        "- Diversity must happen INSIDE that band, not by leaving it.\n"
        "- Do not solve originality with age inflation, austerity, severity, drained beauty, overt intellectualization, or hyper-corporate energy unless the garment clearly justifies it.\n"
        "- When the user asks for elegant, polished, refined, or sophisticated, translate that as desirable and commercially aspirational, not older or rigid.\n"
    )
    if normalized == "natural":
        return (
            base
            + "- In natural mode, lower production and lower status signaling are good, but the woman must still feel beautiful, current, and creator-relevant.\n"
            + "- Prefer a face that feels warm and credible in real life over a face that feels stern, drained, or deliberately serious.\n"
            + "- Avoid prestige-coded creative-class cues such as designer, architect, curator, concept-store, or premium-luxury energy.\n"
            + "- Keep the commercial read accessible, desirable, and everyday-social rather than elite, rarefied, or niche-taste.\n"
        )
    if normalized == "catalog_clean":
        return (
            base
            + "- In catalog_clean, keep beauty clean, legible, and broadly appealing. Avoid drifting into anonymous mannequin logic or mature luxury codes.\n"
        )
    if normalized == "lifestyle":
        return (
            base
            + "- In lifestyle, she should feel socially visible and naturally magnetic, like someone whose presence already works inside product-led social media.\n"
            + "- Avoid drifting into luxury travel, aspirational officewear, or distant premium creator codes.\n"
        )
    if normalized == "editorial_commercial":
        return (
            base
            + "- In editorial_commercial, sharpen distinction and taste, but keep her desirable and commercially usable rather than coldly conceptual.\n"
        )
    return base


def _needs_natural_market_recenter(payload: dict[str, Any], mode_id: Optional[str]) -> bool:
    if str(mode_id or "").strip().lower() != "natural":
        return False
    chosen = payload.get("chosen_direction") or {}
    haystack = " ".join(
        str(item or "").strip().lower()
        for item in (
            payload.get("market_fit_summary"),
            payload.get("profile_hint"),
            chosen.get("label"),
            chosen.get("presence_logic"),
            chosen.get("beauty_logic"),
            chosen.get("platform_presence"),
            chosen.get("commercial_read"),
            chosen.get("rationale"),
        )
    )
    return any(token in haystack for token in _NATURAL_PRESTIGE_DRIFT_TOKENS)


def _needs_social_commerce_recenter(payload: dict[str, Any]) -> bool:
    chosen = payload.get("chosen_direction") or {}
    haystack = " ".join(
        str(item or "").strip().lower()
        for item in (
            payload.get("market_fit_summary"),
            payload.get("profile_hint"),
            chosen.get("platform_presence"),
            chosen.get("commercial_read"),
            chosen.get("rationale"),
        )
    )
    return any(token in haystack for token in _SOCIAL_COMMERCE_DRIFT_TOKENS)


def _build_casting_instruction(
    *,
    mode_lines: list[str],
    model_soul: str,
    mode_casting_mandate: str,
    market_fit_band: str,
    mode_id: Optional[str],
    prompt_text: str,
    garment_text: str,
    analysis_text: str,
    contract: dict[str, Any],
    aesthetic: dict[str, Any],
    has_images: bool,
    wearer_logic: str = "",
) -> str:
    return (
        "Synthesize a casting direction for this job.\n"
        "You are solving only the HUMAN CASTING for a Brazilian social-commerce fashion image.\n"
        "Create an original woman. Do not imitate any real person.\n"
        "First map three materially different candidate directions, then choose one.\n"
        "The three candidates must differ in at least three dimensions among: age energy, face geometry, skin read, hair behavior, body read, polish level, and social presence.\n"
        "HAIR DIVERSITY MANDATE: each candidate must have a materially different hair profile. "
        "Actively rotate between straight, wavy, curly (type 2A-4A), short, medium, long, and color families "
        "(jet black, dark brown, auburn, copper, sandy blonde, highlighted). "
        "Brazilian women have vast hair diversity — reflect that. Do not default to brunette waves.\n"
        "All candidates must remain inside the high-conversion beauty/commercial band for Brazilian social-commerce.\n"
        "Do not solve distinction by aging her up, making her severe, academic, architectural, drained, corporate, or conceptually intellectual unless the garment explicitly demands that.\n"
        "Do not drift into luxury travel, office-professional, Pinterest-only, or premium-lifestyle identities unless the garment explicitly demands that.\n"
        "Prioritize the winning direction in this order: market fit, garment fit, mode fit, distinction.\n\n"
        "<MODE_IDENTITY>\n" + "\n".join(mode_lines) + "\n</MODE_IDENTITY>\n\n"
        "<MODEL_SOUL>\n" + model_soul + "\n</MODEL_SOUL>\n\n"
        "<MODE_CASTING_MANDATE>\n" + mode_casting_mandate + "\n</MODE_CASTING_MANDATE>\n\n"
        "<MARKET_FIT_BAND>\n" + market_fit_band + "</MARKET_FIT_BAND>\n\n"
        "<JOB_CONTEXT>\n"
        f"- mode_id: {str(mode_id or 'natural').strip().lower()}\n"
        f"- user_prompt: {prompt_text}\n"
        f"- garment_hint: {garment_text or 'unknown'}\n"
        f"- image_analysis: {analysis_text or 'unknown'}\n"
        f"- garment_subtype: {str(contract.get('garment_subtype') or 'unknown')}\n"
        f"- silhouette_volume: {str(contract.get('silhouette_volume') or 'unknown')}\n"
        f"- garment_length: {str(contract.get('garment_length') or 'unknown')}\n"
        f"- garment_formality: {str(aesthetic.get('formality') or 'unknown')}\n"
        f"- garment_season: {str(aesthetic.get('season') or 'unknown')}\n"
        f"- garment_vibe: {str(aesthetic.get('vibe') or 'unknown')}\n"
        + (f"- wearer_logic: {weaver_logic}\n" if (weaver_logic := wearer_logic) else "")
        + f"- reference_mode: {'true' if has_images else 'false'}\n"
        "</JOB_CONTEXT>\n\n"
        "OUTPUT RULES:\n"
        "- research_signals: exactly 5 short inferred market signals for this job.\n"
        "- market_fit_summary: one short line on why the winner is commercially right for Brazilian social-commerce.\n"
        "- candidate_directions: exactly 3 options, all original and materially different.\n"
        "- Every candidate must feel attractive, saleable, and socially native.\n"
        "- Use beauty_logic, platform_presence, and commercial_read to keep the winner in the correct market band.\n"
        "- Let differentiation come from geometry, skin read, hair behavior, polish level, and presence rather than age inflation.\n"
        "- chosen_direction: the best direction for this specific garment and mode.\n"
        "- profile_hint: one compact sentence summarizing the chosen casting direction.\n"
        "- casting_state: compact fields for downstream enforcement.\n"
        "- anti_collapse_signals: default patterns to avoid for this job.\n"
        "- Keep fields compact. Prefer short phrases over paragraphs.\n"
        "- candidate_directions should be especially compact.\n"
        "- distinction_markers should have at most 3 items.\n"
        "- Return strict JSON only.\n"
    )


def resolve_casting_direction(
    *,
    mode_id: Optional[str],
    user_prompt: Optional[str],
    garment_hint: Optional[str],
    image_analysis: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    garment_aesthetic: Optional[dict[str, Any]] = None,
    has_images: bool = False,
) -> dict[str, Any]:
    garment_text = _clean_text(garment_hint, limit=140)
    analysis_text = _clean_text(image_analysis, limit=500)
    contract = structural_contract or {}
    aesthetic = garment_aesthetic or {}
    mode_lines = get_mode_identity_soul(mode_id)
    model_soul = get_model_soul(garment_context=garment_text, mode_id=mode_id or "")
    mode_casting_mandate = _get_mode_casting_mandate(mode_id)
    market_fit_band = _get_market_fit_band(mode_id)
    prompt_text = _clean_text(user_prompt, limit=240) or "none"

    def _call_json_model(raw_instruction: str, *, temperature: float, max_attempts: int) -> Any:
        _ = max_attempts
        return generate_structured_json(
            parts=[types.Part(text=raw_instruction)],
            schema=CASTING_DIRECTION_SCHEMA,
            temperature=temperature,
            max_tokens=1800,
            thinking_budget=0,
        )
    wearer_logic = _build_wearer_logic(contract, aesthetic)
    instruction = _build_casting_instruction(
        mode_lines=mode_lines,
        model_soul=model_soul,
        mode_casting_mandate=mode_casting_mandate,
        market_fit_band=market_fit_band,
        mode_id=mode_id,
        prompt_text=prompt_text,
        garment_text=garment_text,
        analysis_text=analysis_text,
        contract=contract,
        aesthetic=aesthetic,
        has_images=has_images,
        wearer_logic=wearer_logic,
    )
    try:
        response = _call_json_model(instruction, temperature=0.35, max_attempts=3)
        parsed = _decode_agent_response(response)
    except Exception as exc:
        err_msg = str(exc)
        print(f"[MODEL_GROUNDING] ⚠️ first parse failed: {err_msg}")
        repaired = try_repair_truncated_json(err_msg)
        if repaired is not None:
            parsed = repaired
            response = None
        else:
            retry_instruction = (
                instruction
                + "\n\n[RETRY TRIGGERED]: The previous response was not valid JSON. "
                "Return EXACTLY one compact JSON object with the requested keys and nothing else. "
                "Keep every field short and compact."
            )
            retry_response = _call_json_model(retry_instruction, temperature=0.2, max_attempts=2)
            try:
                parsed = _decode_agent_response(retry_response)
                response = retry_response
            except Exception as retry_exc:
                print(f"[MODEL_GROUNDING] ❌ retry parse failed: {retry_exc}")
                return {}

    normalized = _normalize_casting_direction(parsed if isinstance(parsed, dict) else {})
    if not normalized.get("chosen_direction") or not (normalized.get("chosen_direction") or {}).get("label"):
        compact_instruction = (
            instruction
            + "\n\n[COMPACT RECOVERY]: The previous output was incomplete. "
            "Use extremely compact phrasing. research_signals=5 items only. "
            "candidate_directions=3 very short options. chosen_direction short but complete."
        )
        try:
            recovery_response = _call_json_model(compact_instruction, temperature=0.2, max_attempts=2)
            recovery_parsed = _decode_agent_response(recovery_response)
            normalized = _normalize_casting_direction(recovery_parsed if isinstance(recovery_parsed, dict) else {})
            response = recovery_response
        except Exception as recovery_exc:
            print(f"[MODEL_GROUNDING] ❌ compact recovery failed: {recovery_exc}")
            return _build_casting_fallback_direction(
                mode_id=mode_id or "",
                user_prompt=prompt_text,
                garment_hint=garment_text,
            )

    if not normalized.get("chosen_direction") or not (normalized.get("chosen_direction") or {}).get("label"):
        return _build_casting_fallback_direction(
            mode_id=mode_id or "",
            user_prompt=prompt_text,
            garment_hint=garment_text,
        )
    if not normalized.get("chosen_direction") or not (normalized.get("chosen_direction") or {}).get("label"):
        return {}

    if _needs_natural_market_recenter(normalized, mode_id):
        recenter_instruction = (
            instruction
            + "\n\n[MARKET RECENTER]: The previous solution drifted into prestige-coded or creative-class casting."
            " Re-solve the JSON while keeping the woman attractive, socially native, accessible, and high-conversion for mainstream Brazilian social-commerce."
            " In natural mode specifically, avoid architect/designer/curator/intellectual/luxury-coded energy."
            " Keep her beautiful and current, with approachable everyday desirability."
        )
        try:
            recenter_response = _call_json_model(recenter_instruction, temperature=0.2, max_attempts=2)
            recenter_parsed = _decode_agent_response(recenter_response)
            recentered = _normalize_casting_direction(recenter_parsed if isinstance(recenter_parsed, dict) else {})
            if recentered.get("chosen_direction") and (recentered.get("chosen_direction") or {}).get("label"):
                normalized = recentered
                response = recenter_response
        except Exception as recenter_exc:
            print(f"[MODEL_GROUNDING] ⚠️ market recenter failed: {recenter_exc}")
    if _needs_social_commerce_recenter(normalized):
        social_recenter_instruction = (
            instruction
            + "\n\n[SOCIAL-COMMERCE RECENTER]: The previous solution drifted into office-professional, luxury-lifestyle, Pinterest-only, or premium creator codes."
            " Re-solve the JSON with a stronger product-led marketplace creator/seller/presenter feel."
            " Keep the woman beautiful, trustworthy, contemporary, and socially magnetic, but closer to conversion-oriented Brazilian social-commerce than to distant premium aspiration."
        )
        try:
            social_recenter_response = _call_json_model(social_recenter_instruction, temperature=0.2, max_attempts=2)
            social_recenter_parsed = _decode_agent_response(social_recenter_response)
            social_recentered = _normalize_casting_direction(
                social_recenter_parsed if isinstance(social_recenter_parsed, dict) else {}
            )
            if social_recentered.get("chosen_direction") and (social_recentered.get("chosen_direction") or {}).get("label"):
                normalized = social_recentered
                response = social_recenter_response
        except Exception as social_recenter_exc:
            print(f"[MODEL_GROUNDING] ⚠️ social-commerce recenter failed: {social_recenter_exc}")

    normalized["grounding_titles"] = []
    if normalized.get("confidence", 0.0) > 0.0:
        chosen = normalized.get("chosen_direction") or {}
        print(
            "[MODEL_GROUNDING] ✅ "
            f"label={normalized.get('chosen_label') or chosen.get('label') or 'unknown'} "
            f"age={chosen.get('age_logic', '')[:40]} "
            f"hair={chosen.get('hair_logic', '')[:50]} "
            f"conf={normalized['confidence']:.2f}"
        )
    return normalized
