"""
Módulo Alma da Modelo — model_soul.py

Responsável por entregar a diretiva criativa universal de casting.
O agente recebe instruções de COMO PENSAR sobre a modelo,
não uma lista prescritiva de atributos físicos.

A alma força o agente a INVENTAR uma mulher brasileira específica
com detalhes de rosto, cabelo, pele, corpo, biotipo e etnia regional,
escolhendo aleatoriamente a região e mistura étnica a cada geração.

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
            para o tipo de roupa (idade, energia, biotipo, presença).
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
            "  Study this garment's personality, occasion, and target customer.\n"
            "  Then CHOOSE the model who would BUY and WEAR this piece in real life:\n"
            "  - A casual beach dress → younger, sun-kissed energy, relaxed posture.\n"
            "  - A tailored blazer → mature professional, strong jawline, composed presence.\n"
            "  - A cozy knit sweater → warm approachable woman, natural comfort.\n"
            "  - A streetwear crop top → urban edge, bold attitude, younger energy.\n"
            "  - An elegant evening dress → refined features, elongated silhouette, poise.\n"
            "  These are EXAMPLES — use the actual garment description above to decide.\n"
            "  The model's age, hair, body type, and energy must feel NATURAL for this garment.\n"
            "  Do NOT default to the same model every time — let the garment lead.\n"
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
        "  Brazil's regional diversity comes from centuries of ancestral mixing.\n"
        "  NEVER label the model with foreign nationality terms.\n"
        "  Describe her PHYSICAL FEATURES directly — ancestry shaped phenotype,\n"
        "  it does NOT define identity. She is Brazilian, period.\n"
        "\n"
        f"{garment_casting_block}"
        "MANDATORY PHYSICAL DETAIL — you MUST describe ALL of these with SPECIFICITY:\n"
        "  1. FACE: bone structure (jaw shape, cheekbone prominence, chin), nose bridge width,\n"
        "     lip fullness and natural color, eye shape and color, brow thickness and arch.\n"
        "     Describe the GEOMETRY, not adjectives.\n"
        "  2. SKIN: exact undertone, texture (matte, natural sheen, sun-kissed glow),\n"
        "     any natural marks (freckles, beauty marks, tan lines).\n"
        "  3. HAIR (critical — do NOT skip): texture and curl pattern (straight, wavy, curly,\n"
        "     coily — describe the tightness), weight and movement (heavy, bouncy, flat),\n"
        "     length relative to body (chin, shoulder, mid-back, waist), natural sheen level,\n"
        "     color with variation (roots, mid-lengths, ends — uniform or gradient?),\n"
        "     styling (center or side part, tucked behind ear, loose, wind-caught, pulled back).\n"
        "     Hair is a KEY identity marker — describe it with the same precision as the face.\n"
        "  4. BODY: height impression, build, shoulder-to-hip ratio, posture energy.\n"
        "     How does her body CARRY the garment?\n"
        "  5. AGE: choose the age that FITS the garment's personality.\n"
        "     Range: adult woman (early 20s to mid 40s). This is YOUR creative decision.\n"
        "  6. MAKEUP: describe only what's VISIBLE on the face, not style labels.\n"
        "\n"
        "BRAZILIAN REGIONAL DIVERSITY — randomly choose ONE region per generation\n"
        "and let its ancestral phenotype mix shape the model's physical appearance:\n"
        "  - NORTE: river-dwelling mixed heritage, indigenous-European ancestry blend.\n"
        "  - NORDESTE: African-indigenous-Portuguese ancestry blend.\n"
        "  - SUDESTE (urban): dense urban ancestry mixing — African, European,\n"
        "    Asian, and Middle Eastern ancestries blended into unique phenotypes.\n"
        "  - SUDESTE (coastal): sun-shaped blend — Portuguese-African ancestry.\n"
        "  - SUL: predominantly European ancestry with regional Brazilian character.\n"
        "  - CENTRO-OESTE: indigenous-European ancestry with savanna-region character.\n"
        "  Use the chosen region ONLY as phenotype inspiration — then INVENT every\n"
        "  physical detail yourself. Do NOT recite regional descriptors back.\n"
        "\n"
        "CRITICAL RULES:\n"
        "  - The model is ALWAYS described as a Brazilian woman.\n"
        "  - Each generation must produce a UNIQUE woman — never repeat phenotypes.\n"
        "  - Vary the region each time. Do NOT default to the same phenotype.\n"
        "  - Include subtle imperfections that break artificial perfection.\n"
        "  - NEVER use abstract labels without the specific physical geometry behind them.\n"
        "  - The model's physicality must COMPLEMENT the garment.\n"
        "  - Do NOT echo these directives in the output — INVENT the person.\n"
        "  - COMPLETENESS CHECK: your description MUST contain all 6 items (face, skin, hair,\n"
        "    body, age, makeup). If any is missing, the output is INVALID. Hair is the most\n"
        "    commonly skipped — verify it is present before finalizing.\n"
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

    return base_soul + editorial_soul_block
