from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from agent_runtime.editing.contracts import PreparedEditPrompt, ViewTransformDirective

ANGLE_VIEW_TARGETS = (
    "front",
    "left_3q",
    "right_3q",
    "left_profile",
    "right_profile",
    "back",
    "left_3q_back",
    "right_3q_back",
)


@dataclass(frozen=True)
class AngleTransformPlan:
    requested_text: str
    source_view_assumption: str
    view_intent: str
    view_target: Optional[str]
    turn_hint_degrees: Optional[int]
    viewpoint_strategy: str
    framing: str
    camera_height: str
    distance_intent: str
    lens_intent: str
    framing_lock: bool
    camera_height_lock: bool
    pose_freedom: str
    garment_identity_lock: bool
    identity_locks: tuple[str, ...]
    forbidden_drift: tuple[str, ...]
    execution_strategy: str
    drift_risk: str


_IDENTITY_LOCKS = (
    "same person",
    "same outfit",
    "same colors",
    "same proportions",
    "same styling",
    "same garment silhouette",
    "same visible outfit identity",
)

_FORBIDDEN_DRIFT = (
    "do not crop from full body into portrait close-up",
    "do not change camera height unless explicitly requested",
    "do not drastically change pose",
    "do not redesign clothing",
    "do not hide garment length",
    "do not replace styling",
    "do not shift from commercial shot to editorial close portrait unless explicitly requested",
)


def is_angle_transform_request(text: Optional[str], *, explicit_submode: Optional[str] = None) -> bool:
    if str(explicit_submode or "").strip().lower() == "angle_transform":
        return True
    normalized = _normalize_request_text(text)
    if not normalized:
        return False
    return any(
        token in normalized
        for token in (
            "angulo",
            "ângulo",
            "grau",
            "graus",
            "3/4",
            "tres quartos",
            "três quartos",
            "perfil",
            "lateral",
            "de lado",
            "costas",
            "frente",
            "front",
            "back",
            "side",
            "three quarter",
        )
    )


def resolve_view_target(
    requested_text: Optional[str],
    *,
    explicit_target: Optional[str] = None,
) -> tuple[str, Optional[int]]:
    normalized = _normalize_request_text(requested_text)
    if explicit_target and explicit_target in ANGLE_VIEW_TARGETS:
        return explicit_target, _extract_turn_hint_degrees(normalized)

    degrees = _extract_turn_hint_degrees(normalized)
    wants_back = any(token in normalized for token in ("costas", "back", "atras", "atrás"))
    wants_profile = any(token in normalized for token in ("perfil", "profile", "lateral", "de lado", "side"))
    wants_three_quarter = any(
        token in normalized for token in ("3/4", "tres quartos", "três quartos", "three quarter", "30 graus", "45 graus")
    )

    side = "left"
    if any(token in normalized for token in ("direita", "right", "lado direito")):
        side = "right"
    elif any(token in normalized for token in ("esquerda", "left", "lado esquerdo")):
        side = "left"

    if wants_back:
        if wants_three_quarter:
            return (f"{side}_3q_back", degrees)
        return ("back", degrees)

    if wants_profile:
        return (f"{side}_profile", degrees)

    if wants_three_quarter:
        return (f"{side}_3q", degrees)

    if degrees is not None:
        if 15 <= degrees <= 60:
            return (f"{side}_3q", degrees)
        if 61 <= degrees <= 120:
            return (f"{side}_profile", degrees)
        if 150 <= degrees <= 210:
            return ("back", degrees)

    if any(token in normalized for token in ("frente", "front")):
        return ("front", degrees)

    return ("left_3q", degrees)


def build_angle_transform_plan(
    directive: ViewTransformDirective,
    *,
    requested_text: Optional[str],
    source_shot_type: Optional[str] = None,
) -> AngleTransformPlan:
    view_target = directive.view_target_hint
    degrees = directive.turn_hint_degrees
    framing = _map_shot_type_to_framing(source_shot_type)
    drift_risk = "low"
    execution_strategy = "direct"

    if directive.view_intent == "back_view" or view_target in {"back", "left_3q_back", "right_3q_back"}:
        drift_risk = "high"
        execution_strategy = "2step"
    elif framing == "close" and view_target in {"left_profile", "right_profile"}:
        drift_risk = "medium"
        execution_strategy = "repair"

    return AngleTransformPlan(
        requested_text=str(requested_text or "").strip(),
        source_view_assumption="front",
        view_intent=directive.view_intent,
        view_target=view_target,
        turn_hint_degrees=degrees,
        viewpoint_strategy="camera_orbit_first",
        framing=framing,
        camera_height="eye_level",
        distance_intent=directive.distance_intent,
        lens_intent="neutral_fashion_perspective",
        framing_lock=directive.framing_lock,
        camera_height_lock=directive.camera_height_lock,
        pose_freedom=directive.pose_freedom,
        garment_identity_lock=directive.garment_identity_lock,
        identity_locks=_IDENTITY_LOCKS,
        forbidden_drift=_FORBIDDEN_DRIFT,
        execution_strategy=execution_strategy,
        drift_risk=drift_risk,
    )


def build_guided_angle_prompt(
    plan: AngleTransformPlan,
    *,
    extra_direction: Optional[str] = None,
) -> PreparedEditPrompt:
    framing_phrase = _render_locked_framing(plan.framing, distance_intent=plan.distance_intent) if plan.framing_lock else "the same overall commercial shot family"
    camera_height_phrase = (
        _render_camera_height(plan.camera_height)
        if plan.camera_height_lock
        else "a commercially coherent camera height"
    )
    distance_phrase = _render_distance_phrase(plan.distance_intent)
    pose_phrase = _render_pose_phrase(plan.pose_freedom)
    viewpoint_phrase = _render_viewpoint_phrase(plan)
    prompt_parts = [
        "Use the attached image as the source of truth.",
        (
            "Create a new commercial fashion photograph of the same person and the same outfit, "
            "keeping the same colors, proportions, styling, garment silhouette, and visible garment identity."
        ),
        _render_view_instruction(plan),
        viewpoint_phrase,
        (
            f"Preserve {framing_phrase}, {camera_height_phrase}, {distance_phrase}, "
            "with a neutral fashion perspective, a similar lighting mood, and a consistent background family."
        ),
        pose_phrase,
        (
            "Preserve garment silhouette, garment length, and visible garment details. "
            "Do not redesign the clothing or change the image into a different shot type."
        ),
    ]
    extra = str(extra_direction or "").strip()
    if extra:
        prompt_parts.append(f"Also keep this additional direction in mind: {extra}.")

    final_prompt = " ".join(part.strip().rstrip(".") + "." for part in prompt_parts if part and part.strip())

    return PreparedEditPrompt(
        flow_mode="guided_angle",
        edit_type="framing",
        display_prompt=final_prompt.strip(),
        model_prompt=final_prompt.strip(),
        change_summary_ptbr=_render_summary_ptbr(plan),
        confidence=0.92,
        include_source_prompt_context=False,
        include_reference_item_description=False,
        use_structured_shell=False,
    )


def _normalize_request_text(text: Optional[str]) -> str:
    normalized = str(text or "").strip().lower()
    normalized = normalized.replace("três", "tres")
    normalized = normalized.replace("ângulo", "angulo")
    return normalized


def _extract_turn_hint_degrees(text: str) -> Optional[int]:
    match = re.search(r"(\d{1,3})\s*(?:graus?|°)", text)
    if not match:
        return None
    try:
        value = int(match.group(1))
    except ValueError:
        return None
    if 0 <= value <= 360:
        return value
    return None


def _map_shot_type_to_framing(source_shot_type: Optional[str]) -> str:
    token = str(source_shot_type or "").strip().lower()
    if token == "wide":
        return "full_body"
    if token == "close-up":
        return "close"
    return "mid"


def _render_framing(framing: str) -> str:
    if framing == "full_body":
        return "full-body framing"
    if framing == "close":
        return "close framing"
    return "mid-length framing"


def _render_locked_framing(framing: str, *, distance_intent: str) -> str:
    if distance_intent in {"closer", "farther"}:
        return "the same overall shot family"
    if framing == "full_body":
        return "full-body framing"
    if framing == "close":
        return "the original close framing"
    return "the original framing"


def _render_camera_height(camera_height: str) -> str:
    if camera_height == "chest_height":
        return "chest-height camera"
    if camera_height == "slightly_high":
        return "slightly high camera"
    if camera_height == "slightly_low":
        return "slightly low camera"
    return "eye-level camera"


def _render_view_phrase(view_target: str, degrees: Optional[int]) -> str:
    degrees_hint = ""
    if degrees is not None and view_target in {"left_3q", "right_3q"}:
        degrees_hint = f", approximately {degrees} degrees from the original front view"
    phrases = {
        "front": "a clean front view",
        "left_3q": f"a clean left three-quarter view{degrees_hint}",
        "right_3q": f"a clean right three-quarter view{degrees_hint}",
        "left_profile": "a clean left profile view",
        "right_profile": "a clean right profile view",
        "back": "a clean full back view",
        "left_3q_back": "a clean left three-quarter back view",
        "right_3q_back": "a clean right three-quarter back view",
    }
    return phrases.get(view_target, "a clean left three-quarter view")


def _render_view_instruction(plan: AngleTransformPlan) -> str:
    if plan.view_intent == "preserve":
        return "Keep the current viewing angle and overall shot composition as the baseline."
    if plan.view_intent == "back_view":
        if plan.view_target:
            return f"Show {_render_view_phrase(plan.view_target, plan.turn_hint_degrees)} clearly."
        return "Show the back of the outfit clearly."
    if plan.view_target:
        return f"Render the subject from {_render_view_phrase(plan.view_target, plan.turn_hint_degrees)}."
    return "Render the subject from a subtle three-quarter camera angle."


def _render_viewpoint_phrase(plan: AngleTransformPlan) -> str:
    if plan.view_intent == "preserve":
        if plan.distance_intent == "closer":
            return (
                "Use a slightly closer camera distance as the primary change, "
                "without introducing a new camera angle or subject rotation."
            )
        if plan.distance_intent == "farther":
            return (
                "Use a slightly farther camera distance as the primary change, "
                "without introducing a new camera angle or subject rotation."
            )
        return "Keep the current camera viewpoint unchanged."
    if plan.view_intent == "back_view":
        return (
            "Reveal this primarily through a back-facing camera viewpoint around the subject, "
            "not by turning the subject as the main solution."
        )
    return (
        "Use a subtle camera repositioning around the subject as the primary change, "
        "not subject rotation as the main solution."
    )


def _render_distance_phrase(distance_intent: str) -> str:
    if distance_intent == "closer":
        return "a slightly closer camera distance while preserving garment readability"
    if distance_intent == "farther":
        return "a slightly farther camera distance while preserving garment readability"
    return "the original camera distance"


def _render_pose_phrase(pose_freedom: str) -> str:
    if pose_freedom == "flexible":
        return (
            "Keep the original stance and torso orientation as the anchor, but allow only a minimal natural body adjustment "
            "if it is needed to support the requested camera change."
        )
    return (
        "Keep the body stance, torso orientation, and pose structure as close as possible to the original."
    )


def _render_summary_ptbr(plan: AngleTransformPlan) -> str:
    if plan.view_intent == "back_view":
        return "Mostrar costas da peça preservando a leitura comercial."
    if plan.distance_intent == "closer":
        return "Ajustar o ângulo com aproximação leve, preservando a peça."
    if plan.distance_intent == "farther":
        return "Ajustar o ângulo com afastamento leve, preservando a peça."
    if plan.view_target:
        labels = {
            "left_3q": "Ajustar para três quartos mantendo a composição comercial.",
            "right_3q": "Ajustar para três quartos mantendo a composição comercial.",
            "left_profile": "Ajustar para um perfil mais lateral mantendo a composição comercial.",
            "right_profile": "Ajustar para um perfil mais lateral mantendo a composição comercial.",
            "back": "Ajustar para vista de costas mantendo a composição comercial.",
        }
        return labels.get(plan.view_target, "Ajustar o ângulo mantendo a composição comercial.")
    return "Ajustar o ângulo de forma sutil mantendo a composição comercial."
