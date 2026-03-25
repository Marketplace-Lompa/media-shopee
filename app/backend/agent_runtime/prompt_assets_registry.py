"""
Registro pragmático de assets de prompting por categoria.

Nesta fase o projeto ainda opera apenas em moda, mas o registry torna
explícita a fronteira de categoria sem forçar um framework maior.

Contrato: o caller normaliza a categoria antes de chamar o registry.
O registry recebe CreateCategory (já validado) e apenas faz lookup.
"""
from __future__ import annotations

from dataclasses import dataclass

from create_categories import CreateCategory
from agent_runtime.constants import REFERENCE_KNOWLEDGE, SYSTEM_INSTRUCTION


@dataclass(frozen=True)
class GeneratePromptAssets:
    category: CreateCategory
    system_instruction: str
    reference_knowledge: str


_FASHION_GENERATE_PROMPT_ASSETS = GeneratePromptAssets(
    category="fashion",
    system_instruction=SYSTEM_INSTRUCTION,
    reference_knowledge=REFERENCE_KNOWLEDGE,
)


def get_generate_prompt_assets(category: CreateCategory) -> GeneratePromptAssets:
    """Retorna os assets de prompting para a categoria já normalizada."""
    if category == "fashion":
        return _FASHION_GENERATE_PROMPT_ASSETS
    raise ValueError(f"Categoria sem prompt assets registrados: {category}")
