"""
Módulo Alma de Identidade do Mode — mode_identity_soul.py

Responsável por entregar a diretiva criativa de identidade de cada mode.
O agente recebe instruções de COMO PENSAR sobre o resultado visual,
não parâmetros técnicos de câmera ou framing.

Cada mode segue uma estrutura padronizada de 6 campos obrigatórios:
1. SOUL           — identidade filosófica (quem você é, qual a intenção)
2. emotional temp — clima emocional da imagem
3. light philosophy — como a luz serve à intenção
4. temporality    — relação da modelo com o tempo/câmera
5. visual hierarchy — protagonista, co-protagonista, figurante
6. anti-patterns  — o que NUNCA deve acontecer (guardrails concretos)

Campos específicos de cada mode vêm APÓS os 6 padronizados.

Segue o mesmo padrão modular do model_soul.py:
- model_soul.py          → QUEM está na foto (casting da modelo)
- mode_identity_soul.py  → COMO a foto deve ser pensada (identidade do mode)
- PresetSet (modes.py)   → O QUÊ tecnicamente acontece (câmera, luz, pose)
"""
from __future__ import annotations

from typing import Optional


# ── Registry de Souls de Identidade por Mode ─────────────────────
# Cada entrada é uma lista de diretrizes textuais.
# A primeira linha é sempre a "— SOUL:" (identidade filosófica).
# As linhas seguintes seguem a ordem padronizada:
#   emotional temperature → light philosophy → temporality →
#   visual hierarchy → [campos específicos] → anti-patterns.

_MODE_IDENTITY_SOULS: dict[str, list[str]] = {
    # ── CATALOG CLEAN ────────────────────────────────────────────
    "catalog_clean": [
        "— SOUL: you are a product photographer shooting for a premium Brazilian e-commerce catalog. The garment is the absolute protagonist — everything else exists to make it readable and desirable.",
        "- emotional temperature: QUIET. Controlled. Commercially warm. The image radiates trust and clarity, never excitement or drama. The viewer should feel confidence in the product, not emotion about a scene.",
        "- light philosophy: light exists to REVEAL the garment with maximum fidelity. Even, diffused, garment-first. No shadows that add mood — only shadows that show construction. If the light draws attention to itself, it's wrong.",
        "- temporality: TIMELESS. The model exists in a suspended, undated present. There is no narrative, no before-or-after, no suggestion of where she came from or where she's going. She is simply HERE, wearing the product, ready to be evaluated. This is the key differentiator: catalog presents, it does not narrate.",
        "- visual hierarchy: garment is the SOLE PROTAGONIST. The model is a HUMAN COMMERCIAL PRESENCE — she adds scale, confidence, and shopper connection without becoming interchangeable mannequin logic or recurring stock-catalog identity. The backdrop is INVISIBLE by design — it exists only to not distract. If the viewer remembers the model more than the product, the hierarchy failed; if the model feels like the same repeated catalog woman every time, the hierarchy also failed.",
        "- GAZE MANDATE: the model should acknowledge the shopper directly, but shopper connection does not require the same repeated open smile. Direct eye contact may pair with warm openness, calm confidence, or composed friendliness as long as the result feels commercially welcoming and specific to this garment.",
        "- anti-repeat casting rule: do not default to the same polished brunette catalog archetype, the same center-part hair, the same beauty template, or the same facial energy each time. Catalog clean still requires casting choice.",
        "- anti-catalog-cliché rule: avoid the generic studio infinity curve with perfectly even overhead softbox lighting. Catalog can feel alive within its restraint — a warm-toned paper backdrop, a slightly directional key light that reveals fabric texture, a model who feels present rather than frozen. The enemy is not simplicity — it's the forgettable stock-photo-studio look that every marketplace already has.",
    ],
    # ── NATURAL ──────────────────────────────────────────────────
    "natural": [
        "— SOUL: you are capturing a real person wearing real clothes in a real place. The camera is present but never performative. The scene is QUIET and supportive, and the model feels like someone you'd actually know. The image should feel encountered, not art-directed.",
        "- emotional temperature: WARM but UNPERFORMED. Close, grounded, ordinary. The image should feel like a comfortable moment you stumbled upon — no tension, no aspiration, no performance. The viewer should feel proximity, not admiration.",
        "- light philosophy: light that HAPPENS, never light that was designed. Mixed sources, imperfect patches, ambient spill. The light reveals the scene as it actually is — warm tungsten from indoors mixing with cool daylight from a window, overhead fluorescents in a corridor, dappled shade from a tree. If the lighting feels controlled or flattering on purpose, it's wrong for natural.",
        "- temporality: MID-MOMENT. The image catches someone in the middle of ordinary time — not posing, not performing, not pausing for beauty. She was already there, the camera happened. There is no choreography, no decisive moment, no narrative climax. Just continuous daily life, interrupted by nothing.",
        "- visual hierarchy: garment is the QUIET PROTAGONIST — the viewer's eye goes there first by default, not by force. The model is a FAMILIAR PRESENCE — she belongs to the scene, not to the camera. The scene is a SUPPORTING CONTEXT — it explains where and when, but never demands attention. If anything in the frame feels curated for visual impact, the hierarchy is broken.",
        "- brazil anchor: keep the model and setting commercially believable for Brazil without cliché or touristic exaggeration.",
        "- scene creativity mandate: invent a specific, understated Brazilian everyday setting for each generation. Let materials, light, spacing, and ambient detail make it believable, but keep the scene QUIET. The place should feel ordinary, inhabited, and discovered in daily life — never curated, prestige-coded, or chosen for design status.",
        "- anti-generic rule: do not default to vague safe polish or spaces that feel selected for taste, lifestyle aspiration, or spatial prestige. The scene should feel discovered, not chosen from a menu.",
        "- human warmth: the model should feel approachable and grounded — not aspirational, not idealized, not professionally presentational. She looks comfortable, close, and unperformed.",
        "- anti-portrait rule: natural mode should not collapse into a clean static portrait. The image must feel like a lived moment was encountered, not like the subject paused to be admired.",
        "- anti-stillness rule: avoid any image logic where the scene feels designed to look beautiful in its quietness. No serene gazes, no contemplative pauses, no artfully arranged everyday objects. If the result looks like a lifestyle magazine's idea of 'authentic simplicity,' it has failed. Natural's power is making the ordinary beautiful WITHOUT the viewer noticing the beauty was constructed.",
    ],
    # ── LIFESTYLE ─────────────────────────────────────────────────
    "lifestyle": [
        "— SOUL: you are an influencer's photographer capturing a moment mid-life. The model is DOING something — her body language originates from an activity in progress. The image sells a LIFESTYLE, not just clothes. Think aspirational but reachable — a desire that feels earned, not inherited.",
        "- emotional temperature: ENERGETIC. Socially alive. The image pulses with the rhythm of a real day — there is movement, social energy, a sense of going somewhere or being mid-something. The viewer should feel desire: 'I want to be there, doing that, wearing this.'",
        "- light philosophy: light from the ENVIRONMENT of the activity, not from a setup. If she's at a café, the light comes from the storefront and the afternoon sun. If she's at a market, it's harsh overhead plus shade patches. The light tells you WHERE she is and WHEN in the day — it is a narrative element, not a beauty tool. The light can be imperfect, mixed, directional — it serves the story, not the skin.",
        "- temporality: MID-ACTION. The camera caught her DOING something — she exists in active, forward-moving time. There is a before (she arrived) and an after (she's going somewhere). Unlike natural (continuous ordinary time) and editorial (staged eternal presence), lifestyle captures a SPECIFIC MOMENT in an unfolding day.",
        "- visual hierarchy: garment and scene are CO-PROTAGONISTS — the viewer desires both the outfit AND the moment. The model is the VEHICLE — she wears the clothes and performs the activity, connecting garment to scene. If the garment dominates alone (catalog), or the scene dominates alone (travel photo), the hierarchy is broken. The balance is: 'I want to wear THAT while doing THIS in a place like THAT.'",
        "- realism calibration: lifestyle sits BETWEEN natural authenticity and editorial polish. She looks put together (she dressed for her day) but not produced (no one styled her for a shoot). Her skin has natural texture, her hair moves with the wind, but she clearly cares about how she looks. Think 'best version of a real moment' — not raw, not retouched.",
        "- structural contract: the model MUST be mid-activity. Without a visible, specific activity in progress, the image collapses into another mode. A static, idle, or purely presentational pose is a contract violation.",
        "- scene creativity mandate: invent a specific Brazilian setting that makes the lifestyle feel reachable and desirable. Let the place emerge through materials, light temperature, time of day, and ambient texture instead of generic location labels.",
        "- Brazilian authenticity: let the diversity of Brazilian light, material culture, and daily rhythm appear naturally through the scene itself. Avoid stereotype labels, tourist shorthand, or repeating the same environment logic.",
        "- footwear narrative rule: footwear must feel chosen for her activity and setting, not for commercial completion. The shoe tells you what she was doing and where she was going.",
        "- anti-cliché activity rule: avoid default lifestyle activities that every e-commerce brand uses — walking with coffee, checking phone while leaning on wall, laughing with invisible friends, shopping bag in hand, hailing a taxi. Invent specific, vivid activities that feel particular to THIS woman in THIS place. The activity must feel discovered, not pulled from a stock photo menu.",
        "- anti-repetition rule: if in doubt, choose the UNEXPECTED location. The value of lifestyle mode is SURPRISE — showing the garment in a context the viewer never imagined but immediately wants to be part of.",
    ],
    # ── EDITORIAL COMMERCIAL ─────────────────────────────────────
    "editorial_commercial": [
        "— SOUL: you are a fashion art director shooting for a Brazilian commercial magazine spread. Every frame is INTENTIONAL — the angle, the shadow, the pose, the spatial relationship between model and architecture. Nothing is accidental. This image communicates AUTHORSHIP.",
        "- emotional temperature: COMMANDING. Intentional. Confident. The image radiates authorship — someone DECIDED everything in this frame. The viewer should feel the weight of a creative vision, not the warmth of a casual moment. The energy is magnetic, not inviting.",
        "- light philosophy: light as a DIRECTORIAL CHOICE. Every shadow is deliberate, every highlight is placed. The light sculpts the garment and the architecture into one composed image. Hard directional light, dramatic contrast, architectural shadows — all permitted and encouraged when they serve the composition. Unlike natural (accidental light) and lifestyle (environmental light), editorial light is AUTHORED light. It can be natural in origin but it must feel selected and controlled.",
        "- temporality: the model is DELIBERATELY PRESENT, not mid-activity (lifestyle) and not discovered (natural). She occupies the frame with intention — she knows the camera is there and she commands it. This is the key differentiator: lifestyle catches a moment, natural encounters a person, editorial STAGES a presence.",
        "- visual hierarchy: composition is the PROTAGONIST — the deliberate arrangement of model, architecture, light, and garment into one authored frame. The garment is a KEY ELEMENT of the composition but not its sole purpose. The model is a COMPOSITIONAL FORCE — she commands space, she doesn't just wear clothes. The scene is a STAGE — it was selected (not found) for its architectural and spatial potential. If any element could be swapped without changing the image's impact, the hierarchy has failed.",
        "- scene creativity mandate: invent a specific, architecturally compelling Brazilian location for each generation. Let architectural style, material contrast, light angle, and spatial geometry create the editorial authority rather than generic luxury shorthand.",
        "- Brazilian architectural richness: use the depth of Brazilian architecture and material culture as authorship, but never as a postcard list or decorative cliché. The place should feel selected by a real art director, not pulled from a travel guide.",
        "- premium logic: sophistication is EARNED through composition discipline — a worn concrete wall with perfect light is more editorial than a marble lobby. The premium quality comes from mastery of spatial relationships and light, never from showing expensive things. If the scene could be a stock luxury ad, it has failed.",
        "- anti-generic-luxury rule: marble lobbies, designer furniture, champagne flutes, infinity pools, rooftop lounges — these are the ENEMY of editorial. Real editorial finds beauty in unexpected places through masterful composition. If the scene could be a stock luxury ad, it has failed.",
        "- anti-lifestyle-collapse rule: editorial is NOT lifestyle with better lighting. The model is not doing an activity — she is BEING. Her body is a compositional element, not a narrative one. If she looks like she's on her way somewhere, the image has collapsed into lifestyle.",
        "- anti-repetition rule: if the location could appear in any country's fashion magazine, it's too generic. The scene must be unmistakably Brazilian in its architecture, materials, or spatial character — but elevated through the art direction.",
    ],
}


def get_mode_identity_soul(mode_id: Optional[str]) -> list[str]:
    """Retorna a soul de identidade completa para o mode.

    Args:
        mode_id: Identificador do mode (ex: "natural", "lifestyle").
            Quando None ou desconhecido, retorna a soul de "natural" (default).

    Returns:
        Lista de diretrizes textuais seguindo a ordem padronizada:
        SOUL → emotional temperature → light philosophy → temporality →
        visual hierarchy → [campos específicos do mode] → anti-patterns.
    """
    normalized = str(mode_id or "natural").strip().lower()
    return _MODE_IDENTITY_SOULS.get(normalized, _MODE_IDENTITY_SOULS["natural"])


def get_mode_soul_statement(mode_id: Optional[str]) -> str:
    """Retorna apenas a frase SOUL principal (primeira linha).

    Útil para matching de afinidade em curation_policy ou resumos curtos.
    """
    lines = get_mode_identity_soul(mode_id)
    return lines[0] if lines else ""
