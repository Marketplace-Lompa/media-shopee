from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from agent_runtime.edit_directives import (
    build_directive_from_command_center,
    infer_directive_from_text,
    merge_edit_directives,
    resolve_effective_directive,
)


def test_infer_directive_maps_soft_turn_from_generic_angle_request() -> None:
    directive = infer_directive_from_text("mudar ângulo da imagem")
    assert directive is not None
    assert directive.view_intent == "soft_turn"
    assert directive.view_target_hint is None


def test_infer_directive_maps_back_view_from_text() -> None:
    directive = infer_directive_from_text("mostrar costas")
    assert directive is not None
    assert directive.view_intent == "back_view"
    assert directive.view_target_hint == "back"


def test_infer_directive_maps_distance_and_pose_control() -> None:
    directive = infer_directive_from_text("mais próximo e liberar posição")
    assert directive is not None
    assert directive.distance_intent == "closer"
    assert directive.pose_freedom == "flexible"


def test_command_center_overrides_chat_for_view_intent() -> None:
    chat = infer_directive_from_text("mostrar costas")
    command_center = build_directive_from_command_center(
        edit_submode="angle_transform",
        view_intent="soft_turn",
        angle_target=None,
        preserve_framing=True,
        preserve_camera_height=True,
        preserve_distance=True,
        preserve_pose=True,
    )
    merged = merge_edit_directives(chat, command_center)
    assert merged.view_intent == "soft_turn"
    assert merged.source == "command_center"


def test_command_center_structured_fields_override_compatibility_flags() -> None:
    directive = build_directive_from_command_center(
        edit_submode="angle_transform",
        view_intent="back_view",
        distance_intent="closer",
        pose_freedom="flexible",
        angle_target=None,
        preserve_framing=True,
        preserve_camera_height=True,
        preserve_distance=True,
        preserve_pose=True,
    )
    assert directive is not None
    assert directive.view_intent == "back_view"
    assert directive.distance_intent == "closer"
    assert directive.pose_freedom == "flexible"


def test_resolve_effective_directive_merges_all_inputs() -> None:
    directive = resolve_effective_directive(
        edit_instruction="mudar ângulo",
        free_text="mais distante",
        edit_submode="angle_transform",
        angle_target="back",
        preserve_framing=False,
        preserve_camera_height=True,
        preserve_distance=False,
        preserve_pose=False,
    )
    assert directive.view_intent == "back_view"
    assert directive.view_target_hint == "back"
    assert directive.distance_intent == "farther"
    assert directive.pose_freedom == "flexible"
    assert directive.framing_lock is False


def test_resolve_effective_directive_prefers_explicit_structured_intents() -> None:
    directive = resolve_effective_directive(
        edit_instruction="mostrar costas e travar posição",
        free_text=None,
        edit_submode="angle_transform",
        view_intent="soft_turn",
        distance_intent="closer",
        pose_freedom="flexible",
        angle_target="back",
        preserve_framing=True,
        preserve_camera_height=True,
        preserve_distance=True,
        preserve_pose=True,
    )
    assert directive.view_intent == "back_view"
    assert directive.view_target_hint == "back"
    assert directive.distance_intent == "closer"
    assert directive.pose_freedom == "flexible"
