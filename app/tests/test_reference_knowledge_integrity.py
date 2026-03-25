"""
Teste de integridade para REFERENCE_KNOWLEDGE.

Garante que a composição das seções funcionais (_RK_*) produz
exatamente o mesmo conteúdo que o valor monolítico original.
Previne regressão ao editar seções individuais.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.constants import (
    REFERENCE_KNOWLEDGE,
    _RK_HEADER,
    _RK_TERM_MAPPING,
    _RK_GARMENT_VOCABULARY,
    _RK_SHOT_COMPOSITION,
    _RK_MODEL_AND_SCENE,
    _RK_REALISM_LEVERS,
)


def test_composition_equals_concatenation() -> None:
    """REFERENCE_KNOWLEDGE deve ser a concatenação exata das 6 seções."""
    composed = (
        _RK_HEADER
        + _RK_TERM_MAPPING
        + _RK_GARMENT_VOCABULARY
        + _RK_SHOT_COMPOSITION
        + _RK_MODEL_AND_SCENE
        + _RK_REALISM_LEVERS
    )
    assert REFERENCE_KNOWLEDGE == composed


def test_all_sections_present() -> None:
    """Cada seção funcional deve estar presente no REFERENCE_KNOWLEDGE final."""
    assert "[REFERENCE KNOWLEDGE" in REFERENCE_KNOWLEDGE
    assert "── BRAZILIAN TERM MAPPING" in REFERENCE_KNOWLEDGE
    assert "── GARMENT DESCRIPTION" in REFERENCE_KNOWLEDGE
    assert "── SHOT COMPOSITION RULES" in REFERENCE_KNOWLEDGE
    assert "── MODEL & SCENE" in REFERENCE_KNOWLEDGE
    assert "── REALISM LEVERS" in REFERENCE_KNOWLEDGE


def test_section_order_preserved() -> None:
    """As seções devem aparecer na ordem funcional correta."""
    indices = [
        REFERENCE_KNOWLEDGE.index("BRAZILIAN TERM MAPPING"),
        REFERENCE_KNOWLEDGE.index("GARMENT DESCRIPTION"),
        REFERENCE_KNOWLEDGE.index("SHOT COMPOSITION RULES"),
        REFERENCE_KNOWLEDGE.index("MODEL & SCENE"),
        REFERENCE_KNOWLEDGE.index("REALISM LEVERS"),
    ]
    assert indices == sorted(indices), f"Seções fora de ordem: {indices}"


def test_known_content_fingerprints() -> None:
    """Marcadores de conteúdo que devem existir para detectar perda acidental."""
    # Vocabulário de domínio
    assert "flat-knit cotton pullover" in REFERENCE_KNOWLEDGE
    assert "brushed-back fleece cotton sweatshirt" in REFERENCE_KNOWLEDGE
    # Regra fotográfica
    assert "85mm lens, f/1.8" in REFERENCE_KNOWLEDGE
    assert "100mm macro lens" in REFERENCE_KNOWLEDGE
    # Realism lever
    assert "choose appropriate capture language" in REFERENCE_KNOWLEDGE
    assert "skin pores" in REFERENCE_KNOWLEDGE
    assert "Reference examples: natural side light" in REFERENCE_KNOWLEDGE
    assert "CAPTURE ARTIFACTS" not in REFERENCE_KNOWLEDGE
    # Cenários brasileiros
    assert "cobblestone street" in REFERENCE_KNOWLEDGE
    assert "botanical garden" in REFERENCE_KNOWLEDGE


def test_char_count_stable() -> None:
    """O tamanho total não deve mudar sem intenção (± 50 chars de margem)."""
    EXPECTED_CHARS = 6219
    MARGIN = 50
    actual = len(REFERENCE_KNOWLEDGE)
    assert abs(actual - EXPECTED_CHARS) <= MARGIN, (
        f"REFERENCE_KNOWLEDGE mudou de tamanho: esperado ~{EXPECTED_CHARS}, "
        f"atual {actual} (diff={actual - EXPECTED_CHARS})"
    )
