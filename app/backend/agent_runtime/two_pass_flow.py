"""
Helpers do fluxo experimental two-pass.

Objetivo:
- Reaproveitar o selector automatico da fase 1.
- Montar prompts curtos e reproduziveis para:
  1. gerar uma base fiel da roupa
  2. editar modelo/contexto sem destruir a peca
"""
from __future__ import annotations

from typing import Any, Optional


_SLEEVE_LOCKS = {
    "set-in": "same set-in sleeve construction",
    "raglan": "same raglan sleeve construction",
    "dolman_batwing": "same dolman-batwing sleeve architecture",
    "drop_shoulder": "same drop-shoulder shoulder fall",
    "cape_like": "same cape-like arm coverage",
}

_HEM_LOCKS = {
    "straight": "same straight hem behavior",
    "rounded": "same rounded hem behavior",
    "asymmetric": "same asymmetric hem behavior",
    "cocoon": "same rounded cocoon hem behavior",
}

_LENGTH_LOCKS = {
    "cropped": "keep the garment ending at a cropped length relative to the model body",
    "waist": "keep the garment ending around the waist relative to the model body",
    "hip": "keep the garment ending around the hips relative to the model body",
    "upper_thigh": "keep the garment ending around the upper thigh relative to the model body",
    "mid_thigh": "keep the garment ending around the mid thigh relative to the model body",
    "knee_plus": "keep the garment extending to the knee or below relative to the model body",
}

_VOLUME_LOCKS = {
    "fitted": "same fitted silhouette",
    "regular": "same regular-volume silhouette",
    "oversized": "same oversized silhouette",
    "draped": "same draped fluid silhouette",
    "structured": "same structured silhouette",
}

_FRONT_LOCKS = {
    "open": "same open-front construction",
    "partial": "same partially open front behavior",
    "closed": "same front closure behavior",
}


def _collect_lock_clauses(structural_contract: Optional[dict[str, Any]]) -> list[str]:
    contract = structural_contract or {}
    locks = [
        "same overall garment identity",
        "same knit or crochet texture continuity",
        "same stitch pattern and fiber relief",
        "same pattern placement and stripe scale if present",
    ]

    front = str(contract.get("front_opening", "") or "").strip().lower()
    volume = str(contract.get("silhouette_volume", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    hem = str(contract.get("hem_shape", "") or "").strip().lower()
    length = str(contract.get("garment_length", "") or "").strip().lower()

    if front in _FRONT_LOCKS:
        locks.append(_FRONT_LOCKS[front])
    if volume in _VOLUME_LOCKS:
        locks.append(_VOLUME_LOCKS[volume])
    if sleeve in _SLEEVE_LOCKS:
        locks.append(_SLEEVE_LOCKS[sleeve])
    if hem in _HEM_LOCKS:
        locks.append(_HEM_LOCKS[hem])
    if length in _LENGTH_LOCKS:
        locks.append(_LENGTH_LOCKS[length])

    must_keep = [str(item).strip() for item in (contract.get("must_keep", []) or []) if str(item).strip()]
    if must_keep:
        locks.append("preserve these structural cues: " + ", ".join(must_keep[:4]))
    return locks


def build_structural_hint(structural_contract: Optional[dict[str, Any]]) -> Optional[str]:
    contract = structural_contract or {}
    if not contract.get("enabled"):
        return None

    parts: list[str] = []
    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    volume = str(contract.get("silhouette_volume", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    hem = str(contract.get("hem_shape", "") or "").strip().lower()
    length = str(contract.get("garment_length", "") or "").strip().lower()

    if subtype and subtype != "unknown":
        parts.append(subtype)
    if volume and volume != "unknown":
        parts.append(f"{volume} silhouette")
    if sleeve and sleeve != "unknown":
        parts.append(f"{sleeve} sleeve architecture")
    if hem and hem != "unknown":
        parts.append(f"{hem} hem")
    if length in _LENGTH_LOCKS:
        parts.append(length.replace("_", "-") + " length")

    hint = ", ".join(parts).strip()
    return hint or None


def build_two_pass_edit_prompt(
    structural_contract: Optional[dict[str, Any]],
    *,
    scene_type: str = "interno",
    pose_style: str = "tradicional",
    innerwear: str = "clean white crew-neck tee",
    user_prompt: Optional[str] = None,
) -> str:
    locks = _collect_lock_clauses(structural_contract)

    scene_clause = (
        "bright premium indoor catalog environment with natural window light"
        if str(scene_type).strip().lower() != "externo"
        else "premium outdoor fashion environment with soft natural daylight"
    )
    pose_clause = (
        "Use a natural fashion pose with full garment visibility."
        if str(pose_style).strip().lower() == "criativa"
        else "Use a standing pose with full garment visibility."
    )

    sentences = [
        "Keep the garment exactly the same: " + ", ".join(locks) + ".",
        "Replace the model with a clearly different adult woman with different face, skin tone, and hair.",
        f"Change the inner top to a {innerwear.strip() or 'clean white crew-neck tee'}.",
        f"Place her in a {scene_clause}.",
        pose_clause,
        "Keep the image highly photorealistic, premium fashion catalog quality, with natural skin texture and realistic body proportions.",
    ]

    extra_direction = (user_prompt or "").strip()
    if extra_direction:
        sentences.append(f"Additional commercial direction: {extra_direction[:220]}.")

    return " ".join(sentence.strip() for sentence in sentences if sentence.strip())


def build_parameterized_two_pass_edit_prompt(
    structural_contract: Optional[dict[str, Any]],
    *,
    casting_profile: Optional[dict[str, Any]] = None,
    scene_description: Optional[str] = None,
    pose_description: Optional[str] = None,
    innerwear: str = "clean white crew-neck tee",
    user_prompt: Optional[str] = None,
) -> str:
    locks = _collect_lock_clauses(structural_contract)

    profile = casting_profile or {}
    identity_sentence = str(profile.get("identity_sentence", "") or "").strip()
    if not identity_sentence:
        identity_sentence = "a clearly different adult Brazilian woman with distinct face, skin tone, and hair"

    difference_instruction = str(profile.get("difference_instruction", "") or "").strip()
    recent_avoid = [str(item).strip() for item in (profile.get("recent_avoid", []) or []) if str(item).strip()]

    scene_clause = (scene_description or "").strip()
    if not scene_clause:
        scene_clause = "bright premium Brazilian indoor catalog environment with natural window light"
    pose_clause = (pose_description or "").strip()
    if not pose_clause:
        pose_clause = "Use a standing pose with full garment visibility."

    sentences = [
        "Keep the garment exactly the same: " + ", ".join(locks) + ".",
        f"Replace the model with {identity_sentence}.",
        difference_instruction,
        (
            "This casting should not resemble recent outputs characterized by "
            + ", ".join(recent_avoid)
            + "."
        ) if recent_avoid else "",
        f"Change the inner top to a {innerwear.strip() or 'clean white crew-neck tee'}.",
        f"Place her in a {scene_clause}.",
        pose_clause,
        "Keep the image highly photorealistic, premium fashion catalog quality, with natural skin texture and realistic body proportions.",
    ]

    extra_direction = (user_prompt or "").strip()
    if extra_direction:
        sentences.append(f"Additional commercial direction: {extra_direction[:220]}.")

    return " ".join(sentence.strip() for sentence in sentences if sentence.strip())


def build_art_direction_two_pass_edit_prompt(
    structural_contract: Optional[dict[str, Any]],
    *,
    art_direction: dict[str, Any],
    garment_material: str = "garment fabric",
    garment_color: str = "the garment colors and yarn tones",
    user_prompt: Optional[str] = None,
) -> str:
    locks = _collect_lock_clauses(structural_contract)

    casting = art_direction.get("casting_profile", {}) or {}
    scene = art_direction.get("scene", {}) or {}
    pose = art_direction.get("pose", {}) or {}
    camera = art_direction.get("camera", {}) or {}
    lighting = art_direction.get("lighting", {}) or {}
    styling = art_direction.get("styling", {}) or {}

    identity_sentence = str(casting.get("identity_sentence", "") or "").strip()
    if not identity_sentence:
        identity_sentence = "a clearly different adult Brazilian woman with distinct face, skin tone, and hair"

    phenotype_sentence = ", ".join(
        [
            part for part in [
                "Brazilian woman",
                str(casting.get("skin", "") or "").strip(),
                str(casting.get("hair", "") or "").strip(),
                str(casting.get("makeup", "") or "").strip(),
                str(casting.get("expression", "") or "").strip(),
            ]
            if part
        ]
    )
    if not phenotype_sentence:
        phenotype_sentence = "Brazilian woman with distinct face, skin tone, and hair"

    recent_avoid = [str(item).strip() for item in (casting.get("recent_avoid", []) or []) if str(item).strip()]
    difference_instruction = str(casting.get("difference_instruction", "") or "").strip()
    age_years = str(art_direction.get("age_years", "") or "30").strip()
    visual_label = str(art_direction.get("model_visual_label", "") or "Brazilian visual profile").strip()
    angle_description = str(pose.get("angle_description", "") or "eye-level standing framing with full garment visibility").strip()
    model_pose = str(pose.get("model_hero_pose", "") or "standing pose with full garment visibility").strip()

    style_clause = f"[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), {angle_description}."
    scene_clause = (
        "[2. SCENE] "
        + str(scene.get("description", "") or "Brazilian lifestyle environment")
        + ", authentic context, (cluttered/lived-in background:0.9)."
    )
    model_clause = (
        f"[3. MODEL HERO] {phenotype_sentence}, {visual_label}, {age_years}yo model, {model_pose}, "
        "(natural skin texture, visible pores, asymmetric features:1.3)."
    )
    camera_clause = (
        f"[4. CAMERA] Shot on {str(camera.get('device', '') or 'Canon R6')}, "
        f"{str(camera.get('lens', '') or '50mm lens')}, "
        f"(subtle chromatic aberration, ISO {str(camera.get('grain_level', '') or '800')} noise, slight motion blur:1.2)."
    )
    lighting_clause = (
        f"[5. LIGHTING] {str(lighting.get('description', '') or 'soft mixed daylight')}, "
        "mixed color temperature, (imperfect ambient bounce:1.1)."
    )
    texture_clause = (
        f"[6. TEXTURE LOCK] (Macro-accurate {garment_material}:1.5), exact thread count, proper fabric weight, "
        f"(realistic light absorption on {garment_color}:1.4)."
    )
    negative_clause = (
        "[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), "
        "symmetrical face, altered clothing silhouette, over-smoothed fabric, resemblance to the source woman's identity."
    )

    sentences = [
        "Keep the garment exactly the same: " + ", ".join(locks) + ".",
        f"Replace the model with {identity_sentence}.",
        "Perform a full model swap: do not preserve the source woman's facial identity, face shape, eye area, nose, mouth, hairline, skin tone, or age impression.",
        difference_instruction,
        (
            "This casting should not resemble recent outputs characterized by "
            + ", ".join(recent_avoid)
            + "."
        ) if recent_avoid else "",
        f"Change the inner top to a {str(styling.get('innerwear', '') or 'clean white crew-neck tee')}.",
        f"Change the lower-body styling to {str(styling.get('bottom', '') or 'clean commercial separates')}.",
        style_clause,
        scene_clause,
        model_clause,
        camera_clause,
        lighting_clause,
        texture_clause,
        negative_clause,
        "Keep the image highly photorealistic with natural skin texture and realistic body proportions.",
    ]

    extra_direction = (user_prompt or "").strip()
    if extra_direction:
        sentences.append(f"Additional commercial direction: {extra_direction[:220]}.")

    return " ".join(sentence.strip() for sentence in sentences if sentence.strip())
