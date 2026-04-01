"""
Módulo Alma do Styling — styling_soul.py

Responsável por entregar a diretiva criativa universal de finalização do look.
O agente recebe instruções de COMO PENSAR a completude visual do styling sem
tirar protagonismo da peça hero.
"""
from __future__ import annotations

from typing import Optional


_WARM_SEASONS = {"summer", "verão", "spring", "primavera"}
_COLD_SEASONS = {"winter", "inverno", "fall", "autumn", "outono"}


def _get_seasonal_footwear_mandate(garment_season: Optional[str]) -> str:
    season = str(garment_season or "").strip().lower()
    if not season or season == "unknown":
        return ""
    if season in _COLD_SEASONS:
        return (
            "\n"
            "SEASONAL FOOTWEAR MANDATE (COLD SEASON — ENFORCE):\n"
            "  The hero garment signals a cold-weather context (winter, autumn, or transitional cold).\n"
            "  Footwear MUST be weather-coherent: closed shoes, boots, ankle boots, sneakers, loafers, or similar.\n"
            "  NEVER suggest open-toe sandals, flip-flops, slides, or bare feet when the garment is cold-season.\n"
            "  If the crop does not show feet, keep footwear unspecified rather than guessing an incompatible option.\n"
        )
    if season in _WARM_SEASONS:
        return (
            "\n"
            "SEASONAL FOOTWEAR MANDATE (WARM SEASON — GUIDE):\n"
            "  The hero garment signals a warm-weather context (summer or spring).\n"
            "  Footwear can be open (sandals, slides) or lightweight closed (sneakers, espadrilles).\n"
            "  Avoid heavy boots or thick-sole winter footwear unless the mode explicitly contrasts season.\n"
        )
    return ""


def get_styling_soul(
    *, mode_id: Optional[str], has_images: bool, garment_season: Optional[str] = None
) -> str:
    normalized = str(mode_id or "").strip().lower()

    reference_guard = ""
    if has_images:
        reference_guard = (
            "\n"
            "REFERENCE STYLING GUARD:\n"
            "  Do NOT copy the reference person's lower-body look, footwear, bag, jewelry, props, or finishing choices.\n"
            "  Invent new styling that supports the garment and the active mode.\n"
        )

    mode_overlay = ""
    if normalized == "catalog_clean":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC STYLING LOGIC:\n"
            "  Keep the look commercially complete, quiet, and premium.\n"
            "  If feet are visible, finish the look with discreet coherent footwear rather than barefoot presentation unless the brief explicitly asks for it.\n"
            "  Quiet does not mean generic: choose one specific completion family that serves this garment.\n"
            "  Avoid defaulting to the same dark trouser plus ankle-boot solution whenever the hero product is a top-layer knit.\n"
        )
    elif normalized == "natural":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC STYLING LOGIC:\n"
            "  Keep the styling believable, lightly personal, and non-performative.\n"
            "  The look should feel resolved, but never overdesigned.\n"
            "  Avoid status-signaling polish, over-accessorized finish, or styling choices that make the image feel prepared for a shoot before it feels lived-in.\n"
            "  Mention footwear or finishing choices only when they are visibly relevant or genuinely complete the lived moment.\n"
            "  Avoid abstract styling language that merely announces tasteful completion without showing real-life necessity.\n"
            "  If the crop does not meaningfully show the lower body or feet, do not force shoe talk just to make the look sound complete.\n"
            "  When in doubt, choose the lower-attention, more ordinary resolution and let optional styling collapse to none.\n"
        )
    elif normalized == "lifestyle":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC STYLING LOGIC:\n"
            "  The styling should reveal what kind of day, movement, or social rhythm she is inside — accessories are narrative tools,\n"
            "  not commercial completion items. Let any finishing choice emerge from use, context, and activity rather than from a preset shopping list.\n"
            "  The garment remains the visual reason for the image, but the finishing touches explain her day.\n"
            "  Avoid both the stripped-back minimalism of 'natural' and the curated fashion finish of 'editorial'.\n"
            "  YOU choose what completion makes this particular moment feel lived rather than assembled.\n"
        )
    elif normalized == "editorial_commercial":
        mode_overlay = (
            "\n"
            "MODE-SPECIFIC STYLING LOGIC:\n"
            "  Let the styling feel edited, intentional, and fashion-aware.\n"
            "  Use finishing choices to sharpen silhouette and image authority without turning the frame into an accessories story.\n"
        )

    seasonal_mandate = _get_seasonal_footwear_mandate(garment_season)

    return (
        "STYLING SOUL (universal look-completion directive — you MUST follow this to resolve the styling):\n"
        "You are inventing how the garment is completed and framed by the rest of the look, not decorating the image with random fashion add-ons.\n"
        "Follow the active MODE_IDENTITY to decide how silent, lived-in, polished, or fashion-edited the styling should feel.\n"
        "\n"
        "STYLING INVENTION METHOD:\n"
        "  1. Start from the garment's role, material, silhouette, and commercial personality.\n"
        "  2. Let the mode decide how resolved the look should feel: minimal, believable, socially alive, or fashion-edited.\n"
        "  2.1 If the garment suggests a more polished or sophisticated finish than the active mode allows, the MODE wins.\n"
        "  3. Complete the look through whatever complementary slots are genuinely unresolved around the hero product, using accessories only when they truly support plausibility and mode coherence.\n"
        "  4. Avoid turning styling into a second protagonist.\n"
        "  5. Avoid generic wording like styled to perfection, accessorized tastefully, or complete premium look without visible fashion logic.\n"
        "\n"
        "MANDATORY STYLING DETAIL:\n"
        "  Your final prompt must make the styling feel intentionally resolved through visible evidence.\n"
        "  Include what matters for this image in fluent prose:\n"
        "  1. complementary garment logic only when another clothing slot remains unresolved or visibly present in the frame\n"
        "  2. footwear logic when feet are visible or the shot genuinely needs it for completion\n"
        "  3. finish logic only when it supports the garment rather than competes with it; accessories are optional, not mandatory\n"
        "  If the look feels unfinished or randomly embellished, the styling is wrong.\n"
        f"{mode_overlay}"
        f"{seasonal_mandate}"
        "\n"
        "VARIATION RULE:\n"
        "  Each generation must invent a fresh styling resolution from scratch.\n"
        "  Do not recycle the same safe completion formula or default to interchangeable finishing choices without reason.\n"
        f"{reference_guard}"
        "CRITICAL RULES:\n"
        "  - Styling exists to complete the garment's world, not to steal attention from it.\n"
        "  - The final prompt should make the look feel coherently finished, not merely described as complete.\n"
        "  - COMPLETENESS CHECK: before finalizing, verify that any visible completion slot feels intentional, necessary, and mode-aligned.\n"
        "  - Do NOT echo these directives in the output — INVENT the styling resolution.\n"
    )
