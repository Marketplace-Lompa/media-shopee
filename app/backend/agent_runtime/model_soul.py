"""
Módulo Alma da Modelo — model_soul.py

Responsável por entregar a diretiva criativa universal de casting.
O agente recebe instruções de COMO PENSAR sobre a modelo,
não uma lista prescritiva de atributos físicos ou referências prontas.

A alma força o agente a INVENTAR uma mulher brasileira específica
com detalhes de rosto, cabelo, pele, corpo e presença,
sem recorrer a menus de arquétipos ou rótulos regionais.

Quando recebe o contexto da peça (garment_context), o agente usa
a personalidade da roupa para guiar o casting inteligente:
a modelo deve COMPLEMENTAR e VENDER a peça.
"""
from __future__ import annotations


def get_model_soul(garment_context: str = "", mode_id: str = "") -> str:
    """Retorna a alma universal de casting — aplicável a todos os modes.

    Args:
        garment_context: Descrição da peça vinda da triagem visual.
            Quando presente, guia o agente a escolher a modelo certa
            para o tipo de roupa (idade, energia, presença, fisicalidade).
        mode_id: Identificador do mode ativo (ex: "editorial_commercial").
            Quando editorial, injeta diretivas criativas de persona
            empoderada, gaze, acessórios e styling intencional.
    """
    # ── Bloco de casting inteligente baseado na peça ──────────────
    garment_casting_block = ""
    if garment_context:
        garment_casting_block = (
            "\n"
            "🎯 GARMENT-DRIVEN CASTING — THE GARMENT DEFINES WHO WEARS IT:\n"
            f"  The garment for this shoot is: {garment_context}\n"
            "  Study the garment's personality, occasion, structure, target customer, and emotional temperature.\n"
            "  Then CHOOSE the woman who would authentically BUY and WEAR this piece in real life.\n"
            "  Let the garment guide age impression, hair presence, frame, face geometry, and emotional register.\n"
            "  The model must feel naturally right for this garment, not randomly beautiful beside it.\n"
            "  Do NOT default to the same woman every time — let the garment lead the casting decision.\n"
            "\n"
        )

    base_soul = (
        "MODEL SOUL (universal casting directive — you MUST follow this to create the model):\n"
        "You are a Brazilian casting director discovering a completely new face for this shoot.\n"
        "You already know the garment from the reference. Now INVENT the woman who would wear it\n"
        "authentically in real life.\n"
        "\n"
        "⚠️ NATIONALITY ANCHOR — NON-NEGOTIABLE:\n"
        "  The model is ALWAYS a BRAZILIAN WOMAN born and raised in Brazil.\n"
        "  NEVER label the model with foreign nationality terms.\n"
        "  Describe her PHYSICAL FEATURES directly. She is Brazilian, period.\n"
        "\n"
        f"{garment_casting_block}"
        "MANDATORY PHYSICAL DETAIL — you MUST describe ALL of these with SPECIFICITY:\n"
        "  1. FACE: bone structure (jaw shape, cheekbone prominence, chin), nose bridge width,\n"
        "     lip fullness and natural color, eye shape and color, brow thickness and arch.\n"
        "     Describe the GEOMETRY, not adjectives. Give enough structure that the face feels cast, not generic.\n"
        "  2. SKIN: exact undertone, texture (matte, natural sheen, sun-kissed glow),\n"
        "     and any subtle natural variation or small visible marks only when they are genuinely useful to the casting.\n"
        "  3. HAIR (critical — do NOT skip): texture and curl pattern (straight, wavy, curly,\n"
        "     coily — describe the tightness), weight and movement (heavy, bouncy, flat),\n"
        "     length relative to body (chin, shoulder, mid-back, waist), natural sheen level,\n"
        "     color with variation (roots, mid-lengths, ends — uniform or gradient?),\n"
        "     styling (center or side part, natural fall, loose, wind-caught, loosely pulled back when functionally justified).\n"
        "     Hair is a KEY identity marker — describe it with the same precision as the face.\n"
        "  4. BODY / FRAME: height impression, build, shoulder-to-hip ratio, and how the garment sits on her frame.\n"
        "     Describe fisicality, not pose choreography.\n"
        "  5. AGE: choose the age that FITS the garment's personality.\n"
        "     State it explicitly as an approximate age or age-range impression. Range: adult woman (early 20s to mid 40s).\n"
        "  6. EXPRESSION: describe what is visible in her face — mouth set, eye energy, calm, warmth, reserve, or confidence.\n"
        "     This must feel like a real commercially believable expression, not a vague attitude label.\n"
        "  7. MAKEUP: describe only what's VISIBLE on the face, not style labels.\n"
        "     All 7 dimensions must appear in the final prompt surface as visible authored traits, not remain implicit in your reasoning.\n"
        "\n"
        "VARIATION RULE:\n"
        "  Each generation must invent a different Brazilian woman from scratch.\n"
        "  Do not rely on pre-made archetypes, menus, regional labels, or ancestry shorthand.\n"
        "  Let variation emerge through concrete physical invention and through the garment's personality.\n"
        "\n"
        "CRITICAL RULES:\n"
        "  - The model is ALWAYS described as a Brazilian woman.\n"
        "  - Each generation must produce a UNIQUE woman — never repeat the same solution.\n"
        "  - Include subtle imperfections that break artificial perfection.\n"
        "  - NEVER use abstract labels without the specific physical geometry behind them.\n"
        "  - The model's physicality must COMPLEMENT the garment.\n"
        "  - Do NOT use regional, ethnic, or ancestry labels as shortcuts for description.\n"
        "  - Do NOT echo these directives in the output — INVENT the person.\n"
        "  - COMPLETENESS CHECK: your description MUST contain all 7 items (face, skin, hair,\n"
        "    body/frame, age, expression, makeup). If any is missing, the output is INVALID.\n"
        "    Hair and age are the most commonly skipped — verify both before finalizing.\n"
    )

    # ── Bloco natural condicional — presença não produzida ────────
    natural_soul_block = ""
    if mode_id == "natural":
        natural_soul_block = (
            "\n"
            "NATURAL MODE HUMAN LOGIC:\n"
            "  BEAUTY FLOOR — ALWAYS ACTIVE (natural ≠ anti-beauty):\n"
            "    She must feel genuinely attractive and commercially desirable — warm, current, and alive.\n"
            "    Natural production level does not mean visual neutrality, plainness, or drained appearance.\n"
            "    She should read as someone a real person would look at twice on social media.\n"
            "  PRESENCE: the woman feels encountered in real life rather than prepared for a shoot.\n"
            "    Her attractiveness is personal and intrinsic, not arranged. She does not need a set to be beautiful.\n"
            "  EXPRESSION: her expression arises from her own attention, not from offering her face to the viewer.\n"
            "    Avoid polished professional engagement, an overly resolved smile, or a serene beauty-portrait calm.\n"
            "  MAKEUP: reads as light daily grooming — not shoot makeup and not a drained bare-faced denial of beauty.\n"
            "    Minimal product, real-life finish, credible for an ordinary day with a personal sense of care.\n"
            "  HAIR: lightly imperfect and non-salon-finished, but still personal and charming.\n"
            "    Avoid deliberately face-flattering precision or hair that looks neatly arranged for the frame.\n"
            "  SKIN: real-life texture with natural variation — not polished into cosmetic perfection, not drained.\n"
            "    Natural sheen, slight unevenness, and honest skin read are welcome.\n"
            "  ANTI-SETUP: do not convert her into a camera-ready beauty portrait or a severity study.\n"
            "    She should feel occupied by her own moment, not anti-beautiful to prove authenticity.\n"
            "  SOCIAL-COMMERCE FIT: quieter and less produced than other modes, but she must still\n"
            "    plausibly sell fashion in a Brazilian social-commerce context through approachable attractiveness.\n"
        )

    # ── Bloco lifestyle condicional — presença socialmente viva ────
    lifestyle_soul_block = ""
    if mode_id == "lifestyle":
        lifestyle_soul_block = (
            "\n"
            "LIFESTYLE MODE HUMAN LOGIC:\n"
            "  PRESENCE: the woman should feel socially self-assured and engaged in her moment,\n"
            "    not presenting herself for a camera or performing beauty for an audience.\n"
            "  EXPRESSION: she is alive in the scene — her expression originates from what she is doing,\n"
            "    not from awareness of being photographed. Brief camera acknowledgment is natural, not staged.\n"
            "  MAKEUP: her makeup should feel intentional but not editorial — she prepared for her day,\n"
            "    not for a photoshoot. The result reads as polished and self-aware, not bare-faced and not fashion-produced.\n"
            "  HAIR: hair should feel cared-for and personal — it has her identity, not a salon's.\n"
            "    It can be styled, but the styling reads as her daily choice, not a hairdresser's decision.\n"
            "  SKIN: natural healthy texture with self-care evidence, not cosmetic perfection.\n"
            "  VISUAL PERSONALITY: she should feel like someone with individual style and social identity,\n"
            "    not a casting-call placeholder. Her specific traits make her memorable.\n"
        )

    # ── Bloco editorial condicional — persona empoderada ──────────
    editorial_soul_block = ""
    if mode_id == "editorial_commercial":
        editorial_soul_block = (
            "\n"
            "🎬 EDITORIAL SOUL — THIS IS A FASHION EDITORIAL, NOT A CATALOG:\n"
            "  ATTITUDE: The model's presence is as important as her physical features.\n"
            "    She projects CONFIDENCE, COMMAND, and SELF-POSSESSION.\n"
            "    Her energy says: 'I chose this garment. It didn't choose me.'\n"
            "  GAZE: She looks DIRECTLY at the camera with intention and power.\n"
            "    Not blank, not friendly — COMMANDING. Think editorial cover energy.\n"
            "  EXPRESSION: Empowered, self-assured, magnetic.\n"
            "    Slight smirk, raised chin, or intense calm. NEVER a generic smile.\n"
            "  ACCESSORIES: Complete the editorial look with 1-3 accessories that\n"
            "    COMPLEMENT the garment's energy level:\n"
            "    - Structured handbag, sunglasses, statement jewelry, watch, bracelet stack.\n"
            "    - Match the garment mood: casual garment → casual accessories,\n"
            "      premium garment → refined accessories.\n"
            "    - YOU decide which accessories elevate this specific look.\n"
            "  HAIR STYLING: Hair must feel EDITORIALLY STYLED, not just washed.\n"
            "    Wind-swept, slicked back, architectural volume, or intentional texture.\n"
            "    The hairstyle is a creative choice, not an afterthought.\n"
        )

    return base_soul + natural_soul_block + lifestyle_soul_block + editorial_soul_block
