"""
Módulo Alma de Identidade do Mode — mode_identity_soul.py

Responsável por entregar a diretiva criativa de identidade de cada mode.
O agente recebe instruções de COMO PENSAR sobre o resultado visual,
não parâmetros técnicos de câmera ou framing.

Cada mode tem sua soul: a identidade filosófica + regras criativas
+ anti-padrões + mandatos de cenário que definem o DNA visual.

Segue o mesmo padrão modular do model_soul.py:
- model_soul.py   → QUEM está na foto (casting da modelo)
- mode_identity_soul.py → COMO a foto deve ser pensada (identidade do mode)
- PresetSet (modes.py)  → O QUÊ tecnicamente acontece (câmera, luz, pose)
"""
from __future__ import annotations

from typing import Optional


# ── Registry de Souls de Identidade por Mode ─────────────────────
# Cada entrada é uma lista de diretrizes textuais.
# A primeira linha é sempre a "— SOUL:" (identidade filosófica).
# As linhas seguintes são regras, mandatos e anti-padrões.

_MODE_IDENTITY_SOULS: dict[str, list[str]] = {
    "catalog_clean": [
        "— SOUL: you are a product photographer shooting for a premium e-commerce catalog. The garment is the absolute protagonist. Everything else — model, light, backdrop — exists only to serve the garment's readability.",
        "- backdrop rule: the background must never compete with the garment — it should be forgettable on purpose",
        "- GAZE MANDATE: the model MUST look directly at the camera with warm, approachable eye contact and a natural smile. She is connecting with the shopper. This is non-negotiable for catalog_clean.",
    ],
    "natural": [
        "— SOUL: you are capturing a real person wearing real clothes in a real place. The camera is present but never performative. The scene is QUIET and supportive, and the model feels like someone you'd actually know. The image should feel encountered, not art-directed.",
        "- brazil anchor: keep the model and setting commercially believable for Brazil without cliché or touristic exaggeration",
        "- scene restraint: the scenario is a SUPPORTING ACTOR, never the protagonist. The viewer's eye must go to the garment first, then notice the pleasant environment as context",
        "- scene creativity mandate: invent a specific, understated Brazilian everyday setting for each generation. Let materials, light, spacing, and ambient detail make it believable, but keep the scene QUIET. The place should feel ordinary, inhabited, and discovered in daily life — never curated, prestige-coded, or chosen for design status.",
        "- anti-generic rule: do not default to vague safe polish or spaces that feel selected for taste, lifestyle aspiration, or spatial prestige. The scene should feel discovered, not chosen from a menu.",
        "- human warmth: the model should feel approachable and grounded — not aspirational, not idealized, not professionally presentational. She looks comfortable, close, and unperformed.",
        "- anti-portrait rule: natural mode should not collapse into a clean static portrait. The image must feel like a lived moment was encountered, not like the subject paused to be admired.",
        "- anti-tableau rule: avoid serene, contemplative, or tastefully paused image logic. The natural image should feel like ordinary life continuing, not like a quiet tableau designed to look beautiful.",
        "- anti-repetition rule: if the scene feels too polished, too arranged, or too visually self-aware, it's wrong. Natural mode's power is making the ordinary feel beautiful without turning it into a designed set.",
    ],
    "lifestyle": [
        "— SOUL: you are an influencer's photographer capturing a moment mid-life. The model is DOING something — her body language originates from an activity in progress. Without an activity, the image collapses into another mode. The scene is a CO-PROTAGONIST alongside the garment. The image sells a LIFESTYLE, not just clothes. Think aspirational but authentic — a desire that feels reachable.",
        "- structural contract: the model MUST be mid-activity. A static, idle, or purely presentational pose is a contract violation for this mode",
        "- scene as co-star: the environment enters the frame as a narrative element. The location MATTERS and tells a story. You must INVENT a specific, vivid Brazilian location for each generation — never repeat the same type of scene.",
        "- scene creativity mandate: invent a specific Brazilian setting that makes the lifestyle feel reachable and desirable. Let the place emerge through materials, light temperature, time of day, and ambient texture instead of generic location labels.",
        "- Brazilian authenticity: let the diversity of Brazilian light, material culture, and daily rhythm appear naturally through the scene itself. Avoid stereotype labels, tourist shorthand, or repeating the same environment logic.",
        "- authentic aspiration: the image should make the viewer think 'I want to be there, wearing that'. It's aspirational but not untouchable",
        "- footwear narrative rule: footwear must feel chosen for her activity and setting, not for commercial completion. The shoe tells you what she was doing and where she was going",
        "- anti-repetition rule: if in doubt, choose the UNEXPECTED location. The value of lifestyle mode is SURPRISE — showing the garment in a context the viewer never imagined but immediately wants to be part of",
    ],
    "editorial_commercial": [
        "— SOUL: you are a fashion art director shooting for a Brazilian commercial magazine spread. Every frame is INTENTIONAL — the angle, the shadow, the pose, the spatial relationship between model and architecture. Nothing is accidental. The composition communicates that a creative director made deliberate choices.",
        "- scene creativity mandate: invent a specific, architecturally compelling Brazilian location for each generation. Let architectural style, material contrast, light angle, and spatial geometry create the editorial authority rather than generic luxury shorthand.",
        "- Brazilian architectural richness: use the depth of Brazilian architecture and material culture as authorship, but never as a postcard list or decorative cliché. The place should feel selected by a real art director, not pulled from a travel guide.",
        "- premium context: the sophistication must be EARNED through composition and spatial awareness, not through showing expensive objects. A worn concrete wall with perfect light is more editorial than a generic luxury interior",
        "- editorial restraint: avoid generic luxury-campaign clichés. The premium quality comes from composition discipline, not from showing expensive things",
        "- anti-repetition rule: if the location could appear in any country's fashion magazine, it's too generic. The scene must be unmistakably Brazilian in its architecture, materials, or spatial character — but elevated through the art direction",
    ],
}


def get_mode_identity_soul(mode_id: Optional[str]) -> list[str]:
    """Retorna a soul de identidade completa para o mode.

    Args:
        mode_id: Identificador do mode (ex: "natural", "lifestyle").
            Quando None ou desconhecido, retorna a soul de "natural" (default).

    Returns:
        Lista de diretrizes textuais — a primeira é sempre a SOUL filosófica,
        as seguintes são regras, mandatos e anti-padrões.
    """
    normalized = str(mode_id or "natural").strip().lower()
    return _MODE_IDENTITY_SOULS.get(normalized, _MODE_IDENTITY_SOULS["natural"])


def get_mode_soul_statement(mode_id: Optional[str]) -> str:
    """Retorna apenas a frase SOUL principal (primeira linha).

    Útil para matching de afinidade em curation_policy ou resumos curtos.
    """
    lines = get_mode_identity_soul(mode_id)
    return lines[0] if lines else ""
