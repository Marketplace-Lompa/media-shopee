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
import os
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
from agent_runtime.curation_policy import (  # type: ignore
    ArtDirectionSelectionPolicy,
    apply_selection_policy as _policy_apply_selection_policy,
    dedupe_preserve_order as _policy_dedupe_preserve_order,
    derive_art_direction_selection_policy,
)
from agent_runtime.structural import (  # type: ignore
    get_set_member_keys,
    is_selfie_capture_compatible,
    is_spatially_sensitive_garment,
)
from config import OUTPUTS_DIR  # type: ignore

_STATE_FILE = OUTPUTS_DIR / "art_direction_sampler_state.json"
_DEFAULT_STATE = {
    "history": [],
    "cursor": 0,
}


def _action_context_enabled() -> bool:
    raw = os.getenv("ENABLE_ACTION_CONTEXT", "true").strip().lower()
    return raw != "false"


def _ugc_entropy_enabled() -> bool:
    raw = os.getenv("ENABLE_UGC_ENTROPY", "true").strip().lower()
    return raw != "false"

_SCENE_FAMILIES: list[dict[str, Any]] = [
    {
        "id": "br_recife_balcony",
        "label": "BR Recife Balcony",
        "description": "airy Recife apartment balcony with textured plaster wall, woven chair, potted plants, and an urban-coastal skyline glimpse",
        "tags": ["lifestyle", "marketplace", "balcony", "outdoor", "warm", "brazilian"],
        "camera_ids": ["phone_cameraroll", "phone_clean", "sony_documentary", "canon_balanced", "fujifilm_candid", "nikon_street"],
        "lighting_ids": ["coastal_late_morning", "open_shade_daylight", "golden_hour_soft", "cloudy_tropical"],
        "styling_ids": ["off_white_shorts", "light_linen_pants", "soft_blue_trousers"],
        "pose_ids": ["standing_3q_relaxed", "walking_stride_controlled", "paused_mid_step", "twist_step_forward", "casual_walkby_glance", "phone_low_hand_snapshot", "half_turn_lookback", "standing_full_shift"],
    },
    {
        "id": "br_pinheiros_living",
        "label": "BR Pinheiros Living",
        "description": "lived-in Pinheiros apartment living room with books, linen armchair, shelf styling, and soft plant shadows",
        "tags": ["lifestyle", "premium", "indoor", "apartment", "brazilian"],
        "camera_ids": ["phone_cameraroll", "canon_balanced", "sony_documentary", "phone_clean", "fujifilm_candid"],
        "lighting_ids": ["mixed_window_lamp", "window_daylight", "phone_practical_mixed"],
        "styling_ids": ["soft_blue_trousers", "indigo_jeans", "black_tailored_pants"],
        "pose_ids": ["standing_full_shift", "front_relaxed_hold", "soft_wall_lean", "hand_adjust_neckline", "doorway_pause_candid", "phone_low_hand_snapshot", "standing_3q_relaxed", "contrapposto_editorial", "full_back_view"],
    },
    {
        "id": "br_curitiba_cafe",
        "label": "BR Curitiba Cafe",
        "description": "neighborhood coffee shop in Curitiba with concrete floor, wood counter, pastry case, and softly busy background depth",
        "tags": ["lifestyle", "cafe", "urban", "authentic", "indoor", "brazilian"],
        "camera_ids": ["phone_cameraroll", "fujifilm_candid", "nikon_street", "phone_clean", "canon_balanced", "sony_documentary"],
        "lighting_ids": ["overcast_cafe", "mixed_window_lamp", "phone_practical_mixed", "window_daylight"],
        "styling_ids": ["indigo_jeans", "beige_midi_skirt", "light_linen_pants"],
        "pose_ids": ["paused_mid_step", "standing_3q_relaxed", "half_turn_lookback", "twist_step_forward", "doorway_pause_candid", "phone_low_hand_snapshot", "front_relaxed_hold", "soft_wall_lean"],
    },
    {
        "id": "br_showroom_sp",
        "label": "BR Sao Paulo Showroom",
        "description": "Brazilian premium showroom in Sao Paulo with softly textured neutral walls, pale stone floor, and minimal decor",
        "tags": ["catalog", "premium", "showroom", "indoor", "brazilian"],
        "camera_ids": ["canon_balanced", "sony_documentary", "phone_clean", "fujifilm_candid"],
        "lighting_ids": ["clean_showroom", "window_daylight", "open_shade_daylight"],
        "styling_ids": ["soft_blue_trousers", "black_tailored_pants"],
        "pose_ids": ["standing_full_shift", "front_relaxed_hold", "contrapposto_editorial", "hand_adjust_neckline", "standing_3q_relaxed", "half_turn_lookback", "soft_wall_lean", "twist_step_forward", "full_back_view"],
    },
    {
        "id": "br_salvador_colonial_street",
        "label": "BR Salvador Colonial Street",
        "description": "historic Salvador street with pastel facades, stone pavement, subtle local texture, and soft depth behind the subject",
        "tags": ["lifestyle", "outdoor", "urban", "authentic", "brazilian", "colorful"],
        "camera_ids": ["phone_cameraroll", "nikon_street", "fujifilm_candid", "sony_documentary", "phone_clean", "canon_balanced"],
        "lighting_ids": ["golden_hour_soft", "open_shade_daylight", "cloudy_tropical", "coastal_late_morning"],
        "styling_ids": ["off_white_shorts", "indigo_jeans", "beige_midi_skirt"],
        "pose_ids": ["walking_stride_controlled", "paused_mid_step", "half_turn_lookback", "twist_step_forward", "casual_walkby_glance", "phone_low_hand_snapshot", "standing_3q_relaxed", "standing_full_shift"],
    },
    {
        "id": "br_floripa_boardwalk",
        "label": "BR Floripa Boardwalk",
        "description": "Florianopolis boardwalk with dune vegetation, clean horizon, and breathable coastal negative space",
        "tags": ["lifestyle", "outdoor", "coastal", "marketplace", "brazilian"],
        "camera_ids": ["phone_cameraroll", "sony_documentary", "phone_clean", "fujifilm_candid", "nikon_street", "canon_balanced"],
        "lighting_ids": ["coastal_late_morning", "cloudy_tropical", "golden_hour_soft", "open_shade_daylight"],
        "styling_ids": ["light_linen_pants", "off_white_shorts"],
        "pose_ids": ["standing_3q_relaxed", "walking_stride_controlled", "standing_full_shift", "twist_step_forward", "casual_walkby_glance", "phone_low_hand_snapshot", "half_turn_lookback", "paused_mid_step"],
    },
    {
        "id": "br_brasilia_concrete_gallery",
        "label": "BR Brasilia Concrete Gallery",
        "description": "Brasilia modernist concrete gallery with long perspective lines, open sky fill light, and elegant architectural rhythm",
        "tags": ["premium", "outdoor", "architecture", "editorial", "brazilian"],
        "camera_ids": ["canon_balanced", "sony_documentary", "nikon_street", "fujifilm_candid", "phone_clean"],
        "lighting_ids": ["open_shade_daylight", "cloudy_tropical", "golden_hour_soft"],
        "styling_ids": ["black_tailored_pants", "soft_blue_trousers"],
        "pose_ids": ["contrapposto_editorial", "half_turn_lookback", "standing_full_shift", "hand_adjust_neckline", "walking_stride_controlled", "standing_3q_relaxed", "twist_step_forward", "front_relaxed_hold", "full_back_view"],
    },
    {
        "id": "br_bh_rooftop_lounge",
        "label": "BR Belo Horizonte Rooftop",
        "description": "Belo Horizonte rooftop lounge with warm stone textures, distant skyline layers, and elegant sunset ambience",
        "tags": ["premium", "outdoor", "rooftop", "lifestyle", "brazilian"],
        "camera_ids": ["sony_documentary", "canon_balanced", "fujifilm_candid", "phone_clean", "nikon_street"],
        "lighting_ids": ["golden_hour_soft", "open_shade_daylight", "cloudy_tropical", "coastal_late_morning"],
        "styling_ids": ["beige_midi_skirt", "black_tailored_pants", "light_linen_pants"],
        "pose_ids": ["standing_3q_relaxed", "contrapposto_editorial", "soft_wall_lean", "twist_step_forward", "half_turn_lookback", "standing_full_shift", "front_relaxed_hold", "hand_adjust_neckline"],
    },
    {
        "id": "br_porto_alegre_bookstore",
        "label": "BR Porto Alegre Bookstore",
        "description": "curated bookstore in Porto Alegre with wood shelving, warm practical lights, and soft aisle depth",
        "tags": ["indoor", "lifestyle", "premium", "authentic", "brazilian"],
        "camera_ids": ["phone_cameraroll", "fujifilm_candid", "canon_balanced", "sony_documentary", "phone_clean"],
        "lighting_ids": ["mixed_window_lamp", "window_daylight", "phone_practical_mixed"],
        "styling_ids": ["indigo_jeans", "black_tailored_pants", "beige_midi_skirt"],
        "pose_ids": ["front_relaxed_hold", "soft_wall_lean", "half_turn_lookback", "hand_adjust_neckline", "doorway_pause_candid", "phone_low_hand_snapshot", "standing_3q_relaxed", "contrapposto_editorial"],
    },
    {
        "id": "br_rio_art_loft",
        "label": "BR Rio Art Loft",
        "description": "Rio de Janeiro artist loft with textured plaster, large industrial windows, and restrained design objects",
        "tags": ["indoor", "editorial", "premium", "lifestyle", "brazilian"],
        "camera_ids": ["sony_documentary", "canon_balanced", "fujifilm_candid", "phone_clean", "nikon_street"],
        "lighting_ids": ["window_daylight", "mixed_window_lamp", "open_shade_daylight"],
        "styling_ids": ["black_tailored_pants", "soft_blue_trousers", "light_linen_pants"],
        "pose_ids": ["contrapposto_editorial", "standing_full_shift", "front_relaxed_hold", "hand_adjust_neckline", "twist_step_forward", "half_turn_lookback", "soft_wall_lean", "standing_3q_relaxed"],
    },
    {
        "id": "br_condo_hallway",
        "label": "BR Condo Hallway",
        "description": "Brazilian apartment building corridor with off-white walls, floor signage, practical fixtures, and believable everyday transition-space realism",
        "tags": ["lifestyle", "indoor", "apartment", "authentic", "ugc", "brazilian"],
        "camera_ids": ["phone_cameraroll", "phone_direct_flash", "sony_documentary", "phone_clean", "fujifilm_candid", "nikon_street"],
        "lighting_ids": ["phone_practical_mixed", "mixed_window_lamp", "phone_flash_direct", "window_daylight"],
        "styling_ids": ["indigo_jeans", "light_linen_pants", "black_tailored_pants"],
        "pose_ids": ["doorway_pause_candid", "phone_low_hand_snapshot", "standing_3q_relaxed", "casual_walkby_glance", "paused_mid_step", "front_relaxed_hold", "standing_full_shift", "half_turn_lookback"],
    },
    {
        "id": "br_bairro_sidewalk",
        "label": "BR Bairro Sidewalk",
        "description": "ordinary Brazilian neighborhood sidewalk with textured walls, parked cars, utility shadows, and incidental street life kept softly behind the subject",
        "tags": ["lifestyle", "outdoor", "urban", "authentic", "ugc", "brazilian"],
        "camera_ids": ["phone_cameraroll", "nikon_street", "phone_clean", "sony_documentary", "fujifilm_candid", "canon_balanced"],
        "lighting_ids": ["open_shade_daylight", "cloudy_tropical", "golden_hour_soft", "coastal_late_morning"],
        "styling_ids": ["indigo_jeans", "light_linen_pants", "off_white_shorts"],
        "pose_ids": ["casual_walkby_glance", "paused_mid_step", "standing_3q_relaxed", "phone_low_hand_snapshot", "half_turn_lookback", "walking_stride_controlled", "twist_step_forward", "standing_full_shift"],
    },
    {
        "id": "br_bedroom_window",
        "label": "BR Bedroom Window",
        "description": "Brazilian apartment bedroom corner with ordinary furniture, soft window spill, and lightly lived-in domestic depth kept secondary to the subject",
        "tags": ["indoor", "apartment", "authentic", "lifestyle", "ugc", "brazilian"],
        "camera_ids": ["phone_cameraroll", "phone_direct_flash", "phone_clean", "sony_documentary", "fujifilm_candid", "canon_balanced"],
        "lighting_ids": ["window_daylight", "phone_practical_mixed", "phone_flash_direct", "mixed_window_lamp"],
        "styling_ids": ["indigo_jeans", "light_linen_pants", "soft_blue_trousers"],
        "pose_ids": ["doorway_pause_candid", "front_relaxed_hold", "phone_low_hand_snapshot", "standing_full_shift", "standing_3q_relaxed", "soft_wall_lean", "hand_adjust_neckline", "casual_walkby_glance"],
    },
    {
        "id": "br_boutique_floor",
        "label": "BR Boutique Floor",
        "description": "small Brazilian fashion boutique with clothing racks, mirror edges, curated merchandise, and believable social-commerce creator energy",
        "tags": ["indoor", "boutique", "store", "ugc", "lifestyle", "brazilian", "creator", "influencer", "social"],
        "camera_ids": ["phone_cameraroll", "phone_front_selfie", "phone_direct_flash", "sony_documentary", "fujifilm_candid", "phone_clean"],
        "lighting_ids": ["phone_practical_mixed", "window_daylight", "phone_flash_direct", "mixed_window_lamp"],
        "styling_ids": ["indigo_jeans", "black_tailored_pants", "beige_midi_skirt", "light_linen_pants"],
        "pose_ids": ["influencer_hip_pop", "shoulder_turn_smile", "mirror_selfie_offset", "one_hand_hair_glance", "phone_low_hand_snapshot", "standing_3q_relaxed", "doorway_pause_candid", "casual_walkby_glance"],
    },
    {
        "id": "br_fitting_room_mirror",
        "label": "BR Fitting Room Mirror",
        "description": "Brazilian boutique fitting-room zone with mirror reflections, curtain edge, and believable try-on social content energy",
        "tags": ["indoor", "mirror", "boutique", "ugc", "authentic", "brazilian", "creator", "influencer", "selfie"],
        "camera_ids": ["phone_front_selfie", "phone_direct_flash", "phone_cameraroll", "phone_clean", "fujifilm_candid"],
        "lighting_ids": ["phone_practical_mixed", "phone_flash_direct", "window_daylight"],
        "styling_ids": ["indigo_jeans", "black_tailored_pants", "beige_midi_skirt", "light_linen_pants"],
        "pose_ids": ["mirror_selfie_offset", "influencer_hip_pop", "one_hand_hair_glance", "standing_3q_relaxed", "shoulder_turn_smile", "phone_low_hand_snapshot", "front_relaxed_hold", "doorway_pause_candid"],
    },
    {
        "id": "br_elevator_mirror",
        "label": "BR Elevator Mirror",
        "description": "Brazilian apartment or mall elevator mirror with brushed metal reflections and believable quick-content capture energy",
        "tags": ["indoor", "mirror", "ugc", "authentic", "urban", "brazilian", "creator", "influencer", "selfie"],
        "camera_ids": ["phone_front_selfie", "phone_direct_flash", "phone_cameraroll", "phone_clean", "fujifilm_candid"],
        "lighting_ids": ["phone_practical_mixed", "phone_flash_direct", "window_daylight"],
        "styling_ids": ["indigo_jeans", "black_tailored_pants", "light_linen_pants"],
        "pose_ids": ["mirror_selfie_offset", "influencer_hip_pop", "phone_low_hand_snapshot", "shoulder_turn_smile", "one_hand_hair_glance", "standing_3q_relaxed", "doorway_pause_candid", "casual_walkby_glance"],
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
        "id": "full_back_view",
        "label": "Full Back View",
        "angle_description": "Camera positioned directly behind the model. Model faces completely away from camera. Full garment back visible from neckline to hem.",
        "pose_description": "Model fully turned with back to camera, arms naturally at sides, garment back completely visible from collar to hem.",
        "model_hero_pose": "full back-to-camera stance with arms naturally at sides",
        "tags": ["catalog", "stable", "indoor", "outdoor", "back_view"],
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
        "id": "doorway_pause_candid",
        "label": "Doorway Pause Candid",
        "angle_description": "slightly off-axis full-body framing as if the subject was caught naturally while pausing in a doorway or corridor",
        "pose_description": "Use a natural doorway pause with uneven weight, relaxed shoulders, and believable non-performative body language while keeping garment visibility clear.",
        "model_hero_pose": "natural doorway pause with one foot lightly crossing and relaxed shoulders",
        "tags": ["lifestyle", "authentic", "ugc", "stable", "indoor", "outdoor"],
    },
    {
        "id": "casual_walkby_glance",
        "label": "Casual Walkby Glance",
        "angle_description": "slightly late-capture three-quarter framing during a casual walkby with the gaze not locked to the camera",
        "pose_description": "Use a believable walkby moment with a soft look-away and relaxed arm swing while keeping the garment contour readable.",
        "model_hero_pose": "casual walkby moment with a soft look-away and relaxed arm swing",
        "tags": ["lifestyle", "authentic", "ugc", "movement", "outdoor", "indoor"],
    },
    {
        "id": "phone_low_hand_snapshot",
        "label": "Phone Low Hand Snapshot",
        "angle_description": "natural off-center full-body framing with one hand loosely holding a phone below waist level",
        "pose_description": "Use a relaxed candid pose with one hand loosely holding a phone at the side or below the waist, without covering the garment.",
        "model_hero_pose": "relaxed candid stance with one hand loosely holding a phone below the waist",
        "tags": ["lifestyle", "authentic", "ugc", "stable", "indoor", "outdoor"],
    },
    {
        "id": "influencer_hip_pop",
        "label": "Influencer Hip Pop",
        "angle_description": "phone-style three-quarter framing with a confident hip pop and light social-media energy",
        "pose_description": "Use a charismatic creator-style stance with a small hip pop, relaxed shoulders, and garment visibility still intact.",
        "model_hero_pose": "charismatic creator-style stance with a small hip pop and relaxed shoulders",
        "tags": ["ugc", "expressive", "stable", "indoor", "outdoor", "lifestyle", "creator", "influencer", "social"],
    },
    {
        "id": "shoulder_turn_smile",
        "label": "Shoulder Turn Smile",
        "angle_description": "slight shoulder turn with a casual smile as if captured mid-story or mid-reel",
        "pose_description": "Use a captivating shoulder-turn pose with casual social energy, a small expression, and clear garment readability.",
        "model_hero_pose": "captivating shoulder-turn with casual social-media expression",
        "tags": ["ugc", "expressive", "lifestyle", "indoor", "outdoor", "creator", "influencer", "social"],
    },
    {
        "id": "one_hand_hair_glance",
        "label": "One Hand Hair Glance",
        "angle_description": "slightly imperfect social-content framing with one hand near the hair and a quick side glance",
        "pose_description": "Use a natural one-hand hair-adjust glance with expressive but believable creator energy while keeping the outfit readable.",
        "model_hero_pose": "natural one-hand hair-adjust glance with expressive creator energy",
        "tags": ["ugc", "expressive", "lifestyle", "indoor", "outdoor", "creator", "influencer", "social"],
    },
    {
        "id": "mirror_selfie_offset",
        "label": "Mirror Selfie Offset",
        "angle_description": "mirror-selfie style framing with the phone offset to one side so the outfit remains visible",
        "pose_description": "Use a believable mirror-selfie pose where the phone stays offset and does not hide the key garment areas.",
        "model_hero_pose": "mirror-selfie pose with the phone offset and the outfit still visible",
        "tags": ["ugc", "selfie", "mirror", "indoor", "expressive", "creator", "influencer", "social"],
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
        "id": "phone_cameraroll",
        "label": "Phone Camera Roll",
        "device": "common smartphone rear camera",
        "lens": "26mm equivalent lens in auto mode",
        "grain_level": "1200",
        "tags": ["ugc", "phone", "authentic", "indoor", "outdoor", "lifestyle"],
    },
    {
        "id": "phone_direct_flash",
        "label": "Phone Direct Flash",
        "device": "common smartphone rear camera",
        "lens": "26mm equivalent lens with direct on-phone flash",
        "grain_level": "1500",
        "tags": ["ugc", "phone", "flash", "authentic", "indoor", "lifestyle"],
    },
    {
        "id": "phone_front_selfie",
        "label": "Phone Front Selfie",
        "device": "common smartphone front camera",
        "lens": "24mm equivalent front-facing lens",
        "grain_level": "1700",
        "tags": ["ugc", "phone", "selfie", "mirror", "authentic", "indoor", "creator", "influencer"],
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
        "id": "phone_practical_mixed",
        "label": "Phone Practical Mixed",
        "description": "ordinary household practical light mixed with weak window spill and slight auto white-balance drift from a phone camera",
        "tags": ["indoor", "authentic", "ugc", "mixed"],
    },
    {
        "id": "phone_flash_direct",
        "label": "Phone Flash Direct",
        "description": "direct smartphone flash with clipped nearby highlights, harder falloff, and believable flat on-axis light",
        "tags": ["indoor", "authentic", "ugc", "flash"],
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
    "br_social_creator": "Brazilian creator visual profile",
    "br_afro": "contemporary Brazilian visual profile",
    "br_morena_clara": "warm Brazilian visual profile",
    "br_loira_natural": "radiant Brazilian visual profile",
    "br_ruiva": "distinctive Brazilian visual profile",
    "br_cabocla": "grounded Brazilian visual profile",
    "br_nikkei": "contemporary Brazilian nikkei visual profile",
    "br_sulista": "polished Brazilian visual profile",
    "br_nordestina": "warm nordeste Brazilian visual profile",
    "br_mulata_cacheada": "vibrant Brazilian visual profile",
    "br_mature_elegante": "refined mature Brazilian visual profile",
    "br_everyday_natural": "real-life Brazilian visual profile",
    "br_warm_commercial": "Brazilian commercial visual profile",
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
    "ugc_real_br": "authentic brazilian social-commerce creator content, everyday real-life phone capture, varied spontaneous poses, organic relatable scenario, casual confident energy",
}

_DEFAULT_MODEL_CASTING_HINT = "brazilian fashion model casting"


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    return _policy_dedupe_preserve_order(items)


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


def _apply_selection_policy(
    allowed_ids: list[str],
    *,
    preferred_ids: Optional[list[str]] = None,
    avoid_ids: Optional[list[str]] = None,
) -> list[str]:
    return _policy_apply_selection_policy(
        allowed_ids,
        preferred_ids=preferred_ids,
        avoid_ids=avoid_ids,
    )


def _derive_realism_selection_policy(
    *,
    preset: str,
    scene_preference: str,
    image_analysis_hint: str,
    structural_hint: str,
    lighting_signature: Optional[dict[str, Any]] = None,
    user_prompt: Optional[str],
    fidelity_mode: str = "balanceada",
    pose_flex_mode: str = "auto",
    selector_stats: Optional[dict[str, Any]] = None,
    structural_contract: Optional[dict[str, Any]] = None,
) -> ArtDirectionSelectionPolicy:
    return derive_art_direction_selection_policy(
        preset=preset,
        scene_preference=scene_preference,
        image_analysis_hint=image_analysis_hint,
        structural_hint=structural_hint,
        lighting_signature=lighting_signature,
        user_prompt=user_prompt,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=pose_flex_mode,
        selector_stats=selector_stats,
        structural_contract=structural_contract,
    )

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
    history = history[-12:]  # type: ignore
    _save_json(
        _STATE_FILE,
        {
            "history": history,
            "cursor": int(state.get("cursor", 0) or 0) + 1,
        },
    )


def _stable_int(seed: str) -> int:
    return int(hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8], 16)  # type: ignore


def _seeded_pick(options: list[dict[str, str]], *, seed_hint: str) -> Optional[dict[str, str]]:
    if not options:
        return None
    return options[_stable_int(seed_hint) % len(options)]


def _build_ugc_entropy_profile(
    *,
    seed_hint: str,
    scene: Optional[dict[str, Any]],
    pose: Optional[dict[str, Any]],
    camera: Optional[dict[str, Any]],
    lighting: Optional[dict[str, Any]],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
    selector_stats: Optional[dict[str, Any]],
    ugc_intent: str = "",
) -> dict[str, Any]:
    scene_info = scene or {}
    pose_info = pose or {}
    camera_info = camera or {}
    lighting_info = lighting or {}
    contract = structural_contract or {}
    set_info = set_detection or {}
    stats = selector_stats or {}

    scene_tags = {str(tag).strip().lower() for tag in (scene_info.get("tags", []) or []) if str(tag).strip()}
    pose_tags = {str(tag).strip().lower() for tag in (pose_info.get("tags", []) or []) if str(tag).strip()}
    camera_id = str(camera_info.get("id", "") or "").strip().lower()
    lighting_id = str(lighting_info.get("id", "") or "").strip().lower()
    subtype = str(contract.get("garment_subtype", "") or "").strip().lower()
    front = str(contract.get("front_opening", "") or "").strip().lower()
    sleeve = str(contract.get("sleeve_type", "") or "").strip().lower()
    length = str(contract.get("garment_length", "") or "").strip().lower()
    set_mode = str(set_info.get("set_mode", "off") or "off").strip().lower()
    complex_garment = bool(stats.get("complex_garment"))
    ugc_intent = str(ugc_intent or "").strip().lower()
    spatially_sensitive = is_spatially_sensitive_garment(
        contract,
        set_detection=set_info,
        selector_stats=stats,
    )
    selfie_compatible = is_selfie_capture_compatible(
        contract,
        set_detection=set_info,
        selector_stats=stats,
    )

    pose_id = str(pose_info.get("id", "") or "").strip().lower()

    allows_tighter_crop = (
        selfie_compatible
        and set_mode == "off"
        and front == "closed"
        and length in {"waist", "hip"}
    )
    allows_flash = (
        not spatially_sensitive
        and set_mode == "off"
        and front == "closed"
        and sleeve == "set-in"
        and "indoor" in scene_tags
        and subtype in {"pullover", "blouse", "t_shirt", "top", "unknown", "other"}
    )
    mirror_like = "mirror" in scene_tags or pose_id == "mirror_selfie_offset" or camera_id == "phone_front_selfie"
    creator_boutique_like = any(tag in scene_tags for tag in {"boutique", "store"}) and "indoor" in scene_tags
    outdoor_like = "outdoor" in scene_tags

    capture_mode_options: list[dict[str, str]] = []
    if ugc_intent == "mirror_tryon" and mirror_like and allows_tighter_crop:
        capture_mode_options.append(
            {
                "id": "mirror_tryon_selfie",
                "text": "Treat the capture like a quick Brazilian fitting-room or elevator mirror selfie, with believable mirror geometry, phone-origin timing, and creator try-on energy.",
            }
        )
    if ugc_intent == "boutique_creator" or creator_boutique_like:
        capture_mode_options.append(
            {
                "id": "creator_boutique_story",
                "text": "Treat the capture like a boutique story or reel frame from a Brazilian creator, with social-commerce charisma, phone-camera spontaneity, and an outfit-first angle.",
            }
        )
    if ugc_intent == "friend_shot_review":
        capture_mode_options.append(
            {
                "id": "friend_phone_snapshot",
                "text": "Treat the capture like a real friend-shot phone review photo for social posting, with human timing, light asymmetry, and an honest outfit-check feel.",
            }
        )
    if ugc_intent == "at_home_creator":
        capture_mode_options.append(
            {
                "id": "at_home_creator_story",
                "text": "Treat the capture like an at-home creator look check, with ordinary phone timing, believable domestic context, and socially engaging body language.",
            }
        )
    if allows_flash and (camera_id == "phone_direct_flash" or lighting_id == "phone_flash_direct"):
        capture_mode_options.append(
            {
                "id": "review_flash_story",
                "text": "Treat the capture like a quick creator review frame made with on-phone flash, preserving a believable try-on or store-check feeling instead of a polished fashion shoot.",
            }
        )
    if outdoor_like:
        capture_mode_options.append(
            {
                "id": "walkby_phone_story",
                "text": "Treat the capture like a spontaneous phone story frame outdoors, with slightly imperfect timing and a more lived social feel than a campaign walk shot.",
            }
        )
    capture_mode_options.append(
        {
            "id": "friend_phone_snapshot",
            "text": "Treat the capture like a real friend-shot phone photo taken for social posting, with human timing, light asymmetry, and no campaign polish.",
        }
    )
    selected_capture = _seeded_pick(capture_mode_options, seed_hint=f"{seed_hint}:ugc-capture") or capture_mode_options[0]
    capture_mode = selected_capture["id"]

    framing_options: list[dict[str, str]] = [
        {
            "id": "off_center_snapshot",
            "text": "Keep the framing slightly off-center with mild handheld tilt and imperfect vertical alignment, like a real phone snapshot instead of a perfectly leveled campaign image.",
        },
        {
            "id": "late_capture_walkby",
            "text": "Let the frame feel slightly late and candid, as if captured half a beat into a real moment rather than on an exact polished pose count.",
        },
    ]
    if capture_mode == "mirror_tryon_selfie":
        framing_options.insert(
            0,
            {
                "id": "mirror_phone_offset",
                "text": "Use believable mirror-selfie framing with the phone present but offset, slight mirror-edge asymmetry, and a clear readable view of the outfit.",
            }
        )
    elif capture_mode == "creator_boutique_story":
        framing_options.insert(
            0,
            {
                "id": "story_angle_snapshot",
                "text": "Use a chest-height or slightly high phone angle, like a creator capturing a boutique story or reel frame with charismatic but believable spontaneity.",
            }
        )
    elif capture_mode == "review_flash_story":
        framing_options.insert(
            0,
            {
                "id": "flash_review_frame",
                "text": "Use a quick review-photo angle with small framing imperfections and believable phone flash timing, as if captured for a social review or try-on check.",
            }
        )
    elif capture_mode == "at_home_creator_story":
        framing_options.insert(
            0,
            {
                "id": "creator_home_snapshot",
                "text": "Use an ordinary at-home creator framing with casual asymmetry and believable phone timing, like a look-check made to post for followers.",
            }
        )
    if allows_tighter_crop:
        framing_options.append(
            {
                "id": "asymmetric_mid_crop",
                "text": "Allow a natural asymmetric mid-body crop when helpful, as long as the neckline, texture panel, sleeves, and hem-relevant shape remain readable.",
            }
        )
    if "movement" not in pose_tags:
        framing_options.append(
            {
                "id": "calm_phone_snapshot",
                "text": "Let the composition feel like a calm phone capture with slight asymmetry and no rigid model centering.",
            }
        )

    if creator_boutique_like or mirror_like:
        background_options = [
            {
                "id": "boutique_trace",
                "text": "Allow one or two soft boutique cues in the background, such as rack edges, mirror frame, curtain edge, or merchandise depth, always secondary to the garment.",
            },
            {
                "id": "social_store_depth",
                "text": "Let the setting feel like a real boutique or store capture, with believable merchandise context and no sterile campaign emptiness.",
            },
        ]
    elif capture_mode == "at_home_creator_story":
        background_options = [
            {
                "id": "creator_home_depth",
                "text": "Let the setting feel like a real at-home creator capture, with believable interior depth such as a mirror, rack, chair, or corner detail kept secondary to the garment.",
            },
            {
                "id": "domestic_creator_trace",
                "text": "Allow one or two ordinary domestic cues in the background so the image feels lived-in and socially real, not staged.",
            },
        ]
    elif "indoor" in scene_tags:
        background_options = [
            {
                "id": "lived_in_room_detail",
                "text": "Allow one softly blurred lived-in background cue, such as a half-open door, a casually used chair, or everyday apartment objects kept fully secondary to the garment.",
            },
            {
                "id": "domestic_depth",
                "text": "Let the room feel lightly lived-in rather than staged, with one small domestic detail remaining behind the subject and outside the garment silhouette.",
            },
        ]
    else:
        background_options = [
            {
                "id": "neighborhood_trace",
                "text": "Allow one incidental neighborhood trace in the background, such as uneven pavement, a planter, a parked vehicle, or a wall shadow, always kept secondary to the outfit.",
            },
            {
                "id": "street_imperfection",
                "text": "Let the setting keep a little ordinary Brazilian street texture in the background instead of looking architecturally cleaned up for a campaign shoot.",
            },
        ]

    behavior_options = [
        {
            "id": "social_creator_energy",
            "text": "The subject should feel like a charismatic Brazilian creator or influencer capturing a spontaneous look moment, not like a campaign model on a professional set.",
        },
        {
            "id": "camera_aware_casual_charisma",
            "text": "Keep the body language socially engaging and casually camera-aware, with expression, attitude, and light asymmetry, but without polished runway performance.",
        },
    ]
    if creator_boutique_like or mirror_like:
        behavior_options.insert(
            0,
            {
                "id": "influencer_tryon_presence",
                "text": "Let the subject carry creator-style charisma, small expression changes, and socially magnetic presence, like authentic try-on or boutique content rather than catalog posing.",
            }
        )
    if "movement" in pose_tags:
        behavior_options.append(
            {
                "id": "not_camera_aware",
                "text": "Favor a non-performative look-away or casual attention shift instead of fully camera-aware model engagement.",
            }
        )

    surface_options = [
        {
            "id": "camera_roll_texture",
            "text": "Keep mild real-world phone capture imperfections such as faint digital noise, restrained digital sharpening, flatter auto-HDR rolloff, and small highlight clipping instead of polished studio smoothness.",
        },
        {
            "id": "unretouched_phone_realism",
            "text": "Keep the image reading like an unretouched phone-origin photograph with honest skin texture, believable micro-contrast, and no beauty-filter finish.",
        },
    ]
    if allows_flash and (camera_id == "phone_direct_flash" or lighting_id == "phone_flash_direct"):
        surface_options.insert(
            0,
            {
                "id": "direct_flash_flatness",
                "text": "Keep the direct on-phone flash look believable, with flatter on-axis light, clipped near highlights, and harder falloff, while protecting garment texture and color fidelity.",
            }
        )

    selected_framing = _seeded_pick(framing_options, seed_hint=f"{seed_hint}:ugc-framing") or framing_options[0]
    selected_background = _seeded_pick(background_options, seed_hint=f"{seed_hint}:ugc-background") or background_options[0]
    selected_behavior = _seeded_pick(behavior_options, seed_hint=f"{seed_hint}:ugc-behavior") or behavior_options[0]
    selected_surface = _seeded_pick(surface_options, seed_hint=f"{seed_hint}:ugc-surface") or surface_options[0]

    guard_clause = (
        "Keep all UGC imperfections outside the locked garment structure: do not let tilt, crop, clutter, or light artifacts hide the neckline, hem, sleeve architecture, front opening, or any coordinated set member."
    )

    return {
        "enabled": True,
        "capture_mode": capture_mode,
        "framing_mode": selected_framing["id"],
        "background_mode": selected_background["id"],
        "behavior_mode": selected_behavior["id"],
        "surface_mode": selected_surface["id"],
        "clauses": [
            selected_capture["text"],
            selected_behavior["text"],
            selected_framing["text"],
            selected_background["text"],
            selected_surface["text"],
            guard_clause,
        ],
        "compatibility": {
            "allows_tighter_crop": allows_tighter_crop,
            "allows_flash": allows_flash,
            "complex_garment": complex_garment,
            "set_mode": set_mode,
        },
    }


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


_MIN_POOL_SIZE_BEFORE_FALLBACK = 4


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
        filtered = [item for item in candidates if item["id"] in allowed]
        # ── Fallback: if filtered pool is too small, expand back to full pool
        # to avoid repetition from a tiny candidate set ──
        if len(filtered) >= _MIN_POOL_SIZE_BEFORE_FALLBACK:
            candidates = filtered
        elif filtered:
            # Keep filtered as priority but pad with remaining items
            remaining = [item for item in candidates if item["id"] not in allowed]
            candidates = filtered + remaining
        # else: use full pool as-is

    recent = [item for item in state.get("history", []) if isinstance(item, dict)][-12:]  # type: ignore
    history_len = len(recent)

    # ── Exponential cooldown: penalty grows with recency ──
    # An item used 1 step ago gets penalty 2^(12-1) = 2048
    # An item used 5 steps ago gets penalty 2^(12-5) = 128
    # An item used 11 steps ago gets penalty 2^(12-11) = 2
    # An item never used gets penalty 0
    recency_penalty: dict[str, float] = {}
    for i, item in enumerate(recent):
        item_id = str(item.get(history_key, "") or "")
        if item_id:
            step_penalty = 2.0 ** (history_len - i)
            recency_penalty[item_id] = recency_penalty.get(item_id, 0.0) + step_penalty

    seed = _stable_int(seed_hint)
    cursor = int(state.get("cursor", 0) or 0)
    text = str(user_prompt or "")

    candidates.sort(
        key=lambda item: (
            recency_penalty.get(item["id"], 0.0),
            -_affinity(text, _as_list(item.get("tags"))),
            item["id"],
        )
    )

    if not candidates:
        return {}

    best_penalty = recency_penalty.get(candidates[0]["id"], 0.0)
    best_affinity = -_affinity(text, _as_list(candidates[0].get("tags")))

    tied = [
        item for item in candidates
        if recency_penalty.get(item["id"], 0.0) == best_penalty
        and -_affinity(text, _as_list(item.get("tags"))) == best_affinity
    ]

    return tied[(cursor + seed) % len(tied)]  # type: ignore


def _build_action_context(
    *,
    pose: Optional[dict[str, Any]],
    scene: Optional[dict[str, Any]],
    structural_contract: Optional[dict[str, Any]],
    set_detection: Optional[dict[str, Any]],
    ugc_intent: str = "",
) -> str:
    pose_info = pose or {}
    scene_info = scene or {}
    contract = structural_contract or {}
    set_info = set_detection or {}

    pose_id = str(pose_info.get("id", "") or "").strip().lower()
    pose_tags = {str(tag).strip().lower() for tag in (pose_info.get("tags", []) or []) if str(tag).strip()}
    scene_tags = {str(tag).strip().lower() for tag in (scene_info.get("tags", []) or []) if str(tag).strip()}
    front = str(contract.get("front_opening", "") or "").strip().lower()
    neckline = str(contract.get("neckline_type", "") or "").strip().lower()
    ugc_intent = str(ugc_intent or "").strip().lower()
    included_keys = get_set_member_keys(
        set_info,
        include_policies={"must_include", "optional"},
        member_classes={"garment", "coordinated_accessory"},
        active_only=True,
        exclude_primary_piece=True,
    )

    if "movement" in pose_tags or pose_id in {"paused_mid_step", "walking_stride_controlled", "twist_step_forward", "casual_walkby_glance"}:
        motion_clause = "she pauses in one measured step"
    elif pose_id == "half_turn_lookback":
        motion_clause = "she settles into a soft half-turn"
    elif pose_id == "soft_wall_lean":
        motion_clause = "she settles into a calm soft lean"
    elif pose_id == "contrapposto_editorial":
        motion_clause = "she settles into a relaxed asymmetrical stance"
    elif pose_id == "doorway_pause_candid":
        motion_clause = "she pauses naturally in a doorway moment"
    elif pose_id == "influencer_hip_pop":
        motion_clause = "she hits a confident casual creator stance"
    elif pose_id == "shoulder_turn_smile":
        motion_clause = "she catches the moment in a playful shoulder turn"
    elif pose_id == "one_hand_hair_glance":
        motion_clause = "she slips into a quick expressive glance"
    elif pose_id == "mirror_selfie_offset":
        motion_clause = "she captures herself in a quick mirror moment"
    else:
        motion_clause = "she settles into a calm natural stance"

    if pose_id == "mirror_selfie_offset":
        gesture_clause = "with the phone offset to one side so the outfit remains visible"
    elif pose_id == "phone_low_hand_snapshot":
        gesture_clause = "with one hand loosely holding a phone below the waist"
    elif pose_id == "one_hand_hair_glance":
        gesture_clause = "with one hand lightly near the hair"
    elif "scarf" in included_keys:
        gesture_clause = "lightly adjusting the coordinated scarf"
    elif front == "open":
        gesture_clause = "lightly holding one garment edge"
    elif neckline in {"mock_neck", "turtleneck", "high_neck"}:
        gesture_clause = "with one hand resting naturally near the waist"
    else:
        gesture_clause = "with relaxed natural arm placement"

    if pose_id == "mirror_selfie_offset":
        orientation_clause = "while checking the look in a believable mirror capture"
    elif ugc_intent == "boutique_creator":
        orientation_clause = "while showing the look with socially engaging creator energy"
    elif ugc_intent == "friend_shot_review":
        orientation_clause = "while reacting as if a friend just captured the look for a quick review post"
    elif ugc_intent == "at_home_creator":
        orientation_clause = "while doing a casual at-home look check with creator-style confidence"
    elif "boutique" in scene_tags or "store" in scene_tags:
        orientation_clause = "while reacting naturally to the boutique or store surroundings"
    elif "outdoor" in scene_tags and ("coastal" in scene_tags or "balcony" in scene_tags or "rooftop" in scene_tags):
        orientation_clause = "while turning subtly toward the open light"
    elif "outdoor" in scene_tags:
        orientation_clause = "while moving gently through the open air"
    elif "indoor" in scene_tags and any(tag in scene_tags for tag in ("showroom", "premium", "architecture", "bookstore", "apartment", "cafe")):
        orientation_clause = "while turning gently toward the natural window light"
    else:
        orientation_clause = "while keeping the body language relaxed and believable"

    return f"{motion_clause}, {gesture_clause}, {orientation_clause}"


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
    fidelity_mode = str(request.get("fidelity_mode", "balanceada") or "balanceada").strip().lower()
    pose_flex_mode = str(request.get("pose_flex_mode", "auto") or "auto").strip().lower()
    image_analysis_hint = str(request.get("image_analysis_hint", "") or "").strip()
    structural_hint = str(request.get("structural_hint", "") or "").strip()
    lighting_signature = request.get("lighting_signature") if isinstance(request.get("lighting_signature"), dict) else {}
    selector_stats = request.get("selector_stats") if isinstance(request.get("selector_stats"), dict) else {}
    structural_contract = request.get("structural_contract") if isinstance(request.get("structural_contract"), dict) else {}
    set_detection = request.get("set_detection") if isinstance(request.get("set_detection"), dict) else {}
    look_contract_req = request.get("look_contract") if isinstance(request.get("look_contract"), dict) else {}
    garment_aesthetic_req = request.get("garment_aesthetic") if isinstance(request.get("garment_aesthetic"), dict) else {}
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
        guidance_tokens.append(image_analysis_hint[:400])
    if structural_hint:
        guidance_tokens.append(structural_hint[:140])
    # garment_aesthetic → vibe/sazonalidade/formalidade informam a seleção de cena
    if garment_aesthetic_req:
        _vibe = str(garment_aesthetic_req.get("vibe") or "").strip()
        _season = str(garment_aesthetic_req.get("season") or "").strip()
        _formality = str(garment_aesthetic_req.get("formality") or "").strip()
        if _vibe:
            guidance_tokens.append(f"garment vibe: {_vibe}")
        if _season and _season != "mid_season":
            guidance_tokens.append(f"garment season: {_season}")
        if _formality and _formality != "casual":
            guidance_tokens.append(f"garment formality: {_formality}")
    # look_contract → ocasião e DNA de estilo para casting e seleção de cena
    if look_contract_req and float(look_contract_req.get("confidence", 0) or 0) > 0.5:
        _occasion = str(look_contract_req.get("occasion") or "").strip()
        _style_kw = ", ".join(
            str(x).strip() for x in (look_contract_req.get("style_keywords") or []) if str(x).strip()
        )
        if _occasion:
            guidance_tokens.append(f"garment occasion: {_occasion}")
        if _style_kw:
            guidance_tokens.append(f"garment style DNA: {_style_kw}")

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

    selection_policy = _derive_realism_selection_policy(
        preset=preset,
        scene_preference=scene_preference,
        image_analysis_hint=image_analysis_hint[:220] if image_analysis_hint else "",
        structural_hint=structural_hint,
        lighting_signature=lighting_signature,
        user_prompt=user_prompt,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=pose_flex_mode,
        selector_stats=selector_stats,
        structural_contract=structural_contract,
    )
    ugc_intent = str(selection_policy.get("ugc_intent", "") or "").strip().lower()

    scene_allowed_ids = preferred_scene_ids
    if not scene_allowed_ids:
        scene_allowed_ids = [str(item.get("id", "") or "") for item in _SCENE_FAMILIES if str(item.get("id", "") or "")]
    scene_allowed_ids = _apply_selection_policy(
        scene_allowed_ids,
        preferred_ids=selection_policy.get("preferred_scene_ids"),
        avoid_ids=selection_policy.get("avoid_scene_ids"),
    )

    casting = select_brazilian_casting_profile(
        seed_hint=f"{seed_hint}:casting",
        user_prompt=casting_hint_prompt,
        forced_family_id=forced_casting_family_id,
        preferred_family_ids=selection_policy.get("preferred_casting_family_ids"),
        avoid_family_ids=selection_policy.get("avoid_casting_family_ids"),
        commit=commit,
    )
    scene = _pick_item(
        state=state,
        pool=_SCENE_FAMILIES,
        history_key="scene_id",
        seed_hint=f"{seed_hint}:scene",
        user_prompt=hint_prompt,
        allowed_ids=scene_allowed_ids,
    )
    pose_allowed_ids = [item for item in _as_list(scene.get("pose_ids")) if item]
    if preferred_pose_ids:
        pose_allowed_ids = [item for item in pose_allowed_ids if item in preferred_pose_ids] or pose_allowed_ids
    pose_allowed_ids = _apply_selection_policy(
        pose_allowed_ids,
        preferred_ids=selection_policy.get("preferred_pose_ids"),
        avoid_ids=selection_policy.get("avoid_pose_ids"),
    )
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
        camera_allowed_ids = [item for item in camera_allowed_ids if item in preferred_camera_ids] or camera_allowed_ids
    camera_allowed_ids = _apply_selection_policy(
        camera_allowed_ids,
        preferred_ids=selection_policy.get("preferred_camera_ids"),
        avoid_ids=selection_policy.get("avoid_camera_ids"),
    )
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
        lighting_allowed_ids = [item for item in lighting_allowed_ids if item in preferred_lighting_ids] or lighting_allowed_ids
    lighting_allowed_ids = _apply_selection_policy(
        lighting_allowed_ids,
        preferred_ids=selection_policy.get("preferred_lighting_ids"),
        avoid_ids=selection_policy.get("avoid_lighting_ids"),
    )
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
        styling_allowed_ids = [item for item in styling_allowed_ids if item in preferred_styling_ids] or styling_allowed_ids
    styling = _pick_item(
        state=state,
        pool=_STYLING_PROFILES,
        history_key="styling_id",
        seed_hint=f"{seed_hint}:styling",
        user_prompt=hint_prompt,
        allowed_ids=styling_allowed_ids,
    )
    action_context = (
        _build_action_context(
            pose=pose,
            scene=scene,
            structural_contract=structural_contract,
            set_detection=set_detection,
            ugc_intent=ugc_intent,
        )
        if _action_context_enabled()
        else ""
    )
    ugc_entropy_profile = (
        _build_ugc_entropy_profile(
            seed_hint=seed_hint,
            scene=scene,
            pose=pose,
            camera=camera,
            lighting=lighting,
            structural_contract=structural_contract,
            set_detection=set_detection,
            selector_stats=selector_stats,
            ugc_intent=ugc_intent,
        )
        if preset == "ugc_real_br" and _ugc_entropy_enabled()
        else {}
    )

    result = {
        "casting_profile": casting,
        "scene": scene,
        "pose": pose,
        "camera": camera,
        "lighting": lighting,
        "styling": styling,
        "action_context": action_context,
        "ugc_entropy_profile": ugc_entropy_profile,
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
            "action_context": action_context,
            "ugc_capture_mode": ugc_entropy_profile.get("capture_mode"),
            "ugc_framing_mode": ugc_entropy_profile.get("framing_mode"),
            "ugc_background_mode": ugc_entropy_profile.get("background_mode"),
            "ugc_intent": ugc_intent,
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
            "fidelity_mode": fidelity_mode,
            "pose_flex_mode": pose_flex_mode,
            "image_analysis_hint": image_analysis_hint[:220] if image_analysis_hint else "",
            "structural_hint": structural_hint,
            "lighting_signature": lighting_signature,
            "set_detection": set_detection,
            "directive_hints": directive_hints,
            "selection_policy": selection_policy,
            "ugc_intent": ugc_intent,
            "action_context_enabled": _action_context_enabled(),
            "ugc_entropy_enabled": _ugc_entropy_enabled(),
            "ugc_entropy_profile": ugc_entropy_profile,
        },
    }

    if commit:
        commit_art_direction_choice(result)

    return result
