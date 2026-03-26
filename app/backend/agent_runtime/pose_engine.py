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
            "stable grounded stance with garment-first readability",
            "rooted catalog stance with calm body control",
            "quiet upright stance with deliberate stillness",
        ),
        "weight_shift": (
            "soft weight balance through both feet",
            "slight weight settlement into one leg without distorting the silhouette",
            "even lower-body support with quiet natural asymmetry",
        ),
        "arm_logic": (
            "one arm resting naturally along the body while the other stays slightly released from the waistline",
            "arms kept quiet and unobtrusive, leaving the waist and side seam visible",
            "hands relaxed at the sides with gentle separation from the skirt",
        ),
        "torso_orientation": (
            "front-facing torso with a subtle natural turn",
            "mostly frontal body alignment with a soft shoulder angle",
            "clean body alignment with restrained torso twist",
        ),
        "head_direction": (
            "calm head direction toward camera",
            "steady near-camera head position",
            "quiet front-facing head placement",
        ),
        "gesture_intention": (
            "controlled commercial stillness",
            "quiet premium composure",
            "stable catalog clarity",
        ),
    },
    "relaxed": {
        "stance_logic": (
            "grounded relaxed stance with breathable body space",
            "soft natural stance with lived-in ease",
            "easy balanced stance with commercial warmth",
        ),
        "weight_shift": (
            "gentle weight shift into one hip",
            "soft weight placement through one leg with relaxed balance",
            "subtle off-center balance that keeps the silhouette clear",
        ),
        "arm_logic": (
            "one hand relaxed near the side seam while the other hangs naturally",
            "arms resting loosely with one hand lightly clearing the waistline",
            "one hand relaxed near the skirt while the opposite arm falls naturally",
        ),
        "torso_orientation": (
            "slight torso turn that keeps the garment readable",
            "gentle shoulder angle with open upper body",
            "soft three-quarter torso orientation without hiding the front",
        ),
        "head_direction": (
            "head open toward camera with relaxed attention",
            "near-camera head turn with a warm relaxed expression",
            "soft head angle that stays commercially approachable",
        ),
        "gesture_intention": (
            "easy commercial warmth",
            "relaxed human presence",
            "soft premium naturalness",
        ),
    },
    "candid": {
        "stance_logic": (
            "paused mid-step stance with natural garment movement",
            "light walking gesture frozen at a believable moment",
            "spontaneous everyday stance with subtle motion",
        ),
        "weight_shift": (
            "weight passing naturally through one leg during a small step",
            "dynamic but controlled lower-body shift that lets the hem move",
            "off-center balance suggesting real movement without blur logic",
        ),
        "arm_logic": (
            "one hand lightly grazing the skirt while the other swings softly",
            "arms moving naturally with one hand kept clear of the garment's key construction",
            "one hand relaxed near the waist while the opposite arm follows the step",
        ),
        "torso_orientation": (
            "slight body turn that introduces directional energy",
            "soft angled torso with lived-in movement",
            "walk-oriented torso rotation that preserves the front read",
        ),
        "head_direction": (
            "slightly off-camera head direction with natural engagement",
            "softly turned head that feels caught mid-moment",
            "casual near-camera glance with everyday spontaneity",
        ),
        "gesture_intention": (
            "commercial spontaneity",
            "lived-in motion with garment clarity",
            "approachable candid energy",
        ),
    },
    "directed": {
        "stance_logic": (
            "confident contrapposto with one hip pushed out and clear vertical line",
            "strong S-curve stance with pronounced hip displacement and elongated torso",
            "power stride pose — one foot slightly forward, body angled like mid-walk on a runway",
            "architectural lean against a surface with one leg crossed over the other creating diagonal tension",
            "commanding three-quarter stance with shoulder leading toward camera and hip angled away",
            "bold wide stance with weight planted and body owning maximum frame space",
        ),
        "weight_shift": (
            "dramatic weight drop into one hip creating a pronounced S-line through the body",
            "assertive weight transfer to one leg with the free leg creating negative space",
            "pronounced contrapposto weight shift that makes the waist and hip line sculptural",
            "dynamic forward-leaning weight that suggests motion and energy",
            "controlled hip push to one side with upper body compensating in the opposite direction",
            "grounded power stance with weight evenly distributed and strong planted presence",
        ),
        "arm_logic": (
            "one hand placed firmly on hip with elbow angled outward, the other arm hanging with editorial control",
            "one hand touching the side of the neck or jaw while the other arm creates a clean line along the body",
            "both hands adjusting the garment — one at the collar, one at the hem — in a styled editorial gesture",
            "one arm extended to touch a surface or prop with fashion authority while the other rests at the hip",
            "one hand running through or holding hair back from the face while the opposite arm stays structured",
            "arms crossed loosely at waist level or one hand gripping the opposite elbow with relaxed confidence",
        ),
        "torso_orientation": (
            "sculpted three-quarter torso angle with shoulder blade tension visible and deliberate spinal line",
            "dramatic shoulder rotation — one shoulder advanced toward camera creating depth and dimension",
            "strong angular torso twist that creates graphic shadow play across the garment surface",
            "elongated upright torso with ribcage lifted and deliberate posture authority",
            "slightly forward-leaning torso with controlled chin position creating editorial intensity",
            "powerful open chest orientation with shoulders pulled back and collarbones prominent",
        ),
        "head_direction": (
            "chin lifted at 15 degrees with eyes locked directly on camera — commanding, not passive",
            "head turned to three-quarter profile with a sharp knowing gaze back toward camera",
            "slightly downward gaze with chin parallel to shoulder, creating editorial mystery",
            "head tilted subtly with an expression of confident self-awareness and magnetic presence",
            "strong profile angle with jaw defined and neck elongated — pure fashion authority",
            "direct forward-facing head position with an intense, fashion-editorial stare that commands attention",
        ),
        "gesture_intention": (
            "magazine-cover authority with every body line deliberate and powerful",
            "runway-to-editorial energy — the model is not posing, she is PERFORMING for the camera",
            "fashion-forward command — the body communicates status, confidence, and deliberate style",
            "editorial precision with controlled intensity — every angle earns its place in the frame",
            "haute couture presence — sculptural body language that elevates the garment to art",
            "power-editorial magnetism — the viewer cannot look away because the pose demands attention",
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
        affinity["arm_logic"] = "one hand lightly grazing the skirt while the other stays relaxed and clear of the waistline"
        affinity["surface_direction"] = "with a soft weight shift, one hand lightly grazing the skirt, and a slight torso turn that keeps the waist and sleeves visible"
    elif any(token in text for token in ("blazer", "alfaiat", "tailored", "structured", "lapela", "lapel")):
        affinity["arm_logic"] = "one arm relaxed while the other stays slightly set away from the torso to preserve the lapel and shoulder line"
        affinity["surface_direction"] = "with a composed stance, shoulders aligned, and one arm kept slightly away from the torso to preserve the tailoring line"

    if framing_profile == "full_body" and not affinity["surface_direction"]:
        affinity["surface_direction"] = "with a grounded stance, a subtle weight shift through one leg, and arms kept quiet so the full silhouette remains clear"
    elif framing_profile == "three_quarter" and not affinity["surface_direction"]:
        affinity["surface_direction"] = "with a relaxed torso turn, one hand kept clear of the waistline, and a natural head direction that keeps the upper-to-skirt transition readable"
    elif framing_profile == "editorial_mid" and not affinity["surface_direction"]:
        affinity["surface_direction"] = "with an intentional torso angle, controlled arm placement, and a head direction that reinforces the image line"

    if mode_id == "catalog_clean":
        affinity["gesture_intention"] = "quiet premium composure"
    elif mode_id == "natural":
        affinity["gesture_intention"] = "relaxed human presence"
    elif mode_id == "lifestyle":
        affinity["gesture_intention"] = "approachable candid energy"
    elif mode_id == "editorial_commercial":
        affinity["gesture_intention"] = "fashion-aware intention"

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
