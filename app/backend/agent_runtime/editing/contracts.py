from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ViewTransformDirective:
    view_intent: str = "preserve"
    view_target_hint: Optional[str] = None
    turn_hint_degrees: Optional[int] = None
    distance_intent: str = "preserve"
    pose_freedom: str = "locked"
    framing_lock: bool = True
    camera_height_lock: bool = True
    garment_identity_lock: bool = True
    source: str = "default"


@dataclass(frozen=True)
class PreparedEditPrompt:
    flow_mode: str
    edit_type: str
    display_prompt: str
    model_prompt: str
    change_summary_ptbr: str = ""
    confidence: float = 0.5
    structured_edit_goal: str = ""
    structured_preserve_clause: str = ""
    reference_item_description: str = ""
    include_source_prompt_context: bool = False
    include_reference_item_description: bool = False
    use_structured_shell: bool = False


@dataclass(frozen=True)
class ImageEditExecutionRequest:
    source_image_bytes: bytes
    prepared_prompt: PreparedEditPrompt
    aspect_ratio: str
    resolution: str
    session_id: Optional[str] = None
    source_session_id: Optional[str] = None
    source_prompt_context: Optional[str] = None
    reference_images_bytes: list[bytes] = field(default_factory=list)
    thinking_level: str = "HIGH"
    use_image_grounding: bool = False
    lock_person: bool = True
    edit_submode: Optional[str] = None
    source_shot_type: Optional[str] = None


@dataclass(frozen=True)
class ImageEditExecutionResult:
    session_id: str
    images: list[dict[str, Any]]
    edit_instruction: str
    edit_type: str
    change_summary: str
    optimized_prompt: str
    aspect_ratio: str
    resolution: str
    source_session_id: Optional[str] = None
    edit_session_id: Optional[str] = None
    edit_submode: Optional[str] = None

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "images": self.images,
            "edit_instruction": self.edit_instruction,
            "edit_type": self.edit_type,
            "change_summary": self.change_summary,
            "optimized_prompt": self.optimized_prompt,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "source_session_id": self.source_session_id,
            "edit_session_id": self.edit_session_id,
            "edit_submode": self.edit_submode,
        }
