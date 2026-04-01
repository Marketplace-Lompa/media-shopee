from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from google.genai import types

from agent_runtime.fidelity import (
    build_reference_edit_art_direction,
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
from agent_runtime.structural import get_set_member_labels


_CASTING_SCHEMA = {
    "type": "object",
    "required": [
        "profile_hint",
        "age_band",
        "face_hair_presence",
        "body_read",
        "expression_read",
    ],
    "properties": {
        "profile_hint": {"type": "string"},
        "age_band": {"type": "string"},
        "face_hair_presence": {"type": "string"},
        "body_read": {"type": "string"},
        "expression_read": {"type": "string"},
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
    summary: dict[str, str]
    fallback_applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any, *, limit: int = 220) -> str:
    return " ".join(str(value or "").strip().split())[:limit].strip()


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
    footwear_direction = "discreet mode-aligned footwear only if it remains visible in frame"

    if topology == "coordinated_set":
        completion_slots = ["footwear"]
    elif hero_family == "top_layer":
        completion_slots = ["lower_body", "footwear"]
        primary_completion = "quiet lower-body completion that does not compete with the hero garment"
    elif hero_family == "lower_body":
        completion_slots = ["top_layer", "footwear"]
        primary_completion = "quiet upper-body completion that keeps the lower-body hero visible"
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
        "completion_strategy": "Keep the look commercially complete without competing with the hero garment.",
        "primary_completion": primary_completion,
        "secondary_completion": "none",
        "footwear_direction": footwear_direction,
        "accessories_optional": "none",
        "outer_layer_optional": "none",
        "finish_logic": "Let finishing choices stay subordinate to the hero garment and the active mode.",
        "direction_summary": "Resolve only the visibly necessary completion around the hero garment.",
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


def _build_default_pose_direction(mode_id: str) -> dict[str, str]:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return {
            "stance": "commercial near-frontal presentation with slight weight shift",
            "arm_logic": "one arm relaxed and one arm purposefully placed without blocking the garment",
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
            "framing": "medium to medium-full commercial framing",
            "angle": "near-frontal 5 to 15 degree body rotation",
            "crop_logic": "show the garment fully without portrait-first cropping",
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
            "profile_hint": "a commercially attractive adult Brazilian woman with approachable direct presence",
            "age_band": "late 20s to early 30s",
            "face_hair_presence": "clean face read, commercially polished hair, and warm camera presence",
            "body_read": "balanced commercial silhouette with calm posture",
            "expression_read": "approachable direct expression with light warmth",
        }
    if normalized == "editorial_commercial":
        return {
            "profile_hint": "a striking adult Brazilian woman with deliberate fashion presence",
            "age_band": "late 20s to mid 30s",
            "face_hair_presence": "clear facial geometry and confident hair silhouette",
            "body_read": "strong body line with authored posture",
            "expression_read": "controlled commanding expression",
        }
    if normalized == "lifestyle":
        return {
            "profile_hint": "an adult Brazilian woman with socially alive, activity-ready presence",
            "age_band": "mid 20s to early 30s",
            "face_hair_presence": "fresh approachable face and natural movement in the hair",
            "body_read": "active everyday body read with believable energy",
            "expression_read": "socially open expression",
        }
    return {
        "profile_hint": "an adult Brazilian woman with everyday, non-performative presence",
        "age_band": "mid 20s to early 30s",
        "face_hair_presence": "fresh natural face read and believable lived-in hair behavior",
        "body_read": "relaxed realistic body presence without over-styled polish",
        "expression_read": "quiet attentive expression",
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
    soul_stack = build_reference_edit_art_direction(mode_id=mode_id, creative_brief=None)
    mode_styling_mandate = _clean_text(styling_context.get("mode_styling_mandate"), limit=200)

    parts = [
        "BASE GENERATION STAGE: create the woman, scene, pose, and camera first; the garment will be replaced in a later edit pass.",
        soul_stack,
        (
            "Use a placeholder garment that matches the uploaded product's structural identity only. "
            "Do not attempt surface transfer from the references in this stage."
        ),
    ]
    if structural_hint:
        parts.append(f"Structural garment identity: {structural_hint}.")
    elif garment_hint:
        parts.append(f"Garment identity: {garment_hint}.")
    if structure_guards:
        parts.append("Keep these product constraints legible in the placeholder: " + "; ".join(structure_guards) + ".")
    if required_set_members:
        parts.append(
            "Preserve these coordinated set members as separate placeholder pieces: "
            + ", ".join(required_set_members)
            + "."
        )

    parts.append(
        "Casting direction: "
        + " ".join(
            sentence
            for sentence in [
                _clean_text(casting_direction.get("profile_hint"), limit=200),
                _clean_text(casting_direction.get("age_band"), limit=100),
                _clean_text(casting_direction.get("face_hair_presence"), limit=180),
                _clean_text(casting_direction.get("body_read"), limit=180),
                _clean_text(casting_direction.get("expression_read"), limit=180),
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
        "Do not copy any reference person's identity, pose, background, or framing. "
        "The uploads are garment-analysis evidence only for this base stage."
    )

    return " ".join(part.strip() for part in parts if part and part.strip())


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
    return ReferenceCreativePlan(
        garment_identity=garment_identity,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        base_scene_prompt=base_scene_prompt,
        summary=summary,
        fallback_applied=True,
    )


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
        "- Styling must stay subordinate to the hero garment and follow the active mode.\n"
        "- Scene must describe a believable Brazilian setting through visible cues.\n"
        "- Pose must describe observable body behavior, not abstract adjectives.\n"
        "- Capture must describe framing, angle, crop logic, and lens feel.\n"
        "- Return strict JSON only.\n\n"
        "<MODE_IDENTITY>\n" + "\n".join(mode_lines) + "\n</MODE_IDENTITY>\n\n"
        "<SCENE_SOUL>\n" + str(get_scene_soul(mode_id=mode_id, has_images=True) or "") + "\n</SCENE_SOUL>\n\n"
        "<POSE_SOUL>\n" + str(get_pose_soul(mode_id=mode_id, has_images=True) or "") + "\n</POSE_SOUL>\n\n"
        "<CAPTURE_SOUL>\n" + str(get_capture_soul(mode_id=mode_id, has_images=True) or "") + "\n</CAPTURE_SOUL>\n\n"
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

    try:
        response = generate_structured_json(
            parts=[types.Part(text=instruction)],
            schema=REFERENCE_CREATIVE_PLANNER_SCHEMA,
            temperature=0.35,
            max_tokens=1600,
            thinking_budget=0,
        )
        parsed = _decode_agent_response(response)
    except Exception as exc:
        repaired = try_repair_truncated_json(str(exc))
        if repaired is None:
            return build_reference_creative_plan_fallback(
                mode_id=mode_id,
                garment_hint=garment_hint,
                structural_contract=structural_contract,
                set_detection=set_detection,
                image_analysis=image_analysis,
                styling_context=styling_context,
            )
        parsed = repaired

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
    if not _clean_text(base_scene_prompt, limit=200):
        return build_reference_creative_plan_fallback(
            mode_id=mode_id,
            garment_hint=garment_hint,
            structural_contract=structural_contract,
            set_detection=set_detection,
            image_analysis=image_analysis,
            styling_context=styling_context,
        )

    return ReferenceCreativePlan(
        garment_identity=garment_identity,
        casting_direction=casting_direction,
        styling_direction=styling_direction,
        scene_direction=scene_direction,
        pose_direction=pose_direction,
        capture_direction=capture_direction,
        base_scene_prompt=base_scene_prompt,
        summary=summary,
        fallback_applied=False,
    )
