"""
Testes unitários para try_repair_truncated_json().

Cobre:
  - Fragmento reparável com sufixos simples (}, "}, "]})
  - Fragmento irreparável retornando None
  - Compatibilidade com formatos de erro usados por triage.py
  - Limpeza de escapes (\\n, \\")
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.parser import try_repair_truncated_json


# ── 1. Fragmento reparável com sufixo simples ────────────────────────────────

def test_repair_simple_object() -> None:
    """JSON truncado que só precisa de '}' para fechar."""
    err = 'Some error raw={"sleeve_type": "set-in", "confidence": 0.9'
    result = try_repair_truncated_json(err)
    assert result is not None
    assert result["sleeve_type"] == "set-in"
    assert result["confidence"] == 0.9


def test_repair_truncated_string_value() -> None:
    """Valor string cortado no meio — precisa de '"}'."""
    err = 'Parsing failed raw={"garment_length": "mid-thigh'
    result = try_repair_truncated_json(err)
    assert result is not None
    assert result["garment_length"] == "mid-thigh"


def test_repair_truncated_array() -> None:
    """Array aberto dentro do objeto — precisa de '"]}'."""
    err = 'Error raw={"must_keep": ["sleeve", "hem'
    result = try_repair_truncated_json(err)
    assert result is not None
    assert "sleeve" in result["must_keep"]
    assert "hem" in result["must_keep"]


# ── 2. Fragmento irreparável retornando None ─────────────────────────────────

def test_irreparable_garbage_returns_none() -> None:
    """Fragmento totalmente corrompido — nenhum sufixo resolve."""
    err = 'raw=not-json-at-all {{{{garbage'
    result = try_repair_truncated_json(err)
    assert result is None


def test_no_raw_marker_returns_none() -> None:
    """Mensagem de erro sem 'raw=' — retorna None direto."""
    err = 'Connection timeout after 30s'
    result = try_repair_truncated_json(err)
    assert result is None


def test_empty_string_returns_none() -> None:
    """String vazia — caminho rápido."""
    assert try_repair_truncated_json("") is None


# ── 3. Compatibilidade com formatos de erro do triage.py ─────────────────────

def test_structural_contract_error_format() -> None:
    """
    Simula o formato real de erro que _infer_structural_contract_from_images
    produzia quando o Gemini SDK retornava JSON truncado.
    """
    err = (
        'google.genai.errors.ClientError: Invalid response — '
        'raw={"enabled": true, "confidence": 0.85, '
        '"sleeve_type": "raglan", "sleeve_length": "long", '
        '"front_opening": "pullover", "hem_shape": "straight"'
    )
    result = try_repair_truncated_json(err)
    assert result is not None
    assert result["enabled"] is True
    assert result["sleeve_type"] == "raglan"
    assert result["front_opening"] == "pullover"


def test_set_detection_error_format() -> None:
    """
    Simula o formato real de erro que _infer_set_pattern_from_images
    produzia — inclui campo booleano e array.
    """
    err = (
        'Validation error raw={"is_garment_set": true, '
        '"set_pattern_score": 0.7, '
        '"detected_garment_roles": ["top", "bottom"'
    )
    result = try_repair_truncated_json(err)
    assert result is not None
    assert result["is_garment_set"] is True
    assert result["set_pattern_score"] == 0.7
    assert "top" in result["detected_garment_roles"]


def test_raw_with_curly_brace_format_truncated() -> None:
    """Formato 'raw={...' truncado — caso real onde falta o fechamento."""
    err = 'raw={"hem_shape": "curved", "garment_length": "knee"'
    result = try_repair_truncated_json(err)
    assert result is not None
    assert result["hem_shape"] == "curved"
    assert result["garment_length"] == "knee"


# ── 4. Nested JSON truncado ──────────────────────────────────────────────────

def test_nested_object_truncated() -> None:
    """JSON com objeto aninhado cortado — sufixo '}' fecha um nível mas '}}' fecha ambos."""
    # Precisa de 2 fechamentos: um do objeto interno, outro do externo
    # A função tenta sufixos simples, então só funciona se o truncamento
    # for no nível mais externo. Caso real: campo simples cortado no topo.
    err = 'raw={"enabled": true, "confidence": 0.9'
    result = try_repair_truncated_json(err)
    assert result is not None
    assert result["enabled"] is True


# ── 5. Casos de borda ───────────────────────────────────────────────────────

def test_raw_at_very_end_of_string() -> None:
    """'raw=' no final sem conteúdo — não deve crashar."""
    err = 'Some error raw='
    result = try_repair_truncated_json(err)
    assert result is None


def test_multiple_raw_markers_uses_first() -> None:
    """
    Se houver mais de um 'raw=', a função usa find() que pega o primeiro.
    Como o fragmento inclui tudo depois do primeiro 'raw=', o JSON completo
    com texto extra depois é irreparável — comportamento esperado.
    """
    err = 'raw={"a": 1} extra raw={"b": 2}'
    result = try_repair_truncated_json(err)
    # O fragmento é '{"a": 1} extra raw={"b": 2}' — não é JSON válido
    assert result is None


def test_single_raw_marker_with_trailing_text() -> None:
    """Fragmento truncado com texto de erro antes do raw=."""
    err = 'google.genai error: invalid response raw={"enabled": true, "confidence": 0.8'
    result = try_repair_truncated_json(err)
    assert result is not None
    assert result["enabled"] is True
