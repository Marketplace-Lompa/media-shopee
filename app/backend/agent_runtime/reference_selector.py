"""
Reference selector — versão simplificada (Fase 1 Prompt-First).

Antes: N+1 chamadas Gemini (1 por imagem × N + 1 unified_triage) para
       classificar roles e ranquear subsets com fórmulas aritméticas.

Depois: 1 chamada Gemini (unified_triage) + dedup por hash.
        Todas as imagens únicas vão para TODOS os subsets.
        O Nano decide sozinho quais fotos olhar — ele é multimodal nativo.

Interface de retorno mantida 100% retrocompatível com pipeline_v2.py.
"""
from __future__ import annotations

from typing import Any, List, Optional

from agent_runtime.triage import _infer_unified_vision_triage
from pipeline_effectiveness import _analyze_image, _sha1


def _is_complex_garment(unified_triage: Optional[dict[str, Any]]) -> bool:
    if not unified_triage:
        return False
    contract = (
        (unified_triage.get("structural_contract") or {})
        if isinstance(unified_triage, dict)
        else {}
    )
    subtype = str(contract.get("garment_subtype", ""))
    volume = str(contract.get("silhouette_volume", ""))
    sleeve_type = str(contract.get("sleeve_type", ""))
    return (
        subtype in {"ruana_wrap", "poncho", "cape", "kimono"}
        or volume in {"draped", "oversized"}
        or sleeve_type in {"cape_like", "dolman_batwing"}
    )


def _derive_identity_risk_from_triage(
    unified_triage: Optional[dict[str, Any]],
    n_images: int,
) -> dict[str, Any]:
    """
    Deriva identity_risk da triagem unificada em vez de scoring individual.

    Heurística simples:
    - Se a triagem menciona 'model', 'face', 'person' na image_analysis
      e há poucas fotos de detalhe → risk medium/high
    - Caso contrário → low
    """
    if not unified_triage or not isinstance(unified_triage, dict):
        return {
            "avg_styling_leak_risk": 0.0,
            "max_styling_leak_risk": 0.0,
            "identity_reference_risk": "low",
            "worn_reference_count": 0,
            "detail_reference_count": 0,
        }

    analysis = str(unified_triage.get("image_analysis") or "").lower()
    contract = unified_triage.get("structural_contract") or {}
    garment_hint = str(unified_triage.get("garment_hint") or "").lower()

    # Sinais de risco: model dominando as referências
    model_signals = sum(1 for token in ("model", "face", "person", "wearing", "posing", "worn")
                        if token in analysis)
    detail_signals = sum(1 for token in ("flat", "detail", "texture", "close-up", "folded", "hanger")
                         if token in analysis)

    if model_signals >= 3 and detail_signals <= 1:
        risk = "high"
    elif model_signals >= 2 and detail_signals <= 1:
        risk = "medium"
    else:
        risk = "low"

    return {
        "avg_styling_leak_risk": 0.0,  # Não calculado individualmente
        "max_styling_leak_risk": 0.0,
        "identity_reference_risk": risk,
        "worn_reference_count": 0,
        "detail_reference_count": 0,
    }


def select_reference_subsets(
    uploaded_images: List[bytes],
    filenames: Optional[List[str]] = None,
    user_prompt: Optional[str] = None,
) -> dict[str, Any]:
    """
    Versão simplificada: dedup por hash + 1 triagem unificada.
    Todas as imagens únicas vão para todos os subsets — o Nano decide o que olhar.
    """
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

    # ─── Dedup por hash (manter — trivial e útil) ─────────────────
    unique_rows: List[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    duplicate_count = 0

    for idx, img in enumerate(uploaded_images):
        sha = _sha1(img)
        if sha in seen_hashes:
            duplicate_count += 1
            continue
        seen_hashes.add(sha)

        # Análise local (PIL, sem API — zero custo)
        local = _analyze_image(img)
        row = {
            "index": idx,
            "filename": filenames[idx] if idx < len(filenames) else f"image_{idx+1}",
            "sha1": sha,
            "bytes": img,
            "local_quality_score": round(float(local.get("score", 0.0) or 0.0), 3),
            "local_luma": round(float(local.get("luma", 0.0) or 0.0), 3),
            "local_edge": round(float(local.get("edge", 0.0) or 0.0), 3),
            "local_ratio": round(float(local.get("ratio", 1.0) or 1.0), 3),
        }
        unique_rows.append(row)

    # ─── 1 chamada Gemini: triagem unificada (contexto semântico) ──
    unified_triage = _infer_unified_vision_triage(
        [row["bytes"] for row in unique_rows[:6]],
        user_prompt,
    )

    complex_garment = _is_complex_garment(unified_triage)
    risk_stats = _derive_identity_risk_from_triage(unified_triage, len(unique_rows))

    # ─── Todos os subsets = todas as imagens únicas ────────────────
    all_bytes = [row["bytes"] for row in unique_rows]
    all_names = [row["filename"] for row in unique_rows]
    item_summaries = [
        {
            "filename": row["filename"],
            "role": "all",
            "score": row["local_quality_score"],
            "detail_score": row["local_quality_score"],
        }
        for row in unique_rows
    ]

    return {
        "items": [
            {k: v for k, v in row.items() if k != "bytes"}
            for row in unique_rows
        ],
        "stats": {
            "raw_count": len(uploaded_images),
            "unique_count": len(unique_rows),
            "duplicate_count": duplicate_count,
            "complex_garment": complex_garment,
            "small_input_mode": len(unique_rows) <= 2,
            **risk_stats,
        },
        "base_generation": item_summaries,
        "strict_single_pass": item_summaries,
        "edit_anchors": item_summaries,
        "selected_bytes": {
            "base_generation": all_bytes,
            "strict_single_pass": all_bytes,
            "edit_anchors": all_bytes,
            "identity_safe": all_bytes,
        },
        "selected_names": {
            "base_generation": all_names,
            "strict_single_pass": all_names,
            "edit_anchors": all_names,
            "identity_safe": all_names,
        },
        "unified_triage": unified_triage,
    }
