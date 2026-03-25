from __future__ import annotations

import re
from typing import Any, Optional

from agent_runtime.compiler import (
    _compile_prompt_v2,
    _count_words,
    _truncate_by_sentence,
    _SENTENCE_SPLIT_RE,
)
from agent_runtime.garment_narrative import sanitize_garment_narrative

# ─── Sanitização de camera_and_realism (ex-camera.py) ───────────────────────
# Essas funções existem apenas para LIMPAR o output do Gemini quando ele
# vaza persona, skin texture ou menciona câmeras/lentes específicas no campo
# camera_and_realism. Não definem templates nem tomam decisões criativas.
# A direção de captura vem dos presets (camera_perspective, lighting_profile,
# framing_profile) via MODE_PRESETS no system context.

_CAMERA_REALISM_KEYWORDS = (
    "sony", "canon", "nikon", "f/", "mm", "lens", "bokeh", "depth of field",
    "lighting", "light", "golden hour", "pores", "skin", "fabric",
    "creases", "grain", "noise", "realism", "realistic",
)

_CAMERA_PERSONA_STRIP_SIGNALS = (
    "features blend",
    "brazilian beauty",
    "authentic beauty",
    "radiant authentic",
    "flawless unretouched",
    "ford models",
    "vogue brasil",
    "farm rio",
    "lança perfume",
    "editorial talent",
    "lookbook model",
    "new face",
    "casting aesthetic",
)

_SKIN_TEXTURE_CLEANUPS = (
    (re.compile(r"(?i)\bvisible\s+natural\s+skin\s+pores\b"), ""),
    (re.compile(r"(?i)\bvisible\s+pores\b"), ""),
    (re.compile(r"(?i)\bsubtle\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\bauthentic\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\bunretouched\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\btrue-to-life\s+skin\s+texture\b"), ""),
    (re.compile(r"(?i)\bskin\s+texture\b"), ""),
    (re.compile(r"(?i)\bsoft\s+flyaway\s+hairs\b"), ""),
    (re.compile(r"(?i)\bsubtle\s+peach\s+fuzz\b"), ""),
    (re.compile(r"(?i)\bpeach\s+fuzz\b"), ""),
)

_PERSONA_PREFIX_RE = re.compile(
    r"(?i)(?:flawless\s+unretouched\s+skin\s+realism\s+with\s*"
    r"|radiant\s+authentic\s+Brazilian\s+beauty\s+with\s*"
    r"|authentic\s+Brazilian\s+beauty\s+with\s*)",
    re.I,
)

# Strip de dispositivos/lentes específicas — o Gemini às vezes menciona
# marcas e especificações técnicas que engessam a geração de imagem.
_DEVICE_STRIP_PATTERNS = (
    re.compile(r"(?i)\bSony\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\bCanon\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\bNikon\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\bFujifilm\s+[A-Z0-9]+[^,.]*, "),
    re.compile(r"(?i)\b\d+mm\s+lens[^,.]*[,.]"),
    re.compile(r"(?i)\bSony\s+[A-Z0-9]+"),
    re.compile(r"(?i)\bCanon\s+[A-Z0-9]+"),
    re.compile(r"(?i)\bNikon\s+[A-Z0-9]+"),
    re.compile(r"(?i)\bFujifilm\s+[A-Z0-9]+"),
    re.compile(r"(?i)\b\d+mm\b"),
    re.compile(r"(?i)\blens\b"),
)

# Fallback mínimo quando o Gemini não gera nenhum texto de captura.
# Sem template longo — os presets no MODE_PRESETS já deram a direção.
_MINIMAL_CAPTURE_FALLBACK = "Commercially clean capture with natural finish."


def _extract_camera_realism_block(text: str, max_sentences: int = 2) -> str:
    """Extrai sentenças de câmera/realismo de um prompt legado."""
    if not text or not text.strip():
        return ""
    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    selected: list[str] = []
    for sent in sentences:
        low = sent.lower()
        if any(token in low for token in _CAMERA_REALISM_KEYWORDS):
            cleaned = sent.strip()
            if cleaned:
                selected.append(cleaned)
        if len(selected) >= max_sentences:
            break
    return " ".join(selected).strip()


def _sanitize_camera_block(camera_text: str) -> str:
    """
    Sanitiza o campo camera_and_realism gerado pelo Gemini.
    Remove vazamentos de persona, skin texture, e mencões a câmeras específicas.
    Não aplica templates nem toma decisões criativas.
    """
    text = re.sub(r"\s+", " ", (camera_text or "").strip())
    if not text:
        return _MINIMAL_CAPTURE_FALLBACK

    # Pass 0: strip device/lens mentions
    for pat in _DEVICE_STRIP_PATTERNS:
        text = pat.sub("", text)
    text = re.sub(r"\s*,\s*,+", ", ", text)
    text = re.sub(r"^\s*,\s*", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    if not text:
        return _MINIMAL_CAPTURE_FALLBACK

    # Pass 1: targeted prefix substitution
    text = _PERSONA_PREFIX_RE.sub("", text)

    # Pass 2: clause-level stripping (comma-separated)
    _clauses = [c.strip() for c in re.split(r",\s*", text) if c.strip()]
    _clean_clauses = [
        c for c in _clauses
        if not any(sig in c.lower() for sig in _CAMERA_PERSONA_STRIP_SIGNALS)
    ]
    if _clean_clauses:
        text = ", ".join(_clean_clauses)
        if re.search(r"[.!?]\s*$", (camera_text or "")):
            text = text.rstrip(",.") + "."

    # Pass 3: sentence-level stripping
    _persona_clean = [
        s for s in re.split(r"(?<=[.!?])\s+", text)
        if not any(sig in s.lower() for sig in _CAMERA_PERSONA_STRIP_SIGNALS)
    ]
    if _persona_clean:
        text = " ".join(_persona_clean)

    # Pass 4: strip skin-surface treatment
    for pattern, replacement in _SKIN_TEXTURE_CLEANUPS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"(?i)\b(and|with)\s*(?:,)?\s*(?=[,.])", "", text)
    text = re.sub(r"\s*,\s*,+", ", ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,.])", r"\1", text)
    text = re.sub(r",\s*(and\s*)?(?=[.!?]|$)", "", text)

    # Word cap (concisão)
    if _count_words(text) > 52:
        text, _ = _truncate_by_sentence(text, 52)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return _MINIMAL_CAPTURE_FALLBACK

    if not text.endswith((".", "!", "?")):
        text += "."
    return text


def _compose_prompt_with_camera(base_prompt: str, camera_block: str) -> str:
    """Concatena base_prompt + camera block sanitizado."""
    base = re.sub(r"\s+", " ", (base_prompt or "").strip())
    camera = re.sub(r"\s+", " ", (camera_block or "").strip())
    if not base:
        return camera
    if not camera:
        return base
    if camera.lower() in base.lower():
        return base
    separator = "" if base.endswith((".", "!", "?")) else "."
    return f"{base}{separator} {camera}".strip()


# ─── Finalizador principal ──────────────────────────────────────────────────

def finalize_prompt_agent_result(
    *,
    result: dict[str, Any],
    has_images: bool,
    has_prompt: bool,
    user_prompt: Optional[str],
    structural_contract: dict[str, Any],
    guided_brief: Optional[dict[str, Any]],
    guided_enabled: bool,
    guided_set_mode: str,
    guided_set_detection: dict[str, Any],
    grounding_mode: str,
    pipeline_mode: str,
    aspect_ratio: str,
    pose: str,
    grounding_pose_clause: str,
    profile: str,
    scenario: str,
    diversity_target: Optional[dict[str, Any]],
    mode_id: str = "",
    framing_profile: str = "",
    camera_perspective: str = "",
    lighting_profile: str = "",
    pose_energy: str = "",
    casting_profile: str = "",
) -> dict[str, Any]:
    base_prompt_raw = str(result.get("base_prompt", "") or "").strip()
    legacy_prompt_raw = str(result.get("prompt", "") or "").strip()
    if not base_prompt_raw:
        base_prompt_raw = legacy_prompt_raw
    if not base_prompt_raw:
        base_prompt_raw = "RAW photo, polished e-commerce catalog composition with garment-first framing."

    garment_narrative = str(result.get("garment_narrative", "") or "").strip()
    if garment_narrative:
        garment_narrative = sanitize_garment_narrative(garment_narrative, structural_contract)
        garment_words = garment_narrative.split()
        if len(garment_words) > 35:
            garment_narrative = " ".join(garment_words[:35])
            garment_words = garment_narrative.split()
        if garment_narrative:
            print(f"[AGENT] 👗 garment_narrative ({len(garment_words)}w): {garment_narrative[:120]}")

    # ── Captura: sanitização pura, sem templates ─────────────────────
    camera_realism_raw = str(result.get("camera_and_realism", "") or "").strip()
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(legacy_prompt_raw)
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(base_prompt_raw)

    camera_realism = _sanitize_camera_block(camera_realism_raw)

    camera_words = _count_words(camera_realism)
    base_budget = max(80, 220 - camera_words)
    if has_images and not has_prompt:
        target_budget = 215
        base_budget = max(80, target_budget - camera_words)

    lighting_hint = (diversity_target or {}).get("lighting_hint", "") or ""
    compiled_base_prompt, compiler_debug = _compile_prompt_v2(
        prompt=base_prompt_raw,
        has_images=has_images,
        has_prompt=has_prompt,
        contract=structural_contract if has_images else None,
        guided_brief=guided_brief if guided_enabled else None,
        guided_enabled=guided_enabled,
        guided_set_detection=guided_set_detection if guided_enabled and guided_set_mode == "conjunto" else None,
        grounding_mode=grounding_mode,
        pipeline_mode=pipeline_mode,
        word_budget=base_budget,
        aspect_ratio=aspect_ratio,
        pose_hint=pose or grounding_pose_clause,
        profile_hint=profile,
        scenario_hint=scenario if (has_images and not has_prompt) else "",
        garment_narrative=garment_narrative if (has_images and not has_prompt) else "",
        lighting_hint=lighting_hint if (has_images and not has_prompt) else "",
        shot_type=str(result.get("shot_type", "auto")),
        framing_profile=framing_profile,
        pose_energy=pose_energy,
        casting_profile=casting_profile,
    )

    final_prompt = _compose_prompt_with_camera(compiled_base_prompt, camera_realism)
    result["base_prompt"] = compiled_base_prompt
    result["camera_and_realism"] = camera_realism
    result["mode"] = mode_id or None
    result["prompt"] = final_prompt

    compiler_debug["camera_words"] = camera_words
    compiler_debug["base_budget"] = base_budget
    compiler_debug["final_words"] = _count_words(final_prompt)
    result["prompt_compiler_debug"] = compiler_debug
    return result
