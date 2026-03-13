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
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Optional

# Adjustment to ensure backend is in sys.path for direct executions and linters
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from agent_runtime.casting_engine import (  # type: ignore
    commit_brazilian_casting_profile,
    reset_brazilian_casting_state,
    select_brazilian_casting_profile,
)
from config import OUTPUTS_DIR  # type: ignore

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
        "tags": ["lifestyle", "marketplace", "balcony", "outdoor", "warm", "brazilian"],
        "camera_ids": ["phone_clean", "sony_documentary", "canon_balanced"],
        "lighting_ids": ["coastal_late_morning", "open_shade_daylight"],
        "styling_ids": ["off_white_shorts", "light_linen_pants", "soft_blue_trousers"],
        "pose_ids": ["standing_3q_relaxed", "walking_stride_controlled", "paused_mid_step", "twist_step_forward"],
    },
    {
        "id": "br_pinheiros_living",
        "label": "BR Pinheiros Living",
        "description": "lived-in Pinheiros apartment living room with books, linen armchair, shelf styling, and soft plant shadows",
        "tags": ["lifestyle", "premium", "indoor", "apartment", "brazilian"],
        "camera_ids": ["canon_balanced", "sony_documentary", "phone_clean"],
        "lighting_ids": ["mixed_window_lamp", "window_daylight"],
        "styling_ids": ["soft_blue_trousers", "indigo_jeans", "black_tailored_pants"],
        "pose_ids": ["standing_full_shift", "front_relaxed_hold", "soft_wall_lean", "hand_adjust_neckline"],
    },
    {
        "id": "br_curitiba_cafe",
        "label": "BR Curitiba Cafe",
        "description": "neighborhood coffee shop in Curitiba with concrete floor, wood counter, pastry case, and softly busy background depth",
        "tags": ["lifestyle", "cafe", "urban", "authentic", "indoor", "brazilian"],
        "camera_ids": ["fujifilm_candid", "nikon_street", "phone_clean"],
        "lighting_ids": ["overcast_cafe", "mixed_window_lamp"],
        "styling_ids": ["indigo_jeans", "beige_midi_skirt", "light_linen_pants"],
        "pose_ids": ["paused_mid_step", "standing_3q_relaxed", "half_turn_lookback", "twist_step_forward"],
    },
    {
        "id": "br_showroom_sp",
        "label": "BR Sao Paulo Showroom",
        "description": "Brazilian premium showroom in Sao Paulo with softly textured neutral walls, pale stone floor, and minimal decor",
        "tags": ["catalog", "premium", "showroom", "indoor", "brazilian"],
        "camera_ids": ["canon_balanced", "sony_documentary"],
        "lighting_ids": ["clean_showroom"],
        "styling_ids": ["soft_blue_trousers", "black_tailored_pants"],
        "pose_ids": ["standing_full_shift", "front_relaxed_hold", "contrapposto_editorial", "hand_adjust_neckline"],
    },
    {
        "id": "br_salvador_colonial_street",
        "label": "BR Salvador Colonial Street",
        "description": "historic Salvador street with pastel facades, stone pavement, subtle local texture, and soft depth behind the subject",
        "tags": ["lifestyle", "outdoor", "urban", "authentic", "brazilian", "colorful"],
        "camera_ids": ["nikon_street", "fujifilm_candid"],
        "lighting_ids": ["golden_hour_soft", "open_shade_daylight"],
        "styling_ids": ["off_white_shorts", "indigo_jeans", "beige_midi_skirt"],
        "pose_ids": ["walking_stride_controlled", "paused_mid_step", "half_turn_lookback", "twist_step_forward"],
    },
    {
        "id": "br_floripa_boardwalk",
        "label": "BR Floripa Boardwalk",
        "description": "Florianopolis boardwalk with dune vegetation, clean horizon, and breathable coastal negative space",
        "tags": ["lifestyle", "outdoor", "coastal", "marketplace", "brazilian"],
        "camera_ids": ["sony_documentary", "phone_clean"],
        "lighting_ids": ["coastal_late_morning", "cloudy_tropical"],
        "styling_ids": ["light_linen_pants", "off_white_shorts"],
        "pose_ids": ["standing_3q_relaxed", "walking_stride_controlled", "standing_full_shift", "twist_step_forward"],
    },
    {
        "id": "br_brasilia_concrete_gallery",
        "label": "BR Brasilia Concrete Gallery",
        "description": "Brasilia modernist concrete gallery with long perspective lines, open sky fill light, and elegant architectural rhythm",
        "tags": ["premium", "outdoor", "architecture", "editorial", "brazilian"],
        "camera_ids": ["canon_balanced", "sony_documentary"],
        "lighting_ids": ["open_shade_daylight", "cloudy_tropical"],
        "styling_ids": ["black_tailored_pants", "soft_blue_trousers"],
        "pose_ids": ["contrapposto_editorial", "half_turn_lookback", "standing_full_shift", "hand_adjust_neckline"],
    },
    {
        "id": "br_bh_rooftop_lounge",
        "label": "BR Belo Horizonte Rooftop",
        "description": "Belo Horizonte rooftop lounge with warm stone textures, distant skyline layers, and elegant sunset ambience",
        "tags": ["premium", "outdoor", "rooftop", "lifestyle", "brazilian"],
        "camera_ids": ["sony_documentary", "canon_balanced"],
        "lighting_ids": ["golden_hour_soft", "open_shade_daylight"],
        "styling_ids": ["beige_midi_skirt", "black_tailored_pants", "light_linen_pants"],
        "pose_ids": ["standing_3q_relaxed", "contrapposto_editorial", "soft_wall_lean", "twist_step_forward"],
    },
    {
        "id": "br_porto_alegre_bookstore",
        "label": "BR Porto Alegre Bookstore",
        "description": "curated bookstore in Porto Alegre with wood shelving, warm practical lights, and soft aisle depth",
        "tags": ["indoor", "lifestyle", "premium", "authentic", "brazilian"],
        "camera_ids": ["fujifilm_candid", "canon_balanced"],
        "lighting_ids": ["mixed_window_lamp", "window_daylight"],
        "styling_ids": ["indigo_jeans", "black_tailored_pants", "beige_midi_skirt"],
        "pose_ids": ["front_relaxed_hold", "soft_wall_lean", "half_turn_lookback", "hand_adjust_neckline"],
    },
    {
        "id": "br_rio_art_loft",
        "label": "BR Rio Art Loft",
        "description": "Rio de Janeiro artist loft with textured plaster, large industrial windows, and restrained design objects",
        "tags": ["indoor", "editorial", "premium", "lifestyle", "brazilian"],
        "camera_ids": ["sony_documentary", "canon_balanced", "fujifilm_candid"],
        "lighting_ids": ["window_daylight", "mixed_window_lamp"],
        "styling_ids": ["black_tailored_pants", "soft_blue_trousers", "light_linen_pants"],
        "pose_ids": ["contrapposto_editorial", "standing_full_shift", "front_relaxed_hold", "hand_adjust_neckline", "twist_step_forward"],
    },
]

_POSE_FAMILIES: list[dict[str, Any]] = [
    {
        "id": "standing_3q_relaxed",
        "label": "Standing 3Q Relaxed",
        "angle_description": "3/4 standing angle with one shoulder slightly forward and direct eye contact",
        "pose_description": "Use a relaxed standing pose with one hand lightly touching the garment opening and full garment visibility.",
        "model_hero_pose": "relaxed standing pose with one hand lightly touching the garment opening",
        "tags": ["stable", "lifestyle", "marketplace", "catalog", "indoor", "outdoor"],
    },
    {
        "id": "front_relaxed_hold",
        "label": "Front Relaxed Hold",
        "angle_description": "eye-level front-facing full-body framing with clean garment readability",
        "pose_description": "Use a calm front-facing standing pose with both arms relaxed and the garment fully visible.",
        "model_hero_pose": "calm front-facing standing pose with both arms relaxed and the garment fully visible",
        "tags": ["stable", "catalog", "premium", "indoor"],
    },
    {
        "id": "standing_full_shift",
        "label": "Standing Full Shift",
        "angle_description": "eye-level full-body framing with a slight weight shift to one leg",
        "pose_description": "Use a calm standing pose with a subtle hip shift, arms relaxed, and full garment visibility.",
        "model_hero_pose": "calm standing pose with a subtle hip shift and arms relaxed",
        "tags": ["stable", "premium", "catalog", "indoor", "outdoor"],
    },
    {
        "id": "paused_mid_step",
        "label": "Paused Mid Step",
        "angle_description": "slight low-angle environmental shot with a casual mid-step pause",
        "pose_description": "Use a natural paused walking pose with one hand adjusting the garment edge while preserving full garment readability.",
        "model_hero_pose": "natural paused walking pose with one hand adjusting the garment edge",
        "tags": ["lifestyle", "authentic", "movement", "outdoor", "marketplace"],
    },
    {
        "id": "contrapposto_editorial",
        "label": "Contrapposto Editorial",
        "angle_description": "slightly elevated full-body framing with elegant asymmetry and clean negative space",
        "pose_description": "Use a subtle contrapposto pose, one shoulder softened and one leg forward, while keeping full garment readability.",
        "model_hero_pose": "subtle contrapposto stance with an editorial calm expression",
        "tags": ["editorial", "premium", "stable", "catalog", "indoor", "outdoor"],
    },
    {
        "id": "half_turn_lookback",
        "label": "Half Turn Lookback",
        "angle_description": "three-quarter half-turn framing that reveals front drape and side silhouette simultaneously",
        "pose_description": "Use a controlled half-turn pose with a soft look-back while keeping the garment front and side lines visible.",
        "model_hero_pose": "controlled half-turn stance with soft look-back and relaxed arms",
        "tags": ["editorial", "lifestyle", "movement", "outdoor", "indoor"],
    },
    {
        "id": "walking_stride_controlled",
        "label": "Walking Stride Controlled",
        "angle_description": "eye-level environmental framing with one measured stride and clear garment contour separation",
        "pose_description": "Use a controlled walking stride with natural arm movement while preserving complete garment readability.",
        "model_hero_pose": "measured walking stride with relaxed but confident body language",
        "tags": ["movement", "lifestyle", "marketplace", "outdoor"],
    },
    {
        "id": "soft_wall_lean",
        "label": "Soft Wall Lean",
        "angle_description": "straight-on full-body framing with subtle architectural support and calm vertical posture",
        "pose_description": "Use a gentle wall-lean stance with one foot slightly forward and the garment fully visible from neckline to hem.",
        "model_hero_pose": "gentle wall-lean with soft posture and clear garment display",
        "tags": ["stable", "premium", "lifestyle", "indoor"],
    },
    {
        "id": "twist_step_forward",
        "label": "Twist Step Forward",
        "angle_description": "full-body frame with a subtle torso twist and one controlled step forward",
        "pose_description": "Use a dynamic twist-step pose with open chest orientation and clear readability of garment drape from neckline to hem.",
        "model_hero_pose": "controlled twist-step with one foot forward and relaxed arm flow",
        "tags": ["movement", "lifestyle", "editorial", "outdoor", "marketplace"],
    },
    {
        "id": "hand_adjust_neckline",
        "label": "Hand Adjust Neckline",
        "angle_description": "front three-quarter framing with one hand gently adjusting the neckline or opening edge",
        "pose_description": "Use a natural interaction pose where one hand adjusts garment opening details while preserving full silhouette readability.",
        "model_hero_pose": "front three-quarter stance with one hand adjusting garment opening and calm expression",
        "tags": ["stable", "catalog", "editorial", "indoor", "premium"],
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
    {
        "id": "sony_documentary",
        "label": "Sony Documentary",
        "device": "Sony A7 IV",
        "lens": "55mm lens",
        "grain_level": "640",
        "tags": ["premium", "editorial", "lifestyle", "indoor", "outdoor"],
    },
    {
        "id": "nikon_street",
        "label": "Nikon Street",
        "device": "Nikon Z6 II",
        "lens": "35mm lens",
        "grain_level": "900",
        "tags": ["street", "outdoor", "authentic", "lifestyle"],
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
    {
        "id": "golden_hour_soft",
        "label": "Golden Hour Soft",
        "description": "soft late-afternoon golden light with controlled warm highlights and long natural shadow gradients",
        "tags": ["outdoor", "warm", "lifestyle", "premium"],
    },
    {
        "id": "open_shade_daylight",
        "label": "Open Shade Daylight",
        "description": "clean open-shade daylight with soft contrast and believable neutral skin rendering",
        "tags": ["outdoor", "catalog", "clean", "premium"],
    },
    {
        "id": "cloudy_tropical",
        "label": "Cloudy Tropical",
        "description": "bright overcast tropical daylight with soft wraps, humid atmosphere, and realistic ambient bounce",
        "tags": ["outdoor", "coastal", "authentic", "lifestyle"],
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
    {
        "id": "black_tailored_pants",
        "label": "Black Tailored Pants",
        "innerwear": "clean white fitted tank top",
        "bottom": "black tailored straight-leg trousers",
        "tags": ["premium", "catalog", "indoor", "editorial"],
    },
    {
        "id": "beige_midi_skirt",
        "label": "Beige Midi Skirt",
        "innerwear": "clean white crew-neck tee",
        "bottom": "sand-beige midi skirt with minimal movement",
        "tags": ["lifestyle", "premium", "outdoor", "marketplace"],
    },
    {
        "id": "light_linen_pants",
        "label": "Light Linen Pants",
        "innerwear": "clean white scoop-neck top",
        "bottom": "light linen wide-leg pants in natural tone",
        "tags": ["lifestyle", "outdoor", "coastal", "marketplace"],
    },
]

_FAMILY_VISUAL_LABELS = {
    "br_afro_modern": "Afro-Brazilian visual profile",
    "br_warm_commercial": "mixed-race Brazilian visual profile",
    "br_mature_elegant": "refined urban Brazilian visual profile",
    "br_minimal_premium": "minimal premium Brazilian visual profile",
    "br_soft_editorial": "soft editorial Brazilian visual profile",
}

_SCENE_GUIDANCE_HINTS = {
    "auto_br": "",
    "indoor_br": "indoor apartment loft showroom living",
    "outdoor_br": "outdoor balcony street boardwalk architecture",
}

_PRESET_GUIDANCE_HINTS = {
    "catalog_clean": "catalog clean stable pose full garment readability",
    "premium_lifestyle": "premium lifestyle editorial believable upscale brazilian context",
    "marketplace_lifestyle": "marketplace lifestyle authentic brazilian scene natural movement",
}

_DEFAULT_MODEL_CASTING_HINT = "brazilian fashion model casting"


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = str(item or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


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


def _as_list(val: Any) -> list[str]:
    """Helpers for robust type matching of optional string/list fields."""
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return [str(v) for v in val]
    return []

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


def get_art_direction_catalog() -> dict[str, list[dict[str, Any]]]:
    return {
        "scenes": [dict(item) for item in _SCENE_FAMILIES],
        "poses": [dict(item) for item in _POSE_FAMILIES],
        "cameras": [dict(item) for item in _CAMERA_PROFILES],
        "lightings": [dict(item) for item in _LIGHTING_PROFILES],
        "stylings": [dict(item) for item in _STYLING_PROFILES],
    }


def commit_art_direction_choice(art_direction: dict[str, Any]) -> None:
    casting = art_direction.get("casting_profile", {}) or {}
    if casting:
        commit_brazilian_casting_profile(casting)

    state = _safe_state()
    history = list(state.get("history", []))
    scene = art_direction.get("scene", {}) or {}
    pose = art_direction.get("pose", {}) or {}
    camera = art_direction.get("camera", {}) or {}
    lighting = art_direction.get("lighting", {}) or {}
    styling = art_direction.get("styling", {}) or {}

    scene_id = str(scene.get("id", "") or "")
    pose_id = str(pose.get("id", "") or "")
    camera_id = str(camera.get("id", "") or "")
    lighting_id = str(lighting.get("id", "") or "")
    styling_id = str(styling.get("id", "") or "")
    if not all([scene_id, pose_id, camera_id, lighting_id, styling_id]):
        return

    history.append(
        {
            "scene_id": scene_id,
            "pose_id": pose_id,
            "camera_id": camera_id,
            "lighting_id": lighting_id,
            "styling_id": styling_id,
            "timestamp": int(time.time()),
        }
    )
    history = history[-8:]  # type: ignore
    _save_json(
        _STATE_FILE,
        {
            "history": history,
            "cursor": int(state.get("cursor", 0) or 0) + 1,
        },
    )


def _stable_int(seed: str) -> int:
    return int(hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8], 16)  # type: ignore


def _normalize_age_value(age_text: str) -> str:
    digits = re.findall(r"\d+", age_text or "")
    if not digits:
        return "30"
    if len(digits) >= 2:
        return str((int(digits[0]) + int(digits[1])) // 2)
    return digits[0]


def _normalize_for_match(text: str) -> str:
    lowered = str(text or "").strip().lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_marks


def _tokenize_for_match(text: str) -> set[str]:
    normalized = _normalize_for_match(text)
    compact = re.sub(r"[^a-z0-9]+", " ", normalized)
    return {token for token in compact.split(" ") if token}


def _affinity(text: str, tags: list[str]) -> int:
    normalized_text = _normalize_for_match(text)
    text_tokens = _tokenize_for_match(text)
    normalized_tags = [_normalize_for_match(tag) for tag in tags if str(tag).strip()]
    score: int = 0
    for tag in normalized_tags:
        if tag and tag in normalized_text:
            score = score + 2  # type: ignore
        tag_tokens = [token for token in re.split(r"[^a-z0-9]+", tag) if token]
        if not tag_tokens:
            continue
        matched = sum(1 for token in tag_tokens if token in text_tokens)
        if matched == len(tag_tokens):
            score = score + 2  # type: ignore
        elif matched > 0:
            score = score + 1  # type: ignore
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

    recent = [item for item in state.get("history", []) if isinstance(item, dict)][-8:]  # type: ignore
    recent_counts: dict[str, int] = {}
    last_seen_index: dict[str, int] = {}
    for i, item in enumerate(recent):
        item_id = str(item.get(history_key, "") or "")
        if item_id:
            recent_counts[item_id] = recent_counts.get(item_id, 0) + 1
            last_seen_index[item_id] = i  # higher means closer to present

    seed = _stable_int(seed_hint)
    cursor = int(state.get("cursor", 0) or 0)
    text = str(user_prompt or "")

    candidates.sort(
        key=lambda item: (
            recent_counts.get(item["id"], 0),
            -_affinity(text, _as_list(item.get("tags"))),
            last_seen_index.get(item["id"], -1),
            item["id"],
        )
    )

    if not candidates:
        return {}

    best_count = recent_counts.get(candidates[0]["id"], 0)
    best_affinity = -_affinity(text, _as_list(candidates[0].get("tags")))

    tied = [
        item for item in candidates
        if recent_counts.get(item["id"], 0) == best_count
        and -_affinity(text, _as_list(item.get("tags"))) == best_affinity
    ]

    best_last_seen = last_seen_index.get(tied[0]["id"], -1)
    perfect_ties = [
        item for item in tied
        if last_seen_index.get(item["id"], -1) == best_last_seen
    ]

    return perfect_ties[(cursor + seed) % len(perfect_ties)]  # type: ignore


def sample_art_direction(
    *,
    seed_hint: str = "",
    user_prompt: Optional[str] = None,
    request: Optional[dict[str, Any]] = None,
    commit: bool = True,
) -> dict[str, Any]:
    state = _safe_state()
    request = request or {}
    forced_casting_family_id = str(request.get("forced_casting_family_id", "") or "").strip() or None
    preferred_scene_ids = _dedupe_preserve_order(_as_list(request.get("preferred_scene_ids")))
    preferred_pose_ids = _dedupe_preserve_order(_as_list(request.get("preferred_pose_ids")))
    preferred_camera_ids = _dedupe_preserve_order(_as_list(request.get("preferred_camera_ids")))
    preferred_lighting_ids = _dedupe_preserve_order(_as_list(request.get("preferred_lighting_ids")))
    preferred_styling_ids = _dedupe_preserve_order(_as_list(request.get("preferred_styling_ids")))
    scene_preference = str(request.get("scene_preference", "") or "").strip().lower()
    preset = str(request.get("preset", "") or "").strip().lower()
    image_analysis_hint = str(request.get("image_analysis_hint", "") or "").strip()
    structural_hint = str(request.get("structural_hint", "") or "").strip()
    directive_hints = request.get("directive_hints", {}) if isinstance(request.get("directive_hints"), dict) else {}
    scene_context_hint = str(directive_hints.get("scene_context_hint", "") or "").strip()
    pose_context_hint = str(directive_hints.get("pose_context_hint", "") or "").strip()
    model_context_hint = str(directive_hints.get("model_context_hint", "") or "").strip()
    custom_context_hint = str(directive_hints.get("custom_context_hint", "") or "").strip()
    # Scene/preset act as soft guidance; only preferred_* IDs are hard constraints.
    guidance_tokens: list[str] = []
    scene_guidance = scene_context_hint or str(_SCENE_GUIDANCE_HINTS.get(scene_preference, "") or "")
    preset_guidance = pose_context_hint or str(_PRESET_GUIDANCE_HINTS.get(preset, "") or "")
    if scene_guidance:
        guidance_tokens.append(scene_guidance)
    if preset_guidance:
        guidance_tokens.append(preset_guidance)
    if custom_context_hint:
        guidance_tokens.append(custom_context_hint[:220])
    if image_analysis_hint:
        guidance_tokens.append(image_analysis_hint[:220])
    if structural_hint:
        guidance_tokens.append(structural_hint[:140])

    hint_prompt = " ".join(part for part in [str(user_prompt or "").strip(), *guidance_tokens] if part).strip()
    if not hint_prompt:
        hint_prompt = user_prompt

    casting_hint_prompt = " ".join(
        part for part in [
            str(user_prompt or "").strip(),
            image_analysis_hint[:220] if image_analysis_hint else "",
            structural_hint,
            model_context_hint or _DEFAULT_MODEL_CASTING_HINT,
        ]
        if part
    ).strip()
    if not casting_hint_prompt:
        casting_hint_prompt = _DEFAULT_MODEL_CASTING_HINT

    casting = select_brazilian_casting_profile(
        seed_hint=f"{seed_hint}:casting",
        user_prompt=casting_hint_prompt,
        forced_family_id=forced_casting_family_id,
        commit=commit,
    )
    scene = _pick_item(
        state=state,
        pool=_SCENE_FAMILIES,
        history_key="scene_id",
        seed_hint=f"{seed_hint}:scene",
        user_prompt=hint_prompt,
        allowed_ids=preferred_scene_ids,
    )
    pose_allowed_ids = [item for item in _as_list(scene.get("pose_ids")) if item]
    if preferred_pose_ids:
        pose_allowed_ids = [item for item in pose_allowed_ids if item in preferred_pose_ids] or preferred_pose_ids
    pose = _pick_item(
        state=state,
        pool=_POSE_FAMILIES,
        history_key="pose_id",
        seed_hint=f"{seed_hint}:pose",
        user_prompt=hint_prompt,
        allowed_ids=pose_allowed_ids,
    )
    camera_allowed_ids = [item for item in _as_list(scene.get("camera_ids")) if item]
    if preferred_camera_ids:
        camera_allowed_ids = [item for item in camera_allowed_ids if item in preferred_camera_ids] or preferred_camera_ids
    camera = _pick_item(
        state=state,
        pool=_CAMERA_PROFILES,
        history_key="camera_id",
        seed_hint=f"{seed_hint}:camera",
        user_prompt=hint_prompt,
        allowed_ids=camera_allowed_ids,
    )
    lighting_allowed_ids = [item for item in _as_list(scene.get("lighting_ids")) if item]
    if preferred_lighting_ids:
        lighting_allowed_ids = [item for item in lighting_allowed_ids if item in preferred_lighting_ids] or preferred_lighting_ids
    lighting = _pick_item(
        state=state,
        pool=_LIGHTING_PROFILES,
        history_key="lighting_id",
        seed_hint=f"{seed_hint}:lighting",
        user_prompt=hint_prompt,
        allowed_ids=lighting_allowed_ids,
    )
    styling_allowed_ids = [item for item in _as_list(scene.get("styling_ids")) if item]
    if preferred_styling_ids:
        styling_allowed_ids = [item for item in styling_allowed_ids if item in preferred_styling_ids] or preferred_styling_ids
    styling = _pick_item(
        state=state,
        pool=_STYLING_PROFILES,
        history_key="styling_id",
        seed_hint=f"{seed_hint}:styling",
        user_prompt=hint_prompt,
        allowed_ids=styling_allowed_ids,
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
        "request": {
            "forced_casting_family_id": forced_casting_family_id,
            "preferred_scene_ids": preferred_scene_ids,
            "preferred_pose_ids": preferred_pose_ids,
            "preferred_camera_ids": preferred_camera_ids,
            "preferred_lighting_ids": preferred_lighting_ids,
            "preferred_styling_ids": preferred_styling_ids,
            "scene_preference": scene_preference,
            "preset": preset,
            "image_analysis_hint": image_analysis_hint[:220] if image_analysis_hint else "",
            "structural_hint": structural_hint,
            "directive_hints": directive_hints,
        },
    }

    if commit:
        commit_art_direction_choice(result)

    return result
