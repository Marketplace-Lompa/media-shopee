from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping, Optional


PresetScope = Literal[
    "scene-first",
    "capture-first",
    "styling-first",
    "pose-first",
]


@dataclass(frozen=True)
class PresetPatch:
    id: str
    label: str
    allowed_modes: tuple[str, ...]
    scope: PresetScope
    engine_deltas: Mapping[str, float] = field(default_factory=dict)
    exclusions: tuple[str, ...] = ()


_PRESET_PATCH_REGISTRY: dict[str, PresetPatch] = {
    "soft_wall_daylight": PresetPatch(
        id="soft_wall_daylight",
        label="Soft Wall Daylight",
        allowed_modes=("catalog_clean",),
        scope="capture-first",
        engine_deltas={
            "capture": 0.08,
            "scene": 0.04,
        },
        exclusions=("harsh directional shadow",),
    ),
    "urban_sidewalk_morning": PresetPatch(
        id="urban_sidewalk_morning",
        label="Urban Sidewalk Morning",
        allowed_modes=("natural", "lifestyle"),
        scope="scene-first",
        engine_deltas={
            "scene": 0.10,
            "capture": 0.03,
        },
        exclusions=("studio backdrop",),
    ),
    "confident_stride": PresetPatch(
        id="confident_stride",
        label="Confident Stride",
        allowed_modes=("natural", "lifestyle", "editorial_commercial"),
        scope="pose-first",
        engine_deltas={
            "pose": 0.12,
            "capture": 0.05,
        },
        exclusions=("static mannequin stance",),
    ),
}


def list_preset_patches() -> list[PresetPatch]:
    return list(_PRESET_PATCH_REGISTRY.values())


def get_preset_patch(preset_id: Optional[str]) -> Optional[PresetPatch]:
    if not preset_id:
        return None
    return _PRESET_PATCH_REGISTRY.get(str(preset_id).strip().lower())
