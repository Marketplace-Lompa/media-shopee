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

def _enum_or_default(value: Any, allowed: set[str], default: str = "unknown") -> str:
    """Valida string contra set de valores permitidos; retorna default se fora."""
    v = str(value or "").strip().lower()
    return v if v in allowed else default

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

    known_fields = [f != "unknown" for f in [
        sleeve_type, sleeve_length, front_opening, hem_shape, garment_length, silhouette_volume
    ]]
    enabled = confidence >= 0.45 and any(known_fields)
    return {
        "enabled": enabled, "confidence": round(confidence, 3),
        "garment_subtype": garment_subtype,
        "sleeve_type": sleeve_type, "sleeve_length": sleeve_length,
        "front_opening": front_opening, "hem_shape": hem_shape,
        "garment_length": garment_length, "silhouette_volume": silhouette_volume,
        "must_keep": must_keep,
        "has_pockets": has_pockets,
    }

def _normalize_set_detection(raw: dict) -> dict:
    """Valida e normaliza o sub-objeto set_detection vindo da triagem unificada."""
    is_set = bool(raw.get("is_garment_set", False))
    score  = max(0.0, min(1.0, float(raw.get("set_pattern_score", 0.0) or 0.0)))
    roles  = [str(x) for x in (raw.get("detected_garment_roles", []) or []) if str(x)]
    cues   = [str(x) for x in (raw.get("set_pattern_cues", []) or []) if str(x)]
    lock_mode = "explicit" if (is_set and score >= 0.68 and len(roles) >= 2) else ("generic" if is_set else "off")
    return {
        "is_garment_set": is_set,
        "set_pattern_score": round(score, 3),
        "detected_garment_roles": roles[:5],
        "set_pattern_cues": cues[:4],
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
