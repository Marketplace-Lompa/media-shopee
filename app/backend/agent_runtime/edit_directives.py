from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from agent_runtime.editing.contracts import ViewTransformDirective


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
class PartialViewTransformDirective:
    view_intent: Optional[str] = None
    view_target_hint: Optional[str] = None
    turn_hint_degrees: Optional[int] = None
    distance_intent: Optional[str] = None
    pose_freedom: Optional[str] = None
    framing_lock: Optional[bool] = None
    camera_height_lock: Optional[bool] = None
    garment_identity_lock: Optional[bool] = None
    source: Optional[str] = None


def build_directive_from_command_center(
    *,
    edit_submode: Optional[str] = None,
    view_intent: Optional[str] = None,
    distance_intent: Optional[str] = None,
    pose_freedom: Optional[str] = None,
    angle_target: Optional[str] = None,
    preserve_framing: bool = True,
    preserve_camera_height: bool = True,
    preserve_distance: bool = True,
    preserve_pose: bool = True,
) -> Optional[PartialViewTransformDirective]:
    if str(edit_submode or "").strip().lower() != "angle_transform":
        return None

    normalized_target = str(angle_target or "").strip().lower()
    normalized_view_intent = str(view_intent or "").strip().lower() or "soft_turn"
    normalized_distance_intent = str(distance_intent or "").strip().lower()
    normalized_pose_freedom = str(pose_freedom or "").strip().lower()
    resolved_view_intent = normalized_view_intent
    view_target_hint: Optional[str] = None
    if normalized_target in {"back", "left_3q_back", "right_3q_back"}:
        resolved_view_intent = "back_view"
        view_target_hint = normalized_target
    elif normalized_target in ANGLE_VIEW_TARGETS:
        resolved_view_intent = "soft_turn"
        view_target_hint = normalized_target

    return PartialViewTransformDirective(
        view_intent=resolved_view_intent,
        view_target_hint=view_target_hint,
        distance_intent=(
            normalized_distance_intent
            if normalized_distance_intent in {"preserve", "closer", "farther"}
            else ("preserve" if preserve_distance else None)
        ),
        pose_freedom=(
            normalized_pose_freedom
            if normalized_pose_freedom in {"locked", "flexible"}
            else ("locked" if preserve_pose else "flexible")
        ),
        framing_lock=preserve_framing,
        camera_height_lock=preserve_camera_height,
        garment_identity_lock=True,
        source="command_center",
    )


def infer_directive_from_text(text: Optional[str]) -> Optional[PartialViewTransformDirective]:
    normalized = _normalize_text(text)
    if not normalized:
        return None

    turn_hint_degrees = _extract_turn_hint_degrees(normalized)
    view_target_hint, inferred_view_intent = _infer_view_from_text(normalized, turn_hint_degrees)
    distance_intent = _infer_distance_from_text(normalized)
    pose_freedom = _infer_pose_freedom_from_text(normalized)

    if (
        inferred_view_intent is None
        and distance_intent is None
        and pose_freedom is None
        and turn_hint_degrees is None
    ):
        return None

    return PartialViewTransformDirective(
        view_intent=inferred_view_intent,
        view_target_hint=view_target_hint,
        turn_hint_degrees=turn_hint_degrees,
        distance_intent=distance_intent,
        pose_freedom=pose_freedom,
        source="chat_text",
    )


def merge_edit_directives(*partials: Optional[PartialViewTransformDirective]) -> ViewTransformDirective:
    directive = ViewTransformDirective()
    for partial in partials:
        if partial is None:
            continue
        if partial.view_intent is not None:
            directive = ViewTransformDirective(
                view_intent=partial.view_intent,
                view_target_hint=directive.view_target_hint,
                turn_hint_degrees=directive.turn_hint_degrees,
                distance_intent=directive.distance_intent,
                pose_freedom=directive.pose_freedom,
                framing_lock=directive.framing_lock,
                camera_height_lock=directive.camera_height_lock,
                garment_identity_lock=directive.garment_identity_lock,
                source=partial.source or directive.source,
            )
        if partial.view_target_hint is not None:
            directive = ViewTransformDirective(
                view_intent=directive.view_intent,
                view_target_hint=partial.view_target_hint,
                turn_hint_degrees=directive.turn_hint_degrees,
                distance_intent=directive.distance_intent,
                pose_freedom=directive.pose_freedom,
                framing_lock=directive.framing_lock,
                camera_height_lock=directive.camera_height_lock,
                garment_identity_lock=directive.garment_identity_lock,
                source=partial.source or directive.source,
            )
        if partial.turn_hint_degrees is not None:
            directive = ViewTransformDirective(
                view_intent=directive.view_intent,
                view_target_hint=directive.view_target_hint,
                turn_hint_degrees=partial.turn_hint_degrees,
                distance_intent=directive.distance_intent,
                pose_freedom=directive.pose_freedom,
                framing_lock=directive.framing_lock,
                camera_height_lock=directive.camera_height_lock,
                garment_identity_lock=directive.garment_identity_lock,
                source=partial.source or directive.source,
            )
        if partial.distance_intent is not None:
            directive = ViewTransformDirective(
                view_intent=directive.view_intent,
                view_target_hint=directive.view_target_hint,
                turn_hint_degrees=directive.turn_hint_degrees,
                distance_intent=partial.distance_intent,
                pose_freedom=directive.pose_freedom,
                framing_lock=directive.framing_lock,
                camera_height_lock=directive.camera_height_lock,
                garment_identity_lock=directive.garment_identity_lock,
                source=partial.source or directive.source,
            )
        if partial.pose_freedom is not None:
            directive = ViewTransformDirective(
                view_intent=directive.view_intent,
                view_target_hint=directive.view_target_hint,
                turn_hint_degrees=directive.turn_hint_degrees,
                distance_intent=directive.distance_intent,
                pose_freedom=partial.pose_freedom,
                framing_lock=directive.framing_lock,
                camera_height_lock=directive.camera_height_lock,
                garment_identity_lock=directive.garment_identity_lock,
                source=partial.source or directive.source,
            )
        if partial.framing_lock is not None:
            directive = ViewTransformDirective(
                view_intent=directive.view_intent,
                view_target_hint=directive.view_target_hint,
                turn_hint_degrees=directive.turn_hint_degrees,
                distance_intent=directive.distance_intent,
                pose_freedom=directive.pose_freedom,
                framing_lock=partial.framing_lock,
                camera_height_lock=directive.camera_height_lock,
                garment_identity_lock=directive.garment_identity_lock,
                source=partial.source or directive.source,
            )
        if partial.camera_height_lock is not None:
            directive = ViewTransformDirective(
                view_intent=directive.view_intent,
                view_target_hint=directive.view_target_hint,
                turn_hint_degrees=directive.turn_hint_degrees,
                distance_intent=directive.distance_intent,
                pose_freedom=directive.pose_freedom,
                framing_lock=directive.framing_lock,
                camera_height_lock=partial.camera_height_lock,
                garment_identity_lock=directive.garment_identity_lock,
                source=partial.source or directive.source,
            )
        if partial.garment_identity_lock is not None:
            directive = ViewTransformDirective(
                view_intent=directive.view_intent,
                view_target_hint=directive.view_target_hint,
                turn_hint_degrees=directive.turn_hint_degrees,
                distance_intent=directive.distance_intent,
                pose_freedom=directive.pose_freedom,
                framing_lock=directive.framing_lock,
                camera_height_lock=directive.camera_height_lock,
                garment_identity_lock=partial.garment_identity_lock,
                source=partial.source or directive.source,
            )
    return directive


def resolve_effective_directive(
    *,
    edit_instruction: Optional[str],
    free_text: Optional[str] = None,
    edit_submode: Optional[str] = None,
    view_intent: Optional[str] = None,
    distance_intent: Optional[str] = None,
    pose_freedom: Optional[str] = None,
    angle_target: Optional[str] = None,
    preserve_framing: bool = True,
    preserve_camera_height: bool = True,
    preserve_distance: bool = True,
    preserve_pose: bool = True,
    preset_directive: Optional[PartialViewTransformDirective] = None,
) -> ViewTransformDirective:
    text_payload = ". ".join(
        part.strip() for part in (edit_instruction or "", free_text or "") if str(part).strip()
    )
    inferred = infer_directive_from_text(text_payload)
    command_center = build_directive_from_command_center(
        edit_submode=edit_submode,
        view_intent=view_intent,
        distance_intent=distance_intent,
        pose_freedom=pose_freedom,
        angle_target=angle_target,
        preserve_framing=preserve_framing,
        preserve_camera_height=preserve_camera_height,
        preserve_distance=preserve_distance,
        preserve_pose=preserve_pose,
    )
    return merge_edit_directives(
        preset_directive,
        inferred,
        command_center,
    )


def directive_requests_transform(
    directive: ViewTransformDirective,
    *,
    explicit_submode: Optional[str] = None,
) -> bool:
    if str(explicit_submode or "").strip().lower() == "angle_transform":
        return True
    return (
        directive.view_intent != "preserve"
        or directive.distance_intent != "preserve"
        or directive.pose_freedom != "locked"
    )


def _normalize_text(text: Optional[str]) -> str:
    normalized = str(text or "").strip().lower()
    normalized = normalized.replace("três", "tres")
    normalized = normalized.replace("ângulo", "angulo")
    normalized = normalized.replace("próximo", "proximo")
    normalized = normalized.replace("posição", "posicao")
    return normalized


def _extract_turn_hint_degrees(text: str) -> Optional[int]:
    match = re.search(r"(\d{1,3})\s*(?:graus?|°)", text)
    if not match:
        return None
    try:
        value = int(match.group(1))
    except ValueError:
        return None
    return value if 0 <= value <= 360 else None


def _infer_view_from_text(text: str, degrees: Optional[int]) -> tuple[Optional[str], Optional[str]]:
    wants_back = any(token in text for token in ("costas", "back", "atras", "atrás"))
    if wants_back:
        if any(token in text for token in ("3/4", "tres quartos", "three quarter")):
            side = _infer_side(text)
            return (f"{side}_3q_back", "back_view")
        return ("back", "back_view")

    wants_angle = any(
        token in text
        for token in (
            "mudar angulo",
            "mudar o angulo",
            "girar",
            "virar",
            "perfil",
            "lateral",
            "de lado",
            "3/4",
            "tres quartos",
            "three quarter",
            "30 graus",
            "45 graus",
        )
    )
    if not wants_angle and degrees is None:
        return (None, None)

    side = _infer_side(text)
    if any(token in text for token in ("perfil", "lateral", "de lado", "side")):
        return (f"{side}_profile", "soft_turn")
    if any(token in text for token in ("3/4", "tres quartos", "three quarter")):
        return (f"{side}_3q", "soft_turn")
    if degrees is not None:
        if 15 <= degrees <= 60:
            return (f"{side}_3q", "soft_turn")
        if 61 <= degrees <= 120:
            return (f"{side}_profile", "soft_turn")
        if 150 <= degrees <= 210:
            return ("back", "back_view")
    return (None, "soft_turn")


def _infer_distance_from_text(text: str) -> Optional[str]:
    if any(token in text for token in ("mais proximo", "mais perto", "aproximar", "aproxima", "close", "fechar")):
        return "closer"
    if any(token in text for token in ("mais distante", "mais longe", "afastar", "afasta", "abrir plano")):
        return "farther"
    return None


def _infer_pose_freedom_from_text(text: str) -> Optional[str]:
    if any(token in text for token in ("liberar posicao", "soltar posicao", "liberar pose", "ajustar pose", "mudar pose")):
        return "flexible"
    if any(token in text for token in ("travar posicao", "manter pose", "mesma pose", "nao mudar pose", "não mudar pose")):
        return "locked"
    return None


def _infer_side(text: str) -> str:
    if any(token in text for token in ("direita", "right", "lado direito")):
        return "right"
    return "left"
