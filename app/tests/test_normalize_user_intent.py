"""
Testes unitários para normalize_user_intent().

Cobre:
  - Tradução pt-BR → EN técnico (garments, cenários, poses, modelo)
  - Substituição longest-first (evita match parcial)
  - Edge cases: vazio, já em inglês, truncamento
  - Contrato de retorno (keys fixas)
  - Detecção de tags encontradas
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.normalize_user_intent import normalize_user_intent


# ── 1. Contrato de retorno ───────────────────────────────────────────────────

def test_return_keys_always_present() -> None:
    """Resultado sempre tem as 4 chaves do contrato."""
    result = normalize_user_intent("qualquer coisa")
    assert "raw" in result
    assert "normalized" in result
    assert "intent_tags" in result
    assert "normalizer_source" in result
    assert result["normalizer_source"] == "rule_based_v1"


def test_empty_input_returns_empty_contract() -> None:
    """Input vazio retorna contrato com strings vazias e lista vazia."""
    result = normalize_user_intent("")
    assert result["raw"] == ""
    assert result["normalized"] == ""
    assert result["intent_tags"] == []


def test_none_input_returns_empty_contract() -> None:
    """Input None não crashar — retorna contrato vazio."""
    result = normalize_user_intent(None)  # type: ignore
    assert result["raw"] == ""
    assert result["normalized"] == ""


def test_whitespace_only_returns_empty() -> None:
    """Apenas espaços = input vazio."""
    result = normalize_user_intent("   ")
    assert result["raw"] == ""


# ── 2. Tradução de garments ──────────────────────────────────────────────────

def test_translate_moletom() -> None:
    """'moletom' → 'fleece hoodie'."""
    result = normalize_user_intent("moletom cinza")
    assert "fleece hoodie" in result["normalized"]
    assert "moletom" in result["intent_tags"]


def test_translate_tricot() -> None:
    """'tricot' → 'flat-knit pullover'."""
    result = normalize_user_intent("tricot rosa")
    assert "flat-knit pullover" in result["normalized"]


def test_translate_croche() -> None:
    """'croche' → 'crochet open-work'."""
    result = normalize_user_intent("blusa de croche branca")
    assert "crochet open-work" in result["normalized"]


def test_translate_alfaiataria() -> None:
    """'alfaiataria' → 'tailored structured fabric'."""
    result = normalize_user_intent("calça alfaiataria preta")
    assert "tailored structured fabric" in result["normalized"]


# ── 3. Tradução de cenários ──────────────────────────────────────────────────

def test_translate_praia() -> None:
    """'praia' → 'beach setting with natural sunlight'."""
    result = normalize_user_intent("foto na praia")
    assert "beach" in result["normalized"]
    assert "praia" in result["intent_tags"]


def test_translate_urbano() -> None:
    """'urbano' → 'urban city street setting'."""
    result = normalize_user_intent("estilo urbano")
    assert "urban" in result["normalized"]


def test_translate_fundo_branco() -> None:
    """'fundo branco' → 'clean seamless white background'."""
    result = normalize_user_intent("foto com fundo branco")
    assert "seamless white background" in result["normalized"]


# ── 4. Tradução de poses e composição ────────────────────────────────────────

def test_translate_corpo_inteiro() -> None:
    """'corpo inteiro' → 'full body wide shot'."""
    result = normalize_user_intent("foto corpo inteiro")
    assert "full body" in result["normalized"]


def test_translate_de_costas() -> None:
    """'de costas' → 'back view showing garment back details'."""
    result = normalize_user_intent("foto de costas")
    assert "back view" in result["normalized"]


def test_translate_andando() -> None:
    """'andando' → 'dynamic walking pose'."""
    result = normalize_user_intent("modelo andando na rua")
    assert "walking" in result["normalized"]


# ── 5. Tradução de modelo ────────────────────────────────────────────────────

def test_translate_loira() -> None:
    """'loira' → 'blonde hair'."""
    result = normalize_user_intent("modelo loira")
    assert "blonde" in result["normalized"]


def test_translate_pele_negra() -> None:
    """'pele negra' → 'dark skin tone'."""
    result = normalize_user_intent("modelo com pele negra")
    assert "dark skin tone" in result["normalized"]


# ── 6. Substituição longest-first ────────────────────────────────────────────

def test_longest_first_vestido_longo_vs_vestido() -> None:
    """'vestido longo' deve casar como unidade, não 'vestido' + 'longo' separados."""
    result = normalize_user_intent("vestido longo vermelho")
    assert "floor-length dress" in result["normalized"]


def test_longest_first_calca_pantalona() -> None:
    """'calça pantalona' deve casar inteira."""
    result = normalize_user_intent("calça pantalona azul")
    assert "wide-leg" in result["normalized"]


def test_longest_first_manga_bufante() -> None:
    """'manga bufante' deve casar inteira, não só 'manga'."""
    result = normalize_user_intent("blusa manga bufante")
    assert "puffed balloon sleeves" in result["normalized"]


# ── 7. Múltiplas substituições ───────────────────────────────────────────────

def test_multiple_substitutions() -> None:
    """Vários termos pt-BR na mesma frase."""
    result = normalize_user_intent("modelo loira com moletom na praia")
    assert "blonde" in result["normalized"]
    assert "fleece hoodie" in result["normalized"]
    assert "beach" in result["normalized"]
    assert len(result["intent_tags"]) >= 3


# ── 8. Texto que já está em inglês ───────────────────────────────────────────

def test_english_text_passes_through() -> None:
    """Texto em inglês sem termos mapeados passa sem mudanças."""
    result = normalize_user_intent("elegant silk dress in golden hour")
    assert result["normalized"] == "elegant silk dress in golden hour"
    assert result["intent_tags"] == []


# ── 9. Truncamento ──────────────────────────────────────────────────────────

def test_truncation_at_max_len() -> None:
    """Resultado acima de max_len é truncado na última palavra inteira."""
    long_text = "modelo " * 50  # ~350 chars
    result = normalize_user_intent(long_text, max_len=100)
    assert len(result["normalized"]) <= 100


def test_raw_field_preserves_original() -> None:
    """O campo 'raw' preserva o texto original (até 250 chars)."""
    original = "Vestido longo com renda na praia"
    result = normalize_user_intent(original)
    assert result["raw"] == original


# ── 10. Acentuação ──────────────────────────────────────────────────────────

def test_with_accent_calca() -> None:
    """'calça pantalona' com acento deve funcionar."""
    result = normalize_user_intent("calça pantalona")
    assert "wide-leg" in result["normalized"]


def test_without_accent_calca() -> None:
    """'calca pantalona' sem acento também deve funcionar (entrada duplicada no dict)."""
    result = normalize_user_intent("calca pantalona")
    assert "wide-leg" in result["normalized"]


def test_with_accent_transparencia() -> None:
    """'transparência' com acento."""
    result = normalize_user_intent("vestido com transparência")
    assert "sheer" in result["normalized"]
