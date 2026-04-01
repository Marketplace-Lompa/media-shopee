"""
Generation Flow — túnel unificado de criação.

Suporta dois caminhos dentro da mesma espinha dorsal:

  A) Reference mode (com uploads):
    1. triagem unificada leve dos uploads
    2. generate_images() cria base fiel da peça (stage 1, locks fortes)
    3. edit_image() cria imagem final (stage 2, soul criativo + fidelidade)

  B) Text-only mode (sem uploads):
    1. Prompt Agent (run_agent) gera prompt criativo com Soul/Presets do Mode
    2. generate_images() executa direto sem referência

Este módulo NÃO contém lógica de negócio — delega para:
  - fidelity.py: prompts, guards, classificação
  - fidelity_gate.py: utilitários legados de gate/retry
  - reference_selector.py: dedup e triagem unificada leve
  - curation_policy.py: budgets, pose flex, guard config
  - generator.py: execução Nano Banana
  - agent.py (run_agent): síntese criativa text-only
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

from agent_runtime.curation_policy import (
    derive_art_direction_selection_policy,
    derive_reference_guard_config,
    stage1_candidate_count,
)
from agent_runtime.editing.contracts import ImageEditExecutionRequest
from agent_runtime.editing.executor import execute_image_edit_request
from agent_runtime.fidelity import (
    _build_mode_guardrail_clauses,
    build_classifier_summary,
    build_structural_hint,
    prepare_garment_replacement_prompt,
    should_use_image_grounding,
)
from agent_runtime.fidelity_gate import (
    build_fidelity_repair_patch,
    build_targeted_repair_prompt,
    classify_stage2_repair_strategy,
    evaluate_visual_fidelity,
    pick_best_stage1_candidate,
    stage1_selection_key,
)
from agent_runtime.creative_brief_builder import build_creative_brief_for_mode
from agent_runtime.mode_profile import get_mode_profile
from agent_runtime.modes import get_mode
from agent_runtime.generation_observability import (
    write_v2_observability_report,
)
from agent_runtime.reference_creative_planner import plan_reference_creative_flow
from agent_runtime.reference_selector import (
    merge_reference_bytes,
    select_reference_subsets,
)
from generator import generate_images
from history import add_entry as history_add, purge_oldest as history_purge
from models import GenerateResponse, GeneratedImage
from pipeline_effectiveness import assess_generated_image
from request_validation import validate_generation_params

# ── Constantes de validação ──────────────────────────────────────────────────
VALID_MODES = {"catalog_clean", "natural", "lifestyle", "editorial_commercial"}
VALID_SCENE_PREFS = {"auto_br", "indoor_br", "outdoor_br"}
DEFAULT_MODE = "natural"


def _coerce_reference_guard_config(
    raw_config: Any,
    *,
    mode_id: str,
    fidelity_mode: str,
) -> tuple[str, list[str], dict[str, Any]]:
    default_rules = [
        "References are visual evidence for garment fidelity only.",
        "Do not copy any human identity traits from references.",
    ]
    identity_guard: dict[str, Any] = {
        "mode_id": mode_id,
        "identity_scope": "replace_person",
        "reference_use": "garment_only",
        "transfer_allowed": False,
    }
    strength = "standard"
    rules: list[str] = list(default_rules)
    supplied_guard: Any = None

    if isinstance(raw_config, tuple):
        if len(raw_config) >= 3:
            strength, rules, supplied_guard = raw_config[:3]
        elif len(raw_config) == 2:
            strength, rules = raw_config
    elif isinstance(raw_config, dict):
        strength = raw_config.get("strength", strength)
        rules = list(raw_config.get("rules") or rules)
        supplied_guard = raw_config.get("identity_guard")
    elif raw_config is not None:
        supplied_guard = raw_config

    strength = str(strength or "standard").strip().lower()
    cleaned_rules = [str(item).strip() for item in (rules or []) if str(item).strip()]
    rules = cleaned_rules or list(default_rules)

    if isinstance(supplied_guard, dict):
        identity_guard.update(supplied_guard)
    if str(fidelity_mode).strip().lower() == "estrita":
        identity_guard.setdefault("strict", True)
    else:
        identity_guard.setdefault("strict", False)
    return strength, rules, identity_guard



def normalize_generation_options(
    *,
    mode: Optional[str] = None,
    scene_preference: str = "auto_br",
    fidelity_mode: str = "balanceada",
) -> tuple[str, str, str]:
    """Normaliza opções de geração. Mode é a fonte da verdade."""
    resolved_mode = mode if mode in VALID_MODES else DEFAULT_MODE
    return (
        resolved_mode,
        scene_preference if scene_preference in VALID_SCENE_PREFS else "auto_br",
        fidelity_mode or "balanceada",
    )


# ── Persistência de histórico ────────────────────────────────────────────────

def persist_generation_history(
    raw: dict[str, Any],
    *,
    aspect_ratio: str,
    resolution: str,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    scene_preference: Optional[str] = None,
    fidelity_mode: Optional[str] = None,

    pipeline_mode: Optional[str] = None,
    marketplace_channel: Optional[str] = None,
    marketplace_operation: Optional[str] = None,
    slot_id: Optional[str] = None,
) -> None:
    session_id = str(raw.get("session_id", "") or "")
    if not session_id:
        return

    resolved_preset = preset or raw.get("preset")
    resolved_scene_preference = scene_preference or raw.get("scene_preference")
    resolved_fidelity_mode = fidelity_mode or raw.get("fidelity_mode")

    resolved_marketplace_channel = marketplace_channel or raw.get("marketplace_channel")
    resolved_marketplace_operation = marketplace_operation or raw.get("marketplace_operation")
    resolved_slot_id = slot_id or raw.get("slot_id")
    art_direction_summary = raw.get("art_direction_summary") or {}
    camera_profile = art_direction_summary.get("camera_profile") if isinstance(art_direction_summary, dict) else None
    reference_urls = list(raw.get("review_reference_urls", []) or [])
    optimized_prompt = raw.get("optimized_prompt") or None
    resolved_pipeline_mode = pipeline_mode or raw.get("pipeline_mode") or None

    for img in raw.get("images", []) or []:
        try:
            history_add(
                session_id=session_id,
                filename=img["filename"],
                url=img["url"],
                prompt=optimized_prompt or "",
                thinking_level="MINIMAL",
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                references=reference_urls,
                base_prompt=raw.get("stage1_prompt"),
                camera_profile=camera_profile,
                mode=mode,
                preset=resolved_preset,
                scene_preference=resolved_scene_preference,
                fidelity_mode=resolved_fidelity_mode,

                pipeline_mode=resolved_pipeline_mode,
                optimized_prompt=optimized_prompt,
                marketplace_channel=resolved_marketplace_channel,
                marketplace_operation=resolved_marketplace_operation,
                slot_id=resolved_slot_id,
            )
        except Exception as hist_err:
            print(f"[HISTORY] generation persist error: {hist_err}")
    try:
        history_purge()
    except Exception:
        pass


# ── Build response ───────────────────────────────────────────────────────────

def build_generation_response_payload(
    raw: dict[str, Any],
    *,
    aspect_ratio: str,
    resolution: str,
    preset: str,
    scene_preference: str,
    fidelity_mode: str,

) -> dict[str, Any]:
    return {
        "session_id": raw.get("session_id"),
        "optimized_prompt": raw.get("optimized_prompt", ""),
        "pipeline_mode": raw.get("pipeline_mode", "reference_mode_strict"),
        "pipeline_version": "v2",
        "thinking_level": "MINIMAL",
        "thinking_reason": "pipeline_v2",
        "user_intent": raw.get("user_intent"),
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "images": raw.get("images", []),
        "failed_indices": raw.get("failed_indices"),
        "pool_refs_used": 0,
        "art_direction_summary": raw.get("art_direction_summary"),
        "lighting_signature": raw.get("lighting_signature"),
        "action_context": raw.get("action_context"),
        "preset": preset,
        "scene_preference": scene_preference,
        "fidelity_mode": fidelity_mode,

        "generation_time": raw.get("generation_time"),
        "reference_pack_stats": raw.get("selector_stats"),
        "repair_applied": raw.get("repair_applied"),
        "reason_codes": raw.get("reason_codes"),
        "debug_report_url": raw.get("report_url"),
        "debug_report_path": raw.get("report_path"),
    }


def build_generation_response(
    raw: dict[str, Any],
    *,
    aspect_ratio: str,
    resolution: str,
    preset: str,
    scene_preference: str,
    fidelity_mode: str,

) -> GenerateResponse:
    payload = build_generation_response_payload(
        raw,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,

    )
    return GenerateResponse(
        session_id=payload.get("session_id"),
        optimized_prompt=payload.get("optimized_prompt", ""),
        pipeline_mode=payload.get("pipeline_mode", "reference_mode_strict"),
        thinking_level="MINIMAL",
        thinking_reason="pipeline_v2",
        user_intent=payload.get("user_intent"),
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        images=[GeneratedImage(**img) for img in raw.get("images", [])],
        failed_indices=payload.get("failed_indices") or None,
        pipeline_version="v2",
        art_direction_summary=payload.get("art_direction_summary"),
        lighting_signature=payload.get("lighting_signature"),
        action_context=payload.get("action_context"),
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,

        generation_time=payload.get("generation_time"),
        reference_pack_stats=payload.get("reference_pack_stats"),
        repair_applied=payload.get("repair_applied"),
        reason_codes=payload.get("reason_codes"),
        debug_report_url=payload.get("debug_report_url"),
        debug_report_path=payload.get("debug_report_path"),
    )


def _targeted_stage2_repair_enabled() -> bool:
    return os.getenv("ENABLE_TARGETED_STAGE2_REPAIR", "true").strip().lower() != "false"


# ── Text-only flow (sem referências) ─────────────────────────────────────

def _run_text_only_flow(
    *,
    prompt: Optional[str],
    mode: str,
    n_images: int,
    aspect_ratio: str,
    resolution: str,
    session_id: str,
    started: float,
    on_stage: Optional[Callable[[str, dict[str, Any]], None]] = None,
) -> dict[str, Any]:
    """Caminho text-only dentro do túnel unificado.

    1. Prompt Agent (run_agent) sintetiza o prompt criativo usando
       Soul + Presets do Mode selecionado.
    2. generate_images() executa direto no Nano Banana sem referência.
    """
    def _emit(stage: str, data: Optional[dict[str, Any]] = None) -> None:
        if on_stage:
            on_stage(stage, data or {})

    _emit("text_only_start", {"message": "Modo text-only: sintetizando prompt criativo..."})

    from agent import run_agent

    _mode_config = get_mode(mode)
    creative_brief = build_creative_brief_for_mode(_mode_config, user_prompt=prompt)

    agent_result = run_agent(
        user_prompt=prompt or "",
        uploaded_images=None,
        pool_context="",
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        category="moda_feminina",
        diversity_target=creative_brief,
        mode=_mode_config.id,
    )
    optimized_prompt = agent_result.get("prompt") or prompt or ""

    _emit("generating_images", {"message": f"Gerando {n_images} imagem(ns)..."})

    all_results: list[dict[str, Any]] = []
    failed_indices: list[int] = []

    for img_idx in range(n_images):
        try:
            results = generate_images(
                prompt=optimized_prompt,
                thinking_level="HIGH",
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                n_images=1,
                uploaded_images=[],
                session_id=f"v2txt_{session_id}_{img_idx + 1}",
            )
            if results:
                result = results[0]
                result["index"] = img_idx + 1
                all_results.append(result)
            else:
                failed_indices.append(img_idx + 1)
        except Exception as gen_exc:
            import traceback
            print(f"\n[DEBUG GF] Text-only generation error (idx {img_idx}): {gen_exc}")
            traceback.print_exc()
            failed_indices.append(img_idx + 1)

    if not all_results:
        raise RuntimeError("Text-only flow falhou: nenhuma imagem gerada")

    elapsed = round(time.time() - started, 2)
    from agent_runtime.normalize_user_intent import normalize_user_intent
    user_intent_payload = normalize_user_intent(prompt or "")

    return {
        "session_id": session_id,
        "pipeline_version": "v2",
        "pipeline_mode": "text_mode",
        "optimized_prompt": optimized_prompt,
        "stage1_prompt": "",
        "edit_prompt": optimized_prompt,
        "user_intent": user_intent_payload,
        "images": all_results,
        "failed_indices": failed_indices,
        "generation_time": elapsed,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "thinking_level": "HIGH",
        "stage2_thinking_level": "",
        "art_direction_summary": {"mode": "text_only", "mode_id": mode},
        "action_context": None,
        "structural_hint": "",
        "lighting_signature": {},
        "selector_stats": {},
        "review_reference_urls": [],
        "review_input_assets": {},

        "mode": mode,
        "scene_preference": "auto_br",
        "fidelity_mode": "balanceada",
        "base_image": None,
        "repair_applied": False,
        "reason_codes": [],
        "fidelity_gate": {"enabled": False, "reasons": [], "stage1": None, "stage1_recovery": None},
    }


# ── Orquestrador principal ───────────────────────────────────────────────

def run_generation_flow(
    *,
    uploaded_bytes: list[bytes],
    uploaded_filenames: Optional[list[str]] = None,
    prompt: Optional[str] = None,
    mode: str = "natural",
    scene_preference: str = "auto_br",
    fidelity_mode: str = "balanceada",


    n_images: int = 1,
    aspect_ratio: str = "4:5",
    resolution: str = "1K",
    art_direction_request: Optional[dict[str, Any]] = None,
    on_stage: Optional[Callable[[str, dict[str, Any]], None]] = None,
) -> dict[str, Any]:
    """Túnel unificado de geração — reference mode ou text-only.

    Returns dict compatível com GenerateResponse.
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

    # ── Text-only: bypass Stages 1 e 2, usa Prompt Agent + generate direto ──
    if not uploaded_bytes:
        return _run_text_only_flow(
            prompt=prompt,
            mode=mode,
            n_images=n_images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            session_id=session_id,
            started=started,
            on_stage=on_stage,
        )

    _mode_config = get_mode(mode)
    _mode_profile = get_mode_profile(mode)

    # ── 1. Análise leve dos uploads (sem stage seller-facing de referências) ──
    _emit("stabilizing_garment", {"message": "Preparando modelo..."})

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

    # Extrair dados do triage unificado
    unified_triage = selector_result.get("unified_triage") or {}
    structural_contract = (unified_triage.get("structural_contract") or {}) if isinstance(unified_triage, dict) else {}
    set_detection = (unified_triage.get("set_detection") or {}) if isinstance(unified_triage, dict) else {}
    image_analysis = str((unified_triage.get("image_analysis") or "") if isinstance(unified_triage, dict) else "").strip()
    lighting_signature = (unified_triage.get("lighting_signature") or {}) if isinstance(unified_triage, dict) else {}
    garment_aesthetic = (unified_triage.get("garment_aesthetic") or {}) if isinstance(unified_triage, dict) else {}
    if structural_contract:
        structural_contract["enabled"] = True

    structural_hint = build_structural_hint(structural_contract)

    # Subsets de referências
    selected_bytes = selector_result.get("selected_bytes", {}) or {}
    selected_names = selector_result.get("selected_names", {}) or {}
    selector_stats = selector_result.get("stats", {}) or {}
    review_input_assets: dict[str, Any] = {}

    # Construir pacotes de referência por estágio
    base_generation_bytes = list(selected_bytes.get("base_generation", []) or [])
    strict_single_pass_bytes = list(selected_bytes.get("strict_single_pass", []) or [])
    edit_anchor_bytes = list(selected_bytes.get("edit_anchors", []) or [])
    identity_safe_bytes = list(selected_bytes.get("identity_safe", []) or [])
    base_generation_names = list(selected_names.get("base_generation", []) or [])
    strict_single_pass_names = list(selected_names.get("strict_single_pass", []) or [])
    edit_anchor_names = list(selected_names.get("edit_anchors", []) or [])
    identity_safe_names = list(selected_names.get("identity_safe", []) or [])

    reference_guard_strength, reference_usage_rules, identity_guard = _coerce_reference_guard_config(
        derive_reference_guard_config(
            selector_stats=selector_stats,
            fidelity_mode=fidelity_mode,
            mode=mode,
        ),
        mode_id=mode,
        fidelity_mode=fidelity_mode,
    )
    identity_risk = str((selector_stats or {}).get("identity_reference_risk", "low") or "low").strip().lower()

    # Mode guardrails — derivados do Soul (mode_profile + curation_policy)
    mode_guardrails = derive_art_direction_selection_policy(
        preset=mode,
        scene_preference=scene_preference,
        image_analysis_hint=image_analysis,
        structural_hint=structural_hint or "",
        lighting_signature=lighting_signature,
        user_prompt=prompt,
        fidelity_mode=fidelity_mode,
        selector_stats=selector_stats,
        structural_contract=structural_contract,
    )
    mode_guardrails.update(
        {
            "guardrail_profile": getattr(_mode_profile, "guardrail_profile", ""),
            "invention_budget": getattr(_mode_profile, "invention_budget", 0.0),
            "mode_hard_rules": list(getattr(_mode_profile, "hard_rules", ()) or ()),
            "reference_safe": True,
            "identity_guard": identity_guard,
        }
    )
    mode_guardrail_text = " ".join(_build_mode_guardrail_clauses(mode_guardrails))


    # O novo upload path gera a base sem referências visuais.
    base_gen_bytes: list[bytes] = []
    base_gen_names: list[str] = []
    edit_reference_bytes = list(identity_safe_bytes or edit_anchor_bytes)
    edit_reference_names = list(identity_safe_names or edit_anchor_names)

    reference_budget = {
        "stage1_max_refs": 0,
        "stage2_max_refs": len(edit_reference_bytes),
        "judge_max_refs": 0,
    }

    # Classificador
    classifier_summary = build_classifier_summary(structural_contract, selector_stats)
    
    # Gate policy está hardcoded para False no V2. O retry foi desativado.
    gate_policy = {
        "enabled": False,
        "reasons": [],
        "stage1_retry_enabled": False,
        "stage2_targeted_repair_enabled": False,
        "stage2_full_retry_enabled": False,
    }
    judge_reference_bytes: list[bytes] = []
    observability_runs: list[dict[str, Any]] = []
    reason_codes: set[str] = set()
    if gate_policy.get("enabled"):
        reason_codes.update(str(item) for item in (gate_policy.get("reasons") or []))

    # Image grounding
    _use_image_grounding = should_use_image_grounding(
        structural_contract=structural_contract,
        image_analysis=image_analysis,
        gate_policy=gate_policy,
        n_uploaded=len(uploaded_bytes),
    )

    # Art direction request
    effective_art_direction_request = dict(art_direction_request or {})
    effective_art_direction_request.setdefault("scene_preference", scene_preference)
    effective_art_direction_request.setdefault("mode", mode)
    effective_art_direction_request.setdefault("fidelity_mode", fidelity_mode)

    effective_art_direction_request.setdefault("selector_stats", selector_stats)
    effective_art_direction_request.setdefault("structural_contract", structural_contract)
    effective_art_direction_request.setdefault("set_detection", set_detection)
    if lighting_signature:
        effective_art_direction_request.setdefault("lighting_signature", lighting_signature)
    if image_analysis:
        effective_art_direction_request.setdefault("image_analysis_hint", image_analysis[:400])
    if structural_hint:
        effective_art_direction_request.setdefault("structural_hint", structural_hint)
    if garment_aesthetic:
        effective_art_direction_request.setdefault("garment_aesthetic", garment_aesthetic)
    effective_art_direction_request.setdefault("mode_guardrails", mode_guardrails)
    effective_art_direction_request.setdefault("mode_guardrail_text", mode_guardrail_text)
    directive_hints = effective_art_direction_request.get("directive_hints")
    if not isinstance(directive_hints, dict):
        directive_hints = {}
    directive_hints.setdefault("mode_guardrails", mode_guardrails)
    directive_hints.setdefault("mode_guardrail_text", mode_guardrail_text)
    directive_hints.setdefault(
        "reference_guard",
        {
            "strength": reference_guard_strength,
            "rules": reference_usage_rules,
            "identity_guard": identity_guard,
        },
    )
    directive_hints.setdefault("model_context_hint", "new identity, garment-first commercial direction")
    if identity_risk in {"medium", "high"}:
        directive_hints.setdefault(
            "custom_context_hint",
            "references are garment-only evidence; avoid identity transfer and pose cloning",
        )
    effective_art_direction_request["directive_hints"] = directive_hints
    reference_creative_plan = plan_reference_creative_flow(
        mode_id=_mode_config.id,
        user_prompt=prompt,
        scene_preference=scene_preference,
        garment_hint=str((unified_triage.get("garment_hint") or "") if isinstance(unified_triage, dict) else ""),
        image_analysis=image_analysis,
        structural_contract=structural_contract,
        set_detection=set_detection,
        garment_aesthetic=garment_aesthetic,
        lighting_signature=lighting_signature,
        mode_guardrail_text=mode_guardrail_text,
    )
    planner_payload = reference_creative_plan.to_dict()
    planner_summary = dict(reference_creative_plan.summary or {})

    # ── 2. Stage 1: base fiel da peça ─────────────────────────────────────
    _emit("stabilizing_garment", {"message": "Estabilizando a peça..."})
    stage1_prompt = str(reference_creative_plan.base_scene_prompt or "").strip()

    stage1_candidate_count_val = stage1_candidate_count(
        fidelity_mode=fidelity_mode, selector_stats=selector_stats,
    )

    base_results = generate_images(
        prompt=stage1_prompt, thinking_level="MINIMAL",
        aspect_ratio=aspect_ratio, resolution=resolution,
        n_images=stage1_candidate_count_val,
        uploaded_images=[],
        session_id=f"v2base_{session_id}",
        structural_hint=structural_hint,
        use_image_grounding=_use_image_grounding,
    )

    if not base_results:
        raise RuntimeError("Stage 1 falhou: nenhuma imagem base gerada")

    selected_base_result, stage1_candidates, selected_stage1_index = pick_best_stage1_candidate(
        base_results, stage1_prompt, classifier_summary,
        assess_fn=assess_generated_image,
        gate_policy=gate_policy,
        gate_reference_bytes=judge_reference_bytes,
        structural_contract=structural_contract,
        set_detection=set_detection,
    )
    base_assessment_bundle = stage1_candidates[selected_stage1_index - 1]
    base_assessment = base_assessment_bundle["assessment"]
    stage1_gate = base_assessment_bundle.get("fidelity_gate")
    stage1_recovery: dict[str, Any] = {"applied": False}

    # Stage 1 retry se gate falhou
    stage1_needs_retry = bool(
        gate_policy.get("stage1_retry_enabled")
        and stage1_gate and stage1_gate.get("available")
        and (
            stage1_gate.get("verdict") == "hard_fail"
            or (str(fidelity_mode).strip().lower() == "estrita" and stage1_gate.get("verdict") == "soft_fail")
        )
    )
    if stage1_needs_retry:
        stage1_recovery = _run_stage1_retry(
            stage1_prompt=stage1_prompt, stage1_gate=stage1_gate,
            structural_contract=structural_contract, set_detection=set_detection,
            stage1_candidate_count_val=stage1_candidate_count_val,
            aspect_ratio=aspect_ratio, resolution=resolution,
            base_gen_bytes=base_gen_bytes, structural_hint=structural_hint,
            session_id=session_id, classifier_summary=classifier_summary,
            gate_policy=gate_policy, judge_reference_bytes=judge_reference_bytes,
            fidelity_mode=fidelity_mode,
            # mutáveis
            selected_base_result=selected_base_result,
            base_assessment=base_assessment,
            stage1_candidates=stage1_candidates,
            selected_stage1_index=selected_stage1_index,
            reason_codes=reason_codes,
        )
        # Atualizar se retry foi melhor
        if stage1_recovery.get("applied"):
            selected_base_result = stage1_recovery["_result"]
            base_assessment = stage1_recovery["_assessment"]
            stage1_gate = stage1_recovery.get("_gate")
            selected_stage1_index = stage1_recovery["_index"]

    if stage1_gate and stage1_gate.get("available"):
        reason_codes.update(str(code) for code in (stage1_gate.get("issue_codes") or []))

    base_image_path = Path(selected_base_result["path"])
    base_image_bytes = base_image_path.read_bytes()

    # ── 3. Stage 2: garment replacement sobre a mesma base ────────────────
    all_results: list[dict[str, Any]] = []
    failed_indices: list[int] = []
    last_art_direction: dict[str, Any] = {
        "summary": planner_summary,
        "creative_plan": planner_payload,
        "action_context": None,
    }
    last_primary_edit_prompt = ""
    last_applied_edit_prompt = ""
    stage2_thinking_level = "MINIMAL" if str(fidelity_mode).strip().lower() == "estrita" else "HIGH"
    any_repair_applied = bool(stage1_recovery.get("applied"))
    prepared_replacement_prompt = prepare_garment_replacement_prompt(
        structural_contract=structural_contract,
        garment_hint=str((unified_triage.get("garment_hint") or "") if isinstance(unified_triage, dict) else ""),
        image_analysis=image_analysis,
        set_detection=set_detection,
        mode_id=_mode_config.id,
        source_prompt_context=stage1_prompt,
    )

    for img_idx in range(n_images):
        _emit("creating_listing", {"message": f"Criando anúncio {img_idx + 1}/{n_images}...", "current": img_idx + 1, "total": n_images})
        try:
            result_data = _run_stage2_iteration(
                img_idx=img_idx, session_id=session_id, mode=mode,
                structural_contract=structural_contract, set_detection=set_detection,
                image_analysis=image_analysis, fidelity_mode=fidelity_mode,
                reference_guard_strength=reference_guard_strength,
                reference_usage_rules=reference_usage_rules,
                art_direction_summary=planner_summary,
                source_prompt_context=stage1_prompt,
                base_image_bytes=base_image_bytes, base_image_path=base_image_path,
                aspect_ratio=aspect_ratio, resolution=resolution,
                stage2_thinking_level=stage2_thinking_level,
                edit_reference_bytes=edit_reference_bytes,
                _use_image_grounding=_use_image_grounding,
                classifier_summary=classifier_summary,
                gate_policy=gate_policy, judge_reference_bytes=judge_reference_bytes,
                reference_budget=reference_budget,
                prepared_replacement_prompt=prepared_replacement_prompt,
                identity_risk=identity_risk,
                edit_reference_names=edit_reference_names,
                reason_codes=reason_codes,
            )
            if result_data is None:
                failed_indices.append(img_idx + 1)
                continue
            all_results.append(result_data["result"])
            last_art_direction = result_data["art_direction"]
            last_primary_edit_prompt = result_data["primary_edit_prompt"]
            last_applied_edit_prompt = result_data["applied_edit_prompt"]
            if result_data.get("repair_applied"):
                any_repair_applied = True
            observability_runs.append(result_data["observability"])
        except Exception as stage2_exc:
            import traceback
            print(f"\n[DEBUG GF] Stage 2 Loop Exception (idx {img_idx}): {str(stage2_exc)}")
            traceback.print_exc()
            observability_runs.append({
                "index": img_idx + 1,
                "art_direction_summary": last_art_direction.get("summary", {}),
                "art_direction": last_art_direction,
                "edit_prompt": last_primary_edit_prompt or "",
                "applied_edit_prompt": last_applied_edit_prompt or "",
                "error": str(stage2_exc),
            })
            failed_indices.append(img_idx + 1)

    if not all_results:
        raise RuntimeError("Stage 2 falhou: nenhuma imagem final gerada")

    # ── 4. Build response ─────────────────────────────────────────────────
    elapsed = round(time.time() - started, 2)
    from agent_runtime.normalize_user_intent import normalize_user_intent
    user_intent_payload = normalize_user_intent(prompt or "")

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

        "mode": mode,
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

    observability_meta = write_v2_observability_report(session_id, {
        "fidelity_gate": gate_policy,
            "request": {
            "prompt": prompt, "user_intent": user_intent_payload,
            "mode": mode, "scene_preference": scene_preference,
            "fidelity_mode": fidelity_mode, "n_images": n_images,
            "aspect_ratio": aspect_ratio, "resolution": resolution,
            "uploaded_count": len(uploaded_bytes), "uploaded_filenames": filenames,
            "art_direction_request": art_direction_request,
            "effective_art_direction_request": effective_art_direction_request,
            "reference_creative_plan": planner_payload,
            "reference_guard_strength": reference_guard_strength,
            "reference_guard_rules": reference_usage_rules,
            "identity_guard": identity_guard,
            "mode_guardrails": mode_guardrails,
            "identity_reference_risk": identity_risk,
            "lighting_signature": lighting_signature,

            "action_context": last_art_direction.get("action_context"),
        },
        "selector": {
            "stats": selector_stats, "selected_names": selected_names,
            "runtime_budget": reference_budget, "lighting_signature": lighting_signature,
            "runtime_reference_names": {"stage1": base_gen_names, "stage2": edit_reference_names},
            "items": selector_result.get("items", []),
            "unified_triage": unified_triage,
        },
        "stage1": {
            "prompt": stage1_prompt,
            "strategy": {"candidate_count": stage1_candidate_count_val, "selected_index": selected_stage1_index},
            "reference_names": list(base_gen_names),
            "candidates": stage1_candidates,
            "result": {"filename": selected_base_result.get("filename"), "url": selected_base_result.get("url"), "path": selected_base_result.get("path")},
            "assessment": base_assessment,
            "fidelity_gate": stage1_gate,
            "recovery": stage1_recovery,
        },
        "stage2": {"runs": observability_runs},
        "response": {
            "failed_indices": failed_indices, "repair_applied": any_repair_applied,
            "reason_codes": sorted(reason_codes),
            "images": [{"filename": img.get("filename"), "url": img.get("url"), "path": img.get("path")} for img in all_results],
        },
    })
    response.update(observability_meta)

    _emit("done", {"message": "Finalizado"})
    return response


# ── Sub-rotinas extraídas do fluxo principal ─────────────────────────────

def _run_stage1_retry(
    *,
    stage1_prompt: str,
    stage1_gate: dict[str, Any],
    structural_contract: dict[str, Any],
    set_detection: dict[str, Any],
    stage1_candidate_count_val: int,
    aspect_ratio: str,
    resolution: str,
    base_gen_bytes: list[bytes],
    structural_hint: Optional[str],
    session_id: str,
    classifier_summary: dict[str, Any],
    gate_policy: dict[str, Any],
    judge_reference_bytes: list[bytes],
    fidelity_mode: str,
    selected_base_result: dict[str, Any],
    base_assessment: dict[str, Any],
    stage1_candidates: list[dict[str, Any]],
    selected_stage1_index: int,
    reason_codes: set[str],
) -> dict[str, Any]:
    """Tenta retry do stage 1 quando o gate detecta falha."""
    initial_stage1_gate = dict(stage1_gate) if isinstance(stage1_gate, dict) else stage1_gate
    stage1_repair_patch = build_fidelity_repair_patch(
        stage="stage1", gate_result=stage1_gate,
        structural_contract=structural_contract, set_detection=set_detection,
    )
    stage1_retry_prompt = f"{stage1_prompt} {stage1_repair_patch}".strip()
    recovery: dict[str, Any] = {"applied": False}
    try:
        retry_results = generate_images(
            prompt=stage1_retry_prompt, thinking_level="MINIMAL",
            aspect_ratio=aspect_ratio, resolution=resolution,
            n_images=stage1_candidate_count_val,
            uploaded_images=base_gen_bytes,
            session_id=f"v2base_retry_{session_id}",
            structural_hint=structural_hint,
        )
        if retry_results:
            retry_selected, retry_candidates, retry_selected_index = pick_best_stage1_candidate(
                retry_results, stage1_retry_prompt, classifier_summary,
                assess_fn=assess_generated_image,
                gate_policy=gate_policy, gate_reference_bytes=judge_reference_bytes,
                structural_contract=structural_contract, set_detection=set_detection,
            )
            offset = len(stage1_candidates)
            for row in retry_candidates:
                row["attempt"] = "retry"
                row["index"] = offset + int(row.get("index", 0) or 0)
            retry_bundle = retry_candidates[retry_selected_index - 1]
            retry_key = stage1_selection_key(retry_bundle.get("assessment") or {}, retry_bundle.get("fidelity_gate"))
            initial_key = stage1_selection_key(base_assessment, stage1_gate)
            use_retry = retry_key > initial_key
            if use_retry and retry_selected is not None:
                reason_codes.add("stage1_fidelity_retry")
                recovery = {
                    "applied": True,
                    "_result": retry_selected,
                    "_assessment": retry_bundle.get("assessment") or {},
                    "_gate": retry_bundle.get("fidelity_gate"),
                    "_index": int(retry_bundle.get("index", selected_stage1_index)),
                    "selected": "retry",
                    "trigger_verdict": initial_stage1_gate.get("verdict") if isinstance(initial_stage1_gate, dict) else None,
                    "prompt_patch": stage1_repair_patch,
                    "retry_prompt": stage1_retry_prompt,
                }
            else:
                recovery = {
                    "applied": False,
                    "selected": "initial",
                    "trigger_verdict": initial_stage1_gate.get("verdict") if isinstance(initial_stage1_gate, dict) else None,
                    "prompt_patch": stage1_repair_patch,
                    "retry_prompt": stage1_retry_prompt,
                }
            stage1_candidates.extend(retry_candidates)
    except Exception as retry_exc:
        recovery = {
            "applied": False, "selected": "initial",
            "trigger_verdict": initial_stage1_gate.get("verdict") if isinstance(initial_stage1_gate, dict) else None,
            "prompt_patch": stage1_repair_patch, "retry_prompt": stage1_retry_prompt,
            "error": str(retry_exc),
        }
    return recovery


def _run_stage2_iteration(
    *,
    img_idx: int,
    session_id: str,
    mode: str,
    structural_contract: dict[str, Any],
    set_detection: dict[str, Any],
    image_analysis: str,
    fidelity_mode: str,
    reference_guard_strength: str,
    reference_usage_rules: list[str],
    art_direction_summary: dict[str, str],
    source_prompt_context: str,
    base_image_bytes: bytes,
    base_image_path: Path,
    aspect_ratio: str,
    resolution: str,
    stage2_thinking_level: str,
    edit_reference_bytes: list[bytes],
    _use_image_grounding: bool,
    classifier_summary: dict[str, Any],
    gate_policy: dict[str, Any],
    judge_reference_bytes: list[bytes],
    reference_budget: dict[str, int],
    prepared_replacement_prompt: Any,
    identity_risk: str,
    edit_reference_names: list[str],
    reason_codes: set[str],
) -> Optional[dict[str, Any]]:
    """Executa uma iteração do stage 2 (edit criativo + recovery).

    Retorna dict com result, art_direction, prompts, observability, ou None se falhou.
    """
    art_direction: dict[str, Any] = {
        "summary": dict(art_direction_summary or {}),
        "action_context": None,
    }
    primary_edit_prompt = str(prepared_replacement_prompt.display_prompt or "").strip()
    selected_edit_prompt = primary_edit_prompt
    edit_session_id = f"v2edit_{session_id}_{img_idx + 1}"
    edit_results = execute_image_edit_request(
        ImageEditExecutionRequest(
            source_image_bytes=base_image_bytes,
            prepared_prompt=prepared_replacement_prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            session_id=edit_session_id,
            source_prompt_context=source_prompt_context,
            reference_images_bytes=edit_reference_bytes,
            thinking_level=stage2_thinking_level,
            use_image_grounding=_use_image_grounding,
            lock_person=True,
        )
    )

    if not edit_results:
        return None

    result = edit_results[0]
    result["index"] = img_idx + 1
    result["art_direction_summary"] = art_direction.get("summary", {})

    final_assessment = assess_generated_image(str(result.get("path", "")), primary_edit_prompt, classifier_summary)
    final_gate = (
        evaluate_visual_fidelity(
            stage="stage2", reference_images=judge_reference_bytes,
            base_image_path=str(base_image_path),
            candidate_image_path=str(result.get("path", "")),
            structural_contract=structural_contract, set_detection=set_detection,
            prompt=primary_edit_prompt,
        )
        if gate_policy.get("enabled") and judge_reference_bytes else None
    )

    # Recovery: targeted repair + full retry
    recovery_info = _run_stage2_recovery(
        result=result, final_assessment=final_assessment, final_gate=final_gate,
        gate_policy=gate_policy, structural_contract=structural_contract,
        set_detection=set_detection, prepared_replacement_prompt=prepared_replacement_prompt,
        base_image_bytes=base_image_bytes, base_image_path=base_image_path,
        aspect_ratio=aspect_ratio, resolution=resolution,
        stage2_thinking_level=stage2_thinking_level,
        edit_reference_bytes=edit_reference_bytes,
        judge_reference_bytes=judge_reference_bytes,
        reference_budget=reference_budget,
        edit_session_id=edit_session_id,
        classifier_summary=classifier_summary,
        _use_image_grounding=_use_image_grounding,
        source_prompt_context=source_prompt_context,

        fidelity_mode=fidelity_mode,
        reason_codes=reason_codes,
        img_idx=img_idx,
        art_direction=art_direction,
    )

    # Aplicar resultado do recovery
    if recovery_info.get("_updated_result"):
        result = recovery_info["_updated_result"]
        result["index"] = img_idx + 1
        result["art_direction_summary"] = art_direction.get("summary", {})
        final_assessment = recovery_info.get("_updated_assessment", final_assessment)
        final_gate = recovery_info.get("_updated_gate", final_gate)
        selected_edit_prompt = recovery_info.get("_updated_prompt", selected_edit_prompt)

    if final_gate and final_gate.get("available"):
        reason_codes.update(str(code) for code in (final_gate.get("issue_codes") or []))

    result["fidelity_gate"] = final_gate
    result["recovery_applied"] = bool(recovery_info.get("applied"))

    return {
        "result": result,
        "art_direction": art_direction,
        "primary_edit_prompt": primary_edit_prompt,
        "applied_edit_prompt": selected_edit_prompt,
        "repair_applied": recovery_info.get("applied", False),
        "observability": {
            "index": img_idx + 1,
            "art_direction_summary": art_direction.get("summary", {}),
            "art_direction": art_direction,
            "edit_prompt": primary_edit_prompt,
            "applied_edit_prompt": selected_edit_prompt,
            "edit_reference_names": edit_reference_names,
            "result": {"filename": result.get("filename"), "url": result.get("url"), "path": result.get("path")},
            "assessment": final_assessment,
            "fidelity_gate": final_gate,
            "recovery": recovery_info,
            "reference_guard": {"strength": reference_guard_strength, "rules": reference_usage_rules, "risk_level": identity_risk},

        },
    }


def _run_stage2_recovery(
    *,
    result: dict[str, Any],
    final_assessment: dict[str, Any],
    final_gate: Optional[dict[str, Any]],
    gate_policy: dict[str, Any],
    structural_contract: dict[str, Any],
    set_detection: dict[str, Any],
    prepared_replacement_prompt: Any,
    base_image_bytes: bytes,
    base_image_path: Path,
    aspect_ratio: str,
    resolution: str,
    stage2_thinking_level: str,
    edit_reference_bytes: list[bytes],
    judge_reference_bytes: list[bytes],
    reference_budget: dict[str, int],
    edit_session_id: str,
    classifier_summary: dict[str, Any],
    _use_image_grounding: bool,
    source_prompt_context: str,

    fidelity_mode: str,
    reason_codes: set[str],
    img_idx: int,
    art_direction: dict[str, Any],
) -> dict[str, Any]:
    """Executa lógica de recovery do stage 2: targeted repair + full retry."""
    edit_prompt = str(prepared_replacement_prompt.display_prompt or "").strip()
    stage2_ref_limit = int(reference_budget.get("stage2_max_refs", 4) or 4)
    judge_ref_limit = int(reference_budget.get("judge_max_refs", 0) or 0)
    targeted_reference_bytes = merge_reference_bytes(
        edit_reference_bytes[:stage2_ref_limit],
        judge_reference_bytes[:judge_ref_limit],
    )
    if stage2_ref_limit > 0:
        targeted_reference_bytes = targeted_reference_bytes[:stage2_ref_limit]

    localized_repair_enabled = _targeted_stage2_repair_enabled()
    localized_repair_plan = (
        classify_stage2_repair_strategy(final_gate)
        if localized_repair_enabled and final_gate
        else {"mode": "none", "issue_codes": list((final_gate or {}).get("issue_codes") or []), "reason": "feature_disabled_or_gate_missing"}
    )

    recovery_info: dict[str, Any] = {
        "applied": False, "selected": "initial",
        "localized_repair": {
            "enabled": localized_repair_enabled,
            "eligible": localized_repair_plan.get("mode") == "targeted_repair",
            "strategy": localized_repair_plan.get("mode"),
            "reason": localized_repair_plan.get("reason"),
            "issue_codes": localized_repair_plan.get("issue_codes", []),
            "applied": False,
        },
        "full_retry": {"eligible": False, "applied": False},
    }

    # Targeted micro-repair
    if localized_repair_plan.get("mode") == "targeted_repair" and final_gate and final_gate.get("available"):
        initial_localized_gate = dict(final_gate) if isinstance(final_gate, dict) else final_gate
        localized_gate_input = dict(final_gate) if isinstance(final_gate, dict) else {}
        localized_gate_input["issue_codes"] = list(localized_repair_plan.get("issue_codes", []))
        localized_prompt = build_targeted_repair_prompt(
            gate_result=localized_gate_input,
            structural_contract=structural_contract,
            set_detection=set_detection,
        )
        try:
            localized_source_bytes = Path(str(result.get("path", ""))).read_bytes()
            localized_prepared_prompt = prepared_replacement_prompt.__class__(
                **{
                    **prepared_replacement_prompt.__dict__,
                    "display_prompt": localized_prompt,
                    "model_prompt": localized_prompt,
                    "structured_edit_goal": localized_prompt,
                }
            )
            localized_results = execute_image_edit_request(
                ImageEditExecutionRequest(
                    source_image_bytes=localized_source_bytes,
                    prepared_prompt=localized_prepared_prompt,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    session_id=f"{edit_session_id}_microrepair",
                    source_prompt_context=source_prompt_context,
                    reference_images_bytes=targeted_reference_bytes,
                    thinking_level="MINIMAL",
                    use_image_grounding=_use_image_grounding,
                    lock_person=True,
                )
            )
            localized_result = localized_results[0] if localized_results else None
            localized_assessment = assess_generated_image(str(localized_result.get("path", "")), localized_prompt, classifier_summary) if localized_result else None
            localized_gate = (
                evaluate_visual_fidelity(
                    stage="stage2", reference_images=judge_reference_bytes,
                    base_image_path=str(base_image_path),
                    candidate_image_path=str(localized_result.get("path", "")),
                    structural_contract=structural_contract, set_detection=set_detection,
                    prompt=localized_prompt,
                )
                if localized_result and gate_policy.get("enabled") and judge_reference_bytes else None
            )
            localized_key = stage1_selection_key(localized_assessment or {}, localized_gate)
            initial_key = stage1_selection_key(final_assessment, final_gate)
            use_localized = bool(localized_result and localized_key > initial_key)
            if use_localized and localized_result is not None:
                reason_codes.add("stage2_targeted_repair")
                recovery_info["applied"] = True
                recovery_info["selected"] = "localized_repair"
                recovery_info["_updated_result"] = localized_result
                recovery_info["_updated_assessment"] = localized_assessment
                recovery_info["_updated_gate"] = localized_gate
                recovery_info["_updated_prompt"] = localized_prompt
            recovery_info["localized_repair"] = {
                "enabled": True, "eligible": True,
                "strategy": localized_repair_plan.get("mode"),
                "reason": localized_repair_plan.get("reason"),
                "issue_codes": localized_repair_plan.get("issue_codes", []),
                "applied": use_localized,
                "trigger_verdict": initial_localized_gate.get("verdict") if isinstance(initial_localized_gate, dict) else None,
                "repair_prompt": localized_prompt,
                "thinking_level": "MINIMAL",
                "repair_assessment": localized_assessment,
                "repair_fidelity_gate": localized_gate,
            }
        except Exception as localized_exc:
            recovery_info["localized_repair"] = {
                "enabled": True, "eligible": True,
                "strategy": localized_repair_plan.get("mode"),
                "reason": localized_repair_plan.get("reason"),
                "issue_codes": localized_repair_plan.get("issue_codes", []),
                "applied": False,
                "repair_prompt": localized_prompt,
                "thinking_level": "MINIMAL",
                "error": str(localized_exc),
            }

    # Se o repair localizado não resolveu, tenta full retry
    _current_assessment = recovery_info.get("_updated_assessment", final_assessment)
    _current_gate = recovery_info.get("_updated_gate", final_gate)
    stage2_needs_retry = bool(
        gate_policy.get("stage2_retry_enabled")
        and _current_gate and _current_gate.get("available")
        and (
            _current_gate.get("verdict") == "hard_fail"
            or (str(fidelity_mode).strip().lower() == "estrita" and _current_gate.get("verdict") == "soft_fail")
        )
    )
    if stage2_needs_retry:
        initial_final_gate = dict(_current_gate) if isinstance(_current_gate, dict) else _current_gate
        recovery_info["full_retry"]["eligible"] = True

        retry_patch = build_fidelity_repair_patch(
            stage="stage2", gate_result=_current_gate,
            structural_contract=structural_contract, set_detection=set_detection,
        )
        retry_prompt = f"{edit_prompt} {retry_patch}".strip()

        retry_thinking_level = "MINIMAL" if _current_gate.get("verdict") == "hard_fail" else stage2_thinking_level
        try:
            retry_prepared_prompt = prepared_replacement_prompt.__class__(
                **{
                    **prepared_replacement_prompt.__dict__,
                    "display_prompt": retry_prompt,
                    "model_prompt": retry_prompt,
                    "structured_edit_goal": retry_prompt,
                }
            )
            retry_results = execute_image_edit_request(
                ImageEditExecutionRequest(
                    source_image_bytes=base_image_bytes,
                    prepared_prompt=retry_prepared_prompt,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    session_id=f"{edit_session_id}_retry",
                    source_prompt_context=source_prompt_context,
                    reference_images_bytes=edit_reference_bytes,
                    thinking_level=retry_thinking_level,
                    use_image_grounding=_use_image_grounding,
                    lock_person=True,
                )
            )
            retry_result = retry_results[0] if retry_results else None
            retry_assessment = assess_generated_image(str(retry_result.get("path", "")), retry_prompt, classifier_summary) if retry_result else None
            retry_gate = (
                evaluate_visual_fidelity(
                    stage="stage2", reference_images=judge_reference_bytes,
                    base_image_path=str(base_image_path),
                    candidate_image_path=str(retry_result.get("path", "")),
                    structural_contract=structural_contract, set_detection=set_detection,
                    prompt=retry_prompt,
                )
                if retry_result and gate_policy.get("enabled") and judge_reference_bytes else None
            )
            retry_key = stage1_selection_key(retry_assessment or {}, retry_gate)
            initial_key = stage1_selection_key(_current_assessment, _current_gate)
            use_retry = bool(retry_result and retry_key > initial_key)
            if use_retry and retry_result is not None:
                reason_codes.add("stage2_fidelity_retry")
                recovery_info["applied"] = True
                recovery_info["selected"] = "full_retry"
                recovery_info["_updated_result"] = retry_result
                recovery_info["_updated_assessment"] = retry_assessment
                recovery_info["_updated_gate"] = retry_gate
                recovery_info["_updated_prompt"] = retry_prompt
            recovery_info["full_retry"] = {
                "eligible": True, "applied": use_retry,
                "selected": "retry" if use_retry else "initial",
                "trigger_verdict": initial_final_gate.get("verdict") if isinstance(initial_final_gate, dict) else None,
                "prompt_patch": retry_patch, "retry_prompt": retry_prompt,

                "retry_thinking_level": retry_thinking_level,
                "retry_assessment": retry_assessment,
                "retry_fidelity_gate": retry_gate,
            }
        except Exception as retry_exc:
            recovery_info["full_retry"] = {
                "eligible": True, "applied": False, "selected": "initial",
                "trigger_verdict": initial_final_gate.get("verdict") if isinstance(initial_final_gate, dict) else None,
                "prompt_patch": retry_patch, "retry_prompt": retry_prompt,

                "retry_thinking_level": retry_thinking_level,
                "error": str(retry_exc),
            }

    return recovery_info
