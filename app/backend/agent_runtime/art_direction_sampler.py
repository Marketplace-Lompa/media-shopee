"""
Art direction sampler experimental para a etapa 2 do fluxo two-pass.

Objetivo:
- manter stage 1 congelado e fiel a peca
- parametrizar stage 2 com um objeto pequeno e equilibrado
- evitar presets fixos e repeticao obvia de modelo/cenario
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from agent_runtime.casting_engine import (
    reset_brazilian_casting_state,
    select_brazilian_casting_profile,
)
from config import OUTPUTS_DIR

_STATE_FILE = OUTPUTS_DIR / "art_direction_sampler_state.json"
_DEFAULT_STATE = {
    "history": [],
    "cursor": 0,
}

_SCENE_FAMILIES: list[dict[str, Any]] = [
    {
        "id": "br_recife_balcony",
        "label": "BR Recife Balcony",
        "description": "airy Recife apartment balcony with textured plaster wall, woven chair, potted plants, and an urban-coastal skyline glimpse",
        "tags": ["lifestyle", "marketplace", "balcony", "outdoor", "warm"],
        "camera_ids": ["phone_clean", "canon_balanced"],
        "lighting_ids": ["coastal_late_morning"],
        "styling_ids": ["off_white_shorts", "soft_blue_trousers"],
        "pose_ids": ["standing_3q_relaxed", "front_relaxed_hold"],
    },
    {
        "id": "br_pinheiros_living",
        "label": "BR Pinheiros Living",
        "description": "lived-in Pinheiros apartment living room with books, linen armchair, shelf styling, and soft plant shadows",
        "tags": ["lifestyle", "premium", "indoor", "apartment"],
        "camera_ids": ["canon_balanced", "phone_clean"],
        "lighting_ids": ["mixed_window_lamp", "window_daylight"],
        "styling_ids": ["soft_blue_trousers", "indigo_jeans"],
        "pose_ids": ["standing_full_shift", "front_relaxed_hold"],
    },
    {
        "id": "br_curitiba_cafe",
        "label": "BR Curitiba Cafe",
        "description": "neighborhood coffee shop in Curitiba with concrete floor, wood counter, pastry case, and softly busy background depth",
        "tags": ["lifestyle", "cafe", "urban", "authentic"],
        "camera_ids": ["fujifilm_candid", "phone_clean"],
        "lighting_ids": ["overcast_cafe"],
        "styling_ids": ["indigo_jeans", "soft_blue_trousers"],
        "pose_ids": ["paused_mid_step", "standing_3q_relaxed"],
    },
    {
        "id": "br_showroom_sp",
        "label": "BR Sao Paulo Showroom",
        "description": "Brazilian premium showroom in Sao Paulo with softly textured neutral walls, pale stone floor, and minimal decor",
        "tags": ["catalog", "premium", "showroom", "indoor"],
        "camera_ids": ["canon_balanced"],
        "lighting_ids": ["clean_showroom"],
        "styling_ids": ["soft_blue_trousers"],
        "pose_ids": ["standing_full_shift", "front_relaxed_hold"],
    },
]

_POSE_FAMILIES: list[dict[str, Any]] = [
    {
        "id": "standing_3q_relaxed",
        "label": "Standing 3Q Relaxed",
        "angle_description": "3/4 standing angle with one shoulder slightly forward and direct eye contact",
        "pose_description": "Use a relaxed standing pose with one hand lightly touching the garment opening and full garment visibility.",
        "model_hero_pose": "relaxed standing pose with one hand lightly touching the garment opening",
        "tags": ["stable", "lifestyle", "marketplace"],
    },
    {
        "id": "front_relaxed_hold",
        "label": "Front Relaxed Hold",
        "angle_description": "eye-level front-facing full-body framing with clean garment readability",
        "pose_description": "Use a calm front-facing standing pose with both arms relaxed and the garment fully visible.",
        "model_hero_pose": "calm front-facing standing pose with both arms relaxed and the garment fully visible",
        "tags": ["stable", "catalog", "premium"],
    },
    {
        "id": "standing_full_shift",
        "label": "Standing Full Shift",
        "angle_description": "eye-level full-body framing with a slight weight shift to one leg",
        "pose_description": "Use a calm standing pose with a subtle hip shift, arms relaxed, and full garment visibility.",
        "model_hero_pose": "calm standing pose with a subtle hip shift and arms relaxed",
        "tags": ["stable", "premium"],
    },
    {
        "id": "paused_mid_step",
        "label": "Paused Mid Step",
        "angle_description": "slight low-angle environmental shot with a casual mid-step pause",
        "pose_description": "Use a natural paused walking pose with one hand adjusting the garment edge while preserving full garment readability.",
        "model_hero_pose": "natural paused walking pose with one hand adjusting the garment edge",
        "tags": ["lifestyle", "authentic", "movement"],
    },
]

_CAMERA_PROFILES: list[dict[str, Any]] = [
    {
        "id": "phone_clean",
        "label": "Phone Clean",
        "device": "iPhone 15 Pro",
        "lens": "48mm equivalent",
        "grain_level": "500",
        "tags": ["lifestyle", "marketplace", "authentic"],
    },
    {
        "id": "canon_balanced",
        "label": "Canon Balanced",
        "device": "Canon R6",
        "lens": "50mm lens",
        "grain_level": "800",
        "tags": ["premium", "balanced", "indoor"],
    },
    {
        "id": "fujifilm_candid",
        "label": "Fujifilm Candid",
        "device": "Fujifilm X-T4",
        "lens": "35mm lens",
        "grain_level": "1000",
        "tags": ["cafe", "street", "lifestyle"],
    },
]

_LIGHTING_PROFILES: list[dict[str, Any]] = [
    {
        "id": "coastal_late_morning",
        "label": "Coastal Late Morning",
        "description": "bright coastal late-morning daylight with warm ambient reflections",
        "tags": ["warm", "balcony", "outdoor"],
    },
    {
        "id": "mixed_window_lamp",
        "label": "Mixed Window Lamp",
        "description": "mixed window daylight and warm floor-lamp spill",
        "tags": ["indoor", "premium", "lived-in"],
    },
    {
        "id": "window_daylight",
        "label": "Window Daylight",
        "description": "soft Brazilian apartment daylight from a large side window with subtle warm room bounce",
        "tags": ["indoor", "clean", "lifestyle"],
    },
    {
        "id": "overcast_cafe",
        "label": "Overcast Cafe",
        "description": "cool overcast street daylight mixing with warm cafe practicals",
        "tags": ["cafe", "authentic", "mixed"],
    },
    {
        "id": "clean_showroom",
        "label": "Clean Showroom",
        "description": "clean diffused daylight with neutral showroom bounce and gentle soft shadow falloff",
        "tags": ["catalog", "showroom", "premium"],
    },
]

_STYLING_PROFILES: list[dict[str, Any]] = [
    {
        "id": "off_white_shorts",
        "label": "Off White Shorts",
        "innerwear": "clean white crew-neck tee",
        "bottom": "relaxed off-white tailored shorts",
        "tags": ["warm", "balcony", "marketplace"],
    },
    {
        "id": "soft_blue_trousers",
        "label": "Soft Blue Trousers",
        "innerwear": "clean white crew-neck tee",
        "bottom": "high-waisted soft-blue wide-leg trousers",
        "tags": ["premium", "indoor", "catalog"],
    },
    {
        "id": "indigo_jeans",
        "label": "Indigo Jeans",
        "innerwear": "clean white crew-neck tee",
        "bottom": "dark indigo straight jeans",
        "tags": ["cafe", "urban", "authentic"],
    },
]

_FAMILY_VISUAL_LABELS = {
    "br_afro_modern": "Afro-Brazilian visual profile",
    "br_warm_commercial": "mixed-race Brazilian visual profile",
    "br_mature_elegant": "refined urban Brazilian visual profile",
    "br_minimal_premium": "minimal premium Brazilian visual profile",
    "br_soft_editorial": "soft editorial Brazilian visual profile",
}


def _load_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_state() -> dict[str, Any]:
    state = _load_json(_STATE_FILE, _DEFAULT_STATE)
    if not isinstance(state, dict):
        return dict(_DEFAULT_STATE)
    history = state.get("history", [])
    if not isinstance(history, list):
        history = []
    return {
        "history": history,
        "cursor": int(state.get("cursor", 0) or 0),
    }


def reset_art_direction_state() -> None:
    _save_json(_STATE_FILE, dict(_DEFAULT_STATE))


def reset_art_direction_memory() -> None:
    reset_brazilian_casting_state()
    reset_art_direction_state()


def _stable_int(seed: str) -> int:
    return int(hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8], 16)


def _normalize_age_value(age_text: str) -> str:
    digits = re.findall(r"\d+", age_text or "")
    if not digits:
        return "30"
    if len(digits) >= 2:
        return str((int(digits[0]) + int(digits[1])) // 2)
    return digits[0]


def _affinity(text: str, tags: list[str]) -> int:
    lowered = text.lower()
    score = 0
    for tag in tags:
        if tag in lowered:
            score += 2
    if "marketplace" in lowered and "marketplace" in tags:
        score += 2
    if "premium" in lowered and "premium" in tags:
        score += 2
    if "lifestyle" in lowered and "lifestyle" in tags:
        score += 2
    if "cafe" in lowered and "cafe" in tags:
        score += 2
    if any(k in lowered for k in ("apartamento", "living", "indoor")) and "indoor" in tags:
        score += 1
    if any(k in lowered for k in ("varanda", "balcony", "outdoor")) and "outdoor" in tags:
        score += 1
    return score


def _pick_item(
    *,
    state: dict[str, Any],
    pool: list[dict[str, Any]],
    history_key: str,
    seed_hint: str,
    user_prompt: Optional[str] = None,
    allowed_ids: Optional[list[str]] = None,
) -> dict[str, Any]:
    candidates = list(pool)
    if allowed_ids:
        allowed = set(allowed_ids)
        candidates = [item for item in candidates if item["id"] in allowed] or candidates

    recent = [item for item in state.get("history", []) if isinstance(item, dict)][-8:]
    recent_counts: dict[str, int] = {}
    for item in recent:
        item_id = str(item.get(history_key, "") or "")
        if item_id:
            recent_counts[item_id] = recent_counts.get(item_id, 0) + 1

    seed = _stable_int(seed_hint)
    cursor = int(state.get("cursor", 0) or 0)
    text = str(user_prompt or "")

    candidates.sort(
        key=lambda item: (
            recent_counts.get(item["id"], 0),
            -_affinity(text, list(item.get("tags", []))),
            item["id"],
        )
    )
    least_count = recent_counts.get(candidates[0]["id"], 0) if candidates else 0
    filtered = [
        item for item in candidates
        if recent_counts.get(item["id"], 0) == least_count
    ] or candidates
    filtered.sort(key=lambda item: (-_affinity(text, list(item.get("tags", []))), item["id"]))
    return filtered[(cursor + seed) % len(filtered)]


def sample_art_direction(
    *,
    seed_hint: str = "",
    user_prompt: Optional[str] = None,
    commit: bool = True,
) -> dict[str, Any]:
    state = _safe_state()

    casting = select_brazilian_casting_profile(
        seed_hint=f"{seed_hint}:casting",
        user_prompt=user_prompt,
        commit=commit,
    )
    scene = _pick_item(
        state=state,
        pool=_SCENE_FAMILIES,
        history_key="scene_id",
        seed_hint=f"{seed_hint}:scene",
        user_prompt=user_prompt,
    )
    pose = _pick_item(
        state=state,
        pool=_POSE_FAMILIES,
        history_key="pose_id",
        seed_hint=f"{seed_hint}:pose",
        user_prompt=user_prompt,
        allowed_ids=list(scene.get("pose_ids", [])),
    )
    camera = _pick_item(
        state=state,
        pool=_CAMERA_PROFILES,
        history_key="camera_id",
        seed_hint=f"{seed_hint}:camera",
        user_prompt=user_prompt,
        allowed_ids=list(scene.get("camera_ids", [])),
    )
    lighting = _pick_item(
        state=state,
        pool=_LIGHTING_PROFILES,
        history_key="lighting_id",
        seed_hint=f"{seed_hint}:lighting",
        user_prompt=user_prompt,
        allowed_ids=list(scene.get("lighting_ids", [])),
    )
    styling = _pick_item(
        state=state,
        pool=_STYLING_PROFILES,
        history_key="styling_id",
        seed_hint=f"{seed_hint}:styling",
        user_prompt=user_prompt,
        allowed_ids=list(scene.get("styling_ids", [])),
    )

    result = {
        "casting_profile": casting,
        "scene": scene,
        "pose": pose,
        "camera": camera,
        "lighting": lighting,
        "styling": styling,
        "model_visual_label": _FAMILY_VISUAL_LABELS.get(
            str(casting.get("family_id", "") or ""),
            "Brazilian visual profile",
        ),
        "age_years": _normalize_age_value(str(casting.get("age", "") or "")),
        "summary": {
            "casting_family": casting.get("family_id"),
            "scene_family": scene.get("id"),
            "pose_family": pose.get("id"),
            "camera_profile": camera.get("id"),
            "lighting_profile": lighting.get("id"),
            "styling_profile": styling.get("id"),
        },
    }

    if commit:
        history = list(state.get("history", []))
        history.append(
            {
                "scene_id": scene["id"],
                "pose_id": pose["id"],
                "camera_id": camera["id"],
                "lighting_id": lighting["id"],
                "styling_id": styling["id"],
                "timestamp": int(time.time()),
            }
        )
        history = history[-8:]
        _save_json(
            _STATE_FILE,
            {
                "history": history,
                "cursor": int(state.get("cursor", 0) or 0) + 1,
            },
        )

    return result
