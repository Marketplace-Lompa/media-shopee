"""
Creative Brief Builder — metadata mínima para modos soul-driven.

Versão simplificada: todos os modes agora são governados pelas souls.
Os antigos engine states (scene, capture, pose, styling, coordination)
foram removidos — a direção criativa vem exclusivamente da stack de souls.

Este módulo preserva `build_creative_brief_for_mode` e
`harmonize_creative_brief_for_mode` com assinatura compatível,
retornando apenas metadata de identificação do mode e profile.
"""
from __future__ import annotations

from typing import Any, Optional

from agent_runtime.modes import ModeConfig
from agent_runtime.preset_patch import PresetPatch


def build_creative_brief_for_mode(
    mode_config: ModeConfig,
    user_prompt: Optional[str] = None,
    preset_patch: Optional[PresetPatch | str] = None,
) -> dict:
    """Retorna metadata mínima de identificação do mode.

    A direção criativa (cenário, modelo, pose, capture, styling)
    é agora responsabilidade exclusiva das souls e do Gemini agent.
    """
    return {
        "profile_id": f"{mode_config.id}:{mode_config.presets.casting_profile}",
        "mode": mode_config.id,
    }


def _is_modern_creative_brief(target: Optional[dict]) -> bool:
    payload = target or {}
    return any(
        key in payload
        for key in (
            "profile_id",
            "mode",
        )
    )


def _map_legacy_age_range(age_range: Optional[str]) -> str:
    normalized = str(age_range or "").strip()
    return {
        "18-24": "early 20s",
        "25-34": "late 20s to early 30s",
        "35-44": "late 30s to early 40s",
        "45+": "mid-40s or older",
    }.get(normalized, "")


def harmonize_creative_brief_for_mode(
    mode_config: ModeConfig,
    creative_brief: Optional[dict],
    *,
    user_prompt: Optional[str] = None,
    preset_patch: Optional[PresetPatch | str] = None,
) -> dict:
    incoming = dict(creative_brief or {})
    if not incoming:
        return {}
    if _is_modern_creative_brief(incoming):
        return incoming

    modern = build_creative_brief_for_mode(
        mode_config,
        user_prompt=user_prompt,
        preset_patch=preset_patch,
    )
    merged = dict(incoming)
    if incoming.get("profile_id"):
        merged["legacy_profile_id"] = incoming.get("profile_id")
    if incoming.get("profile_prompt"):
        merged["legacy_profile_prompt"] = incoming.get("profile_prompt")
    if incoming.get("scenario_id"):
        merged["legacy_scenario_id"] = incoming.get("scenario_id")
    if incoming.get("scenario_prompt"):
        merged["legacy_scenario_prompt"] = incoming.get("scenario_prompt")
    if incoming.get("pose_id"):
        merged["legacy_pose_id"] = incoming.get("pose_id")
    if incoming.get("pose_prompt"):
        merged["legacy_pose_prompt"] = incoming.get("pose_prompt")

    merged.update(modern)

    age_override = _map_legacy_age_range(incoming.get("age_range"))
    if age_override:
        merged["legacy_age_override"] = age_override

    return merged
