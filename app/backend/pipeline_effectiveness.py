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

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

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
    # Perfis regionais leves — diversidade de casting sem descrever físico.
    # O Nano Banana gera a modelo sozinho; o perfil só ancora vibe/região para variar.
    {"id": "DP01", "prompt": "A radiant Baiana Brazilian fashion model"},
    {"id": "DP02", "prompt": "A chic Paulistana editorial model"},
    {"id": "DP03", "prompt": "A sophisticated Carioca commercial model"},
    {"id": "DP04", "prompt": "A striking Northeastern Brazilian model"},
    {"id": "DP05", "prompt": "A fresh-faced Sulista catalog model"},
    {"id": "DP06", "prompt": "A contemporary Mineira model"},
    {"id": "DP07", "prompt": "An elegant Sulista high-end model"},
    {"id": "DP08", "prompt": "A fresh-faced Brasília editorial model"},
]

_SCENARIO_POOL = [
    # ── Externo (5) ────────────────────────────────────────────────────────────
    {"id": "SC01", "prompt": "bright modern downtown with clean architecture and soft depth of field", "scene_type": "externo"},
    {"id": "SC03", "prompt": "upscale shopping district at golden hour with blurred storefronts", "scene_type": "externo"},
    {"id": "SC04", "prompt": "cozy premium cafe terrace with tidy warm-lit composition", "scene_type": "externo"},
    {"id": "SC06", "prompt": "elegant open-air courtyard with dappled natural light and clean background", "scene_type": "externo"},
    {"id": "SC07", "prompt": "lush botanical garden path with gentle backlight and soft greenery", "scene_type": "externo"},
    # ── Interno (5) ────────────────────────────────────────────────────────────
    {"id": "SC02", "prompt": "minimalist indoor studio corner with large soft window light", "scene_type": "interno"},
    {"id": "SC05", "prompt": "bright minimalist apartment with neutral decor and clean background", "scene_type": "interno"},
    {"id": "SC08", "prompt": "light-filled modern loft with white walls and natural wood floor", "scene_type": "interno"},
    {"id": "SC09", "prompt": "upscale fashion showroom with neutral white background and diffused light", "scene_type": "interno"},
    {"id": "SC10", "prompt": "serene home studio with large diffused window light and simple backdrop", "scene_type": "interno"},
]

_POSE_POOL = [
    # ── Tradicional — garment readability priority ─────────────────────────────
    {"id": "PO01", "prompt": "3/4 stance with relaxed shoulders and near-camera gaze", "style": "tradicional"},
    {"id": "PO02", "prompt": "natural standing pose with one hand relaxed, direct eye contact", "style": "tradicional"},
    {"id": "PO04", "prompt": "front-facing confident posture with clean silhouette reveal", "style": "tradicional"},
    {"id": "PO05", "prompt": "contrapposto weight shift with relaxed arms and engaged direct gaze", "style": "tradicional"},
    {"id": "PO06", "prompt": "slight body turn highlighting garment drape, near-camera warm look", "style": "tradicional"},
    # ── Criativa — movement with garment still visible ─────────────────────────
    {"id": "PO03", "prompt": "mid-step subtle movement while maintaining full garment visibility", "style": "criativa"},
    {"id": "PO07", "prompt": "light walking stride with confident arm swing, garment silhouette clear", "style": "criativa"},
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
_LINGERIE_TOKENS = ["lingerie", "sutiã", "sutia", "bodysuit", "body suit", "calcinha", "biquíni", "bikini", "renda íntima"]
_DRESS_TOKENS = ["vestido", "dress", "gown"]
_SIMPLE_TOKENS = ["camiseta", "t-shirt", "regata", "blusa básica", "blusa basica", "camisa"]


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _estimate_human_realism(img: Image.Image) -> dict[str, Any]:
    gray = img.convert("L")
    w, h = gray.size
    if w <= 0 or h <= 0:
        return {"score": 0.0, "reason_codes": ["human_realism_unavailable"]}

    top = gray.crop((0, 0, w, max(1, int(h * 0.42))))
    center = gray.crop((int(w * 0.2), int(h * 0.12), int(w * 0.8), int(h * 0.72)))
    lower = gray.crop((0, int(h * 0.58), w, h))

    top_edges = top.filter(ImageFilter.FIND_EDGES)
    center_edges = center.filter(ImageFilter.FIND_EDGES)
    lower_edges = lower.filter(ImageFilter.FIND_EDGES)

    top_var = float(ImageStat.Stat(top).var[0] or 0.0)
    top_edge_var = float(ImageStat.Stat(top_edges).var[0] or 0.0)
    center_edge_var = float(ImageStat.Stat(center_edges).var[0] or 0.0)
    lower_edge_var = float(ImageStat.Stat(lower_edges).var[0] or 0.0)

    left = top.crop((0, 0, max(1, top.width // 2), top.height))
    right = top.crop((top.width - max(1, top.width // 2), 0, top.width, top.height))
    right = ImageOps.mirror(right)
    paired_width = min(left.width, right.width)
    paired_height = min(left.height, right.height)
    left = left.crop((0, 0, paired_width, paired_height))
    right = right.crop((0, 0, paired_width, paired_height))
    diff = ImageChops.difference(left, right)
    symmetry_penalty = _clamp(1.0 - (ImageStat.Stat(diff).mean[0] / 64.0))

    top_energy = _clamp(top_edge_var / 1600.0)
    center_energy = _clamp(center_edge_var / 1800.0)
    lower_energy = _clamp(lower_edge_var / 1800.0)
    tonal_presence = _clamp(math.sqrt(max(top_var, 0.0)) / 48.0)

    score = _clamp(
        0.28 * top_energy
        + 0.22 * center_energy
        + 0.20 * tonal_presence
        + 0.15 * (1.0 - symmetry_penalty)
        + 0.15 * lower_energy
    )

    reason_codes: list[str] = []
    if top_energy < 0.12 or tonal_presence < 0.18:
        reason_codes.append("dead_gaze_or_flat_face")
    if symmetry_penalty > 0.72:
        reason_codes.append("eye_or_face_alignment_drift")
    if lower_energy < 0.08 and center_energy < 0.10:
        reason_codes.append("hand_or_limb_definition_low")
    if 0.08 <= lower_energy <= 0.14 and 0.08 <= center_energy <= 0.14:
        reason_codes.append("freeze_frame_pose_read")

    return {"score": score, "reason_codes": reason_codes}


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


def _analyze_image(image_bytes: bytes) -> dict:
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
            
            score = _clamp(
                0.35 * area_score
                + 0.25 * brightness_score
                + 0.30 * texture_score
                + 0.10 * ratio_score
            )
            return {
                "score": score,
                "luma": mean_luma,
                "edge": edge_var,
                "ratio": ratio
            }
    except Exception:
        return {"score": 0.0, "luma": 132.0, "edge": 0.0, "ratio": 1.0}


def _anonymize_face_light(image_bytes: bytes) -> bytes:
    """
    Suprime identidade facial SEM recortar a imagem.

    Aplica blur leve apenas no topo (rosto/cabelo) para reduzir
    face-copy mantendo 100% da peça visível (silhueta, textura, drape).
    """
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            w, h = img.size
            # Blur suave no top 15% (rosto) — preserva cabelo/ombros parcialmente
            face_h = int(h * 0.15)
            face_region = img.crop((0, 0, w, face_h)).filter(
                ImageFilter.GaussianBlur(radius=18)
            )
            img.paste(face_region, (0, 0))
            out = BytesIO()
            img.save(out, format="JPEG", quality=92)
            return out.getvalue()
    except Exception:
        return image_bytes


def _select_generation_rows(
    inlier_rows: List[dict],
    outlier_rows: List[dict],
) -> tuple[List[dict], int]:
    """
    Monta o pack final de geração preservando 1-2 referências estruturalmente
    diversas. Isso evita que fotos planas/detalhes da peça sejam eliminadas
    só porque são visualmente diferentes das fotos "vestindo".
    """
    generation_rows = list(inlier_rows[:REFERENCE_GENERATION_MAX])
    if not outlier_rows:
        return generation_rows, 0

    preserved = 0
    for row in sorted(
        outlier_rows,
        key=lambda x: (x.get("score", 0.0), x.get("distance", 0.0)),
        reverse=True,
    ):
        if preserved >= 2:
            break
        generation_rows.append(row)
        preserved += 1

    generation_rows = sorted(
        generation_rows,
        key=lambda x: (
            x.get("adjusted_score", x.get("score", 0.0)),
            x.get("score", 0.0),
        ),
        reverse=True,
    )[:REFERENCE_GENERATION_MAX]
    return generation_rows, preserved


def _select_strict_generation_rows(
    inlier_rows: List[dict],
    outlier_rows: List[dict],
) -> List[dict]:
    """
    Pack curto para benchmark/fluxo estrito:
    - 2 imagens vestindo mais consistentes
    - 1 ancora estrutural diversa, se existir
    """
    strict_rows = list(inlier_rows[:2])
    if outlier_rows:
        ranked_outliers = sorted(
            outlier_rows,
            key=lambda x: (x.get("score", 0.0), x.get("distance", 0.0)),
            reverse=True,
        )
        strict_rows.extend(ranked_outliers[:2])
    elif len(inlier_rows) >= 3:
        strict_rows.append(inlier_rows[2])
    return strict_rows[:4]


def build_reference_pack(uploaded_images: List[bytes]) -> dict:
    raw_count = len(uploaded_images or [])
    if raw_count == 0:
        return {
            "analysis_images": [],
            "generation_images": [],
            "stats": {
                "raw_count": 0,
                "unique_count": 0,
                "pre_outlier_unique_count": 0,
                "analysis_count": 0,
                "generation_count": 0,
                "duplicate_count": 0,
                "dropped_low_quality_count": 0,
                "dropped_outliers_count": 0,
            },
        }

    seen = set()
    scored: List[dict] = []
    duplicate_count = 0
    low_quality_count = 0
    dropped_outliers_count = 0
    preserved_structural_count = 0
    
    for i, img in enumerate(uploaded_images):
        h = _sha1(img)
        if h in seen:
            duplicate_count += 1
            continue
        seen.add(h)
        
        analysis = _analyze_image(img)
        score = analysis["score"]
        if score < 0.16:
            low_quality_count += 1
            continue
            
        scored.append({
            "idx": i, 
            "score": score, 
            "bytes": img,
            "luma": analysis["luma"],
            "edge": analysis["edge"],
            "ratio": analysis["ratio"]
        })

    # Outlier detection (visual consistency) se tivermos 3 ou mais imagens
    outlier_rows: List[dict] = []
    if len(scored) >= 3:
        # Calcular medianas
        lumas = sorted(x["luma"] for x in scored)
        edges = sorted(x["edge"] for x in scored)
        ratios = sorted(x["ratio"] for x in scored)
        
        mid = len(scored) // 2
        med_luma = lumas[mid]
        med_edge = edges[mid]
        med_ratio = ratios[mid]
        
        # Calcular distâncias e ranquear novamente (score ajustado pela distância)
        for img_data in scored:
            # Distância normalizada aproximada
            d_luma = abs(img_data["luma"] - med_luma) / 255.0
            d_edge = abs(img_data["edge"] - med_edge) / max(med_edge, 100.0)
            d_ratio = abs(img_data["ratio"] - med_ratio) / med_ratio
            
            distance = _clamp(d_luma + min(d_edge, 1.0) + d_ratio, 0.0, 3.0)
            img_data["distance"] = distance
            # Penalidade suave na nota se estiver muito distante
            img_data["adjusted_score"] = img_data["score"] - (distance * 0.3)
            
        # Filtra outliers por distância (independente da ordem de entrada).
        # Mantém no mínimo 2 imagens para não quebrar os fluxos subsequentes.
        distance_threshold = 1.2
        filtered = [row for row in scored if row.get("distance", 0.0) <= distance_threshold]
        outlier_rows = [row for row in scored if row.get("distance", 0.0) > distance_threshold]
        if len(filtered) < 2:
            scored.sort(key=lambda x: x["adjusted_score"], reverse=True)
            filtered = scored[:2]
            outlier_rows = [row for row in scored if row not in filtered]

        dropped_outliers_count = max(0, len(scored) - len(filtered))
        scored = sorted(filtered, key=lambda x: x["adjusted_score"], reverse=True)
    else:
        # Menos de 3, não faz consistency check
        scored.sort(key=lambda x: x["score"], reverse=True)

    analysis_images = [row["bytes"] for row in scored[:REFERENCE_ANALYSIS_MAX]]
    generation_source_rows, preserved_structural_count = _select_generation_rows(scored, outlier_rows)
    strict_generation_rows = _select_strict_generation_rows(scored, outlier_rows)
    generation_images = [row["bytes"] for row in generation_source_rows]
    strict_generation_images = [row["bytes"] for row in strict_generation_rows]
    if not analysis_images and scored:
        analysis_images = [scored[0]["bytes"]]
    if not generation_images and scored:
        generation_images = [scored[0]["bytes"]]
    if not strict_generation_images and generation_images:
        strict_generation_images = generation_images[: min(3, len(generation_images))]

    return {
        "analysis_images": analysis_images,
        "generation_images": generation_images,
        "strict_generation_images": strict_generation_images,
        "stats": {
            "raw_count": raw_count,
            "unique_count": len(scored),
            "pre_outlier_unique_count": len(scored) + dropped_outliers_count,
            "analysis_count": len(analysis_images),
            "generation_count": len(generation_images),
            "strict_generation_count": len(strict_generation_images),
            "duplicate_count": duplicate_count,
            "dropped_low_quality_count": low_quality_count,
            "dropped_outliers_count": dropped_outliers_count,
            "preserved_structural_count": preserved_structural_count,
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

    # ONDA 1.1: Em reference_mode com imagens, a referencia visual e a autoridade.
    # Grounding so adiciona ruido (texto sobre a peca que conflita com visual).
    # Quando o structural_contract tem confianca alta, nao precisamos de web search.
    structural_confidence = float(classifier_summary.get("confidence", 0.0) or 0.0)

    if has_images:
        if structural_confidence >= 0.75:
            # Referencia visual forte — grounding OFF para evitar conflito textual
            mode = "off"
            trigger = "auto_visual_reference_sufficient"
            reason_codes.append("grounding_skipped_high_visual_confidence")
        elif atypical or uncertainty >= 0.35:
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


# ── Art Director Intelligence: afinidade estética garment→profile/cenário/lighting ──

# Mapa vibe→IDs de perfil com maior afinidade (peso, não hard filter)
_VIBE_PROFILE_AFFINITY: dict[str, set[str]] = {
    "boho_artisanal":    {"DP01", "DP04", "DP06"},         # Baiana, Nordestina, Mineira
    "urban_chic":        {"DP02", "DP03", "DP08"},         # Paulistana, Carioca, Brasília
    "romantic":          {"DP05", "DP07", "DP06"},         # Sulistas, Mineira
    "bold_edgy":         {"DP03", "DP04", "DP02"},         # Carioca, Nordestina, Paulistana
    "minimalist":        {"DP02", "DP08", "DP05"},         # Paulistana, Brasília, Sulista
    "beachwear_resort":  {"DP03", "DP01", "DP04"},         # Carioca, Baiana, Nordestina
    "sport_casual":      set(),                             # sem preferência regional
}

# Mapa season→scene_type preferido
_SEASON_SCENE_AFFINITY: dict[str, str] = {
    "summer":      "externo",
    "winter":      "interno",
    "mid_season":  "",  # sem preferência → usa alternation normal
}

# Mapa formality→IDs de cenário com maior afinidade
_FORMALITY_SCENARIO_AFFINITY: dict[str, set[str]] = {
    "formal":       {"SC01", "SC02", "SC09"},              # downtown, studio, showroom
    "smart_casual":  {"SC03", "SC04", "SC08", "SC05"},     # shopping, café, loft, apartment
    "casual":       {"SC04", "SC06", "SC07", "SC10"},      # café, courtyard, botanical, home studio
}

# R5: Lighting intelligence — textura/peso da peça → iluminação ideal
_TEXTURED_SUBTYPES = {"ruana_wrap", "poncho", "cape", "pullover"}
_SMOOTH_SUBTYPES = {"blazer", "jacket", "vest", "dress", "blouse"}

def _compute_lighting_hint(structural_contract: Optional[dict], garment_aesthetic: Optional[dict]) -> str:
    """R5: Retorna hint de iluminação baseado na textura/peso da peça."""
    if not structural_contract or not structural_contract.get("enabled"):
        return ""
    subtype = str(structural_contract.get("garment_subtype", "")).strip().lower()
    volume = str(structural_contract.get("silhouette_volume", "")).strip().lower()
    if subtype in _TEXTURED_SUBTYPES or volume == "draped":
        return "dappled natural light revealing fabric texture and depth"
    if subtype in _SMOOTH_SUBTYPES or volume in {"structured", "fitted"}:
        return "soft diffused light for clean fabric surface"
    return ""


def _reorder_by_affinity(candidates: list, preferred_ids: set) -> list:
    """Reordena candidatos colocando IDs preferidos primeiro, mantendo ordem relativa."""
    if not preferred_ids:
        return candidates
    preferred = [c for c in candidates if c["id"] in preferred_ids]
    rest = [c for c in candidates if c["id"] not in preferred_ids]
    return preferred + rest


def select_diversity_target(
    seed_hint: str = "",
    guided_brief: Optional[dict] = None,
    garment_aesthetic: Optional[dict] = None,
    structural_contract: Optional[dict] = None,
) -> dict:
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

    # Art Director: reordenar por afinidade com vibe da peça (peso, não hard filter)
    _ae = garment_aesthetic or {}
    _vibe = str(_ae.get("vibe", "")).strip().lower()
    if _vibe and _vibe in _VIBE_PROFILE_AFFINITY:
        least_used = _reorder_by_affinity(least_used, _VIBE_PROFILE_AFFINITY[_vibe])

    seed = int(hashlib.sha1(seed_hint.encode("utf-8")).hexdigest()[:8], 16) if seed_hint else 0
    cursor_profile = int(state.get("cursor_profile", 0))
    profile = least_used[(cursor_profile + seed) % len(least_used)]

    guided_scene_type = str(((guided_brief or {}).get("scene") or {}).get("type", "")).strip().lower()
    guided_pose_style = str(((guided_brief or {}).get("pose") or {}).get("style", "")).strip().lower()
    guided_age_range = str(((guided_brief or {}).get("model") or {}).get("age_range", "")).strip()

    # MT4: In guided mode use the requested type; in auto mode alternate interno/externo.
    # Art Director: season affinity pode influenciar scene_type quando guided não especifica.
    if guided_scene_type in {"interno", "externo"}:
        scenario_pool = [s for s in _SCENARIO_POOL if s.get("scene_type") == guided_scene_type] or list(_SCENARIO_POOL)
    else:
        _season = str(_ae.get("season", "")).strip().lower()
        _season_pref = _SEASON_SCENE_AFFINITY.get(_season, "")
        if _season_pref:
            # Season da peça sugere scene_type (mas anti-repeat pode sobrescrever)
            scenario_pool = [s for s in _SCENARIO_POOL if s.get("scene_type") == _season_pref]
            if not scenario_pool:
                scenario_pool = list(_SCENARIO_POOL)
        else:
            # Sem preferência sazonal → alternation normal
            last_scene_type = str(state.get("last_scene_type", "externo"))
            preferred_type = "interno" if last_scene_type == "externo" else "externo"
            scenario_pool = [s for s in _SCENARIO_POOL if s.get("scene_type") == preferred_type]
            if not scenario_pool:
                scenario_pool = list(_SCENARIO_POOL)
    scenario_candidates = [s for s in scenario_pool if s["id"] != last_scenario] or scenario_pool

    # Art Director: reordenar cenários por afinidade de formalidade
    _formality = str(_ae.get("formality", "")).strip().lower()
    if _formality and _formality in _FORMALITY_SCENARIO_AFFINITY:
        scenario_candidates = _reorder_by_affinity(
            scenario_candidates, _FORMALITY_SCENARIO_AFFINITY[_formality]
        )

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
        "last_scene_type": scenario.get("scene_type", ""),   # MT4: interno/externo alternation
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

    # R5: lighting intelligence baseada em textura da peça
    lighting_hint = _compute_lighting_hint(structural_contract, garment_aesthetic)

    _art_director_log = ""
    if _vibe:
        _art_director_log = f" vibe={_vibe} season={_ae.get('season')} formality={_formality}"
    if lighting_hint:
        _art_director_log += f" lighting='{lighting_hint[:40]}'"
    if _art_director_log:
        print(f"[DIVERSITY] 🎨 Art Director:{_art_director_log}")

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
        "lighting_hint": lighting_hint,
        "garment_aesthetic": garment_aesthetic,
    }


def _resolve_thresholds(category: str) -> dict:
    defaults = _CATEGORY_THRESHOLDS.get(category, _CATEGORY_THRESHOLDS["general"])
    return {
        "fidelity": round(max(QUALITY_MIN_FIDELITY, defaults["fidelity"]), 3),
        "commercial": round(max(QUALITY_MIN_COMMERCIAL, defaults["commercial"]), 3),
    }


def _score_prompt_fidelity(prompt: str, classifier_summary: dict, pipeline_mode: str) -> float:
    """Score de fidelidade calibrado para sinais do Prompt Compiler V2."""
    text = (prompt or "").lower()
    score = 0.38 if pipeline_mode == "text_mode" else 0.56
    # P1 structural clauses (compilador injeta como cláusulas de prioridade 1)
    if "opening behavior" in text or "sleeve architecture" in text or "hem shape" in text:
        score += 0.14
    # P2 texture fidelity (compilador: "exact texture, stitch, and fiber relief")
    if "exact texture" in text or "fiber relief" in text or "stitch" in text:
        score += 0.10
    # Silhouette-specific signals
    if "front fully open" in text or "open-front" in text or "front opening" in text:
        score += 0.05
    if "batwing" in text or "dolman" in text or "cape-like" in text:
        score += 0.04
    # Pocket fidelity (MT-J positive form: "pocketless garment")
    if "pocketless" in text or "zero visible pockets" in text:
        score += 0.04
    # Legacy signals (still valid if present from external prompts)
    if "reference image is the authority" in text:
        score += 0.10
    if "texture lock" in text:
        score += 0.06
    if classifier_summary.get("atypical") and not ("front fully open" in text or "open-front" in text or "opening behavior" in text):
        score -= 0.08
    return _clamp(score)


def _score_prompt_commercial(prompt: str) -> float:
    """Score comercial calibrado para sinais do Prompt Compiler V2."""
    text = (prompt or "").lower()
    score = 0.42
    # P3 quality_model (compilador: "polished model, natural expression")
    if "polished" in text:
        score += 0.14
    # P3 quality_gaze (compilador: pool de gaze com "eye contact", "gaze", "near-camera look")
    if "eye contact" in text or "gaze" in text or "near-camera" in text or "looking at camera" in text:
        score += 0.14
    # P4 quality_scene + camera block (compilador: scene composition + camera realism)
    if (
        "softly defocused" in text
        or "shallow depth of field" in text
        or "depth of field" in text
        or "bokeh" in text
        or "negative space" in text
        or "backlight" in text
        or "catalog framing" in text
        or "clean background" in text
    ):
        score += 0.14
    # P2 cover composition (compilador: "catalog cover, standing pose")
    if "catalog" in text or "standing pose" in text:
        score += 0.06
    if "confident" in text or "natural expression" in text:
        score += 0.06
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
    """
    Delta-repair: acrescenta ao prompt original apenas 1 cláusula curta
    por dimensão que falhou. Não reescreve o prompt base para minimizar drift.
    """
    base = (original_prompt or "").strip()
    codes = set(reason_codes or [])
    delta: list[str] = []

    if "fidelity_below_threshold" in codes:
        delta.append("exact garment geometry, stitch density, and sleeve architecture as structured")
    elif classifier_summary.get("atypical"):
        # atypical sem fidelity_below_threshold: reforço leve apenas de silhueta
        delta.append("atypical silhouette volume and opening as structured")

    if "commercial_below_threshold" in codes:
        delta.append("direct camera eye contact, polished posture, clean catalog composition")

    if "technical_below_threshold" in codes:
        delta.append("sharp focus throughout garment, accurate exposure, clear subject-background separation")

    if not delta:
        # Nenhum reason_code específico: regeneração sem modificação de prompt
        return base

    delta_str = ", ".join(delta)
    separator = ", " if not base.endswith((".", "!", "?")) else " "
    return (base + separator + delta_str)[:2300].strip()


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
            human_realism = _estimate_human_realism(img)
            technical = _clamp(
                0.30 * sharpness
                + 0.20 * exposure
                + 0.18 * contrast
                + 0.12 * size_ok
                + 0.20 * human_realism["score"]
            )

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
            reason_codes.extend(human_realism["reason_codes"])
            if candidate_score < 0.56:
                reason_codes.append("candidate_score_low")

            return {
                "pass": (
                    candidate_score >= 0.56
                    and technical >= 0.44
                    and human_realism["score"] >= 0.42
                ),
                "candidate_score": round(candidate_score, 3),
                "technical_score": round(technical, 3),
                "human_realism_score": round(human_realism["score"], 3),
                "reason_codes": sorted(set(reason_codes)),
            }
    except Exception:
        return {
            "pass": False,
            "candidate_score": 0.0,
            "technical_score": 0.0,
            "human_realism_score": 0.0,
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
