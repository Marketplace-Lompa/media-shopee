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
                "No text from user. Extract ONLY the garment (color, fabric, structure, pattern) "
                "from the reference images. The person/model shown in the reference is NOT the "
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


def _build_output_parameters_block(*, aspect_ratio: str, resolution: str) -> str:
    return f"<OUTPUT_PARAMETERS>\naspect_ratio={aspect_ratio}\nresolution={resolution}\n</OUTPUT_PARAMETERS>"


def _build_diversity_target_block(
    *,
    profile: str,
    scenario: str,
    pose: str,
    diversity_target: Optional[dict[str, Any]],
    has_images: bool,
) -> str:
    block = "<DIVERSITY_TARGET>\n"
    if diversity_target:
        block += f"Model profile ID: {diversity_target.get('profile_id', 'RUNTIME')}.\n"

    if has_images:
        # Referência visual: regras de extração garment-only + descarte de modelo
        block += (
            "GARMENT-ONLY REFERENCE MODE — CRITICAL RULES:\n"
            "  1. Reference images = garment source ONLY (color, fabric, structure, pattern).\n"
            "  2. The model/person visible in the reference is NOT the subject. Discard her completely.\n"
            "  3. DO NOT copy reference model's face, skin tone, hair, body shape, height, or pose.\n"
            "  4. DO NOT describe or reference the person shown — treat reference as if she were a mannequin.\n"
        )

    # Regras de geração de modelo — aplicáveis em qualquer modo
    if has_images:
        block += (
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
    else:
        # Text-only: diretivas ABSTRATAS apenas.
        # Cenário, pose, lighting e framing já são entregues via MODE_PRESETS.
        # Aqui entregamos APENAS o Name Blending + eixo de presença para persona.
        dt = diversity_target or {}
        profile_hint = dt.get("profile_hint", "")
        presence_energy = dt.get("presence_energy", "")
        presence_tone = dt.get("presence_tone", "")

        block += (
            "TEXT-ONLY FASHION MODE:\n"
            f"  1. Model persona anchor: {profile_hint}\n"
            f"     Presence: {presence_energy}, {presence_tone}.\n"
            "  2. Keep the garment as the hero. Model presence is secondary and must feel believable.\n"
            "  3. Scenario, pose, lighting, and framing directions come from MODE_PRESETS above. Do not duplicate.\n"
            "  4. In base_prompt, open with the model presence before the garment, using your own creative voice.\n"
            "</DIVERSITY_TARGET>"
        )
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
    if not has_images or not structural_contract.get("enabled"):
        return None

    cues = ", ".join(structural_contract.get("must_keep", []) or []) or "none"
    return (
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


def _build_look_contract_block(look_contract: Optional[dict[str, Any]]) -> Optional[str]:
    contract = look_contract or {}
    if not contract or float(contract.get("confidence", 0) or 0) <= 0.5:
        return None

    forbidden = ", ".join(contract.get("forbidden_bottoms") or []) or "none"
    keywords = ", ".join(contract.get("style_keywords") or []) or ""
    return (
        "<LOOK_CONTRACT>\n"
        "[Styling constraints — outfit must be coherent with the target garment]\n"
        f"- bottom_style: {contract.get('bottom_style', '')}\n"
        f"- bottom_color: {contract.get('bottom_color', '')}\n"
        f"- color_family: {contract.get('color_family', '')}\n"
        f"- season: {contract.get('season', '')}\n"
        f"- occasion: {contract.get('occasion', '')}\n"
        f"- forbidden_bottoms: {forbidden}\n"
        f"- accessories: {contract.get('accessories', '')}\n"
        f"- style_keywords: {keywords}\n"
        "Use bottom_style and bottom_color as the primary guide for the "
        "model's lower garment. NEVER suggest a forbidden_bottom type.\n"
        "</LOOK_CONTRACT>"
    )


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
    scenario: str,
    pose: str,
    diversity_target: Optional[dict[str, Any]],
    guided_enabled: bool,
    guided_brief: Optional[dict[str, Any]],
    guided_set_mode: str,
    guided_set_detection: dict[str, Any],
    structural_contract: dict[str, Any],
    look_contract: Optional[dict[str, Any]],
    grounding_research: str,
    grounding_effective: bool,
    grounding_context_hint: Optional[str],
    grounding_mode: str,
    mode_defaults_text: Optional[str],
    reference_knowledge: str,
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

    mode_presets_block = _build_mode_presets_block(mode_defaults_text)
    if mode_presets_block:
        blocks.append(mode_presets_block)

    if pool_context.strip():
        blocks.append(f"<POOL_CONTEXT>\n{pool_context}\n</POOL_CONTEXT>")

    blocks.append(_build_output_parameters_block(aspect_ratio=aspect_ratio, resolution=resolution))
    blocks.append(
        _build_diversity_target_block(
            profile=profile,
            scenario=scenario,
            pose=pose,
            diversity_target=diversity_target,
            has_images=has_images,
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

    structural_block = _build_structural_contract_block(
        has_images=has_images,
        structural_contract=structural_contract,
    )
    if structural_block:
        blocks.append(structural_block)

    look_block = _build_look_contract_block(look_contract)
    if look_block:
        blocks.append(look_block)

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

    blocks.append(reference_knowledge)
    blocks.append("Return ONLY valid JSON matching the schema. No markdown, no explanation.")
    return "\n\n".join(blocks)
