from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.constants import (
    BASE_SYSTEM_BLOCKS,
    OUTPUT_SYSTEM_BLOCKS,
    SCENARIO_SYSTEM_BLOCKS,
    SYSTEM_ANTI_PATTERNS,
    SYSTEM_CORE_RULES,
    SYSTEM_IDENTITY,
    SYSTEM_INSTRUCTION,
    SYSTEM_MODE_1_RULES,
    SYSTEM_MODE_2_RULES,
    SYSTEM_MODE_3_RULES,
    SYSTEM_OUTPUT_JSON_CONTRACT,
)
from agent_runtime.prompt_context import build_system_instruction


# ------------------------------------------------------------------
# Testes de composição estática (verifica que constants.py monta corretamente)
# ------------------------------------------------------------------

def test_system_instruction_keeps_expected_sections_in_order() -> None:
    sections = [
        SYSTEM_IDENTITY.strip(),
        SYSTEM_CORE_RULES.strip(),
        SYSTEM_ANTI_PATTERNS.strip(),
        SYSTEM_OUTPUT_JSON_CONTRACT.strip(),
        SYSTEM_MODE_1_RULES.strip(),
        SYSTEM_MODE_2_RULES.strip(),
        SYSTEM_MODE_3_RULES.strip(),
    ]

    indexes = [SYSTEM_INSTRUCTION.index(section) for section in sections]
    assert indexes == sorted(indexes)


def test_system_instruction_still_contains_key_behavioral_markers() -> None:
    assert 'Always start the canonical final prompt with "RAW photo,"' in SYSTEM_INSTRUCTION
    assert "Brazilian e-commerce fashion catalog photography" in SYSTEM_INSTRUCTION
    # MODE 1 uses semantic language instead of procedural "Treat"
    assert "Read the user's text as a fashion/e-commerce creative brief" in SYSTEM_INSTRUCTION
    assert "MODE 2 — User sent reference images" in SYSTEM_INSTRUCTION
    # Anti-patterns must be present
    assert "ANTI-PATTERNS" in SYSTEM_INSTRUCTION


def test_system_instruction_exposes_compositional_layers() -> None:
    assert BASE_SYSTEM_BLOCKS == [
        SYSTEM_IDENTITY.strip(),
        SYSTEM_CORE_RULES.strip(),
        SYSTEM_ANTI_PATTERNS.strip(),
    ]
    assert OUTPUT_SYSTEM_BLOCKS == [
        SYSTEM_OUTPUT_JSON_CONTRACT.strip(),
    ]
    assert SCENARIO_SYSTEM_BLOCKS == [
        SYSTEM_MODE_1_RULES.strip(),
        SYSTEM_MODE_2_RULES.strip(),
        SYSTEM_MODE_3_RULES.strip(),
    ]
    # POLICY_SYSTEM_BLOCKS foi removido na arquitetura soul-first
    # (thinking_level era meta-instrução ineficaz)
    assert len(BASE_SYSTEM_BLOCKS) == 3  # identity, core_rules, anti_patterns


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
    assert "photographic direction" in m1.lower()
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


def test_build_si_text_only_still_has_base_and_output() -> None:
    """Mesmo filtrando modos, base + output continuam presentes."""
    si = build_system_instruction(has_images=False, has_prompt=True)
    assert "Brazilian e-commerce fashion catalog photography" in si
    assert 'Always start the canonical final prompt with "RAW photo,"' in si


def test_build_si_no_compiler_leak() -> None:
    """OUTPUT CONTRACT não deve vazar detalhes de implementação."""
    si = build_system_instruction(has_images=False, has_prompt=True)
    assert "Used by compiler" not in si
    assert "GARMENT-ONLY" in si
