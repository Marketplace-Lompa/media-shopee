"""
Pose engine latent for fashion image direction.

Objetivo:
- transformar pose_energy em uma direção corporal específica
- manter a pose comercialmente legível para a roupa
- evitar descrições vagas como "stable pose" ou "composed stance" sem gesto real
"""
from __future__ import annotations

import hashlib
from typing import Any, Optional


_POSE_LIBRARY: dict[str, dict[str, tuple[str, ...]]] = {
    "static": {
        "stance_logic": (
            "grounded presence that makes the garment the focal point",
            "rooted foundation emphasizing vertical clarity",
            "quiet structure supporting the clothing architecture",
        ),
        "weight_shift": (
            "balanced stability prioritizing silhouette symmetry",
            "subtle ease that prevents stiffness without distorting fit",
            "even support ensuring clear read of long geometric lines",
        ),
        "arm_logic": (
            "arm placement that avoids obscuring key construction details",
            "limbs kept quiet to preserve the waistline and chest view",
            "negative space maintained between arms and torso",
        ),
        "torso_orientation": (
            "clean forward alignment to showcase the front features",
            "slight depth angle that remains completely legible",
            "controlled presentation maximizing garment surface visibility",
        ),
        "head_direction": (
            "steady engagement that doesn't distract from the style",
            "calm focus radiating commercial reliability",
            "quiet presence framing the upper garment area",
        ),
        "gesture_intention": (
            "controlled commercial stillness",
            "premium composure focused entirely on the product",
            "catalog clarity without artificial tension",
        ),
    },
    "relaxed": {
        "stance_logic": (
            "approachable posture with breathable physical space",
            "soft foundation implying lived-in ease",
            "easy equilibrium carrying warmth and comfort",
        ),
        "weight_shift": (
            "gentle shift creating natural fabric drape",
            "relaxed support that softens the overall silhouette",
            "off-center harmony preventing structural rigidity",
        ),
        "arm_logic": (
            "arms adopting a comfortable, uncontrived arrangement",
            "limbs arranged organically while keeping key design points visible",
            "casual limb positioning that supports the mood without blocking details",
        ),
        "torso_orientation": (
            "welcoming angle that introduces conversational depth",
            "soft rotation that highlights how the fabric moves",
            "three-quarter implied motion retaining primary visibility",
        ),
        "head_direction": (
            "warm attention aimed at the viewer",
            "relaxed and engaging focal point",
            "approachable orientation supporting an everyday narrative",
        ),
        "gesture_intention": (
            "easy commercial warmth",
            "relaxed human presence validating the comfort",
            "soft premium naturalness meant for lifestyle bridging",
        ),
    },
    "candid": {
        "stance_logic": (
            "moment captured in mid-transition to show clothing dynamics",
            "spontaneous foundation implying immediate action",
            "everyday forward-moving energy",
        ),
        "weight_shift": (
            "transitional weight that animates the fabric",
            "dynamic support letting the hem or silhouette naturally sway",
            "active balance suggesting progress rather than stillness",
        ),
        "arm_logic": (
            "arms in natural mid-motion, safely clearing key focal points",
            "limbs following organic movement patterns",
            "unstudied arm positions that emphasize candid authenticity",
        ),
        "torso_orientation": (
            "spirited angle providing directional energy to the look",
            "lived-in rotation proving the clothing's real-world viability",
            "active orientation that retains the commercial read",
        ),
        "head_direction": (
            "caught-in-the-moment glance or distraction",
            "spontaneous engagement breaking the fourth wall softly",
            "off-camera attention implying a broader environment",
        ),
        "gesture_intention": (
            "commercial spontaneity making the fashion tangible",
            "lived-in motion validating the real-world use",
            "approachable candid energy connecting with the consumer",
        ),
    },
    "directed": {
        "stance_logic": (
            "architectural foundation commanding the frame space",
            "bold stance defining a strong stylistic narrative",
            "sculptural base elevating the garment into a fashion statement",
            "tension-driven base highlighting the cut and structure",
            "authoritative posture anchoring a premium visual",
            "commanding spatial ownership maximizing physical impact",
        ),
        "weight_shift": (
            "dramatic transfer defining an assertive body line",
            "pronounced hip or leg engagement creating sculptural curves",
            "intentional imbalance producing graphic tension",
            "forward-driven energy implying power and purpose",
            "controlled asymmetry emphasizing the tailoring",
            "grounded power distribution radiating elite confidence",
        ),
        "arm_logic": (
            "decisive arm geometry creating bold negative space",
            "intentional limb placement interacting with the garment respectfully",
            "highly styled hand or arm positioning that adds high-fashion flair",
            "arms framing the body to guide the viewer's eye to the key details",
            "structured limb tension complementing the apparel's shape",
            "deliberate crossing or anchoring to exude sophisticated control",
        ),
        "torso_orientation": (
            "sculpted torso rotation demanding visual attention",
            "dramatic angle producing graphic light and shadow across the piece",
            "elongated presentation exuding posture authority",
            "challenging orientation introducing edge and mystery",
            "powerful chest prominence projecting luxury presence",
            "intentional twist defining the silhouette with exact precision",
        ),
        "head_direction": (
            "commanding focal connection directly demanding attention",
            "sharp profile or three-quarter gaze exuding knowing confidence",
            "deliberately elevated or lowered angle adding editorial edge",
            "magnetic awareness unbothered by the camera's presence",
            "strong definition of jaw and neck supporting the fashion narrative",
            "intense visual lock intended to stop the viewer completely",
        ),
        "gesture_intention": (
            "magazine-cover authority with every visual line deliberate",
            "performative energy transcending simple wearability",
            "fashion-forward command signaling elite status",
            "editorial precision validating the premium tier",
            "haute-inspired presence making the clothing art",
            "magnetic tension ensuring the image is unforgettable",
        ),
    },
}


def _stable_index(seed: str, size: int) -> int:
    if size <= 1:
        return 0
    hashed = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return int(hashed, 16) % size


def _pose_affinity(user_prompt: str, framing_profile: str, mode_id: str) -> dict[str, str]:
    text = str(user_prompt or "").lower()
    affinity = {
        "arm_logic": "",
        "gesture_intention": "",
        "surface_direction": "",
    }

    if any(token in text for token in ("vestido", "dress", "saia", "skirt", "evasê", "evase", "bufante", "puff")):
        affinity["arm_logic"] = "arms placed to allow the lower garment volume to breathe and expand naturally"
        affinity["surface_direction"] = "with an implicit fluid motion prioritizing the hemline and volume spread"
    elif any(token in text for token in ("blazer", "alfaiat", "tailored", "structured", "lapela", "lapel")):
        affinity["arm_logic"] = "arms positioned to preserve the tailoring, ensuring lapels and shoulder lines remain uninterrupted"
        affinity["surface_direction"] = "with architectural alignment that respects the tailored structuring of the upper body"

    if framing_profile == "full_body" and not affinity["surface_direction"]:
        affinity["surface_direction"] = "anchoring the full vertical line clearly to communicate head-to-toe proportions"
    elif framing_profile == "three_quarter" and not affinity["surface_direction"]:
        affinity["surface_direction"] = "creating engaging depth that connects the torso naturally down past the waistline"
    elif framing_profile == "editorial_mid" and not affinity["surface_direction"]:
        affinity["surface_direction"] = "using deliberate angles to maximize the graphic impact of the upper body structure"

    if mode_id == "catalog_clean":
        affinity["gesture_intention"] = "premium composure focused strictly on product clarity"
    elif mode_id == "natural":
        affinity["gesture_intention"] = "relaxed human presence bridging everyday lifestyle"
    elif mode_id == "lifestyle":
        affinity["gesture_intention"] = "approachable candid energy implying movement"
    elif mode_id == "editorial_commercial":
        affinity["gesture_intention"] = "fashion-aware intention validating a higher tier"

    return affinity


def _pose_profile_keywords(operational_profile: Optional[dict[str, Any]]) -> tuple[tuple[str, ...], float]:
    profile = operational_profile or {}
    guardrail = str(profile.get("guardrail_profile", "") or "")
    invention_budget = float(profile.get("invention_budget", 0.5) or 0.5)
    if guardrail == "strict_catalog":
        return (
            ("stable", "rooted", "quiet", "calm", "front", "steady", "controlled"),
            invention_budget,
        )
    if guardrail == "natural_commercial":
        return (
            ("relaxed", "soft", "warm", "easy", "open", "gentle"),
            invention_budget,
        )
    if guardrail == "lifestyle_permissive":
        return (
            ("spontaneous", "mid-step", "walking", "lived-in", "candid", "approachable"),
            invention_budget,
        )
    if guardrail == "editorial_controlled":
        return (
            ("intentional", "graphic", "fashion", "directed", "controlled"),
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


def select_pose_state(
    *,
    pose_energy: str,
    framing_profile: str,
    scenario_pool: str,
    mode_id: str,
    user_prompt: Optional[str] = None,
    seed_hint: str = "",
    operational_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    library = _POSE_LIBRARY.get(pose_energy, _POSE_LIBRARY["relaxed"])
    affinity = _pose_affinity(user_prompt or "", framing_profile, mode_id)
    profile_keywords, invention_budget = _pose_profile_keywords(operational_profile)
    seed_base = f"{mode_id}:{pose_energy}:{framing_profile}:{scenario_pool}:{user_prompt or ''}:{seed_hint}"

    stance_options = list(library["stance_logic"])
    weight_options = list(library["weight_shift"])
    arm_options = list(library["arm_logic"])
    torso_options = list(library["torso_orientation"])
    head_options = list(library["head_direction"])
    gesture_options = list(library["gesture_intention"])

    if affinity["arm_logic"] and affinity["arm_logic"] not in arm_options:
        arm_options = [affinity["arm_logic"]] + arm_options
    if affinity["gesture_intention"] and affinity["gesture_intention"] in gesture_options:
        gesture_options = [affinity["gesture_intention"]] + [v for v in gesture_options if v != affinity["gesture_intention"]]

    stance_options = _prioritize_options(
        stance_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    weight_options = _prioritize_options(
        weight_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    arm_options = _prioritize_options(
        arm_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    torso_options = _prioritize_options(
        torso_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    head_options = _prioritize_options(
        head_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )
    gesture_options = _prioritize_options(
        gesture_options,
        keywords=profile_keywords,
        invention_budget=invention_budget,
    )

    stance_logic = stance_options[_stable_index(seed_base + ":stance", len(stance_options))]
    weight_shift = weight_options[_stable_index(seed_base + ":weight", len(weight_options))]
    arm_logic = arm_options[_stable_index(seed_base + ":arm", len(arm_options))]
    torso_orientation = torso_options[_stable_index(seed_base + ":torso", len(torso_options))]
    head_direction = head_options[_stable_index(seed_base + ":head", len(head_options))]
    gesture_intention = gesture_options[_stable_index(seed_base + ":gesture", len(gesture_options))]
    garment_interaction = "keep hands and body placement clear of key garment construction details"
    surface_direction = affinity["surface_direction"] or (
        f"with {weight_shift}, {arm_logic}, and {torso_orientation}"
    )

    return {
        "pose_family": pose_energy,
        "stance_logic": stance_logic,
        "weight_shift": weight_shift,
        "arm_logic": arm_logic,
        "torso_orientation": torso_orientation,
        "head_direction": head_direction,
        "gesture_intention": gesture_intention,
        "garment_interaction": garment_interaction,
        "surface_direction": surface_direction,
        "pose_signature": "|".join(
            [
                pose_energy,
                framing_profile,
                stance_logic,
                weight_shift,
                arm_logic,
                torso_orientation,
                head_direction,
                gesture_intention,
            ]
        ),
    }
