"""
Reference selector para benchmark/validacao.

Objetivo:
- Classificar cada imagem de referência por papel visual.
- Selecionar subsets curtos e explicáveis para o Nano.
- Separar subconjuntos por objetivo: base_generation, strict_single_pass, edit_anchors.
"""
from __future__ import annotations

from typing import Any, List, Optional

from google.genai import types

from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.parser import _decode_agent_response
from agent_runtime.triage import _infer_unified_vision_triage
from pipeline_effectiveness import _analyze_image, _clamp, _sha1


REFERENCE_ROLE_SCHEMA = {
    "type": "object",
    "required": [
        "role",
        "garment_focus",
        "silhouette_readability",
        "construction_readability",
        "texture_readability",
        "styling_leak_risk",
        "background_noise",
        "confidence",
        "reason",
    ],
    "properties": {
        "role": {
            "type": "string",
            "enum": [
                "worn_front",
                "worn_three_quarter",
                "worn_side",
                "detail_flat",
                "detail_texture",
                "detail_construction",
                "close_crop",
                "noisy_other",
            ],
        },
        "garment_focus": {"type": "number"},
        "silhouette_readability": {"type": "number"},
        "construction_readability": {"type": "number"},
        "texture_readability": {"type": "number"},
        "styling_leak_risk": {"type": "number"},
        "background_noise": {"type": "number"},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
}

_VALID_ROLES = {
    "worn_front",
    "worn_three_quarter",
    "worn_side",
    "detail_flat",
    "detail_texture",
    "detail_construction",
    "close_crop",
    "noisy_other",
}


def _normalize_reference_role(raw: dict[str, Any]) -> dict[str, Any]:
    role = str(raw.get("role", "noisy_other")).strip().lower()
    if role not in _VALID_ROLES:
        role = "noisy_other"

    def _num(name: str) -> float:
        try:
            return _clamp(float(raw.get(name, 0.0) or 0.0))
        except Exception:
            return 0.0

    return {
        "role": role,
        "garment_focus": _num("garment_focus"),
        "silhouette_readability": _num("silhouette_readability"),
        "construction_readability": _num("construction_readability"),
        "texture_readability": _num("texture_readability"),
        "styling_leak_risk": _num("styling_leak_risk"),
        "background_noise": _num("background_noise"),
        "confidence": _num("confidence"),
        "reason": str(raw.get("reason", "") or "").strip()[:240],
    }


def _infer_reference_role(image_bytes: bytes, user_prompt: Optional[str] = None) -> dict[str, Any]:
    parts = [
        types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=image_bytes)),
    ]
    instruction = (
        "Classify this single garment reference image for fashion image generation.\n"
        "Choose one role:\n"
        "- worn_front: person wearing the garment, front-facing or near-front, useful for main silhouette\n"
        "- worn_three_quarter: person wearing the garment, 3/4 angle, useful for drape and side volume\n"
        "- worn_side: person wearing the garment, mostly side/back angle, useful but secondary\n"
        "- detail_flat: flat or laid-out garment showing overall structure\n"
        "- detail_texture: close or flat detail mainly useful for texture/stitch/pattern\n"
        "- detail_construction: detail mainly useful for opening, edge, hem, sleeve or build logic\n"
        "- close_crop: too cropped or partial to serve as primary reference\n"
        "- noisy_other: low-value for generation\n\n"
        "Score 0.0-1.0:\n"
        "- garment_focus: how much the image is about the garment rather than person/background\n"
        "- silhouette_readability: how well shape, drape, and volume can be read\n"
        "- construction_readability: how well opening, hem, edge, sleeve logic can be read\n"
        "- texture_readability: how well stitch, knit, and pattern can be read\n"
        "- styling_leak_risk: risk that the original model/look/background dominates the generation\n"
        "- background_noise: how distracting the environment is\n"
        "- confidence: your confidence in the classification\n"
        "Return strict JSON only."
    )
    if user_prompt:
        instruction += f" User context: {user_prompt[:200]}"
    parts.append(types.Part(text=instruction))
    response = generate_structured_json(
        parts=parts,
        schema=REFERENCE_ROLE_SCHEMA,
        temperature=0.1,
        max_tokens=500,
        thinking_budget=0,
    )
    parsed = _decode_agent_response(response)
    return _normalize_reference_role(parsed if isinstance(parsed, dict) else {})


def _score_worn_candidate(item: dict[str, Any]) -> float:
    angle_bonus = 0.08 if item["role"] == "worn_front" else (0.05 if item["role"] == "worn_three_quarter" else 0.02)
    local_score = float(item.get("local_quality_score", 0.0) or 0.0)
    value = (
        0.24 * item["garment_focus"]
        + 0.27 * item["silhouette_readability"]
        + 0.20 * item["construction_readability"]
        + 0.11 * item["texture_readability"]
        + 0.08 * item["confidence"]
        + 0.08 * local_score
        + angle_bonus
        - 0.18 * item["styling_leak_risk"]
        - 0.06 * item["background_noise"]
    )
    return _clamp(value)


def _score_detail_candidate(item: dict[str, Any]) -> float:
    local_score = float(item.get("local_quality_score", 0.0) or 0.0)
    value = (
        0.20 * item["garment_focus"]
        + 0.34 * item["construction_readability"]
        + 0.30 * item["texture_readability"]
        + 0.08 * item["silhouette_readability"]
        + 0.08 * item["confidence"]
        + 0.06 * local_score
        - 0.08 * item["styling_leak_risk"]
        - 0.02 * item["background_noise"]
    )
    return _clamp(value)


def _score_identity_safe_candidate(item: dict[str, Any]) -> float:
    role = str(item.get("role", "") or "")
    role_bonus = (
        0.14 if role in {"detail_flat", "detail_texture", "detail_construction"}
        else (0.06 if role == "worn_three_quarter" else (0.03 if role == "worn_front" else 0.0))
    )
    value = (
        0.25 * item["garment_focus"]
        + 0.23 * item["construction_readability"]
        + 0.16 * item["texture_readability"]
        + 0.12 * item["silhouette_readability"]
        + 0.08 * item["confidence"]
        + 0.06 * float(item.get("local_quality_score", 0.0) or 0.0)
        + role_bonus
        - 0.22 * item["styling_leak_risk"]
        - 0.08 * item["background_noise"]
    )
    return _clamp(value)


def _pick_top(items: List[dict[str, Any]], limit: int, used_hashes: set[str]) -> List[dict[str, Any]]:
    selected: List[dict[str, Any]] = []
    for row in items:
        if row["sha1"] in used_hashes:
            continue
        selected.append(row)
        used_hashes.add(row["sha1"])
        if len(selected) >= limit:
            break
    return selected


def _compute_identity_risk_stats(rows: List[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "avg_styling_leak_risk": 0.0,
            "max_styling_leak_risk": 0.0,
            "identity_reference_risk": "low",
            "worn_reference_count": 0,
            "detail_reference_count": 0,
        }
    leak_vals = [float(row.get("styling_leak_risk", 0.0) or 0.0) for row in rows]
    avg_leak = sum(leak_vals) / len(leak_vals)
    max_leak = max(leak_vals)
    worn_count = sum(
        1 for row in rows
        if str(row.get("role", "") or "") in {"worn_front", "worn_three_quarter", "worn_side"}
    )
    detail_count = sum(
        1 for row in rows
        if str(row.get("role", "") or "") in {"detail_flat", "detail_texture", "detail_construction"}
    )
    if max_leak >= 0.75 or avg_leak >= 0.58:
        risk = "high"
    elif max_leak >= 0.55 or avg_leak >= 0.42:
        risk = "medium"
    else:
        risk = "low"
    return {
        "avg_styling_leak_risk": round(avg_leak, 3),
        "max_styling_leak_risk": round(max_leak, 3),
        "identity_reference_risk": risk,
        "worn_reference_count": worn_count,
        "detail_reference_count": detail_count,
    }


def _build_small_input_result(
    unique_rows: List[dict[str, Any]],
    duplicate_count: int,
    unified_triage: Optional[dict[str, Any]],
) -> dict[str, Any]:
    detail_rows = sorted(
        [row for row in unique_rows if row["role"] in {"detail_flat", "detail_texture", "detail_construction"}],
        key=lambda x: (x["identity_safe_score"], x["detail_score"], -x["styling_leak_risk"]),
        reverse=True,
    )
    identity_safe_rows = sorted(
        unique_rows,
        key=lambda x: (x["identity_safe_score"], x["detail_score"], x["construction_readability"]),
        reverse=True,
    )
    anchor_rows = detail_rows[:2] if detail_rows else identity_safe_rows[: min(2, len(identity_safe_rows))]
    identity_safe = identity_safe_rows[: min(3, len(identity_safe_rows))]
    risk_stats = _compute_identity_risk_stats(unique_rows)
    return {
        "items": [
            {k: v for k, v in row.items() if k != "bytes"}
            for row in unique_rows
        ],
        "stats": {
            "raw_count": len(unique_rows) + duplicate_count,
            "unique_count": len(unique_rows),
            "duplicate_count": duplicate_count,
            "complex_garment": _is_complex_garment(unified_triage),
            "small_input_mode": True,
            **risk_stats,
        },
        "base_generation": [
            {"filename": row["filename"], "role": row["role"], "score": row["worn_score"], "detail_score": row["detail_score"]}
            for row in unique_rows
        ],
        "strict_single_pass": [
            {"filename": row["filename"], "role": row["role"], "score": row["worn_score"], "detail_score": row["detail_score"]}
            for row in unique_rows
        ],
        "edit_anchors": [
            {"filename": row["filename"], "role": row["role"], "score": row["detail_score"]}
            for row in anchor_rows
        ],
        "selected_bytes": {
            "base_generation": [row["bytes"] for row in unique_rows],
            "strict_single_pass": [row["bytes"] for row in unique_rows],
            "edit_anchors": [row["bytes"] for row in anchor_rows],
            "identity_safe": [row["bytes"] for row in identity_safe],
        },
        "selected_names": {
            "base_generation": [row["filename"] for row in unique_rows],
            "strict_single_pass": [row["filename"] for row in unique_rows],
            "edit_anchors": [row["filename"] for row in anchor_rows],
            "identity_safe": [row["filename"] for row in identity_safe],
        },
        "unified_triage": unified_triage,
    }


def _is_complex_garment(unified_triage: Optional[dict[str, Any]]) -> bool:
    if not unified_triage:
        return False
    contract = (unified_triage.get("structural_contract") or {}) if isinstance(unified_triage, dict) else {}
    subtype = str(contract.get("garment_subtype", ""))
    volume = str(contract.get("silhouette_volume", ""))
    sleeve_type = str(contract.get("sleeve_type", ""))
    return subtype in {"ruana_wrap", "poncho", "cape", "kimono"} or volume in {"draped", "oversized"} or sleeve_type in {"cape_like", "dolman_batwing"}


def select_reference_subsets(
    uploaded_images: List[bytes],
    filenames: Optional[List[str]] = None,
    user_prompt: Optional[str] = None,
) -> dict[str, Any]:
    if not uploaded_images:
        return {
            "items": [],
            "stats": {"raw_count": 0, "unique_count": 0, "duplicate_count": 0},
            "base_generation": [],
            "strict_single_pass": [],
            "edit_anchors": [],
            "unified_triage": None,
        }

    filenames = filenames or [f"image_{i+1}" for i in range(len(uploaded_images))]
    unique_rows: List[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    duplicate_count = 0

    for idx, img in enumerate(uploaded_images):
        sha = _sha1(img)
        if sha in seen_hashes:
            duplicate_count += 1
            continue
        seen_hashes.add(sha)

        local = _analyze_image(img)
        role_info = _infer_reference_role(img, user_prompt=user_prompt)
        row = {
            "index": idx,
            "filename": filenames[idx] if idx < len(filenames) else f"image_{idx+1}",
            "sha1": sha,
            "bytes": img,
            "local_quality_score": round(float(local.get("score", 0.0) or 0.0), 3),
            "local_luma": round(float(local.get("luma", 0.0) or 0.0), 3),
            "local_edge": round(float(local.get("edge", 0.0) or 0.0), 3),
            "local_ratio": round(float(local.get("ratio", 1.0) or 1.0), 3),
            **role_info,
        }
        row["worn_score"] = round(_score_worn_candidate(row), 3)
        row["detail_score"] = round(_score_detail_candidate(row), 3)
        row["identity_safe_score"] = round(_score_identity_safe_candidate(row), 3)
        unique_rows.append(row)

    unified_triage = _infer_unified_vision_triage([row["bytes"] for row in unique_rows[:6]], user_prompt)
    if len(unique_rows) <= 2:
        return _build_small_input_result(unique_rows, duplicate_count, unified_triage)

    complex_garment = _is_complex_garment(unified_triage)

    worn_rows = sorted(
        [row for row in unique_rows if row["role"] in {"worn_front", "worn_three_quarter", "worn_side"}],
        key=lambda x: (x["worn_score"], x["silhouette_readability"], x["construction_readability"]),
        reverse=True,
    )
    worn_primary = [row for row in worn_rows if row["role"] in {"worn_front", "worn_three_quarter"}]
    worn_diverse = [
        row for row in worn_rows
        if row["role"] in {"worn_side", "worn_three_quarter"}
        and row["silhouette_readability"] >= 0.6
    ]
    detail_rows = sorted(
        [row for row in unique_rows if row["role"] in {"detail_flat", "detail_texture", "detail_construction"}],
        key=lambda x: (x["detail_score"], x["identity_safe_score"], x["construction_readability"], x["texture_readability"]),
        reverse=True,
    )

    used_hashes: set[str] = set()
    base_generation: List[dict[str, Any]] = []
    base_generation.extend(_pick_top(worn_primary, 2, used_hashes))
    if len(base_generation) < 2:
        base_generation.extend(_pick_top(worn_rows, 2 - len(base_generation), used_hashes))
    if worn_diverse:
        base_generation.extend(_pick_top([row for row in worn_diverse if row["sha1"] not in used_hashes], 1, used_hashes))

    extra_worn = [row for row in worn_rows if row["sha1"] not in used_hashes and row["worn_score"] >= 0.55]
    if extra_worn:
        base_generation.extend(_pick_top(extra_worn, 1 if len(base_generation) >= 3 else 2, used_hashes))

    if len(base_generation) < 4:
        detail_fill = [row for row in detail_rows if row["sha1"] not in used_hashes]
        need = 4 - len(base_generation)
        if not complex_garment:
            need = min(need, 1)
        base_generation.extend(_pick_top(detail_fill, need, used_hashes))

    used_hashes = set()
    strict_single_pass: List[dict[str, Any]] = []
    strict_single_pass.extend(_pick_top(worn_primary, 1, used_hashes))
    if worn_diverse:
        strict_single_pass.extend(_pick_top([row for row in worn_diverse if row["sha1"] not in used_hashes], 1, used_hashes))
    if len(strict_single_pass) < 2:
        strict_single_pass.extend(_pick_top(worn_rows, 2 - len(strict_single_pass), used_hashes))
    strict_single_pass.extend(_pick_top(detail_rows, 1, used_hashes))
    strong_detail_rows = [row for row in detail_rows if row["sha1"] not in used_hashes and row["detail_score"] >= 0.72]
    if complex_garment and strong_detail_rows:
        strict_single_pass.extend(_pick_top(strong_detail_rows, 1, used_hashes))
    if len(strict_single_pass) < 3:
        worn_fill = [row for row in worn_rows if row["sha1"] not in used_hashes]
        strict_single_pass.extend(_pick_top(worn_fill, 3 - len(strict_single_pass), used_hashes))

    used_hashes = set()
    edit_anchors: List[dict[str, Any]] = []
    edit_anchors.extend(_pick_top(detail_rows, 2, used_hashes))
    if len(edit_anchors) < 2:
        worn_fill = sorted(
            [
                row for row in worn_rows
                if row["sha1"] not in used_hashes and row["styling_leak_risk"] <= 0.45
            ],
            key=lambda x: (x["identity_safe_score"], x["worn_score"]),
            reverse=True,
        )
        if not worn_fill:
            worn_fill = sorted(
                [row for row in worn_rows if row["sha1"] not in used_hashes],
                key=lambda x: (x["identity_safe_score"], x["worn_score"]),
                reverse=True,
            )
        edit_anchors.extend(_pick_top(worn_fill, 2 - len(edit_anchors), used_hashes))

    used_hashes = set()
    identity_safe: List[dict[str, Any]] = []
    identity_safe.extend(_pick_top(detail_rows, 2, used_hashes))
    low_leak_worn = sorted(
        [
            row for row in worn_rows
            if row["sha1"] not in used_hashes
            and row["styling_leak_risk"] <= 0.45
            and row["background_noise"] <= 0.65
        ],
        key=lambda x: (x["identity_safe_score"], x["worn_score"], x["silhouette_readability"]),
        reverse=True,
    )
    if low_leak_worn:
        identity_safe.extend(_pick_top(low_leak_worn, 2 if complex_garment else 1, used_hashes))
    if len(identity_safe) < 2:
        worn_fallback = sorted(
            [row for row in worn_rows if row["sha1"] not in used_hashes],
            key=lambda x: (x["identity_safe_score"], x["worn_score"]),
            reverse=True,
        )
        identity_safe.extend(_pick_top(worn_fallback, 2 - len(identity_safe), used_hashes))

    risk_stats = _compute_identity_risk_stats(unique_rows)
    return {
        "items": [
            {
                k: v for k, v in row.items()
                if k != "bytes"
            }
            for row in unique_rows
        ],
        "stats": {
            "raw_count": len(uploaded_images),
            "unique_count": len(unique_rows),
            "duplicate_count": duplicate_count,
            "complex_garment": complex_garment,
            "small_input_mode": False,
            **risk_stats,
        },
        "base_generation": [
            {"filename": row["filename"], "role": row["role"], "score": row["worn_score"], "detail_score": row["detail_score"]}
            for row in base_generation
        ],
        "strict_single_pass": [
            {"filename": row["filename"], "role": row["role"], "score": row["worn_score"], "detail_score": row["detail_score"]}
            for row in strict_single_pass
        ],
        "edit_anchors": [
            {"filename": row["filename"], "role": row["role"], "score": row["detail_score"]}
            for row in edit_anchors
        ],
        "selected_bytes": {
            "base_generation": [row["bytes"] for row in base_generation],
            "strict_single_pass": [row["bytes"] for row in strict_single_pass],
            "edit_anchors": [row["bytes"] for row in edit_anchors],
            "identity_safe": [row["bytes"] for row in identity_safe],
        },
        "selected_names": {
            "base_generation": [row["filename"] for row in base_generation],
            "strict_single_pass": [row["filename"] for row in strict_single_pass],
            "edit_anchors": [row["filename"] for row in edit_anchors],
            "identity_safe": [row["filename"] for row in identity_safe],
        },
        "unified_triage": unified_triage,
    }
