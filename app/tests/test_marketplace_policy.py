from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.marketplace_orchestrator import _compose_slot_prompt, _resolve_runtime_options
from agent_runtime.marketplace_policy import resolve_marketplace_policy


def test_marketplace_policy_exposes_runtime_defaults_and_guardrails() -> None:
    policy = resolve_marketplace_policy("shopee", "main_variation")
    runtime = policy.get("runtime_defaults") or {}
    guardrails = policy.get("prompt_guardrails") or []

    assert runtime.get("preset") == "catalog_clean"
    assert runtime.get("scene_preference") == "indoor_br"
    assert runtime.get("fidelity_mode") == "estrita"
    assert runtime.get("pose_flex_mode") == "controlled"
    assert len(guardrails) >= 3


def test_runtime_options_force_clean_defaults_when_legacy_values_are_used() -> None:
    policy = resolve_marketplace_policy("shopee", "main_variation")
    runtime = _resolve_runtime_options(
        policy=policy,
        preset="marketplace_lifestyle",
        scene_preference="auto_br",
        fidelity_mode="estrita",
        pose_flex_mode="controlled",
    )
    applied = runtime.get("applied") or {}

    assert applied.get("preset") == "catalog_clean"
    assert applied.get("scene_preference") == "indoor_br"


def test_marketplace_prompt_contains_anti_clone_and_set_rules() -> None:
    policy = resolve_marketplace_policy("shopee", "main_variation")
    prompt = _compose_slot_prompt(
        channel_hint=str(policy.get("channel_style_hint", "")),
        slot_id="hero_front",
        slot_prompt="Hero slot.",
        user_prompt=None,
        operation="main_variation",
        color_label=None,
        prompt_guardrails=list(policy.get("prompt_guardrails") or []),
    ).lower()

    assert "never copy or approximate the reference person's facial identity" in prompt
    assert "coordinated set members" in prompt


def test_marketplace_prompt_adds_turn_chain_when_anchor_is_active() -> None:
    policy = resolve_marketplace_policy("shopee", "main_variation")
    prompt = _compose_slot_prompt(
        channel_hint=str(policy.get("channel_style_hint", "")),
        slot_id="front_3_4",
        slot_prompt="3/4 slot.",
        user_prompt=None,
        operation="main_variation",
        color_label=None,
        prompt_guardrails=list(policy.get("prompt_guardrails") or []),
        continuity_anchor_active=True,
    ).lower()

    assert "continuity anchor" in prompt
    assert "same generated model identity" in prompt
