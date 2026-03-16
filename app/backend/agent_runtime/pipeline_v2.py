"""
Pipeline V2 — orquestrador unico de producao.

Fluxo fixo:
1. reference_selector classifica uploads por role visual
2. generate_images() cria base fiel da peca (stage 1, locks fortes)
3. sample_art_direction() + edit_image() cria imagem final (stage 2, liberdade criativa)
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
import re
from typing import Any, Callable, Optional

from agent_runtime.pipeline_v2_observability import write_v2_observability_report
from agent_runtime.art_direction_sampler import commit_art_direction_choice, sample_art_direction
from agent_runtime.curation_policy import (
    POSE_FLEX_HINTS as _POSE_FLEX_HINTS,
    build_affinity_prompt as _policy_build_affinity_prompt,
    derive_reference_budget as _policy_reference_budget,
    derive_reference_guard_config as _policy_reference_guard_config,
    normalize_pose_flex_mode as _policy_normalize_pose_flex_mode,
    resolve_auto_pose_flex_mode as _policy_resolve_auto_pose_flex_mode,
    stage1_candidate_count as _policy_stage1_candidate_count,
)
from agent_runtime.fidelity_gate import (
    build_targeted_repair_prompt,
    build_fidelity_repair_patch,
    build_visual_fidelity_gate_policy,
    classify_stage2_repair_strategy,
    evaluate_visual_fidelity,
    suggest_retry_pose_flex_mode,
)
from agent_runtime.reference_selector import select_reference_subsets
from agent_runtime.structural import get_set_member_labels, get_set_member_keys
from agent_runtime.two_pass_flow import (
    build_art_direction_two_pass_edit_prompt,
    build_structure_guard_clauses,
    build_structural_hint,
)
from generator import edit_image, generate_images
from pipeline_effectiveness import assess_generated_image
from config import OUTPUTS_DIR
from request_validation import validate_generation_params


_POSE_FLEX_MODES = {"auto", "controlled", "balanced", "dynamic"}


def _targeted_stage2_repair_enabled() -> bool:
    raw = os.getenv("ENABLE_TARGETED_STAGE2_REPAIR", "true").strip().lower()
    return raw != "false"


def _guess_image_extension(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "webp"
    return "jpg"


def _safe_asset_slug(raw_name: str, *, fallback: str) -> str:
    name = str(raw_name or "").strip().lower()
    stem = Path(name).stem if name else fallback
    slug = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return slug[:48] or fallback


def _persist_review_inputs(
    *,
    session_id: str,
    uploaded_bytes: list[bytes],
    uploaded_filenames: list[str],
    selected_bytes: dict[str, Any],
    selected_names: dict[str, Any],
) -> dict[str, list[str]]:
    review_dir = OUTPUTS_DIR / f"v2diag_{session_id}" / "inputs"
    review_dir.mkdir(parents=True, exist_ok=True)

    def _write_group(group_name: str, items: list[bytes], names: list[str]) -> list[str]:
        group_dir = review_dir / group_name
        group_dir.mkdir(parents=True, exist_ok=True)
        urls: list[str] = []
        for idx, item in enumerate(items):
            slug = _safe_asset_slug(names[idx] if idx < len(names) else "", fallback=f"{group_name}_{idx + 1}")
            ext = _guess_image_extension(item)
            filename = f"{idx + 1:02d}_{slug}.{ext}"
            target = group_dir / filename
            target.write_bytes(item)
            urls.append(f"/outputs/v2diag_{session_id}/inputs/{group_name}/{filename}")
        return urls

    original_urls = _write_group("original_references", uploaded_bytes, uploaded_filenames)
    base_generation_urls = _write_group(
        "base_generation",
        list(selected_bytes.get("base_generation", []) or []),
        list(selected_names.get("base_generation", []) or []),
    )
    edit_anchor_urls = _write_group(
        "edit_anchors",
        list(selected_bytes.get("edit_anchors", []) or []),
        list(selected_names.get("edit_anchors", []) or []),
    )
    identity_safe_urls = _write_group(
        "identity_safe",
        list(selected_bytes.get("identity_safe", []) or []),
        list(selected_names.get("identity_safe", []) or []),
    )
    return {
        "original_references": original_urls,
        "base_generation": base_generation_urls,
        "edit_anchors": edit_anchor_urls,
        "identity_safe": identity_safe_urls,
    }


def _should_use_image_grounding(
    structural_contract: Optional[dict[str, Any]],
    image_analysis: Optional[str],
    gate_policy: Optional[dict[str, Any]],
    n_uploaded: int,
) -> bool:
    """
    Decide se deve ativar Google Image Search grounding para esta geração.

    Critérios de ativação (qualquer um satisfeito):
    - Garment é subtipo incomum/draped que o modelo pode confundir (ruana, poncho, cape, kimono)
    - Gate detectou garment complexo ou drape architecture especial
    - Image analysis descreve padrão específico (chevron, diagonal, crochet radiante)
      que o modelo pode não renderizar corretamente sem referências visuais adicionais
    - Poucas referências do usuário (< 3) para garment de alta fidelidade

    Critérios de NÃO ativação:
    - Garment comum (t-shirt, hoodie, basic knit) — modelo já sabe
    - Muitas referências de alta qualidade (>= 4) — contexto suficiente
    - Variação de cor simples — queremos cor específica do usuário, não web
    """
    contract = structural_contract or {}
    ia = str(image_analysis or "").lower()
    gate = gate_policy or {}

    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    confidence = float(contract.get("confidence", 1.0) or 1.0)
    gate_reasons = [str(r).lower() for r in (gate.get("reasons") or [])]

    # Subtypes que se beneficiam de contexto visual extra da web
    _complex_subtypes = {
        "ruana_wrap", "poncho", "cape", "kimono", "bolero",
        "cape_like", "draped_wrap",
    }

    # Padrões que o modelo tende a errar sem referência visual extra
    _pattern_keywords = (
        "chevron", "diagonal", "radiating", "concentric", "crochet",
        "crochê", "handmade", "artisanal", "boucle", "bouclê",
        "patchwork", "jacquard", "intarsia", "fair isle",
    )

    reasons: list[str] = []

    if subtype in _complex_subtypes:
        reasons.append(f"complex_subtype:{subtype}")

    if any(r in gate_reasons for r in (
        "complex_garment", "draped_subtype", "cape_like", "sleeve_architecture"
    )):
        reasons.append("gate_complex_garment")

    if ia and any(kw in ia for kw in _pattern_keywords):
        reasons.append("distinctive_pattern_in_analysis")

    if n_uploaded < 3 and subtype in _complex_subtypes:
        reasons.append("few_refs_complex_garment")

    if confidence < 0.7:
        reasons.append(f"low_triage_confidence:{confidence:.2f}")

    active = bool(reasons)
    if active:
        print(f"[IMAGE_GROUNDING] ✅ ativado — razões: {reasons}")
    else:
        print(f"[IMAGE_GROUNDING] ⏭ skipped — garment:{subtype}, refs:{n_uploaded}, confidence:{confidence:.2f}")

    return active


def _derive_garment_material_text(
    structural_contract: Optional[dict[str, Any]],
    image_analysis: Optional[str],
) -> str:
    text = f"{str(image_analysis or '')} {str((structural_contract or {}).get('garment_subtype', '') or '')}".lower()
    if any(token in text for token in ("crochet", "crochê")):
        return "crochet knit"
    if any(token in text for token in ("tricô", "tricot", "knit")):
        return "knit fabric"
    if any(token in text for token in ("lã", "wool")):
        return "wool knit"
    if any(token in text for token in ("malha", "jersey")):
        return "soft jersey fabric"
    if any(token in text for token in ("linho", "linen")):
        return "linen fabric"
    if any(token in text for token in ("viscose", "viscose")):
        return "viscose fabric"
    return "garment fabric"


def _build_v2_classifier_summary(
    structural_contract: Optional[dict[str, Any]],
    selector_stats: Optional[dict[str, Any]],
) -> dict[str, Any]:
    subtype = str((structural_contract or {}).get("garment_subtype", "") or "").strip().lower()
    complex_garment = bool((selector_stats or {}).get("complex_garment"))
    if subtype in {"ruana_wrap", "poncho", "cape", "kimono", "jacket"}:
        category = "outerwear"
    elif complex_garment:
        category = "complex_knit"
    else:
        category = "general"
    return {"garment_category": category}


def _build_stage1_prompt(
    structural_contract: Optional[dict[str, Any]],
    structural_hint: Optional[str],
    set_detection: Optional[dict[str, Any]] = None,
    fidelity_mode: str = "balanceada",
    preset: str = "",
    angle_directive: str = "",
    look_contract: Optional[dict[str, Any]] = None,
) -> str:
    """Prompt curto e reproduzivel para stage 1: base fiel da peca."""
    structure_guards = build_structure_guard_clauses(structural_contract, set_detection=set_detection)
    set_info = set_detection or {}
    preset_hint = str(preset or "").strip().lower()
    included_labels = get_set_member_labels(
        set_info,
        include_policies={"must_include", "optional"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )
    must_include_keys = get_set_member_keys(
        set_info,
        include_policies={"must_include"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )
    keep_matching_scarf = "scarf" in must_include_keys
    accessory_guard = (
        (
            "Preserve coordinated set members from the references as distinct product pieces and do not fuse them into the main garment. "
            + ("Preserve the matching coordinated scarf because it belongs to the garment set. " if keep_matching_scarf else "")
        )
        if included_labels else
        "Do not add pins, brooches, belts, scarves, jewelry, or decorative garment accessories. "
    )

    if preset_hint == "ugc_real_br":
        parts = [
            "Ultra-realistic fashion photo of a natural adult woman wearing the garment.",
            "Realistic skin texture, natural body proportions, relaxed readable stance, full garment clearly visible.",
            "Neutral believable real-life indoor composition with ordinary soft light and no campaign polish.",
            "Preserve exact garment geometry, texture continuity, and construction details.",
        ]
    else:
        parts = [
            "Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment.",
            "Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible.",
            "Clean premium indoor composition, soft natural daylight.",
            "Preserve exact garment geometry, texture continuity, and construction details.",
        ]
    # angle_directive governa o ângulo/crop desta slot — entra como instrução #2 (após a descrição do sujeito humano) para evitar a perda da modelo na foto
    if angle_directive:
        parts.insert(1, angle_directive)
    if structural_hint:
        parts.append(f"Garment identity: {structural_hint}.")
    if structure_guards:
        parts.append("Non-negotiable structure guards: " + "; ".join(structure_guards) + ".")
    parts.append(
        "Treat the garment as the fixed object and build the model, camera, and background around it. "
        "Never reshape the garment to solve composition."
    )
    if str(fidelity_mode).strip().lower() == "estrita":
        parts.append("Prioritize exact garment fidelity over editorial variation and avoid any reinterpretation of silhouette, length, or stitch logic.")
    if preset_hint == "ugc_real_br":
        styling_intro = (
            "Keep styling simple, believable, and secondary to the garment. "
            "Avoid showroom polish or campaign props. "
        )
    else:
        styling_intro = (
            "Catalog-ready minimal styling with the garment as the hero piece. "
            "Keep accessories subtle and secondary to the garment. "
        )
    parts.append(
        styling_intro
        + accessory_guard
        + "Do not promote inner tops, jewelry, shoes, or unrelated accessories into coordinated product pieces. "
        + "Build new styling independent from the reference person's lower-body look, footwear, and props."
    )
    # look_contract: guia de coerência de look gerado pelo triage — bottom preferido + proibidos
    if look_contract and float(look_contract.get("confidence", 0) or 0) > 0.5:
        _lc_bottom = str(look_contract.get("bottom_style") or "").strip()
        _lc_forbidden = [str(x).strip() for x in (look_contract.get("forbidden_bottoms") or []) if str(x).strip()]
        if _lc_bottom:
            parts.append(f"Preferred lower-body styling: {_lc_bottom}.")
        if _lc_forbidden:
            parts.append(f"Avoid these lower-body types (incoherent with this garment): {', '.join(_lc_forbidden)}.")
    return " ".join(parts)


def _merge_reference_bytes(*groups: list[bytes]) -> list[bytes]:
    merged: list[bytes] = []
    seen: set[bytes] = set()
    for group in groups:
        for item in group:
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
    return merged


def _merge_reference_names(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            name = str(item or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            merged.append(name)
    return merged


def _limit_reference_pack(
    ref_bytes: list[bytes],
    ref_names: list[str],
    *,
    limit: int,
) -> tuple[list[bytes], list[str]]:
    if limit <= 0:
        return [], []
    return list(ref_bytes[:limit]), list(ref_names[:limit])


def _runtime_reference_budget(
    *,
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
    identity_risk: str,
) -> dict[str, int]:
    return _policy_reference_budget(
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
        identity_risk=identity_risk,
    )


def _build_affinity_prompt(
    user_prompt: Optional[str],
    preset: str,
    scene_preference: str,
) -> Optional[str]:
    return _policy_build_affinity_prompt(user_prompt, preset, scene_preference)


def _reference_guard_config(
    *,
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
) -> tuple[str, list[str]]:
    return _policy_reference_guard_config(
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
    )


def _pose_flex_strategy(
    *,
    user_prompt: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
    preset: str,
) -> str:
    return _policy_resolve_auto_pose_flex_mode(
        user_prompt=user_prompt,
        structural_contract=structural_contract,
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
        preset=preset,
    )


def _normalize_pose_flex_mode(raw_mode: Optional[str]) -> str:
    return _policy_normalize_pose_flex_mode(raw_mode)


def _stage1_candidate_count(
    *,
    fidelity_mode: str,
    selector_stats: Optional[dict[str, Any]],
) -> int:
    return _policy_stage1_candidate_count(
        fidelity_mode=fidelity_mode,
        selector_stats=selector_stats,
    )


def _stage1_selection_key(assessment: dict[str, Any], gate_result: Optional[dict[str, Any]]) -> tuple[float, float, float, float]:
    if gate_result and gate_result.get("available"):
        verdict_rank = {
            "pass": 2.0,
            "soft_fail": 1.0,
            "hard_fail": 0.0,
        }.get(str(gate_result.get("verdict", "") or "").strip().lower(), 0.0)
        return (
            verdict_rank,
            float(gate_result.get("fidelity_score", 0.0) or 0.0),
            float(gate_result.get("structure_fidelity", 0.0) or 0.0),
            float(assessment.get("technical_score", 0.0) or 0.0),
        )
    return (
        float(assessment.get("candidate_score", 0.0) or 0.0),
        float(assessment.get("technical_score", 0.0) or 0.0),
        0.0,
        0.0,
    )


def _pick_best_stage1_candidate(
    candidates: list[dict[str, Any]],
    stage1_prompt: str,
    classifier_summary: dict[str, Any],
    gate_policy: Optional[dict[str, Any]] = None,
    gate_reference_bytes: Optional[list[bytes]] = None,
    structural_contract: Optional[dict[str, Any]] = None,
    set_detection: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    assessments: list[dict[str, Any]] = []
    best_idx = 0
    best_key = (-1.0, -1.0, -1.0, -1.0)
    gate_enabled = bool((gate_policy or {}).get("enabled"))
    judge_refs = list(gate_reference_bytes or [])

    for idx, candidate in enumerate(candidates):
        candidate_path = str(candidate.get("path", "") or "")
        assessment = assess_generated_image(candidate_path, stage1_prompt, classifier_summary)
        gate_result = None
        if gate_enabled and judge_refs:
            gate_result = evaluate_visual_fidelity(
                stage="stage1",
                reference_images=judge_refs,
                candidate_image_path=candidate_path,
                structural_contract=structural_contract,
                set_detection=set_detection,
                prompt=stage1_prompt,
            )
        assessments.append(
            {
                "index": idx + 1,
                "filename": candidate.get("filename"),
                "url": candidate.get("url"),
                "path": candidate.get("path"),
                "assessment": assessment,
                "fidelity_gate": gate_result,
            }
        )
        key = _stage1_selection_key(assessment, gate_result)
        if key > best_key:
            best_key = key
            best_idx = idx

    return candidates[best_idx], assessments, best_idx + 1


def run_pipeline_v2(
    *,
    uploaded_bytes: list[bytes],
    uploaded_filenames: Optional[list[str]] = None,
    prompt: Optional[str] = None,
    preset: str = "marketplace_lifestyle",
    scene_preference: str = "auto_br",
    fidelity_mode: str = "balanceada",
    pose_flex_mode: str = "auto",
    n_images: int = 1,
    aspect_ratio: str = "4:5",
    resolution: str = "1K",
    art_direction_request: Optional[dict[str, Any]] = None,
    on_stage: Optional[Callable[[str, dict[str, Any]], None]] = None,
) -> dict[str, Any]:
    """
    Orquestrador principal v2.

    Returns dict compativel com GenerateResponse.
    """
    started = time.time()
    session_id = str(uuid.uuid4())[:8]

    def _emit(stage: str, data: Optional[dict[str, Any]] = None) -> None:
        if on_stage:
            on_stage(stage, data or {})

    validate_generation_params(
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        n_images=n_images,
    )

    if not uploaded_bytes:
        raise ValueError("Pipeline v2 requer pelo menos 1 imagem de referencia")

    # ── 1. Reference selection ────────────────────────────────────────────────
    _emit("preparing_references", {"message": "Classificando referencias..."})

    filenames: list[str] = []
    for i in range(len(uploaded_bytes)):
        raw_name = ""
        if uploaded_filenames and i < len(uploaded_filenames):
            raw_name = str(uploaded_filenames[i] or "").strip()
        filenames.append(raw_name or f"upload_{i + 1}")
    selector_result = select_reference_subsets(
        uploaded_images=uploaded_bytes,
        filenames=filenames,
        user_prompt=prompt,
    )

    unified_triage = selector_result.get("unified_triage") or {}
    structural_contract = (
        (unified_triage.get("structural_contract") or {})
        if isinstance(unified_triage, dict)
        else {}
    )
    set_detection = (
        (unified_triage.get("set_detection") or {})
        if isinstance(unified_triage, dict)
        else {}
    )
    image_analysis = str((unified_triage.get("image_analysis") or "") if isinstance(unified_triage, dict) else "").strip()
    lighting_signature = (
        (unified_triage.get("lighting_signature") or {})
        if isinstance(unified_triage, dict)
        else {}
    )
    look_contract = (
        (unified_triage.get("look_contract") or {})
        if isinstance(unified_triage, dict)
        else {}
    )
    garment_aesthetic = (
        (unified_triage.get("garment_aesthetic") or {})
        if isinstance(unified_triage, dict)
        else {}
    )
    if structural_contract:
        structural_contract["enabled"] = True

    structural_hint = build_structural_hint(structural_contract)

    selected_bytes = selector_result.get("selected_bytes", {}) or {}
    selected_names = selector_result.get("selected_names", {}) or {}
    selector_stats = selector_result.get("stats", {}) or {}
    review_input_assets = _persist_review_inputs(
        session_id=session_id,
        uploaded_bytes=uploaded_bytes,
        uploaded_filenames=filenames,
        selected_bytes=selected_bytes,
        selected_names=selected_names,
    )
    base_generation_bytes = list(selected_bytes.get("base_generation", []) or [])
    strict_single_pass_bytes = list(selected_bytes.get("strict_single_pass", []) or [])
    edit_anchor_bytes = list(selected_bytes.get("edit_anchors", []) or [])
    identity_safe_bytes = list(selected_bytes.get("identity_safe", []) or [])
    base_generation_names = list(selected_names.get("base_generation", []) or [])
    strict_single_pass_names = list(selected_names.get("strict_single_pass", []) or [])
    edit_anchor_names = list(selected_names.get("edit_anchors", []) or [])
    identity_safe_names = list(selected_names.get("identity_safe", []) or [])
    reference_guard_strength, reference_usage_rules = _reference_guard_config(
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
    )
    identity_risk = str((selector_stats or {}).get("identity_reference_risk", "low") or "low").strip().lower()
    requested_pose_flex_mode = _normalize_pose_flex_mode(pose_flex_mode)
    if requested_pose_flex_mode == "auto":
        resolved_pose_flex_mode = _pose_flex_strategy(
            user_prompt=prompt,
            structural_contract=structural_contract,
            selector_stats=selector_stats,
            fidelity_mode=fidelity_mode,
            preset=preset,
        )
    else:
        resolved_pose_flex_mode = requested_pose_flex_mode
    pose_flex_hint = _POSE_FLEX_HINTS.get(resolved_pose_flex_mode, _POSE_FLEX_HINTS["balanced"])

    if str(fidelity_mode).strip().lower() == "estrita":
        base_gen_bytes = strict_single_pass_bytes or base_generation_bytes
        base_gen_names = strict_single_pass_names or base_generation_names
        edit_reference_bytes = _merge_reference_bytes(edit_anchor_bytes, identity_safe_bytes[:3])
        edit_reference_names = _merge_reference_names(edit_anchor_names, identity_safe_names[:3])
        if not edit_reference_bytes:
            edit_reference_bytes = _merge_reference_bytes(edit_anchor_bytes, strict_single_pass_bytes[:2])
            edit_reference_names = _merge_reference_names(edit_anchor_names, strict_single_pass_names[:2])
    else:
        base_gen_bytes = base_generation_bytes or strict_single_pass_bytes
        base_gen_names = base_generation_names or strict_single_pass_names
        if bool(selector_stats.get("complex_garment")):
            edit_reference_bytes = _merge_reference_bytes(edit_anchor_bytes, identity_safe_bytes[:3])
            edit_reference_names = _merge_reference_names(edit_anchor_names, identity_safe_names[:3])
        else:
            edit_reference_bytes = _merge_reference_bytes(edit_anchor_bytes, identity_safe_bytes[:2])
            edit_reference_names = _merge_reference_names(edit_anchor_names, identity_safe_names[:2])

    if not edit_reference_bytes:
        if identity_risk == "high":
            edit_reference_bytes = _merge_reference_bytes(
                identity_safe_bytes[:2],
                edit_anchor_bytes[:2],
                base_gen_bytes[:1],
            )
            edit_reference_names = _merge_reference_names(
                identity_safe_names[:2],
                edit_anchor_names[:2],
                base_gen_names[:1],
            )
        else:
            edit_reference_bytes = _merge_reference_bytes(
                identity_safe_bytes[:2],
                edit_anchor_bytes[:2],
                strict_single_pass_bytes[:2],
                base_gen_bytes[:2],
            )
            edit_reference_names = _merge_reference_names(
                identity_safe_names[:2],
                edit_anchor_names[:2],
                strict_single_pass_names[:2],
                base_gen_names[:2],
            )

    reference_budget = _runtime_reference_budget(
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
        identity_risk=identity_risk,
    )
    base_gen_bytes, base_gen_names = _limit_reference_pack(
        base_gen_bytes,
        base_gen_names,
        limit=int(reference_budget.get("stage1_max_refs", 4) or 4),
    )
    edit_reference_bytes, edit_reference_names = _limit_reference_pack(
        edit_reference_bytes,
        edit_reference_names,
        limit=int(reference_budget.get("stage2_max_refs", 4) or 4),
    )

    classifier_summary = _build_v2_classifier_summary(structural_contract, selector_stats)
    gate_policy = build_visual_fidelity_gate_policy(
        structural_contract=structural_contract,
        set_detection=set_detection,
        selector_stats=selector_stats,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=resolved_pose_flex_mode,
    )
    judge_reference_bytes = _merge_reference_bytes(
        strict_single_pass_bytes[: int(reference_budget.get("stage1_max_refs", 4) or 4)],
        base_generation_bytes[: int(reference_budget.get("stage1_max_refs", 4) or 4)],
        uploaded_bytes[:2],
    )[: int(reference_budget.get("judge_max_refs", 4) or 4)]
    observability_runs: list[dict[str, Any]] = []
    reason_codes: set[str] = set()
    if gate_policy.get("enabled"):
        reason_codes.update(str(item) for item in (gate_policy.get("reasons") or []))

    # Decidir se ativar Google Image Search grounding baseado no triage
    _use_image_grounding = _should_use_image_grounding(
        structural_contract=structural_contract,
        image_analysis=image_analysis,
        gate_policy=gate_policy,
        n_uploaded=len(uploaded_bytes),
    )

    effective_art_direction_request = dict(art_direction_request or {})
    effective_art_direction_request.setdefault("scene_preference", scene_preference)
    effective_art_direction_request.setdefault("preset", preset)
    effective_art_direction_request.setdefault("fidelity_mode", fidelity_mode)
    effective_art_direction_request.setdefault("pose_flex_mode", resolved_pose_flex_mode)
    effective_art_direction_request.setdefault("selector_stats", selector_stats)
    effective_art_direction_request.setdefault("structural_contract", structural_contract)
    effective_art_direction_request.setdefault("set_detection", set_detection)
    if lighting_signature:
        effective_art_direction_request.setdefault("lighting_signature", lighting_signature)
    if image_analysis:
        effective_art_direction_request.setdefault("image_analysis_hint", image_analysis[:400])
    if structural_hint:
        effective_art_direction_request.setdefault("structural_hint", structural_hint)
    if look_contract and float(look_contract.get("confidence", 0) or 0) > 0.5:
        effective_art_direction_request.setdefault("look_contract", look_contract)
    if garment_aesthetic:
        effective_art_direction_request.setdefault("garment_aesthetic", garment_aesthetic)
    directive_hints = effective_art_direction_request.get("directive_hints")
    if not isinstance(directive_hints, dict):
        directive_hints = {}
    directive_hints.setdefault(
        "model_context_hint",
        "brazilian fashion model casting with clearly new identity",
    )
    directive_hints.setdefault("pose_context_hint", pose_flex_hint)
    if identity_risk in {"medium", "high"}:
        directive_hints.setdefault(
            "custom_context_hint",
            "references are garment-only guidance; avoid identity and pose cloning from source photos",
        )
    effective_art_direction_request["directive_hints"] = directive_hints

    # ── 2. Generate base image (stage 1 — locks fortes) ──────────────────────
    _emit("stabilizing_garment", {"message": "Estabilizando a peca..."})

    # Extrair angle_directive para governar ângulo/crop em ambos os estágios
    _stage1_angle_directive = str(directive_hints.get("angle_directive", "") or "").strip()

    stage1_prompt = _build_stage1_prompt(
        structural_contract,
        structural_hint,
        set_detection=set_detection,
        fidelity_mode=fidelity_mode,
        preset=preset,
        angle_directive=_stage1_angle_directive,
        look_contract=look_contract,
    )

    stage1_candidate_count = _stage1_candidate_count(
        fidelity_mode=fidelity_mode,
        selector_stats=selector_stats,
    )

    base_results = generate_images(
        prompt=stage1_prompt,
        thinking_level="MINIMAL",
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        n_images=stage1_candidate_count,
        uploaded_images=base_gen_bytes,
        session_id=f"v2base_{session_id}",
        structural_hint=structural_hint,
        use_image_grounding=_use_image_grounding,
    )

    if not base_results:
        raise RuntimeError("Stage 1 falhou: nenhuma imagem base gerada")

    selected_base_result, stage1_candidates, selected_stage1_index = _pick_best_stage1_candidate(
        base_results,
        stage1_prompt,
        classifier_summary,
        gate_policy=gate_policy,
        gate_reference_bytes=judge_reference_bytes,
        structural_contract=structural_contract,
        set_detection=set_detection,
    )
    base_assessment_bundle = stage1_candidates[selected_stage1_index - 1]
    base_assessment = base_assessment_bundle["assessment"]
    stage1_gate = base_assessment_bundle.get("fidelity_gate")
    stage1_recovery: dict[str, Any] = {"applied": False}

    stage1_needs_retry = bool(
        gate_policy.get("stage1_retry_enabled")
        and stage1_gate
        and stage1_gate.get("available")
        and (
            stage1_gate.get("verdict") == "hard_fail"
            or (
                str(fidelity_mode).strip().lower() == "estrita"
                and stage1_gate.get("verdict") == "soft_fail"
            )
        )
    )
    if stage1_needs_retry:
        initial_stage1_gate = dict(stage1_gate or {}) if isinstance(stage1_gate, dict) else stage1_gate
        stage1_repair_patch = build_fidelity_repair_patch(
            stage="stage1",
            gate_result=stage1_gate,
            structural_contract=structural_contract,
            set_detection=set_detection,
        )
        stage1_retry_prompt = f"{stage1_prompt} {stage1_repair_patch}".strip()
        try:
            retry_results = generate_images(
                prompt=stage1_retry_prompt,
                thinking_level="MINIMAL",
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                n_images=stage1_candidate_count,
                uploaded_images=base_gen_bytes,
                session_id=f"v2base_retry_{session_id}",
                structural_hint=structural_hint,
            )
            retry_selected = None
            retry_candidates: list[dict[str, Any]] = []
            retry_selected_index = 0
            if retry_results:
                retry_selected, retry_candidates, retry_selected_index = _pick_best_stage1_candidate(
                    retry_results,
                    stage1_retry_prompt,
                    classifier_summary,
                    gate_policy=gate_policy,
                    gate_reference_bytes=judge_reference_bytes,
                    structural_contract=structural_contract,
                    set_detection=set_detection,
                )
                offset = len(stage1_candidates)
                for row in retry_candidates:
                    row["attempt"] = "retry"
                    row["index"] = offset + int(row.get("index", 0) or 0)
                retry_bundle = retry_candidates[retry_selected_index - 1]
                retry_key = _stage1_selection_key(
                    retry_bundle.get("assessment") or {},
                    retry_bundle.get("fidelity_gate"),
                )
                initial_key = _stage1_selection_key(base_assessment, stage1_gate)
                use_retry = retry_key > initial_key
                if use_retry and retry_selected is not None:
                    selected_base_result = retry_selected
                    selected_stage1_index = int(retry_bundle.get("index", selected_stage1_index))
                    base_assessment_bundle = retry_bundle
                    base_assessment = retry_bundle.get("assessment") or {}
                    stage1_gate = retry_bundle.get("fidelity_gate")
                    reason_codes.add("stage1_fidelity_retry")
                stage1_candidates.extend(retry_candidates)
                stage1_recovery = {
                    "applied": use_retry,
                    "selected": "retry" if use_retry else "initial",
                    "trigger_verdict": initial_stage1_gate.get("verdict") if isinstance(initial_stage1_gate, dict) else None,
                    "prompt_patch": stage1_repair_patch,
                    "retry_prompt": stage1_retry_prompt,
                    "retry_selected_index": int(retry_bundle.get("index", 0) or 0),
                    "retry_assessment": retry_bundle.get("assessment") if retry_bundle else None,
                    "retry_fidelity_gate": retry_bundle.get("fidelity_gate") if retry_bundle else None,
                }
        except Exception as retry_exc:
            stage1_recovery = {
                "applied": False,
                "selected": "initial",
                "trigger_verdict": initial_stage1_gate.get("verdict") if isinstance(initial_stage1_gate, dict) else None,
                "prompt_patch": stage1_repair_patch,
                "retry_prompt": stage1_retry_prompt,
                "error": str(retry_exc),
            }

    if stage1_gate and stage1_gate.get("available"):
        reason_codes.update(str(code) for code in (stage1_gate.get("issue_codes") or []))

    base_image_path = Path(selected_base_result["path"])
    base_image_bytes = base_image_path.read_bytes()

    # ── 3. Art direction + edit (stage 2 — liberdade criativa) ────────────────
    affinity_prompt = _build_affinity_prompt(prompt, preset, scene_preference)
    all_results: list[dict[str, Any]] = []
    failed_indices: list[int] = []
    last_art_direction: dict[str, Any] = {}
    last_primary_edit_prompt = ""
    last_applied_edit_prompt = ""
    stage2_thinking_level = "MINIMAL" if str(fidelity_mode).strip().lower() == "estrita" else "HIGH"
    any_repair_applied = bool(stage1_recovery.get("applied"))

    for img_idx in range(n_images):
        _emit(
            "creating_listing",
            {
                "message": f"Criando anuncio {img_idx + 1}/{n_images}...",
                "current": img_idx + 1,
                "total": n_images,
            },
        )

        seed = f"{session_id}:{img_idx}"
        art_direction = sample_art_direction(
            seed_hint=seed,
            user_prompt=affinity_prompt,
            request=effective_art_direction_request,
            commit=False,
        )
        last_art_direction = art_direction

        garment_material = _derive_garment_material_text(structural_contract, image_analysis)
        garment_color = "the garment colors and yarn tones"

        try:
            edit_prompt = build_art_direction_two_pass_edit_prompt(
                structural_contract=structural_contract,
                art_direction=art_direction,
                set_detection=set_detection,
                garment_material=garment_material,
                garment_color=garment_color,
                reference_guard_strength=reference_guard_strength,
                reference_usage_rules=reference_usage_rules,
                pose_flex_guideline=pose_flex_hint,
                user_prompt=prompt,
                image_analysis=image_analysis,
            )
            if str(fidelity_mode).strip().lower() == "estrita":
                edit_prompt += (
                    " Prioritize exact garment fidelity over scene creativity. "
                    "Do not alter garment silhouette, length, sleeve architecture, hem behavior, or stripe placement."
                )

            primary_edit_prompt = edit_prompt
            selected_edit_prompt = primary_edit_prompt
            edit_session_id = f"v2edit_{session_id}_{img_idx + 1}"
            edit_results = edit_image(
                source_image_bytes=base_image_bytes,
                edit_prompt=edit_prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                thinking_level=stage2_thinking_level,
                session_id=edit_session_id,
                reference_images_bytes=edit_reference_bytes,
                use_image_grounding=_use_image_grounding,
            )

            if not edit_results:
                failed_indices.append(img_idx + 1)
                continue

            result = edit_results[0]
            result["index"] = img_idx + 1
            result["art_direction_summary"] = art_direction.get("summary", {})
            final_assessment = assess_generated_image(str(result.get("path", "")), edit_prompt, classifier_summary)
            final_gate = (
                evaluate_visual_fidelity(
                    stage="stage2",
                    reference_images=judge_reference_bytes,
                    base_image_path=str(base_image_path),
                    candidate_image_path=str(result.get("path", "")),
                    structural_contract=structural_contract,
                    set_detection=set_detection,
                    prompt=edit_prompt,
                )
                if gate_policy.get("enabled") and judge_reference_bytes else None
            )

            targeted_reference_bytes = _merge_reference_bytes(
                edit_reference_bytes[: int(reference_budget.get("stage2_max_refs", 4) or 4)],
                judge_reference_bytes[: int(reference_budget.get("judge_max_refs", 4) or 4)],
                uploaded_bytes[:2],
            )[: int(reference_budget.get("judge_max_refs", 4) or 4)]
            localized_repair_enabled = _targeted_stage2_repair_enabled()
            localized_repair_plan = (
                classify_stage2_repair_strategy(final_gate)
                if localized_repair_enabled and final_gate
                else {
                    "mode": "none",
                    "issue_codes": list((final_gate or {}).get("issue_codes") or []),
                    "reason": "feature_disabled_or_gate_missing",
                }
            )
            recovery_info: dict[str, Any] = {
                "applied": False,
                "selected": "initial",
                "localized_repair": {
                    "enabled": localized_repair_enabled,
                    "eligible": localized_repair_plan.get("mode") == "targeted_repair",
                    "strategy": localized_repair_plan.get("mode"),
                    "reason": localized_repair_plan.get("reason"),
                    "issue_codes": localized_repair_plan.get("issue_codes", []),
                    "applied": False,
                },
                "full_retry": {
                    "eligible": False,
                    "applied": False,
                },
            }
            if localized_repair_plan.get("mode") == "targeted_repair" and final_gate and final_gate.get("available"):
                initial_localized_gate = dict(final_gate or {}) if isinstance(final_gate, dict) else final_gate
                localized_gate_input = dict(final_gate or {}) if isinstance(final_gate, dict) else {}
                localized_gate_input["issue_codes"] = list(localized_repair_plan.get("issue_codes", []))
                localized_prompt = build_targeted_repair_prompt(
                    gate_result=localized_gate_input,
                    structural_contract=structural_contract,
                    set_detection=set_detection,
                )
                localized_thinking_level = "MINIMAL"
                try:
                    localized_source_bytes = Path(str(result.get("path", ""))).read_bytes()
                    localized_results = edit_image(
                        source_image_bytes=localized_source_bytes,
                        edit_prompt=localized_prompt,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        thinking_level=localized_thinking_level,
                        session_id=f"{edit_session_id}_microrepair",
                        reference_images_bytes=targeted_reference_bytes,
                    )
                    localized_result = localized_results[0] if localized_results else None
                    localized_assessment = (
                        assess_generated_image(str(localized_result.get("path", "")), localized_prompt, classifier_summary)
                        if localized_result else None
                    )
                    localized_gate = (
                        evaluate_visual_fidelity(
                            stage="stage2",
                            reference_images=judge_reference_bytes,
                            base_image_path=str(base_image_path),
                            candidate_image_path=str(localized_result.get("path", "")),
                            structural_contract=structural_contract,
                            set_detection=set_detection,
                            prompt=localized_prompt,
                        )
                        if localized_result and gate_policy.get("enabled") and judge_reference_bytes else None
                    )
                    localized_key = _stage1_selection_key(localized_assessment or {}, localized_gate)
                    initial_key = _stage1_selection_key(final_assessment, final_gate)
                    use_localized = bool(localized_result and localized_key > initial_key)
                    if use_localized and localized_result is not None:
                        result = localized_result
                        result["index"] = img_idx + 1
                        result["art_direction_summary"] = art_direction.get("summary", {})
                        final_assessment = localized_assessment or final_assessment
                        final_gate = localized_gate or final_gate
                        selected_edit_prompt = localized_prompt
                        any_repair_applied = True
                        reason_codes.add("stage2_targeted_repair")
                        recovery_info["applied"] = True
                        recovery_info["selected"] = "localized_repair"
                    recovery_info["localized_repair"] = {
                        "enabled": localized_repair_enabled,
                        "eligible": True,
                        "strategy": localized_repair_plan.get("mode"),
                        "reason": localized_repair_plan.get("reason"),
                        "issue_codes": localized_repair_plan.get("issue_codes", []),
                        "applied": use_localized,
                        "trigger_verdict": initial_localized_gate.get("verdict") if isinstance(initial_localized_gate, dict) else None,
                        "repair_prompt": localized_prompt,
                        "thinking_level": localized_thinking_level,
                        "repair_assessment": localized_assessment,
                        "repair_fidelity_gate": localized_gate,
                    }
                except Exception as localized_exc:
                    recovery_info["localized_repair"] = {
                        "enabled": localized_repair_enabled,
                        "eligible": True,
                        "strategy": localized_repair_plan.get("mode"),
                        "reason": localized_repair_plan.get("reason"),
                        "issue_codes": localized_repair_plan.get("issue_codes", []),
                        "applied": False,
                        "trigger_verdict": initial_localized_gate.get("verdict") if isinstance(initial_localized_gate, dict) else None,
                        "repair_prompt": localized_prompt,
                        "thinking_level": localized_thinking_level,
                        "error": str(localized_exc),
                    }

            stage2_needs_retry = bool(
                gate_policy.get("stage2_retry_enabled")
                and final_gate
                and final_gate.get("available")
                and (
                    final_gate.get("verdict") == "hard_fail"
                    or (
                        str(fidelity_mode).strip().lower() == "estrita"
                        and final_gate.get("verdict") == "soft_fail"
                    )
                )
            )
            if stage2_needs_retry:
                initial_final_gate = dict(final_gate or {}) if isinstance(final_gate, dict) else final_gate
                recovery_info["full_retry"]["eligible"] = True
                retry_pose_mode = suggest_retry_pose_flex_mode(
                    current_pose_flex_mode=resolved_pose_flex_mode,
                    issue_codes=list(final_gate.get("issue_codes") or []),
                ) or resolved_pose_flex_mode
                retry_pose_guideline = _POSE_FLEX_HINTS.get(retry_pose_mode, pose_flex_hint)
                retry_patch = build_fidelity_repair_patch(
                    stage="stage2",
                    gate_result=final_gate,
                    structural_contract=structural_contract,
                    set_detection=set_detection,
                )
                retry_prompt = f"{edit_prompt} {retry_patch}".strip()
                if retry_pose_guideline and retry_pose_guideline != pose_flex_hint:
                    retry_prompt = f"{retry_prompt} Pose correction: {retry_pose_guideline}."
                retry_thinking_level = "MINIMAL" if final_gate.get("verdict") == "hard_fail" else stage2_thinking_level
                try:
                    retry_results = edit_image(
                        source_image_bytes=base_image_bytes,
                        edit_prompt=retry_prompt,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        thinking_level=retry_thinking_level,
                        session_id=f"{edit_session_id}_retry",
                        reference_images_bytes=edit_reference_bytes,
                        use_image_grounding=_use_image_grounding,
                    )
                    retry_result = retry_results[0] if retry_results else None
                    retry_assessment = (
                        assess_generated_image(str(retry_result.get("path", "")), retry_prompt, classifier_summary)
                        if retry_result else None
                    )
                    retry_gate = (
                        evaluate_visual_fidelity(
                            stage="stage2",
                            reference_images=judge_reference_bytes,
                            base_image_path=str(base_image_path),
                            candidate_image_path=str(retry_result.get("path", "")),
                            structural_contract=structural_contract,
                            set_detection=set_detection,
                            prompt=retry_prompt,
                        )
                        if retry_result and gate_policy.get("enabled") and judge_reference_bytes else None
                    )
                    retry_key = _stage1_selection_key(retry_assessment or {}, retry_gate)
                    initial_key = _stage1_selection_key(final_assessment, final_gate)
                    use_retry = bool(retry_result and retry_key > initial_key)
                    if use_retry and retry_result is not None:
                        result = retry_result
                        result["index"] = img_idx + 1
                        result["art_direction_summary"] = art_direction.get("summary", {})
                        final_assessment = retry_assessment or final_assessment
                        final_gate = retry_gate or final_gate
                        selected_edit_prompt = retry_prompt
                        any_repair_applied = True
                        reason_codes.add("stage2_fidelity_retry")
                    recovery_info["full_retry"] = {
                        "eligible": True,
                        "applied": use_retry,
                        "selected": "retry" if use_retry else "initial",
                        "trigger_verdict": initial_final_gate.get("verdict") if isinstance(initial_final_gate, dict) else None,
                        "prompt_patch": retry_patch,
                        "retry_prompt": retry_prompt,
                        "retry_pose_flex_mode": retry_pose_mode,
                        "retry_pose_flex_guideline": retry_pose_guideline,
                        "retry_thinking_level": retry_thinking_level,
                        "retry_assessment": retry_assessment,
                        "retry_fidelity_gate": retry_gate,
                    }
                    if use_retry:
                        recovery_info["applied"] = True
                        recovery_info["selected"] = "full_retry"
                except Exception as retry_exc:
                    recovery_info["full_retry"] = {
                        "eligible": True,
                        "applied": False,
                        "selected": "initial",
                        "trigger_verdict": initial_final_gate.get("verdict") if isinstance(initial_final_gate, dict) else None,
                        "prompt_patch": retry_patch,
                        "retry_prompt": retry_prompt,
                        "retry_pose_flex_mode": retry_pose_mode,
                        "retry_pose_flex_guideline": retry_pose_guideline,
                        "retry_thinking_level": retry_thinking_level,
                        "error": str(retry_exc),
                    }

            if final_gate and final_gate.get("available"):
                reason_codes.update(str(code) for code in (final_gate.get("issue_codes") or []))

            commit_art_direction_choice(art_direction)
            result["fidelity_gate"] = final_gate
            result["recovery_applied"] = bool(recovery_info.get("applied"))
            last_primary_edit_prompt = primary_edit_prompt
            last_applied_edit_prompt = selected_edit_prompt
            all_results.append(result)
            observability_runs.append(
                {
                    "index": img_idx + 1,
                    "art_direction_summary": art_direction.get("summary", {}),
                    "art_direction": art_direction,
                    "edit_prompt": primary_edit_prompt,
                    "applied_edit_prompt": selected_edit_prompt,
                    "edit_reference_names": edit_reference_names,
                    "result": {
                        "filename": result.get("filename"),
                        "url": result.get("url"),
                        "path": result.get("path"),
                    },
                    "assessment": final_assessment,
                    "fidelity_gate": final_gate,
                    "recovery": recovery_info,
                    "reference_guard": {
                        "strength": reference_guard_strength,
                        "rules": reference_usage_rules,
                        "risk_level": identity_risk,
                    },
                    "pose_flex": {
                        "mode": resolved_pose_flex_mode,
                        "guideline": pose_flex_hint,
                    },
                }
            )
        except Exception as stage2_exc:
            import traceback
            print(f"\n[DEBUG P2] Stage 2 Loop Exception (idx {img_idx}): {str(stage2_exc)}")
            traceback.print_exc()
            observability_runs.append(
                {
                    "index": img_idx + 1,
                    "art_direction_summary": art_direction.get("summary", {}),
                    "art_direction": art_direction,
                    "edit_prompt": last_primary_edit_prompt or "",
                    "applied_edit_prompt": last_applied_edit_prompt or "",
                    "error": str(stage2_exc),
                }
            )
            failed_indices.append(img_idx + 1)
            continue

    if not all_results:
        raise RuntimeError("Stage 2 falhou: nenhuma imagem final gerada")

    elapsed = round(time.time() - started, 2)
    from agent_runtime.normalize_user_intent import normalize_user_intent
    user_intent_payload = normalize_user_intent(prompt or "")

    # ── Build response ────────────────────────────────────────────────────────
    response: dict[str, Any] = {
        "session_id": session_id,
        "pipeline_version": "v2",
        "pipeline_mode": "reference_mode_strict" if str(fidelity_mode).strip().lower() == "estrita" else "reference_mode",
        "optimized_prompt": last_primary_edit_prompt or stage1_prompt,
        "stage1_prompt": stage1_prompt,
        "edit_prompt": last_applied_edit_prompt or last_primary_edit_prompt or stage1_prompt,
        "user_intent": user_intent_payload,
        "images": all_results,
        "failed_indices": failed_indices,
        "generation_time": elapsed,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "thinking_level": "MINIMAL",
        "stage2_thinking_level": stage2_thinking_level,
        "art_direction_summary": last_art_direction.get("summary", {}),
        "action_context": last_art_direction.get("action_context"),
        "structural_hint": structural_hint,
        "lighting_signature": lighting_signature,
        "selector_stats": selector_stats,
        "review_reference_urls": review_input_assets.get("original_references", []),
        "review_input_assets": review_input_assets,
        "pose_flex_mode": resolved_pose_flex_mode,
        "pose_flex_requested": requested_pose_flex_mode,
        "pose_flex_guideline": pose_flex_hint,
        "preset": preset,
        "scene_preference": scene_preference,
        "fidelity_mode": fidelity_mode,
        "base_image": selected_base_result,
        "repair_applied": any_repair_applied,
        "reason_codes": sorted(reason_codes),
        "fidelity_gate": {
            "enabled": bool(gate_policy.get("enabled")),
            "reasons": list(gate_policy.get("reasons", []) or []),
            "stage1": stage1_gate,
            "stage1_recovery": stage1_recovery,
        },
    }

    observability_meta = write_v2_observability_report(
        session_id,
        {
            "fidelity_gate": gate_policy,
            "request": {
                "prompt": prompt,
                "user_intent": user_intent_payload,
                "preset": preset,
                "scene_preference": scene_preference,
                "fidelity_mode": fidelity_mode,
                "n_images": n_images,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "uploaded_count": len(uploaded_bytes),
                "uploaded_filenames": filenames,
                "art_direction_request": art_direction_request,
                "effective_art_direction_request": effective_art_direction_request,
                "reference_guard_strength": reference_guard_strength,
                "reference_guard_rules": reference_usage_rules,
                "identity_reference_risk": identity_risk,
                "lighting_signature": lighting_signature,
                "pose_flex_mode": resolved_pose_flex_mode,
                "pose_flex_requested": requested_pose_flex_mode,
                "pose_flex_guideline": pose_flex_hint,
                "action_context": last_art_direction.get("action_context"),
            },
            "selector": {
                "stats": selector_stats,
                "selected_names": selected_names,
                "runtime_budget": reference_budget,
                "lighting_signature": lighting_signature,
                "runtime_reference_names": {
                    "stage1": base_gen_names,
                    "stage2": edit_reference_names,
                },
                "items": selector_result.get("items", []),
                "unified_triage": unified_triage,
            },
            "stage1": {
                "prompt": stage1_prompt,
                "strategy": {
                    "candidate_count": stage1_candidate_count,
                    "selected_index": selected_stage1_index,
                },
                "reference_names": list(base_gen_names),
                "candidates": stage1_candidates,
                "result": {
                    "filename": selected_base_result.get("filename"),
                    "url": selected_base_result.get("url"),
                    "path": selected_base_result.get("path"),
                },
                "assessment": base_assessment,
                "fidelity_gate": stage1_gate,
                "recovery": stage1_recovery,
            },
            "stage2": {
                "runs": observability_runs,
            },
            "response": {
                "failed_indices": failed_indices,
                "repair_applied": any_repair_applied,
                "reason_codes": sorted(reason_codes),
                "images": [
                    {
                        "filename": img.get("filename"),
                        "url": img.get("url"),
                        "path": img.get("path"),
                    }
                    for img in all_results
                ],
            },
        },
    )
    response.update(observability_meta)

    _emit("done", {"message": "Finalizado"})
    return response
