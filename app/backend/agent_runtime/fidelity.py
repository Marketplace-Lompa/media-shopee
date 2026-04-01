"""
Camada de fidelidade para fluxo com imagem de referência.

Responsabilidade ÚNICA: proteger a identidade visual da peça durante
a geração com input de imagem. Monta locks, guards, reference policy,
pattern lock, neckline guard e texture fidelity.

NÃO decide direção criativa (cena, pose, câmera, iluminação).
Essa direção vem do mode ativo via modes.py.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from agent_runtime.editing.contracts import PreparedEditPrompt
from agent_runtime.structural import get_set_member_labels, get_set_member_keys


# ── Constantes de fidelidade ─────────────────────────────────────────────

_LENGTH_PHRASES = {
    "cropped": "cropped length",
    "waist": "waist length",
    "hip": "hip length",
    "upper_thigh": "upper-thigh length",
    "mid_thigh": "mid-thigh length",
    "knee_plus": "knee-or-below length",
}

_REFERENCE_USAGE_RULES_BASE = [
    "Use all references only as garment evidence for shape, fabric, stitch, color behavior, and garment geometry.",
    "Never transfer identity from references; create a fully new Brazilian woman around the locked garment.",
]

_REFERENCE_USAGE_RULES_STRICT = [
    "Treat every visible person in references as an anonymous mannequin for garment transfer only.",
    "Any resemblance to reference people is a hard failure.",
]

_REFERENCE_USAGE_RULES_HIGH_GUARD = [
    "Keep identity transfer from references at zero; deliberately separate the new face, hair silhouette, body, and age impression from any visible person in the references.",
]

_REAL_FRONT_CLOSURE_SUBTYPES = {
    "standard_cardigan",
    "jacket",
    "blazer",
    "vest",
    "bolero",
    "blouse",
    "dress",
}


# ── Guardrails de modo ───────────────────────────────────────────────────

def _guardrail_text(value: Any) -> str:
    return str(value or "").strip()


def _build_mode_guardrail_clauses(mode_guardrails: Optional[dict[str, Any]]) -> list[str]:
    if not isinstance(mode_guardrails, dict):
        return []

    clauses: list[str] = []
    guardrail_profile = _guardrail_text(mode_guardrails.get("guardrail_profile"))
    if guardrail_profile:
        clauses.append(f"Mode guardrail profile: {guardrail_profile}.")

    mode_hard_rules = [
        _guardrail_text(item)
        for item in (mode_guardrails.get("mode_hard_rules") or [])
        if _guardrail_text(item)
    ]
    if mode_hard_rules:
        clauses.append("Mode hard rules: " + "; ".join(mode_hard_rules) + ".")

    scene = mode_guardrails.get("scene_constraints") or {}
    if isinstance(scene, dict):
        backdrop = _guardrail_text(scene.get("backdrop")) or _guardrail_text(scene.get("backdrop_mode"))
        if backdrop:
            clauses.append(f"Scene constraint: {backdrop}.")
        scene_role = _guardrail_text(scene.get("role"))
        if scene_role:
            clauses.append(f"Scene role: {scene_role}.")
        rigidity = _guardrail_text(scene.get("rigidity")) or _guardrail_text(scene.get("context_rigidity"))
        if rigidity:
            clauses.append(f"Scene rigidity: {rigidity}.")
        environment_competition = _guardrail_text(scene.get("environment_competition"))
        if environment_competition:
            clauses.append(f"Environment competition tolerance: {environment_competition}.")
        if scene.get("needs_piece_first_readability"):
            clauses.append("Prioritize piece-first readability over environmental storytelling.")
        if _guardrail_text(scene.get("detail_preservation")):
            clauses.append(f"Scene detail preservation: {_guardrail_text(scene.get('detail_preservation'))}.")

    pose = mode_guardrails.get("pose_constraints") or {}
    if isinstance(pose, dict):
        pose_bits: list[str] = []
        movement_budget = _guardrail_text(pose.get("movement_budget"))
        if movement_budget:
            pose_bits.append(f"movement budget {movement_budget}")
        frontality_bias = _guardrail_text(pose.get("frontality_bias"))
        if frontality_bias:
            pose_bits.append(f"frontality bias {frontality_bias}")
        occlusion_tolerance = _guardrail_text(pose.get("occlusion_tolerance"))
        if occlusion_tolerance:
            pose_bits.append(f"occlusion tolerance {occlusion_tolerance}")
        allowed_variation = _guardrail_text(pose.get("allowed_variation"))
        if allowed_variation:
            pose_bits.append(f"allowed variation {allowed_variation}")
        gesture_range = _guardrail_text(pose.get("gesture_range"))
        if gesture_range:
            pose_bits.append(f"gesture range {gesture_range}")
        silhouette_priority = _guardrail_text(pose.get("silhouette_priority"))
        if silhouette_priority:
            pose_bits.append(f"silhouette priority {silhouette_priority}")
        if pose_bits:
            clauses.append("Pose guardrails: " + ", ".join(pose_bits) + ".")
        if movement_budget == "low" and frontality_bias == "front":
            clauses.append("Keep the stance quiet, frontal, and catalog-stable with minimal motion.")

    capture = mode_guardrails.get("capture_constraints") or {}
    if isinstance(capture, dict):
        capture_bits = [
            _guardrail_text(capture.get("framing_profile")) or _guardrail_text(capture.get("framing_priority")),
            _guardrail_text(capture.get("camera_type")) or _guardrail_text(capture.get("camera_language")),
            _guardrail_text(capture.get("capture_geometry")) or _guardrail_text(capture.get("angle_bias")),
            _guardrail_text(capture.get("lighting_profile")) or _guardrail_text(capture.get("depth_context")),
        ]
        capture_bits = [item for item in capture_bits if item]
        if capture_bits:
            clauses.append("Capture guardrails: " + ", ".join(capture_bits) + ".")

    identity_guard = mode_guardrails.get("identity_guard") or {}
    if isinstance(identity_guard, dict):
        identity_bits: list[str] = []
        scope = _guardrail_text(identity_guard.get("identity_scope"))
        if scope:
            identity_bits.append(f"scope {scope}")
        reference_use = _guardrail_text(identity_guard.get("reference_use"))
        if reference_use:
            identity_bits.append(f"reference use {reference_use}")
        if identity_guard.get("transfer_allowed") is False:
            identity_bits.append("no identity transfer")
        if identity_guard.get("strict") is True:
            identity_bits.append("strict identity lock")
        if identity_bits:
            clauses.append("Identity guard: " + ", ".join(identity_bits) + ".")

    return clauses


def _clean_text(text: Any, limit: int = 500) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "").strip())
    return cleaned[:limit].rstrip(",. ") if cleaned else ""


def _ensure_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "").strip())
    if not cleaned:
        return ""
    if cleaned.endswith((".", "!", "?")):
        return cleaned
    return f"{cleaned}."


def _strip_mode_soul_prefix(text: str) -> str:
    return re.sub(r"^\s*[-\u2014]+\s*SOUL:\s*", "", str(text or "").strip(), flags=re.I)


def _compact_reference_scene_guard(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "").strip())
    if not cleaned:
        return ""
    return (
        "Do not copy the reference background, location signature, or original spatial composition; "
        "invent a new setting that serves the garment and the active mode better."
    )


def _extract_mode_specific_block(soul_text: str) -> str:
    """Extrai o bloco MODE-SPECIFIC de uma soul string.

    As souls (pose, capture, scene) contêm seções de meta-instrução para agentes
    (INVENTION METHOD, CRITICAL RULES, COMPLETENESS CHECK) que não devem ir ao Nano.
    Esta helper extrai apenas o bloco MODE-SPECIFIC X LOGIC, que contém a prosa
    operacional concreta adequada para uso direto no prompt de geração.

    Retorna string vazia se o bloco não existir (ex: catalog_clean em scene_soul).
    """
    if not soul_text:
        return ""
    # Encontra o início do bloco MODE-SPECIFIC
    match = re.search(r"MODE-SPECIFIC[^\n]*LOGIC:\n(.+?)(?=\n+[A-Z][A-Z _]+:|\Z)", soul_text, re.S)
    if not match:
        return ""
    # Limpa indentação e normaliza espaço em branco
    raw = match.group(1)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return " ".join(lines)


def build_reference_edit_art_direction(
    *,
    mode_id: str,
    creative_brief: Optional[dict[str, Any]],
) -> str:
    """Sintetiza a direção criativa do stage 2 em prosa fluida para Nano.

    Fallback usado quando o agente não retorna soul criativo.
    Injeta conteúdo operacional real das souls ao invés de frases genéricas.

    Camadas injetadas:
    - mode_identity_soul: todas as diretivas do mode (não só a linha SOUL)
    - pose_soul: bloco MODE-SPECIFIC (linguagem corporal concreta do mode)
    - capture_soul: bloco MODE-SPECIFIC (comportamento de câmera concreto do mode)
    - scene_soul: bloco MODE-SPECIFIC (lógica de cenário concreta do mode)
    """
    from agent_runtime.mode_identity_soul import get_mode_identity_soul
    from agent_runtime.scene_soul import get_scene_soul
    from agent_runtime.pose_soul import get_pose_soul
    from agent_runtime.capture_soul import get_capture_soul

    sentences: list[str] = []

    # ── 1. Mode identity: todas as diretivas (soul + emotional temp + light + etc.) ──
    mode_soul_lines = get_mode_identity_soul(mode_id)
    if mode_soul_lines:
        # Primeira linha: remover prefixo "— SOUL:" e usar como abertura
        first = _strip_mode_soul_prefix(mode_soul_lines[0])
        if first:
            sentences.append(_ensure_sentence(first))
        # Demais linhas: remover marcador de lista e injetar como prosa
        for line in mode_soul_lines[1:]:
            cleaned = re.sub(r"^[\-\u2014]+\s*", "", line.strip())
            if cleaned:
                sentences.append(_ensure_sentence(cleaned))

    # ── 2. Modelo: nova mulher brasileira (âncora de identidade) ─────────────
    sentences.append(
        "Create a completely new Brazilian woman — "
        "invent her age, face geometry, skin tone, hair, frame, and expression "
        "from scratch, choosing what feels naturally right for this garment and this mode."
    )

    # ── 3. Pose: bloco MODE-SPECIFIC operacional ─────────────────────────────
    pose_soul = get_pose_soul(mode_id=mode_id, has_images=True)
    pose_block = _extract_mode_specific_block(pose_soul)
    if pose_block:
        sentences.append(pose_block)
    elif pose_soul:
        # fallback mínimo se o bloco não parsear
        sentences.append(
            "Invent fresh body language that makes the garment readable and serves the mode."
        )

    # ── 4. Captura: bloco MODE-SPECIFIC operacional ───────────────────────────
    capture_soul = get_capture_soul(mode_id=mode_id, has_images=True)
    capture_block = _extract_mode_specific_block(capture_soul)
    if capture_block:
        sentences.append(capture_block)
    elif capture_soul:
        sentences.append(
            "Choose a fresh camera distance and angle that keeps the garment legible "
            "and the scene coherent. Never use 0° pure frontal — always include body rotation."
        )

    # ── 5. Cenário: bloco MODE-SPECIFIC operacional (não se catalog_clean) ────
    if mode_id != "catalog_clean":
        scene_soul = get_scene_soul(mode_id=mode_id, has_images=True)
        scene_block = _extract_mode_specific_block(scene_soul)
        if scene_block:
            sentences.append(scene_block)
        elif scene_soul:
            sentences.append(
                "Invent a new Brazilian setting through visible material, light, and spatial evidence."
            )
        reference_scene_guard = _compact_reference_scene_guard(scene_soul)
        if reference_scene_guard:
            sentences.append(reference_scene_guard)
    else:
        # catalog_clean: backdrop neutro determinístico — não inventar cenário
        sentences.append(
            "Background: neutral studio surface only — default to ice-white or light-grey backdrop "
            "(cool, clean, high-contrast paper sweep with soft, even light). "
            "Use warm-cream or off-white ONLY when the garment itself is very light "
            "(white, ivory, off-white, cream) to avoid garment-backdrop fusion. "
            "For all other garment colors, ice-white or light-grey is mandatory. "
            "No real environments, no architectural elements, no outdoor settings, "
            "no recognizable locations enter the frame. "
            "The backdrop is invisible by design — it exists only to create contrast with the garment."
        )

    return " ".join(s for s in sentences if s.strip())





def _build_reference_usage_clauses(mode_guardrails: Optional[dict[str, Any]]) -> list[str]:
    if not isinstance(mode_guardrails, dict):
        return []

    identity_guard = mode_guardrails.get("identity_guard") or {}
    guardrail_profile = _guardrail_text(mode_guardrails.get("guardrail_profile"))
    clauses: list[str] = []

    forbid_pose_clone = bool(identity_guard.get("forbid_pose_clone"))
    forbid_composition_clone = bool(identity_guard.get("forbid_composition_clone"))

    if forbid_pose_clone:
        clauses.append(
            "Do not copy the dominant gesture from references unless the user brief explicitly requires it."
        )
    if forbid_composition_clone:
        clauses.append(
            "Avoid repeating the exact composition or framing from references when a fresh composition can preserve garment readability."
        )
    elif guardrail_profile == "strict_catalog":
        clauses.append(
            "You may keep a commercially familiar catalog composition when it best preserves garment readability, but do not clone the reference person's exact body language."
        )

    return clauses


# ── Guards de estrutura ──────────────────────────────────────────────────

def _collect_lock_clauses(structural_contract: Optional[dict[str, Any]]) -> list[str]:
    """Guards prioritários (máx 5) — confia na imagem para o resto.

    Antes havia 14+ locks granulares que diluíam o sinal visual.
    Agora: 1 anchor de identidade + até 4 guards de drift comprovado.
    """
    contract = structural_contract or {}
    locks = [
        "preserve the exact garment identity, shape, and texture visible in the references",
    ]

    length = str(contract.get("garment_length", "") or "").strip().lower()
    if length in _LENGTH_PHRASES:
        locks.append(f"maintain {_LENGTH_PHRASES[length]} as shown in the reference")

    opening_lock = _render_front_opening_lock(contract)
    if opening_lock:
        locks.append(opening_lock)

    # Filtra must_keep: apenas atributos estruturais entram no lock textual.
    # Atributos de superfície/padrão (texture, relief, diamond, geometric...)
    # NÃO são injetados como texto — o Nano os extrai diretamente das imagens.
    # Injetar esses termos causa espalhamento de textura para zonas lisas.
    _SURFACE_TERMS = (
        "texture", "textura", "relief", "relevo", "diamond", "losango",
        "geometric", "geométric", "pattern", "padrão", "jacquard", "argyle",
        "cable", "waffle", "pointelle", "intarsia", "chevron", "stripe",
        "listras", "xadrez", "plaid", "grid", "check",
    )
    must_keep_raw = [str(item).strip() for item in (contract.get("must_keep", []) or []) if str(item).strip()]
    must_keep_structural = [
        item for item in must_keep_raw
        if not any(term in item.lower() for term in _SURFACE_TERMS)
    ]
    if must_keep_structural:
        locks.append("preserve: " + ", ".join(must_keep_structural[:2]))

    return locks


def _render_front_opening_lock(contract: Optional[dict[str, Any]]) -> str:
    payload = contract or {}
    front = str(payload.get("front_opening", "") or "").strip().lower()
    subtype = str(payload.get("garment_subtype", "") or "").strip().lower()
    continuity = str(payload.get("opening_continuity", "") or "").strip().lower()

    if front == "open":
        if continuity == "continuous":
            return "keep the front visibly open as one continuous uninterrupted edge"
        return "keep the front visibly open"

    if front == "partial":
        return "preserve the partial front opening exactly as shown"

    if front != "closed":
        return ""

    if subtype in _REAL_FRONT_CLOSURE_SUBTYPES and continuity != "continuous":
        return "keep the front closure fully closed as shown"

    return "keep the front fully closed with no visible opening or placket break"


def _closed_neckline_guard(structural_contract: Optional[dict[str, Any]]) -> str:
    contract = structural_contract or {}
    front = str(contract.get("front_opening", "") or "").strip().lower()
    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    if front != "closed":
        return ""
    if subtype in {"pullover", "t_shirt", "blouse", "dress", "jacket", "blazer", "standard_cardigan", "other", "unknown"}:
        return (
            "Do not introduce any visible undershirt, layered neckline, or contrasting inner collar; "
            "the garment neckline itself must remain the only visible neckline element."
        )
    return ""


def _specialized_structure_guards(
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]] = None,
) -> list[str]:
    contract = structural_contract or {}
    set_info = set_detection or {}

    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    lock_mode = str(set_info.get("set_lock_mode", "off") or "off").strip().lower()
    must_include_labels = get_set_member_labels(
        set_info,
        include_policies={"must_include"},
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

    guards: list[str] = []
    if subtype == "ruana_wrap":
        guards.append("keep this as an open ruana-style wrap and not a closed poncho, sweater, or pullover body")
    if sleeve == "cape_like":
        guards.append(
            "do not invent separate sewn sleeves, long vertical sleeve slits, or tailored armholes; arm coverage must come from the continuous draped side panel"
        )
    if lock_mode != "off" and must_include_labels:
        guards.append(
            "preserve coordinated set members as distinct product pieces with matching textile DNA, not as unrelated styling or fused garment parts"
        )
    if "scarf" in must_include_keys:
        guards.append("preserve the matching scarf as part of the same coordinated knit set with the same stripe order, yarn tones, and stitch texture")
    return guards


def build_structure_guard_clauses(
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]] = None,
) -> list[str]:
    """Compila todas as cláusulas de proteção estrutural da peça."""
    clauses = _collect_lock_clauses(structural_contract)
    clauses.extend(_specialized_structure_guards(structural_contract, set_detection=set_detection))
    return list(dict.fromkeys([clause.strip() for clause in clauses if clause and clause.strip()]))


# ── Hint estrutural ──────────────────────────────────────────────────────

def build_structural_hint(structural_contract: Optional[dict[str, Any]]) -> Optional[str]:
    """Frase curta em prosa descrevendo a identidade da peça.

    Produz linguagem natural ('a draped ruana wrap with three-quarter sleeves at hip length')
    para orientar o Nano Banana sem jargão técnico.
    """
    contract = structural_contract or {}
    if not contract.get("enabled"):
        return None

    subtype = str(contract.get("garment_subtype", "") or "").strip().lower().replace("_", " ")
    volume = str(contract.get("silhouette_volume", "") or "").strip().lower()
    sleeve_len = str(contract.get("sleeve_length", "") or "").strip().lower().replace("_", "-")
    length = str(contract.get("garment_length", "") or "").strip().lower()

    if not subtype or subtype == "unknown":
        return None

    phrase = "a "
    if volume and volume != "unknown":
        phrase += f"{volume} "
    phrase += subtype
    if sleeve_len and sleeve_len not in ("unknown", "sleeveless"):
        phrase += f" with {sleeve_len} sleeves"
    elif sleeve_len == "sleeveless":
        phrase += ", sleeveless"
    if length in _LENGTH_PHRASES:
        phrase += f" at {_LENGTH_PHRASES[length]}"

    return phrase


# ── Reference policy ─────────────────────────────────────────────────────

def build_reference_policy(
    *,
    strength: str = "standard",
    extra_rules: Optional[list[str]] = None,
    mode_guardrails: Optional[dict[str, Any]] = None,
) -> str:
    """Monta a política de uso de referências por nível de proteção."""
    dynamic_rules = list(extra_rules or [])
    dynamic_rules.extend(_build_reference_usage_clauses(mode_guardrails))
    base_rules = list(_REFERENCE_USAGE_RULES_BASE)
    level = str(strength).strip().lower()
    if level in {"strict", "high"}:
        base_rules.extend(_REFERENCE_USAGE_RULES_STRICT)
    if level == "high":
        base_rules.extend(_REFERENCE_USAGE_RULES_HIGH_GUARD)
    combined = list(dict.fromkeys(
        [r.strip() for r in (base_rules + dynamic_rules) if r and r.strip()]
    ))
    return " ".join(combined)


# ── Pattern lock ─────────────────────────────────────────────────────────

_PATTERN_KEYWORDS = (
    "stripe", "chevron", "diagonal", "radiating", "concentric",
    "plaid", "grid", "check", "argyle", "listras", "listra", "xadrez",
    "geometric", "diamond", "relief", "ribbed", "textured", "jacquard",
    "intarsia", "pointelle", "cable", "waffle",
)


def build_pattern_lock(image_analysis: Optional[str]) -> str:
    """Retorna sempre string vazia — padrão visual é guiado 100% pelas imagens.

    Histórico de decisão:
    - v1: injetava ia_trunc com 'geometric diamond relief' → Nano espalhava
      textura para mangas lisas (texto sem ancoragem de zona).
    - v2: 'zone-by-zone exactly as shown' → instrução abstrata piorou; Nano
      aplicou textura em toda a peça sem referência de zona.
    - v3 (atual): sem texto de padrão. Nano extrai distribuição de zona
      diretamente das imagens de referência. Qualquer instrução textual de
      padrão conflita com a percepção visual do modelo.

    A detecção de padrão (_PATTERN_KEYWORDS) ainda vive no arquivo para uso
    em outras decisões (ex: grounding). Não remove a função.
    """
    return ""


# ── Decisão de grounding visual ──────────────────────────────────────────

_COMPLEX_SUBTYPES = {
    "ruana_wrap", "poncho", "cape", "kimono", "bolero",
    "cape_like", "draped_wrap",
}

_GROUNDING_PATTERN_KEYWORDS = (
    "chevron", "diagonal", "radiating", "concentric", "crochet",
    "crochê", "handmade", "artisanal", "boucle", "bouclê",
    "patchwork", "jacquard", "intarsia", "fair isle",
    # Padrões de malha com relevo — ativam image grounding para fidelidade de zona
    "geometric", "diamond", "relief", "cable", "waffle", "pointelle",
)


def should_use_image_grounding(
    structural_contract: Optional[dict[str, Any]],
    image_analysis: Optional[str],
    gate_policy: Optional[dict[str, Any]] = None,
    n_uploaded: int = 0,
) -> bool:
    """Decide se ativa Google Image Search grounding para esta geração.

    Critérios de ativação (qualquer um satisfeito):
    - Garment é subtipo incomum/draped (ruana, poncho, cape, kimono)
    - Gate detectou garment complexo ou drape architecture especial
    - Image analysis descreve padrão específico que o modelo pode errar
    - Poucas referências do usuário (< 3) para garment de alta fidelidade
    """
    contract = structural_contract or {}
    ia = str(image_analysis or "").lower()
    gate = gate_policy or {}

    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    confidence = float(contract.get("confidence", 1.0) or 1.0)
    gate_reasons = [str(r).lower() for r in (gate.get("reasons") or [])]

    reasons: list[str] = []

    if subtype in _COMPLEX_SUBTYPES:
        reasons.append(f"complex_subtype:{subtype}")

    if any(r in gate_reasons for r in (
        "complex_garment", "draped_subtype", "cape_like", "sleeve_architecture"
    )):
        reasons.append("gate_complex_garment")

    if ia and any(kw in ia for kw in _GROUNDING_PATTERN_KEYWORDS):
        reasons.append("distinctive_pattern_in_analysis")

    if n_uploaded < 3 and subtype in _COMPLEX_SUBTYPES:
        reasons.append("few_refs_complex_garment")

    if confidence < 0.7:
        reasons.append(f"low_triage_confidence:{confidence:.2f}")

    active = bool(reasons)
    if active:
        print(f"[IMAGE_GROUNDING] ✅ ativado — razões: {reasons}")
    else:
        print(f"[IMAGE_GROUNDING] ⏭ skipped — garment:{subtype}, refs:{n_uploaded}, confidence:{confidence:.2f}")

    return active


# ── Detecção de material ─────────────────────────────────────────────────

def derive_garment_material_text(
    structural_contract: Optional[dict[str, Any]],
    image_analysis: Optional[str],
) -> str:
    """Infere texto de material da peça para instruções de textura no prompt."""
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
    if any(token in text for token in ("viscose",)):
        return "viscose fabric"
    return "garment fabric"


def build_classifier_summary(
    structural_contract: Optional[dict[str, Any]],
    selector_stats: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Classifica peça em categoria para gates de fidelidade."""
    subtype = str((structural_contract or {}).get("garment_subtype", "") or "").strip().lower()
    complex_garment = bool((selector_stats or {}).get("complex_garment"))
    if subtype in {"ruana_wrap", "poncho", "cape", "kimono", "jacket"}:
        category = "outerwear"
    elif complex_garment:
        category = "complex_knit"
    else:
        category = "general"
    return {"garment_category": category}


# ── Compilador de prompt de edição (fidelity shell + soul) ───────────────

def compile_edit_prompt(
    structural_contract: Optional[dict[str, Any]],
    *,
    art_direction_soul: str,
    set_detection: Optional[dict[str, Any]] = None,
    angle_directive: str = "",
    fidelity_mode: str = "balanceada",
) -> str:
    """Compila o prompt final de edição: guardrail mínimo + soul criativo.

    Arquitetura Soul-First:
      - Guardrail mínimo (~50w): reference policy consolidada + locks em 1 frase.
      - Soul criativo (~80-120w): art_direction_soul domina o prompt.
      - Fidelidade granular (pattern, texture, stitch) é delegada ao corredor
        de repair/recovery no generation_flow, NÃO ao prompt de geração.
    """
    # 1. Garment identity locks (1 frase condensada)
    locks = build_structure_guard_clauses(
        structural_contract, set_detection=set_detection,
    )

    # 2. Neckline guard (resolve bug real — mantido se necessário)
    neckline_guard = _closed_neckline_guard(structural_contract)

    # 3. Compile: guardrail mínimo + soul dominante
    sentences = [
        str(angle_directive or "").strip(),
        # Reference policy consolidada (substitui 5 repetições anteriores)
        (
            "References are garment evidence only — "
            "create a completely new Brazilian woman, pose, and setting around the locked garment."
        ),
        # Locks condensados em 1 frase
        "Keep the garment exactly as shown: " + ", ".join(locks) + ".",
        # Neckline guard (se aplicável)
        neckline_guard,
        # SOUL — bloco criativo completo, domina o prompt
        art_direction_soul,
    ]

    # 4. Estrita: prioridade absoluta à fidelidade (internalizado)
    if str(fidelity_mode).strip().lower() == "estrita":
        sentences.append(
            "Prioritize exact garment fidelity over scene creativity. "
            "Do not alter garment silhouette, length, sleeve architecture, hem behavior, or stripe placement."
        )

    return " ".join(s.strip() for s in sentences if s and s.strip())


def prepare_garment_replacement_prompt(
    *,
    structural_contract: dict[str, Any],
    garment_hint: str,
    image_analysis: str,
    set_detection: Optional[dict[str, Any]] = None,
    mode_id: str,
    source_prompt_context: str,
) -> PreparedEditPrompt:
    """Cria prompt estruturado para substituir apenas a peça na base gerada."""
    structural_hint = build_structural_hint(structural_contract)
    structure_guards = build_structure_guard_clauses(
        structural_contract,
        set_detection=set_detection,
    )
    set_info = set_detection or {}
    required_labels = get_set_member_labels(
        set_info,
        include_policies={"must_include"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )
    garment_material = derive_garment_material_text(structural_contract, image_analysis)
    pattern_lock = build_pattern_lock(image_analysis)
    garment_label = _clean_text(garment_hint, limit=120) or "the hero garment"
    structural_sentence = structural_hint or garment_label
    # Âncora de preservação única — fica no topo, antes de qualquer constraint de peça
    preserve_clause = (
        "Preserve exactly: the base image person (face, identity, skin tone, hair, body proportions), "
        "pose, expression, camera angle, framing, environment, background, and lighting. "
        "Preserve all visible non-target outfit items and accessories exactly as shown — "
        "trousers, skirts, footwear, belts, jewelry, bags, scarves, and any styling layers outside the replacement target. "
        "Do not redesign the scene or the model."
    )

    replacement_goal_parts = [
        "Replace only the placeholder garment in the base image with the real uploaded product.",
        f"Use the uploaded references only as garment evidence for {garment_label}.",
        f"Match the real product's structural identity: {structural_sentence}.",
    ]
    if structure_guards:
        replacement_goal_parts.append(
            "Preserve these product constraints during replacement: " + "; ".join(structure_guards) + "."
        )
    if pattern_lock:
        replacement_goal_parts.append(pattern_lock)
    if required_labels:
        replacement_goal_parts.append(
            "Treat these coordinated members as part of the same replacement set: "
            + ", ".join(required_labels)
            + "."
        )

    reference_item_description_parts = [
        f"Hero product: {garment_label}.",
        f"Structural identity: {structural_sentence}.",
        f"Material family: {garment_material}.",
    ]
    if image_analysis:
        reference_item_description_parts.append(
            "Reference garment analysis: " + _clean_text(image_analysis, limit=400) + "."
        )
        # Qualificador crítico: a análise textual é âncora estrutural (silhueta,
        # comprimento, abertura). Para distribuição de textura e padrão por zona,
        # as imagens são a única fonte verdade — o texto não define quais zonas
        # têm relevo e quais são lisas.
        reference_item_description_parts.append(
            "Surface texture zone distribution: follow the reference images exclusively. "
            "Do not apply any texture, relief, or pattern to areas that appear smooth or plain in the reference photos. "
            "Text analysis is structural guidance only — images override text for texture zone allocation."
        )
    if structure_guards:
        reference_item_description_parts.append(
            "Locked product constraints: " + "; ".join(structure_guards) + "."
        )
    if required_labels:
        reference_item_description_parts.append(
            "Required coordinated members: " + ", ".join(required_labels) + "."
        )
    reference_item_description_parts.append(
        "Never transfer any person identity from the references. Extract only the garment and set-member properties."
    )

    structured_goal = " ".join(part.strip() for part in replacement_goal_parts if part and part.strip())
    reference_item_description = " ".join(
        part.strip() for part in reference_item_description_parts if part and part.strip()
    )
    display_prompt = structured_goal.strip()

    return PreparedEditPrompt(
        flow_mode="garment_replacement",
        edit_type="garment_replacement",
        display_prompt=display_prompt,
        model_prompt=display_prompt,
        change_summary_ptbr=(
            f"Substituir a peça placeholder pela peça real analisada em mode `{mode_id}`."
        ),
        confidence=0.88,
        structured_edit_goal=structured_goal,
        structured_preserve_clause=preserve_clause,
        reference_item_description=reference_item_description,
        include_source_prompt_context=bool(str(source_prompt_context or "").strip()),
        include_reference_item_description=True,
        use_structured_shell=True,
    )


# ── Prompt de fidelidade para stage 1 (base fiel) ────────────────────────

def build_stage1_prompt(
    structural_contract: Optional[dict[str, Any]],
    structural_hint: Optional[str],
    *,
    set_detection: Optional[dict[str, Any]] = None,
    art_direction_soul: str = "",
    fidelity_mode: str = "balanceada",
    angle_directive: str = "",
    use_image_grounding: bool = False,
) -> str:
    """Prompt para stage 1 (base fiel da peça) — arquitetura soul-first.

    Stage 1 prioriza reprodução fiel da peça com identidade humana nova.
    Guardrails são condensados; soul criativo domina quando disponível.
    """
    structure_guards = build_structure_guard_clauses(
        structural_contract, set_detection=set_detection,
    )
    set_info = set_detection or {}
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
            "Preserve coordinated set members as distinct product pieces. "
            + ("Keep the matching coordinated scarf. " if keep_matching_scarf else "")
        )
        if included_labels else
        "Do not add accessories not present in the references. "
    )

    creative_direction = str(art_direction_soul or "").strip()

    # Montagem: identity guard consolidado + locks + soul dominante
    parts = [
        # 1. Reference policy consolidada (1 frase, substitui identity_guard verboso)
        (
            "References are garment evidence only — "
            "completely ignore the face, skin, hair, body, and age of any person in the references. "
            "Create a clearly different adult Brazilian woman for this photo."
        ),
    ]
    if angle_directive:
        parts.append(angle_directive)

    # 2. Garment locks condensados
    if structural_hint:
        parts.append(f"Garment identity: {structural_hint}.")
    if structure_guards:
        parts.append("Keep the garment exactly as shown: " + "; ".join(structure_guards) + ".")

    # 3. Composição — garment é o objeto fixo
    parts.append(
        "Build the woman, pose, and environment around the locked garment. "
        "Never reshape the garment to solve composition."
    )

    # 4. SOUL — direção criativa (bloco dominante)
    if creative_direction:
        parts.append(creative_direction)
    else:
        parts.append(
            "Invent a new Brazilian woman and a commercially believable setting around the locked garment."
        )

    # 5. Estrita: prioridade absoluta à fidelidade
    if str(fidelity_mode).strip().lower() == "estrita":
        parts.append("Prioritize exact garment fidelity over editorial variation.")

    # 6. Accessory guard (resolve bug real de acessórios fantasma)
    parts.append(
        "Keep the garment as the visual hero. "
        + accessory_guard
        + "Build styling independent from the reference person's look."
    )

    if use_image_grounding:
        parts.insert(0,
            "Use image search to reference real examples of this garment type for accurate silhouette and texture."
        )
    return " ".join(parts)
