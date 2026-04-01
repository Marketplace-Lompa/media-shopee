"""
prompt_result.py — Sanitização de prompts.

Contém utilitários de limpeza de ruído do output do Gemini.
A compilação completa foi deprecada; os orchestrators (generation_flow)
montam os prompts finais diretamente.
"""
from __future__ import annotations

import re


# ─── Marcadores de controle que o Gemini vaza no reference_mode ──────────────
_NANO_REFERENCE_CONTROL_MARKERS = (
    "replace the placeholder person",
    "do not preserve any face",
    "do not transfer identity from references",
    "create a fully new",
    "if the pattern appears",
    "it must remain",
    "use all references only as garment evidence",
    "use all references as garment evidence",
    "use the references only as garment evidence",
    "keep the garment exactly the same",
    "critical — preserve the exact surface pattern geometry",
    "critical - preserve the exact surface pattern geometry",
    "do not reinterpret stripe direction",
    "pattern angle",
    "never transfer identity from references",
    "do not copy any human identity traits from references",
    "do not repeat the dominant gesture",
    "treat the garment as the locked object",
    "do not introduce any visible undershirt",
    "render the garment with macro-accurate",
    "keep the result highly photorealistic",
)


def _strip_reference_prompt_noise(text: str) -> str:
    """Remove frases de controle de prompt (metadados/mandatos) antes de compilação."""

    if not text:
        return ""

    normalized = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("<CASTING_DIRECTION>", "\n<CASTING_DIRECTION>\n")
    normalized = normalized.replace("</CASTING_DIRECTION>", "\n</CASTING_DIRECTION>\n")
    segments = [
        segment.strip()
        for segment in re.split(r"(?<=[.!?])\s+|[\n\r]+", normalized)
        if segment.strip()
    ]
    kept: list[str] = []
    for segment in segments:
        low = segment.lower()
        if any(marker in low for marker in _NANO_REFERENCE_CONTROL_MARKERS):
            continue

        # Trechos curtos típicos de remoção de negativas deixam fragmentos sem sujeito
        # (ex.: "skin tone, hair, body type..."). Mantêm apenas frases úteis.
        if re.match(r"(?i)^(skin tone|body type|age impression|preserve|retain|copy|features)\b", low):
            continue
        if low in {",", ";", ".", "-", "do not", "keep", "replace", "critical"}:
            continue

        kept.append(segment)

    rebuilt = "\n".join(kept).strip()
    rebuilt = rebuilt.replace("\t", " ")
    rebuilt = re.sub(r" +", " ", rebuilt)
    return rebuilt
