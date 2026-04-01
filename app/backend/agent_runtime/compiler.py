import re
from typing import Any, Optional

from agent_runtime.constants import (
    _RESIDUAL_NEG_RE,
)
from agent_runtime.structural import (
    _neg_to_pos,
    _prune_structural_conflicts,
    _resolve_structural_conflicts,
    _compress_structural_facts,
    get_set_member_labels,
)

_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z\"\']|$)')
_CASTING_KEY_VALUE_RE = re.compile(r"(?im)^\s*[-•]\s*([A-Za-z0-9_\- ]+):\s*(.+?)\s*$")


def _count_words(text: str) -> int:
    return len(text.split()) if text.strip() else 0


def _extract_tagged_block(text: str, start_tag: str, end_tag: str) -> tuple[str, str]:
    """Extrai um bloco tagado e retorna (bloco, texto_sem_bloco)."""
    source = text or ""
    start = source.find(start_tag)
    if start < 0:
        return "", source
    end = source.find(end_tag, start + len(start_tag))
    if end < 0:
        return "", source

    end = end + len(end_tag)
    extracted = source[start:end].strip()
    before = source[:start].strip()
    after = source[end:].strip()
    if before and after:
        return extracted, f"{before}\n\n{after}"
    return extracted, before or after


def _extract_casting_checklist_text(casting_block: str) -> str:
    if not casting_block:
        return ""
    checklist_items: list[str] = []
    for match in _CASTING_KEY_VALUE_RE.finditer(casting_block):
        key = (match.group(1) or "").strip().lower()
        value = (match.group(2) or "").strip().rstrip(".")
        if not value:
            continue
        if key == "casting_checklist" or key == "casting checklist":
            for part in re.split(r"[,;]+", value):
                part = part.strip()
                if part and part.lower() not in {"none", "unknown", "undefined", "to be defined"}:
                    checklist_items.append(part)
            continue
        if key in {
            "age_logic",
            "face_geometry",
            "skin_logic",
            "hair_logic",
            "body_logic",
            "presence_logic",
            "expression_logic",
            "beauty_logic",
        }:
            if value.lower() not in {"none", "unknown", "undefined", "to be defined"}:
                checklist_items.append(value)
    if not checklist_items:
        return ""
    reduced = ", ".join(part for part in checklist_items[:5])
    return f"CASTING CHECKLIST: {reduced}"


def _format_casting_clause_for_nano(casting_clause: str) -> str:
    """Converte checklist técnico em cláusula narrativa limpa para o gerador de imagem."""

    if not casting_clause:
        return ""
    cleaned = re.sub(r"(?i)\bcasting checklist:\s*", "", casting_clause).strip()
    if not cleaned:
        return ""
    cleaned_low = cleaned.lower()
    if re.match(r"^(?:a |an |the |she )", cleaned_low):
        return cleaned
    age_match = re.match(r"(?i)^(?:in her\s+)?((?:late|mid|early|mid-to-late)\s+\d{2}s)\b(?:,\s*(.*))?$", cleaned)
    if age_match:
        age = (age_match.group(1) or "").strip()
        rest = (age_match.group(2) or "").strip().strip(",")
        if rest:
            return f"a woman in her {age} with {rest}"
        return f"a woman in her {age}"
    if re.match(r"^\d", cleaned_low):
        return f"a woman in her {cleaned}"
    return f"a woman with {cleaned}"


def _truncate_by_sentence(text: str, max_words: int) -> tuple[str, bool]:
    """
    Trunca *text* ao limite de *max_words* palavras cortando apenas em
    fronteiras de sentença completa.

    Retorna (texto_truncado, foi_truncado).
    """
    if _count_words(text) <= max_words:
        return text, False

    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    
    # Fallback: sem marcadores e excede budget → corta por palavra forçadamente
    if len(sentences) <= 1:
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]), True
        return text, False

    kept: list[str] = []
    total = 0
    for sent in sentences:
        w = _count_words(sent)
        if total + w <= max_words:
            kept.append(sent)
            total += w
        else:
            break

    if not kept:
        # Nenhuma sentença completa coube.
        first = sentences[0]
        w_first = first.split()
        if len(w_first) > max_words:
            return " ".join(w_first[:max_words]), True
        return first, True

    return " ".join(kept), True


def _frame_occupancy_clause(aspect_ratio: str, shot_type: str) -> str:
    """Evita o artefato de "portrait inset" dentro de canvas quadrado:
    o modelo precisa ocupar um quadro nativo, sem faixas bluradas laterais.
    """
    if aspect_ratio == "1:1":
        if shot_type == "wide":
            return (
                "full-bleed catalog composition with the environment extending naturally to every edge of the frame, "
                "balanced negative space around the model, and no inset portrait treatment"
            )
        return (
            "full-bleed composition with natural background continuity to every edge of the frame, "
            "native framing around the subject, and no blurred side filler panels"
        )
    return (
        "native edge-to-edge composition with background continuity across the full frame"
    )


def _compile_prompt_v2(
    prompt: str,
    has_images: bool,
    has_prompt: bool,
    contract: Optional[dict],
    guided_brief: Optional[dict],
    guided_enabled: bool,
    guided_set_detection: Optional[dict],
    grounding_mode: str,
    pipeline_mode: str,
    word_budget: int = 220,
    aspect_ratio: str = "1:1",
    pose_hint: str = "",
    profile_hint: str = "",
    scenario_hint: str = "",
    garment_narrative: str = "",
    lighting_hint: str = "",
    shot_type: str = "medium",
    framing_profile: str = "",
    pose_energy: str = "",
    casting_state: Optional[dict[str, Any]] = None,
    casting_profile: str = "",
    mode_id: str = "",
) -> tuple[str, dict]:
    """
    Prompt Compiler V2: converte todas as restrições de lock em frases fotográficas
    positivas e monta o prompt final com controle de orçamento por palavras.

    Prioridades (menor = maior prioridade):
      P1 — fidelidade estrutural (contrato geométrico)
      P2 — textura / material
      P3 — composição comercial (modelo, olhar, cena)
      P4 — styling secundário (guided)

    Retorna: (prompt_final, debug_dict)
    """
    # (text, priority, source_tag)
    clauses: list[tuple[str, int, str]] = []
    discarded: list[tuple[str, str]] = []

    # No fluxo com imagem de referência para modes criativos, o prompt precisa
    # permanecer fluido e autorado pelo agente. A fidelidade exata da roupa é
    # reforçada depois pelo corredor de transferência/repair, então evitamos
    # despejar cláusulas mecânicas na superfície do prompt-base.
    suppress_reference_mechanics = (
        has_images and pipeline_mode == "reference_mode" and mode_id != "catalog_clean"
    )

    guided_pose_style = ""
    if guided_enabled and guided_brief:
        guided_pose_style = str((guided_brief.get("pose") or {}).get("style", "")).strip().lower()
    guided_pose_creative = guided_pose_style == "criativa"

    # ── Strip labels from base prompt (defensive) ──────────────────
    base = prompt.strip() if prompt else ""

    casting_block, base = _extract_tagged_block(base, "<CASTING_DIRECTION>", "</CASTING_DIRECTION>")
    casting_clause = _extract_casting_checklist_text(casting_block)

    if not casting_clause and casting_state and pipeline_mode not in {"text_mode", "reference_mode"}:
        state_parts = [
            str((casting_state or {}).get("age", "") or "").strip(),
            str((casting_state or {}).get("face_structure", "") or "").strip(),
            str((casting_state or {}).get("hair", "") or "").strip(),
            str((casting_state or {}).get("presence", "") or "").strip(),
            str((casting_state or {}).get("expression", "") or "").strip(),
            str((casting_state or {}).get("beauty_read", "") or "").strip(),
            str((casting_state or {}).get("body", "") or "").strip(),
        ]
        normalized_parts = [
            part for part in state_parts
            if part and part.lower() not in {"none", "unknown", "undefined", "to be defined"}
        ]
        if normalized_parts:
            casting_clause = "CASTING CHECKLIST: " + ", ".join(normalized_parts[:5])

    if casting_clause:
        casting_clause = _format_casting_clause_for_nano(casting_clause)
        casting_clause = casting_clause[:320]
        clauses.append((casting_clause, 0, "casting_surface"))

    base = base.strip()
    base = _neg_to_pos(base)
    base = _prune_structural_conflicts(base, contract)
    base = _resolve_structural_conflicts(base, contract)

    # ── P1: Fidelidade estrutural (geometria observável compactada via MT-B) ──
    if (
        has_images
        and contract
        and contract.get("enabled")
        and not suppress_reference_mechanics
    ):
        struct_clauses, struct_discarded = _compress_structural_facts(contract)
        clauses.extend(struct_clauses)
        discarded.extend(struct_discarded)

    # ── P1: Âncora de fidelidade de garment (reference_mode) ─────────
    # A referência é a ÚNICA fonte de verdade para a roupa.
    # Modelo e cenário são livres — apenas a roupa deve ser fiel.
    # catalog_clean partilha o mesmo fluxo de fidelidade de peça: a diferença
    # do mode é apenas o backdrop neutro, não o tratamento da roupa.
    if has_images and pipeline_mode == "reference_mode" and not suppress_reference_mechanics:
        clauses.append((
            "the uploaded reference image is the sole garment truth source — "
            "preserve exact color, fabric, pattern scale, construction, and silhouette",
            1, "garment_fidelity_anchor"
        ))

    # ── P2: Anti-cópia de modelo ──────────────────────────────────
    # REMOVIDO (soul-first): consolidado na reference policy única do
    # compile_edit_prompt() em fidelity.py. Evita repetição no prompt.

    # ── P1: Atypical silhouette / Complex matching (grounding full) ──
    if grounding_mode == "full" and not suppress_reference_mechanics:
        clauses.append((
            "preserve garment geometry: opening behavior, sleeve architecture, hem shape, garment length",
            1, "grounding_atypical"
        ))

    # ── P2: Hints de composição (cenário, iluminação) ──
    # No Prompt-First, o agente já resolve isso via MODE_PRESETS.
    # Aqui apenas injetamos como fallback leve se disponíveis.
    if scenario_hint:
        clauses.append((scenario_hint, 3, "diversity_scenario"))
    if lighting_hint:
        clauses.append((lighting_hint, 4, "lighting_hint"))

    # ── P3: Perfil do modelo (garantia de fenótipo) ──────────────────
    # Detecta se Gemini JÁ ecoou nosso diversity profile no base_prompt.
    # "features blend" é assinatura única do _sample_diversity_target —
    # se aparece no base, Gemini obedeceu o DIVERSITY_TARGET e não precisa duplicar.
    _PROFILE_ECHO_SIGNALS = ("features blend", "blend reminiscent", "blend of")
    _profile_already_in_base = any(sig in base.lower() for sig in _PROFILE_ECHO_SIGNALS)

    # Sinais de fenótipo genérico (usuário ou Gemini espelhando referência).
    # Se presentes e não forem echo do nosso profile, Gemini descreveu a modelo da ref.
    _PHENOTYPE_SIGNALS = (
        "baiana", "paulistana", "gaúcha", "carioca", "nordestina",
        "ford models", "vogue brasil", "farm rio", "lança perfume",
        "peach fuzz",
        # legacy signals
        "afro", "parda", "sulista",
    )
    _phenotype_in_base = any(sig in base.lower() for sig in _PHENOTYPE_SIGNALS)

    # Lógica:
    # - Se Gemini já ecoou nosso profile ("features blend" no base) → skip (evita duplicação)
    # - Se fenótipo ausente → injetar como guardrail de diversidade
    if (
        profile_hint
        and pipeline_mode != "text_mode"
        and not _profile_already_in_base
        and not (has_images and mode_id == "catalog_clean")
    ):
        if not _phenotype_in_base:
            clauses.append((profile_hint, 3, "model_profile"))



    # ── P2: Fidelidade de textura ────────────────────────────────────
    # REMOVIDO (soul-first): delegado ao corredor de repair/recovery.
    # O prompt de geração foca na direção criativa, não em specs de textura.

    # ── P3: Composição comercial (guardrails apenas) ──────────────────
    # Direção criativa de model_presence, gaze, scene_composition e pose_body
    # são responsabilidade do agent (via souls/briefings), não do compiler.
    # O compiler só mantém guardrails estruturais aqui.

    effective_shot = shot_type
    if effective_shot == "auto":
        if framing_profile == "full_body":
            effective_shot = "wide"
        elif framing_profile == "detail_crop":
            effective_shot = "close-up"
        else:
            effective_shot = "medium"

    if has_images and not suppress_reference_mechanics:
        clauses.append((_frame_occupancy_clause(aspect_ratio, effective_shot), 3, "frame_occupancy"))
    elif pipeline_mode == "text_mode":
        # No text_mode, toda direção criativa (model, gaze, scene, pose) já entra
        # via souls/briefings + estados latentes. O compiler não adiciona nada.
        pass

    # ── P3: Pose de referência do grounding ──────────────────────────
    if pose_hint:
        clauses.append((pose_hint, 3, "grounding_pose"))

    # ── P4: Guided (styling secundário) ─────────────────────────────
    if guided_enabled and guided_brief:
        garment_g = guided_brief.get("garment", {}) or {}
        scene_g = guided_brief.get("scene", {}) or {}
        pose_g = guided_brief.get("pose", {}) or {}
        fidelity_mode = str(guided_brief.get("fidelity_mode", "balanceada")).strip().lower()

        set_mode = str(garment_g.get("set_mode", "unica")).strip().lower()
        scene_type = str(scene_g.get("type", "")).strip().lower()
        pose_style = str(pose_g.get("style", "")).strip().lower()

        if set_mode == "conjunto":
            det = guided_set_detection or {}
            roles = get_set_member_labels(
                det,
                include_policies={"must_include", "optional"},
                member_classes={"garment", "coordinated_accessory"},
            ) or list(det.get("detected_garment_roles", []) or [])
            # Só usa roles se forem descritivos (>1 token cada) — evita injetar
            # rótulos genéricos como "top, bottom, outerwear" que levam o Imagen
            # a inventar peças que não existem na referência.
            _GENERIC_ROLES = {"top", "bottom", "outerwear", "inner", "outer", "base", "layer"}
            descriptive_roles = [r for r in roles if r.strip().lower() not in _GENERIC_ROLES and len(r.split()) > 1]
            if descriptive_roles:
                clauses.append((
                    f"coordinated pieces: {', '.join(descriptive_roles[:4])}",
                    4, "guided_set",
                ))
            else:
                clauses.append(("coordinated pieces from reference", 4, "guided_set"))

        if scene_type == "interno":
            clauses.append(("indoor", 4, "guided_scene"))
        elif scene_type == "externo":
            clauses.append(("outdoor", 4, "guided_scene"))

        if pose_style == "tradicional":
            clauses.append(("stable catalog stance", 4, "guided_pose"))
        elif pose_style == "criativa":
            clauses.append(("creative pose, full garment visibility", 4, "guided_pose"))

        # Guided fidelity suave
        if has_images and (set_mode == "conjunto" or fidelity_mode == "estrita"):
            clauses.append(("retain reference pockets and closures, exactly as reference", 3, "guided_fidelity"))

    # ── Budget v2: P1-reserve → base truncation → fill P2-P4 ────────
    #
    # Garantia:  cláusulas P1 (fidelidade estrutural) SEMPRE cabem.
    # Estratégia:
    #   1. Mede palavras de P1 para reservar espaço.
    #   2. Trunca base por sentença completa se necessário.
    #   3. Adiciona P1 (garantido).
    #   4. Preenche P2-P4 com o espaço restante.

    p0_clauses   = [(t, s) for t, p, s in clauses if p == 0]
    p1_clauses   = [(t, s) for t, p, s in clauses if p == 1]
    p2p_clauses  = [(t, p, s) for t, p, s in clauses if p > 1]

    # P0 e P1 têm prioridade máxima: processado primeiro contra o budget completo.
    # Estratégia de condensação: se todos os P1 cabem → inclui na ordem original.
    # Se não cabem → ordena por tamanho crescente (maximiza número de cláusulas
    # incluídas) e descarta apenas as que não couberem por último.
    # Nota: não é garantia absoluta em budgets extremamente apertados (< ~30w),
    # mas em operação normal (budget=220, P1 total ≈ 50-80w) todas entram.
    used: list[tuple[str, str]] = []
    p0_total_words = sum(_count_words(t) for t, _ in p0_clauses)
    used.extend(p0_clauses)
    current_budget = max(0, word_budget - p0_total_words)

    p1_total_words = sum(_count_words(t) for t, _ in p1_clauses)
    if p1_total_words <= current_budget:
        # Caso comum: todos P1 cabem — mantém ordem de geração
        used.extend(p1_clauses)
        current_budget -= p1_total_words
    else:
        # Condensação: prefere cláusulas menores para maximizar cobertura de P1
        for text, source in sorted(p1_clauses, key=lambda x: _count_words(x[0])):
            clause_words = _count_words(text)
            if current_budget >= clause_words:
                used.append((text, source))
                current_budget -= clause_words
            else:
                discarded.append((text, f"budget(P1_condensed, {current_budget}w left, need {clause_words}w)"))

    # Reserva total para P2-P4 (composição comercial).
    # Sem limite de reserva, o base trunca para garantir que P2-P4 entrem
    # se a string base for puro "estilo/comercial excedente".
    p2p_total_words = sum(_count_words(t) for t, _, _ in p2p_clauses)
    effective_reserve = p2p_total_words

    base_allowed = max(0, current_budget - effective_reserve)

    # Com imagens: prosa descritiva do Gemini sobre a peça duplica os P1 structural clauses.
    # MT-A: dynamic budget — 28w quando temos profile/scenario hints (diversidade precisa
    # de espaço para modelo+cenário no base); 12w default para manter frame directive apenas.
    _has_diversity_context = bool(profile_hint or scenario_hint or suppress_reference_mechanics)
    _base_cap = 50 if _has_diversity_context else 12
    if pipeline_mode == "text_mode":
        _base_cap = max(_base_cap, 180)
    if has_images and mode_id == "catalog_clean":
        _base_cap = max(_base_cap, 110)
    elif suppress_reference_mechanics:
        _base_cap = max(_base_cap, 140)
    if has_images and base_allowed > _base_cap:
        base_allowed = _base_cap

    if base_allowed > 0:
        base, base_was_truncated = _truncate_by_sentence(base, base_allowed)
    else:
        base, base_was_truncated = ("", True)

    if base_was_truncated:
        discarded.append(
            ("[base narrative]",
             f"base_truncation(base exceeded {base_allowed}w after P1+P2P_reserve)")
        )

    base_words = _count_words(base)
    # Remaining real após base + P1 + P0 (não limitado pelo base_allowed)
    remaining = word_budget - p0_total_words - p1_total_words - base_words

    # P2-P4: preenche por prioridade com o que couber
    for text, priority, source in sorted(p2p_clauses, key=lambda x: x[1]):
        clause_words = _count_words(text)
        if remaining >= clause_words:
            used.append((text, source))
            remaining -= clause_words
        else:
            discarded.append((text, f"budget(P{priority}, {remaining}w left, need {clause_words}w)"))

    # Log de runtime para tuning rápido
    if discarded:
        for txt, reason in discarded:
            preview = txt[:55] + "…" if len(txt) > 55 else txt
            print(f"[COMPILER] ⚠️  dropped [{reason}]: {preview}")

    additions = " ".join(t for t, _ in used)
    assembled = f"{base} {additions}".strip() if additions else base
    # MT5: run BOTH conflict passes on the fully assembled prompt (not just on base).
    # _prune removes contract-contradicting terms reintroduced by P1-P4 clauses;
    # _resolve then handles the higher-level semantic pair conflicts.
    assembled = _prune_structural_conflicts(assembled, contract)
    assembled = _resolve_structural_conflicts(assembled, contract)

    # ── Normalização final: passa _neg_to_pos no prompt completo ─────
    # Captura negativos que o modelo gerou e que não estavam no base isolado.
    final = _neg_to_pos(assembled)

    # Telemetria: negativos residuais não mapeados (para tuning da tabela)
    residual_matches = _RESIDUAL_NEG_RE.findall(final)
    residual_negatives = list(dict.fromkeys(m.lower() for m in residual_matches))

    _CREATIVE_SOURCES = {"quality_gaze", "quality_scene", "diversity_scenario",
                         "model_profile", "lighting_hint"}
    creative_clauses = [{"text": t, "source": s} for t, s in used if s in _CREATIVE_SOURCES]

    debug = {
        "used_clauses":        [{"text": t, "source": s} for t, s in used],
        "discarded_clauses":   [{"text": t, "reason": r} for t, r in discarded],
        "creative_clauses":    creative_clauses,
        "base_words":          base_words,
        "base_truncated":      base_was_truncated,
        "total_words":         _count_words(final),
        "word_budget":         word_budget,
        "guided_pose_creative": guided_pose_creative,
        "residual_negatives":  residual_negatives,
    }

    return final, debug


def _test_compiler_budget() -> None:
    """
    Smoke-test de borda para _truncate_by_sentence e _compile_prompt_v2.
    Execute via:  python -c "from agent_runtime.compiler import _test_compiler_budget; _test_compiler_budget()"
    """
    # ── Caso 1: base longa → truncamento por sentença, sem prompt quebrado ──
    long_base = (
        "RAW photo, full-body wide shot. "
        "Model mid-stride in bright downtown setting. "
        "Garment drapes naturally over shoulders. "
        "Batwing volume visible from front and side. "
        "Background softly defocused and catalog-clean. "
        "Natural skin tone, warm confident expression. "
        "Sony A7III, 85mm f/1.8, natural light. "
        "Subtle grain, visible fabric texture, natural wear creases. "
        "Additional filler sentence number nine here for testing. "
        "And one more sentence to push beyond two hundred words total padding text."
    )
    truncated, was_cut = _truncate_by_sentence(long_base, 40)
    assert was_cut, "Expected truncation for long base"
    assert _count_words(truncated) <= 40, f"Truncated base exceeds limit: {_count_words(truncated)}"
    assert not truncated.endswith(("the", "a", "an", "and", "in", "of")), \
        f"Truncated mid-word: '{truncated[-30:]}'"
    print(f"[TEST 1] ✅ truncation: {_count_words(long_base)}w → {_count_words(truncated)}w")

    # ── Caso 2: sentença única maior que limite → corta forçadamente ──
    single = "This is one single long run-on sentence with many many words to exceed the limit set here."
    result, cut = _truncate_by_sentence(single, 5)
    assert cut, "Single sentence exceeding budget should be cut"
    assert _count_words(result) <= 5, "Single sentence should be truncated to word limits"
    print(f"[TEST 2] ✅ single-sentence forced cut: {_count_words(single)}w → {_count_words(result)}w")

    # ── Caso 3: P1 garantido mesmo com base longa e budget apertado ──
    contract = {
        "enabled": True, "confidence": 0.75,
        "garment_subtype": "standard_cardigan",
        "sleeve_type": "set-in", "sleeve_length": "long",
        "front_opening": "open", "hem_shape": "straight",
        "garment_length": "hip", "silhouette_volume": "regular",
        "must_keep": [],
    }
    result3, debug3 = _compile_prompt_v2(
        prompt=long_base,
        has_images=True,
        has_prompt=False,
        contract=contract,
        guided_brief=None,
        guided_enabled=False,
        guided_set_detection=None,
        grounding_mode="off",
        pipeline_mode="image_mode",
        word_budget=100,
    )
    assert _count_words(result3) <= 100, f"Budget exceeded: {_count_words(result3)}"
    p1_sources = {c["source"] for c in debug3["used_clauses"]}
    assert "garment_length" in p1_sources, "P1 garment_length must always be included"
    print(f"[TEST 3] ✅ P1 guaranteed ({len(p1_sources)} P1 sources), total={debug3['total_words']}w")

    # ── Caso 4: budget sem restrições → sem descarte ──
    short_base = "RAW photo, medium shot. Model wearing open cardigan, hip length."
    result4, debug4 = _compile_prompt_v2(
        prompt=short_base,
        has_images=False,
        has_prompt=True,
        contract=None,
        guided_brief=None,
        guided_enabled=False,
        guided_set_detection=None,
        grounding_mode="off",
        pipeline_mode="text_mode",
        word_budget=220,
    )
    assert _count_words(result4) <= 220
    print(f"[TEST 4] ✅ no budget pressure: {debug4['total_words']}w, discarded={len(debug4['discarded_clauses'])}")

    print("\n[COMPILER TEST] ✅ All budget edge cases passed.")
