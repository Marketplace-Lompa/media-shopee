"""
Capture engine latent for fashion image direction.

Objetivo:
- transformar framing + camera_type + capture_geometry em um estado interno
  que responda melhor ao molde da peça e à intenção comercial
- manter a captura como linguagem visual, não como ficha técnica
"""
from __future__ import annotations

import hashlib
from typing import Any, Optional


_CAPTURE_LIBRARY: dict[str, dict[str, tuple[str, ...]]] = {
    "commercial_full_frame": {
        "capture_feel": (
            "clean commercial precision",
            "neutral premium commercial clarity",
            "controlled garment-first capture",
        ),
        "lens_language": (
            "natural commercial lens feel",
            "clean portrait-commercial perspective",
            "balanced full-frame clarity",
        ),
        "subject_separation": (
            "soft subject separation",
            "controlled background falloff",
            "restrained depth separation",
        ),
    },
    "natural_digital": {
        "capture_feel": (
            "natural digital commercial feel",
            "clean contemporary digital realism",
            "softly observational commercial capture",
        ),
        "lens_language": (
            "natural digital lens feel",
            "eye-level observational perspective",
            "modern everyday commercial perspective",
        ),
        "subject_separation": (
            "gentle natural depth",
            "light background softness",
            "modest subject separation",
        ),
    },
    "editorial_fashion": {
        "capture_feel": (
            "fashion-forward commercial capture",
            "editorial commercial sharpness",
            "intentional fashion image control",
        ),
        "lens_language": (
            "refined fashion perspective",
            "editorial image perspective with controlled compression",
            "graphic fashion lens feel",
        ),
        "subject_separation": (
            "selective depth emphasis",
            "controlled fashion separation",
            "graphic foreground-background hierarchy",
        ),
    },
    "phone_social": {
        "capture_feel": (
            "mobile-first social realism",
            "casual creator capture feel",
            "phone-native social-commerce capture",
        ),
        "lens_language": (
            "believable handheld phone perspective",
            "casual mobile viewpoint",
            "social capture perspective",
        ),
        "subject_separation": (
            "minimal separation",
            "phone-like scene continuity",
            "natural app-camera depth behavior",
        ),
    },
}


_GEOMETRY_LIBRARY: dict[str, dict[str, str]] = {
    "full_body_neutral": {
        "body_relation": "stable full-body proportion",
        "angle_logic": "neutral body-aligned view",
        "garment_priority": "preserve the full silhouette and hem behavior",
    },
    "three_quarter_eye_level": {
        "body_relation": "three-quarter proportion with clear upper-to-skirt transition",
        "angle_logic": "eye-level body relation",
        "garment_priority": "favor neckline, sleeve architecture, and waist-to-skirt transition",
    },
    "three_quarter_slight_angle": {
        "body_relation": "three-quarter proportion with mild directional energy",
        "angle_logic": "slight-angle body relation",
        "garment_priority": "favor waist definition, sleeve volume, and movement through the skirt",
    },
    "editorial_mid_low_angle": {
        "body_relation": "mid-frame fashion proportion",
        "angle_logic": "subtle low-angle relation",
        "garment_priority": "favor stature, line, and graphic garment structure",
    },
    "environmental_wide_observer": {
        "body_relation": "wide environmental proportion",
        "angle_logic": "observer viewpoint with spatial breathing room",
        "garment_priority": "preserve full look readability while allowing more setting context",
    },
    "detail_close_observer": {
        "body_relation": "close observational proportion",
        "angle_logic": "near-detail viewing relation",
        "garment_priority": "favor texture, construction detail, and localized fabric behavior",
    },
}


def _stable_index(seed: str, size: int) -> int:
    if size <= 1:
        return 0
    hashed = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return int(hashed, 16) % size


def _garment_capture_affinity(user_prompt: str) -> dict[str, str]:
    text = str(user_prompt or "").lower()
    affinity = {
        "garment_priority": "",
        "capture_feel": "",
    }
    if any(token in text for token in ("vestido", "dress", "saia", "skirt", "evasê", "evase", "bufante", "puff")):
        affinity["garment_priority"] = "favor waist definition, sleeve volume, and movement through the skirt"
        affinity["capture_feel"] = "softly observational commercial capture"
    if any(token in text for token in ("blazer", "alfaiat", "structured", "tailored", "lapela", "lapel")):
        affinity["garment_priority"] = "favor line, shoulder structure, lapel definition, and tailoring precision"
        affinity["capture_feel"] = "controlled garment-first capture"
    if any(token in text for token in ("tricô", "tricot", "knit", "crochet", "crochê", "texture")):
        affinity["garment_priority"] = "favor texture, surface depth, and stitch readability"
    return affinity


def _capture_profile_keywords(operational_profile: Optional[dict[str, Any]]) -> tuple[tuple[str, ...], float]:
    profile = operational_profile or {}
    guardrail = str(profile.get("guardrail_profile", "") or "")
    invention_budget = float(profile.get("invention_budget", 0.5) or 0.5)
    if guardrail == "strict_catalog":
        return (("controlled", "clean", "neutral", "balanced", "restrained", "soft"), invention_budget)
    if guardrail == "natural_commercial":
        return (("natural", "observational", "contemporary", "gentle", "everyday", "light"), invention_budget)
    if guardrail == "lifestyle_permissive":
        return (("mobile", "casual", "social", "observational", "minimal", "phone"), invention_budget)
    if guardrail == "editorial_controlled":
        return (("fashion", "editorial", "intentional", "graphic", "selective"), invention_budget)
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


def select_capture_state(
    *,
    framing_profile: str,
    camera_type: str,
    capture_geometry: str,
    mode_id: str,
    user_prompt: Optional[str] = None,
    seed_hint: str = "",
    operational_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    camera_library = _CAPTURE_LIBRARY.get(camera_type, _CAPTURE_LIBRARY["natural_digital"])
    geometry_library = _GEOMETRY_LIBRARY.get(capture_geometry, _GEOMETRY_LIBRARY["three_quarter_eye_level"])
    affinity = _garment_capture_affinity(user_prompt or "")
    profile_keywords, invention_budget = _capture_profile_keywords(operational_profile)
    seed_base = f"{mode_id}:{framing_profile}:{camera_type}:{capture_geometry}:{user_prompt or ''}:{seed_hint}"

    capture_feels = list(camera_library["capture_feel"])
    lens_languages = list(camera_library["lens_language"])
    separations = list(camera_library["subject_separation"])

    if affinity["capture_feel"] and affinity["capture_feel"] in capture_feels:
        capture_feels = [affinity["capture_feel"]] + [v for v in capture_feels if v != affinity["capture_feel"]]

    capture_feels = _prioritize_options(
        capture_feels,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    lens_languages = _prioritize_options(
        lens_languages,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    separations = _prioritize_options(
        separations,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )

    capture_feel = capture_feels[_stable_index(seed_base + ":feel", len(capture_feels))]
    lens_language = lens_languages[_stable_index(seed_base + ":lens", len(lens_languages))]
    subject_separation = separations[_stable_index(seed_base + ":sep", len(separations))]
    garment_priority = affinity["garment_priority"] or geometry_library["garment_priority"]

    return {
        "framing_intent": framing_profile,
        "camera_family": camera_type,
        "geometry_intent": capture_geometry,
        "capture_feel": capture_feel,
        "lens_language": lens_language,
        "subject_separation": subject_separation,
        "body_relation": geometry_library["body_relation"],
        "angle_logic": geometry_library["angle_logic"],
        "garment_priority": garment_priority,
        "capture_signature": "|".join(
            [
                framing_profile,
                camera_type,
                capture_geometry,
                capture_feel,
                lens_language,
                subject_separation,
                garment_priority,
            ]
        ),
    }
