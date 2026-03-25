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

from agent_runtime.modes import (
    CastingProfile,
    ModeConfig,
    PoseEnergy,
    ScenarioPool,
)

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
    "agency_polished": [
        "refined",
        "composed",
        "elevated",
        "polished",
    ],
    "commercial_natural": [
        "warm",
        "fresh",
        "grounded",
        "approachable",
    ],
    "casual_relational": [
        "easygoing",
        "relatable",
        "light",
        "casual",
    ],
}

_PRESENCE_TONE = {
    "agency_polished": [
        "premium",
        "editorial",
        "fashion-aware",
        "polished",
    ],
    "commercial_natural": [
        "believable",
        "softly-premium",
        "commercial",
        "natural",
    ],
    "casual_relational": [
        "easygoing",
        "lightly-styled",
        "everyday",
        "relatable",
    ],
}


# ─── Preset pool por mode ─────────────────────────────────────────────
# Cada mode define QUAIS valores de preset são possíveis.
# O preset é um EIXO SEMÂNTICO, não texto de prompt.

_MODE_PRESET_POOLS: dict[str, dict[str, tuple[str, ...]]] = {
    "catalog_clean": {
        "scenario_pool": ("studio_minimal",),
        "pose_energy": ("static",),
        "casting_profile": ("agency_polished",),
        "framing_profile": ("full_body", "three_quarter"),
        "camera_perspective": ("standard_prime",),
        "lighting_profile": ("studio_controlled",),
    },
    "natural": {
        "scenario_pool": ("residential_daylight", "neighborhood_commercial"),
        "pose_energy": ("relaxed",),
        "casting_profile": ("commercial_natural",),
        "framing_profile": ("three_quarter", "full_body"),
        "camera_perspective": ("standard_prime",),
        "lighting_profile": ("natural_soft",),
    },
    "lifestyle": {
        "scenario_pool": ("textured_city", "nature_open_air", "neighborhood_commercial"),
        "pose_energy": ("candid", "dynamic"),
        "casting_profile": ("commercial_natural", "casual_relational"),
        "framing_profile": ("environmental_wide", "editorial_mid"),
        "camera_perspective": ("wide_environmental",),
        "lighting_profile": ("ambient_mixed", "natural_soft"),
    },
    "editorial_commercial": {
        "scenario_pool": ("architecture_premium", "curated_interior"),
        "pose_energy": ("dynamic",),
        "casting_profile": ("agency_polished", "commercial_natural"),
        "framing_profile": ("editorial_mid", "three_quarter"),
        "camera_perspective": ("compressed_portrait",),
        "lighting_profile": ("dramatic_directional", "natural_soft"),
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
    casting_profile: CastingProfile = "commercial_natural",
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
        "camera_perspective": _pick_from_pool(
            pools.get("camera_perspective", (mode_config.presets.camera_perspective,)),
            key=f"{mode_config.id}:camera_perspective",
        ),
        "lighting_profile": _pick_from_pool(
            pools.get("lighting_profile", (mode_config.presets.lighting_profile,)),
            key=f"{mode_config.id}:lighting_profile",
        ),
    }


def build_mode_diversity_target(mode_config: ModeConfig) -> dict:
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
    casting_key = resolved_presets["casting_profile"]

    profile_hint, presence_energy, presence_tone = _sample_diversity_target(
        casting_profile=casting_key,  # type: ignore[arg-type]
    )

    return {
        "profile_id": f"{mode_config.id}:{casting_key}",
        "profile_hint": profile_hint,
        "presence_energy": presence_energy,
        "presence_tone": presence_tone,
        "mode": mode_config.id,
        "preset_defaults": resolved_presets,
    }
