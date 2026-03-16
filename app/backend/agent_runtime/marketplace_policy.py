"""
Políticas e receitas de slots do fluxo Marketplace.
Slots de main_variation são diferenciados por canal (Shopee vs ML)
conforme regras oficiais de foto de moda BR 2026.
"""
from __future__ import annotations

from typing import Any


# ── Shopee: capa exige fundo branco (hard rule) ───────────────────────────────

_MAIN_VARIATION_SLOTS_SHOPEE: list[dict[str, str]] = [
    {
        "slot_id": "hero_front",
        "slot_type": "main_variation",
        "shot_prompt": (
            "Hero cover shot, full body, front-facing, garment fully visible. "
            "Clean neutral background — white or very light gray — chosen to contrast clearly with the garment color "
            "(use light gray or off-white if the garment is white or very light, to keep edges visible). "
            "No textures, no distracting elements. High mobile readability for Shopee product listing."
        ),
    },
    {
        "slot_id": "front_3_4",
        "slot_type": "main_variation",
        "shot_prompt": (
            "Front three-quarter shot, full garment visibility, preserve drape and silhouette readability. "
            "Use clean neutral indoor background (white/off-white/light gray) with no outdoor landscape visible."
        ),
    },
    {
        "slot_id": "back_or_side",
        "slot_type": "main_variation",
        "shot_prompt": (
            "Back or side complementary angle to show construction and fit behavior. "
            "Use clean neutral indoor background (white/off-white/light gray), no scenic window view."
        ),
    },
    {
        "slot_id": "fabric_closeup",
        "slot_type": "main_variation",
        "shot_prompt": (
            "Close-up detail of textile relief, knit/texture and stitch definition with commercial clarity. "
            "Keep framing clean on neutral background, no lifestyle scene context."
        ),
    },
    {
        "slot_id": "functional_detail_or_size",
        "slot_type": "main_variation",
        "shot_prompt": (
            "Functional detail shot (hem, collar, cuff, closure, finishing) or size reference table "
            "in centimeters with clear legibility on mobile. Commercial product readability. "
            "Neutral clean background only, without scenic elements."
        ),
    },
]

# ── Mercado Livre: moda aceita contexto/textura leve (regime híbrido) ─────────
# Fundo branco não é obrigatório para moda no ML; contexto neutro é permitido.

_MAIN_VARIATION_SLOTS_ML: list[dict[str, str]] = [
    {
        "slot_id": "hero_front",
        "slot_type": "main_variation",
        "shot_prompt": (
            "Hero cover shot, full body, front-facing, garment fully visible, protagonist of the frame. "
            "Neutral light background — solid white, off-white or very subtle light texture are all acceptable. "
            "Clear commercial readability for Mercado Livre fashion listing."
        ),
    },
    {
        "slot_id": "front_3_4",
        "slot_type": "main_variation",
        "shot_prompt": "Front three-quarter shot, full garment visibility, preserve drape and silhouette readability.",
    },
    {
        "slot_id": "back_or_side",
        "slot_type": "main_variation",
        "shot_prompt": "Back or side complementary angle to show construction and fit behavior.",
    },
    {
        "slot_id": "fabric_closeup",
        "slot_type": "main_variation",
        "shot_prompt": "Close-up detail of textile relief, knit/texture and stitch definition with commercial clarity.",
    },
    {
        "slot_id": "functional_detail_or_size",
        "slot_type": "main_variation",
        "shot_prompt": (
            "Functional detail shot (hem, collar, cuff, closure, finishing) or size reference table "
            "in centimeters with clear legibility. Commercial product readability."
        ),
    },
]

# ── Variações de cor: igual nos dois canais ───────────────────────────────────

_COLOR_VARIATION_SLOTS: list[dict[str, str]] = [
    {
        "slot_id": "color_hero_front",
        "slot_type": "color_variation",
        "shot_prompt": "Hero front shot for this exact colorway, garment fully visible.",
    },
    {
        "slot_id": "color_front_3_4",
        "slot_type": "color_variation",
        "shot_prompt": "Front three-quarter shot for this colorway, preserving geometry and drape.",
    },
    {
        "slot_id": "color_detail",
        "slot_type": "color_variation",
        "shot_prompt": "Color-focused detail shot to confirm yarn/fabric tone and texture consistency.",
    },
]

_CHANNEL_STYLE_HINTS = {
    "shopee": (
        "Optimize for Shopee Brasil fashion listing: clean neutral cover background "
        "(white or light gray contrasting with garment color), "
        "conversion-oriented framing, clear product hero with high mobile readability. "
        "Garment must occupy at least 70% of the frame. "
        "For main photos, keep a neutral indoor catalog setting across all slots and avoid scenic outdoor views."
    ),
    "mercado_livre": (
        "Optimize for Mercado Livre Brasil fashion listing: garment is the absolute protagonist, "
        "neutral background preferred (white, off-white or light texture accepted for moda). "
        "Objective commercial framing, no promotional text or overlays."
    ),
}

_CHANNEL_RUNTIME_DEFAULTS: dict[str, dict[str, str]] = {
    # Baseline mais estável para capa/foto comercial limpa.
    "shopee": {
        "preset": "catalog_clean",
        "scene_preference": "indoor_br",
        "fidelity_mode": "balanceada",
        "pose_flex_mode": "controlled",
    },
    # ML moda aceita contexto em parte das subcategorias, mas o default guiado
    # fica clean para previsibilidade e compliance amplo.
    "mercado_livre": {
        "preset": "catalog_clean",
        "scene_preference": "indoor_br",
        "fidelity_mode": "balanceada",
        "pose_flex_mode": "controlled",
    },
}

_COMMON_PROMPT_GUARDRAILS: list[str] = [
    "Use references as garment evidence only; do not copy the person.",
    "Never copy or approximate the reference person's facial identity, face proportions, hairline, dominant hairstyle silhouette, skin-tone cluster, age impression, or body-shape signature.",
    "Keep the model commercially plausible for Brazilian marketplace, but with a clearly new identity that does not resemble the reference person.",
    "Prioritize natural face rendering: realistic skin pores and asymmetry, avoid plastic/mannequin facial finish.",
    "Preserve textile micro-texture, stitch relief, and yarn definition; avoid over-smoothing the knit surface.",
    "No logos, watermarks, QR codes, contact info, frames, or promotional text overlays.",
    "If references indicate coordinated set members, keep the set logic intact and preserve each member as a distinct product piece.",
]

_MAIN_VARIATION_SLOTS_BY_CHANNEL: dict[str, list[dict[str, str]]] = {
    "shopee": _MAIN_VARIATION_SLOTS_SHOPEE,
    "mercado_livre": _MAIN_VARIATION_SLOTS_ML,
}


def resolve_marketplace_policy(channel: str, operation: str) -> dict[str, Any]:
    if operation == "main_variation":
        slots = list(
            _MAIN_VARIATION_SLOTS_BY_CHANNEL.get(channel, _MAIN_VARIATION_SLOTS_SHOPEE)
        )
    elif operation == "color_variations":
        slots = list(_COLOR_VARIATION_SLOTS)
    else:
        raise ValueError("Operação de marketplace inválida")

    return {
        "channel": channel,
        "operation": operation,
        "channel_style_hint": _CHANNEL_STYLE_HINTS.get(channel, _CHANNEL_STYLE_HINTS["shopee"]),
        "runtime_defaults": _CHANNEL_RUNTIME_DEFAULTS.get(channel, _CHANNEL_RUNTIME_DEFAULTS["shopee"]),
        "prompt_guardrails": list(_COMMON_PROMPT_GUARDRAILS),
        "slots": slots,
    }
