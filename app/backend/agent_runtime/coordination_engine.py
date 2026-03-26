"""
Coordination engine for fashion image direction.

Objetivo:
- transformar bons estados latentes separados em uma assinatura única de direção
- alinhar casting + scene + capture + pose + styling em uma mesma imagem mental
- orientar a síntese final para soar menos montada e mais autoral
"""
from __future__ import annotations

from typing import Any, Optional


_MASTER_INTENT_BY_MODE = {
    "catalog_clean": "quiet premium catalog clarity",
    "natural": "warm believable commercial ease",
    "lifestyle": "lived-in social commercial energy",
    "editorial_commercial": "refined fashion-commercial control",
}

_BRIDGE_CLAUSE_BY_MODE = {
    "catalog_clean": "The restrained setting, grounded stance, and clean capture work together to keep the garment visually primary.",
    "natural": "The warm setting, relaxed body direction, and clean capture work together to keep the garment believable and visually primary.",
    "lifestyle": "The lived-in setting, natural body direction, and casual commercial capture work together to keep the garment central within the scene.",
    "editorial_commercial": "The directed pose, refined setting, and fashion-aware capture work together to keep the garment central within the image.",
}

_GUARDRAIL_SYNTHESIS_SUFFIX = {
    "strict_catalog": "Keep the image spare, product-led, and commercially resolved.",
    "natural_commercial": "Keep the image warm, believable, and commercially grounded.",
    "lifestyle_permissive": "Keep the image lived-in and energetic without losing garment readability.",
    "editorial_controlled": "Keep the image expressive and fashion-aware without letting the garment disappear.",
}


def select_coordination_state(
    *,
    mode_id: str,
    casting_state: Optional[dict[str, Any]] = None,
    scene_state: Optional[dict[str, Any]] = None,
    capture_state: Optional[dict[str, Any]] = None,
    pose_state: Optional[dict[str, Any]] = None,
    styling_state: Optional[dict[str, Any]] = None,
    user_prompt: Optional[str] = None,
    operational_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    casting_state = casting_state or {}
    scene_state = scene_state or {}
    capture_state = capture_state or {}
    pose_state = pose_state or {}
    styling_state = styling_state or {}
    profile = operational_profile or {}
    guardrail_profile = str(profile.get("guardrail_profile", "") or "")
    preset_scope = str(profile.get("preset_scope", "") or "")

    master_intent = _MASTER_INTENT_BY_MODE.get(mode_id, "coherent commercial image direction")
    presence_world_fusion = (
        f"{casting_state.get('presence', 'commercial presence')} inside "
        f"{scene_state.get('emotional_register', 'a believable world')}"
    )
    camera_body_fusion = (
        f"{capture_state.get('capture_feel', 'commercial capture')} matched to "
        f"{pose_state.get('gesture_intention', 'clear body direction')}"
    )
    styling_world_balance = (
        f"{styling_state.get('look_finish', 'resolved styling')} with "
        f"{scene_state.get('background_density', 'controlled background support')}"
    )
    garment_priority_rule = str(
        styling_state.get("hero_balance", "garment remains the visual hero")
    ).strip()
    visual_tension = (
        f"{capture_state.get('subject_separation', 'controlled separation')} + "
        f"{pose_state.get('stance_logic', 'clear stance logic')}"
    )
    synthesis_rule = (
        "All visible choices must feel like the same photograph with one commercial intention, "
        "not separate good ideas described in sequence."
    )
    if guardrail_profile:
        suffix = _GUARDRAIL_SYNTHESIS_SUFFIX.get(guardrail_profile, "")
        if suffix:
            synthesis_rule = f"{synthesis_rule} {suffix}"
    if preset_scope:
        synthesis_rule = f"{synthesis_rule} Let the preset act as a {preset_scope} bias, not as a second mode."
    coordination_signature = "|".join(
        [
            mode_id,
            master_intent,
            presence_world_fusion,
            camera_body_fusion,
            styling_world_balance,
            visual_tension,
        ]
    )
    bridge_clause = _BRIDGE_CLAUSE_BY_MODE.get(
        mode_id,
        "The setting, body direction, and capture work together to keep the garment visually primary.",
    )
    if preset_scope == "scene-first":
        bridge_clause = f"{bridge_clause.rstrip('.')}.\nThe setting may lead, but it must still serve the garment."
    elif preset_scope == "capture-first":
        bridge_clause = f"{bridge_clause.rstrip('.')}.\nCapture language may lead, but it must remain commercially disciplined."
    elif preset_scope == "pose-first":
        bridge_clause = f"{bridge_clause.rstrip('.')}.\nBody direction may lead, but garment readability must stay intact."
    elif preset_scope == "styling-first":
        bridge_clause = f"{bridge_clause.rstrip('.')}.\nStyling may resolve the image, but it must never outrank the garment."
    bridge_clause = bridge_clause.replace("\n", " ").strip()
    if not bridge_clause.endswith("."):
        bridge_clause += "."

    return {
        "master_intent": master_intent,
        "presence_world_fusion": presence_world_fusion,
        "camera_body_fusion": camera_body_fusion,
        "styling_world_balance": styling_world_balance,
        "garment_priority_rule": garment_priority_rule,
        "visual_tension": visual_tension,
        "synthesis_rule": synthesis_rule,
        "bridge_clause": bridge_clause,
        "guardrail_profile": guardrail_profile,
        "preset_scope": preset_scope or None,
        "coordination_signature": coordination_signature,
    }
