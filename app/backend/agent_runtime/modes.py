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
        "cafe_bistro": "neighborhood café, padaria, or bistro with warm social intimacy",
        "beach_coastal": "coastal boardwalk, beach proximity, or marina with open-air luminosity",
        "hotel_pousada": "boutique hotel or pousada with restrained hospitality charm",
        "market_feira": "open market, feira, or mercado with vibrant everyday abundance",
        "cultural_space": "museum, gallery, or cultural center with composed institutional calm",
        "rooftop_terrace": "rooftop terrace with elevated urban openness or skyline depth",
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
    # Modos criativos usam direção inspiracional; catalog_clean usa restrição rígida
    _PRESCRIPTIVE_MODES = {"catalog_clean"}
    if mode_config.id in _PRESCRIPTIVE_MODES:
        scenario_line = f"- scenario constraint: {scenario_map.get(p.scenario_pool, '')}. Do not deviate from this backdrop type."
    else:
        seed_desc = scenario_map.get(p.scenario_pool, "")
        scenario_line = (
            f"- scenario direction: use creative freedom to invent authentic Brazilian scenes "
            f"(indoor or outdoor) that match this mode's tone. "
            f"Seed inspiration: {seed_desc}. "
            f"Treat this seed as a starting point, not a boundary — freely explore "
            f"gardens, cafés, pousadas, rooftops, parks, feiras, cultural spaces, "
            f"coastal areas, courtyards, and more. Prioritize variety."
        )
    lines = [
        f"Active visual mode: {mode_config.label}.",
        "Treat these as preferred defaults for this job unless the user brief clearly asks otherwise:",
        scenario_line,
        f"- framing: {framing_map[p.framing_profile]}",
        f"- camera type: {camera_type_map[p.camera_type]}",
        f"- capture geometry: {capture_geometry_map[p.capture_geometry]}",
        f"- lighting: {lighting_map[p.lighting_profile]}",
        f"- pose energy: {pose_map[p.pose_energy]}",
        f"- casting: {casting_map[p.casting_profile]}",
    ]
    mode_notes = {
        "catalog_clean": [
            "— SOUL: you are a product photographer shooting for a premium e-commerce catalog. The garment is the absolute protagonist. Everything else — model, light, backdrop — exists only to serve the garment's readability.",
            "- styling completion: full-body fashion looks should feel commercially complete by default; avoid barefoot or unfinished styling unless the brief clearly asks for it",
            "- footwear policy: if feet are visible, prefer discreet commercially coherent footwear rather than barefoot presentation unless the brief explicitly requests barefoot",
            "- catalog discipline: keep the pose quiet and stable, but still human and premium rather than mannequin-rigid",
            "- backdrop rule: the background must never compete with the garment — it should be forgettable on purpose",
        ],
        "natural": [
            "— SOUL: you are capturing a real person wearing real clothes in a real place. Think of a friend who just sent you a photo from a café. The camera is there but it's not performing. The scene is QUIET — it supports the outfit without stealing attention. The model looks like someone you'd actually know.",
            "- brazil anchor: keep the model and setting commercially believable for Brazil without cliché or touristic exaggeration",
            "- scene restraint: the scenario is a SUPPORTING ACTOR, never the protagonist. The viewer's eye must go to the garment first, then notice the pleasant environment as context",
            "- scene creativity mandate: you must INVENT a specific, understated Brazilian location for each generation. Do NOT default to generic settings like 'cozy café' or 'quiet street'. Instead, think like a friend sharing a photo: WHERE exactly is she? The reception desk of a pousada in Paraty with worn wood and a guest book? A laundromat bench in Pinheiros with afternoon sun slicing through glass? A pharmacy line in Ipanema scrolling her phone? Be THAT specific with materials, light, and ambient detail — but keep the scene QUIET. The location whispers, it doesn't shout.",
            "- Brazilian everyday variety: Brazil's everyday spaces are visually rich and diverse. Rotate between: padarias with glass counters and chalkboards, apartment building lobbies with mailboxes, neighborhood praças with iron benches, açaí counters, bus stop shelters, bookshop aisles, pet shop waiting areas, residential elevator mirrors, university cantinas. Each generation must feel like a different slice of Brazilian daily life.",
            "- human warmth: the model should feel approachable and grounded — not aspirational, not idealized. She looks comfortable, not performative",
            "- capture discipline: keep the camera feel natural and contemporary; never expose preset terminology or mechanical capture labels in the final prompt",
            "- styling completion: when the framing is full-body, prefer discreet commercially coherent footwear rather than barefoot presentation unless the brief explicitly asks for it",
            "- anti-repetition rule: if the scene feels 'safe' or 'expected', it's wrong. Natural mode's power is making the mundane look beautiful — find beauty in unexpected everyday corners of Brazil",
        ],
        "lifestyle": [
            "— SOUL: you are an influencer's photographer capturing a moment mid-life. The model is DOING something — walking, arriving, pausing in conversation, adjusting sunglasses. The scene is a CO-PROTAGONIST alongside the garment. The image sells a LIFESTYLE, not just clothes. Think aspirational but authentic — a desire that feels reachable.",
            "- scene as co-star: the environment enters the frame as a narrative element. The location MATTERS and tells a story. You must INVENT a specific, vivid Brazilian location for each generation — never repeat the same type of scene.",
            "- scene creativity mandate: you are the creative director of this scene. Do NOT default to generic locations like 'urban plaza', 'garden courtyard', or 'city street'. Instead, think like a location scout: WHERE specifically in Brazil would this moment happen? A padaria counter in Vila Madalena at 7am with espresso steam? A ferry deck crossing Baía de Guanabara with salt wind? A hammock warehouse in Fortaleza with stacked fabric rolls? A vinyl record shop in Lapa with afternoon dust motes? Be THAT specific. Name materials, light temperature, time of day, ambient texture.",
            "- Brazilian authenticity: Brazil is vast and visually rich — Nordeste has different light, materials, and rhythm than Sul or Sudeste. Rotate between regional identities: tropical coastal, urban paulistano, rural mineiro, nordestino colorido, sulista europeu, amazônico, carioca, candango. Each generation should feel like a different corner of Brazil.",
            "- action energy: the model should never look like she's posing for a catalog. She's caught in a moment — mid-stride, laughing, turning. The gesture is open, the energy is alive",
            "- authentic aspiration: the image should make the viewer think 'I want to be there, wearing that'. It's aspirational but not untouchable",
            "- mobile-first feel: prefer a capture language that feels like a high-end phone photo or BTS shot rather than a studio setup",
            "- anti-repetition rule: if in doubt, choose the UNEXPECTED location. The value of lifestyle mode is SURPRISE — showing the garment in a context the viewer never imagined but immediately wants to be part of",
        ],
        "editorial_commercial": [
            "— SOUL: you are a fashion art director shooting for a Brazilian commercial magazine spread. Every frame is INTENTIONAL — the angle, the shadow, the pose, the spatial relationship between model and architecture. Nothing is accidental. The composition communicates that a creative director made deliberate choices.",
            "- pose authority: the model OWNS the frame. She is not standing still — she is COMMANDING space. Think fashion editorial poses: weight shifted to one hip, one hand on waist or touching hair, chin slightly lifted, shoulders angled. The body creates DYNAMIC LINES, never a static symmetrical silhouette. Arms must have PURPOSE — resting on a surface, adjusting clothing, framing the face, placed on hip. Arms hanging limp at both sides is FORBIDDEN in editorial.",
            "- directed intention: the pose should feel CHOREOGRAPHED — not stiff, but clearly directed. The model knows she's being photographed and owns the frame. Her expression should carry ATTITUDE: confident, knowing, magnetic. Not blank, not passive, not friendly-casual.",
            "- scene creativity mandate: you must INVENT a specific, architecturally compelling Brazilian location for each generation. Do NOT default to generic 'modern building' or 'luxury hotel lobby'. Instead, think like a magazine art director scouting locations: a brutalist concrete stairwell in the MASP building with afternoon shadows? The interior of a restored colonial sobrado in Salvador with crumbling blue azulejos? A mid-century modernist living room in a Niemeyer-inspired apartment with curved concrete and a single orchid? Be THAT specific — name the architectural style, the materials, the light angle, the spatial geometry.",
            "- Brazilian architectural richness: Brazil has world-class architecture spanning colonial, modernist, brutalist, tropical contemporary, and vernacular traditions. Rotate between: Art Deco cinemas in São Paulo, Burle Marx-landscaped terraces, colonial churches with baroque gold leaf, industrial lofts in converted warehouses, contemporary gallery white cubes with polished concrete, mid-century furniture showrooms, restored train station halls. Each generation should showcase a different architectural moment of Brazil.",
            "- premium context: the sophistication must be EARNED through composition and spatial awareness, not through showing expensive objects. A worn concrete wall with perfect light is more editorial than a generic luxury interior",
            "- fashion-forward capture: the camera language should convey fashion authority — deliberate angles, sophisticated framing, controlled depth. Prefer slightly low angles that elongate the model and create power. Never shoot straight-on at eye level like a passport photo.",
            "- editorial restraint: avoid generic luxury-campaign clichés. The premium quality comes from composition discipline, not from showing expensive things",
            "- anti-repetition rule: if the location could appear in any country's fashion magazine, it's too generic. The scene must be unmistakably Brazilian in its architecture, materials, or spatial character — but elevated through the art direction",
        ],
    }
    lines.extend(mode_notes.get(mode_config.id, []))
    return "\n".join(lines)
