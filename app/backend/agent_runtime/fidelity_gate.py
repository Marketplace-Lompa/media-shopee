from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from google.genai import types

from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.parser import _decode_agent_response
from agent_runtime.structural import get_set_member_keys, get_set_member_labels

_DRAPED_SUBTYPES = {"ruana_wrap", "poncho", "cape", "kimono"}
_HARD_ISSUES = {
    "wrong_subtype",
    "closed_front_error",
    "invented_sleeve_slit",
    "invented_sleeves",
    "set_piece_lost",
    "construction_drift",
}
_SOFT_ISSUES = {
    "silhouette_drift",
    "hem_shape_drift",
    "texture_pattern_drift",
    "low_garment_readability",
    "pose_over_occlusion",
    "identity_similarity",
}
_LOCALIZED_REPAIR_ISSUES = {
    "texture_pattern_drift",
    "stripe_order_drift",
    "color_tone_drift",
    "low_garment_readability",
}
_LOCALIZED_POLISH_TEXTURE_THRESHOLD = 0.93
_LOCALIZED_POLISH_READABILITY_THRESHOLD = 0.94
_LOCALIZED_REPAIR_BLOCKERS = _HARD_ISSUES | {
    "silhouette_drift",
    "hem_shape_drift",
    "pose_over_occlusion",
    "identity_similarity",
    "wrong_opening_logic",
}
_KNOWN_ISSUE_CODES = _HARD_ISSUES | _SOFT_ISSUES | {
    "wrong_opening_logic",
    "stripe_order_drift",
    "color_tone_drift",
}
_STAGE_THRESHOLDS = {
    "stage1": {
        "hard_garment": 0.82,
        "soft_garment": 0.90,
        "hard_structure": 0.80,
        "soft_structure": 0.88,
        "hard_set": 0.78,
        "soft_set": 0.90,
    },
    "stage2": {
        "hard_garment": 0.78,
        "soft_garment": 0.86,
        "hard_structure": 0.76,
        "soft_structure": 0.84,
        "hard_set": 0.74,
        "soft_set": 0.86,
    },
}
_NEGATIVE_HINTS = {
    "missing",
    "omitted",
    "omit",
    "lost",
    "loss",
    "fails",
    "failed",
    "failure",
    "incorrect",
    "wrong",
    "violated",
    "invented",
    "closed",
    "converted",
    "turned",
    "instead",
    "absent",
    "without",
    "drift",
    "deviation",
}
_POSITIVE_SET_HINTS = (
    "matching scarf",
    "set preservation",
    "set fidelity",
    "coordinated set",
    "matching piece",
    "scarf is present",
    "scarf correctly rendered",
    "matching scarf set",
)
_POSITIVE_OPEN_HINTS = (
    "open-front",
    "open front",
    "front visibly open",
    "maintains its open front",
    "preserves the open front",
    "correctly maintains the open-front",
)
_TARGETED_PATCH_FORBIDDEN_HINTS = (
    "background",
    "scene",
    "camera",
    "lens",
    "framing",
    "composition",
    "pose",
    "hairstyle",
    "hair",
    "face",
    "expression",
    "body proportion",
    "lighting mood",
    "new location",
    "move the subject",
)
_TARGETED_PATCH_SCOPE_HINTS = (
    "garment",
    "stitch",
    "texture",
    "textile",
    "yarn",
    "stripe",
    "hem",
    "edge",
    "opening",
    "panel",
    "drape",
    "sleeve",
    "readability",
    "knit",
    "color",
)

FIDELITY_GATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "garment_fidelity",
        "structure_fidelity",
        "texture_fidelity",
        "set_fidelity",
        "readability_score",
        "issue_codes",
        "summary",
        "recommended_prompt_patch",
    ],
    "properties": {
        "garment_fidelity": {"type": "number"},
        "structure_fidelity": {"type": "number"},
        "texture_fidelity": {"type": "number"},
        "set_fidelity": {"type": "number"},
        "readability_score": {"type": "number"},
        "issue_codes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "summary": {"type": "string"},
        "recommended_prompt_patch": {"type": "string"},
    },
}


def _clamp_score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def _mime_from_bytes(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _mime_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def _normalize_issue_code(raw_issue: Any) -> Optional[str]:
    token = str(raw_issue or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not token:
        return None
    if token in _KNOWN_ISSUE_CODES:
        return token

    mapping = {
        "closed": "closed_front_error",
        "open_front": "wrong_opening_logic",
        "front_opening": "wrong_opening_logic",
        "sleeve_slit": "invented_sleeve_slit",
        "invented_slit": "invented_sleeve_slit",
        "separate_sleeve": "invented_sleeves",
        "tailored_armhole": "invented_sleeves",
        "set_piece": "set_piece_lost",
        "scarf": "set_piece_lost",
        "silhouette": "silhouette_drift",
        "hem": "hem_shape_drift",
        "texture": "texture_pattern_drift",
        "stitch": "texture_pattern_drift",
        "stripe": "stripe_order_drift",
        "color": "color_tone_drift",
        "readability": "low_garment_readability",
        "occlusion": "pose_over_occlusion",
        "identity": "identity_similarity",
        "subtype": "wrong_subtype",
        "construction": "construction_drift",
    }
    for needle, normalized in mapping.items():
        if needle in token:
            return normalized
    return None


def _normalize_issue_codes(raw_issues: Any) -> list[str]:
    codes: list[str] = []
    mapping = {
        "closed": "closed_front_error",
        "open_front": "wrong_opening_logic",
        "front_opening": "wrong_opening_logic",
        "sleeve_slit": "invented_sleeve_slit",
        "invented_slit": "invented_sleeve_slit",
        "separate_sleeve": "invented_sleeves",
        "tailored_armhole": "invented_sleeves",
        "set_piece": "set_piece_lost",
        "scarf": "set_piece_lost",
        "silhouette": "silhouette_drift",
        "hem": "hem_shape_drift",
        "texture": "texture_pattern_drift",
        "stitch": "texture_pattern_drift",
        "stripe": "stripe_order_drift",
        "color": "color_tone_drift",
        "readability": "low_garment_readability",
        "occlusion": "pose_over_occlusion",
        "identity": "identity_similarity",
        "subtype": "wrong_subtype",
        "construction": "construction_drift",
    }
    for item in raw_issues or []:
        normalized = _normalize_issue_code(item)
        if normalized and normalized not in codes:
            codes.append(normalized)
        token = str(item or "").strip().lower().replace("-", "_").replace(" ", "_")
        for needle, mapped in mapping.items():
            if needle in token and mapped not in codes:
                codes.append(mapped)
    return codes


def _negative_summary_issue_codes(summary_text: str) -> list[str]:
    text = str(summary_text or "").strip().lower()
    if not text:
        return []

    sentences = [chunk.strip() for chunk in re.split(r"[.!?]+", text) if chunk.strip()]
    codes: list[str] = []
    for sentence in sentences:
        if not any(hint in sentence for hint in _NEGATIVE_HINTS):
            continue

        if any(term in sentence for term in ("scarf", "set", "matching piece", "coordinated")) and any(
            hint in sentence for hint in ("missing", "omitted", "lost", "absent", "without", "fails", "failed")
        ):
            if "set_piece_lost" not in codes:
                codes.append("set_piece_lost")

        if (
            ("open front" in sentence or "open-front" in sentence or "front edge" in sentence)
            and any(hint in sentence for hint in ("missing", "violated", "wrong", "closed", "failed", "fails", "not "))
        ) or ("closed-front" in sentence or "closed front" in sentence):
            if "wrong_opening_logic" not in codes:
                codes.append("wrong_opening_logic")
            if "closed_front_error" not in codes:
                codes.append("closed_front_error")

        if any(term in sentence for term in ("converted", "turned into", "instead of", "reinterpreted")) and any(
            term in sentence for term in ("poncho", "pullover", "cardigan", "sweater", "ruana", "cape", "kimono")
        ):
            if "wrong_subtype" not in codes:
                codes.append("wrong_subtype")

        if "invented" in sentence and "slit" in sentence and "invented_sleeve_slit" not in codes:
            codes.append("invented_sleeve_slit")
        if "invented" in sentence and "sleeve" in sentence and "invented_sleeves" not in codes:
            codes.append("invented_sleeves")
        if "hem" in sentence and any(term in sentence for term in ("drift", "deviation", "wrong")) and "hem_shape_drift" not in codes:
            codes.append("hem_shape_drift")
        if any(term in sentence for term in ("texture", "stitch")) and any(term in sentence for term in ("drift", "deviation", "wrong")) and "texture_pattern_drift" not in codes:
            codes.append("texture_pattern_drift")
        if "stripe" in sentence and any(term in sentence for term in ("drift", "deviation", "wrong")) and "stripe_order_drift" not in codes:
            codes.append("stripe_order_drift")
        if "construction" in sentence and any(term in sentence for term in ("drift", "deviation", "violated", "wrong")) and "construction_drift" not in codes:
            codes.append("construction_drift")
    return codes


def _has_negative_set_signal(summary_text: str) -> bool:
    text = str(summary_text or "").strip().lower()
    if not text:
        return False
    return any(term in text for term in ("scarf", "set", "matching piece", "coordinated")) and any(
        hint in text for hint in ("missing", "omitted", "lost", "absent", "without", "fails", "failed")
    )


def _has_negative_open_signal(summary_text: str) -> bool:
    text = str(summary_text or "").strip().lower()
    if not text:
        return False
    return (
        ("closed-front" in text or "closed front" in text)
        or (
            any(term in text for term in ("open-front", "open front", "front edge"))
            and any(hint in text for hint in ("missing", "violated", "wrong", "closed", "failed", "fails", "not "))
        )
    )


def _reconcile_issue_codes(
    issue_codes: list[str],
    *,
    summary_text: str,
    set_fidelity: float,
    structure_fidelity: float,
    active_set_expected: bool = True,
) -> list[str]:
    codes = list(dict.fromkeys(str(code).strip().lower() for code in issue_codes if str(code).strip()))
    text = str(summary_text or "").strip().lower()

    if not active_set_expected and "set_piece_lost" in codes:
        codes = [code for code in codes if code != "set_piece_lost"]

    if (
        "set_piece_lost" in codes
        and set_fidelity >= 0.9
        and any(token in text for token in _POSITIVE_SET_HINTS)
        and not _has_negative_set_signal(text)
    ):
        codes = [code for code in codes if code != "set_piece_lost"]

    if (
        structure_fidelity >= 0.9
        and any(token in text for token in _POSITIVE_OPEN_HINTS)
        and not _has_negative_open_signal(text)
    ):
        codes = [code for code in codes if code not in {"wrong_opening_logic", "closed_front_error"}]

    return codes


def build_visual_fidelity_gate_policy(
    *,
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
    selector_stats: Optional[dict[str, Any]],
    fidelity_mode: str,
) -> dict[str, Any]:
    contract = structural_contract or {}
    set_info = set_detection or {}
    stats = selector_stats or {}

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
    reasons: list[str] = []

    if str(fidelity_mode).strip().lower() == "estrita":
        reasons.append("strict_fidelity")
    if bool(stats.get("complex_garment")):
        reasons.append("complex_garment")
    if bool(stats.get("small_input_mode")):
        reasons.append("small_input_mode")
    if subtype in _DRAPED_SUBTYPES:
        reasons.append(f"draped_subtype:{subtype}")
    if sleeve in {"cape_like", "dolman_batwing"}:
        reasons.append(f"sleeve_architecture:{sleeve}")
    if lock_mode != "off" or must_include_labels:
        reasons.append(f"coordinated_set:{lock_mode}")


    enabled = bool(reasons)
    return {
        "enabled": enabled,
        "reasons": reasons,
        "stage1_retry_enabled": enabled,
        "stage2_retry_enabled": enabled,
        "max_stage1_retries": 1 if enabled else 0,
        "max_stage2_retries": 1 if enabled else 0,
    }


def _gate_context_excerpt(
    *,
    stage: str,
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
    prompt: Optional[str],
) -> str:
    payload = {
        "stage": stage,
        "structural_contract": structural_contract or {},
        "set_detection": set_detection or {},
        "prompt_excerpt": str(prompt or "")[:800],
    }
    return json.dumps(payload, ensure_ascii=False)


def _base_gate_instruction(stage: str) -> str:
    if stage == "stage1":
        return (
            "You are a strict garment fidelity gate for a fashion generation pipeline. "
            "The first images are garment references and the last image is a stage-1 candidate base image. "
            "Ignore identity, hair, skin tone, body type, and background. Judge only the garment object. "
            "Focus on subtype, open-vs-closed front behavior, sleeve architecture, continuous draped panels, "
            "hem behavior, stripe order, stitch texture, and coordinated set pieces. "
            "If a ruana, poncho, or cape-like garment is turned into a sewn-sleeve cardigan/pullover, that is a severe error. "
            "Return JSON only."
        )
    return (
        "You are a strict garment fidelity gate for a fashion generation pipeline. "
        "The first images are garment references, then one approved stage-1 base image, and the last image is the stage-2 final result. "
        "Ignore identity, hair, skin tone, body type, and background. Judge only whether the final image preserved the garment object. "
        "Focus on subtype, opening logic, sleeve architecture, continuous draped panels, hem behavior, stripe order, stitch texture, "
        "set preservation, and garment readability under the new pose/camera/scene. "
        "Return JSON only."
    )


def _derive_verdict(
    *,
    stage: str,
    garment_fidelity: float,
    structure_fidelity: float,
    set_fidelity: float,
    issue_codes: list[str],
) -> str:
    thresholds = _STAGE_THRESHOLDS.get(stage, _STAGE_THRESHOLDS["stage2"])
    issue_set = set(issue_codes)

    if issue_set & _HARD_ISSUES:
        return "hard_fail"
    if (
        garment_fidelity < thresholds["hard_garment"]
        or structure_fidelity < thresholds["hard_structure"]
        or set_fidelity < thresholds["hard_set"]
    ):
        return "hard_fail"
    if issue_set & _SOFT_ISSUES:
        return "soft_fail"
    if (
        garment_fidelity < thresholds["soft_garment"]
        or structure_fidelity < thresholds["soft_structure"]
        or set_fidelity < thresholds["soft_set"]
    ):
        return "soft_fail"
    return "pass"


def _summarize_score(
    *,
    garment_fidelity: float,
    structure_fidelity: float,
    texture_fidelity: float,
    set_fidelity: float,
    readability_score: float,
) -> float:
    weighted = (
        0.40 * structure_fidelity
        + 0.22 * garment_fidelity
        + 0.16 * texture_fidelity
        + 0.14 * set_fidelity
        + 0.08 * readability_score
    )
    return round(min(garment_fidelity, weighted), 3)




def classify_stage2_repair_strategy(
    gate_result: Optional[dict[str, Any]],
) -> dict[str, Any]:
    gate = gate_result or {}
    if not gate.get("available"):
        return {"mode": "none", "issue_codes": [], "reason": "gate_unavailable"}

    verdict = str(gate.get("verdict", "") or "").strip().lower()
    issue_codes = [str(item).strip().lower() for item in (gate.get("issue_codes") or []) if str(item).strip()]
    issue_set = set(issue_codes)
    texture_fidelity = _clamp_score(gate.get("texture_fidelity"))
    readability_score = _clamp_score(gate.get("readability_score"))

    if verdict == "pass":
        polish_codes: list[str] = []
        if texture_fidelity and texture_fidelity < _LOCALIZED_POLISH_TEXTURE_THRESHOLD:
            polish_codes.append("texture_pattern_drift")
        if readability_score and readability_score < _LOCALIZED_POLISH_READABILITY_THRESHOLD:
            polish_codes.append("low_garment_readability")
        if polish_codes:
            return {
                "mode": "targeted_repair",
                "issue_codes": polish_codes,
                "reason": "pass_but_polishable",
            }
        return {"mode": "none", "issue_codes": issue_codes, "reason": "gate_pass"}
    if not issue_codes:
        return {"mode": "full_retry", "issue_codes": issue_codes, "reason": "missing_issue_codes"}
    if issue_set & _LOCALIZED_REPAIR_BLOCKERS:
        return {
            "mode": "full_retry",
            "issue_codes": issue_codes,
            "reason": "structural_or_occlusion_issue",
        }

    localized_codes = [code for code in issue_codes if code in _LOCALIZED_REPAIR_ISSUES]
    if verdict == "soft_fail" and localized_codes and set(issue_codes).issubset(_LOCALIZED_REPAIR_ISSUES):
        return {
            "mode": "targeted_repair",
            "issue_codes": localized_codes,
            "reason": "localized_surface_or_readability_drift",
        }

    return {"mode": "full_retry", "issue_codes": issue_codes, "reason": "mixed_or_nonlocal_failure"}


def build_fidelity_repair_patch(
    *,
    stage: str,
    gate_result: Optional[dict[str, Any]],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
) -> str:
    contract = structural_contract or {}
    set_info = set_detection or {}
    issue_codes = set(str(item).strip().lower() for item in (gate_result or {}).get("issue_codes", []) or [])
    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    front = str(contract.get("front_opening", "") or "").strip().lower()
    hem = str(contract.get("hem_shape", "") or "").strip().lower()
    volume = str(contract.get("silhouette_volume", "") or "").strip().lower()
    edge_contour = str(contract.get("edge_contour", "") or "").strip().lower()
    drop_profile = str(contract.get("drop_profile", "") or "").strip().lower()
    opening_continuity = str(contract.get("opening_continuity", "") or "").strip().lower()
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
    patches: list[str] = []

    if subtype == "ruana_wrap" or issue_codes & {"wrong_subtype", "closed_front_error", "wrong_opening_logic"}:
        patches.append(
            "Keep the garment as an open-front ruana wrap with continuous front edges and continuous draped side panels; do not reinterpret it as a cardigan, pullover, sweater, or closed poncho body."
        )
    if front == "open":
        patches.append("Keep the front visibly open from neckline to hem edge.")
    if sleeve == "cape_like" or issue_codes & {"invented_sleeve_slit", "invented_sleeves"}:
        patches.append(
            "Do not invent separate sewn sleeves, tailored armholes, or vertical sleeve slits; the arm coverage must come from the same continuous draped panel."
        )
    if volume:
        patches.append(f"Preserve the {volume.replace('_', ' ')} silhouette and drape.")
    if hem:
        patches.append(f"Keep the {hem.replace('_', ' ')} hem behavior unchanged.")
    if edge_contour == "clean":
        patches.append("Keep the outer garment border clean and even; do not introduce wavy or scalloped edge distortion.")
    elif edge_contour == "soft_curve":
        patches.append("Keep the outer garment border smooth with a continuous soft curve; do not exaggerate ripples or scallops.")
    elif edge_contour in {"undulating", "scalloped", "angular"}:
        patches.append(f"Keep the outer garment border {edge_contour.replace('_', ' ')} exactly as in the references.")
    if drop_profile in {"side_drop", "cocoon_side_drop"}:
        patches.append("Keep the longest visible fall on the outer side silhouette, not on the folded inner front edge.")
    elif drop_profile == "high_low":
        patches.append("Keep the high-low outline distribution unchanged.")
    if opening_continuity == "continuous":
        patches.append("Keep the neckline-to-front opening as one continuous uninterrupted edge.")
    elif opening_continuity == "lapel_like":
        patches.append("Keep the opening edge reading as a lapel-like break rather than a continuous wrap edge.")
    if issue_codes & {"texture_pattern_drift", "stripe_order_drift", "color_tone_drift"}:
        patches.append("Match stripe order, stripe scale, yarn tones, stitch texture, and surface relief exactly to the references.")
    if must_include_labels and (issue_codes & {"set_piece_lost"} or str(set_info.get("set_lock_mode", "off") or "off").strip().lower() != "off"):
        label_text = ", ".join(must_include_labels[:3])
        patches.append(
            f"Preserve the coordinated set members as separate product pieces: {label_text}. Keep their textile DNA matched to the references."
        )
    if "scarf" in must_include_keys:
        patches.append("Preserve the matching scarf as part of the same knit set with the same stripe order, yarn tones, and texture.")
    if issue_codes & {"low_garment_readability", "pose_over_occlusion"}:
        patches.append("Keep the pose readable with the front opening, side drape, and hem fully legible.")

    model_patch = str((gate_result or {}).get("recommended_prompt_patch", "") or "").strip()
    if model_patch:
        patches.append(model_patch[:260])

    if stage == "stage1":
        patches.append("This is a neutral fidelity base pass, so keep a clean catalog composition and do not stylize around the garment.")
    else:
        patches.append("Keep the art direction fresh, but treat model identity, pose, camera, and environment as the only flexible layers around a locked garment object.")

    return " ".join(dict.fromkeys([item.strip() for item in patches if item and item.strip()]))


def build_targeted_repair_prompt(
    *,
    gate_result: Optional[dict[str, Any]],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
) -> str:
    contract = structural_contract or {}
    set_info = set_detection or {}
    issue_codes = set(str(item).strip().lower() for item in (gate_result or {}).get("issue_codes", []) or [])
    front = str(contract.get("front_opening", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    volume = str(contract.get("silhouette_volume", "") or "").strip().lower()
    hem = str(contract.get("hem_shape", "") or "").strip().lower()
    edge_contour = str(contract.get("edge_contour", "") or "").strip().lower()
    drop_profile = str(contract.get("drop_profile", "") or "").strip().lower()
    opening_continuity = str(contract.get("opening_continuity", "") or "").strip().lower()
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

    corrected_attributes: list[str] = []
    if "texture_pattern_drift" in issue_codes:
        corrected_attributes.append("knit relief, stitch definition, and textile micro-texture")
    if "stripe_order_drift" in issue_codes:
        corrected_attributes.append("stripe order, stripe spacing, and stripe width")
    if "color_tone_drift" in issue_codes:
        corrected_attributes.append("yarn tones and local garment color balance")

    allowed_edits: list[str] = []
    if "texture_pattern_drift" in issue_codes:
        allowed_edits.append("rebuild garment-local knit/textile surface detail only where drift is visible")
    if "stripe_order_drift" in issue_codes:
        allowed_edits.append("correct stripe sequence and stripe sizing only on the garment")
    if "color_tone_drift" in issue_codes:
        allowed_edits.append("correct garment yarn tones and local garment color balance only")
    if "low_garment_readability" in issue_codes:
        allowed_edits.append(
            "increase garment readability through local edge clarity and front-panel separation without reframing"
        )
    if not allowed_edits:
        allowed_edits.append("apply garment-only micro-corrections in visible drift regions")

    patches: list[str] = [
        "Localized garment-only fidelity correction on an already successful fashion image.",
        "Goal: Correct only visible garment regions that drifted from the references.",
        "Priority rule: Keep current garment geometry and all non-garment elements unchanged.",
        "Keep unchanged: model identity, facial features, hair, expression, pose, body proportions, framing, camera perspective/lens feel, background, styling context, and lighting mood.",
        "Do not recompose the scene or move the subject.",
        "Allowed edits: " + "; ".join(allowed_edits) + ".",
    ]
    if corrected_attributes:
        patches.append(
            "Use references as the source of truth only for these corrected garment-local attributes: "
            + ", ".join(corrected_attributes)
            + "."
        )

    if volume:
        patches.append(f"Keep the {volume.replace('_', ' ')} silhouette unchanged.")
    if hem:
        patches.append(f"Keep the {hem.replace('_', ' ')} hem behavior unchanged.")
    if edge_contour:
        patches.append(f"Keep the {edge_contour.replace('_', ' ')} outer edge contour unchanged.")
    if drop_profile in {"side_drop", "cocoon_side_drop"}:
        patches.append("Keep the longest visible fall on the outer side silhouette.")
    elif drop_profile == "high_low":
        patches.append("Keep the high-low outline distribution unchanged.")
    if opening_continuity == "continuous":
        patches.append("Keep the neckline-to-front opening as one continuous uninterrupted edge.")
    elif opening_continuity == "lapel_like":
        patches.append("Keep the opening edge as a lapel-like break and do not smooth it into a continuous wrap edge.")

    if front == "open":
        patches.append("Keep the front opening visible and unchanged.")
    elif front == "closed":
        patches.append("Keep the front closed and uninterrupted with no extra inner layer appearing.")

    if sleeve == "cape_like":
        patches.append("Keep the cape-like panel architecture unchanged and do not create separate sleeves.")
    elif sleeve == "dolman_batwing":
        patches.append("Keep the dolman or batwing sleeve geometry unchanged.")

    if must_include_labels:
        label_text = ", ".join(must_include_labels[:3])
        patches.append(f"If visible, keep these coordinated set members intact and separate: {label_text}.")
    if "scarf" in must_include_keys:
        patches.append("If the matching scarf is visible, keep it present as a separate coordinated knit piece with the same textile DNA.")

    model_patch = str((gate_result or {}).get("recommended_prompt_patch", "") or "").strip()
    if model_patch:
        patch_compact = " ".join(model_patch.split())
        patch_lower = patch_compact.lower()
        patch_is_local_scope = any(token in patch_lower for token in _TARGETED_PATCH_SCOPE_HINTS)
        patch_is_off_scope = any(token in patch_lower for token in _TARGETED_PATCH_FORBIDDEN_HINTS)
        if patch_is_local_scope and not patch_is_off_scope:
            patches.append(patch_compact[:220])

    patches.append("No redesign, no scene-wide edits, and no garment category reinterpretation.")
    return " ".join(dict.fromkeys([item.strip() for item in patches if item and item.strip()]))


def evaluate_visual_fidelity(
    *,
    stage: str,
    reference_images: list[bytes],
    candidate_image_path: str,
    structural_contract: Optional[dict[str, Any]] = None,
    set_detection: Optional[dict[str, Any]] = None,
    prompt: Optional[str] = None,
    base_image_path: Optional[str] = None,
    thinking_budget: int = 64,
) -> dict[str, Any]:
    candidate_path = Path(str(candidate_image_path or "")).expanduser()
    if not candidate_path.exists():
        return {
            "available": False,
            "stage": stage,
            "error": f"candidate_not_found:{candidate_image_path}",
        }

    refs = [img for img in reference_images if isinstance(img, (bytes, bytearray))]
    if not refs:
        return {
            "available": False,
            "stage": stage,
            "error": "missing_reference_images",
        }

    parts: list[types.Part] = [
        types.Part(text=_base_gate_instruction(stage)),
        types.Part(text="Context: " + _gate_context_excerpt(
            stage=stage,
            structural_contract=structural_contract,
            set_detection=set_detection,
            prompt=prompt,
        )),
        types.Part(text="Original garment references:"),
    ]
    for idx, img in enumerate(refs[:4], start=1):
        parts.append(types.Part(text=f"Reference {idx}"))
        parts.append(
            types.Part(
                inline_data=types.Blob(mime_type=_mime_from_bytes(bytes(img)), data=bytes(img)),
                media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
            )
        )

    if stage == "stage2" and base_image_path:
        base_path = Path(str(base_image_path)).expanduser()
        if base_path.exists():
            parts.append(types.Part(text="Selected stage-1 base image:"))
            parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type=_mime_from_path(base_path), data=base_path.read_bytes()),
                    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                )
            )

    parts.append(types.Part(text="Candidate image to evaluate:"))
    parts.append(
        types.Part(
            inline_data=types.Blob(mime_type=_mime_from_path(candidate_path), data=candidate_path.read_bytes()),
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
        )
    )

    try:
        response = generate_structured_json(
            parts=parts,
            schema=FIDELITY_GATE_SCHEMA,
            temperature=0.1,
            max_tokens=1200,
            thinking_budget=thinking_budget,
        )
        raw = _decode_agent_response(response)
    except Exception as exc:
        return {
            "available": False,
            "stage": stage,
            "error": str(exc),
        }

    garment_fidelity = _clamp_score(raw.get("garment_fidelity"))
    structure_fidelity = _clamp_score(raw.get("structure_fidelity"))
    texture_fidelity = _clamp_score(raw.get("texture_fidelity"))
    set_fidelity = _clamp_score(raw.get("set_fidelity", 1.0))
    readability_score = _clamp_score(raw.get("readability_score"))
    active_set_expected = bool(
        get_set_member_labels(
            set_detection,
            include_policies={"must_include"},
            member_classes={"garment", "coordinated_accessory"},
            active_only=True,
            exclude_primary_piece=True,
        )
    )
    if not active_set_expected:
        set_fidelity = 1.0
    raw_issue_sources = list(raw.get("issue_codes") or [])
    summary_text = str(raw.get("summary", "") or "").strip()
    issue_codes = _normalize_issue_codes(raw_issue_sources)
    for code in _negative_summary_issue_codes(summary_text):
        if code not in issue_codes:
            issue_codes.append(code)
    issue_codes = _reconcile_issue_codes(
        issue_codes,
        summary_text=summary_text,
        set_fidelity=set_fidelity,
        structure_fidelity=structure_fidelity,
        active_set_expected=active_set_expected,
    )
    verdict = _derive_verdict(
        stage=stage,
        garment_fidelity=garment_fidelity,
        structure_fidelity=structure_fidelity,
        set_fidelity=set_fidelity,
        issue_codes=issue_codes,
    )
    fidelity_score = _summarize_score(
        garment_fidelity=garment_fidelity,
        structure_fidelity=structure_fidelity,
        texture_fidelity=texture_fidelity,
        set_fidelity=set_fidelity,
        readability_score=readability_score,
    )

    return {
        "available": True,
        "stage": stage,
        "verdict": verdict,
        "fidelity_score": fidelity_score,
        "garment_fidelity": garment_fidelity,
        "structure_fidelity": structure_fidelity,
        "texture_fidelity": texture_fidelity,
        "set_fidelity": set_fidelity,
        "readability_score": readability_score,
        "issue_codes": issue_codes,
        "summary": summary_text,
        "recommended_prompt_patch": str(raw.get("recommended_prompt_patch", "") or "").strip(),
        "retry_recommended": verdict != "pass",
    }


# ── Seleção de candidatos por gate score ─────────────────────────────────

def stage1_selection_key(
    assessment: dict[str, Any],
    gate_result: Optional[dict[str, Any]],
) -> tuple[float, float, float, float]:
    """Chave de ordenação para selecionar o melhor candidato stage 1.

    Retorna uma tupla comparável: maior = melhor candidato.
    Se gate está disponível, prioriza verdict > fidelity_score > structure > técnico.
    Caso contrário, usa candidate_score + technical_score.
    """
    if gate_result and gate_result.get("available"):
        verdict_rank = {
            "pass": 2.0,
            "soft_fail": 1.0,
            "hard_fail": 0.0,
        }.get(str(gate_result.get("verdict", "") or "").strip().lower(), 0.0)
        return (
            verdict_rank,
            float(gate_result.get("fidelity_score", 0.0) or 0.0),
            float(gate_result.get("structure_fidelity", 0.0) or 0.0),
            float(assessment.get("technical_score", 0.0) or 0.0),
        )
    return (
        float(assessment.get("candidate_score", 0.0) or 0.0),
        float(assessment.get("technical_score", 0.0) or 0.0),
        0.0,
        0.0,
    )


def pick_best_stage1_candidate(
    candidates: list[dict[str, Any]],
    stage1_prompt: str,
    classifier_summary: dict[str, Any],
    *,
    assess_fn: Any,
    gate_policy: Optional[dict[str, Any]] = None,
    gate_reference_bytes: Optional[list[bytes]] = None,
    structural_contract: Optional[dict[str, Any]] = None,
    set_detection: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    """Avalia todos os candidatos stage 1 e retorna (melhor, assessments, índice 1-based).

    Args:
        assess_fn: função de avaliação (pipeline_effectiveness.assess_generated_image).
                   Injetada para evitar dependência circular.
    """
    assessments: list[dict[str, Any]] = []
    best_idx = 0
    best_key = (-1.0, -1.0, -1.0, -1.0)
    gate_enabled = bool((gate_policy or {}).get("enabled"))
    judge_refs = list(gate_reference_bytes or [])

    for idx, candidate in enumerate(candidates):
        candidate_path = str(candidate.get("path", "") or "")
        assessment = assess_fn(candidate_path, stage1_prompt, classifier_summary)
        gate_result = None
        if gate_enabled and judge_refs:
            gate_result = evaluate_visual_fidelity(
                stage="stage1",
                reference_images=judge_refs,
                candidate_image_path=candidate_path,
                structural_contract=structural_contract,
                set_detection=set_detection,
                prompt=stage1_prompt,
            )
        assessments.append(
            {
                "index": idx + 1,
                "filename": candidate.get("filename"),
                "url": candidate.get("url"),
                "path": candidate.get("path"),
                "assessment": assessment,
                "fidelity_gate": gate_result,
            }
        )
        key = stage1_selection_key(assessment, gate_result)
        if key > best_key:
            best_key = key
            best_idx = idx

    return candidates[best_idx], assessments, best_idx + 1
