"""
Testes para o reference_selector simplificado (Fase 1 Prompt-First).

Valida:
1. Interface de retorno compatível com pipeline_v2.py
2. Deduplicação por hash
3. Derivação de identity_risk a partir da triagem unificada
4. Detecção de garment complexo
5. Todas as imagens vão para todos os subsets
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from unittest.mock import patch
from agent_runtime.reference_selector import (
    select_reference_subsets,
    _is_complex_garment,
    _derive_identity_risk_from_triage,
)


# ─── Helpers ──────────────────────────────────────────────────────────

MOCK_TRIAGE = {
    "garment_hint": "crochet cardigan with chevron pattern",
    "image_analysis": "flat garment photos showing texture and construction details",
    "structural_contract": {
        "garment_subtype": "standard_cardigan",
        "silhouette_volume": "relaxed",
        "sleeve_type": "set_in",
    },
    "set_detection": {},
    "garment_aesthetic": {},
    "lighting_signature": {},
    "look_contract": {},
}

FAKE_IMG_A = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"A"
FAKE_IMG_B = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"B"
FAKE_IMG_C = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"C"


# ─── Testes de Interface ─────────────────────────────────────────────

def test_empty_input():
    result = select_reference_subsets([])
    assert result["items"] == []
    assert result["stats"]["raw_count"] == 0
    assert result["unified_triage"] is None


@patch("agent_runtime.reference_selector._infer_unified_vision_triage", return_value=MOCK_TRIAGE)
def test_all_subsets_contain_all_unique_images(mock_triage):
    """Verifica que TODOS os subsets recebem TODAS as imagens únicas."""
    images = [FAKE_IMG_A, FAKE_IMG_B, FAKE_IMG_C]
    result = select_reference_subsets(images, filenames=["a.jpg", "b.jpg", "c.jpg"])

    assert result["stats"]["unique_count"] == 3
    assert result["stats"]["duplicate_count"] == 0

    # Todos os subsets devem ter exatamente 3 imagens
    for key in ["base_generation", "strict_single_pass", "edit_anchors", "identity_safe"]:
        assert len(result["selected_bytes"][key]) == 3, f"subset {key} deveria ter 3 imagens"
        assert len(result["selected_names"][key]) == 3, f"subset names {key} deveria ter 3 nomes"


@patch("agent_runtime.reference_selector._infer_unified_vision_triage", return_value=MOCK_TRIAGE)
def test_dedup_removes_duplicates(mock_triage):
    """Verifica que duplicatas por hash são removidas."""
    images = [FAKE_IMG_A, FAKE_IMG_A, FAKE_IMG_B]  # A aparece 2x
    result = select_reference_subsets(images, filenames=["a1.jpg", "a2.jpg", "b.jpg"])

    assert result["stats"]["unique_count"] == 2
    assert result["stats"]["duplicate_count"] == 1
    assert len(result["selected_bytes"]["base_generation"]) == 2


@patch("agent_runtime.reference_selector._infer_unified_vision_triage", return_value=MOCK_TRIAGE)
def test_unified_triage_returned(mock_triage):
    """Verifica que a triagem unificada é retornada intacta."""
    result = select_reference_subsets([FAKE_IMG_A])
    assert result["unified_triage"] == MOCK_TRIAGE
    mock_triage.assert_called_once()


@patch("agent_runtime.reference_selector._infer_unified_vision_triage", return_value=MOCK_TRIAGE)
def test_stats_fields_match_pipeline_v2_expectations(mock_triage):
    """Verifica que stats contém os campos que o pipeline_v2 consome."""
    result = select_reference_subsets([FAKE_IMG_A, FAKE_IMG_B])
    stats = result["stats"]

    required_fields = {
        "raw_count", "unique_count", "duplicate_count",
        "complex_garment", "small_input_mode",
        "identity_reference_risk",
    }
    for field in required_fields:
        assert field in stats, f"Campo {field} ausente em stats"


# ─── Testes de identity_risk ─────────────────────────────────────────

def test_identity_risk_low_for_flat_images():
    triage = {"image_analysis": "flat garment on white background, folded detail shot"}
    result = _derive_identity_risk_from_triage(triage, 3)
    assert result["identity_reference_risk"] == "low"


def test_identity_risk_elevated_for_worn_dominant():
    triage = {"image_analysis": "model wearing the garment, person posing in studio, front view of worn look"}
    result = _derive_identity_risk_from_triage(triage, 3)
    assert result["identity_reference_risk"] in {"medium", "high"}


def test_identity_risk_null_triage():
    result = _derive_identity_risk_from_triage(None, 0)
    assert result["identity_reference_risk"] == "low"


# ─── Testes de complex_garment ────────────────────────────────────────

def test_complex_garment_ruana():
    assert _is_complex_garment({"structural_contract": {"garment_subtype": "ruana_wrap"}})


def test_complex_garment_draped():
    assert _is_complex_garment({"structural_contract": {"silhouette_volume": "draped"}})


def test_not_complex_garment_pullover():
    assert not _is_complex_garment({"structural_contract": {"garment_subtype": "pullover"}})


def test_not_complex_garment_none():
    assert not _is_complex_garment(None)
