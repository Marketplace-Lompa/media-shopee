from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_context import build_generate_context_text


def test_build_generate_context_text_preserves_core_block_order() -> None:
    context = build_generate_context_text(
        has_images=True,
        has_prompt=True,
        uploaded_images_count=1,
        user_prompt="foto premium de ecommerce",
        pool_context="pool ready",
        aspect_ratio="4:5",
        resolution="1536",
        profile="profile anchor",
        scenario="studio scene",
        pose="standing pose",
        diversity_target={"profile_id": "runtime-profile"},
        guided_enabled=False,
        guided_brief=None,
        guided_set_mode="unica",
        guided_set_detection={},
        structural_contract={
            "enabled": True,
            "front_opening": "open",
            "garment_length": "hip",
            "silhouette_volume": "regular",
            "hem_shape": "straight",
            "sleeve_type": "set-in",
            "must_keep": ["front opening"],
            "confidence": 0.9,
        },
        look_contract=None,
        grounding_research="grounding text",
        grounding_effective=True,
        grounding_context_hint="cardigan",
        grounding_mode="full",
        reference_knowledge="REFERENCE_KNOWLEDGE_BLOCK",
    )

    mode_index = context.index("<MODE>")
    pool_index = context.index("<POOL_CONTEXT>")
    output_index = context.index("<OUTPUT_PARAMETERS>")
    diversity_index = context.index("<DIVERSITY_TARGET>")
    grounding_index = context.index("<GROUNDING_RESULTS>")
    triage_hint_index = context.index("<TRIAGE_HINT>")
    grounding_constraints_index = context.index("<GROUNDING_CONSTRAINTS>")
    reference_index = context.index("REFERENCE_KNOWLEDGE_BLOCK")
    final_instruction_index = context.index("Return ONLY valid JSON matching the schema. No markdown, no explanation.")

    assert mode_index < pool_index < output_index < diversity_index
    assert diversity_index < grounding_index < triage_hint_index < grounding_constraints_index
    assert grounding_constraints_index < reference_index < final_instruction_index


def test_build_generate_context_text_skips_optional_blocks_when_inputs_are_empty() -> None:
    context = build_generate_context_text(
        has_images=False,
        has_prompt=False,
        uploaded_images_count=0,
        user_prompt=None,
        pool_context="",
        aspect_ratio="1:1",
        resolution="1024",
        profile="profile anchor",
        scenario="studio scene",
        pose="standing pose",
        diversity_target=None,
        guided_enabled=False,
        guided_brief=None,
        guided_set_mode="unica",
        guided_set_detection={},
        structural_contract={},
        look_contract=None,
        grounding_research="",
        grounding_effective=False,
        grounding_context_hint=None,
        grounding_mode="off",
        reference_knowledge="REFERENCE_KNOWLEDGE_BLOCK",
    )

    assert "<POOL_CONTEXT>" not in context
    assert "<GUIDED_BRIEF>" not in context
    assert "<STRUCTURAL_CONTRACT>" not in context
    assert "<LOOK_CONTRACT>" not in context
    assert "<GROUNDING_RESULTS>" not in context
    assert "<TRIAGE_HINT>" not in context
    assert "<GROUNDING_CONSTRAINTS>" not in context


def test_build_generate_context_text_uses_text_only_diversity_rules_without_reference_leak() -> None:
    context = build_generate_context_text(
        has_images=False,
        has_prompt=True,
        uploaded_images_count=0,
        user_prompt="vestido premium para ecommerce",
        pool_context="",
        aspect_ratio="4:5",
        resolution="1536",
        profile="contemporary Brazilian fashion model",
        scenario="clean boutique interior",
        pose="relaxed editorial stance",
        diversity_target={"profile_id": "runtime-profile"},
        guided_enabled=False,
        guided_brief=None,
        guided_set_mode="unica",
        guided_set_detection={},
        structural_contract={},
        look_contract=None,
        grounding_research="",
        grounding_effective=False,
        grounding_context_hint=None,
        grounding_mode="off",
        reference_knowledge="REFERENCE_KNOWLEDGE_BLOCK",
    )

    assert "TEXT-ONLY FASHION MODE:" in context
    assert "GARMENT-ONLY REFERENCE MODE — CRITICAL RULES:" not in context
    assert "Discard her completely." not in context
