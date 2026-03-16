from __future__ import annotations

import sys
import types
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Stub mínimo para permitir import do módulo sem dependência do SDK no ambiente de teste.
google_mod = types.ModuleType("google")
genai_mod = types.ModuleType("google.genai")
genai_types_mod = types.ModuleType("google.genai.types")
genai_mod.types = genai_types_mod
google_mod.genai = genai_mod
sys.modules.setdefault("google", google_mod)
sys.modules.setdefault("google.genai", genai_mod)
sys.modules.setdefault("google.genai.types", genai_types_mod)

# Evita carregar SDK/config reais neste teste unitário de montagem de texto.
gemini_client_stub = types.ModuleType("agent_runtime.gemini_client")
gemini_client_stub.generate_structured_json = lambda *args, **kwargs: {}
sys.modules.setdefault("agent_runtime.gemini_client", gemini_client_stub)

from agent_runtime.fidelity_gate import build_targeted_repair_prompt


def test_targeted_repair_prompt_is_localized_and_hierarchical() -> None:
    prompt = build_targeted_repair_prompt(
        gate_result={
            "issue_codes": ["texture_pattern_drift", "stripe_order_drift", "low_garment_readability"],
        },
        structural_contract={
            "front_opening": "open",
            "sleeve_type": "cape_like",
            "silhouette_volume": "draped",
            "hem_shape": "cocoon",
            "edge_contour": "soft_curve",
            "opening_continuity": "continuous",
        },
        set_detection={},
    )

    lowered = prompt.lower()
    assert "localized garment-only fidelity correction" in lowered
    assert "goal: correct only visible garment regions that drifted from the references." in lowered
    assert "priority rule: keep current garment geometry and all non-garment elements unchanged." in lowered
    assert "allowed edits:" in lowered
    assert "do not recompose the scene or move the subject." in lowered
    assert "re-render the exact garment geometry" not in lowered
    assert "keep the front opening visible and unchanged." in lowered
    assert "do not create separate sleeves" in lowered


def test_targeted_repair_prompt_filters_off_scope_model_patch() -> None:
    prompt = build_targeted_repair_prompt(
        gate_result={
            "issue_codes": ["texture_pattern_drift"],
            "recommended_prompt_patch": "Change background lighting and camera angle, then sharpen the garment.",
        },
        structural_contract={"front_opening": "open"},
        set_detection={},
    )

    lowered = prompt.lower()
    assert "change background lighting and camera angle" not in lowered


def test_targeted_repair_prompt_keeps_local_model_patch() -> None:
    prompt = build_targeted_repair_prompt(
        gate_result={
            "issue_codes": ["texture_pattern_drift"],
            "recommended_prompt_patch": "Tighten stitch definition on the chest panel only.",
        },
        structural_contract={"front_opening": "open"},
        set_detection={},
    )

    lowered = prompt.lower()
    assert "tighten stitch definition on the chest panel only." in lowered
