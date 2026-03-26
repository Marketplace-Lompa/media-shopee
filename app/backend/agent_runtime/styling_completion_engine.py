"""
Styling completion engine latent for fashion image direction.

Objetivo:
- resolver o nível de completude do look como decisão interna de moda
- escolher uma direção de calçado coerente com mode + framing + peça
- manter o styling subordinado à venda da roupa, sem competir com a peça
"""
from __future__ import annotations

import hashlib
from typing import Any, Optional


_BAREFOOT_EXCEPTION_KEYWORDS = (
    "barefoot", "descalço", "descalca", "descalça", "sem sapato", "sem sapatos",
    "beachwear", "swimwear", "bikini", "lingerie", "sleepwear", "pajama", "pyjama",
    "loungewear", "robe",
)

_FOOTWEAR_FAMILY_RENDERINGS: dict[str, tuple[str, ...]] = {
    "open_minimal": (
        "minimal open-profile footwear with restrained lines and low contrast",
        "understated open footwear with a quiet visual profile",
        "clean open footwear that stays secondary to the garment",
    ),
    "closed_clean": (
        "clean closed footwear with low profile and tonal restraint",
        "closed low-profile footwear with a quiet commercial finish",
        "closed footwear with restrained contrast and minimal visual noise",
    ),
    "soft_flat": (
        "soft flat footwear with a clean low-profile outline and restrained contrast",
        "low-profile flat footwear with a gentle commercial finish",
        "softly structured flat footwear that stays visually quiet",
    ),
    "refined_lifted": (
        "refined low-lift footwear with controlled emphasis and tonal balance",
        "elevated low-profile footwear that stays secondary to the garment",
        "polished low-lift footwear with restrained visual presence",
    ),
    "casual_grounded": (
        "grounded everyday footwear with relaxed polish and low visual noise",
        "casual grounded footwear with low contrast and believable ease",
        "everyday footwear with a grounded profile and restrained presence",
    ),
}


_STYLING_LIBRARY: dict[str, dict[str, tuple[str, ...]]] = {
    "catalog_clean": {
        "completion_level": (
            "commercially complete minimal look",
            "catalog-complete restrained styling",
        ),
        "footwear_family": (
            "closed_clean",
            "refined_lifted",
            "soft_flat",
        ),
        "accessory_restraint": (
            "nearly absent accessories",
            "minimal styling accents only",
            "strict accessory restraint",
        ),
        "look_finish": (
            "clean commercial finish",
            "quiet premium catalog finish",
            "commercial completeness without styling noise",
        ),
    },
    "natural": {
        "completion_level": (
            "commercially complete natural styling",
            "softly resolved everyday styling",
            "clean believable look completion",
        ),
        "footwear_family": (
            "soft_flat",
            "closed_clean",
            "casual_grounded",
            "open_minimal",
        ),
        "accessory_restraint": (
            "restrained everyday accessories",
            "light personal styling only",
            "minimal jewelry with believable warmth",
        ),
        "look_finish": (
            "warm commercially believable finish",
            "natural complete look without overstyling",
            "soft premium everyday finish",
        ),
    },
    "lifestyle": {
        "completion_level": (
            "socially complete lifestyle styling",
            "commercially resolved lived-in styling",
            "believable lifestyle look completion",
        ),
        "footwear_family": (
            "casual_grounded",
            "soft_flat",
            "open_minimal",
            "closed_clean",
        ),
        "accessory_restraint": (
            "light lifestyle accessories",
            "small personal styling accents",
            "restrained but lived-in accessory detail",
        ),
        "look_finish": (
            "socially believable finish",
            "commercial lifestyle finish",
            "fresh lived-in completion without clutter",
        ),
    },
    "editorial_commercial": {
        "completion_level": (
            "editorially complete restrained styling",
            "fashion-aware commercial look completion",
            "resolved styling with stronger image intention",
        ),
        "footwear_family": (
            "refined_lifted",
            "closed_clean",
            "open_minimal",
        ),
        "accessory_restraint": (
            "edited fashion accessories only",
            "restrained editorial accents",
            "accessories kept secondary to silhouette",
        ),
        "look_finish": (
            "fashion-aware commercial finish",
            "refined editorial-commercial finish",
            "intentional styling without stealing focus",
        ),
    },
}


def _stable_index(seed: str, size: int) -> int:
    if size <= 1:
        return 0
    hashed = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return int(hashed, 16) % size


def _garment_styling_affinity(user_prompt: str) -> dict[str, str]:
    text = str(user_prompt or "").lower()
    affinity = {
        "footwear_family": "",
        "look_finish": "",
    }
    if any(token in text for token in ("vestido", "dress", "saia", "skirt", "linho", "linen", "evasê", "evase", "bufante", "puff")):
        affinity["footwear_family"] = "soft_flat"
        affinity["look_finish"] = "natural complete look without overstyling"
    if any(token in text for token in ("blazer", "alfaiat", "tailored", "structured", "lapela", "lapel")):
        affinity["footwear_family"] = "closed_clean"
        affinity["look_finish"] = "quiet premium catalog finish"
    if any(token in text for token in ("tricô", "tricot", "knit", "crochê", "crochet", "malha")):
        affinity["footwear_family"] = "casual_grounded"
        affinity["look_finish"] = "soft premium everyday finish"
    return affinity


def _styling_profile_keywords(operational_profile: Optional[dict[str, Any]]) -> tuple[tuple[str, ...], float]:
    profile = operational_profile or {}
    guardrail = str(profile.get("guardrail_profile", "") or "")
    invention_budget = float(profile.get("invention_budget", 0.5) or 0.5)
    if guardrail == "strict_catalog":
        return (("minimal", "restrained", "quiet", "clean", "tonal", "neutral", "low-contrast"), invention_budget)
    if guardrail == "natural_commercial":
        return (("natural", "believable", "warm", "light", "everyday", "understated"), invention_budget)
    if guardrail == "lifestyle_permissive":
        return (("casual", "social", "lived", "fresh", "believable"), invention_budget)
    if guardrail == "editorial_controlled":
        return (("fashion", "refined", "editorial", "sculptural", "intentional"), invention_budget)
    return ((), invention_budget)


def _budget_window(options: list[str], invention_budget: float) -> list[str]:
    if len(options) <= 2:
        return options
    if invention_budget < 0.3:
        return options[:2]
    if invention_budget < 0.5:
        return options[: min(3, len(options))]
    return options


def _prioritize_options(
    options: list[str],
    *,
    keywords: tuple[str, ...],
    invention_budget: float,
) -> list[str]:
    windowed = _budget_window(options, invention_budget)
    if not keywords:
        return windowed
    matched = [opt for opt in windowed if any(key in opt.lower() for key in keywords)]
    unmatched = [opt for opt in windowed if opt not in matched]
    return matched + unmatched if matched else windowed


def render_footwear_strategy(
    *,
    mode_id: str,
    footwear_family: str,
    seed_hint: str = "",
    operational_profile: Optional[dict[str, Any]] = None,
) -> str:
    renderings = list(_FOOTWEAR_FAMILY_RENDERINGS.get(footwear_family, ()))
    if not renderings:
        return "commercially coherent footwear with restrained visual presence"
    profile_keywords, invention_budget = _styling_profile_keywords(operational_profile)
    prioritized = _prioritize_options(
        renderings,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    seed = f"{mode_id}:{footwear_family}:{seed_hint}"
    return prioritized[_stable_index(seed, len(prioritized))]


def select_styling_completion_state(
    *,
    mode_id: str,
    framing_profile: str,
    scenario_pool: str,
    user_prompt: Optional[str] = None,
    seed_hint: str = "",
    operational_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    library = _STYLING_LIBRARY.get(mode_id, _STYLING_LIBRARY["natural"])
    affinity = _garment_styling_affinity(user_prompt or "")
    profile_keywords, invention_budget = _styling_profile_keywords(operational_profile)
    seed_base = f"{mode_id}:{framing_profile}:{scenario_pool}:{user_prompt or ''}:{seed_hint}"

    completion_levels = list(library["completion_level"])
    footwear_families = list(library["footwear_family"])
    accessory_options = list(library["accessory_restraint"])
    finish_options = list(library["look_finish"])

    if affinity["footwear_family"] and affinity["footwear_family"] in footwear_families:
        footwear_families = [affinity["footwear_family"]] + [v for v in footwear_families if v != affinity["footwear_family"]]
    if affinity["look_finish"] and affinity["look_finish"] in finish_options:
        finish_options = [affinity["look_finish"]] + [v for v in finish_options if v != affinity["look_finish"]]

    completion_levels = _prioritize_options(
        completion_levels,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    footwear_families = _prioritize_options(
        footwear_families,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    accessory_options = _prioritize_options(
        accessory_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    finish_options = _prioritize_options(
        finish_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )

    completion_level = completion_levels[_stable_index(seed_base + ":completion", len(completion_levels))]
    footwear_family = footwear_families[_stable_index(seed_base + ":footwear_family", len(footwear_families))]
    footwear_strategy = render_footwear_strategy(
        mode_id=mode_id,
        footwear_family=footwear_family,
        seed_hint=seed_base + ":footwear_strategy",
        operational_profile=operational_profile,
    )
    accessory_restraint = accessory_options[_stable_index(seed_base + ":accessory", len(accessory_options))]
    look_finish = finish_options[_stable_index(seed_base + ":finish", len(finish_options))]
    footwear_required = framing_profile == "full_body" and not any(
        token in str(user_prompt or "").lower() for token in _BAREFOOT_EXCEPTION_KEYWORDS
    )

    guardrail = str((operational_profile or {}).get("guardrail_profile", "") or "")
    if guardrail == "strict_catalog" or mode_id == "catalog_clean":
        styling_interference = "very low styling interference"
    elif guardrail == "editorial_controlled" or mode_id == "editorial_commercial":
        styling_interference = "restrained fashion-directed interference"
    elif guardrail == "lifestyle_permissive":
        styling_interference = "light lived-in styling interference"
    else:
        styling_interference = "low styling interference"

    return {
        "completion_level": completion_level,
        "footwear_family": footwear_family,
        "footwear_strategy": footwear_strategy,
        "accessory_restraint": accessory_restraint,
        "look_finish": look_finish,
        "styling_interference": styling_interference,
        "hero_balance": "garment remains the hero while the look feels resolved",
        "footwear_required": footwear_required,
        "styling_signature": "|".join(
            [
                mode_id,
                framing_profile,
                completion_level,
                footwear_family,
                footwear_strategy,
                accessory_restraint,
                look_finish,
                styling_interference,
                "footwear_required" if footwear_required else "footwear_optional",
            ]
        ),
    }
