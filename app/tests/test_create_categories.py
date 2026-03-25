from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_assets_registry import get_generate_prompt_assets
from create_categories import DEFAULT_CREATE_CATEGORY, normalize_create_category


def test_normalize_create_category_supports_default_and_aliases() -> None:
    assert normalize_create_category(None) == DEFAULT_CREATE_CATEGORY
    assert normalize_create_category("") == DEFAULT_CREATE_CATEGORY
    assert normalize_create_category("fashion") == "fashion"
    assert normalize_create_category("moda") == "fashion"


def test_normalize_create_category_rejects_invalid_values() -> None:
    try:
        normalize_create_category("beauty")
    except ValueError as exc:
        assert "category inválida" in str(exc)
    else:
        raise AssertionError("normalize_create_category deveria rejeitar categorias inválidas")


def test_get_generate_prompt_assets_returns_registered_fashion_assets() -> None:
    assets = get_generate_prompt_assets("fashion")

    assert assets.category == "fashion"
    assert isinstance(assets.system_instruction, str) and assets.system_instruction.strip()
    assert isinstance(assets.reference_knowledge, str) and assets.reference_knowledge.strip()
