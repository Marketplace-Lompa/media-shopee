"""
Helpers puros para montar o contexto textual enviado ao Prompt Agent.

O objetivo aqui é tirar de agent.py a montagem de blocos sem mover ainda
decisões maiores de policy ou contratos do pipeline.
"""
from __future__ import annotations

from typing import Any, Optional


def build_system_instruction(*, has_images: bool, has_prompt: bool) -> str:
    """Monta a system instruction filtrando modos irrelevantes ao cenário atual.

    No text-only (has_images=False, has_prompt=True):
      - Remove SYSTEM_MODE_2_RULES (referência visual) → ~150 tokens economizados
      - Remove SYSTEM_MODE_3_RULES (sem prompt) → ~50 tokens economizados
    Com imagens, envia tudo.
    """
    from agent_runtime.constants import (
        BASE_SYSTEM_BLOCKS,
        OUTPUT_SYSTEM_BLOCKS,
        POLICY_SYSTEM_BLOCKS,
        SYSTEM_OPERATING_MODES,
        SYSTEM_MODE_1_RULES,
        SYSTEM_MODE_2_RULES,
        SYSTEM_MODE_3_RULES,
    )

    # Seleciona apenas os modos relevantes ao cenário atual
    scenario_blocks = [SYSTEM_OPERATING_MODES.strip()]
    if has_prompt and not has_images:
        # Text-only: apenas MODE 1
        scenario_blocks.append(SYSTEM_MODE_1_RULES.strip())
    elif has_images:
        # Com imagem: MODE 1 (se tiver texto) + MODE 2 (sempre)
        if has_prompt:
            scenario_blocks.append(SYSTEM_MODE_1_RULES.strip())
        scenario_blocks.append(SYSTEM_MODE_2_RULES.strip())
    else:
        # Sem nada: MODE 3
        scenario_blocks.append(SYSTEM_MODE_3_RULES.strip())

    return "\n\n".join(
        BASE_SYSTEM_BLOCKS
        + OUTPUT_SYSTEM_BLOCKS
        + scenario_blocks
        + POLICY_SYSTEM_BLOCKS
    )


def _build_mode_block(
    *,
    has_images: bool,
    has_prompt: bool,
    user_prompt: Optional[str],
    uploaded_images_count: int,
) -> str:
    if has_images:
        if has_prompt:
            extra_text = f'User text to incorporate: "{user_prompt}".'
        else:
            extra_text = (
                "No text from user. Extract ONLY the garment structural skeleton (type, silhouette, fit, length) "
                "from the reference images — surface details like pattern, stitch, texture, and color are already "
                "conveyed by the images with higher fidelity than text. The person/model shown in the reference is NOT the "
                "subject — completely ignore her appearance. Build the hero shot around the "
                "DIVERSITY_TARGET new model profile, scenario, and pose."
            )
        mode_info = (
            f"MODE 2 — User sent {uploaded_images_count} reference image(s). "
            f"Extract GARMENT ONLY from the reference (do NOT use the reference person's appearance). "
            f"The reference model is a placeholder — she will be fully replaced by DIVERSITY_TARGET. "
            f"{extra_text}"
        )
    elif has_prompt:
        mode_info = (
            f'MODE 1 — Interpret this user text as a fashion/e-commerce creative brief: "{user_prompt}". '
            "Translate informal wording into professional fashion and photographic language when useful. "
            "Keep the garment as the protagonist, choose framing and scenario with commercial judgment, "
            "and complete missing gaps with taste and restraint. Output a complete photographic direction."
        )
    else:
        mode_info = (
            "MODE 3 — No prompt or images. Generate a creative, commercially attractive catalog prompt "
            "for Brazilian e-commerce. Use REFERENCE KNOWLEDGE for 3D garment vocabulary, "
            "Brazilian model diversity, scenario selection, and appropriate realism levers. "
            "Compose a complete photographic direction with coherent styling and garment-first framing."
        )
    return f"<MODE>\n{mode_info}\n</MODE>"


def _build_mode_presets_block(mode_defaults_text: Optional[str]) -> Optional[str]:
    if not mode_defaults_text:
        return None
    return f"<MODE_PRESETS>\n{mode_defaults_text}\n</MODE_PRESETS>"


def _build_mode_identity_block(mode_id: Optional[str]) -> Optional[str]:
    """Bloco de identidade criativa do mode — simétrico ao model_soul."""
    from agent_runtime.mode_identity_soul import get_mode_identity_soul
    lines = get_mode_identity_soul(mode_id)
    if not lines:
        return None
    return f"<MODE_IDENTITY>\n" + "\n".join(lines) + "\n</MODE_IDENTITY>"


def _build_semantic_briefs_block(diversity_target: Optional[dict[str, Any]]) -> Optional[str]:
    dt = diversity_target or {}
    semantic_briefs = dt.get("semantic_briefs") or {}
    if not isinstance(semantic_briefs, dict) or not semantic_briefs:
        return None

    ordered_briefs = [
        ("MODEL_BRIEF", semantic_briefs.get("model_brief")),
        ("SCENE_BRIEF", semantic_briefs.get("scene_brief")),
        ("POSE_BRIEF", semantic_briefs.get("pose_brief")),
        ("ANGLE_BRIEF", semantic_briefs.get("angle_brief")),
        ("CAMERA_BRIEF", semantic_briefs.get("camera_brief")),
    ]
    lines: list[str] = []
    for label, value in ordered_briefs:
        text = str(value or "").strip()
        if text:
            lines.append(f"{label}: {text}")
    if not lines:
        return None
    return "<SEMANTIC_BRIEFS>\n" + "\n".join(lines) + "\n</SEMANTIC_BRIEFS>"


def _build_model_soul_block(*, garment_hint: str, mode_id: Optional[str], has_images: bool) -> Optional[str]:
    from agent_runtime.model_soul import get_model_soul

    soul = str(get_model_soul(garment_context=garment_hint, mode_id=mode_id or "") or "").strip()
    if not soul:
        return None

    lines = [soul]
    if has_images:
        lines.append(
            "If the reference images contain a woman, make the new model read clearly distinct from her in overall identity, hair silhouette, and presence."
        )
    return "<MODEL_SOUL>\n" + "\n".join(lines) + "\n</MODEL_SOUL>"


def _build_casting_direction_block(casting_direction: Optional[dict[str, Any]]) -> Optional[str]:
    payload = casting_direction or {}
    confidence = float(payload.get("confidence", 0) or 0)
    chosen = payload.get("chosen_direction") or {}
    if confidence <= 0.35 or not isinstance(chosen, dict):
        return None

    candidate_labels = [
        str(item.get("label") or "").strip()
        for item in (payload.get("candidate_directions") or [])
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    ][:3]
    distinction_markers = ", ".join(str(item).strip() for item in (chosen.get("distinction_markers") or []) if str(item).strip()) or "none"
    anti_collapse = ", ".join(str(item).strip() for item in (payload.get("anti_collapse_signals") or []) if str(item).strip()) or "none"
    lines = [
        "<CASTING_DIRECTION>",
        "[Grounded casting direction for this specific job]",
        f"- alternates_considered: {', '.join(candidate_labels) or 'none'}",
        f"- chosen_direction: {str(payload.get('chosen_label') or chosen.get('label') or '').strip()}",
        f"- profile_hint: {str(payload.get('profile_hint') or '').strip()}",
        f"- age_logic: {str(chosen.get('age_logic') or '').strip()}",
        f"- face_geometry: {str(chosen.get('face_geometry') or '').strip()}",
        f"- skin_logic: {str(chosen.get('skin_logic') or '').strip()}",
        f"- hair_logic: {str(chosen.get('hair_logic') or '').strip()}",
        f"- body_logic: {str(chosen.get('body_logic') or '').strip()}",
        f"- presence_logic: {str(chosen.get('presence_logic') or '').strip()}",
        f"- expression_logic: {str(chosen.get('expression_logic') or '').strip()}",
        f"- makeup_logic: {str(chosen.get('makeup_logic') or '').strip()}",
        f"- distinction_markers: {distinction_markers}",
        f"- anti_collapse_signals: {anti_collapse}",
        "Use this as grounded casting direction for the woman in this generation.",
        "Do not copy these labels literally into the final prompt — synthesize them into a new original Brazilian woman.",
        "</CASTING_DIRECTION>",
    ]
    return "\n".join(lines)


def _build_scene_soul_block(*, mode_id: Optional[str], has_images: bool) -> Optional[str]:
    from agent_runtime.scene_soul import get_scene_soul

    soul = str(get_scene_soul(mode_id=mode_id, has_images=has_images) or "").strip()
    if not soul:
        return None
    return f"<SCENE_SOUL>\n{soul}\n</SCENE_SOUL>"


def _build_pose_soul_block(*, mode_id: Optional[str], has_images: bool) -> Optional[str]:
    from agent_runtime.pose_soul import get_pose_soul

    soul = str(get_pose_soul(mode_id=mode_id, has_images=has_images) or "").strip()
    if not soul:
        return None
    return f"<POSE_SOUL>\n{soul}\n</POSE_SOUL>"


def _build_capture_soul_block(*, mode_id: Optional[str], has_images: bool) -> Optional[str]:
    from agent_runtime.capture_soul import get_capture_soul

    soul = str(get_capture_soul(mode_id=mode_id, has_images=has_images) or "").strip()
    if not soul:
        return None
    return f"<CAPTURE_SOUL>\n{soul}\n</CAPTURE_SOUL>"


def _build_styling_soul_block(
    *,
    mode_id: Optional[str],
    has_images: bool,
) -> Optional[str]:
    from agent_runtime.styling_soul import get_styling_soul

    soul = str(get_styling_soul(mode_id=mode_id, has_images=has_images) or "").strip()
    if not soul:
        return None
    return f"<STYLING_SOUL>\n{soul}\n</STYLING_SOUL>"


def _build_styling_direction_block(styling_direction: Optional[dict[str, Any]]) -> Optional[str]:
    payload = styling_direction or {}
    confidence = float(payload.get("confidence", 0) or 0)
    if not payload or confidence <= 0.35:
        return None

    hero_components = ", ".join(payload.get("hero_components") or []) or "hero product only"
    completion_slots = ", ".join(payload.get("completion_slots") or []) or "none"
    lines = [
        "<STYLING_DIRECTION>",
        "[Job-specific styling resolution inferred after garment analysis]",
        f"- product_topology: {payload.get('product_topology', '')}",
        f"- hero_family: {payload.get('hero_family', '')}",
        f"- hero_components: {hero_components}",
        f"- completion_slots: {completion_slots}",
        f"- completion_strategy: {payload.get('completion_strategy', '')}",
        f"- primary_completion: {payload.get('primary_completion', '')}",
        f"- secondary_completion: {payload.get('secondary_completion', '')}",
        f"- footwear_direction: {payload.get('footwear_direction', '')}",
        f"- accessories_optional: {payload.get('accessories_optional', '')}",
        f"- outer_layer_optional: {payload.get('outer_layer_optional', '')}",
        f"- finish_logic: {payload.get('finish_logic', '')}",
        "Use this as a contextual styling direction for this specific generation.",
        "Do not copy these labels literally into the final prompt — synthesize them into fluent visual prose.",
        "</STYLING_DIRECTION>",
    ]
    return "\n".join(lines)


def _build_output_parameters_block(*, aspect_ratio: str, resolution: str) -> str:
    return f"<OUTPUT_PARAMETERS>\naspect_ratio={aspect_ratio}\nresolution={resolution}\n</OUTPUT_PARAMETERS>"


def _build_diversity_target_block(
    *,
    profile: str,
    diversity_target: Optional[dict[str, Any]],
    has_images: bool,
    garment_hint: str = "",
) -> str:
    dt = diversity_target or {}

    block = "<DIVERSITY_TARGET>\n"
    if dt.get("profile_id"):
        block += f"Model profile ID: {dt['profile_id']}.\n"

    # ── Regras anti-cópia + fidelidade de roupa (só quando há imagens de referência) ────
    if has_images:
        block += (
            "GARMENT-ONLY REFERENCE MODE:\n"
            "  - The uploaded reference image is the SOLE SOURCE OF TRUTH for the garment.\n"
            "  - Copy EXACTLY from reference: color, fabric, texture, pattern scale, construction, silhouette, drape.\n"
            "  - Preserve garment geometry: opening style, sleeve architecture, hem behavior, garment length, neckline shape.\n"
            "  - NEVER simplify, reinterpret, or hallucinate garment details that differ from the reference.\n"
            "  - Discard the reference model completely. Invent a NEW person. Do not copy face, skin, hair, body, or pose.\n"
            "  - Model and scene are FREE — only the GARMENT must match the reference with absolute fidelity.\n"
        )

    block += (
        "Scenario, model, pose, angle, and camera direction come from MODE_IDENTITY and the active SOUL blocks.\n"
        "Inside those directions, invent a fresh specific solution instead of repeating a generic safe default.\n"
        "Never mention preset labels or metatextual terms like capture geometry, scenario family, or lighting profile in the final prompt.\n"
        "Write one canonical final prompt directly usable by the image generator.\n"
    )
    block += "</DIVERSITY_TARGET>"
    return block





def _build_guided_brief_block(
    *,
    guided_enabled: bool,
    guided_brief: Optional[dict[str, Any]],
    guided_set_mode: str,
    guided_set_detection: dict[str, Any],
    has_images: bool,
) -> Optional[str]:
    if not guided_enabled:
        return None

    garment = (guided_brief or {}).get("garment", {}) or {}
    model = (guided_brief or {}).get("model", {}) or {}
    scene = (guided_brief or {}).get("scene", {}) or {}
    pose_cfg = (guided_brief or {}).get("pose", {}) or {}
    capture = (guided_brief or {}).get("capture", {}) or {}
    fidelity_mode = str((guided_brief or {}).get("fidelity_mode", "balanceada")).strip().lower()

    block = (
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
        block += (
            "\n\n[GUIDED SET DETECTION]\n"
            f"- set_pattern_score: {guided_set_detection.get('set_pattern_score', 0.0)}\n"
            f"- detected_garment_roles: {', '.join(guided_set_detection.get('detected_garment_roles', []) or []) or 'unknown'}\n"
            f"- set_pattern_cues: {', '.join(guided_set_detection.get('set_pattern_cues', []) or []) or 'unknown'}\n"
            f"- set_lock_mode: {guided_set_detection.get('set_lock_mode', 'generic')}"
        )
    block += "\n</GUIDED_BRIEF>"
    return block


def _build_structural_contract_block(
    *,
    has_images: bool,
    structural_contract: dict[str, Any],
) -> Optional[str]:
    """Prosa orientativa sobre a geometria da peça — sem jargão técnico de moda.

    O agente tende a ecoar termos técnicos (dolman_batwing, cocoon) literalmente
    no prompt final, o que pode confundir o modelo visual. Usamos linguagem natural
    de relacionamento: o que preservar, não como classificar.
    """
    if not has_images or not structural_contract.get("enabled"):
        return None

    # Montar descrição em prosa a partir dos campos estruturais
    traits: list[str] = []

    subtype = str(structural_contract.get("garment_subtype", "") or "").strip()
    if subtype and subtype != "unknown":
        traits.append(subtype.replace("_", " "))

    volume = str(structural_contract.get("silhouette_volume", "") or "").strip()
    if volume and volume != "unknown":
        traits.append(f"{volume} silhouette")

    front = str(structural_contract.get("front_opening", "") or "").strip()
    if front == "open":
        traits.append("open front")
    elif front == "partial":
        traits.append("partially open front")

    length = str(structural_contract.get("garment_length", "") or "").strip()
    if length and length != "unknown":
        traits.append(f"{length.replace('_', '-')} length")

    must_keep = [str(c).strip() for c in (structural_contract.get("must_keep", []) or []) if str(c).strip()]

    trait_text = ", ".join(traits) if traits else "the garment as shown"
    cue_text = "; ".join(must_keep[:3]) if must_keep else ""

    prose = (
        "<STRUCTURAL_CONTRACT>\n"
        f"The reference shows a {trait_text}. "
        "Preserve the overall shape, proportions, sleeve coverage, hem behavior, and construction "
        "exactly as visible in the reference images. "
        "Do not redesign, simplify, or reinterpret the garment structure."
    )
    if cue_text:
        prose += f"\nKey visual anchors to preserve: {cue_text}."
    prose += "\n</STRUCTURAL_CONTRACT>"
    return prose


def _build_grounding_results_block(
    *,
    grounding_research: str,
    grounding_effective: bool,
) -> Optional[str]:
    if not grounding_research or not grounding_effective:
        return None
    return (
        "<GROUNDING_RESULTS>\n"
        "[Use this to correctly identify the garment]\n"
        f"{grounding_research}\n"
        "</GROUNDING_RESULTS>"
    )


def _build_triage_hint_block(grounding_context_hint: Optional[str]) -> Optional[str]:
    if not grounding_context_hint:
        return None
    return (
        "<TRIAGE_HINT>\n"
        f"Garment hypothesis: {grounding_context_hint}. Keep this silhouette strictly.\n"
        "</TRIAGE_HINT>"
    )


def _build_grounding_constraints_block(
    *,
    grounding_mode: str,
    has_images: bool,
    structural_contract: dict[str, Any],
) -> Optional[str]:
    if grounding_mode != "full" or not has_images:
        return None

    attrs = [
        ("front_opening", "front opening"),
        ("garment_length", "garment length"),
        ("silhouette_volume", "volume"),
        ("hem_shape", "hem shape"),
        ("sleeve_type", "sleeve type"),
    ]
    parts = [
        f"{label}: {structural_contract.get(attr, 'unknown')}"
        for attr, label in attrs
        if structural_contract.get(attr, "unknown") not in ("unknown", "", None)
    ]
    if parts:
        body = (
            "Silhouette constraints (detected from reference images): "
            + ", ".join(parts)
            + ".\nMaintain these geometry attributes in the generated image.\n"
        )
    else:
        body = (
            "Silhouette constraints: maintain the detected garment geometry "
            "(opening behavior, sleeve architecture, hem shape, garment length) "
            "from reference images.\n"
        )
    return f"<GROUNDING_CONSTRAINTS>\n{body}</GROUNDING_CONSTRAINTS>"


def build_generate_context_text(
    *,
    has_images: bool,
    has_prompt: bool,
    uploaded_images_count: int,
    user_prompt: Optional[str],
    pool_context: str,
    aspect_ratio: str,
    resolution: str,
    profile: str,
    diversity_target: Optional[dict[str, Any]],
    guided_enabled: bool,
    guided_brief: Optional[dict[str, Any]],
    guided_set_mode: str,
    guided_set_detection: dict[str, Any],
    structural_contract: dict[str, Any],
    casting_direction: Optional[dict[str, Any]],
    styling_direction: Optional[dict[str, Any]],
    grounding_research: str,
    grounding_effective: bool,
    grounding_context_hint: Optional[str],
    grounding_mode: str,
    mode_defaults_text: Optional[str],
    reference_knowledge: str,
    mode_id: Optional[str] = None,
    garment_hint: str = "",
) -> str:
    # A ordem dos blocos e deliberada: primeiro tarefa/constraints de alto nivel,
    # depois contexto especializado. Mudar a sequencia sem validar pode degradar
    # a qualidade do prompt por efeito de prioridade/lost-in-the-middle.
    blocks = [
        _build_mode_block(
            has_images=has_images,
            has_prompt=has_prompt,
            user_prompt=user_prompt,
            uploaded_images_count=uploaded_images_count,
        )
    ]

    structural_block = _build_structural_contract_block(
        has_images=has_images,
        structural_contract=structural_contract,
    )
    if structural_block and has_images:
        blocks.append(structural_block)

    mode_identity_block = _build_mode_identity_block(mode_id)
    if mode_identity_block:
        blocks.append(mode_identity_block)

    model_soul_block = _build_model_soul_block(
        garment_hint=garment_hint,
        mode_id=mode_id,
        has_images=has_images,
    )
    if model_soul_block:
        blocks.append(model_soul_block)

    casting_direction_block = _build_casting_direction_block(casting_direction)
    if casting_direction_block:
        blocks.append(casting_direction_block)

    scene_soul_block = _build_scene_soul_block(
        mode_id=mode_id,
        has_images=has_images,
    )
    if scene_soul_block:
        blocks.append(scene_soul_block)

    pose_soul_block = _build_pose_soul_block(
        mode_id=mode_id,
        has_images=has_images,
    )
    if pose_soul_block:
        blocks.append(pose_soul_block)

    capture_soul_block = _build_capture_soul_block(
        mode_id=mode_id,
        has_images=has_images,
    )
    if capture_soul_block:
        blocks.append(capture_soul_block)

    styling_soul_block = _build_styling_soul_block(
        mode_id=mode_id,
        has_images=has_images,
    )
    if styling_soul_block:
        blocks.append(styling_soul_block)

    styling_direction_block = _build_styling_direction_block(styling_direction)
    if styling_direction_block:
        blocks.append(styling_direction_block)

    semantic_briefs_block = _build_semantic_briefs_block(diversity_target)
    if semantic_briefs_block:
        blocks.append(semantic_briefs_block)

    mode_presets_block = _build_mode_presets_block(mode_defaults_text)
    if mode_presets_block:
        blocks.append(mode_presets_block)

    if pool_context.strip():
        blocks.append(f"<POOL_CONTEXT>\n{pool_context}\n</POOL_CONTEXT>")

    blocks.append(_build_output_parameters_block(aspect_ratio=aspect_ratio, resolution=resolution))
    blocks.append(
        _build_diversity_target_block(
            profile=profile,
            diversity_target=diversity_target,
            has_images=has_images,
            garment_hint=garment_hint,
        )
    )

    guided_block = _build_guided_brief_block(
        guided_enabled=guided_enabled,
        guided_brief=guided_brief,
        guided_set_mode=guided_set_mode,
        guided_set_detection=guided_set_detection,
        has_images=has_images,
    )
    if guided_block:
        blocks.append(guided_block)

    if structural_block and not has_images:
        blocks.append(structural_block)

    grounding_results_block = _build_grounding_results_block(
        grounding_research=grounding_research,
        grounding_effective=grounding_effective,
    )
    if grounding_results_block:
        blocks.append(grounding_results_block)

    triage_hint_block = _build_triage_hint_block(grounding_context_hint)
    if triage_hint_block:
        blocks.append(triage_hint_block)

    grounding_constraints_block = _build_grounding_constraints_block(
        grounding_mode=grounding_mode,
        has_images=has_images,
        structural_contract=structural_contract,
    )
    if grounding_constraints_block:
        blocks.append(grounding_constraints_block)

    if reference_knowledge.strip():
        blocks.append(reference_knowledge)
    blocks.append("Return ONLY valid JSON matching the schema. No markdown, no explanation.")
    return "\n\n".join(blocks)
