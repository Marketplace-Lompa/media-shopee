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
    diversity_target: Optional[dict[str, Any]],
    has_images: bool,
) -> str:
    dt = diversity_target or {}
    profile_hint = dt.get("profile_hint", "") or profile
    presence_energy = dt.get("presence_energy", "")
    presence_tone = dt.get("presence_tone", "")
    casting_state = dt.get("casting_state") or {}
    scene_state = dt.get("scene_state") or {}
    capture_state = dt.get("capture_state") or {}
    pose_state = dt.get("pose_state") or {}
    styling_state = dt.get("styling_state") or {}
    coordination_state = dt.get("coordination_state") or {}
    operational_profile = dt.get("operational_profile") or {}

    def _budget_label(value: float) -> str:
        if value < 0.3:
            return "restrained"
        if value < 0.55:
            return "moderate"
        return "open"

    def _surface_label(value: int) -> str:
        if value <= 1:
            return "minimal"
        if value == 2:
            return "light"
        if value == 3:
            return "present"
        return "strong"

    block = "<DIVERSITY_TARGET>\n"
    if dt.get("profile_id"):
        block += f"Model profile ID: {dt['profile_id']}.\n"

    # ── Regras anti-cópia (só quando há imagens de referência) ────
    if has_images:
        block += (
            "GARMENT-ONLY REFERENCE MODE:\n"
            "  - Reference images = garment source ONLY (color, fabric, structure, pattern).\n"
            "  - Discard the reference model completely. Do not copy face, skin, hair, body, or pose.\n"
        )

    # ── Diretivas de persona (compartilhadas) ─────────────────────
    presence_clause = ""
    if presence_energy or presence_tone:
        presence_clause = f" Presence: {presence_energy}, {presence_tone}."
    block += (
        f"Model persona anchor: {profile_hint}.{presence_clause}\n"
        "Keep the model distinctly Brazilian in a believable, non-stereotyped way.\n"
        "Use the persona anchor consistently in the final prompt instead of dropping it.\n"
        + (
            "Invent a new Brazilian persona that complements the garment, but keep physical characterization broad and non-dominant.\n"
            "Do not lock the model into a highly specific phenotype unless the brief explicitly asks for it.\n"
            if has_images
            else "Invent unique physical characteristics (skin tone, hair, age, build) that complement the garment.\n"
        )
        + "Keep the garment as the hero. Model presence is secondary.\n"
        "Scenario, framing, lighting, and pose come from MODE_PRESETS. Follow those directions.\n"
        "Inside those directions, invent a fresh specific solution instead of repeating a generic safe default.\n"
        "Never mention preset labels or metatextual terms like capture geometry, scenario family, or lighting profile in the final prompt.\n"
        "Write one canonical final prompt directly usable by the image generator.\n"
    )
    if operational_profile:
        weights = operational_profile.get("engine_weights") or {}
        surface_budget = operational_profile.get("surface_budget") or {}
        emphasis_pairs = sorted(
            [
                ("casting", float(weights.get("casting", 0.0) or 0.0)),
                ("scene", float(weights.get("scene", 0.0) or 0.0)),
                ("capture", float(weights.get("capture", 0.0) or 0.0)),
                ("styling", float(weights.get("styling", 0.0) or 0.0)),
                ("pose", float(weights.get("pose", 0.0) or 0.0)),
            ],
            key=lambda item: item[1],
            reverse=True,
        )
        emphasis = ", ".join(name for name, _ in emphasis_pairs[:2])
        block += (
            "OPERATIONAL DIRECTION (resolved behavioral effect, do not copy as labels):\n"
            f"  - invention budget: {_budget_label(float(operational_profile.get('invention_budget', 0.5) or 0.5))}\n"
            f"  - primary emphasis: {emphasis}\n"
            f"  - subject surface budget: {_surface_label(int(surface_budget.get('subject', 0) or 0))}\n"
            f"  - scene surface budget: {_surface_label(int(surface_budget.get('scene', 0) or 0))}\n"
            f"  - capture surface budget: {_surface_label(int(surface_budget.get('capture', 0) or 0))}\n"
            f"  - styling surface budget: {_surface_label(int(surface_budget.get('styling', 0) or 0))}\n"
            f"  - pose surface budget: {_surface_label(int(surface_budget.get('pose', 0) or 0))}\n"
            f"  - guardrail behavior: {operational_profile.get('guardrail_profile', '')}\n"
            "Let this shape how much each layer appears in the final prompt, without naming modes or preset mechanics.\n"
        )
    if casting_state:
        recent_avoid = ", ".join(casting_state.get("recent_avoid") or []) or "none"
        if has_images:
            block += (
                "CASTING LATENT STATE (reference mode: use as abstract persona guidance, not as literal phenotype casting):\n"
                f"  - age energy: {casting_state.get('age', '')}\n"
                f"  - polish level: {casting_state.get('makeup', '')}\n"
                f"  - expression energy: {casting_state.get('expression', '')}\n"
                f"  - presence: {casting_state.get('presence', '')}\n"
                f"  - variation rule: {casting_state.get('difference_instruction', '')}\n"
                f"  - recent avoid: {recent_avoid}\n"
                "If you surface physical cues, keep them broad and secondary.\n"
                "Avoid locking both exact skin tone and exact hair silhouette into a highly specific phenotype unless the brief explicitly asks for it.\n"
                "Final prompt surface minimum: apparent age or overall presence is enough; do not over-specify phenotype in garment-reference mode.\n"
            )
        else:
            block += (
                "CASTING LATENT STATE (internal creative coordinates, do not copy as a checklist):\n"
                f"  - age energy: {casting_state.get('age', '')}\n"
                f"  - face impression: {casting_state.get('face_structure', '')}\n"
                f"  - skin direction: {casting_state.get('skin', '')}\n"
                f"  - hair language: {casting_state.get('hair', '')}\n"
                f"  - polish level: {casting_state.get('makeup', '')}\n"
                f"  - expression energy: {casting_state.get('expression', '')}\n"
                f"  - presence: {casting_state.get('presence', '')}\n"
                f"  - variation rule: {casting_state.get('difference_instruction', '')}\n"
                f"  - recent avoid: {recent_avoid}\n"
                "Final prompt surface minimum: explicitly render apparent age, one concrete face impression, and one clear hair description.\n"
            )
    if scene_state:
        block += (
            "SCENE LATENT STATE (creative seed — use as inspiration, NOT as a rigid constraint):\n"
            f"  - world family: {scene_state.get('world_family', '')}\n"
            f"  - microcontext: {scene_state.get('microcontext', '')}\n"
            f"  - emotional register: {scene_state.get('emotional_register', '')}\n"
            f"  - material language: {scene_state.get('material_language', '')}\n"
            f"  - background density: {scene_state.get('background_density', '')}\n"
            f"  - Brazil anchor: {scene_state.get('brazil_anchor', '')}\n"
            "These scene coordinates are starting inspiration, not boundaries.\n"
            "Freely invent an authentic Brazilian scene — indoor or outdoor — that fits\n"
            "the active visual mode's tone. Surprise with variety: tropical gardens,\n"
            "pousada verandas, padarias, rooftops, parks, hotel lobbies, feiras,\n"
            "residential courtyards, coastal boardwalks, cultural spaces.\n"
            "Avoid defaulting to the same type of scene across consecutive generations.\n"
        )
    if capture_state:
        block += (
            "CAPTURE LATENT STATE (internal image-direction coordinates, do not copy as a checklist):\n"
            f"  - framing intent: {capture_state.get('framing_intent', '')}\n"
            f"  - camera family: {capture_state.get('camera_family', '')}\n"
            f"  - geometry intent: {capture_state.get('geometry_intent', '')}\n"
            f"  - capture feel: {capture_state.get('capture_feel', '')}\n"
            f"  - lens language: {capture_state.get('lens_language', '')}\n"
            f"  - subject separation: {capture_state.get('subject_separation', '')}\n"
            f"  - body relation: {capture_state.get('body_relation', '')}\n"
            f"  - angle logic: {capture_state.get('angle_logic', '')}\n"
            f"  - garment priority: {capture_state.get('garment_priority', '')}\n"
            "Use this to choose how the camera should look at the garment, based on silhouette, proportion, and selling points, without exposing preset mechanics.\n"
        )
    if pose_state:
        block += (
            "POSE LATENT STATE (internal body-direction coordinates, do not copy as a checklist):\n"
            f"  - pose family: {pose_state.get('pose_family', '')}\n"
            f"  - stance logic: {pose_state.get('stance_logic', '')}\n"
            f"  - weight shift: {pose_state.get('weight_shift', '')}\n"
            f"  - arm logic: {pose_state.get('arm_logic', '')}\n"
            f"  - torso orientation: {pose_state.get('torso_orientation', '')}\n"
            f"  - head direction: {pose_state.get('head_direction', '')}\n"
            f"  - gesture intention: {pose_state.get('gesture_intention', '')}\n"
            f"  - garment interaction: {pose_state.get('garment_interaction', '')}\n"
            "Final prompt surface minimum: describe a specific stance or gesture, not only generic wording like stable pose or composed stance.\n"
        )
    if styling_state:
        footwear_required = "yes" if styling_state.get("footwear_required") else "no"
        block += (
            "STYLING LATENT STATE (internal fashion-styling coordinates, do not copy as a checklist):\n"
            f"  - completion level: {styling_state.get('completion_level', '')}\n"
            f"  - footwear strategy: {styling_state.get('footwear_strategy', '')}\n"
            f"  - accessory restraint: {styling_state.get('accessory_restraint', '')}\n"
            f"  - look finish: {styling_state.get('look_finish', '')}\n"
            f"  - styling interference: {styling_state.get('styling_interference', '')}\n"
            f"  - garment balance: {styling_state.get('hero_balance', '')}\n"
            f"  - footwear required: {footwear_required}\n"
            "Use this to complete the look with fashion judgment, only as much as needed, while keeping the garment visually primary.\n"
        )
    if coordination_state:
        block += (
            "ART DIRECTION COORDINATION STATE (internal synthesis coordinates, do not copy as a checklist):\n"
            f"  - master intent: {coordination_state.get('master_intent', '')}\n"
            f"  - presence/world fusion: {coordination_state.get('presence_world_fusion', '')}\n"
            f"  - camera/body fusion: {coordination_state.get('camera_body_fusion', '')}\n"
            f"  - styling/world balance: {coordination_state.get('styling_world_balance', '')}\n"
            f"  - garment priority rule: {coordination_state.get('garment_priority_rule', '')}\n"
            f"  - visual tension: {coordination_state.get('visual_tension', '')}\n"
            f"  - synthesis rule: {coordination_state.get('synthesis_rule', '')}\n"
            "Use this to make casting, scene, capture, pose, and styling feel like one authored image direction rather than separate good decisions.\n"
            "Weave at least one natural relational phrase that links body direction, setting, and capture (for example through language like while, keeping, so that, or work together), instead of describing each layer in isolation.\n"
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

    if reference_knowledge.strip():
        blocks.append(reference_knowledge)
    blocks.append("Return ONLY valid JSON matching the schema. No markdown, no explanation.")
    return "\n\n".join(blocks)
