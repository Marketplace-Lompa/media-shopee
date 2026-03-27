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
