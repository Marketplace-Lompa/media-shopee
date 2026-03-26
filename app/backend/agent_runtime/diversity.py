"""
Diversity sampling — diretivas abstratas para casting, cenário e pose.

Gera direções de diversidade via Name Blending + eixos semânticos.
NÃO injeta frases literais de cenário, pose ou lighting — essas direções
já vivem nos presets via MODE_PRESETS (describe_mode_defaults).

O papel deste módulo é exclusivamente gerar:
  1. Name Blending — ancora persona no espaço latente do modelo
  2. Presence axis — energia + tom (1 palavra cada)
  3. Preset resolution — resolve qual preset concreto usar por mode

Princípio: se o texto pode ser lido como frase de prompt, está errado.
O preset é uma intenção que o agente *resolve*, não um fragmento que ele *cola*.
"""
import random
from typing import Optional

from agent_runtime.casting_engine import select_brazilian_casting_profile
from agent_runtime.coordination_engine import select_coordination_state
from agent_runtime.capture_engine import select_capture_state
from agent_runtime.mode_profile import resolve_operational_profile
from agent_runtime.modes import (
    CastingProfile,
    ModeConfig,
    PoseEnergy,
    ScenarioPool,
)
from agent_runtime.preset_patch import PresetPatch
from agent_runtime.pose_engine import select_pose_state
from agent_runtime.scene_engine import select_scene_state
from agent_runtime.styling_completion_engine import select_styling_completion_state

_last_presence_idx_by_casting: dict[str, int] = {}
_last_tone_idx_by_casting: dict[str, int] = {}
_last_preset_choice_by_key: dict[str, int] = {}


_FIRST_NAMES = [
    "Camila", "Dandara", "Isadora", "Juliana", "Taís", "Valentina",
    "Yasmin", "Nayara", "Marina", "Luiza", "Bruna", "Aline",
    "Letícia", "Sofia", "Gabriela", "Fernanda", "Renata", "Bianca",
]

_SURNAMES = [
    "Silva", "Costa", "Souza", "Albuquerque", "Ribeiro",
    "Ferreira", "Lima", "Gomes", "Macedo", "Coutinho",
]

# Eixos de presença — UMA PALAVRA cada. Sem frases.
# O agente cruza energia + tom + name blending para resolver a persona.
_PRESENCE_ENERGY = {
    "polished_commercial": [
        "refined",
        "composed",
        "elevated",
        "polished",
    ],
    "natural_commercial": [
        "warm",
        "fresh",
        "grounded",
        "approachable",
    ],
    "editorial_presence": [
        "elevated",
        "intentional",
        "fashion-aware",
        "assured",
    ],
}

_PRESENCE_TONE = {
    "polished_commercial": [
        "premium",
        "polished",
        "commercial",
        "refined",
    ],
    "natural_commercial": [
        "believable",
        "softly-premium",
        "commercial",
        "natural",
    ],
    "editorial_presence": [
        "editorial",
        "fashion-aware",
        "composed",
        "premium",
    ],
}


_CASTING_FAMILY_BIASES: dict[str, tuple[str, ...]] = {
    "catalog_clean": (
        "br_minimal_premium",
        "br_warm_commercial",
        "br_afro_modern",
        "br_mature_elegant",
    ),
    "natural": (
        "br_everyday_natural",
        "br_everyday_afro",
        "br_everyday_mature",
        "br_social_creator",
        "br_social_afro",
        "br_social_mature",
        "br_warm_commercial",
    ),
    "lifestyle": (
        "br_social_creator",
        "br_social_afro",
        "br_social_mature",
        "br_everyday_natural",
        "br_everyday_afro",
        "br_everyday_mature",
    ),
    "editorial_commercial": (
        "br_soft_editorial",
        "br_afro_modern",
        "br_minimal_premium",
        "br_mature_elegant",
    ),
}


# ─── Preset pool por mode ─────────────────────────────────────────────
# Cada mode define QUAIS valores de preset são possíveis.
# O preset é um EIXO SEMÂNTICO, não texto de prompt.

_MODE_PRESET_POOLS: dict[str, dict[str, tuple[str, ...]]] = {
    "catalog_clean": {
        "scenario_pool": ("studio_minimal",),
        "pose_energy": ("static",),
        "casting_profile": ("polished_commercial",),
        "framing_profile": ("full_body",),
        "camera_type": ("commercial_full_frame",),
        "capture_geometry": ("full_body_neutral",),
        "lighting_profile": ("studio_even",),
    },
    "natural": {
        "scenario_pool": (
            "residential_daylight",
            "neighborhood_commercial",
            "nature_open_air",
            "curated_interior",
            "tropical_garden",
            "cafe_bistro",
            "hotel_pousada",
        ),
        "pose_energy": ("relaxed", "candid"),
        "casting_profile": ("natural_commercial",),
        "framing_profile": ("three_quarter", "full_body"),
        "camera_type": ("natural_digital",),
        "capture_geometry": ("three_quarter_eye_level", "three_quarter_slight_angle", "full_body_neutral"),
        "lighting_profile": ("natural_soft", "directional_daylight"),
    },
    "lifestyle": {
        "scenario_pool": (
            "textured_city",
            "nature_open_air",
            "neighborhood_commercial",
            "beach_coastal",
            "market_feira",
            "tropical_garden",
            "cafe_bistro",
            "rooftop_terrace",
        ),
        "pose_energy": ("candid", "relaxed"),
        "casting_profile": ("natural_commercial",),
        "framing_profile": ("environmental_wide", "three_quarter"),
        "camera_type": ("natural_digital", "phone_social"),
        "capture_geometry": ("environmental_wide_observer", "three_quarter_slight_angle", "three_quarter_eye_level"),
        "lighting_profile": ("ambient_lifestyle", "directional_daylight", "natural_soft"),
    },
    "editorial_commercial": {
        "scenario_pool": (
            "architecture_premium",
            "curated_interior",
            "cultural_space",
            "hotel_pousada",
            "rooftop_terrace",
        ),
        "pose_energy": ("directed", "relaxed"),
        "casting_profile": ("editorial_presence", "polished_commercial"),
        "framing_profile": ("editorial_mid", "three_quarter"),
        "camera_type": ("editorial_fashion", "commercial_full_frame"),
        "capture_geometry": ("editorial_mid_low_angle", "three_quarter_slight_angle"),
        "lighting_profile": ("architectural_diffused", "directional_daylight"),
    },
}

def _pick_non_repeating_index(length: int, last_idx: int) -> int:
    if length <= 1:
        return 0
    choices = [i for i in range(length) if i != last_idx]
    return random.choice(choices)


def _pick_from_pool(values: tuple[str, ...], *, key: str) -> str:
    if len(values) == 1:
        return values[0]
    last_idx = _last_preset_choice_by_key.get(key, -1)
    idx = _pick_non_repeating_index(len(values), last_idx)
    _last_preset_choice_by_key[key] = idx
    return values[idx]


def _sample_diversity_target(
    *,
    casting_profile: CastingProfile = "natural_commercial",
) -> tuple[str, str, str]:
    """
    Latent Space Casting via Name Blending.

    Retorna:
      - profile_hint: Name Blending (nomes brasileiros para ancorar persona)
      - presence_energy: 1 palavra de energia (ex: "warm", "refined")
      - presence_tone: 1 palavra de tom (ex: "commercial", "editorial")

    NÃO retorna cenário, pose ou lighting — essas direções vivem nos presets
    e são entregues ao agente via MODE_PRESETS (describe_mode_defaults).
    """
    presence_energies = _PRESENCE_ENERGY[casting_profile]
    presence_tones = _PRESENCE_TONE[casting_profile]

    last_presence_idx = _last_presence_idx_by_casting.get(casting_profile, -1)
    last_tone_idx = _last_tone_idx_by_casting.get(casting_profile, -1)
    presence_idx = _pick_non_repeating_index(len(presence_energies), last_presence_idx)
    tone_idx = _pick_non_repeating_index(len(presence_tones), last_tone_idx)
    _last_presence_idx_by_casting[casting_profile] = presence_idx
    _last_tone_idx_by_casting[casting_profile] = tone_idx

    n1, n2 = random.sample(_FIRST_NAMES, 2)
    surname = random.choice(_SURNAMES)
    presence = presence_energies[presence_idx]
    tone = presence_tones[tone_idx]

    # Name Blending — o formato que o Gemini reconhece para ancorar persona
    profile_hint = (
        f"features blend '{n1}' and '{n2} {surname}'"
    )

    return profile_hint, presence, tone


def _resolve_mode_presets(mode_config: ModeConfig) -> dict[str, str]:
    pools = _MODE_PRESET_POOLS.get(mode_config.id, {})
    return {
        "scenario_pool": _pick_from_pool(
            pools.get("scenario_pool", (mode_config.presets.scenario_pool,)),
            key=f"{mode_config.id}:scenario_pool",
        ),
        "pose_energy": _pick_from_pool(
            pools.get("pose_energy", (mode_config.presets.pose_energy,)),
            key=f"{mode_config.id}:pose_energy",
        ),
        "casting_profile": _pick_from_pool(
            pools.get("casting_profile", (mode_config.presets.casting_profile,)),
            key=f"{mode_config.id}:casting_profile",
        ),
        "framing_profile": _pick_from_pool(
            pools.get("framing_profile", (mode_config.presets.framing_profile,)),
            key=f"{mode_config.id}:framing_profile",
        ),
        "camera_type": _pick_from_pool(
            pools.get("camera_type", (mode_config.presets.camera_type,)),
            key=f"{mode_config.id}:camera_type",
        ),
        "capture_geometry": _pick_from_pool(
            pools.get("capture_geometry", (mode_config.presets.capture_geometry,)),
            key=f"{mode_config.id}:capture_geometry",
        ),
        "lighting_profile": _pick_from_pool(
            pools.get("lighting_profile", (mode_config.presets.lighting_profile,)),
            key=f"{mode_config.id}:lighting_profile",
        ),
    }


def build_mode_diversity_target(
    mode_config: ModeConfig,
    user_prompt: Optional[str] = None,
    preset_patch: Optional[PresetPatch | str] = None,
) -> dict:
    """
    Monta o diversity_target para um mode.

    Retorna apenas:
      - Name Blending (profile_hint) para persona
      - Eixos de presença (energy + tone)
      - Presets resolvidos (para uso interno do pipeline)
      - profile_id, mode (para telemetria)

    NÃO retorna cenário/pose/lighting como texto — essas direções
    já são entregues ao agente via describe_mode_defaults() no MODE_PRESETS.
    """
    resolved_presets = _resolve_mode_presets(mode_config)
    operational_profile = resolve_operational_profile(
        mode_id=mode_config.id,
        preset_patch=preset_patch,
    )
    profile_dict = operational_profile.to_dict()
    casting_key = resolved_presets["casting_profile"]
    casting_state = select_brazilian_casting_profile(
        seed_hint=(
            f"{mode_config.id}:"
            f"{resolved_presets['scenario_pool']}:"
            f"{resolved_presets['framing_profile']}:"
            f"{resolved_presets['camera_type']}:"
            f"{resolved_presets['capture_geometry']}:"
            f"{resolved_presets['lighting_profile']}:"
            f"{resolved_presets['pose_energy']}:"
            f"{casting_key}"
        ),
        user_prompt=user_prompt or mode_config.description,
        preferred_family_ids=list(_CASTING_FAMILY_BIASES.get(mode_config.id, ())),
        commit=False,
        operational_profile=profile_dict,
    )

    scene_state = select_scene_state(
        scenario_pool=resolved_presets["scenario_pool"],
        mode_id=mode_config.id,
        user_prompt=user_prompt,
        seed_hint=(
            f"{resolved_presets['scenario_pool']}:"
            f"{resolved_presets['lighting_profile']}:"
            f"{resolved_presets['framing_profile']}:"
            f"{resolved_presets['pose_energy']}"
        ),
        operational_profile=profile_dict,
    )
    capture_state = select_capture_state(
        framing_profile=resolved_presets["framing_profile"],
        camera_type=resolved_presets["camera_type"],
        capture_geometry=resolved_presets["capture_geometry"],
        mode_id=mode_config.id,
        user_prompt=user_prompt,
        seed_hint=(
            f"{resolved_presets['framing_profile']}:"
            f"{resolved_presets['camera_type']}:"
            f"{resolved_presets['capture_geometry']}:"
            f"{resolved_presets['pose_energy']}"
        ),
        operational_profile=profile_dict,
    )
    pose_state = select_pose_state(
        pose_energy=resolved_presets["pose_energy"],
        framing_profile=resolved_presets["framing_profile"],
        scenario_pool=resolved_presets["scenario_pool"],
        mode_id=mode_config.id,
        user_prompt=user_prompt,
        seed_hint=(
            f"{resolved_presets['pose_energy']}:"
            f"{resolved_presets['framing_profile']}:"
            f"{resolved_presets['scenario_pool']}:"
            f"{resolved_presets['capture_geometry']}"
        ),
        operational_profile=profile_dict,
    )
    styling_state = select_styling_completion_state(
        mode_id=mode_config.id,
        framing_profile=resolved_presets["framing_profile"],
        scenario_pool=resolved_presets["scenario_pool"],
        user_prompt=user_prompt,
        seed_hint=(
            f"{resolved_presets['framing_profile']}:"
            f"{resolved_presets['scenario_pool']}:"
            f"{resolved_presets['casting_profile']}:"
            f"{resolved_presets['pose_energy']}"
        ),
        operational_profile=profile_dict,
    )
    coordination_state = select_coordination_state(
        mode_id=mode_config.id,
        casting_state=casting_state,
        scene_state=scene_state,
        capture_state=capture_state,
        pose_state=pose_state,
        styling_state=styling_state,
        user_prompt=user_prompt,
        operational_profile=profile_dict,
    )

    profile_hint, presence_energy, presence_tone = _sample_diversity_target(
        casting_profile=casting_key,  # type: ignore[arg-type]
    )

    return {
        "profile_id": f"{mode_config.id}:{casting_key}",
        "profile_hint": profile_hint,
        "presence_energy": presence_energy,
        "presence_tone": presence_tone,
        "casting_state": {
            "age": casting_state.get("age", ""),
            "skin": casting_state.get("skin", ""),
            "face_structure": casting_state.get("face_structure", ""),
            "hair": casting_state.get("hair", ""),
            "makeup": casting_state.get("makeup", ""),
            "expression": casting_state.get("expression", ""),
            "presence": casting_state.get("presence", ""),
            "signature": casting_state.get("signature", ""),
            "difference_instruction": casting_state.get("difference_instruction", ""),
            "recent_avoid": list(casting_state.get("recent_avoid", []) or []),
        },
        "scene_state": scene_state,
        "capture_state": capture_state,
        "pose_state": pose_state,
        "styling_state": styling_state,
        "coordination_state": coordination_state,
        "mode": mode_config.id,
        "operational_profile": profile_dict,
        "preset_defaults": resolved_presets,
    }


def _is_modern_prompt_agent_diversity_target(target: Optional[dict]) -> bool:
    payload = target or {}
    return any(
        key in payload
        for key in (
            "profile_hint",
            "casting_state",
            "scene_state",
            "capture_state",
            "pose_state",
            "styling_state",
            "coordination_state",
            "operational_profile",
        )
    )


def _map_legacy_age_range(age_range: Optional[str]) -> str:
    normalized = str(age_range or "").strip()
    return {
        "18-24": "early 20s",
        "25-34": "late 20s to early 30s",
        "35-44": "late 30s to early 40s",
        "45+": "mid-40s or older",
    }.get(normalized, "")


def harmonize_diversity_target_for_mode(
    mode_config: ModeConfig,
    diversity_target: Optional[dict],
    *,
    user_prompt: Optional[str] = None,
    preset_patch: Optional[PresetPatch | str] = None,
) -> dict:
    """
    Bridge de compatibilidade para o Prompt Agent.

    - Se já receber o contrato novo (states latentes + profile_hint), mantém como está.
    - Se receber o contrato antigo do fluxo com imagens (profile/scenario/pose prompts),
      gera os states modernos a partir do mode atual e preserva metadados legados úteis.

    Objetivo: alinhar o norte novo de abstração sem quebrar callers antigos.
    """
    incoming = dict(diversity_target or {})
    if not incoming:
        return {}
    if _is_modern_prompt_agent_diversity_target(incoming):
        return incoming

    modern = build_mode_diversity_target(
        mode_config,
        user_prompt=user_prompt,
        preset_patch=preset_patch,
    )
    merged = dict(incoming)
    if incoming.get("profile_id"):
        merged["legacy_profile_id"] = incoming.get("profile_id")
    if incoming.get("profile_prompt"):
        merged["legacy_profile_prompt"] = incoming.get("profile_prompt")
    if incoming.get("scenario_id"):
        merged["legacy_scenario_id"] = incoming.get("scenario_id")
    if incoming.get("scenario_prompt"):
        merged["legacy_scenario_prompt"] = incoming.get("scenario_prompt")
    if incoming.get("pose_id"):
        merged["legacy_pose_id"] = incoming.get("pose_id")
    if incoming.get("pose_prompt"):
        merged["legacy_pose_prompt"] = incoming.get("pose_prompt")

    merged.update(modern)

    age_override = _map_legacy_age_range(incoming.get("age_range"))
    if age_override:
        casting_state = dict(merged.get("casting_state") or {})
        casting_state["age"] = age_override
        merged["casting_state"] = casting_state

    return merged
