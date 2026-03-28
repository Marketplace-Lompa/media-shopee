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


def build_reference_edit_art_direction(
    *,
    mode_id: str,
    creative_brief: Optional[dict[str, Any]],
) -> str:
    """Sintetiza a direção criativa do stage 2 em prosa fluida para Nano.

    Todas as camadas criativas vêm das souls — engine states foram removidos.
    """
    from agent_runtime.mode_identity_soul import get_mode_soul_statement
    from agent_runtime.scene_soul import get_scene_soul
    from agent_runtime.pose_soul import get_pose_soul
    from agent_runtime.capture_soul import get_capture_soul

    brief = creative_brief or {}
    semantic_briefs = brief.get("semantic_briefs") or {}
    sentences: list[str] = []

    mode_soul = _strip_mode_soul_prefix(get_mode_soul_statement(mode_id))
    if mode_soul:
        sentences.append(_ensure_sentence(mode_soul))

    sentences.append(
        "Create a completely new Brazilian woman whose age, face geometry, skin, hair, frame, expression, and visible makeup feel naturally right for this garment and this mode."
    )

    # Scene: semantic brief > soul
    scene_brief = str(semantic_briefs.get("scene_brief", "") or "").strip()
    if scene_brief:
        sentences.append(_ensure_sentence(scene_brief))
    elif mode_id != "catalog_clean":
        scene_soul = get_scene_soul(mode_id=mode_id, has_images=True)
        if scene_soul:
            sentences.append(
                "Invent a new Brazilian setting aligned with the active mode through visible material, light, and spatial evidence."
            )
        reference_scene_guard = _compact_reference_scene_guard(scene_soul)
        if reference_scene_guard:
            sentences.append(reference_scene_guard)

    # Pose: semantic brief > soul
    pose_brief = str(semantic_briefs.get("pose_brief", "") or "").strip()
    if pose_brief:
        sentences.append(_ensure_sentence(pose_brief))
    else:
        pose_soul = get_pose_soul(mode_id=mode_id, has_images=True)
        if pose_soul:
            sentences.append(
                "Invent fresh body language aligned with the active mode, keeping the garment readable and not copying the reference pose."
            )

    # Camera: semantic brief > soul
    angle_brief = str(semantic_briefs.get("angle_brief", "") or "").strip()
    camera_brief = str(semantic_briefs.get("camera_brief", "") or "").strip()
    if angle_brief:
        sentences.append(_ensure_sentence(angle_brief))
    if camera_brief:
        sentences.append(_ensure_sentence(camera_brief))
    else:
        capture_soul = get_capture_soul(mode_id=mode_id, has_images=True)
        if capture_soul:
            sentences.append(
                "Choose a fresh camera relationship aligned with the active mode, keeping the garment legible and the scene coherent."
            )

    return " ".join(sentence for sentence in sentences if sentence.strip())





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

    front = str(contract.get("front_opening", "") or "").strip().lower()
    if front == "open":
        locks.append("keep the front visibly open")
    elif front == "closed":
        locks.append("keep the front closure intact")

    must_keep = [str(item).strip() for item in (contract.get("must_keep", []) or []) if str(item).strip()]
    if must_keep:
        locks.append("preserve: " + ", ".join(must_keep[:2]))

    return locks


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
)


def build_pattern_lock(image_analysis: Optional[str]) -> str:
    """Gera lock de padrão visual se detectado na análise da imagem."""
    ia_text = str(image_analysis or "").strip()
    if not ia_text or not any(w in ia_text.lower() for w in _PATTERN_KEYWORDS):
        return ""
    _max = 400
    _chunk = ia_text[:_max]
    _dot = _chunk.rfind(".")
    ia_trunc = _chunk[:_dot + 1].strip() if _dot > 100 else _chunk.rstrip(",. ")
    return (
        f"CRITICAL — preserve the exact surface pattern geometry from the references: {ia_trunc}. "
        "Do not reinterpret stripe direction, pattern angle, or pattern scale. "
        "If the pattern appears diagonal or chevron in the references, "
        "it must remain diagonal or chevron in the output."
    )


# ── Decisão de grounding visual ──────────────────────────────────────────

_COMPLEX_SUBTYPES = {
    "ruana_wrap", "poncho", "cape", "kimono", "bolero",
    "cape_like", "draped_wrap",
}

_GROUNDING_PATTERN_KEYWORDS = (
    "chevron", "diagonal", "radiating", "concentric", "crochet",
    "crochê", "handmade", "artisanal", "boucle", "bouclê",
    "patchwork", "jacquard", "intarsia", "fair isle",
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
    garment_material: str = "garment fabric",
    garment_color: str = "the garment colors and yarn tones",
    reference_guard_strength: str = "standard",
    reference_usage_rules: Optional[list[str]] = None,
    mode_guardrails: Optional[dict[str, Any]] = None,
    image_analysis: Optional[str] = None,
    angle_directive: str = "",
) -> str:
    """Compila o prompt final de edição: shell de fidelidade + soul criativo.

    Arquitetura:
      - Camadas determinísticas: locks, guards, reference policy, pattern lock,
        neckline guard, texture fidelity.
      - Camada criativa: art_direction_soul é injetado como bloco único.
        O LLM lê e INVENTA cena, pose, câmera, iluminação e styling.
    """
    # 1. Garment identity locks
    locks = build_structure_guard_clauses(
        structural_contract, set_detection=set_detection,
    )

    # 2. Pattern lock
    pattern_lock = build_pattern_lock(image_analysis)

    # 3. Reference policy
    reference_policy = build_reference_policy(
        strength=reference_guard_strength,
        extra_rules=reference_usage_rules,
        mode_guardrails=mode_guardrails,
    )

    # 4. Neckline guard
    neckline_guard = _closed_neckline_guard(structural_contract)

    # 5. Texture fidelity
    texture_clause = (
        f"Render the garment with macro-accurate {garment_material}, "
        f"correct fabric weight, consistent stitch definition, "
        f"and realistic light absorption across {garment_color}."
    )

    # 6. Compile: deterministic shell + creative soul
    sentences = [
        str(angle_directive or "").strip(),
        (
            "Replace the placeholder person in the base image completely. "
            "Do not preserve any face, skin tone, hair, body type, or age impression from the base image person or from the references."
        ),
        "Keep the garment exactly the same: " + ", ".join(locks) + ".",
        pattern_lock,
        reference_policy,
        (
            "Treat the garment as the locked object and redesign only the woman, the pose, the camera relation, and the environment around it."
        ),

        # Creative direction (SOUL — from mode, LLM invents freely)
        art_direction_soul,
        neckline_guard,
        texture_clause,
        (
            "Keep the result highly photorealistic with believable human skin and realistic body proportions."
        ),
    ]

    return " ".join(s.strip() for s in sentences if s and s.strip())


# ── Prompt de fidelidade para stage 1 (base fiel) ────────────────────────

def build_stage1_prompt(
    structural_contract: Optional[dict[str, Any]],
    structural_hint: Optional[str],
    *,
    set_detection: Optional[dict[str, Any]] = None,
    art_direction_soul: str = "",
    fidelity_mode: str = "balanceada",
    mode: str = "natural",
    angle_directive: str = "",
    use_image_grounding: bool = False,
    image_analysis: Optional[str] = None,
) -> str:
    """Prompt curto e reproduzível para stage 1: base fiel da peça."""
    structure_guards = build_structure_guard_clauses(
        structural_contract, set_detection=set_detection,
    )
    set_info = set_detection or {}
    mode_hint = str(mode or "").strip().lower()
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

    _identity_guard = (
        "The people/models shown in the reference images are NOT the subject — "
        "completely ignore their face, skin tone, hair color, hair style, body type, age, and ethnicity. "
        "Create a clearly different adult Brazilian woman for this photo."
    )
    creative_direction = str(art_direction_soul or "").strip()
    parts = [
        _identity_guard,
        "Preserve exact garment geometry, texture continuity, and construction details.",
    ]
    if angle_directive:
        parts.insert(1, angle_directive)
    if structural_hint:
        parts.append(f"Garment identity: {structural_hint}.")
    if structure_guards:
        parts.append("Non-negotiable structure guards: " + "; ".join(structure_guards) + ".")
    parts.append(
        "Treat the garment as the fixed object and build the woman, pose, camera relation, and environment around it. "
        "Never reshape the garment to solve composition."
    )
    if creative_direction:
        parts.append(creative_direction)
    else:
        parts.append(
            "Invent a new Brazilian woman and a commercially believable setting around the locked garment. "
            "Do not default to a premium indoor catalog setup unless the active image direction explicitly asks for it."
        )
    if str(fidelity_mode).strip().lower() == "estrita":
        parts.append("Prioritize exact garment fidelity over editorial variation and avoid any reinterpretation of silhouette, length, or stitch logic.")
    styling_intro = (
        "Keep the garment as the visual hero and let styling stay secondary to it. "
    )
    parts.append(
        styling_intro
        + accessory_guard
        + "Do not promote inner tops, jewelry, shoes, or unrelated accessories into coordinated product pieces. "
        + "Build new styling independent from the reference person's lower-body look, footwear, and props."
    )
    if use_image_grounding:
        parts.insert(0,
            "Use image search to reference real examples of this garment type for accurate silhouette and texture."
        )
    return " ".join(parts)
