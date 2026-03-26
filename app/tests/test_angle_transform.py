from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from agent_runtime.angle_transform import (
    build_guided_angle_prompt,
    build_angle_transform_plan,
)
from agent_runtime.editing.contracts import ViewTransformDirective


def test_build_angle_transform_prompt_preserves_identity_and_framing() -> None:
    plan = build_angle_transform_plan(
        ViewTransformDirective(
            view_intent="soft_turn",
            view_target_hint="left_3q",
            turn_hint_degrees=30,
            distance_intent="preserve",
            pose_freedom="locked",
            framing_lock=True,
            camera_height_lock=True,
            garment_identity_lock=True,
            source="chat_text",
        ),
        requested_text="mudar para 3/4 mas manter corpo inteiro",
        source_shot_type="wide",
    )
    prepared = build_guided_angle_prompt(plan, extra_direction="manter mood clean")

    assert prepared.edit_type == "framing"
    assert "same person" in prepared.display_prompt
    assert "same outfit" in prepared.display_prompt
    assert "clean left three-quarter view" in prepared.display_prompt
    assert "subtle camera repositioning around the subject" in prepared.display_prompt
    assert "not subject rotation as the main solution" in prepared.display_prompt
    assert "full-body framing" in prepared.display_prompt
    assert "original camera distance" in prepared.display_prompt
    assert "manter mood clean" in prepared.display_prompt
    assert prepared.use_structured_shell is False
    assert prepared.include_source_prompt_context is False
    assert "Preserve garment silhouette" in prepared.display_prompt


def test_build_angle_transform_prompt_supports_agentic_soft_turn_without_canonical_target() -> None:
    plan = build_angle_transform_plan(
        ViewTransformDirective(
            view_intent="soft_turn",
            view_target_hint=None,
            turn_hint_degrees=None,
            distance_intent="closer",
            pose_freedom="flexible",
            framing_lock=True,
            camera_height_lock=True,
            garment_identity_lock=True,
            source="command_center",
        ),
        requested_text="mudar angulo",
        source_shot_type="medium",
    )
    prepared = build_guided_angle_prompt(plan, extra_direction=None)

    assert "subtle three-quarter camera angle" in prepared.display_prompt
    assert "slightly closer camera distance" in prepared.display_prompt
    assert "same overall shot family" in prepared.display_prompt
    assert "minimal natural body adjustment" in prepared.display_prompt.lower()
    assert prepared.flow_mode == "guided_angle"


def test_build_angle_transform_prompt_preserves_view_when_only_distance_changes() -> None:
    plan = build_angle_transform_plan(
        ViewTransformDirective(
            view_intent="preserve",
            view_target_hint=None,
            turn_hint_degrees=None,
            distance_intent="closer",
            pose_freedom="locked",
            framing_lock=True,
            camera_height_lock=True,
            garment_identity_lock=True,
            source="command_center",
        ),
        requested_text="mais proximo",
        source_shot_type="medium",
    )
    prepared = build_guided_angle_prompt(plan, extra_direction=None)

    assert "current viewing angle and overall shot composition as the baseline" in prepared.display_prompt
    assert "slightly closer camera distance as the primary change" in prepared.display_prompt
    assert "without introducing a new camera angle or subject rotation" in prepared.display_prompt
    assert "subtle three-quarter camera angle" not in prepared.display_prompt
    assert "camera repositioning around the subject" not in prepared.display_prompt


def test_build_angle_transform_prompt_back_view_stays_camera_first() -> None:
    plan = build_angle_transform_plan(
        ViewTransformDirective(
            view_intent="back_view",
            view_target_hint="back",
            turn_hint_degrees=None,
            distance_intent="farther",
            pose_freedom="locked",
            framing_lock=True,
            camera_height_lock=True,
            garment_identity_lock=True,
            source="command_center",
        ),
        requested_text="mostrar costas",
        source_shot_type="wide",
    )
    prepared = build_guided_angle_prompt(plan, extra_direction=None)

    assert "clean full back view" in prepared.display_prompt
    assert "back-facing camera viewpoint around the subject" in prepared.display_prompt
    assert "not by turning the subject as the main solution" in prepared.display_prompt
    assert "body stance, torso orientation, and pose structure" in prepared.display_prompt
    assert prepared.model_prompt == prepared.display_prompt
