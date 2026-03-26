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

from agent_runtime.prompt_assets_registry import get_generate_prompt_assets
from agent_runtime.prompt_context import build_generate_context_text, build_system_instruction
from agent_runtime.prompt_result import finalize_prompt_agent_result
from agent_runtime.prompt_response import decode_prompt_agent_response
from agent_runtime.triage import (
    _infer_text_mode_shot,
    resolve_prompt_agent_visual_triage,
)
from agent_runtime.target_builder import (
    _sample_diversity_target,
    build_mode_diversity_target,
    harmonize_diversity_target_for_mode,
)
from agent_runtime.constants import AGENT_RESPONSE_SCHEMA, build_reference_knowledge
from agent_runtime.modes import (
    describe_mode_defaults,
    get_mode,
    preferred_shot_type_for_framing,
    preferred_shot_type_for_mode,
    resolve_mode_with_overrides,
)
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
    mode: Optional[str] = None,
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
    active_mode = get_mode(mode or "natural")  # Modes ativos em AMBOS os pipelines
    effective_mode = (
        resolve_mode_with_overrides(active_mode.id, (diversity_target or {}).get("preset_defaults"))
        if active_mode
        else None
    )
    guided_enabled = bool(guided_brief and guided_brief.get("enabled"))
    guided_set_mode = str((((guided_brief or {}).get("garment") or {}).get("set_mode") or "")).strip().lower()
    if has_images:
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
    else:
        structural_contract = {
            "enabled": False,
            "confidence": 0.0,
            "sleeve_type": "unknown",
            "sleeve_length": "unknown",
            "front_opening": "unknown",
            "hem_shape": "unknown",
            "garment_length": "unknown",
            "silhouette_volume": "unknown",
            "must_keep": [],
        }
        guided_set_detection = {
            "is_garment_set": False,
            "set_pattern_score": 0.0,
            "detected_garment_roles": [],
            "set_pattern_cues": [],
            "set_lock_mode": "off",
        }
        garment_hint = ""
        image_analysis = ""
        look_contract = {}

    diversity_context_prompt = (
        user_prompt or garment_hint or image_analysis or (effective_mode.description if effective_mode else "")
    )

    if has_images and effective_mode and not diversity_target:
        diversity_target = build_mode_diversity_target(
            effective_mode,
            user_prompt=diversity_context_prompt,
        )
    if effective_mode:
        diversity_target = harmonize_diversity_target_for_mode(
            effective_mode,
            diversity_target,
            user_prompt=diversity_context_prompt,
        )

    # Profile via Name Blending — persona anchor para o Gemini.
    # Modes criativos: identidade vem da MODEL SOUL, sem name blending.
    # Catalog_clean: mantém name blending para ancoragem determinística.
    is_creative = effective_mode and effective_mode.id != "catalog_clean"
    if is_creative:
        fallback_hint = ""
    elif effective_mode:
        fallback_hint, _, _ = _sample_diversity_target(
            casting_profile=effective_mode.presets.casting_profile,
        )
    else:
        fallback_hint, _, _ = _sample_diversity_target()

    profile = (diversity_target or {}).get("profile_hint", "") or fallback_hint
    # No text-only mode, cenário e pose são guiados pelos presets e estados latentes.
    # O compiler ainda recebe scenario_hint por compatibilidade, mas deixamos vazio
    # para não reintroduzir direção autoral fora da síntese principal.
    scenario = ""

    # Grounding: Camada 2 (pesquisa separada) removida — API-level ImageSearch (Camada 1) é suficiente.
    grounding_research = ""
    grounding_meta = {"effective": False, "mode": "off", "reason_codes": ["layer2_removed"]}
    grounded_images: List[bytes] = []
    grounding_pose_clause: str = ""

    context_text = build_generate_context_text(
        has_images=has_images,
        has_prompt=has_prompt,
        uploaded_images_count=len(uploaded_images or []),
        user_prompt=user_prompt,
        pool_context=pool_context,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        profile=profile,
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
        mode_defaults_text=describe_mode_defaults(effective_mode) if effective_mode else None,  # Sempre injetado (text + ref)
        reference_knowledge=build_reference_knowledge(
            user_prompt,
            has_images,
            compact_text_mode=has_prompt and not has_images,
        ),
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

    system_instruction = build_system_instruction(
        has_images=has_images,
        has_prompt=has_prompt,
    )

    def _call_prompt_model(context: str, temperature: float) -> Any:
        return generate_with_system_instruction(
            parts=_build_parts(context),
            system_instruction=system_instruction,
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
        result["shot_type"] = (
            preferred_shot_type_for_framing(effective_mode.presets.framing_profile)
            if effective_mode
            else _infer_text_mode_shot(user_prompt)
        )

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
        pose="",  # legado: MODE_PRESETS cuida da pose
        grounding_pose_clause=grounding_pose_clause,
        profile=profile,
        scenario=scenario,
        diversity_target=diversity_target,
        mode_id=effective_mode.id if effective_mode else "",
        framing_profile=effective_mode.presets.framing_profile if effective_mode else "",
        camera_type=effective_mode.presets.camera_type if effective_mode else "",
        capture_geometry=effective_mode.presets.capture_geometry if effective_mode else "",
        lighting_profile=effective_mode.presets.lighting_profile if effective_mode else "",
        pose_energy=effective_mode.presets.pose_energy if effective_mode else "",
        casting_profile=effective_mode.presets.casting_profile if effective_mode else "",
    )

    result["grounding"] = grounding_meta
    result["pipeline_mode"] = pipeline_mode
    result["category"] = normalized_category
    result["mode"] = effective_mode.id if effective_mode else None
    result["mode_label"] = effective_mode.label if effective_mode else None
    result["preset_defaults"] = effective_mode.presets.__dict__ if effective_mode else None
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
