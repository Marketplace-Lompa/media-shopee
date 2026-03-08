"""
Normalização e utilitários do Modo Guiado (V1 Lean).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

AGE_RANGES = {"18-24", "25-34", "35-44", "45+"}
SET_MODES = {"unica", "conjunto"}
SCENE_TYPES = {"interno", "externo"}
POSE_STYLES = {"tradicional", "criativa"}
CAPTURE_DISTANCES = {"distante", "media", "proxima"}
FIDELITY_MODES = {"balanceada", "estrita"}

_COMPONENT_ALIAS = {
    "cardigan/ruana": "cardigan/ruana",
    "cardigan_ruana": "cardigan/ruana",
    "cardigan": "cardigan/ruana",
    "ruana": "cardigan/ruana",
    "cachecol": "cachecol",
    "scarf": "cachecol",
    "top": "top",
    "calça": "calca",
    "calca": "calca",
    "saia": "saia",
}
_COMPONENT_CANONICAL = ["cardigan/ruana", "cachecol", "top", "calca", "saia"]


def _safe_json_loads(raw: str) -> Optional[dict]:
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else None
    except Exception:
        return None


def normalize_guided_brief(raw: Optional[Any]) -> Optional[dict]:
    if raw is None:
        return None

    payload: Optional[dict]
    if isinstance(raw, str):
        txt = raw.strip()
        if not txt:
            return None
        payload = _safe_json_loads(txt)
    elif isinstance(raw, dict):
        payload = raw
    else:
        return None

    if not payload:
        return None

    enabled = bool(payload.get("enabled", True))
    if not enabled:
        return None

    model = payload.get("model", {}) or {}
    garment = payload.get("garment", {}) or {}
    scene = payload.get("scene", {}) or {}
    pose = payload.get("pose", {}) or {}
    capture = payload.get("capture", {}) or {}

    age_range = str(model.get("age_range", "25-34")).strip()
    if age_range not in AGE_RANGES:
        age_range = "25-34"

    set_mode = str(garment.get("set_mode", "unica")).strip().lower()
    if set_mode not in SET_MODES:
        set_mode = "unica"

    fidelity_mode = str(payload.get("fidelity_mode", "balanceada")).strip().lower()
    if fidelity_mode not in FIDELITY_MODES:
        fidelity_mode = "balanceada"

    raw_components = garment.get("components", []) or []
    components: List[str] = []
    if isinstance(raw_components, list):
        for item in raw_components:
            alias = _COMPONENT_ALIAS.get(str(item).strip().lower())
            if alias and alias not in components:
                components.append(alias)
    components = [c for c in _COMPONENT_CANONICAL if c in components]

    scene_type = str(scene.get("type", "externo")).strip().lower()
    if scene_type not in SCENE_TYPES:
        scene_type = "externo"

    pose_style = str(pose.get("style", "tradicional")).strip().lower()
    if pose_style not in POSE_STYLES:
        pose_style = "tradicional"

    capture_distance = str(capture.get("distance", "media")).strip().lower()
    if capture_distance not in CAPTURE_DISTANCES:
        capture_distance = "media"

    return {
        "enabled": True,
        "model": {"age_range": age_range},
        "garment": {
            "set_mode": set_mode,
            "components": components if set_mode == "conjunto" else [],
        },
        "scene": {"type": scene_type},
        "pose": {"style": pose_style},
        "capture": {"distance": capture_distance},
        "fidelity_mode": fidelity_mode,
    }


def guided_capture_to_shot(distance: str) -> Optional[str]:
    if distance == "distante":
        return "wide"
    if distance == "media":
        return "medium"
    if distance == "proxima":
        return "close-up"
    return None


def guided_force_grounding_floor(brief: Optional[dict], has_images: bool) -> bool:
    if not brief or not has_images:
        return False
    set_mode = ((brief.get("garment") or {}).get("set_mode") or "").strip().lower()
    fidelity_mode = (brief.get("fidelity_mode") or "").strip().lower()
    return set_mode == "conjunto" or fidelity_mode == "estrita"


def guided_summary(brief: Optional[dict], shot_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not brief:
        return None
    garment = brief.get("garment", {}) or {}
    model = brief.get("model", {}) or {}
    scene = brief.get("scene", {}) or {}
    pose = brief.get("pose", {}) or {}
    capture = brief.get("capture", {}) or {}
    return {
        "applied": True,
        "shot_type": shot_type or guided_capture_to_shot(str(capture.get("distance", "")).lower()) or "medium",
        "set_mode": garment.get("set_mode", "unica"),
        "components": garment.get("components", []) or [],
        "age_range": model.get("age_range", "25-34"),
        "scene": scene.get("type", "externo"),
        "pose": pose.get("style", "tradicional"),
    }
