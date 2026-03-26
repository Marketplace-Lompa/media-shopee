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

from agent_runtime.structural import get_set_member_labels, get_set_member_keys


# Mapeamento de comprimento para frase natural — único lock granular que
# comprovadamente previne drift visual (o Nano tende a mudar o comprimento).
_LENGTH_PHRASES = {
    "cropped": "cropped length",
    "waist": "waist length",
    "hip": "hip length",
    "upper_thigh": "upper-thigh length",
    "mid_thigh": "mid-thigh length",
    "knee_plus": "knee-or-below length",
}

_REFERENCE_USAGE_RULES_BASE = [
    "Use all references only as GARMENT references for shape, fabric, stitch, and color behavior.",
    "Never transfer identity from references: do not copy face, skin tone, body type, hairline, hairstyle, or age impression.",
    "Never repeat the exact composition, framing, or dominant gesture from the references. Keep the garment completely faithful, but create an entirely new context and physical presence.",
]

_REFERENCE_USAGE_RULES_STRICT = [
    "Treat every visible person in references as an anonymous mannequin used only for garment transfer.",
    "Generate a fully new Brazilian model identity from scratch; any resemblance to reference people is a hard failure.",
]

_REFERENCE_USAGE_RULES_HIGH_GUARD = [
    "Use references for garment-only visual evidence; identity transfer from references is strictly forbidden.",
    "Deliberately separate facial geometry from references by changing jawline, eye spacing, nose bridge, lip shape, and hairline.",
]


def _tag_set(payload: Optional[dict[str, Any]]) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    return {
        str(tag).strip().lower()
        for tag in (payload.get("tags", []) or [])
        if str(tag).strip()
    }


def _scene_creative_brief(
    scene: Optional[dict[str, Any]],
    *,
    preset: Optional[str] = None,
) -> str:
    tags = _tag_set(scene)
    qualities: list[str] = []

    if "indoor" in tags:
        qualities.append("an authentic Brazilian interior")
    elif "outdoor" in tags:
        qualities.append("an authentic Brazilian exterior")
    else:
        qualities.append("an authentic Brazilian setting")

    if "premium" in tags:
        qualities.append("premium but believable atmosphere")
    if "architecture" in tags:
        qualities.append("clean architectural rhythm")
    if "coastal" in tags:
        qualities.append("breathable coastal openness")
    if "balcony" in tags or "rooftop" in tags:
        qualities.append("light airy depth")
    if "cafe" in tags:
        qualities.append("casual editorial warmth")
    if "showroom" in tags:
        qualities.append("restrained commercial clarity")
    if "colorful" in tags:
        qualities.append("controlled Brazilian color presence")
    if "authentic" in tags or "lifestyle" in tags:
        qualities.append("lived-in naturalism")

    preset_hint = str(preset or "").strip().lower()
    if preset_hint == "premium_lifestyle":
        qualities.append("editorial polish without looking staged")
    elif preset_hint == "marketplace_lifestyle":
        qualities.append("commercial readability with natural realism")
    elif preset_hint == "catalog_clean":
        qualities.append("low-noise commercial clarity")
    elif preset_hint == "ugc_real_br":
        qualities.append("creator-led Brazilian social-commerce realism")
        qualities.append("honest creator-context atmosphere")

    qualities = list(dict.fromkeys([item.strip() for item in qualities if item.strip()]))
    quality_text = ", ".join(qualities[:4])
    if preset_hint == "ugc_real_br":
        environment_cues: list[str] = []
        if "mirror" in tags:
            environment_cues.append("mirror try-on energy")
        if "boutique" in tags or "store" in tags:
            environment_cues.append("boutique or store context")
        if "apartment" in tags:
            environment_cues.append("creator-at-home capture plausibility")
        if "cafe" in tags:
            environment_cues.append("social everyday hangout context")
        cue_text = ", ".join(environment_cues[:3]) if environment_cues else "a believable creator-content environment"
        return (
            "Invent a fresh Brazilian creator-content scene that feels genuinely compatible with the garment and socially believable for an influencer-style capture. "
            f"Aim for {quality_text} and {cue_text}. "
            "Let the environment include one or two authentic contextual cues, such as racks, mirrors, curtain edges, counters, hallway details, or lived-in interior depth, while keeping the garment readable and clearly in focus."
        )
    return (
        "Invent a fresh Brazilian scene that feels compatible with the garment and the campaign tone. "
        f"Aim for {quality_text}. "
        "Keep the environment coherent, premium, and visually quiet enough to let the garment remain the hero."
    )


def _pose_creative_brief(
    structural_contract: Optional[dict[str, Any]],
    *,
    pose: Optional[dict[str, Any]] = None,
    set_detection: Optional[dict[str, Any]] = None,
    preset: Optional[str] = None,
) -> str:
    contract = structural_contract or {}
    pose_tags = _tag_set(pose)
    set_info = set_detection or {}
    focus_targets: list[str] = []

    front = str(contract.get("front_opening", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    hem = str(contract.get("hem_shape", "") or "").strip().lower().replace("_", " ")
    volume = str(contract.get("silhouette_volume", "") or "").strip().lower().replace("_", " ")
    included_labels = get_set_member_labels(
        set_info,
        include_policies={"must_include", "optional"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )
    included_keys = get_set_member_keys(
        set_info,
        include_policies={"must_include", "optional"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )

    if front == "open":
        focus_targets.append("the open front")
    if sleeve in {"cape_like", "dolman_batwing"}:
        focus_targets.append("the lateral drape and arm coverage")
    if hem:
        focus_targets.append(f"the {hem} hem")
    if volume:
        focus_targets.append(f"the {volume} silhouette")
    if "scarf" in included_keys:
        focus_targets.append("the coordinated scarf")
    elif included_labels:
        focus_targets.append("the coordinated set members")

    preset_hint = str(preset or "").strip().lower()
    if preset_hint == "ugc_real_br":
        movement_text = (
            "Allow expressive, socially engaging movement and creator-style asymmetry"
            if "movement" in pose_tags else
            "Favor captivating creator body language with attitude, micro-gesture, and believable social charisma"
        )
    else:
        movement_text = (
            "Allow subtle controlled movement"
            if "movement" in pose_tags else
            "Favor calm premium catalog body language"
        )
    focus_text = ", ".join(focus_targets[:4]) if focus_targets else "the garment silhouette and details"
    return (
        "Invent a fresh pose that is born from the garment instead of forcing the garment to adapt to the pose. "
        f"{movement_text}, and make sure the pose highlights {focus_text}. "
        "Avoid occluding key construction lines or compressing the natural fall of the piece."
    )


def _action_context_brief(action_context: Optional[str]) -> str:
    context = str(action_context or "").strip()
    if not context:
        return ""
    return (
        "Use this only as a natural action intention, not as a rigid pose to copy: "
        f"{context}. "
        "Let it create believable hand placement, posture, and micro-asymmetry while preserving garment readability."
    )


def _ugc_entropy_clauses(ugc_entropy_profile: Optional[dict[str, Any]]) -> list[str]:
    profile = ugc_entropy_profile if isinstance(ugc_entropy_profile, dict) else {}
    if not profile.get("enabled"):
        return []
    clauses = [str(item).strip() for item in (profile.get("clauses", []) or []) if str(item).strip()]
    if not clauses:
        return []
    return [
        "For this UGC result, make the image read as a genuine Brazilian creator or influencer phone capture for social-commerce, not as a polished editorial recreation of UGC.",
        *clauses,
        "Avoid a luxury campaign finish, perfect studio symmetry, professional model energy, or over-retouched polish; keep the result commercially usable but recognizably human and informal.",
    ]


def _style_creative_brief(*, preset: Optional[str] = None) -> str:
    preset_hint = str(preset or "").strip().lower()
    if preset_hint == "premium_lifestyle":
        return (
            "Create a Brazilian fashion photograph with authentic local cues, restrained premium-editorial warmth, "
            "and commercially readable composition. Avoid stock-photo cheerfulness, exaggerated friendliness, or hero props "
            "that compete with the garment."
        )
    if preset_hint == "ugc_real_br":
        return (
            "Create a Brazilian fashion photograph that feels like believable creator-led social-commerce content in a genuine local setting, "
            "with expressive but believable body language, honest skin texture, ordinary phone-camera imperfection, and strong garment readability. "
            "Allow boutique, store, mirror, hallway, apartment, or everyday creator-context cues when they fit the garment. "
            "Avoid showroom perfection, beauty-filter smoothness, sterile campaign emptiness, artificial glamour lighting, or clutter that competes with the garment."
        )
    if preset_hint == "marketplace_lifestyle":
        return (
            "Create a Brazilian fashion photograph with authentic local cues, polished everyday realism, and clean commercial readability. "
            "Avoid stock-photo energy, forced gestures, or props that pull attention away from the garment."
        )
    return (
        "Create a Brazilian fashion photograph with authentic local cues, calm commercial clarity, and restrained realism. "
        "Avoid generic template energy or scene props that compete with the garment."
    )


def _closed_neckline_guard(structural_contract: Optional[dict[str, Any]]) -> str:
    contract = structural_contract or {}
    front = str(contract.get("front_opening", "") or "").strip().lower()
    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    if front != "closed":
        return ""
    if subtype in {"pullover", "t_shirt", "blouse", "dress", "jacket", "blazer", "standard_cardigan", "other", "unknown"}:
        return (
            "Do not introduce any visible undershirt, layered neckline, or contrasting inner collar; "
            "the garment neckline itself must remain the only visible neckline element."
        )
    return ""


def _specialized_structure_guards(
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]] = None,
) -> list[str]:
    contract = structural_contract or {}
    set_info = set_detection or {}

    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    front = str(contract.get("front_opening", "") or "").strip().lower()
    lock_mode = str(set_info.get("set_lock_mode", "off") or "off").strip().lower()
    must_include_labels = get_set_member_labels(
        set_info,
        include_policies={"must_include"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )
    must_include_keys = get_set_member_keys(
        set_info,
        include_policies={"must_include"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )

    guards: list[str] = []
    if subtype == "ruana_wrap":
        guards.append("keep this as an open ruana-style wrap and not a closed poncho, sweater, or pullover body")
    if sleeve == "cape_like":
        guards.append(
            "do not invent separate sewn sleeves, long vertical sleeve slits, or tailored armholes; arm coverage must come from the continuous draped side panel"
        )
    if lock_mode != "off" and must_include_labels:
        guards.append(
            "preserve coordinated set members as distinct product pieces with matching textile DNA, not as unrelated styling or fused garment parts"
        )
    if "scarf" in must_include_keys:
        guards.append("preserve the matching scarf as part of the same coordinated knit set with the same stripe order, yarn tones, and stitch texture")
    return guards


def build_structure_guard_clauses(
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]] = None,
) -> list[str]:
    clauses = _collect_lock_clauses(structural_contract)
    clauses.extend(_specialized_structure_guards(structural_contract, set_detection=set_detection))
    return list(dict.fromkeys([clause.strip() for clause in clauses if clause and clause.strip()]))


def _collect_lock_clauses(structural_contract: Optional[dict[str, Any]]) -> list[str]:
    """Guards prioritários (máx 5) — confia na imagem para o resto.

    Antes havia 14+ locks granulares que diluíam o sinal visual.
    Agora: 1 anchor de identidade + até 4 guards de drift comprovado.
    """
    contract = structural_contract or {}
    locks = [
        "preserve the exact garment identity, shape, and texture visible in the references",
    ]

    # Comprimento: drift mais frequente — o Nano tende a encurtar/alongar.
    length = str(contract.get("garment_length", "") or "").strip().lower()
    if length in _LENGTH_PHRASES:
        locks.append(f"maintain {_LENGTH_PHRASES[length]} as shown in the reference")

    # Abertura frontal: confusão open/closed é segundo drift mais comum.
    front = str(contract.get("front_opening", "") or "").strip().lower()
    if front == "open":
        locks.append("keep the front visibly open")
    elif front == "closed":
        locks.append("keep the front closure intact")

    # must_keep: até 2 anchors visuais do triage (ex: continuous edge, back panel)
    must_keep = [str(item).strip() for item in (contract.get("must_keep", []) or []) if str(item).strip()]
    if must_keep:
        locks.append("preserve: " + ", ".join(must_keep[:2]))

    return locks


def build_structural_hint(structural_contract: Optional[dict[str, Any]]) -> Optional[str]:
    """Frase curta em prosa descrevendo a identidade da peça.

    Produz linguagem natural ('a draped ruana wrap with three-quarter sleeves at hip length')
    para orientar o Nano Banana sem jargão técnico.
    """
    contract = structural_contract or {}
    if not contract.get("enabled"):
        return None

    subtype = str(contract.get("garment_subtype", "") or "").strip().lower().replace("_", " ")
    volume = str(contract.get("silhouette_volume", "") or "").strip().lower()
    sleeve_len = str(contract.get("sleeve_length", "") or "").strip().lower().replace("_", "-")
    length = str(contract.get("garment_length", "") or "").strip().lower()

    if not subtype or subtype == "unknown":
        return None

    # "a [volume] [subtype] with [sleeve] sleeves at [length] length"
    phrase = "a "
    if volume and volume != "unknown":
        phrase += f"{volume} "
    phrase += subtype
    if sleeve_len and sleeve_len not in ("unknown", "sleeveless"):
        phrase += f" with {sleeve_len} sleeves"
    elif sleeve_len == "sleeveless":
        phrase += ", sleeveless"
    if length in _LENGTH_PHRASES:
        phrase += f" at {_LENGTH_PHRASES[length]}"

    return phrase


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

    from agent_runtime.normalize_user_intent import normalize_user_intent
    extra_direction = (user_prompt or "").strip()
    if extra_direction:
        intent = normalize_user_intent(extra_direction)
        sentences.append(f"Additional commercial direction: {intent['normalized']}.")

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

    from agent_runtime.normalize_user_intent import normalize_user_intent
    extra_direction = (user_prompt or "").strip()
    if extra_direction:
        intent = normalize_user_intent(extra_direction)
        sentences.append(f"Additional commercial direction: {intent['normalized']}.")

    return " ".join(sentence.strip() for sentence in sentences if sentence.strip())


def build_art_direction_two_pass_edit_prompt(
    structural_contract: Optional[dict[str, Any]],
    *,
    art_direction: dict[str, Any],
    set_detection: Optional[dict[str, Any]] = None,
    garment_material: str = "garment fabric",
    garment_color: str = "the garment colors and yarn tones",
    reference_guard_strength: str = "standard",
    reference_usage_rules: Optional[list[str]] = None,
    pose_flex_guideline: Optional[str] = None,
    user_prompt: Optional[str] = None,
    image_analysis: Optional[str] = None,
) -> str:
    locks = build_structure_guard_clauses(structural_contract, set_detection=set_detection)

    # Se image_analysis descreve um padrão específico (listras, chevron, etc.),
    # gera um lock explícito de direção de padrão para substituir o genérico.
    _pattern_lock_sentence = ""
    _ia = str(image_analysis or "").strip()
    _pattern_keywords = ("stripe", "chevron", "diagonal", "radiating", "concentric", "plaid", "grid", "check", "argyle", "listras", "listra", "xadrez")
    if _ia and any(w in _ia.lower() for w in _pattern_keywords):
        _ia_truncated = _ia[:250].rstrip(",. ")
        _pattern_lock_sentence = (
            f"CRITICAL — preserve the exact surface pattern geometry from the references: {_ia_truncated}. "
            "Do not reinterpret stripe direction, pattern angle, or pattern scale. "
            "If the pattern appears diagonal or chevron in the references, it must remain diagonal or chevron in the output."
        )

    casting = art_direction.get("casting_profile", {}) or {}
    scene = art_direction.get("scene", {}) or {}
    pose = art_direction.get("pose", {}) or {}
    camera = art_direction.get("camera", {}) or {}
    lighting = art_direction.get("lighting", {}) or {}
    styling = art_direction.get("styling", {}) or {}
    action_context = str(art_direction.get("action_context", "") or "").strip()
    ugc_entropy_profile = art_direction.get("ugc_entropy_profile") if isinstance(art_direction.get("ugc_entropy_profile"), dict) else {}

    identity_sentence = str(casting.get("identity_sentence", "") or "").strip()
    if not identity_sentence:
        identity_sentence = "a clearly different adult Brazilian woman with distinct face, skin tone, and hair"

    phenotype_sentence = ", ".join(
        [
            part for part in [
                "Brazilian woman",
                str(casting.get("skin", "") or "").strip(),
                str(casting.get("face_structure", "") or "").strip(),
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

    request_meta = art_direction.get("request", {}) if isinstance(art_direction.get("request"), dict) else {}
    preset_hint = str(request_meta.get("preset", "") or "").strip().lower()
    directive_hints_meta = request_meta.get("directive_hints", {}) if isinstance(request_meta.get("directive_hints"), dict) else {}
    angle_directive = str(directive_hints_meta.get("angle_directive", "") or "").strip()
    look_contract_meta = (
        request_meta.get("look_contract")
        if isinstance(request_meta.get("look_contract"), dict)
        else {}
    )
    _lc_active = bool(look_contract_meta) and float(look_contract_meta.get("confidence", 0) or 0) > 0.5
    scene_brief = _scene_creative_brief(
        scene,
        preset=preset_hint,
    )
    pose_brief = _pose_creative_brief(
        structural_contract,
        pose=pose,
        set_detection=set_detection,
        preset=preset_hint,
    )
    camera_device = str(camera.get("device", "") or "Canon R6").strip()
    camera_lens = str(camera.get("lens", "") or "50mm lens").strip()
    lighting_description = str(lighting.get("description", "") or "soft mixed daylight").strip()

    style_clause = _style_creative_brief(preset=preset_hint)
    scene_clause = scene_brief
    ugc_capture_mode = str(ugc_entropy_profile.get("capture_mode", "") or "").strip().lower()
    model_clause = (
        f"The model should read as {phenotype_sentence}, with a {visual_label} presence, around {age_years} years old, "
        "with a clearly new identity created for this job."
    )
    if preset_hint == "ugc_real_br":
        model_clause += " She should feel like a real Brazilian woman in a creator or influencer moment, not like professional fashion talent on a campaign set."
    camera_clause = (
        f"The photograph should feel like it was captured on {camera_device} with a {camera_lens}, "
        "with believable depth, natural handheld realism, and subtle real-world camera imperfections."
    )
    if preset_hint == "ugc_real_br":
        camera_clause += " Prefer ordinary phone-camera optics, flatter everyday perspective, and imperfect casual capture timing over luxury photo aesthetics."
        if ugc_capture_mode == "mirror_tryon_selfie":
            camera_clause += " Let the phone and mirror relationship feel believable, with selfie-style perspective and slightly imperfect alignment."
        elif ugc_capture_mode == "creator_boutique_story":
            camera_clause += " Favor the sense of a boutique story or reel frame, with chest-height phone framing and quick creator timing."
        elif ugc_capture_mode == "review_flash_story":
            camera_clause += " Favor quick review-photo timing with believable on-phone flash flatness instead of professional flash shaping."
        elif ugc_capture_mode == "walkby_phone_story":
            camera_clause += " Favor a quick moving phone capture with small timing imperfections instead of a leveled fashion-walk frame."
    lighting_clause = (
        f"Use {lighting_description}, with believable mixed color temperature and imperfect real-world ambient bounce."
    )
    texture_clause = (
        f"Render the garment with macro-accurate {garment_material}, correct fabric weight, consistent stitch definition, "
        f"and realistic light absorption across {garment_color}."
    )
    dynamic_rules = list(reference_usage_rules or [])
    base_rules = list(_REFERENCE_USAGE_RULES_BASE)
    if str(reference_guard_strength).strip().lower() in {"strict", "high"}:
        base_rules.extend(_REFERENCE_USAGE_RULES_STRICT)
    if str(reference_guard_strength).strip().lower() == "high":
        base_rules.extend(_REFERENCE_USAGE_RULES_HIGH_GUARD)
    combined_reference_rules = list(dict.fromkeys([rule.strip() for rule in (base_rules + dynamic_rules) if rule and rule.strip()]))
    reference_policy_clause = " ".join(combined_reference_rules)
    neckline_guard = _closed_neckline_guard(structural_contract)
    pose_flex_clause = (
        str(pose_flex_guideline).strip()
        if str(pose_flex_guideline or "").strip()
        else "Allow a naturally varied pose while preserving garment silhouette and readability."
    )
    action_context_clause = _action_context_brief(action_context)
    ugc_entropy_clauses = _ugc_entropy_clauses(ugc_entropy_profile)

    sentences = [
        angle_directive,  # instrução de ângulo/crop obrigatória — vazia se não houver slot directive
        (
            "IDENTITY REPLACEMENT: The person in the base image is a PLACEHOLDER and must be fully replaced. "
            "Do not preserve ANY facial features, skin tone, hair color, hair style, body type, or age "
            "from the base image person OR from the reference images. Create a completely new person."
        ),
        "Keep the garment exactly the same: " + ", ".join(locks) + ".",
        _pattern_lock_sentence,  # lock específico de padrão — vazio se padrão não detectado
        f"Replace the model with {identity_sentence}.",
        reference_policy_clause,
        "Before rendering, internally plan the composition around a locked garment object. Only the model identity, pose, camera, and environment may change.",
        pose_flex_clause,
        action_context_clause,
        "Do not follow a fixed pose template or a fixed scene template; invent both around the garment.",
        pose_brief,
        "Create a fresh pose and a fresh scene that fit the garment's natural drape instead of reshaping the garment to fit the pose.",
        difference_instruction,
        (
            "This casting should not resemble recent outputs characterized by "
            + ", ".join(recent_avoid)
            + "."
        ) if recent_avoid else "",
        neckline_guard,
        f"Change the inner top to a {str(styling.get('innerwear', '') or 'clean white crew-neck tee')}." if not neckline_guard else "",
        # look_contract.bottom_style tem prioridade sobre styling profile aleatório quando confiança > 0.5
        (
            "Change the lower-body styling to "
            + (str(look_contract_meta.get("bottom_style") or "").strip() or str(styling.get("bottom", "") or "clean commercial separates"))
            + "."
        ) if not neckline_guard else "",
        # forbidden_bottoms: guard explícito contra looks incoerentes com a peça
        (
            "NEVER use these lower-body types for this garment (styling incoherence): "
            + ", ".join(str(x).strip() for x in (look_contract_meta.get("forbidden_bottoms") or []) if str(x).strip())
            + "."
        ) if _lc_active and look_contract_meta.get("forbidden_bottoms") else "",
        style_clause,
        scene_clause,
        model_clause,
        camera_clause,
        lighting_clause,
        *ugc_entropy_clauses,
        texture_clause,
        "Keep the image highly photorealistic with natural skin texture, visible pores, mild facial asymmetry, and realistic body proportions.",
    ]

    from agent_runtime.normalize_user_intent import normalize_user_intent
    extra_direction = (user_prompt or "").strip()
    if extra_direction:
        intent = normalize_user_intent(extra_direction)
        sentences.append(f"Additional commercial direction: {intent['normalized']}.")

    return " ".join(sentence.strip() for sentence in sentences if sentence.strip())
