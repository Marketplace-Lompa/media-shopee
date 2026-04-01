"""
Testes para o reference_selector do fluxo upload vNext.

Valida:
1. Interface de retorno compatível com pipeline_v2.py
2. Deduplicação por hash
3. Derivação de identity_risk a partir da triagem unificada
4. Detecção de garment complexo
5. Replacement subset ordenado e limitado sem depender da ordem de upload
"""
import sys
import os
import types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("GOOGLE_AI_API_KEY", "test-key")


class _Blob:
    def __init__(self, mime_type: str | None = None, data: bytes | None = None):
        self.mime_type = mime_type
        self.data = data


class _Part:
    def __init__(self, text: str | None = None, inline_data: _Blob | None = None, media_resolution=None):
        self.text = text
        self.inline_data = inline_data
        self.media_resolution = media_resolution


class _Content:
    def __init__(self, role: str | None = None, parts=None):
        self.role = role
        self.parts = parts or []


class _Simple:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Client:
    def __init__(self, *args, **kwargs):
        self.models = _Simple(generate_content=lambda *a, **k: None)


google_mod = sys.modules.get("google") or types.ModuleType("google")
genai_mod = sys.modules.get("google.genai") or types.ModuleType("google.genai")
genai_types_mod = sys.modules.get("google.genai.types") or types.ModuleType("google.genai.types")

genai_types_mod.Blob = _Blob
genai_types_mod.Part = _Part
genai_types_mod.Content = _Content
genai_types_mod.MediaResolution = _Simple(MEDIA_RESOLUTION_HIGH="high")
genai_types_mod.GenerateContentConfig = _Simple
genai_types_mod.ImageConfig = _Simple
genai_types_mod.ThinkingConfig = _Simple
genai_types_mod.SafetySetting = _Simple
genai_types_mod.HarmCategory = _Simple(
    HARM_CATEGORY_SEXUALLY_EXPLICIT="sex",
    HARM_CATEGORY_HARASSMENT="harassment",
    HARM_CATEGORY_HATE_SPEECH="hate",
    HARM_CATEGORY_DANGEROUS_CONTENT="danger",
)
genai_types_mod.HarmBlockThreshold = _Simple(BLOCK_NONE="none")
genai_types_mod.Tool = _Simple
genai_types_mod.GoogleSearch = _Simple
genai_types_mod.SearchTypes = _Simple
genai_types_mod.ImageSearch = _Simple
genai_mod.Client = _Client
genai_mod.types = genai_types_mod
google_mod.genai = genai_mod

sys.modules["google"] = google_mod
sys.modules["google.genai"] = genai_mod
sys.modules["google.genai.types"] = genai_types_mod

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
FAKE_IMG_D = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"D"
FAKE_IMG_E = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"E"


# ─── Testes de Interface ─────────────────────────────────────────────

def test_empty_input():
    result = select_reference_subsets([])
    assert result["items"] == []
    assert result["stats"]["raw_count"] == 0
    assert result["unified_triage"] is None


@patch("agent_runtime.reference_selector._infer_unified_vision_triage", return_value=MOCK_TRIAGE)
@patch(
    "agent_runtime.reference_selector._analyze_image",
    side_effect=[
        {"score": 0.2, "luma": 100.0, "edge": 10.0, "ratio": 1.0},
        {"score": 0.9, "luma": 120.0, "edge": 50.0, "ratio": 1.0},
        {"score": 0.5, "luma": 110.0, "edge": 20.0, "ratio": 1.0},
        {"score": 0.7, "luma": 118.0, "edge": 30.0, "ratio": 1.0},
        {"score": 0.8, "luma": 125.0, "edge": 40.0, "ratio": 1.0},
    ],
)
def test_edit_anchors_are_sorted_and_capped(mock_analyze, mock_triage):
    """Verifica que o pack de replacement é ordenado por score local e limitado."""
    images = [FAKE_IMG_A, FAKE_IMG_B, FAKE_IMG_C, FAKE_IMG_D, FAKE_IMG_E]
    result = select_reference_subsets(
        images,
        filenames=["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"],
    )

    assert result["stats"]["unique_count"] == 5
    assert result["stats"]["duplicate_count"] == 0
    assert len(result["selected_bytes"]["base_generation"]) == 5
    assert len(result["selected_bytes"]["strict_single_pass"]) == 5
    assert len(result["selected_bytes"]["edit_anchors"]) == 4
    assert result["selected_names"]["edit_anchors"] == ["b.jpg", "e.jpg", "d.jpg", "c.jpg"]
    assert result["selected_names"]["identity_safe"] == result["selected_names"]["edit_anchors"]


@patch("agent_runtime.reference_selector._infer_unified_vision_triage", return_value=MOCK_TRIAGE)
def test_dedup_removes_duplicates(mock_triage):
    """Verifica que duplicatas por hash são removidas."""
    images = [FAKE_IMG_A, FAKE_IMG_A, FAKE_IMG_B]  # A aparece 2x
    result = select_reference_subsets(images, filenames=["a1.jpg", "a2.jpg", "b.jpg"])

    assert result["stats"]["unique_count"] == 2
    assert result["stats"]["duplicate_count"] == 1
    assert len(result["selected_bytes"]["base_generation"]) == 2


@patch(
    "agent_runtime.reference_selector._infer_unified_vision_triage",
    return_value={
        **MOCK_TRIAGE,
        "image_analysis": "model face person wearing garment and person posing in worn look",
    },
)
@patch(
    "agent_runtime.reference_selector._analyze_image",
    side_effect=[
        {"score": 0.2, "luma": 100.0, "edge": 10.0, "ratio": 1.0},
        {"score": 0.9, "luma": 120.0, "edge": 50.0, "ratio": 1.0},
        {"score": 0.5, "luma": 110.0, "edge": 20.0, "ratio": 1.0},
    ],
)
def test_high_identity_risk_caps_edit_anchors_to_two(mock_analyze, mock_triage):
    result = select_reference_subsets(
        [FAKE_IMG_A, FAKE_IMG_B, FAKE_IMG_C],
        filenames=["a.jpg", "b.jpg", "c.jpg"],
    )

    assert result["stats"]["identity_reference_risk"] == "high"
    assert result["selected_names"]["edit_anchors"] == ["b.jpg", "c.jpg"]
    assert len(result["selected_bytes"]["identity_safe"]) == 2


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
