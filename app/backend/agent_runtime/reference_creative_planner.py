from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from google.genai import types

from agent_runtime.fidelity import (
    build_structure_guard_clauses,
    build_structural_hint,
)
from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.capture_soul import get_capture_soul
from agent_runtime.parser import _decode_agent_response, try_repair_truncated_json
from agent_runtime.pose_soul import get_pose_soul
from agent_runtime.scene_soul import get_scene_soul
from agent_runtime.styling_direction import (
    STYLING_DIRECTION_SCHEMA,
    derive_styling_context,
    normalize_styling_direction_payload,
)
from agent_runtime.model_soul import get_model_soul
from agent_runtime.structural import get_set_member_labels


_CASTING_SCHEMA = {
    "type": "object",
    "required": [
        "profile_hint",
        "age_band",
        "face_geometry",
        "eye_logic",
        "skin_read",
        "face_hair_presence",
        "hair_logic",
        "body_frame",
        "body_read",
        "expression_read",
        "makeup_read",
    ],
    "properties": {
        "profile_hint": {"type": "string"},
        "age_band": {"type": "string"},
        "face_geometry": {"type": "string"},
        "eye_logic": {"type": "string"},
        "skin_read": {"type": "string"},
        "face_hair_presence": {"type": "string"},
        "hair_logic": {"type": "string"},
        "body_frame": {"type": "string"},
        "body_read": {"type": "string"},
        "expression_read": {"type": "string"},
        "makeup_read": {"type": "string"},
    },
}

_SCENE_SCHEMA = {
    "type": "object",
    "required": ["setting", "surface_cues", "lighting_logic"],
    "properties": {
        "setting": {"type": "string"},
        "surface_cues": {"type": "string"},
        "lighting_logic": {"type": "string"},
    },
}

_POSE_SCHEMA = {
    "type": "object",
    "required": ["stance", "arm_logic", "garment_visibility"],
    "properties": {
        "stance": {"type": "string"},
        "arm_logic": {"type": "string"},
        "garment_visibility": {"type": "string"},
    },
}

_CAPTURE_SCHEMA = {
    "type": "object",
    "required": ["framing", "angle", "crop_logic", "lens_feel"],
    "properties": {
        "framing": {"type": "string"},
        "angle": {"type": "string"},
        "crop_logic": {"type": "string"},
        "lens_feel": {"type": "string"},
    },
}

REFERENCE_CREATIVE_PLANNER_SCHEMA = {
    "type": "object",
    "required": [
        "casting_direction",
        "styling_direction",
        "scene_direction",
        "pose_direction",
        "capture_direction",
    ],
    "properties": {
        "casting_direction": _CASTING_SCHEMA,
        "styling_direction": STYLING_DIRECTION_SCHEMA,
        "scene_direction": _SCENE_SCHEMA,
        "pose_direction": _POSE_SCHEMA,
        "capture_direction": _CAPTURE_SCHEMA,
    },
}


@dataclass(frozen=True)
class ReferenceCreativePlan:
    garment_identity: dict[str, Any]
    casting_direction: dict[str, Any]
    styling_direction: dict[str, Any]
    scene_direction: dict[str, Any]
    pose_direction: dict[str, Any]
    capture_direction: dict[str, Any]
    base_scene_prompt: str
    stage2_scene_context: str
    summary: dict[str, str]
    fallback_applied: bool = False
    debug_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any, *, limit: int = 220) -> str:
    text = " ".join(str(value or "").strip().split())
    if len(text) <= limit:
        return text

    min_boundary = max(int(limit * 0.6), 1)
    strong_cutoffs = [
        text.rfind(". ", 0, limit + 1) + 1,
        text.rfind("; ", 0, limit + 1) + 1,
    ]
    clause_cutoff = text.rfind(", ", 0, limit + 1) + 1
    word_cutoff = text.rfind(" ", 0, limit + 1)
    strong_candidates = [cut for cut in strong_cutoffs if cut >= min_boundary]
    if strong_candidates:
        return text[: max(strong_candidates)].rstrip(" ,;:-")
    if clause_cutoff >= min_boundary:
        return text[:clause_cutoff].rstrip(" ,;:-")
    if word_cutoff >= min_boundary:
        return text[:word_cutoff].rstrip(" ,;:-")
    return text[:limit].rstrip(" ,;:-")


def _sentence_text(value: Any, *, limit: int = 220) -> str:
    text = _clean_text(value, limit=limit).rstrip(" .;,:-")
    if not text:
        return ""
    return text + "."


def _normalize_compact_object(
    payload: Optional[dict[str, Any]],
    *,
    defaults: dict[str, str],
) -> dict[str, str]:
    raw = payload if isinstance(payload, dict) else {}
    normalized: dict[str, str] = {}
    for key, default in defaults.items():
        normalized[key] = _clean_text(raw.get(key), limit=220) or default
    return normalized


def _build_default_styling_direction(styling_context: dict[str, Any]) -> dict[str, Any]:
    topology = str(styling_context.get("inferred_topology") or "single_piece")
    hero_family = str(styling_context.get("inferred_hero_family") or "unclear")
    components = list(styling_context.get("inferred_components") or [])

    completion_slots: list[str]
    primary_completion = "none"
    footwear_direction = (
        "choose one discreet, mode-aligned footwear family only if it remains visible in frame; "
        "do not default automatically to ankle boots or the same safe neutral shoe"
    )

    if topology == "coordinated_set":
        completion_slots = ["footwear"]
    elif hero_family == "top_layer":
        completion_slots = ["lower_body", "footwear"]
        primary_completion = (
            "choose one quiet lower-body completion family that supports the hero garment without competing with it; "
            "do not fall back to the same dark tailored trouser formula"
        )
    elif hero_family == "lower_body":
        completion_slots = ["top_layer", "footwear"]
        primary_completion = (
            "choose one quiet upper-body completion family that keeps the lower-body hero visible "
            "without reusing the same safe styling formula"
        )
    elif hero_family == "one_piece":
        completion_slots = ["footwear"]
        primary_completion = "none"
    else:
        completion_slots = []

    return {
        "product_topology": topology,
        "hero_family": hero_family,
        "hero_components": components,
        "completion_slots": completion_slots,
        "completion_strategy": (
            "Keep the look commercially complete without competing with the hero garment, "
            "but make a specific completion choice rather than a median catalog default."
        ),
        "primary_completion": primary_completion,
        "secondary_completion": "none",
        "footwear_direction": footwear_direction,
        "accessories_optional": "none",
        "outer_layer_optional": "none",
        "finish_logic": "Let finishing choices stay subordinate to the hero garment and the active mode.",
        "direction_summary": (
            "Resolve only the visibly necessary completion around the hero garment, with a distinct but commercially quiet choice."
        ),
        "confidence": 0.55,
    }


def _build_default_scene_direction(mode_id: str) -> dict[str, str]:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return {
            "setting": "neutral studio backdrop only",
            "surface_cues": "clean ice-white or light-grey sweep with no location cues",
            "lighting_logic": "soft even studio light that keeps the product fully legible",
        }
    if normalized == "lifestyle":
        return {
            "setting": "socially alive Brazilian environment with lived context",
            "surface_cues": "real-use materials and background depth that support activity",
            "lighting_logic": "commercially believable ambient light with natural scene continuity",
        }
    if normalized == "editorial_commercial":
        return {
            "setting": "authored Brazilian architectural setting",
            "surface_cues": "strong material contrast and deliberate spatial geometry",
            "lighting_logic": "controlled directional light that adds authority without burying the garment",
        }
    return {
        "setting": "ordinary Brazilian real-life setting",
        "surface_cues": "modest lived-in surfaces with believable daily-use texture",
        "lighting_logic": "observational natural light that feels real and unforced",
    }


def _mode_aesthetic_context(mode_id: str) -> str:
    """Traduz o mode_id em contexto visual denso para o modelo de imagem.
    Nunca passa o nome do mode — passa o que ele significa visualmente.
    """
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return (
            "The image aesthetic is clean and product-forward: neutral studio light, "
            "white or light-grey backdrop, no environmental storytelling. "
            "The woman's presence is composed and commercially legible — she serves the garment read, not a narrative."
        )
    if normalized == "lifestyle":
        return (
            "The image aesthetic is socially alive and situationally grounded: "
            "a real Brazilian environment with ambient light, lived-in surfaces, and activity context. "
            "The woman belongs inside the scene — she is mid-something, not posed for the camera."
        )
    if normalized == "editorial_commercial":
        return (
            "The image aesthetic is authored and visually deliberate: "
            "strong architectural setting, controlled directional light, "
            "and a woman whose presence commands the frame. "
            "Every element is a choice — nothing is accidental or unresolved."
        )
    # natural / default
    return (
        "The image aesthetic is observational and real: "
        "an ordinary Brazilian everyday setting with natural unforced light and modest lived-in surfaces. "
        "The woman reads as encountered, not produced — her presence is unconsidered and believable."
    )


def _build_default_pose_direction(mode_id: str) -> dict[str, str]:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return {
            "stance": (
                "commercial standing presentation with a specific body decision such as a subtle cross-step, offset planted stance, "
                "or asymmetrical weight shift; do not default to the same hand-on-hip catalog pose"
            ),
            "arm_logic": (
                "choose one commercially useful arm solution that keeps the garment open to view, "
                "without repeating the same waist-touch or mirror-symmetry formula"
            ),
            "garment_visibility": "keep full silhouette, length, and front read clear",
        }
    if normalized == "lifestyle":
        return {
            "stance": "mid-activity body direction with believable movement",
            "arm_logic": "gesture shaped by the action rather than by posing",
            "garment_visibility": "keep the hero garment readable while the body remains active",
        }
    if normalized == "editorial_commercial":
        return {
            "stance": "authored asymmetrical stance with deliberate body placement",
            "arm_logic": "intentional arm geometry that sharpens the silhouette",
            "garment_visibility": "preserve product readability while keeping the body fashion-aware",
        }
    return {
        "stance": "relaxed lived-in stance with natural asymmetry",
        "arm_logic": "small everyday hand behavior that does not look posed",
        "garment_visibility": "keep the hero garment visible without turning the body into a catalog pose",
    }


def _build_default_capture_direction(mode_id: str) -> dict[str, str]:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return {
            "framing": (
                "clean commercial framing chosen specifically for the garment, ranging from full-body to medium-full rather than one fixed crop"
            ),
            "angle": (
                "subtle commercial body rotation between near-frontal and clean three-quarter, not always the same eye-level centered relation"
            ),
            "crop_logic": "show the garment fully without portrait-first cropping, while allowing slight variation in subject placement",
            "lens_feel": "clean neutral fashion perspective",
        }
    if normalized == "lifestyle":
        return {
            "framing": "participatory medium-wide framing",
            "angle": "fresh three-quarter camera relation that follows the activity",
            "crop_logic": "keep body, garment, and enough environment alive together",
            "lens_feel": "socially present camera feel",
        }
    if normalized == "editorial_commercial":
        return {
            "framing": "fashion-authored medium or medium-full framing",
            "angle": "deliberate three-quarter camera relation",
            "crop_logic": "preserve garment legibility while letting architecture participate",
            "lens_feel": "controlled fashion perspective with compositional authority",
        }
    return {
        "framing": "observational medium-wide framing",
        "angle": "fresh three-quarter view with visible body rotation",
        "crop_logic": "keep body and setting alive without collapsing into portrait logic",
        "lens_feel": "human-scaled observational perspective",
    }


def _build_default_casting_direction(mode_id: str) -> dict[str, str]:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return {
            "profile_hint": (
                "a specifically cast adult Brazilian woman with a concrete facial signature chosen for this garment; "
                "do not default to the same median polished catalog archetype"
            ),
            "age_band": "adult, with the age presence chosen deliberately for the garment rather than defaulting to late 20s/early 30s every time",
            "face_geometry": "choose one concrete facial geometry with clear brow, eye, nose, mouth, and jaw structure; avoid generic beauty-face shorthand",
            "eye_logic": "eyes must feel alive, aligned, and commercially present — never vacant, glassy, or divergent",
            "skin_read": "natural commercial skin with believable undertone and microtexture, not waxed or over-smoothed",
            "face_hair_presence": (
                "commit to one memorable facial and hair logic with visible specificity; "
                "do not recycle the same sleek center-part, same smile, or same catalog beauty shorthand"
            ),
            "hair_logic": "choose a specific real hair behavior, density, length, and parting that supports the face rather than repeating the same polished fall",
            "body_frame": "describe a believable frame and proportion read that makes the garment sit naturally on the body",
            "body_read": "her posture communicates ease with the garment and commercial clarity without collapsing into the same repeated showroom body language",
            "expression_read": "direct and shopper-aware, but choose one specific expression register rather than defaulting to the same open smile or drained blank stare",
            "makeup_read": "visible makeup must stay believable and commercially light, never mask-like or over-airbrushed",
        }
    if normalized == "editorial_commercial":
        return {
            "profile_hint": "a visually commanding adult Brazilian woman — her presence reads immediately at thumbnail scale; she was cast because of something specific about her face, not despite it",
            "age_band": "late 20s to mid 30s",
            "face_geometry": "facial geometry with clear editorial structure and distinct brow-eye-mouth architecture",
            "eye_logic": "eyes focused and alive, with intentional directional energy",
            "skin_read": "real skin with controlled polish and visible natural texture",
            "face_hair_presence": "her facial geometry is the reason she was cast — name what that quality is; her hair styling is a deliberate creative decision, not a default fall",
            "hair_logic": "hair styling chosen as part of the authored image, with explicit shape and movement logic",
            "body_frame": "body frame with clear line, proportion, and silhouette authority",
            "body_read": "she occupies her space with intention — her posture is authored, the garment is something she selected",
            "expression_read": "controlled and in command — not cold, but self-aware; the camera comes to her, not the other way around",
            "makeup_read": "visible makeup should support authority and precision without becoming mask-like",
        }
    if normalized == "lifestyle":
        return {
            "profile_hint": "a socially alive adult Brazilian woman — her presence has individual personality, not just physical correctness; she gives the impression of being mid-something",
            "age_band": "mid 20s to early 30s",
            "face_geometry": "clear face geometry with memorable asymmetry and lived-in specificity",
            "eye_logic": "eyes alert and alive inside the action, never vacant or beauty-portrait frozen",
            "skin_read": "real skin with daylight credibility, natural texture, and lived tone variation",
            "face_hair_presence": "her face communicates a point of view — something in her features or expression says she has opinions; her hair moves with her rather than staying composed",
            "hair_logic": "hair behavior must feel lived, mobile, and plausible for the scene rather than arranged for portrait flattery",
            "body_frame": "body/frame read should feel plausible for someone actually inhabiting the activity",
            "body_read": "she reads as someone in the middle of something — self-directed, not waiting to be photographed",
            "expression_read": "open and forward-moving — her energy goes toward something in her world, the camera catches her rather than she poses for it",
            "makeup_read": "visible makeup should read as personal daily grooming, not shoot styling",
        }
    return {
        "profile_hint": "a naturally attractive adult Brazilian woman — her beauty reads as real and encountered, not aspirational or produced; she could be someone you know",
        "age_band": "mid 20s to early 30s",
        "face_geometry": "specific face geometry with believable asymmetry and non-generic proportions",
        "eye_logic": "eyes must look attentive and alive in the world, never deadened or artificially centered",
        "skin_read": "skin should preserve natural texture, undertone, and slight unevenness that confirms reality",
        "face_hair_presence": "her face and hair carry the minor imperfections that confirm she is real — nothing has been corrected into artificiality; her styling is the absence of styling",
        "hair_logic": "hair should feel minimally handled, naturally falling, and not arranged for beauty-portrait perfection",
        "body_frame": "a believable body/frame read that helps the garment sit naturally rather than mannequin-neatly",
        "body_read": "her body language is unconsidered — she is not presenting herself to anyone, she is simply present in the frame",
        "expression_read": "she is not performing for the camera — her attention is somewhere else, her face is at natural rest",
        "makeup_read": "visible makeup should stay minimal and plausibly real-life",
    }


def _render_styling_summary(styling_direction: dict[str, Any], *, mode_styling_mandate: str) -> str:
    direction_summary = _clean_text(styling_direction.get("direction_summary"), limit=220)
    completion_strategy = _clean_text(styling_direction.get("completion_strategy"), limit=220)
    primary_completion = _clean_text(styling_direction.get("primary_completion"), limit=140)
    footwear_direction = _clean_text(styling_direction.get("footwear_direction"), limit=140)
    accessories_optional = _clean_text(styling_direction.get("accessories_optional"), limit=140)

    parts = [direction_summary, completion_strategy]
    if primary_completion and primary_completion != "none":
        parts.append(f"Primary completion: {primary_completion}.")
    if footwear_direction and footwear_direction != "none":
        parts.append(f"Footwear: {footwear_direction}.")
    if accessories_optional:
        parts.append(f"Accessories: {accessories_optional}.")
    if mode_styling_mandate:
        parts.append(f"Mode styling mandate: {mode_styling_mandate}.")
    return " ".join(part.strip() for part in parts if part and part.strip())


def _build_summary(
    *,
    mode_id: str,
    casting_direction: dict[str, Any],
    styling_direction: dict[str, Any],
    scene_direction: dict[str, Any],
    pose_direction: dict[str, Any],
    capture_direction: dict[str, Any],
    fallback_applied: bool,
) -> dict[str, str]:
    capture_summary = " | ".join(
        item for item in [
            _clean_text(capture_direction.get("framing"), limit=90),
            _clean_text(capture_direction.get("angle"), limit=90),
        ]
        if item
    )
    return {
        "creative_source": "reference_planner",
        "base_strategy": "creative_base_then_garment_replacement",
        "replacement_strategy": "lock_person_replace_garment",
        "mode_id": str(mode_id or "natural"),
        "model_direction": _clean_text(casting_direction.get("profile_hint"), limit=160),
        "scene_direction": _clean_text(scene_direction.get("setting"), limit=160),
        "pose_direction": _clean_text(pose_direction.get("stance"), limit=160),
        "capture_direction": capture_summary,
        "styling_direction": _clean_text(styling_direction.get("direction_summary"), limit=200),
        "fallback_applied": "true" if fallback_applied else "false",
    }


def _build_base_scene_prompt(
    *,
    mode_id: str,
    garment_identity: dict[str, Any],
    casting_direction: dict[str, Any],
    styling_direction: dict[str, Any],
    scene_direction: dict[str, Any],
    pose_direction: dict[str, Any],
    capture_direction: dict[str, Any],
    styling_context: dict[str, Any],
) -> str:
    structural_hint = _clean_text(garment_identity.get("structural_hint"), limit=200)
    garment_hint = _clean_text(garment_identity.get("garment_hint"), limit=160)
    structure_guards = list(garment_identity.get("structure_guards") or [])
    required_set_members = list(garment_identity.get("required_set_members") or [])
    mode_styling_mandate = _clean_text(styling_context.get("mode_styling_mandate"), limit=200)

    parts = [
        _mode_aesthetic_context(mode_id),
    ]
    if structural_hint:
        parts.append(f"Structural garment identity: {structural_hint}.")
    elif garment_hint:
        parts.append(f"Garment identity: {garment_hint}.")
    if structure_guards:
        parts.append("The garment worn must show these structural characteristics clearly: " + "; ".join(structure_guards) + ".")
    if required_set_members:
        parts.append(
            "She is wearing a coordinated set — these separate pieces must also appear: "
            + ", ".join(required_set_members)
            + "."
        )

    parts.append(
        "This woman is visually specific and individually cast for this garment — "
        "not a placeholder face, not a generic type. "
        "Her physical description in the prompt must read as a real individual choice, not a category."
    )
    parts.append(
        "Casting direction: "
        + " ".join(
            sentence
            for sentence in [
                _clean_text(casting_direction.get("profile_hint"), limit=200),
                _clean_text(casting_direction.get("age_band"), limit=100),
                _clean_text(casting_direction.get("face_geometry"), limit=180),
                _clean_text(casting_direction.get("eye_logic"), limit=180),
                _clean_text(casting_direction.get("skin_read"), limit=180),
                _clean_text(casting_direction.get("face_hair_presence"), limit=180),
                _clean_text(casting_direction.get("hair_logic"), limit=180),
                _clean_text(casting_direction.get("body_frame"), limit=180),
                _clean_text(casting_direction.get("body_read"), limit=180),
                _clean_text(casting_direction.get("expression_read"), limit=180),
                _clean_text(casting_direction.get("makeup_read"), limit=140),
            ]
            if sentence
        )
        + "."
    )
    parts.append(f"Styling direction: {_render_styling_summary(styling_direction, mode_styling_mandate=mode_styling_mandate)}")
    parts.append(
        "Scene direction: "
        + " ".join(
            sentence
            for sentence in [
                _clean_text(scene_direction.get("setting"), limit=200),
                _clean_text(scene_direction.get("surface_cues"), limit=200),
                _clean_text(scene_direction.get("lighting_logic"), limit=200),
            ]
            if sentence
        )
        + "."
    )
    parts.append(
        "Pose direction: "
        + " ".join(
            sentence
            for sentence in [
                _clean_text(pose_direction.get("stance"), limit=200),
                _clean_text(pose_direction.get("arm_logic"), limit=200),
                _clean_text(pose_direction.get("garment_visibility"), limit=200),
            ]
            if sentence
        )
        + "."
    )
    parts.append(
        "Capture direction: "
        + " ".join(
            sentence
            for sentence in [
                _clean_text(capture_direction.get("framing"), limit=200),
                _clean_text(capture_direction.get("angle"), limit=200),
                _clean_text(capture_direction.get("crop_logic"), limit=200),
                _clean_text(capture_direction.get("lens_feel"), limit=200),
            ]
            if sentence
        )
        + "."
    )
    parts.append(
        "Do not replicate any person, pose, background, or framing visible in the reference images. "
        "The references exist only to establish the garment's physical form."
    )

    return " ".join(part.strip() for part in parts if part and part.strip())


def _build_stage2_scene_context(
    *,
    mode_id: str,
    casting_direction: dict[str, Any],
    styling_direction: dict[str, Any],
    scene_direction: dict[str, Any],
    pose_direction: dict[str, Any],
    capture_direction: dict[str, Any],
) -> str:
    limit = 700
    parts = [
        f"Preserve the base image's {str(mode_id or 'natural').strip().lower()} creative intent.",
        "Presence: " + _sentence_text(casting_direction.get("profile_hint"), limit=120),
        "Scene: " + _sentence_text(scene_direction.get("setting"), limit=150),
        "Lighting: " + _sentence_text(scene_direction.get("lighting_logic"), limit=150),
        "Pose: " + _sentence_text(pose_direction.get("stance"), limit=140),
        "Capture: " + _sentence_text(capture_direction.get("framing"), limit=120),
        "Angle: " + _sentence_text(capture_direction.get("angle"), limit=120),
    ]
    optional_parts = [
        "Expression: " + _sentence_text(casting_direction.get("expression_read"), limit=120),
        "Arms: " + _sentence_text(pose_direction.get("arm_logic"), limit=130),
    ]

    chosen = [part for part in parts if part and not part.endswith(": .")]
    current = " ".join(chosen)
    for candidate in optional_parts:
        clean_candidate = candidate.strip()
        if not clean_candidate or clean_candidate.endswith(": ."):
            continue
        proposal = f"{current} {clean_candidate}".strip()
        if len(proposal) <= limit:
            chosen.append(clean_candidate)
            current = proposal

    return current


def build_reference_creative_plan_fallback(
    *,
    mode_id: str,
    garment_hint: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
    image_analysis: Optional[str],
    styling_context: dict[str, Any],
) -> ReferenceCreativePlan:
    garment_identity = {
        "garment_hint": _clean_text(garment_hint, limit=120),
        "image_analysis": _clean_text(image_analysis, limit=320),
        "structural_hint": build_structural_hint(structural_contract),
        "structure_guards": build_structure_guard_clauses(structural_contract, set_detection=set_detection),
        "required_set_members": get_set_member_labels(
            set_detection or {},
            include_policies={"must_include"},
            member_classes={"garment", "coordinated_accessory"},
            active_only=True,
            exclude_primary_piece=True,
        ),
    }
    casting_direction = _build_default_casting_direction(mode_id)
    styling_direction = normalize_styling_direction_payload(
        _build_default_styling_direction(styling_context),
        styling_context=styling_context,
    )
    scene_direction = _build_default_scene_direction(mode_id)
    pose_direction = _build_default_pose_direction(mode_id)
    capture_direction = _build_default_capture_direction(mode_id)
    summary = _build_summary(
        mode_id=mode_id,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        fallback_applied=True,
    )
    base_scene_prompt = _build_base_scene_prompt(
        mode_id=mode_id,
        garment_identity=garment_identity,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        styling_context=styling_context,
    )
    stage2_scene_context = _build_stage2_scene_context(
        mode_id=mode_id,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
    )
    plan = ReferenceCreativePlan(
        garment_identity=garment_identity,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        base_scene_prompt=base_scene_prompt,
        stage2_scene_context=stage2_scene_context,
        summary=summary,
        fallback_applied=True,
    )
    debug_trace = {
        "input": {
            "instruction_prompt": "",
            "input_parts_text_blocks": [],
            "mode_id": str(mode_id or "natural").strip().lower(),
            "garment_hint": garment_identity.get("garment_hint", ""),
            "image_analysis": garment_identity.get("image_analysis", ""),
        },
        "output": {
            "raw_response_text": "",
            "parsed_response_payload": {},
            "normalized_plan": plan.to_dict(),
            "fallback_applied": True,
        },
    }
    return ReferenceCreativePlan(**{**plan.to_dict(), "debug_trace": debug_trace})


def plan_reference_creative_flow(
    *,
    mode_id: str,
    user_prompt: Optional[str],
    scene_preference: Optional[str],
    garment_hint: Optional[str],
    image_analysis: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
    garment_aesthetic: Optional[dict[str, Any]] = None,
    lighting_signature: Optional[dict[str, Any]] = None,
    mode_guardrail_text: str = "",
) -> ReferenceCreativePlan:
    styling_context = derive_styling_context(
        mode_id=mode_id,
        user_prompt=user_prompt,
        garment_hint=garment_hint,
        image_analysis=image_analysis,
        structural_contract=structural_contract,
        set_detection=set_detection,
        garment_aesthetic=garment_aesthetic,
        has_images=True,
    )

    garment_identity = {
        "garment_hint": _clean_text(garment_hint, limit=120),
        "image_analysis": _clean_text(image_analysis, limit=320),
        "structural_hint": build_structural_hint(structural_contract),
        "structure_guards": build_structure_guard_clauses(structural_contract, set_detection=set_detection),
        "required_set_members": get_set_member_labels(
            set_detection or {},
            include_policies={"must_include"},
            member_classes={"garment", "coordinated_accessory"},
            active_only=True,
            exclude_primary_piece=True,
        ),
    }

    mode_lines = list(styling_context.get("mode_lines") or [])
    styling_soul = str(styling_context.get("styling_soul") or "").strip()
    mode_styling_mandate = str(styling_context.get("mode_styling_mandate") or "").strip()
    prompt_text = str(styling_context.get("prompt_text") or "") or "none"
    garment_text = str(styling_context.get("garment_text") or "") or "unknown"
    analysis_text = str(styling_context.get("analysis_text") or "") or "unknown"
    contract = styling_context.get("contract") or {}
    aesthetic = styling_context.get("aesthetic") or {}
    set_info = styling_context.get("set_info") or {}
    lighting = lighting_signature or {}

    model_soul = str(get_model_soul(garment_context=garment_text, mode_id=mode_id) or "")
    scene_soul = str(get_scene_soul(mode_id=mode_id, has_images=True) or "")
    pose_soul = str(get_pose_soul(mode_id=mode_id, has_images=True) or "")
    capture_soul = str(get_capture_soul(mode_id=mode_id, has_images=True) or "")
    instruction = (
        "Build a structured creative plan for an upload-based fashion generation flow.\n\n"
        "This is the BASE generation stage before garment replacement.\n"
        "The uploaded references define only the garment structure and product identity.\n"
        "Do NOT copy the reference person, pose, framing, or background.\n"
        "The job now is to choose the right woman, styling completion, scene, pose, and camera for a fresh base image.\n"
        "The base image should be creative and coherent, while the exact garment surface will be replaced later.\n\n"
        "OUTPUT RULES:\n"
        "- Keep every field compact and concrete.\n"
        "- Casting must describe a NEW adult Brazilian woman.\n"
        "- Casting must make a specific choice, not a median commercial archetype.\n"
        "- Casting must make the face, eyes, skin, hair, frame, expression, and visible makeup readable as a real human choice.\n"
        "- Eyes must read as alive and aligned; avoid vacant, glassy, or divergent-eye results.\n"
        "- Styling must stay subordinate to the hero garment and follow the active mode.\n"
        "- Styling must choose a concrete completion family when completion is needed; do not answer with generic neutral completion language only.\n"
        "- Scene must describe a believable Brazilian setting through visible cues.\n"
        "- Pose must describe observable body behavior, not abstract adjectives.\n"
        "- Pose must choose one distinct commercial body solution; do not fall back to the same safe standing formula.\n"
        "- Capture must describe framing, angle, crop logic, and lens feel.\n"
        "- Capture must choose one concrete commercial relation; do not default to the same centered catalog view.\n"
        "- Return strict JSON only.\n\n"
        "ANTI-REPETITION RULES:\n"
        "- Do not output the same polished brunette catalog woman by default.\n"
        "- Do not default to the same direct open-smile expression unless it is clearly the best choice for this garment.\n"
        "- Do not default to dark tailored trousers plus ankle boots as the universal completion for every top-layer garment.\n"
        "- Do not default to the same hand-on-hip near-frontal catalog pose.\n\n"
        "<MODE_IDENTITY>\n" + "\n".join(mode_lines) + "\n</MODE_IDENTITY>\n\n"
        "<MODEL_SOUL>\n" + model_soul + "\n</MODEL_SOUL>\n\n"
        "<SCENE_SOUL>\n" + scene_soul + "\n</SCENE_SOUL>\n\n"
        "<POSE_SOUL>\n" + pose_soul + "\n</POSE_SOUL>\n\n"
        "<CAPTURE_SOUL>\n" + capture_soul + "\n</CAPTURE_SOUL>\n\n"
        "<STYLING_SOUL>\n" + styling_soul + "\n</STYLING_SOUL>\n\n"
        "<MODE_STYLING_MANDATE>\n" + mode_styling_mandate + "\n</MODE_STYLING_MANDATE>\n\n"
        "<MODE_GUARDRAILS>\n" + _clean_text(mode_guardrail_text, limit=500) + "\n</MODE_GUARDRAILS>\n\n"
        "<JOB_CONTEXT>\n"
        f"- mode_id: {str(mode_id or 'natural').strip().lower()}\n"
        f"- scene_preference: {_clean_text(scene_preference, limit=40) or 'auto_br'}\n"
        f"- user_prompt: {prompt_text}\n"
        f"- garment_hint: {garment_text}\n"
        f"- image_analysis: {analysis_text}\n"
        f"- structural_hint: {_clean_text(garment_identity.get('structural_hint'), limit=160) or 'unknown'}\n"
        f"- structure_guards: {', '.join(garment_identity.get('structure_guards') or []) or 'none'}\n"
        f"- required_set_members: {', '.join(garment_identity.get('required_set_members') or []) or 'none'}\n"
        f"- garment_subtype: {str(contract.get('garment_subtype') or 'unknown')}\n"
        f"- silhouette_volume: {str(contract.get('silhouette_volume') or 'unknown')}\n"
        f"- garment_length: {str(contract.get('garment_length') or 'unknown')}\n"
        f"- front_opening: {str(contract.get('front_opening') or 'unknown')}\n"
        f"- inferred_product_topology: {str(styling_context.get('inferred_topology') or 'single_piece')}\n"
        f"- inferred_hero_family: {str(styling_context.get('inferred_hero_family') or 'unclear')}\n"
        f"- inferred_hero_components: {', '.join(styling_context.get('inferred_components') or []) or 'hero product only'}\n"
        f"- garment_formality: {str(aesthetic.get('formality') or 'unknown')}\n"
        f"- garment_season: {str(aesthetic.get('season') or 'unknown')}\n"
        f"- garment_vibe: {str(aesthetic.get('vibe') or 'unknown')}\n"
        f"- lighting_subject_read: {str(lighting.get('subject_read') or 'unknown')}\n"
        f"- lighting_background_read: {str(lighting.get('background_read') or 'unknown')}\n"
        f"- lighting_integration_risk: {str(lighting.get('integration_risk') or 'unknown')}\n"
        f"- set_mode: {str(set_info.get('set_mode') or 'off')}\n"
        f"- detected_roles: {', '.join(set_info.get('detected_garment_roles') or []) or 'none'}\n"
        "</JOB_CONTEXT>"
    )

    raw_response_text = ""
    parsed_payload: dict[str, Any] = {}
    planner_error = ""
    try:
        response = generate_structured_json(
            parts=[types.Part(text=instruction)],
            schema=REFERENCE_CREATIVE_PLANNER_SCHEMA,
            temperature=0.35,
            max_tokens=1600,
            thinking_budget=0,
        )
        raw_response_text = str(getattr(response, "text", "") or "").strip()
        parsed = _decode_agent_response(response)
        parsed_payload = dict(parsed) if isinstance(parsed, dict) else {}
    except Exception as exc:
        planner_error = str(exc)
        repaired = try_repair_truncated_json(str(exc))
        if repaired is None:
            fallback_plan = build_reference_creative_plan_fallback(
                mode_id=mode_id,
                garment_hint=garment_hint,
                structural_contract=structural_contract,
                set_detection=set_detection,
                image_analysis=image_analysis,
                styling_context=styling_context,
            )
            debug_trace = dict(fallback_plan.debug_trace or {})
            debug_trace["input"] = {
                "instruction_prompt": instruction,
                "input_parts_text_blocks": [instruction],
                "mode_id": str(mode_id or "natural").strip().lower(),
                "souls": {
                    "mode_identity": mode_lines,
                    "model": model_soul,
                    "scene": scene_soul,
                    "pose": pose_soul,
                    "capture": capture_soul,
                    "styling": styling_soul,
                },
                "styling_context": styling_context,
                "garment_identity": garment_identity,
            }
            debug_trace["output"] = {
                "raw_response_text": raw_response_text,
                "parsed_response_payload": {},
                "normalized_plan": fallback_plan.to_dict(),
                "fallback_applied": True,
                "error": planner_error,
            }
            return ReferenceCreativePlan(**{**fallback_plan.to_dict(), "debug_trace": debug_trace})
        parsed = repaired
        parsed_payload = dict(parsed) if isinstance(parsed, dict) else {}

    casting_direction = _normalize_compact_object(
        parsed.get("casting_direction") if isinstance(parsed, dict) else None,
        defaults=_build_default_casting_direction(mode_id),
    )
    styling_direction = normalize_styling_direction_payload(
        (parsed or {}).get("styling_direction") if isinstance(parsed, dict) else None,
        styling_context=styling_context,
    )
    if not _clean_text(styling_direction.get("direction_summary"), limit=200):
        styling_direction = normalize_styling_direction_payload(
            _build_default_styling_direction(styling_context),
            styling_context=styling_context,
        )
    scene_direction = _normalize_compact_object(
        parsed.get("scene_direction") if isinstance(parsed, dict) else None,
        defaults=_build_default_scene_direction(mode_id),
    )
    pose_direction = _normalize_compact_object(
        parsed.get("pose_direction") if isinstance(parsed, dict) else None,
        defaults=_build_default_pose_direction(mode_id),
    )
    capture_direction = _normalize_compact_object(
        parsed.get("capture_direction") if isinstance(parsed, dict) else None,
        defaults=_build_default_capture_direction(mode_id),
    )

    summary = _build_summary(
        mode_id=mode_id,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        fallback_applied=False,
    )
    base_scene_prompt = _build_base_scene_prompt(
        mode_id=mode_id,
        garment_identity=garment_identity,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        styling_context=styling_context,
    )
    stage2_scene_context = _build_stage2_scene_context(
        mode_id=mode_id,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
    )
    if not _clean_text(base_scene_prompt, limit=200):
        return build_reference_creative_plan_fallback(
            mode_id=mode_id,
            garment_hint=garment_hint,
            structural_contract=structural_contract,
            set_detection=set_detection,
            image_analysis=image_analysis,
            styling_context=styling_context,
        )

    normalized_plan = {
        "garment_identity": garment_identity,
        "casting_direction": casting_direction,
        "styling_direction": styling_direction,
        "scene_direction": scene_direction,
        "pose_direction": pose_direction,
        "capture_direction": capture_direction,
        "base_scene_prompt": base_scene_prompt,
        "stage2_scene_context": stage2_scene_context,
        "summary": summary,
        "fallback_applied": False,
    }
    debug_trace = {
        "input": {
            "instruction_prompt": instruction,
            "input_parts_text_blocks": [instruction],
            "mode_id": str(mode_id or "natural").strip().lower(),
            "souls": {
                "mode_identity": mode_lines,
                "model": model_soul,
                "scene": scene_soul,
                "pose": pose_soul,
                "capture": capture_soul,
                "styling": styling_soul,
            },
            "styling_context": styling_context,
            "garment_identity": garment_identity,
        },
        "output": {
            "raw_response_text": raw_response_text,
            "parsed_response_payload": parsed_payload,
            "normalized_plan": normalized_plan,
            "fallback_applied": False,
            "error": planner_error,
        },
    }

    return ReferenceCreativePlan(
        garment_identity=garment_identity,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        base_scene_prompt=base_scene_prompt,
        stage2_scene_context=stage2_scene_context,
        summary=summary,
        fallback_applied=False,
        debug_trace=debug_trace,
    )
