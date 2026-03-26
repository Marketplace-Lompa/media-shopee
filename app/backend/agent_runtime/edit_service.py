from __future__ import annotations

import uuid
from typing import Optional

from agent_runtime.editing.contracts import (
    ImageEditExecutionRequest,
    ImageEditExecutionResult,
    PreparedEditPrompt,
)
from agent_runtime.editing.executor import execute_image_edit_request
from agent_runtime.editing.freeform_flow import prepare_freeform_edit_prompt
from agent_runtime.editing.guided_angle_flow import prepare_guided_angle_prompt


def curate_edit_instruction(
    *,
    edit_instruction: str,
    source_image_bytes: bytes,
    source_prompt: Optional[str] = None,
    reference_images_bytes: Optional[list[bytes]] = None,
    category: str = "fashion",
) -> PreparedEditPrompt:
    return prepare_freeform_edit_prompt(
        edit_instruction=edit_instruction,
        source_image_bytes=source_image_bytes,
        source_prompt=source_prompt,
        reference_images_bytes=reference_images_bytes,
        category=category,
    )


def build_curated_edit_prompt(
    *,
    edit_instruction: str,
    source_image_bytes: bytes,
    source_prompt: Optional[str] = None,
    reference_images_bytes: Optional[list[bytes]] = None,
    category: str = "fashion",
    edit_submode: Optional[str] = None,
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
    if str(edit_submode or "").strip().lower() == "angle_transform":
        return prepare_guided_angle_prompt(
            edit_instruction=edit_instruction,
            view_intent=view_intent,
            distance_intent=distance_intent,
            pose_freedom=pose_freedom,
            angle_target=angle_target,
            preserve_framing=preserve_framing,
            preserve_camera_height=preserve_camera_height,
            preserve_distance=preserve_distance,
            preserve_pose=preserve_pose,
            source_shot_type=source_shot_type,
        )
    return prepare_freeform_edit_prompt(
        edit_instruction=edit_instruction,
        source_image_bytes=source_image_bytes,
        source_prompt=source_prompt,
        reference_images_bytes=reference_images_bytes,
        category=category,
    )


def execute_edit_request(request: ImageEditExecutionRequest) -> list[dict]:
    return execute_image_edit_request(request)


def run_edit_flow(
    *,
    edit_instruction: str,
    source_image_bytes: bytes,
    aspect_ratio: str,
    resolution: str,
    source_prompt: Optional[str] = None,
    source_session_id: Optional[str] = None,
    reference_images_bytes: Optional[list[bytes]] = None,
    session_id: Optional[str] = None,
    thinking_level: str = "HIGH",
    category: str = "fashion",
    use_image_grounding: bool = False,
    lock_person: bool = True,
    edit_submode: Optional[str] = None,
    view_intent: Optional[str] = None,
    distance_intent: Optional[str] = None,
    pose_freedom: Optional[str] = None,
    angle_target: Optional[str] = None,
    preserve_framing: bool = True,
    preserve_camera_height: bool = True,
    preserve_distance: bool = True,
    preserve_pose: bool = True,
    source_shot_type: Optional[str] = None,
) -> ImageEditExecutionResult:
    prepared_prompt = build_curated_edit_prompt(
        edit_instruction=edit_instruction,
        source_image_bytes=source_image_bytes,
        source_prompt=source_prompt,
        reference_images_bytes=reference_images_bytes,
        category=category,
        edit_submode=edit_submode,
        view_intent=view_intent,
        distance_intent=distance_intent,
        pose_freedom=pose_freedom,
        angle_target=angle_target,
        preserve_framing=preserve_framing,
        preserve_camera_height=preserve_camera_height,
        preserve_distance=preserve_distance,
        preserve_pose=preserve_pose,
        source_shot_type=source_shot_type,
    )
    batch = execute_image_edit_request(
        ImageEditExecutionRequest(
            source_image_bytes=source_image_bytes,
            prepared_prompt=prepared_prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            session_id=session_id,
            source_session_id=source_session_id,
            source_prompt_context=(
                source_prompt if prepared_prompt.include_source_prompt_context else None
            ),
            reference_images_bytes=list(reference_images_bytes or []),
            thinking_level=thinking_level,
            use_image_grounding=use_image_grounding,
            lock_person=lock_person,
            edit_submode=edit_submode,
            source_shot_type=source_shot_type,
        )
    )
    effective_session_id = session_id or ""
    if not effective_session_id and batch:
        first_url = str(batch[0].get("url") or "")
        effective_session_id = first_url.strip("/").split("/")[1] if first_url.startswith("/outputs/") else ""
    return ImageEditExecutionResult(
        session_id=effective_session_id or str(uuid.uuid4())[:8],
        images=batch,
        edit_instruction=edit_instruction,
        edit_type=prepared_prompt.edit_type,
        change_summary=prepared_prompt.change_summary_ptbr,
        optimized_prompt=prepared_prompt.display_prompt,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        source_session_id=source_session_id,
        edit_submode=edit_submode,
    )
