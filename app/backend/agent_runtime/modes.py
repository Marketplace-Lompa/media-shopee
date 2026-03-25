from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal, Mapping, Optional


ModeId = Literal[
    "catalog_clean",
    "natural",
    "lifestyle",
    "editorial_commercial",
]

ScenarioPool = Literal[
    "studio_minimal",
    "architecture_premium",
    "residential_daylight",
    "neighborhood_commercial",
    "textured_city",
    "nature_open_air",
    "curated_interior",
]

FramingProfile = Literal[
    "full_body",
    "three_quarter",
    "editorial_mid",
    "detail_crop",
    "environmental_wide",
]

CameraPerspective = Literal[
    "standard_prime",
    "wide_environmental",
    "compressed_portrait",
    "macro_detail",
    "phone_native",
]

LightingProfile = Literal[
    "studio_controlled",
    "natural_soft",
    "ambient_mixed",
    "dramatic_directional",
]

PoseEnergy = Literal[
    "static",
    "relaxed",
    "dynamic",
    "candid",
]

CastingProfile = Literal[
    "agency_polished",
    "commercial_natural",
    "casual_relational",
]


@dataclass(frozen=True)
class PresetSet:
    scenario_pool: ScenarioPool
    framing_profile: FramingProfile
    camera_perspective: CameraPerspective
    lighting_profile: LightingProfile
    pose_energy: PoseEnergy
    casting_profile: CastingProfile


@dataclass(frozen=True)
class ModeConfig:
    id: ModeId
    label: str
    description: str
    presets: PresetSet


DEFAULT_TEXT_MODE: ModeId = "natural"


MODE_REGISTRY: dict[ModeId, ModeConfig] = {
    "catalog_clean": ModeConfig(
        id="catalog_clean",
        label="Catálogo Clean",
        description="Leitura máxima da peça, pose controlada, cenário mínimo e composição limpa.",
        presets=PresetSet(
            scenario_pool="studio_minimal",
            framing_profile="full_body",
            camera_perspective="standard_prime",
            lighting_profile="studio_controlled",
            pose_energy="static",
            casting_profile="agency_polished",
        ),
    ),
    "natural": ModeConfig(
        id="natural",
        label="Natural",
        description="E-commerce humano e premium, menos rígido e mais leve.",
        presets=PresetSet(
            scenario_pool="residential_daylight",
            framing_profile="three_quarter",
            camera_perspective="standard_prime",
            lighting_profile="natural_soft",
            pose_energy="relaxed",
            casting_profile="commercial_natural",
        ),
    ),
    "lifestyle": ModeConfig(
        id="lifestyle",
        label="Lifestyle",
        description="Mais contexto, espontaneidade e sensação de vida real, sem perder venda.",
        presets=PresetSet(
            scenario_pool="textured_city",
            framing_profile="environmental_wide",
            camera_perspective="wide_environmental",
            lighting_profile="ambient_mixed",
            pose_energy="candid",
            casting_profile="commercial_natural",
        ),
    ),
    "editorial_commercial": ModeConfig(
        id="editorial_commercial",
        label="Editorial Comercial",
        description="Direção mais sofisticada, pose mais dirigida e cenário premium com foco em moda.",
        presets=PresetSet(
            scenario_pool="architecture_premium",
            framing_profile="editorial_mid",
            camera_perspective="compressed_portrait",
            lighting_profile="dramatic_directional",
            pose_energy="dynamic",
            casting_profile="agency_polished",
        ),
    ),
}


def list_modes() -> list[ModeConfig]:
    return list(MODE_REGISTRY.values())


def get_mode(mode: Optional[str]) -> ModeConfig:
    normalized = str(mode or DEFAULT_TEXT_MODE).strip().lower()
    if normalized not in MODE_REGISTRY:
        normalized = DEFAULT_TEXT_MODE
    return MODE_REGISTRY[normalized]  # type: ignore[index]


def resolve_mode_with_overrides(
    mode: Optional[str],
    overrides: Optional[Mapping[str, str]] = None,
) -> ModeConfig:
    config = get_mode(mode)
    if not overrides:
        return config

    current = config.presets
    patched = replace(
        current,
        scenario_pool=overrides.get("scenario_pool", current.scenario_pool),  # type: ignore[arg-type]
        framing_profile=overrides.get("framing_profile", current.framing_profile),  # type: ignore[arg-type]
        camera_perspective=overrides.get("camera_perspective", current.camera_perspective),  # type: ignore[arg-type]
        lighting_profile=overrides.get("lighting_profile", current.lighting_profile),  # type: ignore[arg-type]
        pose_energy=overrides.get("pose_energy", current.pose_energy),  # type: ignore[arg-type]
        casting_profile=overrides.get("casting_profile", current.casting_profile),  # type: ignore[arg-type]
    )
    return replace(config, presets=patched)


def preferred_shot_type_for_mode(mode: Optional[str]) -> str:
    framing = get_mode(mode).presets.framing_profile
    return preferred_shot_type_for_framing(framing)


def preferred_shot_type_for_framing(framing: str) -> str:
    if framing == "full_body":
        return "wide"
    if framing in {"detail_crop"}:
        return "close-up"
    return "medium"


def describe_mode_defaults(mode_config: ModeConfig) -> str:
    scenario_map = {
        "studio_minimal": "minimal controlled studio backdrop with almost no contextual interference",
        "architecture_premium": "architectural premium environment with stronger spatial identity",
        "residential_daylight": "believable residential interior with calm everyday polish",
        "neighborhood_commercial": "street-level commercial or neighborhood context with practical city life",
        "textured_city": "more tactile urban environment with visible real-world material texture",
        "nature_open_air": "open-air outdoor context with breathable natural depth",
        "curated_interior": "refined indoor commercial setting with deliberate styling restraint",
    }
    framing_map = {
        "full_body": "prefer full-body garment readability",
        "three_quarter": "prefer three-quarter commercial framing",
        "editorial_mid": "prefer mid-frame fashion composition",
        "detail_crop": "prefer detail-driven crop",
        "environmental_wide": "prefer wider framing with visible environment",
    }
    perspective_map = {
        "standard_prime": "use a neutral prime-lens commercial perspective",
        "wide_environmental": "use a wider environmental perspective with more context",
        "compressed_portrait": "use a compressed portrait perspective with stronger presence",
        "macro_detail": "use a close macro-style perspective for detail",
        "phone_native": "use a native mobile-camera perspective",
    }
    lighting_map = {
        "studio_controlled": "favor controlled studio light with uniform garment readability",
        "natural_soft": "favor soft natural light with gentle contrast",
        "ambient_mixed": "favor believable ambient light with a more lived-in feel",
        "dramatic_directional": "favor directional light with cleaner mood and stronger shape",
    }
    pose_map = {
        "static": "keep pose energy controlled and stable",
        "relaxed": "keep pose energy relaxed and commercially natural",
        "dynamic": "keep pose energy dynamic and intentional",
        "candid": "keep pose energy candid and lightly spontaneous",
    }
    casting_map = {
        "agency_polished": "model presence should feel polished, professional, and premium",
        "commercial_natural": "model presence should feel natural, warm, and commercially believable",
        "casual_relational": "model presence should feel relatable, easy, and less staged",
    }
    p = mode_config.presets
    lines = [
        f"Active visual mode: {mode_config.label}.",
        "Treat these as preferred defaults for this job unless the user brief clearly asks otherwise:",
        f"- scenario family: {scenario_map[p.scenario_pool]}",
        f"- framing: {framing_map[p.framing_profile]}",
        f"- camera perspective: {perspective_map[p.camera_perspective]}",
        f"- lighting: {lighting_map[p.lighting_profile]}",
        f"- pose energy: {pose_map[p.pose_energy]}",
        f"- casting: {casting_map[p.casting_profile]}",
    ]
    return "\n".join(lines)
