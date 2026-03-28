from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal, Mapping, Optional


from agent_runtime.mode_profile import (
    ModeProfile,
    ResolvedOperationalProfile,
    get_mode_profile as _get_mode_profile,
    list_mode_profiles as _list_mode_profiles,
    resolve_operational_profile as _resolve_operational_profile,
)
from agent_runtime.preset_patch import PresetPatch


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
    "tropical_garden",
    "cafe_bistro",
    "beach_coastal",
    "hotel_pousada",
    "market_feira",
    "cultural_space",
    "rooftop_terrace",
]

FramingProfile = Literal[
    "full_body",
    "three_quarter",
    "editorial_mid",
    "detail_crop",
    "environmental_wide",
]

CameraType = Literal[
    "commercial_full_frame",
    "natural_digital",
    "editorial_fashion",
    "phone_social",
]

CaptureGeometry = Literal[
    "full_body_neutral",
    "three_quarter_eye_level",
    "three_quarter_slight_angle",
    "editorial_mid_low_angle",
    "environmental_wide_observer",
    "detail_close_observer",
]

LightingProfile = Literal[
    "studio_even",
    "natural_soft",
    "directional_daylight",
    "architectural_diffused",
    "ambient_lifestyle",
]

PoseEnergy = Literal[
    "static",
    "relaxed",
    "candid",
    "directed",
]

CastingProfile = Literal[
    "polished_commercial",
    "natural_commercial",
    "editorial_presence",
]


@dataclass(frozen=True)
class PresetSet:
    scenario_pool: ScenarioPool
    framing_profile: FramingProfile
    camera_type: CameraType
    capture_geometry: CaptureGeometry
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
        description="A peça é a estrela absoluta. Vitrine de loja premium — fundo neutro, pose estável, luz lisa, corpo inteiro. Zero distração.",
        presets=PresetSet(
            scenario_pool="studio_minimal",
            framing_profile="full_body",
            camera_type="commercial_full_frame",
            capture_geometry="full_body_neutral",
            lighting_profile="studio_even",
            pose_energy="static",
            casting_profile="polished_commercial",
        ),
    ),
    "natural": ModeConfig(
        id="natural",
        label="Natural",
        description="Uma pessoa real vestindo a peça. Foto de amiga no Instagram — cenário discreto, luz suave, pose natural, terrena e acessível.",
        presets=PresetSet(
            scenario_pool="neighborhood_commercial",
            framing_profile="three_quarter",
            camera_type="natural_digital",
            capture_geometry="three_quarter_eye_level",
            lighting_profile="natural_soft",
            pose_energy="relaxed",
            casting_profile="natural_commercial",
        ),
    ),
    "lifestyle": ModeConfig(
        id="lifestyle",
        label="Lifestyle",
        description="Vivendo o momento. Influencer em ação — cenário protagonista, gesture amplo, energia alta, storytelling visual aspiracional.",
        presets=PresetSet(
            scenario_pool="textured_city",
            framing_profile="environmental_wide",
            camera_type="natural_digital",
            capture_geometry="environmental_wide_observer",
            lighting_profile="ambient_lifestyle",
            pose_energy="candid",
            casting_profile="natural_commercial",
        ),
    ),
    "editorial_commercial": ModeConfig(
        id="editorial_commercial",
        label="Editorial Comercial",
        description="Moda como arte. Página de revista — composição deliberada, ângulo sofisticado, presença intensa, ambiência premium dirigida.",
        presets=PresetSet(
            scenario_pool="architecture_premium",
            framing_profile="editorial_mid",
            camera_type="editorial_fashion",
            capture_geometry="editorial_mid_low_angle",
            lighting_profile="architectural_diffused",
            pose_energy="directed",
            casting_profile="editorial_presence",
        ),
    ),
}


def list_modes() -> list[ModeConfig]:
    return list(MODE_REGISTRY.values())


def list_operational_mode_profiles() -> list[ModeProfile]:
    return _list_mode_profiles()


def get_mode(mode: Optional[str]) -> ModeConfig:
    normalized = str(mode or DEFAULT_TEXT_MODE).strip().lower()
    if normalized not in MODE_REGISTRY:
        normalized = DEFAULT_TEXT_MODE
    return MODE_REGISTRY[normalized]  # type: ignore[index]


def get_mode_profile(mode: Optional[str]) -> ModeProfile:
    return _get_mode_profile(get_mode(mode).id)


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
        camera_type=overrides.get("camera_type", overrides.get("camera_perspective", current.camera_type)),  # type: ignore[arg-type]
        capture_geometry=overrides.get("capture_geometry", current.capture_geometry),  # type: ignore[arg-type]
        lighting_profile=overrides.get("lighting_profile", current.lighting_profile),  # type: ignore[arg-type]
        pose_energy=overrides.get("pose_energy", current.pose_energy),  # type: ignore[arg-type]
        casting_profile=overrides.get("casting_profile", current.casting_profile),  # type: ignore[arg-type]
    )
    return replace(config, presets=patched)


def resolve_operational_mode_profile(
    mode: Optional[str],
    preset_patch: Optional[PresetPatch | str] = None,
) -> ResolvedOperationalProfile:
    return _resolve_operational_profile(
        mode_id=get_mode(mode).id,
        preset_patch=preset_patch,
    )


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
        "tropical_garden": "tropical garden or courtyard with organic warmth and natural shade",
        "cafe_bistro": "social everyday interior or threshold space with warm public intimacy",
        "beach_coastal": "open coastal air with luminous horizon depth",
        "hotel_pousada": "restrained hospitality environment with softened transitional calm",
        "market_feira": "public commerce environment with visible everyday density",
        "cultural_space": "institutional or civic interior with composed spatial calm",
        "rooftop_terrace": "elevated open-air urban context with broader city depth",
    }
    framing_map = {
        "full_body": "prefer full-body garment readability",
        "three_quarter": "prefer three-quarter commercial framing",
        "editorial_mid": "prefer mid-frame fashion composition",
        "detail_crop": "prefer detail-driven crop",
        "environmental_wide": "prefer wider framing with visible environment",
    }
    camera_type_map = {
        "commercial_full_frame": "use a clean full-frame commercial capture language",
        "natural_digital": "use a natural digital commercial capture language",
        "editorial_fashion": "use a fashion-forward editorial capture language",
        "phone_social": "use a believable mobile-first social capture language",
    }
    capture_geometry_map = {
        "full_body_neutral": "use neutral full-body capture geometry",
        "three_quarter_eye_level": "use eye-level three-quarter capture geometry",
        "three_quarter_slight_angle": "use a slight-angle three-quarter capture geometry",
        "editorial_mid_low_angle": "use a low-angle editorial mid-frame geometry",
        "environmental_wide_observer": "use a wider observer geometry with stronger environment context",
        "detail_close_observer": "use a close observer detail geometry",
    }
    lighting_map = {
        "studio_even": "favor even studio light with uniform garment readability",
        "natural_soft": "favor soft natural light with gentle contrast",
        "directional_daylight": "favor directional daylight with controlled commercial shape",
        "architectural_diffused": "favor diffused architectural light with refined spatial shape",
        "ambient_lifestyle": "favor believable ambient lifestyle light with a more lived-in feel",
    }
    pose_map = {
        "static": "keep pose energy stable, composed, and commercially human without mannequin stiffness",
        "relaxed": "keep pose energy relaxed and commercially natural",
        "candid": "keep pose energy candid and lightly spontaneous",
        "directed": "keep pose energy directed and intentional",
    }
    casting_map = {
        "polished_commercial": "model presence should feel polished, professional, and premium",
        "natural_commercial": "model presence should feel natural, warm, and commercially believable",
        "editorial_presence": "model presence should feel elevated, fashion-aware, and intentionally editorial",
    }
    p = mode_config.presets
    _PRESCRIPTIVE_MODES = {"catalog_clean"}

    if mode_config.id in _PRESCRIPTIVE_MODES:
        intro_line = "Treat these as hard commercial constraints for this job unless the user brief explicitly requests a compatible override:"
        scenario_line = f"- scenario constraint: {scenario_map.get(p.scenario_pool, '')}. Do not deviate from this backdrop type."
        lines = [
            f"Active visual mode: {mode_config.label}.",
            intro_line,
            scenario_line,
            f"- framing: {framing_map[p.framing_profile]}",
            f"- camera type: {camera_type_map[p.camera_type]}",
            f"- capture geometry: {capture_geometry_map[p.capture_geometry]}",
            f"- lighting: {lighting_map[p.lighting_profile]}",
            f"- pose energy: {pose_map[p.pose_energy]}",
            f"- casting: {casting_map[p.casting_profile]}",
        ]
    else:
        # Soul-driven modes: souls handle scene, pose, capture, casting, styling.
        # Presets omitted to avoid ambiguity and prescriptive references.
        lines = [
            f"Active visual mode: {mode_config.label}.",
            f"- lighting: {lighting_map[p.lighting_profile]}",
        ]
    return "\n".join(lines)
