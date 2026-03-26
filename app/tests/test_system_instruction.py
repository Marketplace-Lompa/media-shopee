from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.constants import (
    BASE_ROLE,
    BASE_SYSTEM_BLOCKS,
    DOMAIN_FASHION_RULES,
    FASHION_PERSONA_ROLE,
    OUTPUT_JSON_REQUIREMENT,
    OUTPUT_SYSTEM_BLOCKS,
    POLICY_SYSTEM_BLOCKS,
    SCENARIO_SYSTEM_BLOCKS,
    SYSTEM_ANTI_PATTERNS,
    SYSTEM_CREATIVE_OPERATION_RULES,
    SYSTEM_CORE_RULES,
    SYSTEM_INSTRUCTION,
    SYSTEM_MODE_1_RULES,
    SYSTEM_MODE_2_RULES,
    SYSTEM_MODE_3_RULES,
    SYSTEM_OUTPUT_JSON_CONTRACT,
    SYSTEM_PROMPT_CONSOLIDATION,
    SYSTEM_REFERENCE_KNOWLEDGE_NOTE,
    SYSTEM_THINKING_LEVEL,
)
from agent_runtime.prompt_context import build_system_instruction


# ------------------------------------------------------------------
# Testes de composição estática (verifica que constants.py monta corretamente)
# ------------------------------------------------------------------

def test_system_instruction_keeps_expected_sections_in_order() -> None:
    sections = [
        BASE_ROLE.strip(),
        DOMAIN_FASHION_RULES.strip(),
        FASHION_PERSONA_ROLE.strip(),
        SYSTEM_CORE_RULES.strip(),
        SYSTEM_CREATIVE_OPERATION_RULES.strip(),
        SYSTEM_ANTI_PATTERNS.strip(),
        OUTPUT_JSON_REQUIREMENT.strip(),
        SYSTEM_OUTPUT_JSON_CONTRACT.strip(),
        SYSTEM_MODE_1_RULES.strip(),
        SYSTEM_MODE_2_RULES.strip(),
        SYSTEM_MODE_3_RULES.strip(),
        SYSTEM_THINKING_LEVEL.strip(),
        SYSTEM_REFERENCE_KNOWLEDGE_NOTE.strip(),
    ]

    indexes = [SYSTEM_INSTRUCTION.index(section) for section in sections]
    assert indexes == sorted(indexes)


def test_system_instruction_still_contains_key_behavioral_markers() -> None:
    assert 'Always start the canonical final prompt with "RAW photo,"' in SYSTEM_INSTRUCTION
    assert "Brazilian e-commerce fashion catalog photography" in SYSTEM_INSTRUCTION
    # MODE 1 now uses semantic language instead of procedural "Treat"
    assert "Read the user's text as a fashion/e-commerce creative brief" in SYSTEM_INSTRUCTION
    assert "MODE 2 — User sent reference images" in SYSTEM_INSTRUCTION
    assert "Consult the [REFERENCE KNOWLEDGE] block" in SYSTEM_INSTRUCTION
    assert "Always create a fresh solution inside the allowed territory" in SYSTEM_INSTRUCTION


def test_system_instruction_exposes_compositional_layers() -> None:
    assert BASE_SYSTEM_BLOCKS == [
        BASE_ROLE.strip(),
        DOMAIN_FASHION_RULES.strip(),
        FASHION_PERSONA_ROLE.strip(),
        SYSTEM_CORE_RULES.strip(),
        SYSTEM_CREATIVE_OPERATION_RULES.strip(),
        SYSTEM_ANTI_PATTERNS.strip(),
    ]
    assert OUTPUT_SYSTEM_BLOCKS == [
        OUTPUT_JSON_REQUIREMENT.strip(),
        SYSTEM_PROMPT_CONSOLIDATION.strip(),
        SYSTEM_OUTPUT_JSON_CONTRACT.strip(),
    ]
    assert SCENARIO_SYSTEM_BLOCKS == [
        "OPERATING MODES:",
        SYSTEM_MODE_1_RULES.strip(),
        SYSTEM_MODE_2_RULES.strip(),
        SYSTEM_MODE_3_RULES.strip(),
    ]
    assert POLICY_SYSTEM_BLOCKS == [
        SYSTEM_THINKING_LEVEL.strip(),
        SYSTEM_REFERENCE_KNOWLEDGE_NOTE.strip(),
    ]


# ------------------------------------------------------------------
# Testes de MODE 1 semântico (verifica que não há resíduos procedurais)
# ------------------------------------------------------------------

def test_mode_1_is_semantic_not_procedural() -> None:
    """MODE 1 não deve conter steps numerados, exemplos literais ou
    obrigações mecânicas de pipeline."""
    m1 = SYSTEM_MODE_1_RULES
    # Sem steps numerados
    assert "STEP 1" not in m1
    assert "STEP 2" not in m1
    assert "STEP 3" not in m1
    # Sem exemplos literais de tradução (pertencem ao REFERENCE_KNOWLEDGE)
    assert '"tricot"' not in m1
    assert '"moletom"' not in m1
    assert '"rua bonita"' not in m1


def test_mode_1_keeps_core_fashion_principles() -> None:
    """Conceitos essenciais devem sobreviver à reescrita."""
    m1 = SYSTEM_MODE_1_RULES
    assert "garment" in m1.lower()
    assert "protagonist" in m1.lower() or "showcasing" in m1.lower()
    assert "REFERENCE KNOWLEDGE" in m1
    assert "framing" in m1.lower()
    assert "Portuguese" in m1


# ------------------------------------------------------------------
# Testes do build_system_instruction condicional
# ------------------------------------------------------------------

def test_build_si_text_only_excludes_mode2_and_mode3() -> None:
    si = build_system_instruction(has_images=False, has_prompt=True)
    assert "MODE 1" in si
    assert "MODE 2" not in si
    assert "MODE 3" not in si


def test_build_si_with_images_and_text_includes_mode1_and_mode2() -> None:
    si = build_system_instruction(has_images=True, has_prompt=True)
    assert "MODE 1" in si
    assert "MODE 2" in si
    assert "MODE 3" not in si


def test_build_si_image_only_has_mode2_without_mode1() -> None:
    si = build_system_instruction(has_images=True, has_prompt=False)
    assert "MODE 2" in si
    assert "MODE 1" not in si
    assert "MODE 3" not in si


def test_build_si_no_input_has_mode3_only() -> None:
    si = build_system_instruction(has_images=False, has_prompt=False)
    assert "MODE 3" in si
    assert "MODE 1" not in si
    assert "MODE 2" not in si


def test_build_si_text_only_still_has_base_and_policy() -> None:
    """Mesmo filtrando modos, base + output + policy continuam presentes."""
    si = build_system_instruction(has_images=False, has_prompt=True)
    assert "Brazilian e-commerce fashion catalog photography" in si
    assert 'Always start the canonical final prompt with "RAW photo,"' in si
    assert "Consult the [REFERENCE KNOWLEDGE] block" in si


def test_build_si_no_compiler_leak() -> None:
    """OUTPUT CONTRACT não deve vazar detalhes de implementação."""
    si = build_system_instruction(has_images=False, has_prompt=True)
    assert "Used by compiler" not in si
    assert "Core garment identity" in si
