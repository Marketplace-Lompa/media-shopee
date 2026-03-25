"""
Registro e normalização de categorias de criação.

Por enquanto o produto opera apenas em moda, mas este módulo cria o
ponto único de extensão para futuras categorias.
"""
from __future__ import annotations

from typing import Final, Literal, Optional

CreateCategory = Literal["fashion"]

DEFAULT_CREATE_CATEGORY: Final[CreateCategory] = "fashion"
VALID_CREATE_CATEGORIES: Final[tuple[CreateCategory, ...]] = (DEFAULT_CREATE_CATEGORY,)

_CREATE_CATEGORY_ALIASES: Final[dict[str, CreateCategory]] = {
    "fashion": "fashion",
    "moda": "fashion",
}


def normalize_create_category(raw: Optional[str]) -> CreateCategory:
    value = str(raw or "").strip().lower()
    if not value:
        return DEFAULT_CREATE_CATEGORY

    normalized = _CREATE_CATEGORY_ALIASES.get(value)
    if normalized in VALID_CREATE_CATEGORIES:
        return normalized

    raise ValueError(f"category inválida. Use: {list(VALID_CREATE_CATEGORIES)}")
