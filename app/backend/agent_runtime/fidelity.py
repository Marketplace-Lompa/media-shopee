"""
Camada de fidelidade para fluxo com imagem de referência.

Responsabilidade ÚNICA: proteger a identidade visual da peça durante
a geração com input de imagem. Monta locks, guards, reference policy,
pattern lock, neckline guard e texture fidelity.

NÃO decide direção criativa (cena, pose, câmera, iluminação).
Essa direção vem do mode ativo via modes.py.
"""
from __future__ import annotations

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
    "Use all references only as GARMENT references for shape, fabric, stitch, and color behavior.",
    "Never transfer identity from references: do not copy face, skin tone, body type, hairline, hairstyle, or age impression.",
    "Never repeat the exact composition, framing, or dominant gesture from the references. Keep the garment completely faithful, but create an entirely new context and physical presence.",
]

_REFERENCE_USAGE_RULES_STRICT = [
    "Treat every visible person in references as an anonymous mannequin used only for garment transfer.",
    "Generate a fully new Brazilian model identity from scratch; any resemblance to reference people is a hard failure.",
]

_REFERENCE_USAGE_RULES_HIGH_GUARD = [
    "Use references for garment-only visual evidence; identity transfer from references is strictly forbidden.",
    "Deliberately separate facial geometry from references by changing jawline, eye spacing, nose bridge, lip shape, and hairline.",
]


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
) -> str:
    """Monta a política de uso de referências por nível de proteção."""
    dynamic_rules = list(extra_rules or [])
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
    ia_trunc = ia_text[:250].rstrip(",. ")
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
    pose_flex_guideline: Optional[str] = None,
    user_prompt: Optional[str] = None,
    image_analysis: Optional[str] = None,
    look_contract: Optional[dict[str, Any]] = None,
    angle_directive: str = "",
) -> str:
    """Compila o prompt final de edição: shell de fidelidade + soul criativo.

    Arquitetura:
      - Camadas determinísticas: locks, guards, reference policy, pattern lock,
        neckline guard, look_contract, texture fidelity.
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
    )

    # 4. Neckline guard
    neckline_guard = _closed_neckline_guard(structural_contract)

    # 5. Look contract constraints
    lc = look_contract if isinstance(look_contract, dict) else {}
    lc_active = bool(lc) and float(lc.get("confidence", 0) or 0) > 0.5
    forbidden_bottoms_clause = ""
    if lc_active and lc.get("forbidden_bottoms"):
        items = ", ".join(
            str(x).strip() for x in lc["forbidden_bottoms"] if str(x).strip()
        )
        if items:
            forbidden_bottoms_clause = (
                f"NEVER use these lower-body types for this garment "
                f"(styling incoherence): {items}."
            )

    # 6. Pose flex
    pose_flex = (
        str(pose_flex_guideline).strip()
        if str(pose_flex_guideline or "").strip()
        else "Allow a naturally varied pose while preserving garment silhouette and readability."
    )

    # 7. Texture fidelity
    texture_clause = (
        f"Render the garment with macro-accurate {garment_material}, "
        f"correct fabric weight, consistent stitch definition, "
        f"and realistic light absorption across {garment_color}."
    )

    # 8. Compile: deterministic shell + creative soul
    sentences = [
        str(angle_directive or "").strip(),
        (
            "IDENTITY REPLACEMENT: The person in the base image is a PLACEHOLDER "
            "and must be fully replaced. Do not preserve ANY facial features, "
            "skin tone, hair color, hair style, body type, or age from the "
            "base image person OR from the reference images. "
            "Create a completely new person."
        ),
        "Keep the garment exactly the same: " + ", ".join(locks) + ".",
        pattern_lock,
        reference_policy,
        (
            "Before rendering, internally plan the composition around a "
            "locked garment object. Only the model identity, pose, camera, "
            "and environment may change."
        ),
        pose_flex,
        # Creative direction (SOUL — from mode, LLM invents freely)
        art_direction_soul,
        neckline_guard,
        forbidden_bottoms_clause,
        texture_clause,
        (
            "Keep the image highly photorealistic with natural skin texture, "
            "visible pores, mild facial asymmetry, and realistic body proportions."
        ),
    ]

    # User prompt override
    extra = (user_prompt or "").strip()
    if extra:
        from agent_runtime.normalize_user_intent import normalize_user_intent
        intent = normalize_user_intent(extra)
        sentences.append(f"Additional commercial direction: {intent['normalized']}.")

    return " ".join(s.strip() for s in sentences if s and s.strip())


# ── Prompt de fidelidade para stage 1 (base fiel) ────────────────────────

def build_stage1_prompt(
    structural_contract: Optional[dict[str, Any]],
    structural_hint: Optional[str],
    *,
    set_detection: Optional[dict[str, Any]] = None,
    fidelity_mode: str = "balanceada",
    mode: str = "natural",
    angle_directive: str = "",
    look_contract: Optional[dict[str, Any]] = None,
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
    # Todos os modes usam o prompt padrão premium
    parts = [
        "Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment.",
        _identity_guard,
        "Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible.",
        "Clean premium indoor composition, soft natural daylight.",
        "Preserve exact garment geometry, texture continuity, and construction details.",
    ]
    if angle_directive:
        parts.insert(1, angle_directive)
    if structural_hint:
        parts.append(f"Garment identity: {structural_hint}.")
    if structure_guards:
        parts.append("Non-negotiable structure guards: " + "; ".join(structure_guards) + ".")
    parts.append(
        "Treat the garment as the fixed object and build the model, camera, and background around it. "
        "Never reshape the garment to solve composition."
    )
    if str(fidelity_mode).strip().lower() == "estrita":
        parts.append("Prioritize exact garment fidelity over editorial variation and avoid any reinterpretation of silhouette, length, or stitch logic.")
    styling_intro = (
        "Catalog-ready minimal styling with the garment as the hero piece. "
        "Keep accessories subtle and secondary to the garment. "
    )
    parts.append(
        styling_intro
        + accessory_guard
        + "Do not promote inner tops, jewelry, shoes, or unrelated accessories into coordinated product pieces. "
        + "Build new styling independent from the reference person's lower-body look, footwear, and props."
    )
    if look_contract and float(look_contract.get("confidence", 0) or 0) > 0.5:
        _lc_bottom = str(look_contract.get("bottom_style") or "").strip()
        _lc_forbidden = [str(x).strip() for x in (look_contract.get("forbidden_bottoms") or []) if str(x).strip()]
        if _lc_bottom:
            parts.append(f"Preferred lower-body styling: {_lc_bottom}.")
        if _lc_forbidden:
            parts.append(f"Avoid these lower-body types (incoherent with this garment): {', '.join(_lc_forbidden)}.")
    if use_image_grounding:
        parts.insert(0,
            "Use image search to reference real examples of this garment type for accurate silhouette and texture."
        )
    return " ".join(parts)
