from __future__ import annotations

from typing import Optional

from edit_agent import refine_edit_instruction

from agent_runtime.editing.contracts import PreparedEditPrompt


def prepare_freeform_edit_prompt(
    *,
    edit_instruction: str,
    source_image_bytes: bytes,
    source_prompt: Optional[str] = None,
    reference_images_bytes: Optional[list[bytes]] = None,
    category: str = "fashion",
) -> PreparedEditPrompt:
    agent_result = refine_edit_instruction(
        edit_instruction=edit_instruction,
        source_image_bytes=source_image_bytes,
        source_prompt=source_prompt,
        reference_images_bytes=reference_images_bytes,
        category=category,
    )
    edit_goal = str(
        agent_result.get("edit_delta_prompt")
        or agent_result.get("refined_prompt")
        or edit_instruction
    ).strip()
    preserve_clause = str(agent_result.get("preserve_clause") or "").strip()
    final_prompt = str(
        agent_result.get("final_prompt")
        or f"{edit_goal.rstrip('.')}. {preserve_clause}".strip()
    ).strip()
    try:
        confidence = max(0.0, min(1.0, float(agent_result.get("confidence", 0.5) or 0.5)))
    except (TypeError, ValueError):
        confidence = 0.5
    return PreparedEditPrompt(
        flow_mode="freeform",
        edit_type=str(agent_result.get("edit_type") or "general").strip() or "general",
        display_prompt=final_prompt,
        model_prompt=final_prompt,
        change_summary_ptbr=str(agent_result.get("change_summary_ptbr") or edit_instruction).strip(),
        confidence=round(confidence, 3),
        structured_edit_goal=edit_goal,
        structured_preserve_clause=preserve_clause,
        reference_item_description=str(agent_result.get("reference_item_description") or "").strip(),
        include_source_prompt_context=True,
        include_reference_item_description=True,
        use_structured_shell=True,
    )
