"""
Prompt Agent — Gemini Flash (texto).

Orquestrador principal: recebe inputs, monta contexto, chama Gemini, compila prompt.
Funções de inferência visual e diversidade vivem em agent_runtime/.

3 modos de operação:
  MODO 1: Usuário deu prompt → agente refina aplicando skills
  MODO 2: Usuário enviou imagens → agente descreve e cria prompt (Fidelity Lock)
  MODO 3: Sem prompt nem imagens → agente gera do zero via contexto do pool
"""
from typing import Any, Optional, List

from google.genai import types

from create_categories import DEFAULT_CREATE_CATEGORY, normalize_create_category
from agent_runtime.gemini_client import generate_with_system_instruction
from agent_runtime.grounding import _run_grounding_research
from agent_runtime.prompt_assets_registry import get_generate_prompt_assets
from agent_runtime.prompt_context import build_generate_context_text
from agent_runtime.prompt_result import finalize_prompt_agent_result
from agent_runtime.prompt_response import decode_prompt_agent_response
from agent_runtime.triage import (
    _infer_text_mode_shot,
    resolve_prompt_agent_visual_triage,
)
from agent_runtime.diversity import _sample_diversity_target
from agent_runtime.constants import AGENT_RESPONSE_SCHEMA
from agent_runtime.normalize_user_intent import normalize_user_intent

from guided_mode import guided_capture_to_shot, guided_summary


def run_agent(
    user_prompt: Optional[str],
    uploaded_images: Optional[List[bytes]],
    pool_context: str,
    aspect_ratio: str,
    resolution: str,
    category: str = DEFAULT_CREATE_CATEGORY,
    use_grounding: bool = False,
    grounding_mode: str = "lexical",
    grounding_context_hint: Optional[str] = None,
    diversity_target: Optional[dict] = None,
    guided_brief: Optional[dict] = None,
    structural_contract_hint: Optional[dict] = None,
    unified_vision_triage_result: Optional[dict] = None,
) -> dict:
    """
    Executa o Prompt Agent e retorna:
    {
        "prompt": str,
        "thinking_level": "MINIMAL" | "HIGH",
        "thinking_reason": str,
        "shot_type": "wide" | "medium" | "close-up" | "auto",
        "realism_level": 1 | 2 | 3,
    }
    """
    has_prompt = bool(user_prompt and user_prompt.strip())
    has_images = bool(uploaded_images)
    pipeline_mode = "reference_mode" if has_images else "text_mode"
    normalized_category = normalize_create_category(category)
    prompt_assets = get_generate_prompt_assets(normalized_category)
    guided_enabled = bool(guided_brief and guided_brief.get("enabled"))
    guided_set_mode = str((((guided_brief or {}).get("garment") or {}).get("set_mode") or "")).strip().lower()
    triage_result = resolve_prompt_agent_visual_triage(
        uploaded_images=uploaded_images or [],
        user_prompt=user_prompt,
        guided_enabled=guided_enabled,
        guided_set_mode=guided_set_mode,
        structural_contract_hint=structural_contract_hint,
        unified_vision_triage_result=unified_vision_triage_result,
    )
    structural_contract = triage_result["structural_contract"]
    guided_set_detection = triage_result["guided_set_detection"]
    garment_hint = str(triage_result["garment_hint"] or "")
    image_analysis = str(triage_result["image_analysis"] or "")
    look_contract = triage_result["look_contract"] or {}

    # Profile: SEMPRE gera dinamicamente via name blending (ignora _PROFILE_POOL estático
    # que produz AI Face com anatomia explícita). Scenario/pose: usa diversity_target
    # para preservar lógica anti-repeat do select_diversity_target.
    fallback_profile, fallback_scenario, fallback_pose = _sample_diversity_target()
    profile = (diversity_target or {}).get("profile_prompt", "") or fallback_profile
    if diversity_target:
        scenario = diversity_target.get("scenario_prompt", "") or fallback_scenario
        pose = diversity_target.get("pose_prompt", "") or fallback_pose
    else:
        scenario = fallback_scenario
        pose = fallback_pose

    # Grounding: chamada separada de pesquisa antes do agente
    grounding_research = ""
    grounding_meta = {
        "effective": False,
        "queries": [],
        "sources": [],
        "engine": "none",
        "source_engine": "none",
        "mode": "off",
        "grounded_images_count": 0,
        "visual_ref_engine": "none",
        "reason_codes": [],
    }
    grounded_images: List[bytes] = []
    grounding_pose_clause: str = ""
    if use_grounding:
        print("[AGENT] 🔍 Running grounding research (separate call)...")
        try:
            grounding_data = _run_grounding_research(
                uploaded_images=uploaded_images or [],
                user_prompt=user_prompt,
                mode=grounding_mode,
                garment_hint_override=garment_hint,
            )
            grounding_research = grounding_data.get("text", "")
            grounding_pose_clause = grounding_data.get("pose_clause", "")
            grounded_images = list(grounding_data.get("grounded_images", []) or [])
            grounding_meta = {
                "effective": bool(grounding_data.get("effective")),
                "queries": grounding_data.get("queries", []),
                "sources": grounding_data.get("sources", []),
                "engine": grounding_data.get("engine", "none"),
                "source_engine": grounding_data.get("source_engine", grounding_data.get("engine", "none")),
                "mode": grounding_mode,
                "grounded_images_count": int(grounding_data.get("grounded_images_count", 0) or 0),
                "visual_ref_engine": grounding_data.get("visual_ref_engine", "none"),
                "reason_codes": grounding_data.get("reason_codes", []),
            }
        except Exception as e:
            print(f"[AGENT] ⚠️  Grounding research failed: {e}")
            grounding_research = ""
            grounded_images = []

    context_text = build_generate_context_text(
        has_images=has_images,
        has_prompt=has_prompt,
        uploaded_images_count=len(uploaded_images or []),
        user_prompt=user_prompt,
        pool_context=pool_context,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        profile=profile,
        scenario=scenario,
        pose=pose,
        diversity_target=diversity_target,
        guided_enabled=guided_enabled,
        guided_brief=guided_brief,
        guided_set_mode=guided_set_mode,
        guided_set_detection=guided_set_detection,
        structural_contract=structural_contract,
        look_contract=look_contract,
        grounding_research=grounding_research,
        grounding_effective=bool(grounding_meta.get("effective")),
        grounding_context_hint=grounding_context_hint,
        grounding_mode=grounding_mode,
        reference_knowledge=prompt_assets.reference_knowledge,
    )

    def _build_parts(context: str) -> List[types.Part]:
        parts: List[types.Part] = []
        if has_images:
            for img_bytes in (uploaded_images or []):
                parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)
                    )
                )
        parts.append(types.Part(text=context))
        return parts

    def _call_prompt_model(context: str, temperature: float) -> Any:
        return generate_with_system_instruction(
            parts=_build_parts(context),
            system_instruction=prompt_assets.system_instruction,
            schema=AGENT_RESPONSE_SCHEMA,
            temperature=temperature,
            max_tokens=8192
        )

    response = _call_prompt_model(context_text, temperature=0.75)
    result = decode_prompt_agent_response(
        response=response,
        context_text=context_text,
        call_prompt_model=_call_prompt_model,
    )

    # Validações de segurança
    if result.get("thinking_level") not in ["MINIMAL", "HIGH"]:
        result["thinking_level"] = "MINIMAL"

    if result.get("shot_type") not in ["wide", "medium", "close-up", "auto"]:
        result["shot_type"] = "auto"

    guided_distance = str(((guided_brief or {}).get("capture") or {}).get("distance", "")).strip().lower()
    guided_pose_style = str(((guided_brief or {}).get("pose") or {}).get("style", "")).strip().lower()
    guided_pose_creative = guided_enabled and guided_pose_style == "criativa"
    guided_shot = guided_capture_to_shot(guided_distance) if guided_enabled else None
    # guided_shot só substitui o default quando há texto explícito ou pose criativa.
    if guided_shot and (has_prompt or guided_pose_creative):
        result["shot_type"] = guided_shot
    # Permite variabilidade baseada no contexto no lugar de lock "wide"
    elif pipeline_mode == "text_mode" and result.get("shot_type") == "auto":
        result["shot_type"] = _infer_text_mode_shot(user_prompt)

    if result.get("realism_level") not in [1, 2, 3]:
        result["realism_level"] = 2

    result = finalize_prompt_agent_result(
        result=result,
        has_images=has_images,
        has_prompt=has_prompt,
        user_prompt=user_prompt,
        structural_contract=structural_contract,
        guided_brief=guided_brief,
        guided_enabled=guided_enabled,
        guided_set_mode=guided_set_mode,
        guided_set_detection=guided_set_detection,
        grounding_mode=grounding_mode,
        pipeline_mode=pipeline_mode,
        aspect_ratio=aspect_ratio,
        pose=pose,
        grounding_pose_clause=grounding_pose_clause,
        profile=profile,
        scenario=scenario,
        diversity_target=diversity_target,
    )

    result["grounding"] = grounding_meta
    result["pipeline_mode"] = pipeline_mode
    result["category"] = normalized_category
    result["model_profile_id"] = diversity_target.get("profile_id") if diversity_target else None
    result["diversity_target"] = diversity_target or {}
    result["image_analysis"] = image_analysis
    result["guided_summary"] = guided_summary(
        guided_brief if guided_enabled else None,
        result.get("shot_type"),
        set_detection=guided_set_detection if guided_enabled and guided_set_mode == "conjunto" else None,
    )
    result["structural_contract"] = structural_contract
    result["_grounded_images"] = grounded_images

    # ── Log de observabilidade ─────────────────────────────────────
    prompt_text = result.get("prompt", "")
    print(f"\n{'='*60}")
    print(f"[AGENT] Mode: {'MODE 2 (images)' if has_images else 'MODE 1' if has_prompt else 'MODE 3'}")
    print(f"[AGENT] Category: {normalized_category}")
    print(f"[AGENT] Images sent: {len(uploaded_images) if uploaded_images else 0}")
    print(f"[AGENT] Pool context: {'Yes' if bool(pool_context.strip()) else 'No'}")
    print(f"[AGENT] Thinking: {result.get('thinking_level')} | Shot: {result.get('shot_type')} | Realism: {result.get('realism_level')}")
    if image_analysis:
        print(f"[AGENT] 🔍 Image Analysis: {image_analysis}")
    if guided_enabled and guided_set_mode == "conjunto":
        print(
            "[AGENT] 🧩 Set detection:"
            f" score={guided_set_detection.get('set_pattern_score')}"
            f" roles={guided_set_detection.get('detected_garment_roles')}"
            f" lock={guided_set_detection.get('set_lock_mode')}"
        )
    if has_images and structural_contract.get("enabled"):
        print(
            "[AGENT] 📐 Structural contract:"
            f" subtype={structural_contract.get('garment_subtype')}"
            f" sleeve={structural_contract.get('sleeve_type')}/{structural_contract.get('sleeve_length')}"
            f" hem={structural_contract.get('hem_shape')}"
            f" length={structural_contract.get('garment_length')}"
            f" conf={structural_contract.get('confidence')}"
        )
    print(f"[AGENT] Prompt ({len(prompt_text)} chars): {prompt_text[:300]}{'…' if len(prompt_text) > 300 else ''}")
    print(f"{'='*60}\n")

    result["user_intent"] = normalize_user_intent(str(user_prompt or "").strip())

    return result
