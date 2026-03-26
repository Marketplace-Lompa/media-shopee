from __future__ import annotations

from typing import Optional

from agent_runtime.angle_transform import (
    build_angle_transform_plan,
    build_guided_angle_prompt,
)
from agent_runtime.edit_directives import build_directive_from_command_center, merge_edit_directives
from agent_runtime.editing.contracts import PreparedEditPrompt


def prepare_guided_angle_prompt(
    *,
    edit_instruction: str,
    view_intent: Optional[str] = None,
    distance_intent: Optional[str] = None,
    pose_freedom: Optional[str] = None,
    angle_target: Optional[str] = None,
    preserve_framing: bool = True,
    preserve_camera_height: bool = True,
    preserve_distance: bool = True,
    preserve_pose: bool = True,
    source_shot_type: Optional[str] = None,
) -> PreparedEditPrompt:
    partial = build_directive_from_command_center(
        edit_submode="angle_transform",
        view_intent=view_intent,
        distance_intent=distance_intent,
        pose_freedom=pose_freedom,
        angle_target=angle_target,
        preserve_framing=preserve_framing,
        preserve_camera_height=preserve_camera_height,
        preserve_distance=preserve_distance,
        preserve_pose=preserve_pose,
    )
    if partial is None:
        raise ValueError("guided angle prompt requires explicit angle transform controls")
    directive = merge_edit_directives(partial)
    plan = build_angle_transform_plan(
        directive,
        requested_text=edit_instruction,
        source_shot_type=source_shot_type,
    )
    return build_guided_angle_prompt(plan)
