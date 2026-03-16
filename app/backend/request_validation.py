"""
Validação central de parâmetros de request.
Mantém consistência entre rotas síncronas, assíncronas e SSE.
"""
from __future__ import annotations

from typing import Optional, Sequence

from config import VALID_ASPECT_RATIOS, VALID_N_IMAGES, VALID_RESOLUTIONS

VALID_MARKETPLACE_CHANNELS = {"shopee", "mercado_livre"}
VALID_MARKETPLACE_OPERATIONS = {"main_variation", "color_variations"}

_MARKETPLACE_CHANNEL_ALIASES = {
    "shopee": "shopee",
    "mercado_livre": "mercado_livre",
    "mercadolivre": "mercado_livre",
    "mercado livre": "mercado_livre",
    "ml": "mercado_livre",
}

_MARKETPLACE_OPERATION_ALIASES = {
    "main_variation": "main_variation",
    "main-variation": "main_variation",
    "main variation": "main_variation",
    "principal": "main_variation",
    "variacao_principal": "main_variation",
    "variacao principal": "main_variation",
    "color_variations": "color_variations",
    "color-variations": "color_variations",
    "color variations": "color_variations",
    "colors": "color_variations",
    "cores": "color_variations",
    "variacoes_cor": "color_variations",
    "variacoes de cor": "color_variations",
}


def validate_generation_params(
    *,
    aspect_ratio: str,
    resolution: str,
    n_images: int,
    valid_n_images: Optional[Sequence[int]] = None,
) -> None:
    allowed_n = list(valid_n_images or VALID_N_IMAGES)
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(f"aspect_ratio inválido. Use: {VALID_ASPECT_RATIOS}")
    if resolution not in VALID_RESOLUTIONS:
        raise ValueError(f"resolution inválida. Use: {VALID_RESOLUTIONS}")
    if n_images not in allowed_n:
        raise ValueError(f"n_images inválido. Use: {allowed_n}")


def normalize_marketplace_channel(raw: str) -> str:
    value = str(raw or "").strip().lower()
    normalized = _MARKETPLACE_CHANNEL_ALIASES.get(value)
    if normalized in VALID_MARKETPLACE_CHANNELS:
        return normalized
    raise ValueError(f"marketplace_channel inválido. Use: {sorted(VALID_MARKETPLACE_CHANNELS)}")


def normalize_marketplace_operation(raw: str) -> str:
    value = str(raw or "").strip().lower()
    normalized = _MARKETPLACE_OPERATION_ALIASES.get(value)
    if normalized in VALID_MARKETPLACE_OPERATIONS:
        return normalized
    raise ValueError(f"operation inválida. Use: {sorted(VALID_MARKETPLACE_OPERATIONS)}")
