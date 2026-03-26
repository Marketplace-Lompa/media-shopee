"""
Scene engine latent for fashion image direction.

Objetivo:
- transformar scenario_pool em um estado interno mais rico de mundo visual
- evitar repetir apenas "apartment", "street", "courtyard" como soluções rasas
- manter a criação condicionada por mode + peça + intenção comercial
"""
from __future__ import annotations

import hashlib
from typing import Any, Optional


_SCENE_WORLD_LIBRARY: dict[str, dict[str, tuple[str, ...]]] = {
    "studio_minimal": {
        "microcontext": (
            "seamless studio sweep with soft floor transition",
            "minimal off-white studio corner with quiet depth",
            "controlled studio wall-to-floor set with restrained tonal variation",
        ),
        "emotional_register": (
            "clean premium restraint",
            "quiet commercial precision",
            "calm catalog discipline",
        ),
        "material_language": (
            "matte backdrop + softened floor reflection",
            "soft plaster neutrality + clean studio floor",
            "seamless neutral surface + low visual texture",
        ),
        "background_density": (
            "very low interference",
            "nearly absent environmental noise",
            "strictly restrained background detail",
        ),
        "brazil_anchor": (
            "subtle Brazilian commercial polish",
            "Brazilian catalog realism without local cliché",
        ),
    },
    "residential_daylight": {
        "microcontext": (
            "integrated living area with calm domestic depth",
            "window-side residential corner with quiet lived-in order",
            "light residential interior with soft furniture depth",
            "apartment transition space with restrained domestic detail",
        ),
        "emotional_register": (
            "calm everyday polish",
            "warm domestic clarity",
            "soft lived-in ease",
        ),
        "material_language": (
            "light wood + matte wall + soft textile",
            "wood floor + neutral plaster + muted upholstery",
            "simple domestic joinery + natural fabric accents",
        ),
        "background_density": (
            "restrained",
            "softly supportive",
            "controlled domestic detail",
        ),
        "brazil_anchor": (
            "subtle Brazilian residential realism",
            "credible Brazilian apartment atmosphere",
        ),
    },
    "neighborhood_commercial": {
        "microcontext": (
            "tree-lined neighborhood sidewalk with local everyday rhythm",
            "street-level commercial stretch with calm foot traffic energy",
            "quiet residential-commercial block with walkable human scale",
            "sunlit sidewalk edge with understated storefront presence",
        ),
        "emotional_register": (
            "approachable city ease",
            "lived urban calm",
            "practical everyday warmth",
        ),
        "material_language": (
            "painted façades + sidewalk texture + filtered greenery",
            "mixed plaster + glass + shaded pavement",
            "urban masonry + muted signage + soft foliage",
        ),
        "background_density": (
            "moderately restrained",
            "commercially believable",
            "light everyday motion without crowding",
        ),
        "brazil_anchor": (
            "believable Brazilian neighborhood life",
            "credible Brazilian street materiality",
        ),
    },
    "textured_city": {
        "microcontext": (
            "textured urban passage with layered wall surfaces",
            "city sidewalk with tactile façades and architectural wear",
            "street corner with visible material age and human passage",
        ),
        "emotional_register": (
            "urban vitality",
            "tactile city realism",
            "confident street presence",
        ),
        "material_language": (
            "concrete + plaster + metal + worn stone",
            "textured wall paint + urban glass + pavement grain",
            "aged masonry + street markings + graphic surfaces",
        ),
        "background_density": (
            "medium",
            "visibly active but controlled",
            "textured without clutter",
        ),
        "brazil_anchor": (
            "credible Brazilian urban texture",
            "contemporary Brazilian street atmosphere",
        ),
    },
    "nature_open_air": {
        "microcontext": (
            "open-air garden edge with breathable depth",
            "tree-framed outdoor path with soft natural recession",
            "landscaped exterior with airy horizon and natural spacing",
        ),
        "emotional_register": (
            "open breathable calm",
            "fresh natural ease",
            "soft resort-like openness",
        ),
        "material_language": (
            "foliage + stone path + warm outdoor light",
            "green depth + soft earth + open sky reflection",
            "natural planting + pale stone + gentle shadow pattern",
        ),
        "background_density": (
            "low-to-medium",
            "airy",
            "soft natural layering",
        ),
        "brazil_anchor": (
            "credible Brazilian open-air warmth",
            "subtle Brazilian outdoor softness",
        ),
    },
    "architecture_premium": {
        "microcontext": (
            "architectural courtyard with measured spatial rhythm",
            "premium exterior threshold with strong geometric clarity",
            "refined stone-and-shadow environment with controlled openness",
        ),
        "emotional_register": (
            "refined spatial confidence",
            "composed premium sophistication",
            "intentional architectural elegance",
        ),
        "material_language": (
            "limestone + concrete + shadow rhythm",
            "stone planes + soft glass reflection + controlled geometry",
            "architectural mineral surfaces + restrained metal detailing",
        ),
        "background_density": (
            "restrained but graphic",
            "low clutter with strong form",
            "premium spatial support",
        ),
        "brazil_anchor": (
            "contemporary Brazilian architectural polish",
            "Brazilian premium design language without postcard cues",
        ),
    },
    "curated_interior": {
        "microcontext": (
            "refined interior with curated commercial restraint",
            "quiet styled room with deliberate furniture spacing",
            "minimal indoor fashion setting with soft spatial depth",
        ),
        "emotional_register": (
            "quiet refinement",
            "controlled interior polish",
            "soft premium calm",
        ),
        "material_language": (
            "neutral upholstery + soft wood + matte wall finish",
            "curated furniture + stone accent + restrained textile surfaces",
            "clean interior joinery + muted decor + subtle reflection",
        ),
        "background_density": (
            "restrained",
            "curated but secondary",
            "low visual noise",
        ),
        "brazil_anchor": (
            "credible Brazilian interior polish",
            "subtle Brazilian design-store sensibility",
        ),
    },
    "tropical_garden": {
        "microcontext": (
            "shaded tropical garden path with filtered canopy light",
            "residential courtyard with potted palms and terracotta",
            "pousada garden with hammock edges and bougainvillea depth",
            "quintal brasileiro with mango tree shade and worn tile",
        ),
        "emotional_register": (
            "warm organic ease",
            "tropical domestic calm",
            "lush lived-in softness",
        ),
        "material_language": (
            "foliage + terracotta + soft earth + dappled shade",
            "tropical planting + weathered stone + warm wood",
            "palm shadow + tile + green depth + filtered light",
        ),
        "background_density": (
            "medium natural layering",
            "lush but secondary",
            "soft organic depth",
        ),
        "brazil_anchor": (
            "authentic Brazilian tropical residential warmth",
            "credible Brazilian garden domesticity",
        ),
    },
    "cafe_bistro": {
        "microcontext": (
            "neighborhood padaria with glass counter and warm interior light",
            "Brazilian bistro corner with wood stools and chalkboard depth",
            "açaí shop front with casual seating and sidewalk proximity",
            "corner coffee bar with espresso machine and morning routine energy",
        ),
        "emotional_register": (
            "warm social ease",
            "approachable everyday ritual",
            "soft commercial intimacy",
        ),
        "material_language": (
            "wood counter + glass + tile + warm practical light",
            "concrete floor + menu board + casual furniture",
            "mosaic tile + wood + metal fixtures + coffee aroma suggestion",
        ),
        "background_density": (
            "moderately active",
            "believable morning rhythm",
            "controlled social background",
        ),
        "brazil_anchor": (
            "authentic Brazilian café culture",
            "credible Brazilian padaria atmosphere",
        ),
    },
    "beach_coastal": {
        "microcontext": (
            "boardwalk edge with sand depth and open horizon",
            "coastal town sidewalk with sea breeze suggestion and pastel facades",
            "beach kiosk proximity with soft sand transition and dune vegetation",
            "marina walkway with boat masts and calm waterfront light",
        ),
        "emotional_register": (
            "open coastal freedom",
            "breezy relaxed warmth",
            "salt-air luminosity",
        ),
        "material_language": (
            "sand + weathered wood + coastal vegetation + open sky",
            "pastel plaster + boardwalk planks + sea light reflection",
            "dune grass + pale concrete + warm horizon glow",
        ),
        "background_density": (
            "airy with coastal depth",
            "open but grounded",
            "breathable horizon presence",
        ),
        "brazil_anchor": (
            "authentic Brazilian coastal warmth",
            "credible Brazilian beach-town life",
        ),
    },
    "hotel_pousada": {
        "microcontext": (
            "pousada reception with woven textures and warm ambient light",
            "boutique hotel corridor with soft art and restrained luxury",
            "pousada veranda with rattan chairs and garden view glimpse",
            "hotel lobby lounge with curated plants and quiet spatial depth",
        ),
        "emotional_register": (
            "quiet hospitality warmth",
            "restrained travel elegance",
            "soft curated welcome",
        ),
        "material_language": (
            "rattan + linen + warm wood + indirect light",
            "polished floor + soft upholstery + curated greenery",
            "woven textures + plaster + ambient lamp warmth",
        ),
        "background_density": (
            "restrained but curated",
            "soft hospitality depth",
            "quietly furnished",
        ),
        "brazil_anchor": (
            "credible Brazilian pousada charm",
            "authentic Brazilian boutique hospitality",
        ),
    },
    "market_feira": {
        "microcontext": (
            "covered market aisle with colorful produce and diffused overhead light",
            "feira livre edge with awning shade and stacked crate texture",
            "mercado municipal gallery with tile and warm vendor depth",
            "artisan craft fair with textile displays and soft crowd recession",
        ),
        "emotional_register": (
            "vibrant everyday abundance",
            "warm communal energy",
            "colorful authentic bustle",
        ),
        "material_language": (
            "canvas awning + wooden crate + colorful produce + warm shade",
            "tile floor + iron structure + diffused overhead light",
            "textile stacks + handcraft displays + filtered natural light",
        ),
        "background_density": (
            "moderate with selective focus",
            "active but depth-controlled",
            "colorful but secondary",
        ),
        "brazil_anchor": (
            "authentic Brazilian feira atmosphere",
            "credible Brazilian mercado vitality",
        ),
    },
    "cultural_space": {
        "microcontext": (
            "museum gallery with clean walls and controlled spatial rhythm",
            "cultural center foyer with high ceilings and geometric light",
            "art gallery transition space with curated negative space",
            "library reading corner with warm wood and book-spine depth",
        ),
        "emotional_register": (
            "composed intellectual calm",
            "quiet cultural sophistication",
            "elegant institutional restraint",
        ),
        "material_language": (
            "white wall + polished floor + curated light + spatial void",
            "concrete + glass + wood bench + controlled geometry",
            "book spines + warm wood + soft institutional light",
        ),
        "background_density": (
            "deliberately sparse",
            "curated negative space",
            "controlled institutional depth",
        ),
        "brazil_anchor": (
            "contemporary Brazilian cultural refinement",
            "credible Brazilian institutional elegance",
        ),
    },
    "rooftop_terrace": {
        "microcontext": (
            "residential rooftop terrace with city skyline and potted plants",
            "apartment building terraço with clothesline edges and sky openness",
            "bar rooftop with string lights and warm evening transition",
            "hotel terrace with lounge seating and panoramic urban depth",
        ),
        "emotional_register": (
            "elevated urban openness",
            "sky-level domestic ease",
            "warm aerial intimacy",
        ),
        "material_language": (
            "concrete parapet + potted greenery + sky reflection",
            "tile floor + metal railing + string lights + warm dusk",
            "lounge furniture + glass barrier + urban panorama",
        ),
        "background_density": (
            "open with skyline depth",
            "airy elevated perspective",
            "panoramic but controlled",
        ),
        "brazil_anchor": (
            "authentic Brazilian urban rooftop life",
            "credible Brazilian terraço atmosphere",
        ),
    },
}


def _stable_index(seed: str, size: int) -> int:
    if size <= 1:
        return 0
    hashed = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return int(hashed, 16) % size


def _scene_affinity(user_prompt: str) -> dict[str, str]:
    text = str(user_prompt or "").lower()
    affinity = {
        "emotional_bias": "",
        "material_bias": "",
    }
    if any(token in text for token in ("linho", "linen", "algod", "cotton", "tricot", "croch")):
        affinity["emotional_bias"] = "soft lived-in ease"
        affinity["material_bias"] = "light wood + matte wall + soft textile"
    if any(token in text for token in ("blazer", "alfaiat", "structured", "tailored")):
        affinity["emotional_bias"] = "refined spatial confidence"
        affinity["material_bias"] = "stone planes + soft glass reflection + controlled geometry"
    if any(token in text for token in ("vestido", "dress", "saia", "skirt", "bufante", "puff")):
        affinity["emotional_bias"] = "warm domestic clarity"
    return affinity


def _profile_keywords(operational_profile: Optional[dict[str, Any]]) -> tuple[tuple[str, ...], float]:
    profile = operational_profile or {}
    guardrail = str(profile.get("guardrail_profile", "") or "")
    invention_budget = float(profile.get("invention_budget", 0.5) or 0.5)
    if guardrail == "strict_catalog":
        return (
            ("restrained", "quiet", "clean", "calm", "seamless", "very low", "low"),
            invention_budget,
        )
    if guardrail == "natural_commercial":
        return (
            ("warm", "calm", "soft", "credible", "believable", "everyday", "residential"),
            invention_budget,
        )
    if guardrail == "lifestyle_permissive":
        return (
            ("urban", "textured", "active", "vitality", "lived", "human", "open", "airy"),
            invention_budget,
        )
    if guardrail == "editorial_controlled":
        return (
            ("refined", "graphic", "architectural", "premium", "intentional", "controlled"),
            invention_budget,
        )
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


def select_scene_state(
    *,
    scenario_pool: str,
    mode_id: str,
    user_prompt: Optional[str] = None,
    seed_hint: str = "",
    operational_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    library = _SCENE_WORLD_LIBRARY.get(scenario_pool, _SCENE_WORLD_LIBRARY["residential_daylight"])
    affinity = _scene_affinity(user_prompt or "")
    profile_keywords, invention_budget = _profile_keywords(operational_profile)
    seed_base = f"{mode_id}:{scenario_pool}:{user_prompt or ''}:{seed_hint}"

    microcontext_options = list(library["microcontext"])
    emotional_options = list(library["emotional_register"])
    material_options = list(library["material_language"])
    density_options = list(library["background_density"])
    brazil_options = list(library["brazil_anchor"])

    if affinity["emotional_bias"] and affinity["emotional_bias"] in emotional_options:
        emotional_options = [affinity["emotional_bias"]] + [v for v in emotional_options if v != affinity["emotional_bias"]]
    if affinity["material_bias"] and affinity["material_bias"] in material_options:
        material_options = [affinity["material_bias"]] + [v for v in material_options if v != affinity["material_bias"]]

    microcontext_options = _prioritize_options(
        microcontext_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    emotional_options = _prioritize_options(
        emotional_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    material_options = _prioritize_options(
        material_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    density_options = _prioritize_options(
        density_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    brazil_options = _prioritize_options(
        brazil_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )

    microcontext = microcontext_options[_stable_index(seed_base + ":micro", len(microcontext_options))]
    emotional_register = emotional_options[_stable_index(seed_base + ":emotion", len(emotional_options))]
    material_language = material_options[_stable_index(seed_base + ":material", len(material_options))]
    background_density = density_options[_stable_index(seed_base + ":density", len(density_options))]
    brazil_anchor = brazil_options[_stable_index(seed_base + ":brazil", len(brazil_options))]

    return {
        "world_family": scenario_pool,
        "microcontext": microcontext,
        "emotional_register": emotional_register,
        "material_language": material_language,
        "background_density": background_density,
        "brazil_anchor": brazil_anchor,
        "scene_signature": "|".join(
            [
                scenario_pool,
                microcontext,
                emotional_register,
                material_language,
                background_density,
                brazil_anchor,
            ]
        ),
    }
