"""
Prompt Agent — Gemini Flash (texto).

Orquestrador principal: recebe inputs, monta contexto, chama Gemini, compila prompt.
Funções de inferência visual e diversidade vivem em agent_runtime/.

3 modos de operação:
  MODO 1: Usuário deu prompt → agente refina aplicando skills
  MODO 2: Usuário enviou imagens → agente descreve e cria prompt (Fidelity Lock)
  MODO 3: Sem prompt nem imagens → agente gera do zero via contexto do pool
"""
import re
from typing import Any, Optional, List

from google.genai import types

from agent_runtime.gemini_client import generate_with_system_instruction
from agent_runtime.parser import _extract_response_text, _decode_agent_response
from agent_runtime.camera import (
    _extract_camera_realism_block,
    _select_camera_realism_profile,
    _normalize_camera_realism_block,
    _compose_prompt_with_camera,
)
from agent_runtime.structural import normalize_prompt_text
from agent_runtime.compiler import _compile_prompt_v2, _count_words
from agent_runtime.grounding import _run_grounding_research
from agent_runtime.triage import (
    _infer_garment_hint,
    _infer_structural_contract_from_images,
    _infer_set_pattern_from_images,
    _infer_unified_vision_triage,
    _infer_text_mode_shot,
)
from agent_runtime.diversity import _sample_diversity_target
from agent_runtime.constants import (
    AGENT_RESPONSE_SCHEMA,
    SYSTEM_INSTRUCTION,
    REFERENCE_KNOWLEDGE,
)

from guided_mode import guided_capture_to_shot, guided_summary


def _sanitize_garment_narrative(text: str, structural_contract: Optional[dict]) -> str:
    narrative = re.sub(r"\s+", " ", (text or "").strip())
    if not narrative:
        return ""

    contract = structural_contract or {}
    subtype = str(contract.get("garment_subtype", "unknown")).strip().lower()
    sleeve_type = str(contract.get("sleeve_type", "unknown")).strip().lower()
    must_keep = " ".join(str(x).lower() for x in (contract.get("must_keep", []) or []))
    drapedish = (
        subtype in {"ruana_wrap", "poncho", "cape"}
        or sleeve_type == "cape_like"
        or "continuous neckline-to-front edge" in must_keep
        or "rounded cocoon side drop" in must_keep
    )

    if drapedish:
        narrative = re.sub(r"(?i)\b(?:striped\s+)?(?:crochet|knit)?\s*(?:cocoon\s+)?shrug\b", "draped knit wrap", narrative)
        narrative = re.sub(r"(?i)\b(?:oversized\s+)?cocoon cardigan\b", "draped knit wrap", narrative)
        narrative = re.sub(r"(?i)\bcardigan\b", "draped knit wrap", narrative)
        narrative = re.sub(r"(?i)\b(?:integrated\s+)?(?:wide\s+)?(?:batwing|dolman)\s+sleeves?\b", "fluid draped arm coverage", narrative)
        narrative = re.sub(r"(?i)\bopen-front cocoon silhouette\b", "open draped cocoon silhouette", narrative)
        narrative = re.sub(r"(?i)\bopen front\b", "soft open front edge", narrative)
        narrative = re.sub(r"(?i)\b(?:continuous\s+)?(?:ribbed\s+)?collar\b", "continuous knitted edge", narrative)
        narrative = re.sub(r"(?i)\bcollar band\b", "knitted edge finish", narrative)
        narrative = re.sub(r"(?i)\b(draped)\s*\1\b", r"\1", narrative)
        narrative = re.sub(r"(?i)\b(draped)(draped)\b", r"\1", narrative)

    if subtype == "other" and re.search(r"(?i)\b(?:shrug|cardigan)\b", narrative):
        return ""

    return narrative.strip(" .,")


def run_agent(
    user_prompt: Optional[str],
    uploaded_images: Optional[List[bytes]],
    pool_context: str,
    aspect_ratio: str,
    resolution: str,
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
    guided_enabled = bool(guided_brief and guided_brief.get("enabled"))
    guided_set_mode = str((((guided_brief or {}).get("garment") or {}).get("set_mode") or "")).strip().lower()
    guided_set_detection = {
        "is_garment_set": False,
        "set_pattern_score": 0.0,
        "detected_garment_roles": [],
        "set_pattern_cues": [],
        "set_lock_mode": "off",
    }
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
    has_pool = False

    # ── Triagem visual unificada: UMA chamada Gemini por run_agent() ─────────
    # Consolida _infer_garment_hint + _infer_structural_contract + _infer_set_pattern
    # em uma única chamada. Fallback seguro para as funções individuais se falhar.
    _unified: Optional[dict] = None
    _unified_garment_hint: str = ""
    _unified_image_analysis: str = ""
    _unified_look_contract: dict = {}
    if has_images:
        if isinstance(structural_contract_hint, dict) and structural_contract_hint:
            # structural_contract já fornecido externamente — ainda roda unificada para hint/set
            structural_contract = structural_contract_hint
            _unified_garment_hint = _infer_garment_hint(uploaded_images or [])
            print(f"[AGENT] unified_vision_triage: skipped (external structural_contract_hint provided)")
        elif isinstance(unified_vision_triage_result, dict) and unified_vision_triage_result:
            _unified = unified_vision_triage_result
            print(f"[AGENT] unified_vision_triage: using pre-computed result")
        else:
            _unified = _infer_unified_vision_triage(uploaded_images or [], user_prompt)

        if _unified:
            structural_contract   = _unified["structural_contract"]
            _unified_garment_hint = _unified["garment_hint"]
            _unified_image_analysis = _unified.get("image_analysis", "")
            _unified_look_contract = _unified.get("look_contract", {})
            # set_detection: aplica override de lock_mode se necessário
            _sd = _unified["set_detection"]
            if guided_enabled and guided_set_mode == "conjunto":
                if _sd.get("set_lock_mode") == "off":
                    _sd["set_lock_mode"] = "generic"
                guided_set_detection = _sd
        elif not (isinstance(structural_contract_hint, dict) and structural_contract_hint):
            # Fallback individual (não entra quando structural_contract_hint externo)
            print("[AGENT] unified_vision_triage: fallback")
            structural_contract = _infer_structural_contract_from_images(uploaded_images or [], user_prompt)
            if guided_enabled and guided_set_mode == "conjunto":
                guided_set_detection = _infer_set_pattern_from_images(uploaded_images or [], user_prompt)
                if guided_set_detection.get("set_lock_mode") == "off":
                    guided_set_detection["set_lock_mode"] = "generic"
            _unified_garment_hint = _infer_garment_hint(uploaded_images or [])
    elif guided_enabled and guided_set_mode == "conjunto":
        # Sem imagens: set detection sem triagem visual
        guided_set_detection = _infer_set_pattern_from_images([], user_prompt)

    if has_images:
        # FIX: ternário separado para não engolir o MODE 2
        if has_prompt:
            extra_text = f'User text to incorporate: "{user_prompt}".'
        else:
            extra_text = (
                "No text from user. Extract ONLY the garment (color, fabric, structure, pattern) "
                "from the reference images. The person/model shown in the reference is NOT the "
                "subject — completely ignore her appearance. Build the hero shot around the "
                "DIVERSITY_TARGET new model profile, scenario, and pose."
            )
        mode_info = (
            f"MODE 2 — User sent {len(uploaded_images)} reference image(s). "
            f"Extract GARMENT ONLY from the reference (do NOT use the reference person's appearance). "
            f"The reference model is a placeholder — she will be fully replaced by DIVERSITY_TARGET. "
            f"{extra_text}"
        )
    elif has_prompt:
        mode_info = (
            f'MODE 1 — TRANSLATE this user intent into a technically precise photographic prompt: "{user_prompt}". '
            "The user may write in Portuguese or use casual terms. Map every term to technical English "
            "using REFERENCE KNOWLEDGE (especially the BRAZILIAN TERM MAPPING section). "
            "Apply 3D garment description, select appropriate realism levers, and choose a scenario "
            "that complements the garment aesthetic. Output a complete photographic direction."
        )
    else:
        mode_info = (
            "MODE 3 — No prompt or images. Generate a creative, commercially attractive catalog prompt "
            "for Brazilian e-commerce. Use REFERENCE KNOWLEDGE for 3D garment vocabulary, "
            "Brazilian model diversity, scenario selection, and appropriate realism levers. "
            "Compose a complete photographic direction with coherent styling and garment-first framing."
        )

    # ── Construção da Mensagem em Blocos (Mitiga "lost in the middle") ──
    blocks: List[str] = []

    blocks.append(f"<MODE>\n{mode_info}\n</MODE>")

    if has_pool:
        blocks.append(f"<POOL_CONTEXT>\n{pool_context}\n</POOL_CONTEXT>")

    blocks.append(f"<OUTPUT_PARAMETERS>\naspect_ratio={aspect_ratio}\nresolution={resolution}\n</OUTPUT_PARAMETERS>")

    # Profile: SEMPRE gera dinamicamente via name blending (ignora _PROFILE_POOL estático
    # que produz AI Face com anatomia explícita). Scenario/pose: usa diversity_target
    # para preservar lógica anti-repeat do select_diversity_target.
    _fb_profile, _fb_scenario, _fb_pose = _sample_diversity_target()
    profile = (diversity_target or {}).get("profile_prompt", "") or _fb_profile
    if diversity_target:
        scenario = diversity_target.get("scenario_prompt", "") or _fb_scenario
        pose = diversity_target.get("pose_prompt", "") or _fb_pose
    else:
        scenario = _fb_scenario
        pose = _fb_pose

    div_block = "<DIVERSITY_TARGET>\n"
    if diversity_target:
        div_block += f"Model profile ID: {diversity_target.get('profile_id', 'RUNTIME')}.\n"
    div_block += (
        # ── GARMENT-ONLY REFERENCE MODE ─────────────────────────────────────────────
        # A pessoa/modelo na imagem de referência NÃO faz parte deste produto.
        # O compilador deve extrair APENAS a peça e construir uma modelo nova do zero.
        "GARMENT-ONLY REFERENCE MODE — CRITICAL RULES:\n"
        "  1. Reference images = garment source ONLY (color, fabric, structure, pattern).\n"
        "  2. The model/person visible in the reference is NOT the subject. Discard her completely.\n"
        "  3. DO NOT copy reference model's face, skin tone, hair, body shape, height, or pose.\n"
        "  4. DO NOT describe or reference the person shown — treat reference as if she were a mannequin.\n"
        f"  5. GENERATE A BRAND NEW MODEL based on this regional anchor: {profile}\n"
        "     YOU MUST invent unique physical characteristics for her: skin tone, hair color/style,\n"
        "     approximate age, and build. Choose features that complement the garment aesthetic.\n"
        "     Be specific (e.g. 'warm olive skin, wavy dark hair, mid-20s') — vague = repetitive results.\n"
        f"  6. Place new model in scenario: {scenario}\n"
        f"  7. Use pose: {pose}\n"
        "  8. In base_prompt: open with the new model (including her physical description) BEFORE garment.\n"
        "     Example: 'RAW photo, [regional anchor], [skin], [hair], [age]. Wearing [garment]...'\n"
        "</DIVERSITY_TARGET>"
    )
    blocks.append(div_block)

    if guided_enabled:
        garment = (guided_brief or {}).get("garment", {}) or {}
        model = (guided_brief or {}).get("model", {}) or {}
        scene = (guided_brief or {}).get("scene", {}) or {}
        pose_cfg = (guided_brief or {}).get("pose", {}) or {}
        capture = (guided_brief or {}).get("capture", {}) or {}
        fidelity_mode = str((guided_brief or {}).get("fidelity_mode", "balanceada")).strip().lower()
        
        guided_str = (
            "<GUIDED_BRIEF>\n"
            "[Deterministic constraints, must obey]\n"
            f"- model_age_range: {model.get('age_range', '25-34')}\n"
            f"- set_mode: {garment.get('set_mode', 'unica')}\n"
            f"- scene_type: {scene.get('type', 'externo')}\n"
            f"- pose_style: {pose_cfg.get('style', 'tradicional')}\n"
            f"- capture_distance: {capture.get('distance', 'media')}\n"
            f"- fidelity_mode: {fidelity_mode}\n"
            "If set_mode is conjunto, map garment-set pieces via repeated color/texture/motif cues from references."
        )
        if guided_set_mode == "conjunto" and has_images:
            guided_str += (
                "\n\n[GUIDED SET DETECTION]\n"
                f"- set_pattern_score: {guided_set_detection.get('set_pattern_score', 0.0)}\n"
                f"- detected_garment_roles: {', '.join(guided_set_detection.get('detected_garment_roles', []) or []) or 'unknown'}\n"
                f"- set_pattern_cues: {', '.join(guided_set_detection.get('set_pattern_cues', []) or []) or 'unknown'}\n"
                f"- set_lock_mode: {guided_set_detection.get('set_lock_mode', 'generic')}"
            )
        guided_str += "\n</GUIDED_BRIEF>"
        blocks.append(guided_str)

    if has_images and structural_contract.get("enabled"):
        cues = ", ".join(structural_contract.get("must_keep", []) or []) or "none"
        sc_str = (
            "<STRUCTURAL_CONTRACT>\n"
            "[Preserve garment geometry from references]\n"
            f"- garment_subtype: {structural_contract.get('garment_subtype', 'unknown')}\n"
            f"- sleeve_type: {structural_contract.get('sleeve_type', 'unknown')}\n"
            f"- sleeve_length: {structural_contract.get('sleeve_length', 'unknown')}\n"
            f"- front_opening: {structural_contract.get('front_opening', 'unknown')}\n"
            f"- hem_shape: {structural_contract.get('hem_shape', 'unknown')}\n"
            f"- garment_length: {structural_contract.get('garment_length', 'unknown')}\n"
            f"- silhouette_volume: {structural_contract.get('silhouette_volume', 'unknown')}\n"
            f"- confidence: {structural_contract.get('confidence', 0.0)}\n"
            f"- must_keep_cues: {cues}\n"
            "Treat these as shape/proportion constraints. Maintain sleeve/hem proportions exactly. "
            "Pay special attention to garment_subtype — it defines the construction method.\n"
            "</STRUCTURAL_CONTRACT>"
        )
        blocks.append(sc_str)

    # ── LOOK CONTRACT — styling coerência (campo 7 do unified_vision_triage) ──
    _lc = _unified_look_contract
    if _lc and float(_lc.get("confidence", 0) or 0) > 0.5:
        _forbidden_str = ", ".join(_lc.get("forbidden_bottoms") or []) or "none"
        _kw_str = ", ".join(_lc.get("style_keywords") or []) or ""
        lc_block = (
            "<LOOK_CONTRACT>\n"
            "[Styling constraints — outfit must be coherent with the target garment]\n"
            f"- bottom_style: {_lc.get('bottom_style', '')}\n"
            f"- bottom_color: {_lc.get('bottom_color', '')}\n"
            f"- color_family: {_lc.get('color_family', '')}\n"
            f"- season: {_lc.get('season', '')}\n"
            f"- occasion: {_lc.get('occasion', '')}\n"
            f"- forbidden_bottoms: {_forbidden_str}\n"
            f"- accessories: {_lc.get('accessories', '')}\n"
            f"- style_keywords: {_kw_str}\n"
            "Use bottom_style and bottom_color as the primary guide for the "
            "model's lower garment. NEVER suggest a forbidden_bottom type.\n"
            "</LOOK_CONTRACT>"
        )
        blocks.append(lc_block)

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
                garment_hint_override=_unified_garment_hint,
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

    if grounding_research and grounding_meta.get("effective"):
        blocks.append(
            "<GROUNDING_RESULTS>\n"
            "[Use this to correctly identify the garment]\n"
            f"{grounding_research}\n"
            "</GROUNDING_RESULTS>"
        )
    if grounding_context_hint:
        blocks.append(
            "<TRIAGE_HINT>\n"
            f"Garment hypothesis: {grounding_context_hint}. Keep this silhouette strictly.\n"
            "</TRIAGE_HINT>"
        )

    if grounding_mode == "full" and has_images:
        _sc_attrs = [
            ("front_opening",    "front opening"),
            ("garment_length",   "garment length"),
            ("silhouette_volume","volume"),
            ("hem_shape",        "hem shape"),
            ("sleeve_type",      "sleeve type"),
        ]
        _sc_parts = [
            f"{label}: {structural_contract.get(attr, 'unknown')}"
            for attr, label in _sc_attrs
            if structural_contract.get(attr, "unknown") not in ("unknown", "", None)
        ]
        
        sil_str = "<GROUNDING_CONSTRAINTS>\n"
        if _sc_parts:
            sil_str += "Silhouette constraints (detected from reference images): " + ", ".join(_sc_parts) + ".\n"
            sil_str += "Maintain these geometry attributes in the generated image.\n"
        else:
            sil_str += (
                "Silhouette constraints: maintain the detected garment geometry "
                "(opening behavior, sleeve architecture, hem shape, garment length) "
                "from reference images.\n"
            )
        sil_str += "</GROUNDING_CONSTRAINTS>"
        blocks.append(sil_str)

    blocks.append(REFERENCE_KNOWLEDGE)
    blocks.append("Return ONLY valid JSON matching the schema. No markdown, no explanation.")

    context_text = "\n\n".join(blocks)

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
            system_instruction=SYSTEM_INSTRUCTION,
            schema=AGENT_RESPONSE_SCHEMA,
            temperature=temperature,
            max_tokens=8192
        )

    response = _call_prompt_model(context_text, temperature=0.75)

    # ── DECODE: caminho principal (schema) → fallback robusto (_parse_json) ──
    result = None
    # 1) Tenta response.parsed (disponível com schema enforced)
    try:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict) and ("base_prompt" in parsed or "prompt" in parsed):
            result = parsed
            print("[AGENT] ✅ JSON via response.parsed (schema enforced)")
    except Exception:
        pass

    # 2) Fallback: parser robusto existente (lida com respostas malformadas/vazias)
    if result is None:
        try:
            result = _decode_agent_response(response)
            print("[AGENT] ✅ JSON via _decode_agent_response (parser robusto)")
        except Exception as primary_error:
            print(f"[AGENT] ⚠️  JSON parse failed (attempt 1): {primary_error}")
            raw_preview = _extract_response_text(response)[:320].replace("\n", "\\n")
            print(f"[AGENT] ⚠️  Raw preview: {raw_preview}")

            # 3) Retry: mantemos todo_ o contexto estruturado (inclusive XML tags) mas reforçamos o JSON
            retry_context = (
                context_text
                + "\n\n[RETRY TRIGGERED]: The previous response was not valid JSON. You MUST return EXACTLY ONE valid JSON object, without markdown wrappers like ```json"
            )

            response_retry = _call_prompt_model(retry_context, temperature=0.2)
            try:
                result = _decode_agent_response(response_retry)
                print("[AGENT] ✅ JSON parse recovered on retry without grounding context.")
            except Exception as retry_error:
                raw_retry = _extract_response_text(response_retry)[:320].replace("\n", "\\n")
                print(f"[AGENT] ❌ JSON parse failed (attempt 2): {retry_error}")
                print(f"[AGENT] ❌ Retry raw preview: {raw_retry}")
                raise ValueError(f"AGENT_JSON_INVALID: {retry_error}") from retry_error

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

    base_prompt_raw = str(result.get("base_prompt", "") or "").strip()
    legacy_prompt_raw = str(result.get("prompt", "") or "").strip()
    if not base_prompt_raw:
        base_prompt_raw = legacy_prompt_raw
    if not base_prompt_raw:
        base_prompt_raw = "RAW photo, polished e-commerce catalog composition with garment-first framing."

    # M3: garment_narrative — campo JSON dedicado com descrição limpa da peça
    garment_narrative = str(result.get("garment_narrative", "") or "").strip()
    # Sanitizar: max 30 palavras, sem menções a pessoa/cenário residuais
    if garment_narrative:
        garment_narrative = _sanitize_garment_narrative(garment_narrative, structural_contract)
        gn_words = garment_narrative.split()
        if len(gn_words) > 35:
            garment_narrative = " ".join(gn_words[:35])
            gn_words = garment_narrative.split()
        if garment_narrative:
            print(f"[AGENT] 👗 garment_narrative ({len(gn_words)}w): {garment_narrative[:120]}")

    camera_realism_raw = str(result.get("camera_and_realism", "") or "").strip()
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(legacy_prompt_raw)
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(base_prompt_raw)
    camera_profile = _select_camera_realism_profile(
        has_images=has_images,
        has_prompt=has_prompt,
        user_prompt=user_prompt,
        base_prompt=base_prompt_raw,
        camera_text=camera_realism_raw,
    )
    camera_realism = _normalize_camera_realism_block(
        camera_realism_raw,
        str(result.get("shot_type", "auto")),
        profile=camera_profile,
    )
    camera_words = _count_words(camera_realism)
    base_budget = max(80, 220 - camera_words)
    if has_images and not has_prompt:
        # Art Director: budget para acomodar garment_narrative + lighting_hint + gaze + scenario
        # Profile(14w) + narrative(28w) + P1(~40w) + cover(12w) + stance(10w)
        # + texture(6w) + model(3w) + gaze(6w) + scenario(10w) + lighting(8w) + scene(8w) = ~175w
        # Headroom de +40w para clauses não previstas
        target_budget = 215
        base_budget = max(80, target_budget - camera_words)

    # M2/R5: lighting_hint do diversity_target (seleção garment-aware)
    _lighting_hint = (diversity_target or {}).get("lighting_hint", "") or ""

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
        lighting_hint=_lighting_hint if (has_images and not has_prompt) else "",
    )
    final_prompt = _compose_prompt_with_camera(compiled_base_prompt, camera_realism)
    result["base_prompt"] = compiled_base_prompt
    result["camera_and_realism"] = camera_realism
    result["camera_profile"] = camera_profile
    result["prompt"] = final_prompt
    compiler_debug["camera_words"] = camera_words
    compiler_debug["base_budget"] = base_budget
    compiler_debug["camera_profile"] = camera_profile
    compiler_debug["final_words"] = _count_words(final_prompt)
    result["prompt_compiler_debug"] = compiler_debug

    result["grounding"] = grounding_meta
    result["pipeline_mode"] = pipeline_mode
    result["model_profile_id"] = diversity_target.get("profile_id") if diversity_target else None
    result["diversity_target"] = diversity_target or {}
    result["image_analysis"] = _unified_image_analysis
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
    print(f"[AGENT] Images sent: {len(uploaded_images) if uploaded_images else 0}")
    print(f"[AGENT] Pool context: {'Yes' if has_pool else 'No'}")
    print(f"[AGENT] Thinking: {result.get('thinking_level')} | Shot: {result.get('shot_type')} | Realism: {result.get('realism_level')}")
    analysis = result.get("image_analysis", "")
    if analysis:
        print(f"[AGENT] 🔍 Image Analysis: {analysis}")
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

    from normalize_user_intent import normalize_user_intent
    extra_direction = str(instruction_notes or "").strip()
    base_direction = str(user_prompt or "").strip()
    if extra_direction:
        result["user_intent"] = normalize_user_intent(extra_direction)
    else:
        result["user_intent"] = normalize_user_intent(base_direction)

    return result
