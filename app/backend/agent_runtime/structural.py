import re
from typing import Any, Optional

from agent_runtime.constants import (
    _LABEL_STRIP_RE,
    _WITHOUT_MAP,
    _NEG_CLAUSE_RE,
    _FRONT_OPENING_PHRASES,
    _LENGTH_PHRASES,
    _VOLUME_PHRASES,
    _HEM_PHRASES,
    _SLEEVE_TYPE_PHRASES,
    _SLEEVE_LEN_PHRASES,
)

_SET_MEMBER_CLASSES = {"garment", "coordinated_accessory", "styling_layer", "unrelated_accessory", "unknown"}
_SET_INCLUDE_POLICIES = {"must_include", "optional", "exclude", "unknown"}
_SET_MODES = {"off", "probable", "explicit"}
_SET_ROLE_KEYWORDS = (
    "cardigan",
    "pullover",
    "sweater",
    "scarf",
    "shawl",
    "ruana",
    "poncho",
    "cape",
    "kimono",
    "blazer",
    "jacket",
    "vest",
    "blouse",
    "shirt",
    "top",
    "dress",
    "skirt",
    "pants",
    "trousers",
    "shorts",
    "jumpsuit",
    "wrap",
)

def _enum_or_default(value: Any, allowed: set[str], default: str = "unknown") -> str:
    """Valida string contra set de valores permitidos; retorna default se fora."""
    v = str(value or "").strip().lower()
    return v if v in allowed else default

def _clamp01(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except Exception:
        return 0.0

def _infer_set_role_key(role_label: str) -> str:
    role = str(role_label or "").strip().lower()
    for token in _SET_ROLE_KEYWORDS:
        if re.search(rf"\b{re.escape(token)}s?\b", role):
            return token
    return role.split()[-1] if role else "unknown"

def _normalize_set_member(raw: Any, *, score: float, explicit_mode: bool) -> Optional[dict]:
    if not isinstance(raw, dict):
        return None

    role = str(raw.get("role") or raw.get("label") or raw.get("name") or "").strip()
    if not role:
        return None

    role_key = _infer_set_role_key(role)
    member_class = _enum_or_default(raw.get("member_class"), _SET_MEMBER_CLASSES, "unknown")
    if member_class == "unknown":
        if role_key in {"scarf", "shawl"} and score >= 0.5:
            member_class = "coordinated_accessory"
        elif role_key in {"top", "shirt", "blouse"}:
            member_class = "styling_layer"
        else:
            member_class = "garment"

    include_policy = _enum_or_default(raw.get("include_policy"), _SET_INCLUDE_POLICIES, "unknown")
    if include_policy == "unknown":
        if member_class in {"styling_layer", "unrelated_accessory"}:
            include_policy = "exclude"
        elif explicit_mode:
            include_policy = "must_include"
        elif score >= 0.45 and member_class in {"garment", "coordinated_accessory"}:
            include_policy = "optional"
        else:
            include_policy = "exclude"

    render_separately_raw = raw.get("render_separately")
    if render_separately_raw is None:
        render_separately = include_policy != "exclude" and member_class in {"garment", "coordinated_accessory"}
    else:
        render_separately = bool(render_separately_raw)

    fusion_forbidden_raw = raw.get("fusion_forbidden")
    if fusion_forbidden_raw is None:
        fusion_forbidden = (
            member_class == "coordinated_accessory"
            or (include_policy == "must_include" and render_separately)
        )
    else:
        fusion_forbidden = bool(fusion_forbidden_raw)

    confidence = _clamp01(raw.get("confidence", score if include_policy != "exclude" else min(score, 0.5)))
    return {
        "role": role[:72],
        "role_key": role_key[:32],
        "member_class": member_class,
        "include_policy": include_policy,
        "render_separately": render_separately,
        "fusion_forbidden": fusion_forbidden,
        "confidence": round(confidence, 3),
    }

def get_set_members(
    set_detection: Optional[dict],
    *,
    include_policies: Optional[set[str]] = None,
    member_classes: Optional[set[str]] = None,
    active_only: bool = False,
    exclude_primary_piece: bool = False,
) -> list[dict]:
    payload = set_detection or {}
    if active_only and str(payload.get("set_lock_mode", "off") or "off").strip().lower() == "off":
        return []
    members = payload.get("set_members") or []
    primary_piece_role = str(payload.get("primary_piece_role", "") or "").strip().lower()
    rows: list[dict] = []
    for raw in members:
        if not isinstance(raw, dict):
            continue
        include_policy = str(raw.get("include_policy", "") or "").strip().lower()
        member_class = str(raw.get("member_class", "") or "").strip().lower()
        role = str(raw.get("role", "") or "").strip().lower()
        if include_policies and include_policy not in include_policies:
            continue
        if member_classes and member_class not in member_classes:
            continue
        if exclude_primary_piece and primary_piece_role and role == primary_piece_role:
            continue
        rows.append(raw)
    return rows

def get_set_member_labels(
    set_detection: Optional[dict],
    *,
    include_policies: Optional[set[str]] = None,
    member_classes: Optional[set[str]] = None,
    active_only: bool = False,
    exclude_primary_piece: bool = False,
) -> list[str]:
    labels: list[str] = []
    for member in get_set_members(
        set_detection,
        include_policies=include_policies,
        member_classes=member_classes,
        active_only=active_only,
        exclude_primary_piece=exclude_primary_piece,
    ):
        label = str(member.get("role", "") or "").strip()
        if label and label not in labels:
            labels.append(label)
    return labels

def get_set_member_keys(
    set_detection: Optional[dict],
    *,
    include_policies: Optional[set[str]] = None,
    member_classes: Optional[set[str]] = None,
    active_only: bool = False,
    exclude_primary_piece: bool = False,
) -> list[str]:
    keys: list[str] = []
    for member in get_set_members(
        set_detection,
        include_policies=include_policies,
        member_classes=member_classes,
        active_only=active_only,
        exclude_primary_piece=exclude_primary_piece,
    ):
        key = str(member.get("role_key", "") or "").strip().lower()
        if key and key not in keys:
            keys.append(key)
    return keys

def has_set_member(
    set_detection: Optional[dict],
    role_key: str,
    *,
    include_policies: Optional[set[str]] = None,
    member_classes: Optional[set[str]] = None,
    active_only: bool = False,
    exclude_primary_piece: bool = False,
) -> bool:
    target = str(role_key or "").strip().lower()
    if not target:
        return False
    return target in get_set_member_keys(
        set_detection,
        include_policies=include_policies,
        member_classes=member_classes,
        active_only=active_only,
        exclude_primary_piece=exclude_primary_piece,
    )

def is_open_draped_outer_garment(contract: Optional[dict]) -> bool:
    payload = contract or {}
    front_opening = str(payload.get("front_opening", "") or "").strip().lower()
    sleeve_type = str(payload.get("sleeve_type", "") or "").strip().lower()
    silhouette_volume = str(payload.get("silhouette_volume", "") or "").strip().lower()
    opening_continuity = str(payload.get("opening_continuity", "") or "").strip().lower()
    drop_profile = str(payload.get("drop_profile", "") or "").strip().lower()
    hem_shape = str(payload.get("hem_shape", "") or "").strip().lower()
    edge_contour = str(payload.get("edge_contour", "") or "").strip().lower()
    return (
        front_opening == "open"
        and (
            sleeve_type in {"cape_like", "dolman_batwing"}
            or silhouette_volume in {"draped", "oversized"}
            or opening_continuity == "continuous"
            or drop_profile in {"side_drop", "cocoon_side_drop"}
            or hem_shape in {"rounded", "cocoon", "asymmetric"}
            or edge_contour == "soft_curve"
        )
    )

def is_spatially_sensitive_garment(
    contract: Optional[dict],
    *,
    set_detection: Optional[dict] = None,
    selector_stats: Optional[dict] = None,
) -> bool:
    payload = contract or {}
    sleeve_type = str(payload.get("sleeve_type", "") or "").strip().lower()
    silhouette_volume = str(payload.get("silhouette_volume", "") or "").strip().lower()
    garment_length = str(payload.get("garment_length", "") or "").strip().lower()
    set_mode = str((set_detection or {}).get("set_mode", "off") or "off").strip().lower()
    complex_garment = bool((selector_stats or {}).get("complex_garment"))
    return bool(
        complex_garment
        or set_mode in {"explicit", "probable"}
        or is_open_draped_outer_garment(payload)
        or sleeve_type in {"cape_like", "dolman_batwing"}
        or (silhouette_volume in {"draped", "oversized"} and garment_length in {"upper_thigh", "mid_thigh", "knee_plus"})
    )

def is_selfie_capture_compatible(
    contract: Optional[dict],
    *,
    set_detection: Optional[dict] = None,
    selector_stats: Optional[dict] = None,
) -> bool:
    payload = contract or {}
    front_opening = str(payload.get("front_opening", "") or "").strip().lower()
    return not is_spatially_sensitive_garment(
        payload,
        set_detection=set_detection,
        selector_stats=selector_stats,
    ) and front_opening != "open"


def has_surface_hero_priority(
    contract: Optional[dict],
    *,
    set_detection: Optional[dict] = None,
    selector_stats: Optional[dict] = None,
) -> bool:
    payload = contract or {}
    must_keep = [str(item or "").strip().lower() for item in (payload.get("must_keep") or []) if str(item).strip()]
    front_opening = str(payload.get("front_opening", "") or "").strip().lower()
    garment_length = str(payload.get("garment_length", "") or "").strip().lower()
    silhouette_volume = str(payload.get("silhouette_volume", "") or "").strip().lower()
    set_mode = str((set_detection or {}).get("set_mode", "off") or "off").strip().lower()
    hero_tokens = (
        "texture",
        "stitch",
        "pattern",
        "stripe",
        "rib",
        "crochet",
        "knit",
        "panel",
        "scarf",
        "set",
    )
    return bool(
        is_spatially_sensitive_garment(
            payload,
            set_detection=set_detection,
            selector_stats=selector_stats,
        )
        or set_mode in {"explicit", "probable"}
        or any(any(token in cue for token in hero_tokens) for cue in must_keep)
        or (
            front_opening == "closed"
            and garment_length in {"cropped", "waist", "hip"}
            and silhouette_volume in {"fitted", "regular", "structured"}
        )
    )


def prefers_supported_lower_body_styling(
    contract: Optional[dict],
    *,
    set_detection: Optional[dict] = None,
    selector_stats: Optional[dict] = None,
) -> bool:
    payload = contract or {}
    front_opening = str(payload.get("front_opening", "") or "").strip().lower()
    garment_length = str(payload.get("garment_length", "") or "").strip().lower()
    set_mode = str((set_detection or {}).get("set_mode", "off") or "off").strip().lower()
    return bool(
        is_spatially_sensitive_garment(
            payload,
            set_detection=set_detection,
            selector_stats=selector_stats,
        )
        or front_opening == "open"
        or garment_length in {"upper_thigh", "mid_thigh", "knee_plus"}
        or set_mode in {"explicit", "probable"}
    )

def _normalize_structural_contract(raw: dict) -> dict:
    """Valida e normaliza o sub-objeto structural_contract vindo da triagem unificada."""
    garment_subtype = _enum_or_default(
        raw.get("garment_subtype"),
        {"standard_cardigan", "ruana_wrap", "poncho", "cape", "kimono", "bolero", "vest",
         "jacket", "blazer", "pullover", "t_shirt", "blouse", "dress", "skirt",
         "pants", "shorts", "jumpsuit", "other", "unknown"},
    )
    sleeve_type = _enum_or_default(
        raw.get("sleeve_type"),
        {"set-in", "raglan", "dolman_batwing", "drop_shoulder", "cape_like", "unknown"},
    )
    sleeve_length = _enum_or_default(
        raw.get("sleeve_length"),
        {"sleeveless", "cap", "short", "elbow", "three_quarter", "long", "unknown"},
    )
    front_opening = _enum_or_default(raw.get("front_opening"), {"open", "partial", "closed", "unknown"})
    hem_shape     = _enum_or_default(raw.get("hem_shape"), {"straight", "rounded", "asymmetric", "cocoon", "unknown"})
    garment_length = _enum_or_default(
        raw.get("garment_length"),
        {"cropped", "waist", "hip", "upper_thigh", "mid_thigh", "knee_plus", "unknown"},
    )
    silhouette_volume = _enum_or_default(
        raw.get("silhouette_volume"),
        {"fitted", "regular", "oversized", "draped", "structured", "unknown"},
    )
    edge_contour = _enum_or_default(
        raw.get("edge_contour"),
        {"clean", "soft_curve", "undulating", "scalloped", "angular", "unknown"},
    )
    drop_profile = _enum_or_default(
        raw.get("drop_profile"),
        {"even", "side_drop", "high_low", "cocoon_side_drop", "unknown"},
    )
    opening_continuity = _enum_or_default(
        raw.get("opening_continuity"),
        {"continuous", "broken", "lapel_like", "unknown"},
    )
    try:
        confidence = float(raw.get("confidence", 0.0) or 0.0)
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    must_keep = []
    for item in list(raw.get("must_keep", []) or []):
        txt = str(item or "").strip()
        if txt:
            must_keep.append(txt[:84])
        if len(must_keep) >= 4:
            break
    must_keep_lower = [item.lower() for item in must_keep]

    _hp_raw = raw.get("has_pockets")
    has_pockets: bool | None = bool(_hp_raw) if _hp_raw is not None else None

    draped_cues = (
        "continuous neckline-to-front edge",
        "broad uninterrupted back panel",
        "rounded cocoon side drop",
        "arm coverage formed by the same draped panel",
    )
    looks_like_draped_wrap = (
        front_opening == "open"
        and silhouette_volume in {"draped", "oversized"}
        and (
            sleeve_type in {"cape_like", "dolman_batwing"}
            or any(cue in must_keep_lower for cue in draped_cues)
        )
    )

    if garment_subtype == "other" and looks_like_draped_wrap:
        garment_subtype = "ruana_wrap"

    if garment_subtype in {"ruana_wrap", "poncho", "cape"} or sleeve_type == "cape_like":
        if garment_length in {"waist", "hip"} and silhouette_volume in {"draped", "oversized"}:
            garment_length = "upper_thigh"
        if hem_shape == "straight" and silhouette_volume in {"draped", "oversized"}:
            hem_shape = "rounded"
        micro_edge_cues = (
            "scalloped crochet border",
            "crochet border texture",
            "ribbed edge finish",
            "edge texture",
            "trim texture",
        )
        has_macro_edge_cue = any(
            cue in " ".join(must_keep_lower)
            for cue in (
                "scalloped outline",
                "undulating outline",
                "wavy outer edge",
                "curved outer border",
                "cocoon side drop",
            )
        )
        if edge_contour in {"undulating", "scalloped"} and hem_shape in {"rounded", "cocoon"}:
            if any(cue in " ".join(must_keep_lower) for cue in micro_edge_cues) and not has_macro_edge_cue:
                edge_contour = "soft_curve"
        if edge_contour == "unknown" and hem_shape in {"rounded", "cocoon"}:
            edge_contour = "soft_curve"
        if drop_profile == "unknown" and hem_shape == "cocoon":
            drop_profile = "cocoon_side_drop"
        elif drop_profile == "unknown" and garment_length in {"upper_thigh", "mid_thigh"}:
            drop_profile = "side_drop"
        if opening_continuity == "unknown" and front_opening == "open":
            opening_continuity = "continuous"

    if must_keep:
        filtered_must_keep: list[str] = []
        for cue in must_keep:
            cue_low = cue.lower()
            if (
                ("crochet border" in cue_low or "edge texture" in cue_low or "trim texture" in cue_low)
                and not any(token in cue_low for token in ("outline", "silhouette", "outer edge", "outer border"))
            ):
                continue
            filtered_must_keep.append(cue)
        must_keep = filtered_must_keep[:4]

    known_fields = [f != "unknown" for f in [
        sleeve_type, sleeve_length, front_opening, hem_shape, garment_length, silhouette_volume,
        edge_contour, drop_profile, opening_continuity,
    ]]
    enabled = confidence >= 0.45 and any(known_fields)
    return {
        "enabled": enabled, "confidence": round(confidence, 3),
        "garment_subtype": garment_subtype,
        "sleeve_type": sleeve_type, "sleeve_length": sleeve_length,
        "front_opening": front_opening, "hem_shape": hem_shape,
        "garment_length": garment_length, "silhouette_volume": silhouette_volume,
        "edge_contour": edge_contour,
        "drop_profile": drop_profile,
        "opening_continuity": opening_continuity,
        "must_keep": must_keep,
        "has_pockets": has_pockets,
    }

def _normalize_set_detection(raw: dict) -> dict:
    """Valida e normaliza o sub-objeto set_detection vindo da triagem unificada."""
    is_set = bool(raw.get("is_garment_set", False))
    score = _clamp01(raw.get("set_pattern_score", 0.0))
    roles = [str(x).strip() for x in (raw.get("detected_garment_roles", []) or []) if str(x).strip()]
    cues = [str(x).strip() for x in (raw.get("set_pattern_cues", []) or []) if str(x).strip()]

    raw_mode = _enum_or_default(raw.get("set_mode"), _SET_MODES, "unknown")
    explicit_mode = raw_mode == "explicit" or (is_set and score >= 0.68)
    normalized_members: list[dict] = []
    seen_member_keys: set[tuple[str, str]] = set()
    for item in list(raw.get("set_members", []) or []):
        member = _normalize_set_member(item, score=score, explicit_mode=explicit_mode)
        if not member:
            continue
        member_key = (str(member.get("role", "")).lower(), str(member.get("member_class", "")).lower())
        if member_key in seen_member_keys:
            continue
        seen_member_keys.add(member_key)
        normalized_members.append(member)
        if len(normalized_members) >= 6:
            break

    if not normalized_members:
        for role in roles[:5]:
            fallback_member = _normalize_set_member({"role": role}, score=score, explicit_mode=explicit_mode)
            if not fallback_member:
                continue
            member_key = (str(fallback_member.get("role", "")).lower(), str(fallback_member.get("member_class", "")).lower())
            if member_key in seen_member_keys:
                continue
            seen_member_keys.add(member_key)
            normalized_members.append(fallback_member)

    initial_included_members = get_set_members(
        {"set_members": normalized_members},
        include_policies={"must_include", "optional"},
        member_classes={"garment", "coordinated_accessory"},
    )
    has_secondary_piece = any(
        str(member.get("member_class", "") or "").strip().lower() == "coordinated_accessory"
        for member in initial_included_members
    ) or len(initial_included_members) >= 2

    if raw_mode in _SET_MODES:
        set_mode = raw_mode
    elif has_secondary_piece and is_set and score >= 0.68:
        set_mode = "explicit"
    elif has_secondary_piece and (is_set or score >= 0.48):
        set_mode = "probable"
    else:
        set_mode = "off"

    if set_mode == "explicit":
        for member in normalized_members:
            member_class = str(member.get("member_class", "") or "").strip().lower()
            if member_class == "coordinated_accessory" and str(member.get("include_policy", "") or "").strip().lower() != "exclude":
                member["include_policy"] = "must_include"
            if member_class == "coordinated_accessory" and str(member.get("include_policy", "") or "").strip().lower() != "exclude":
                member["render_separately"] = True
                member["fusion_forbidden"] = True
    for member in normalized_members:
        member_class = str(member.get("member_class", "") or "").strip().lower()
        if member_class in {"styling_layer", "unrelated_accessory"}:
            member["include_policy"] = "exclude"
            member["render_separately"] = False
            member["fusion_forbidden"] = True

    primary_piece_role = str(raw.get("primary_piece_role") or "").strip()
    if not primary_piece_role:
        for member in normalized_members:
            if str(member.get("member_class", "") or "").strip().lower() == "garment":
                primary_piece_role = str(member.get("role", "") or "").strip()
                break
    if not primary_piece_role and roles:
        primary_piece_role = roles[0]

    detected_roles = list(dict.fromkeys(
        roles
        + get_set_member_labels(
            {"set_members": normalized_members},
            include_policies={"must_include", "optional"},
            member_classes={"garment", "coordinated_accessory"},
        )
    ))
    lock_mode = "explicit" if set_mode == "explicit" else ("generic" if set_mode == "probable" else "off")
    must_include_roles = get_set_member_labels({"set_members": normalized_members}, include_policies={"must_include"})
    excluded_roles = get_set_member_labels({"set_members": normalized_members}, include_policies={"exclude"})
    return {
        "is_garment_set": bool(is_set or set_mode != "off"),
        "set_pattern_score": round(score, 3),
        "set_mode": set_mode,
        "primary_piece_role": primary_piece_role[:72],
        "detected_garment_roles": detected_roles[:6],
        "set_pattern_cues": cues[:4],
        "set_members": normalized_members[:6],
        "must_include_roles": must_include_roles[:4],
        "excluded_roles": excluded_roles[:4],
        "set_lock_mode": lock_mode,
    }

def _neg_to_pos(text: str) -> str:
    """
    Strip label prefixes (LOCK:, GUIDED:, STRUCTURE:) e converte negativos
    comuns em equivalentes positivos ou os remove.
    """
    if not text:
        return ""
    result = _LABEL_STRIP_RE.sub("", text)
    for pattern, replacement in _WITHOUT_MAP:
        result = pattern.sub(replacement, result)
    result = _NEG_CLAUSE_RE.sub("", result)
    result = re.sub(r" {2,}", " ", result)
    return result.strip()

def normalize_prompt_text(text: str) -> str:
    """Wrapper público: normaliza labels e negativos de um prompt (ex: repair_prompt)."""
    return _neg_to_pos(text)

def _prune_structural_conflicts(base: str, contract: Optional[dict]) -> str:
    if not contract or not contract.get("enabled"):
        return base
    
    pruned = base
    sleeve_type = str(contract.get("sleeve_type", ""))
    sleeve_length = str(contract.get("sleeve_length", ""))
    front_opening = str(contract.get("front_opening", ""))
    hem_shape = str(contract.get("hem_shape", ""))
    
    if sleeve_length == "sleeveless" or sleeve_type in ["straps", "tube", "cape_like", "sleeveless"]:
        pruned = re.sub(r'(?i)\b(?:long|short|three-quarter|\d/4|puff|batwing|bell|fitted|set-in)\s*sleeves?\b', '', pruned)
    elif sleeve_length in ["long", "three_quarter"]:
        pruned = re.sub(r'(?i)\b(?:sleeveless|short sleeves?|tank top|tube top)\b', '', pruned)
    
    if front_opening == "open":
        pruned = re.sub(r'(?i)\b(?:buttoned up|zipped up|closed front|fully closed|button closed)\b', '', pruned)
    elif front_opening == "closed":
        pruned = re.sub(r'(?i)\b(?:open front|unbuttoned|unzipped|worn open|fully open)\b', '', pruned)
        
    if hem_shape == "straight":
        pruned = re.sub(r'(?i)\b(?:asymmetric hem|rounded hem|cocoon hem|curved hem)\b', '', pruned)
    elif hem_shape == "asymmetric":
        pruned = re.sub(r'(?i)\b(?:straight hem|even hem)\b', '', pruned)

    # Volume conflict: "structured" no base puxa silhueta rígida quando contract diz draped
    silhouette_volume = str(contract.get("silhouette_volume", ""))
    if silhouette_volume == "draped":
        pruned = re.sub(r'(?i)\bstructured\b', '', pruned)

    pruned = re.sub(r'\s+([,.])', r'\1', pruned)
    pruned = re.sub(r'([,.])\s*([,.])', r'\2', pruned)
    pruned = re.sub(r',\s*\.', '.', pruned)
    pruned = re.sub(r'(?<!\w)[,.](?!\w)', ' ', pruned)
    return re.sub(r' {2,}', ' ', pruned).strip()

def _resolve_structural_conflicts(base: str, contract: Optional[dict]) -> str:
    text = (base or "").strip()
    if not text:
        return text
    if not contract or not contract.get("enabled"):
        return text

    subtype = str(contract.get("garment_subtype", "unknown")).strip().lower()
    sleeve_type = str(contract.get("sleeve_type", "unknown")).strip().lower()
    must_keep = [str(x).strip().lower() for x in (contract.get("must_keep", []) or []) if str(x).strip()]
    must_keep_blob = " ".join(must_keep)
    base_low = text.lower()

    neck_wrap_signals = (
        "neck wrap", "wrapped around neck", "around her neck", "around the neck",
        "draped around neck", "cowl", "scarf", "cachecol", "pescoço",
    )
    has_neck_wrap = any(sig in must_keep_blob for sig in neck_wrap_signals) or any(sig in base_low for sig in neck_wrap_signals)

    draped_panel_signals = (
        "continuous panel", "draped panel", "single panel", "one-piece drape", "one piece drape",
        "continuous drape", "cape-like",
    )
    is_draped_panel = (
        subtype in {"ruana_wrap", "poncho", "cape"}
        or sleeve_type == "cape_like"
        or any(sig in must_keep_blob for sig in draped_panel_signals)
        or any(sig in base_low for sig in draped_panel_signals)
    )

    if has_neck_wrap:
        text = re.sub(r'(?i)\bfront panel fully open and draping\b', "front drape opening preserved from reference", text)
        text = re.sub(r'(?i)\bfully open front\b', "front opening behavior preserved from reference", text)
        text = re.sub(r'(?i)\bopen-front construction\b', "reference opening behavior", text)

    if is_draped_panel:
        text = re.sub(
            r'(?i)\barm coverage from draped fabric panel only,\s*no separate sleeve tubes\b',
            "arm coverage from a continuous draped panel",
            text,
        )
        text = re.sub(r'(?i)\bno separate sleeve tubes\b', "", text)
        text = re.sub(r'(?i)\bseparate sleeve tubes?\b', "", text)
        text = re.sub(r'(?i)\bset-in sleeves?\b', "", text)
        text = re.sub(r'(?i)\bfitted sleeves?\b', "", text)
        # "structured" puxa o image model para silhueta rígida/cardigan —
        # conflita com ruana/poncho/cape que são peças fluidas sem estrutura fixa.
        text = re.sub(r'(?i)\bstructured\b', "", text)

    if re.search(r'(?i)\bcape-like arm coverage\b', text) and re.search(r'(?i)\bfitted sleeves?\b', text):
        text = re.sub(r'(?i)\bfitted sleeves?\b', "", text)

    text = re.sub(r'\s+([,.])', r'\1', text)
    text = re.sub(r'([,.])\s*([,.])', r'\2', text)
    text = re.sub(r',\s*\.', '.', text)
    text = re.sub(r'(?<!\w)[,.](?!\w)', ' ', text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text

def _prune_cover_pose_conflicts(base: str) -> str:
    """Remove apenas bans duros: sentada, mesa/café, candid-lifestyle.
    mid-stride e vocabulário fashion (high-fashion, striking) são mantidos —
    contribuem para diversidade de pose e linguagem visual."""
    pruned = base
    # Hard bans: seated/sitting (incompatível com catálogo standing)
    pruned = re.sub(r'(?i)\b(?:sitting|seated|sit down|sits|chair|stool|bench|sofa|couch)\b', '', pruned)
    # Hard bans: table/coffee props (incompatível com foco na peça)
    pruned = re.sub(
        r'(?i)\b(?:at a table|coffee table|cafe table|holding (?:a )?(?:cup|mug|coffee|drink)|coffee cup|drinking coffee)\b',
        '', pruned,
    )
    # Hard bans: candid-lifestyle phrasing (produz composição difusa)
    pruned = re.sub(r'(?i)\b(?:candid moment|candid lifestyle|relaxed cafe moment|candid cafe moment)\b', '', pruned)
    # Soft ban: sensual/sexy (incompatível com e-commerce de moda casual)
    pruned = re.sub(r'(?i)\b(?:sensual|sexy)\b', '', pruned)
    pruned = re.sub(r'\s+([,.])', r'\1', pruned)
    pruned = re.sub(r'([,.])\s*([,.])', r'\2', pruned)
    pruned = re.sub(r',\s*\.', '.', pruned)
    return re.sub(r" {2,}", " ", pruned).strip()

def _compress_structural_facts(contract: dict) -> tuple[list[tuple[str, int, str]], list[tuple[str, str]]]:
    if not contract or not contract.get("enabled"):
        return [], []

    clauses: list[tuple[str, int, str]] = []
    discarded: list[tuple[str, str]] = []

    confidence    = float(contract.get("confidence", 0.0) or 0.0)
    subtype       = str(contract.get("garment_subtype",  "unknown"))
    sleeve_type   = str(contract.get("sleeve_type",      "unknown"))
    sleeve_length = str(contract.get("sleeve_length",    "unknown"))
    front_opening = str(contract.get("front_opening",    "unknown"))
    hem_shape     = str(contract.get("hem_shape",        "unknown"))
    garment_length= str(contract.get("garment_length",   "unknown"))
    silhouette_volume = str(contract.get("silhouette_volume", "unknown"))
    must_keep     = list(contract.get("must_keep", []) or [])
    has_pockets   = contract.get("has_pockets")

    _draped_subtypes = {"ruana_wrap", "poncho", "cape"}
    is_draped_no_sleeve = (subtype in _draped_subtypes or sleeve_type == "cape_like")

    _SUBTYPE_PHRASES = {
        # Draped wraps: frases mínimas — visual reference é autoridade sobre construção.
        # Evitar "single-piece draped over shoulders" que Nano interpreta como poncho fechado.
        "ruana_wrap": "open-front ruana wrap",
        "poncho": "poncho wrap",
        "cape": "open-front cape",
        "standard_cardigan": "cardigan construction",
        "kimono": "kimono-wrap construction",
        "jacket": "jacket construction",
        "dress": "dress construction",
    }

    if subtype in _SUBTYPE_PHRASES:
        clauses.append((_SUBTYPE_PHRASES[subtype], 1, "garment_subtype"))

    # has_pockets=False: NÃO injetar cláusula "no pockets" —
    # mencionar "pockets" (mesmo negando) faz Nano adicionar bolsos.
    # Visual reference é autoridade.

    if is_draped_no_sleeve and front_opening == "open":
        # Sem cláusula textual — visual reference mostra a abertura.
        # "knitted edge" fazia Nano renderizar costura fantasma.
        pass
    elif front_opening in _FRONT_OPENING_PHRASES:
        clauses.append((_FRONT_OPENING_PHRASES[front_opening], 1, "front_opening"))
    elif front_opening != "unknown":
        discarded.append(("front_opening", front_opening))

    if garment_length in _LENGTH_PHRASES:
        if is_draped_no_sleeve:
            _length_text = _LENGTH_PHRASES[garment_length]
            if hem_shape == "cocoon":
                clauses.append((
                    f"The outer silhouette falls in a rounded cocoon side drop reaching { _length_text } relative to the model body.",
                    1,
                    "garment_length",
                ))
            elif hem_shape == "rounded":
                clauses.append((
                    f"The outer silhouette falls in a rounded side drop reaching { _length_text } relative to the model body.",
                    1,
                    "garment_length",
                ))
            elif hem_shape == "asymmetric":
                clauses.append((
                    f"The outer silhouette falls in a soft draped side drop reaching { _length_text } relative to the model body.",
                    1,
                    "garment_length",
                ))
            else:
                clauses.append((
                    f"The outer panel falls to { _length_text } relative to the model body.",
                    1,
                    "garment_length",
                ))
        else:
            clauses.append((_LENGTH_PHRASES[garment_length] + " relative to model body", 1, "garment_length"))
    elif garment_length != "unknown":
        discarded.append(("garment_length", garment_length))

    if silhouette_volume in _VOLUME_PHRASES and not is_draped_no_sleeve:
        clauses.append((_VOLUME_PHRASES[silhouette_volume], 1, "silhouette_volume"))
    elif silhouette_volume != "unknown":
        if not is_draped_no_sleeve:
            discarded.append(("silhouette_volume", silhouette_volume))

    if confidence >= 0.55:
        if hem_shape in _HEM_PHRASES and not is_draped_no_sleeve:
            clauses.append((_HEM_PHRASES[hem_shape], 1, "hem_shape"))
        elif hem_shape != "unknown":
            if not is_draped_no_sleeve:
                discarded.append(("hem_shape", hem_shape))

        if is_draped_no_sleeve:
            clauses.append((
                "Arm coverage is created by the same continuous body panel as the garment, forming a fluid draped wrap over the arms.",
                1,
                "sleeve_arch",
            ))
            if sleeve_type != "unknown": discarded.append(("sleeve_type", "draped_override"))
            if sleeve_length != "unknown": discarded.append(("sleeve_length", "draped_override"))
        else:
            if sleeve_type in _SLEEVE_TYPE_PHRASES:
                clauses.append((_SLEEVE_TYPE_PHRASES[sleeve_type], 1, "sleeve_type"))
            elif sleeve_type != "unknown":
                discarded.append(("sleeve_type", sleeve_type))
                
            if sleeve_length in _SLEEVE_LEN_PHRASES:
                clauses.append((_SLEEVE_LEN_PHRASES[sleeve_length], 1, "sleeve_length"))
            elif sleeve_length != "unknown":
                discarded.append(("sleeve_length", sleeve_length))
    else:
        if hem_shape != "unknown": discarded.append(("hem_shape", "low_confidence"))
        if sleeve_type != "unknown": discarded.append(("sleeve_type", "low_confidence"))
        if sleeve_length != "unknown": discarded.append(("sleeve_length", "low_confidence"))

    if confidence >= 0.68:
        _GENERIC_DRAPED_CUES = {
            "open front",
            "knit texture",
            "horizontal stripes",
            "vertical stripes",
            "striped knit texture",
            "ribbed edge finish",
            "ribbed horizontal stripe texture",
            "horizontal stripe texture",
        }
        added_cues = 0
        for cue in must_keep:
            cleaned = cue.strip()
            if cleaned:
                cleaned_low = cleaned.lower()
                if is_draped_no_sleeve:
                    if cleaned_low in _GENERIC_DRAPED_CUES or "sleeve" in cleaned_low or "batwing" in cleaned_low:
                        discarded.append(("must_keep", f"generic:{cleaned_low}"))
                        continue
                if added_cues < 3:
                    clauses.append((cleaned, 1, "must_keep"))
                    added_cues += 1
                else:
                    discarded.append(("must_keep", "limit_reached"))

    return clauses, discarded
