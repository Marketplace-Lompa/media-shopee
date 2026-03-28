"""
Módulo Alma do Cenário — scene_soul.py

Responsável por entregar a diretiva criativa universal de cenário
para os modes que inventam ambiente. O agente recebe instruções de
COMO PENSAR um cenário brasileiro, não uma lista de locações prontas.
"""
from __future__ import annotations

from typing import Optional


_SCENE_SOUL_MODES = {"natural", "lifestyle", "editorial_commercial"}


def get_scene_soul(*, mode_id: Optional[str], has_images: bool) -> str:
    """Retorna a alma universal de cenário para modes criativos.

    Apenas os modes que realmente inventam ambiente consomem esta camada.
    """
    normalized = str(mode_id or "").strip().lower()
    if normalized not in _SCENE_SOUL_MODES:
        return ""

    reference_guard = ""
    if has_images:
        reference_guard = (
            "\n"
            "REFERENCE SCENE GUARD:\n"
            "  If the reference image contains a recognizable background or location,\n"
            "  treat it only as contrast. Do NOT copy the original backdrop, layout,\n"
            "  architecture, dominant composition, or spatial signature.\n"
            "  Invent a NEW Brazilian setting that serves the garment and the active mode better.\n"
        )

    mode_overlay = ""
    if normalized == "catalog_clean":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC SCENE LOGIC:\n"
            "  The setting MUST be a minimal, controlled studio backdrop with near-zero contextual interference.\n"
            "  The background exists ONLY to let the garment read cleanly — make it intentionally forgettable.\n"
            "  Use a neutral, tonal surface with restrained texture and low visual competition.\n"
            "  Do NOT invent a real-world location. The studio is not a place with personality — it is an absence of place.\n"
        )
    elif normalized == "natural":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC SCENE LOGIC:\n"
            "  Let the environment feel ordinary, inhabited, modest, and discovered in daily life.\n"
            "  Avoid spaces that read as curated, prestige-coded, institutionally calm, or selected for design value.\n"
            "  If the setting feels visually elevated or spatially self-conscious, it is wrong for natural mode.\n"
            "  Prefer signs of routine use, practical circulation, and lived wear over airy calm, retreat-like quiet, or tasteful threshold beauty.\n"
            "  Avoid hospitality-coded comfort or visually flattering calm that makes the place feel like a lifestyle retreat.\n"
        )
    elif normalized == "lifestyle":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC SCENE LOGIC:\n"
            "  The scene is a co-protagonist — it implies a reason for being there, not just a backdrop.\n"
            "  The environment should feel like a place real people choose to go, with social energy and lived texture.\n"
            "  Avoid both the quiet domesticity of 'natural' and the curated premium of 'editorial'.\n"
            "  The setting must support the model's activity — she is doing something HERE, and the place explains WHY.\n"
            "  YOU choose the specific location — the soul only requires it to feel socially alive and narratively coherent.\n"
        )

    return (
        "SCENE SOUL (universal scene invention directive — you MUST follow this to create the setting):\n"
        "You are inventing a Brazilian setting for this image, not selecting a location from a preset menu.\n"
        "Follow the active MODE_IDENTITY to decide how much the environment should speak, how visible it should be,\n"
        "and whether it should support, accompany, or co-star with the garment.\n"
        "\n"
        "SCENE INVENTION METHOD:\n"
        "  1. Start from the garment's personality, materiality, use occasion, and emotional temperature.\n"
        "  2. Let the active mode decide the ROLE of the environment — quiet support, lived context, or authored narrative.\n"
        "  3. Invent a Brazilian setting through physical evidence: materials, surfaces, spacing, light behavior,\n"
        "     ambient wear, and the rhythm of daily life. Build the setting from observed reality, not from labels.\n"
        "  4. Describe the setting through what is visibly there, not through generic shortcuts like city street,\n"
        "     prestige-coded interiors, hospitality shorthand, or generic escapist fantasy.\n"
        "  5. Keep the environment coherent with the garment and commercially believable for Brazil without cliché,\n"
        "     touristic shorthand, or repeating the same safe scene logic every time.\n"
        "\n"
        "MANDATORY SCENE DETAIL:\n"
        "  Your final prompt must make the setting legible as a physically believable environment through visible evidence.\n"
        "  Include ALL of these in fluent prose:\n"
        "  1. the kind of Brazilian environment this is, described through use, atmosphere, or context rather than a generic aesthetic label\n"
        "  2. at least one material or surface cue\n"
        "  3. at least one light or atmosphere cue\n"
        "  4. at least one spatial or background cue that shows how the place is organized\n"
        "  If these are missing, the scene is under-described.\n"
        f"{mode_overlay}"
        "\n"
        "VARIATION RULE:\n"
        "  Each generation must invent a new Brazilian setting from scratch.\n"
        "  Do not rely on recurring menus of places, neighborhoods, regions, or postcard cues.\n"
        "  Let variation emerge from material reality, light, and spatial character.\n"
        f"{reference_guard}"
        "CRITICAL RULES:\n"
        "  - The final prompt must make the scene feel physically real, not generically aesthetic.\n"
        "  - The setting must feel commercially believable for Brazil on the prompt surface, not only in hidden reasoning.\n"
        "  - The environment must be described as a concrete lived setting, not as a vague mood board.\n"
        "  - COMPLETENESS CHECK: before finalizing, verify that the prompt surface contains Brazilian setting logic + material + light + spatial cue.\n"
        "  - Do NOT echo these directives in the output — INVENT the place.\n"
    )
