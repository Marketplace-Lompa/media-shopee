"""
Pipeline Effectiveness V4 helpers.

Camadas implementadas:
- Reference pack builder (analysis/generation split + dedupe)
- Visual classifier summary
- Grounding orchestrator decision
- Diversity scheduler com janela móvel
- Quality contract e scoring global
- Validação leve de candidato + repair prompt
- Métricas locais semanais
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import time
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageFilter, ImageStat

from config import (
    AUTO_FULL_COMPLEXITY_THRESHOLD,
    DIVERSITY_MAX_SHARE,
    DIVERSITY_WINDOW,
    OUTPUTS_DIR,
    QUALITY_MIN_COMMERCIAL,
    QUALITY_MIN_FIDELITY,
    REFERENCE_ANALYSIS_MAX,
    REFERENCE_GENERATION_MAX,
)

_DIVERSITY_STATE_FILE = OUTPUTS_DIR / "diversity_state.json"
_EFFECTIVENESS_LOG_FILE = OUTPUTS_DIR / "effectiveness_log.jsonl"

_PROFILE_POOL = [
    {
        "id": "DP01",
        "prompt": "Southern Brazilian woman, fair skin with pink undertones, styled light-brown hair, slim frame, polished commercial look",
    },
    {
        "id": "DP02",
        "prompt": "Mixed-race São Paulo woman, warm olive skin, wavy dark hair, curvy figure, polished commercial look",
    },
    {
        "id": "DP03",
        "prompt": "Afro-Brazilian woman, deep brown skin, styled natural curls, athletic build, polished commercial look",
    },
    {
        "id": "DP04",
        "prompt": "Northeastern mixed-heritage woman, golden tanned skin, thick dark waves, tall and lean, polished commercial look",
    },
    {
        "id": "DP05",
        "prompt": "Italian-descent Southern Brazilian woman, fair olive skin, long dark hair, curvy figure, polished commercial look",
    },
]

_SCENARIO_POOL = [
    {"id": "SC01", "prompt": "bright modern downtown with clean architecture", "scene_type": "externo"},
    {"id": "SC02", "prompt": "minimalist indoor studio corner with soft window light", "scene_type": "interno"},
    {"id": "SC03", "prompt": "upscale shopping district at golden hour", "scene_type": "externo"},
    {"id": "SC04", "prompt": "cozy premium cafe terrace with tidy composition", "scene_type": "externo"},
    {"id": "SC05", "prompt": "bright minimalist apartment with neutral decor", "scene_type": "interno"},
]

_POSE_POOL = [
    {"id": "PO01", "prompt": "3/4 stance with relaxed shoulders and near-camera gaze", "style": "tradicional"},
    {"id": "PO02", "prompt": "natural standing pose with one hand relaxed, direct eye contact", "style": "tradicional"},
    {"id": "PO03", "prompt": "mid-step subtle movement while maintaining garment visibility", "style": "criativa"},
    {"id": "PO04", "prompt": "front-facing confident posture with clean silhouette reveal", "style": "tradicional"},
]

_CATEGORY_THRESHOLDS = {
    "simple_knit": {"fidelity": 0.62, "commercial": 0.60},
    "complex_knit": {"fidelity": 0.70, "commercial": 0.62},
    "lingerie": {"fidelity": 0.64, "commercial": 0.66},
    "dress": {"fidelity": 0.64, "commercial": 0.61},
    "outerwear": {"fidelity": 0.68, "commercial": 0.62},
    "general": {"fidelity": QUALITY_MIN_FIDELITY, "commercial": QUALITY_MIN_COMMERCIAL},
}

_OUTERWEAR_TOKENS = [
    "ruana",
    "poncho",
    "cardigan",
    "kimono",
    "casaco",
    "coat",
    "cape",
    "xale",
    "pelerine",
]
_COMPLEXITY_TOKENS = [
    "tricot",
    "tricô",
    "crochê",
    "croche",
    "knit",
    "stitch",
    "manga morcego",
    "batwing",
    "dolman",
    "assimetr",
    "mullet",
    "cocoon",
]
_LINGERIE_TOKENS = ["lingerie", "sutiã", "sutia", "body", "calcinha", "biquíni", "bikini", "renda"]
_DRESS_TOKENS = ["vestido", "dress", "gown"]
_SIMPLE_TOKENS = ["camiseta", "t-shirt", "regata", "blusa básica", "blusa basica", "camisa"]


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _image_quality_score(image_bytes: bytes) -> float:
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            rgb = img.convert("RGB")
            gray = rgb.convert("L")
            w, h = gray.size

            area_score = _clamp((w * h) / float(1200 * 1200))
            mean_luma = ImageStat.Stat(gray).mean[0]
            brightness_score = _clamp(1.0 - (abs(mean_luma - 132.0) / 132.0))

            edge_map = gray.filter(ImageFilter.FIND_EDGES)
            edge_var = ImageStat.Stat(edge_map).var[0]
            texture_score = _clamp(edge_var / 1800.0)

            ratio = w / max(h, 1)
            ratio_score = 1.0 if 0.55 <= ratio <= 1.8 else 0.6
            return _clamp(
                0.35 * area_score
                + 0.25 * brightness_score
                + 0.30 * texture_score
                + 0.10 * ratio_score
            )
    except Exception:
        return 0.0


def build_reference_pack(uploaded_images: List[bytes]) -> dict:
    raw_count = len(uploaded_images or [])
    if raw_count == 0:
        return {
            "analysis_images": [],
            "generation_images": [],
            "stats": {
                "raw_count": 0,
                "unique_count": 0,
                "analysis_count": 0,
                "generation_count": 0,
                "duplicate_count": 0,
                "dropped_low_quality_count": 0,
            },
        }

    seen = set()
    scored: List[dict] = []
    duplicate_count = 0
    low_quality_count = 0
    for i, img in enumerate(uploaded_images):
        h = _sha1(img)
        if h in seen:
            duplicate_count += 1
            continue
        seen.add(h)
        score = _image_quality_score(img)
        if score < 0.16:
            low_quality_count += 1
            continue
        scored.append({"idx": i, "score": score, "bytes": img})

    scored.sort(key=lambda x: x["score"], reverse=True)
    analysis = [row["bytes"] for row in scored[:REFERENCE_ANALYSIS_MAX]]
    generation = [row["bytes"] for row in scored[:REFERENCE_GENERATION_MAX]]
    if not analysis and scored:
        analysis = [scored[0]["bytes"]]
    if not generation and scored:
        generation = [scored[0]["bytes"]]

    return {
        "analysis_images": analysis,
        "generation_images": generation,
        "stats": {
            "raw_count": raw_count,
            "unique_count": len(scored),
            "analysis_count": len(analysis),
            "generation_count": len(generation),
            "duplicate_count": duplicate_count,
            "dropped_low_quality_count": low_quality_count,
        },
    }


def _has_any(text: str, tokens: List[str]) -> bool:
    return any(t in text for t in tokens)


def classify_visual_context(
    user_prompt: Optional[str],
    image_analysis: Optional[str],
    has_images: bool,
    reference_pack_stats: Optional[dict] = None,
) -> dict:
    prompt_text = (user_prompt or "").strip()
    analysis_text = (image_analysis or "").strip()
    text = f"{prompt_text} {analysis_text}".lower()

    garment_category = "general"
    if _has_any(text, _LINGERIE_TOKENS):
        garment_category = "lingerie"
    elif _has_any(text, _DRESS_TOKENS):
        garment_category = "dress"
    elif _has_any(text, _OUTERWEAR_TOKENS):
        garment_category = "outerwear"
    elif _has_any(text, _SIMPLE_TOKENS):
        garment_category = "simple_knit"

    complexity_hits = sum(1 for t in _COMPLEXITY_TOKENS if t in text)
    atypical = _has_any(
        text, ["ruana", "poncho", "batwing", "dolman", "manga morcego", "pelerine", "cocoon", "open-front"]
    )
    has_knit_signal = _has_any(text, ["tricot", "tricô", "crochê", "croche", "knit", "stitch"])
    has_ambiguity = ("poncho" in text and "cardigan" in text) or ("cape" in text and "cardigan" in text)

    ref_unique = int((reference_pack_stats or {}).get("unique_count", 0))
    complexity_score = _clamp(
        0.08
        + (0.22 if has_images else 0.0)
        + (0.22 if atypical else 0.0)
        + 0.1 * min(complexity_hits, 3) / 3
        + (0.12 if has_knit_signal else 0.0)
        + (0.08 if ref_unique >= 5 else 0.0)
    )
    uncertainty_score = _clamp(
        0.15
        + (0.22 if has_ambiguity else 0.0)
        + (0.16 if not analysis_text and has_images else 0.0)
        + (0.1 if not prompt_text and has_images else 0.0)
        - (0.12 if atypical else 0.0)
    )
    confidence = _clamp(1.0 - uncertainty_score)
    if garment_category == "outerwear" and has_knit_signal and complexity_score >= 0.56:
        garment_category = "complex_knit"

    silhouette_tokens: List[str] = []
    if "open-front" in text or "frente aberta" in text:
        silhouette_tokens.append("open_front")
    if "batwing" in text or "dolman" in text or "manga morcego" in text:
        silhouette_tokens.append("batwing_dolman")
    if "cocoon" in text:
        silhouette_tokens.append("cocoon_hem")
    if "cachecol" in text or "scarf" in text:
        silhouette_tokens.append("matching_scarf")

    garment_type = "garment"
    if "ruana" in text:
        garment_type = "ruana"
    elif "poncho" in text:
        garment_type = "poncho"
    elif "cardigan" in text:
        garment_type = "cardigan"
    elif "vestido" in text or "dress" in text:
        garment_type = "dress"

    return {
        "garment_type": garment_type,
        "garment_category": garment_category,
        "silhouette_tokens": silhouette_tokens,
        "atypical": atypical,
        "complexity_score": round(complexity_score, 3),
        "uncertainty_score": round(uncertainty_score, 3),
        "confidence": round(confidence, 3),
        "has_knit_signal": has_knit_signal,
    }


def decide_grounding_mode(
    strategy: str,
    has_images: bool,
    triage: dict,
    classifier_summary: dict,
) -> dict:
    reason_codes: List[str] = []
    triage_mode = triage.get("recommended_mode", "off")
    complexity = float(classifier_summary.get("complexity_score", triage.get("complexity_score", 0.0) or 0.0))
    uncertainty = float(classifier_summary.get("uncertainty_score", 0.0) or 0.0)
    atypical = bool(classifier_summary.get("atypical"))

    if strategy == "off":
        return {
            "grounding_mode": "off",
            "trigger_reason": "manual_off",
            "reason_codes": ["manual_grounding_off"],
        }

    if strategy == "on":
        mode = "full" if (atypical or complexity >= AUTO_FULL_COMPLEXITY_THRESHOLD) else "lexical"
        reason_codes.append("manual_grounding_on")
        if mode == "full":
            reason_codes.append("high_complexity_or_atypical")
        return {
            "grounding_mode": mode,
            "trigger_reason": "manual_on_forced_grounding",
            "reason_codes": reason_codes,
        }

    # auto
    mode = triage_mode
    trigger = triage.get("trigger_reason", "auto_default")

    if has_images:
        if atypical or uncertainty >= 0.35:
            if complexity >= AUTO_FULL_COMPLEXITY_THRESHOLD:
                mode = "full"
                trigger = "auto_visual_complexity_full"
                reason_codes.extend(["auto_ref_not_off", "atypical_or_uncertain", "visual_complexity_full"])
            else:
                mode = "lexical"
                trigger = "auto_visual_floor_lexical"
                reason_codes.extend(["auto_ref_not_off", "atypical_or_uncertain"])
        elif mode == "off" and complexity >= 0.5:
            mode = "lexical"
            trigger = "auto_complexity_floor"
            reason_codes.append("auto_complexity_floor")
    else:
        # sem imagem: conservador
        if uncertainty >= 0.55 or atypical:
            mode = "lexical"
            trigger = "auto_text_uncertain"
            reason_codes.append("text_uncertain_grounding")
        elif mode not in {"off", "lexical"}:
            mode = "lexical"

    if mode == "off":
        reason_codes.append("grounding_skipped_by_policy")

    return {
        "grounding_mode": mode,
        "trigger_reason": trigger,
        "reason_codes": sorted(set(reason_codes)),
    }


def _safe_state() -> dict:
    state = _load_json(
        _DIVERSITY_STATE_FILE,
        {
            "history": [],
            "last_profile_id": "",
            "last_scenario_id": "",
            "last_pose_id": "",
            "cursor_profile": 0,
            "cursor_scenario": 0,
            "cursor_pose": 0,
        },
    )
    if not isinstance(state, dict):
        return {
            "history": [],
            "last_profile_id": "",
            "last_scenario_id": "",
            "last_pose_id": "",
            "cursor_profile": 0,
            "cursor_scenario": 0,
            "cursor_pose": 0,
        }
    return state


def select_diversity_target(seed_hint: str = "", guided_brief: Optional[dict] = None) -> dict:
    state = _safe_state()
    history = list(state.get("history", []))
    window = max(8, DIVERSITY_WINDOW)
    max_share = _clamp(DIVERSITY_MAX_SHARE, 0.2, 0.8)
    recent = history[-window:]
    counts = Counter(recent)

    last_profile = str(state.get("last_profile_id", ""))
    last_scenario = str(state.get("last_scenario_id", ""))
    last_pose = str(state.get("last_pose_id", ""))

    max_count = max(1, int(math.floor(window * max_share)))
    profile_candidates = [
        p for p in _PROFILE_POOL if p["id"] != last_profile and counts.get(p["id"], 0) < max_count
    ]
    if not profile_candidates:
        profile_candidates = [p for p in _PROFILE_POOL if p["id"] != last_profile] or list(_PROFILE_POOL)
    min_count = min(counts.get(p["id"], 0) for p in profile_candidates)
    least_used = [p for p in profile_candidates if counts.get(p["id"], 0) == min_count]
    least_used.sort(key=lambda x: x["id"])

    seed = int(hashlib.sha1(seed_hint.encode("utf-8")).hexdigest()[:8], 16) if seed_hint else 0
    cursor_profile = int(state.get("cursor_profile", 0))
    profile = least_used[(cursor_profile + seed) % len(least_used)]

    guided_scene_type = str(((guided_brief or {}).get("scene") or {}).get("type", "")).strip().lower()
    guided_pose_style = str(((guided_brief or {}).get("pose") or {}).get("style", "")).strip().lower()
    guided_age_range = str(((guided_brief or {}).get("model") or {}).get("age_range", "")).strip()

    scenario_pool = (
        [s for s in _SCENARIO_POOL if s.get("scene_type") == guided_scene_type]
        if guided_scene_type in {"interno", "externo"}
        else list(_SCENARIO_POOL)
    )
    if not scenario_pool:
        scenario_pool = list(_SCENARIO_POOL)
    scenario_candidates = [s for s in scenario_pool if s["id"] != last_scenario] or scenario_pool

    pose_pool = (
        [p for p in _POSE_POOL if p.get("style") == guided_pose_style]
        if guided_pose_style in {"tradicional", "criativa"}
        else list(_POSE_POOL)
    )
    if not pose_pool:
        pose_pool = list(_POSE_POOL)
    pose_candidates = [p for p in pose_pool if p["id"] != last_pose] or pose_pool

    cursor_scenario = int(state.get("cursor_scenario", 0))
    cursor_pose = int(state.get("cursor_pose", 0))
    scenario = scenario_candidates[cursor_scenario % len(scenario_candidates)]
    pose = pose_candidates[cursor_pose % len(pose_candidates)]

    history.append(profile["id"])
    history = history[-window:]

    next_state = {
        "history": history,
        "last_profile_id": profile["id"],
        "last_scenario_id": scenario["id"],
        "last_pose_id": pose["id"],
        "cursor_profile": cursor_profile + 1,
        "cursor_scenario": cursor_scenario + 1,
        "cursor_pose": cursor_pose + 1,
    }
    _save_json(_DIVERSITY_STATE_FILE, next_state)

    age_prefix_map = {
        "18-24": "early 20s",
        "25-34": "late 20s to early 30s",
        "35-44": "late 30s to early 40s",
        "45+": "45+",
    }
    age_prefix = age_prefix_map.get(guided_age_range, "")
    profile_prompt = profile["prompt"]
    if age_prefix:
        profile_prompt = f"{age_prefix}, {profile_prompt}"

    profile_share = _clamp((counts.get(profile["id"], 0) + 1) / float(window))
    diversity_score = _clamp(1.0 - max(0.0, profile_share - max_share) / max(max_share, 1e-6))

    return {
        "profile_id": profile["id"],
        "profile_prompt": profile_prompt,
        "scenario_id": scenario["id"],
        "scenario_prompt": scenario["prompt"],
        "pose_id": pose["id"],
        "pose_prompt": pose["prompt"],
        "age_range": guided_age_range or None,
        "scene_type": guided_scene_type or None,
        "pose_style": guided_pose_style or None,
        "window": window,
        "max_share": max_share,
        "profile_share": round(profile_share, 3),
        "diversity_score": round(diversity_score, 3),
    }


def _resolve_thresholds(category: str) -> dict:
    defaults = _CATEGORY_THRESHOLDS.get(category, _CATEGORY_THRESHOLDS["general"])
    return {
        "fidelity": round(max(QUALITY_MIN_FIDELITY, defaults["fidelity"]), 3),
        "commercial": round(max(QUALITY_MIN_COMMERCIAL, defaults["commercial"]), 3),
    }


def _score_prompt_fidelity(prompt: str, classifier_summary: dict, pipeline_mode: str) -> float:
    text = (prompt or "").lower()
    score = 0.38 if pipeline_mode == "text_mode" else 0.56
    if "reference image is the authority" in text:
        score += 0.18
    if "texture lock" in text:
        score += 0.08
    if "front fully open" in text or "open-front" in text:
        score += 0.05
    if "batwing" in text or "dolman" in text:
        score += 0.04
    if "no extra pockets" in text or "without added pockets" in text:
        score += 0.04
    if classifier_summary.get("atypical") and not ("front fully open" in text or "open-front" in text):
        score -= 0.08
    return _clamp(score)


def _score_prompt_commercial(prompt: str) -> float:
    text = (prompt or "").lower()
    score = 0.42
    if "polished" in text:
        score += 0.18
    if "eye contact" in text or "near-camera gaze" in text or "looking at camera" in text:
        score += 0.14
    if "clean, bright" in text or "catalog-friendly" in text or "clean background" in text:
        score += 0.14
    if "confident" in text:
        score += 0.08
    return _clamp(score)


def compute_quality_contract(
    prompt: str,
    pipeline_mode: str,
    classifier_summary: dict,
    grounding_info: dict,
    diversity_target: dict,
) -> dict:
    category = classifier_summary.get("garment_category", "general")
    thresholds = _resolve_thresholds(category)
    fidelity = _score_prompt_fidelity(prompt, classifier_summary, pipeline_mode)
    commercial = _score_prompt_commercial(prompt)
    diversity = float(diversity_target.get("diversity_score", 0.6))

    applied_mode = str(grounding_info.get("applied_mode", "off"))
    attempted = bool(grounding_info.get("attempted", applied_mode != "off"))
    effective = bool(grounding_info.get("effective", False))
    source_count = len(grounding_info.get("sources", []) or [])
    grounded_images_count = int(grounding_info.get("grounded_images_count", 0) or 0)
    grounding_reliability = _clamp(
        (0.45 if applied_mode == "off" else 0.30)
        + (0.18 if attempted else 0.0)
        + (0.25 if effective else 0.0)
        + (0.12 if source_count >= 2 or grounded_images_count >= 1 else 0.0)
    )

    global_score = _clamp(
        0.40 * fidelity + 0.30 * commercial + 0.15 * diversity + 0.15 * grounding_reliability
    )

    reason_codes: List[str] = []
    if fidelity < thresholds["fidelity"]:
        reason_codes.append("fidelity_below_threshold")
    if commercial < thresholds["commercial"]:
        reason_codes.append("commercial_below_threshold")
    if applied_mode != "off" and not effective:
        reason_codes.append("grounding_not_effective")

    return {
        "effective_formula": "0.40*fidelity + 0.30*commercial + 0.15*diversity + 0.15*grounding",
        "category": category,
        "thresholds": thresholds,
        "fidelity_score": round(fidelity, 3),
        "commercial_score": round(commercial, 3),
        "diversity_score": round(diversity, 3),
        "grounding_reliability": round(grounding_reliability, 3),
        "global_score": round(global_score, 3),
        "needs_repair": bool(fidelity < thresholds["fidelity"] or commercial < thresholds["commercial"]),
        "reason_codes": sorted(set(reason_codes)),
    }


def build_repair_prompt(original_prompt: str, classifier_summary: dict, reason_codes: List[str]) -> str:
    base = (original_prompt or "").strip()
    repairs = [
        "REPAIR LOCK: improve commercial quality with polished styling, engaging near-camera gaze, and clean uncluttered catalog composition.",
        "REPAIR LOCK: preserve garment construction exactly from references; do not add extra pockets, closures, or set-in sleeves.",
    ]
    if classifier_summary.get("atypical"):
        repairs.append(
            "REPAIR LOCK: keep atypical silhouette exact (open front, batwing/dolman volume, rounded cocoon hem, scarf separate)."
        )
    if "fidelity_below_threshold" in reason_codes:
        repairs.append("REPAIR LOCK: enforce texture fidelity and exact stitch density from the reference garment.")
    if "commercial_below_threshold" in reason_codes:
        repairs.append("REPAIR LOCK: improve model grooming and expression for conversion-focused e-commerce look.")

    merged = base
    for line in repairs:
        if line[:30] not in merged:
            merged += f" {line}"
    return merged[:2300].strip()


def assess_generated_image(image_path: str, prompt: str, classifier_summary: dict) -> dict:
    try:
        with Image.open(image_path) as img:
            gray = img.convert("L")
            w, h = gray.size
            mean = ImageStat.Stat(gray).mean[0]
            std = math.sqrt(max(ImageStat.Stat(gray).var[0], 0.0))
            edge_var = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).var[0]

            sharpness = _clamp(edge_var / 1500.0)
            exposure = _clamp(1.0 - abs(mean - 132.0) / 132.0)
            contrast = _clamp(std / 64.0)
            size_ok = 1.0 if min(w, h) >= 700 else 0.6
            technical = _clamp(0.38 * sharpness + 0.25 * exposure + 0.22 * contrast + 0.15 * size_ok)

            fidelity = _score_prompt_fidelity(prompt, classifier_summary, pipeline_mode="reference_mode")
            commercial = _score_prompt_commercial(prompt)
            candidate_score = _clamp(0.50 * technical + 0.30 * fidelity + 0.20 * commercial)

            reason_codes: List[str] = []
            if sharpness < 0.28:
                reason_codes.append("low_texture_definition")
            if exposure < 0.30:
                reason_codes.append("bad_exposure_balance")
            if contrast < 0.20:
                reason_codes.append("low_contrast")
            if candidate_score < 0.56:
                reason_codes.append("candidate_score_low")

            return {
                "pass": candidate_score >= 0.56 and technical >= 0.44,
                "candidate_score": round(candidate_score, 3),
                "technical_score": round(technical, 3),
                "reason_codes": sorted(set(reason_codes)),
            }
    except Exception:
        return {
            "pass": False,
            "candidate_score": 0.0,
            "technical_score": 0.0,
            "reason_codes": ["candidate_assessment_failed"],
        }


def enrich_quality_with_generation(quality_contract: dict, assessments: List[dict]) -> dict:
    if not assessments:
        return quality_contract
    avg_candidate = sum(float(a.get("candidate_score", 0.0) or 0.0) for a in assessments) / len(assessments)
    merged = dict(quality_contract)
    merged["generation_score"] = round(_clamp(avg_candidate), 3)
    merged["global_score"] = round(
        _clamp(0.72 * float(quality_contract.get("global_score", 0.0)) + 0.28 * avg_candidate),
        3,
    )
    reason_codes = set(merged.get("reason_codes", []) or [])
    if avg_candidate < 0.56:
        reason_codes.add("generation_score_low")
    merged["reason_codes"] = sorted(reason_codes)
    merged["needs_repair"] = bool(merged.get("needs_repair", False) or avg_candidate < 0.56)
    return merged


def log_effectiveness_event(payload: dict) -> None:
    row = dict(payload)
    row["ts"] = int(time.time() * 1000)
    _EFFECTIVENESS_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _EFFECTIVENESS_LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize_effectiveness(days: int = 7) -> dict:
    if days <= 0:
        days = 7
    if not _EFFECTIVENESS_LOG_FILE.exists():
        return {
            "window_days": days,
            "total_jobs": 0,
            "avg_global_score": 0.0,
            "reason_distribution": {},
            "category_distribution": {},
        }

    now_ms = int(time.time() * 1000)
    cutoff = now_ms - days * 24 * 60 * 60 * 1000
    rows: List[dict] = []
    with _EFFECTIVENESS_LOG_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if int(row.get("ts", 0) or 0) >= cutoff:
                rows.append(row)

    reason_counter: Counter = Counter()
    category_counter: Counter = Counter()
    total_score = 0.0
    for row in rows:
        for code in row.get("reason_codes", []) or []:
            reason_counter[code] += 1
        category_counter[row.get("category", "general")] += 1
        total_score += float(row.get("global_score", 0.0) or 0.0)

    avg_global = (total_score / len(rows)) if rows else 0.0
    return {
        "window_days": days,
        "total_jobs": len(rows),
        "avg_global_score": round(avg_global, 3),
        "reason_distribution": dict(reason_counter.most_common()),
        "category_distribution": dict(category_counter.most_common()),
    }
