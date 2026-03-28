"""
Resolver de direção de styling após a triagem da peça hero.

Esta camada existe para responder, de forma contextual e soul-first, como o
look deve se completar ao redor do produto analisado. Ela NÃO faz parte da
triagem estrutural da peça.
"""
from __future__ import annotations

from typing import Any, Optional

from google.genai import types

from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.mode_identity_soul import get_mode_identity_soul
from agent_runtime.parser import _decode_agent_response, try_repair_truncated_json
from agent_runtime.styling_soul import get_styling_soul


STYLING_DIRECTION_SCHEMA = {
    "type": "object",
    "required": [
        "product_topology",
        "hero_family",
        "hero_components",
        "completion_slots",
        "completion_strategy",
        "primary_completion",
        "secondary_completion",
        "footwear_direction",
        "accessories_optional",
        "outer_layer_optional",
        "finish_logic",
        "direction_summary",
        "confidence",
    ],
    "properties": {
        "product_topology": {
            "type": "string",
            "enum": [
                "single_piece",
                "coordinated_set",
                "garment_plus_coordinated_accessory",
                "unclear",
            ],
        },
        "hero_family": {
            "type": "string",
            "enum": [
                "top_layer",
                "lower_body",
                "one_piece",
                "footwear",
                "accessory",
                "unclear",
            ],
        },
        "hero_components": {"type": "array", "items": {"type": "string"}},
        "completion_slots": {"type": "array", "items": {"type": "string"}},
        "completion_strategy": {"type": "string"},
        "primary_completion": {"type": "string"},
        "secondary_completion": {"type": "string"},
        "footwear_direction": {"type": "string"},
        "accessories_optional": {"type": "string"},
        "outer_layer_optional": {"type": "string"},
        "finish_logic": {"type": "string"},
        "direction_summary": {"type": "string"},
        "confidence": {"type": "number"},
    },
}

_LOWER_BODY_HINTS = (
    "calça", "pants", "trouser", "trousers", "jeans", "saia", "skirt",
    "short", "shorts", "bermuda", "legging",
)
_ONE_PIECE_HINTS = (
    "dress", "vestido", "jumpsuit", "macacão", "macacao", "romper",
)
_FOOTWEAR_HINTS = (
    "shoe", "shoes", "boot", "boots", "loafer", "loafer", "sneaker",
    "sandália", "sandalia", "sapato", "bota", "tênis", "tenis",
)
_ACCESSORY_HINTS = (
    "bag", "bolsa", "belt", "cinto", "scarf", "lenço", "lenco",
    "hat", "chapéu", "chapeu", "earring", "brinco",
)
_TOP_LAYER_SUBTYPES = {
    "standard_cardigan", "ruana_wrap", "poncho", "cape", "kimono",
    "bolero", "vest", "jacket", "pullover", "other",
}


def _clean_text(value: Any, *, limit: int = 220) -> str:
    return " ".join(str(value or "").strip().split())[:limit].strip()


def _get_mode_styling_mandate(mode_id: Optional[str]) -> str:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return (
            "Choose quiet, commercially complete styling. The look should read clean, discreet, and supportive. "
            "Do not let fashion finishing compete with garment readability."
        )
    if normalized == "natural":
        return (
            "Choose styling that feels ordinary, non-prestige, unproduced, and low-attention. "
            "If the garment's own personality suggests sophistication, reduce it into everyday plausibility rather than elevating the rest of the look. "
            "When uncertain, choose the less polished, less edited, less status-signaling completion. "
            "Accessories should often collapse to none, and footwear should read functionally ordinary rather than tastefully refined."
        )
    if normalized == "lifestyle":
        return (
            "Choose styling that serves the activity and scene. Narrative utility beats abstract elegance. "
            "Resolve the look through lived context rather than polished completion."
        )
    if normalized == "editorial_commercial":
        return (
            "Choose styling that feels deliberate, fashion-aware, and compositionally useful. "
            "Sharpen silhouette and authority without turning accessories into the subject."
        )
    return (
        "Choose styling that serves the active mode first. If garment personality and mode taste diverge, the mode wins."
    )


def _infer_product_topology(set_detection: Optional[dict[str, Any]]) -> str:
    sd = set_detection or {}
    if not isinstance(sd, dict):
        return "single_piece"
    members = [m for m in (sd.get("set_members") or []) if isinstance(m, dict)]
    included_garments = [
        m for m in members
        if str(m.get("member_class") or "") == "garment"
        and str(m.get("include_policy") or "") in {"must_include", "optional"}
    ]
    included_coordinated_accessories = [
        m for m in members
        if str(m.get("member_class") or "") == "coordinated_accessory"
        and str(m.get("include_policy") or "") in {"must_include", "optional"}
    ]
    if len(included_garments) >= 2:
        return "coordinated_set"
    if included_garments and included_coordinated_accessories:
        return "garment_plus_coordinated_accessory"
    return "single_piece"


def _infer_hero_family(
    garment_hint: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
) -> str:
    topology = _infer_product_topology(set_detection)
    if topology in {"coordinated_set", "garment_plus_coordinated_accessory"}:
        return "top_layer"

    hint = _clean_text(garment_hint, limit=160).lower()
    subtype = str((structural_contract or {}).get("garment_subtype") or "").strip().lower()

    if any(token in hint for token in _ONE_PIECE_HINTS) or subtype in {"dress"}:
        return "one_piece"
    if any(token in hint for token in _FOOTWEAR_HINTS):
        return "footwear"
    if any(token in hint for token in _ACCESSORY_HINTS):
        return "accessory"
    if any(token in hint for token in _LOWER_BODY_HINTS):
        return "lower_body"
    if subtype in _TOP_LAYER_SUBTYPES:
        return "top_layer"
    return "unclear"


def _infer_hero_components(
    garment_hint: Optional[str],
    set_detection: Optional[dict[str, Any]],
) -> list[str]:
    sd = set_detection or {}
    members = [m for m in (sd.get("set_members") or []) if isinstance(m, dict)]
    labels = [
        _clean_text(m.get("role"), limit=80)
        for m in members
        if str(m.get("include_policy") or "") in {"must_include", "optional"}
        and _clean_text(m.get("role"), limit=80)
    ]
    if labels:
        return labels[:4]
    hint = _clean_text(garment_hint, limit=80)
    return [hint] if hint else []


def _normalize_styling_direction(
    payload: Optional[dict[str, Any]],
    *,
    inferred_topology: str,
    inferred_hero_family: str,
    inferred_components: list[str],
) -> dict[str, Any]:
    raw = payload if isinstance(payload, dict) else {}
    topology = str(raw.get("product_topology") or inferred_topology).strip().lower()
    if topology not in {"single_piece", "coordinated_set", "garment_plus_coordinated_accessory", "unclear"}:
        topology = inferred_topology

    hero_family = str(raw.get("hero_family") or inferred_hero_family).strip().lower()
    if hero_family not in {"top_layer", "lower_body", "one_piece", "footwear", "accessory", "unclear"}:
        hero_family = inferred_hero_family

    components = [
        _clean_text(x, limit=80)
        for x in (raw.get("hero_components") or inferred_components or [])
        if _clean_text(x, limit=80)
    ][:4] or list(inferred_components[:4])

    slots = [
        _clean_text(x, limit=40).lower()
        for x in (raw.get("completion_slots") or [])
        if _clean_text(x, limit=40)
    ][:5]

    return {
        "product_topology": topology,
        "hero_family": hero_family,
        "hero_components": components,
        "completion_slots": slots,
        "completion_strategy": _clean_text(raw.get("completion_strategy"), limit=220),
        "primary_completion": _clean_text(raw.get("primary_completion"), limit=140),
        "secondary_completion": _clean_text(raw.get("secondary_completion"), limit=140),
        "footwear_direction": _clean_text(raw.get("footwear_direction"), limit=140),
        "accessories_optional": _clean_text(raw.get("accessories_optional"), limit=140),
        "outer_layer_optional": _clean_text(raw.get("outer_layer_optional"), limit=140),
        "finish_logic": _clean_text(raw.get("finish_logic"), limit=180),
        "direction_summary": _clean_text(raw.get("direction_summary"), limit=260),
        "confidence": max(0.0, min(1.0, float(raw.get("confidence") or 0.0))),
    }


def resolve_styling_direction(
    *,
    mode_id: Optional[str],
    user_prompt: Optional[str],
    garment_hint: Optional[str],
    image_analysis: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
    garment_aesthetic: Optional[dict[str, Any]] = None,
    has_images: bool = False,
) -> dict[str, Any]:
    inferred_topology = _infer_product_topology(set_detection)
    inferred_hero_family = _infer_hero_family(garment_hint, structural_contract, set_detection)
    inferred_components = _infer_hero_components(garment_hint, set_detection)

    mode_lines = get_mode_identity_soul(mode_id)
    styling_soul = get_styling_soul(mode_id=mode_id, has_images=has_images)

    contract = structural_contract or {}
    aesthetic = garment_aesthetic or {}
    set_info = set_detection or {}
    prompt_text = _clean_text(user_prompt, limit=220)
    garment_text = _clean_text(garment_hint, limit=120)
    analysis_text = _clean_text(image_analysis, limit=500)
    mode_label = str(mode_id or "natural").strip().lower()
    components_text = ", ".join(inferred_components) if inferred_components else "hero product only"
    mode_styling_mandate = _get_mode_styling_mandate(mode_id)

    instruction = (
        "Resolve the styling direction for a single generation after garment analysis.\n\n"
        "You are NOT doing garment triage. You are deciding how the look should be completed around the hero product.\n"
        "Use the inferred product topology and hero role to decide which completion slots are genuinely unresolved.\n"
        "Do NOT assume a fixed completion path.\n"
        "If the product already resolves most of the look on its own, keep completion minimal.\n"
        "Resolve only what is truly missing or commercially necessary.\n"
        "Footwear matters when visible or commercially needed. Accessories remain optional.\n"
        "Use the literal string 'none' whenever a completion slot should stay absent.\n"
        "Do not add accessories, outer layers, or secondary completions just to make the styling feel more designed.\n"
        "Never copy the styling of the reference person. Invent a fresh, mode-aligned completion.\n\n"
        "OUTPUT SCOPE RULE:\n"
        "direction_summary must summarize only the clothing completion, footwear logic, and finishing logic.\n"
        "It must NOT mention locations, activities, destinations, or scene archetypes.\n\n"
        "PRIORITY RULE:\n"
        "When garment personality, user wording, and mode styling expectations pull in different directions, the active MODE has final authority over how polished, ordinary, edited, or complete the styling should feel.\n\n"
        "<MODE_IDENTITY>\n" + "\n".join(mode_lines) + "\n</MODE_IDENTITY>\n\n"
        "<STYLING_SOUL>\n" + styling_soul + "\n</STYLING_SOUL>\n\n"
        "<MODE_STYLING_MANDATE>\n" + mode_styling_mandate + "\n</MODE_STYLING_MANDATE>\n\n"
        "<JOB_CONTEXT>\n"
        f"- mode_id: {mode_label}\n"
        f"- user_prompt: {prompt_text or 'none'}\n"
        f"- garment_hint: {garment_text or 'unknown'}\n"
        f"- image_analysis: {analysis_text or 'unknown'}\n"
        f"- garment_subtype: {str(contract.get('garment_subtype') or 'unknown')}\n"
        f"- silhouette_volume: {str(contract.get('silhouette_volume') or 'unknown')}\n"
        f"- garment_length: {str(contract.get('garment_length') or 'unknown')}\n"
        f"- front_opening: {str(contract.get('front_opening') or 'unknown')}\n"
        f"- set_mode: {str(set_info.get('set_mode') or 'off')}\n"
        f"- detected_roles: {', '.join(set_info.get('detected_garment_roles') or []) or 'none'}\n"
        f"- inferred_product_topology: {inferred_topology}\n"
        f"- inferred_hero_family: {inferred_hero_family}\n"
        f"- inferred_hero_components: {components_text}\n"
        f"- garment_formality: {str(aesthetic.get('formality') or 'unknown')}\n"
        f"- garment_season: {str(aesthetic.get('season') or 'unknown')}\n"
        f"- garment_vibe: {str(aesthetic.get('vibe') or 'unknown')}\n"
        "</JOB_CONTEXT>\n\n"
        "Return strict JSON only."
    )

    parts = [types.Part(text=instruction)]
    try:
        response = generate_structured_json(
            parts=parts,
            schema=STYLING_DIRECTION_SCHEMA,
            temperature=0.35,
            max_tokens=800,
            thinking_budget=0,
        )
        parsed = _decode_agent_response(response)
    except Exception as e:
        err_msg = str(e)
        print(f"[STYLING_DIRECTION] ⚠️ resolver failed: {err_msg}")
        repaired = try_repair_truncated_json(err_msg)
        if repaired is None:
            return {}
        parsed = repaired

    normalized = _normalize_styling_direction(
        parsed,
        inferred_topology=inferred_topology,
        inferred_hero_family=inferred_hero_family,
        inferred_components=inferred_components,
    )
    if normalized.get("confidence", 0.0) > 0.0:
        print(
            "[STYLING_DIRECTION] ✅ "
            f"topology={normalized['product_topology']} "
            f"family={normalized['hero_family']} "
            f"slots={normalized['completion_slots']} "
            f"conf={normalized['confidence']:.2f}"
        )
    return normalized
