"""
Orquestrador Marketplace:
- cada slot roda como geração independente (n_images=1)
- suporta main_variation (5 slots) e color_variations (3 slots por cor)
"""
from __future__ import annotations

import logging
from pathlib import Path
import re
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Optional

from agent_runtime.marketplace_policy import resolve_marketplace_policy

_log = logging.getLogger(__name__)

# ── Configuração de art direction por slot ────────────────────────────────────
# Define ângulo, câmera, fidelidade e hint contextual específico por slot_id.
# Isso garante que cada imagem entregue o enquadramento prometido ao comprador.

_SLOT_ART_DIRECTION: dict[str, dict[str, Any]] = {
    # Capa: full body frontal, câmera catálogo, fidelidade máxima
    "hero_front": {
        "fidelity_override": None,  # usa normalized_fidelity do fluxo
        "pose_flex_override": None,
        "preferred_pose_ids": ["front_relaxed_hold", "contrapposto_editorial", "standing_full_shift"],
        "preferred_camera_ids": ["sony_documentary", "canon_balanced"],
        "custom_context_hint": "Full body front-facing catalog shot. Model fully visible head to toe. Neutral studio background.",
        "angle_directive": "MANDATORY SHOT ANGLE: straight-on front view. Camera directly in front of model, model faces camera fully, complete garment front visible from collar to hem.",
    },
    # 3/4: ângulo ligeiramente girado, full body
    "front_3_4": {
        "fidelity_override": None,
        "pose_flex_override": None,
        "preferred_pose_ids": ["half_turn_lookback", "contrapposto_editorial", "standing_3q_relaxed"],
        "preferred_camera_ids": ["fujifilm_candid", "nikon_street", "sony_documentary"],
        "custom_context_hint": "Three-quarter angle shot. Model slightly turned to reveal front drape and side silhouette simultaneously. Full body visible.",
        "angle_directive": "MANDATORY SHOT ANGLE: three-quarter angle (45°). Camera positioned to the model's right, model body rotated ~45°, face partially toward camera, front and right-side of garment visible simultaneously.",
    },
    # Costas/lateral: ângulo 3/4 de costas — garment back panel + drape visíveis
    # Não força 180° exato (full back) pois referências são majoritariamente frontais;
    # 3/4 de costas usa a geometria estrutural conhecida sem precisar inventar o verso.
    "back_or_side": {
        "fidelity_override": None,
        "pose_flex_override": None,
        "preferred_pose_ids": ["half_turn_lookback", "full_back_view"],
        "preferred_camera_ids": ["sony_documentary", "canon_balanced", "fujifilm_candid"],
        "custom_context_hint": "Back three-quarter angle shot showing garment back panel, drape behavior, and silhouette from behind. Model faces away or at 3/4 away from camera. Full body visible head to hem.",
        "angle_directive": (
            "MANDATORY SHOT ANGLE: back three-quarter view. "
            "Camera positioned behind and slightly to the model's left, model body angled ~45° away from camera. "
            "The garment back panel, back drape, and full back silhouette must be clearly visible from neckline to hem. "
            "Face NOT visible or only very partially visible at the cheek edge. "
            "Show the complete back construction and how the garment falls from behind."
        ),
    },
    # Close-up têxtil: zoom de produto com ênfase na textura do tecido
    # Não força macro extremo de fibra — mantém contexto de peça vestida com detalhe de textura.
    "fabric_closeup": {
        "fidelity_override": "balanceada",
        "pose_flex_override": "balanced",
        "preferred_pose_ids": [],
        "preferred_camera_ids": ["sony_documentary", "canon_balanced"],
        "custom_context_hint": "Medium close-up of garment upper body showing textile surface detail, stitch relief, and pattern at readable zoom. Model's torso and part of the garment visible — no extreme fiber macro.",
        "angle_directive": (
            "MANDATORY FRAMING: medium close-up of garment. "
            "Camera closer than a full body shot, framing roughly from mid-torso up to just above the shoulders. "
            "Fill the frame with the garment surface to show textile texture, stitch relief, and pattern detail clearly. "
            "Do NOT use extreme macro or fill the frame with individual yarn fibers — the overall garment surface "
            "and pattern should remain readable. Hands or partial arms may be visible for natural context."
        ),
    },
    # Detalhe funcional: zoom em acabamento/bainhas/fechos
    "functional_detail_or_size": {
        "fidelity_override": "balanceada",  # libera câmera para detalhe
        "pose_flex_override": "balanced",
        "preferred_pose_ids": [],
        "preferred_camera_ids": ["sony_documentary", "canon_balanced"],
        "custom_context_hint": "Close-up detail shot showing functional garment features: hem finishing, cuff, collar, opening edge, button, or closure. Tight crop on the specific functional area.",
        "angle_directive": "MANDATORY FRAMING: tight detail close-up. Crop tightly on one specific functional garment area (hem finishing, cuff, collar, opening edge, or closure). No full body shot.",
    },
    # Color variations slots — mantêm fidelidade estrita mas mudam ângulo
    "color_hero_front": {
        "fidelity_override": None,
        "pose_flex_override": None,
        "preferred_pose_ids": ["front_relaxed_hold", "contrapposto_editorial", "standing_full_shift"],
        "preferred_camera_ids": ["sony_documentary", "canon_balanced"],
        "custom_context_hint": "Full body front-facing catalog shot for this specific colorway.",
        "angle_directive": "MANDATORY SHOT ANGLE: straight-on front view. Camera directly in front of model, model faces camera fully, complete garment front visible from collar to hem.",
    },
    "color_front_3_4": {
        "fidelity_override": None,
        "pose_flex_override": None,
        "preferred_pose_ids": ["half_turn_lookback", "contrapposto_editorial"],
        "preferred_camera_ids": ["fujifilm_candid", "nikon_street", "sony_documentary"],
        "custom_context_hint": "Three-quarter angle shot showing colorway drape and silhouette.",
        "angle_directive": "MANDATORY SHOT ANGLE: three-quarter angle (45°). Camera to model's right, body rotated ~45°, front and right-side of garment visible simultaneously.",
    },
    "color_detail": {
        "fidelity_override": "balanceada",
        "pose_flex_override": "balanced",
        "preferred_pose_ids": [],
        "preferred_camera_ids": ["sony_documentary", "canon_balanced"],
        "custom_context_hint": "Medium close-up of garment showing colorway tone and textile surface detail. Frame from mid-torso up — no extreme fiber macro.",
        "angle_directive": (
            "MANDATORY FRAMING: medium close-up of garment for colorway detail. "
            "Frame roughly from mid-torso up, filling the shot with the garment surface to show color tone and texture clearly. "
            "Do NOT use extreme macro showing individual yarn fibers — the pattern and color must remain readable."
        ),
    },
}

_COLOR_PATTERNS: list[tuple[str, list[str]]] = [
    ("preto", ["preto", "black"]),
    ("branco", ["branco", "white"]),
    ("off_white", ["off white", "off-white", "offwhite", "gelo", "ivory"]),
    ("cinza", ["cinza", "gray", "grey", "grafite", "chumbo"]),
    ("bege", ["bege", "beige", "nude", "areia", "camel"]),
    ("marrom", ["marrom", "brown", "cafe", "coffee", "caramelo", "caramel"]),
    ("vermelho", ["vermelho", "red", "bordo", "burgundy", "vinho", "wine"]),
    ("rosa", ["rosa", "pink", "fucsia", "fuchsia"]),
    ("laranja", ["laranja", "orange", "coral"]),
    ("amarelo", ["amarelo", "yellow", "mostarda", "mustard"]),
    ("verde", ["verde", "green", "oliva", "olive", "musgo", "moss"]),
    ("azul", ["azul", "blue", "marinho", "navy", "royal"]),
    ("roxo", ["roxo", "purple", "lilas", "lilac", "violeta", "violet"]),
]
_ROOT = Path(__file__).resolve().parents[3]
_APP_DIR = _ROOT / "app"


@dataclass
class _ColorReference:
    label: str
    source_index: int
    filename: str
    image_bytes: bytes


def _emit(on_stage: Optional[Callable[[str, dict[str, Any]], None]], stage: str, data: dict[str, Any]) -> None:
    if not on_stage:
        return
    try:
        on_stage(stage, data)
    except Exception:
        pass


def _slug(text: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "item"


def _extract_color_label(filename: str) -> Optional[str]:
    source = str(filename or "").strip().lower()
    if not source:
        return None
    normalized = source.replace("-", " ").replace("_", " ")
    for canonical, patterns in _COLOR_PATTERNS:
        if any(pat in normalized for pat in patterns):
            return canonical
    return None


def detect_color_references(
    *,
    color_images_bytes: list[bytes],
    color_filenames: Optional[list[str]] = None,
) -> list[_ColorReference]:
    if not color_images_bytes:
        return []

    detected: list[_ColorReference] = []
    seen_labels: set[str] = set()

    for idx, image_bytes in enumerate(color_images_bytes):
        raw_name = ""
        if color_filenames and idx < len(color_filenames):
            raw_name = str(color_filenames[idx] or "").strip()
        label = _extract_color_label(raw_name) or f"cor_{idx + 1}"
        if label in seen_labels:
            continue
        seen_labels.add(label)
        detected.append(
            _ColorReference(
                label=label,
                source_index=idx + 1,
                filename=raw_name or f"color_{idx + 1}.jpg",
                image_bytes=image_bytes,
            )
        )
    return detected


def _resolve_runtime_options(
    *,
    policy: dict[str, Any],
    preset: Optional[str],
    scene_preference: str,
    fidelity_mode: str,
    pose_flex_mode: str,
) -> dict[str, Any]:
    runtime_defaults = dict(policy.get("runtime_defaults") or {})

    requested_preset = str(preset or "").strip()
    requested_scene = str(scene_preference or "").strip()
    requested_fidelity = str(fidelity_mode or "").strip()
    requested_pose = str(pose_flex_mode or "").strip()

    # Mantém override manual apenas quando for claramente intencional.
    # No guided mode, os valores legados ("marketplace_lifestyle"/"auto_br")
    # são substituídos por baseline clean/compliance.
    desired_preset = (
        runtime_defaults.get("preset", "catalog_clean")
        if requested_preset.lower() in {"", "marketplace_lifestyle"}
        else requested_preset
    )
    desired_scene = (
        runtime_defaults.get("scene_preference", "indoor_br")
        if requested_scene.lower() in {"", "auto_br"}
        else requested_scene
    )
    desired_fidelity = requested_fidelity or str(runtime_defaults.get("fidelity_mode", "balanceada"))
    desired_pose = (
        runtime_defaults.get("pose_flex_mode", "controlled")
        if requested_pose.lower() in {"", "auto"}
        else requested_pose
    )

    valid_presets = {"catalog_clean", "marketplace_lifestyle", "premium_lifestyle", "ugc_real_br"}
    valid_scenes = {"auto_br", "indoor_br", "outdoor_br"}
    valid_fidelity = {"estrita", "balanceada"}
    valid_pose = {"auto", "controlled", "balanced", "dynamic"}

    normalized_preset = desired_preset if desired_preset in valid_presets else "catalog_clean"
    normalized_scene = desired_scene if desired_scene in valid_scenes else "indoor_br"
    normalized_fidelity = desired_fidelity if desired_fidelity in valid_fidelity else "balanceada"
    normalized_pose = desired_pose if desired_pose in valid_pose else "controlled"

    return {
        "requested": {
            "preset": requested_preset or None,
            "scene_preference": requested_scene or None,
            "fidelity_mode": requested_fidelity or None,
            "pose_flex_mode": requested_pose or None,
        },
        "applied": {
            "preset": normalized_preset,
            "scene_preference": normalized_scene,
            "fidelity_mode": normalized_fidelity,
            "pose_flex_mode": normalized_pose,
        },
    }


def _compose_slot_prompt(
    *,
    channel_hint: str,
    slot_id: str,
    slot_prompt: str,
    user_prompt: Optional[str],
    operation: str,
    color_label: Optional[str] = None,
    prompt_guardrails: Optional[list[str]] = None,
    continuity_anchor_active: bool = False,
) -> str:
    parts = [
        "Marketplace listing generation. Produce one independent photo slot.",
        channel_hint,
        "Keep listing-level visual coherence across slots, but always generate a newly created model identity distinct from all reference people.",
        "Preserve exact garment geometry, silhouette, drape, and texture fidelity from references.",
        "Do not redesign the garment.",
        slot_prompt,
    ]

    if prompt_guardrails:
        parts.extend([item for item in prompt_guardrails if str(item or "").strip()])

    if continuity_anchor_active:
        parts.append(
            "Use the approved first shot as continuity anchor: keep the same generated model identity "
            "(face family, hair silhouette, body proportions) and keep garment fidelity unchanged."
        )

    slot_key = str(slot_id or "").strip().lower()
    if slot_key in {"hero_front", "front_3_4", "back_or_side", "color_hero_front", "color_front_3_4"}:
        parts.append(
            "If the references indicate coordinated set members, "
            "the model must wear all required set members together in this slot with matching textile DNA."
        )
        parts.append(
            "Keep knit/crochet micro-texture crisp and tactile: visible stitch definition, yarn relief, and natural fiber depth."
        )
    elif slot_key in {"fabric_closeup", "functional_detail_or_size", "color_detail"}:
        parts.append(
            "If coordinated set members exist, this slot must still preserve the set textile DNA "
            "(same stripe order, yarn tone, and stitch family) in the visible detail."
        )

    if operation == "color_variations" and color_label:
        parts.extend(
            [
                f"Apply the garment colorway '{color_label}' based on the provided color references.",
                "Change only garment colorway attributes required for this slot; keep shape and construction identical.",
            ]
        )

    clean_user = str(user_prompt or "").strip()
    if clean_user:
        parts.append(f"User business context: {clean_user}")

    return " ".join(parts)


def _output_path_from_url(url: str) -> Optional[Path]:
    raw = str(url or "").strip()
    if not raw.startswith("/outputs/"):
        return None
    candidate = _APP_DIR / raw.lstrip("/")
    return candidate


def run_marketplace_orchestration(
    *,
    marketplace_channel: str,
    operation: str,
    base_images_bytes: list[bytes],
    base_filenames: Optional[list[str]] = None,
    color_images_bytes: Optional[list[bytes]] = None,
    color_filenames: Optional[list[str]] = None,
    prompt: Optional[str] = None,
    aspect_ratio: str = "4:5",
    resolution: str = "1K",
    preset: Optional[str] = "marketplace_lifestyle",
    scene_preference: str = "auto_br",
    fidelity_mode: str = "estrita",
    pose_flex_mode: str = "controlled",
    on_stage: Optional[Callable[[str, dict[str, Any]], None]] = None,
) -> dict[str, Any]:
    if not base_images_bytes:
        raise ValueError("Marketplace requer pelo menos 1 imagem base em base_images")

    if operation == "color_variations" and not (color_images_bytes or []):
        raise ValueError("operation=color_variations requer pelo menos 1 imagem em color_images")

    policy = resolve_marketplace_policy(marketplace_channel, operation)
    runtime_profile = _resolve_runtime_options(
        policy=policy,
        preset=preset,
        scene_preference=scene_preference,
        fidelity_mode=fidelity_mode,
        pose_flex_mode=pose_flex_mode,
    )
    normalized_preset = str((runtime_profile.get("applied") or {}).get("preset") or "catalog_clean")
    normalized_scene = str((runtime_profile.get("applied") or {}).get("scene_preference") or "indoor_br")
    normalized_fidelity = str((runtime_profile.get("applied") or {}).get("fidelity_mode") or "estrita")
    normalized_pose = str((runtime_profile.get("applied") or {}).get("pose_flex_mode") or "controlled")

    orchestrator_session = f"mkt_{str(uuid.uuid4())[:8]}"
    slots_plan: list[dict[str, Any]] = []
    detected_colors: list[dict[str, Any]] = []
    safe_base_filenames = [
        (str(base_filenames[i] or "").strip() if base_filenames and i < len(base_filenames) else f"base_{i + 1}.jpg")
        for i in range(len(base_images_bytes))
    ]

    if operation == "main_variation":
        for slot in policy["slots"]:
            slots_plan.append(
                {
                    "slot_id": slot["slot_id"],
                    "slot_type": slot["slot_type"],
                    "slot_prompt": slot["shot_prompt"],
                    "color_label": None,
                    "reference_bytes": list(base_images_bytes)[:14],
                    "reference_filenames": list(safe_base_filenames)[:14],
                }
            )
    else:
        color_refs = detect_color_references(
            color_images_bytes=list(color_images_bytes or []),
            color_filenames=color_filenames,
        )
        if not color_refs:
            raise ValueError("Não foi possível detectar variações de cor a partir das referências")

        detected_colors = [
            {
                "label": item.label,
                "source_index": item.source_index,
                "source_filename": item.filename,
            }
            for item in color_refs
        ]
        for color_ref in color_refs:
            for slot in policy["slots"]:
                merged_bytes = (list(base_images_bytes) + [color_ref.image_bytes])[:14]
                merged_names = (list(safe_base_filenames) + [color_ref.filename])[:14]
                slots_plan.append(
                    {
                        "slot_id": f"{_slug(color_ref.label)}__{slot['slot_id']}",
                        "slot_type": slot["slot_type"],
                        "slot_prompt": slot["shot_prompt"],
                        "color_label": color_ref.label,
                        "reference_bytes": merged_bytes,
                        "reference_filenames": merged_names,
                    }
                )

    total_slots = len(slots_plan)
    completed_slots = 0
    failed_slots = 0
    results: list[dict[str, Any]] = []
    continuity_anchor_bytes: Optional[bytes] = None
    continuity_anchor_filename: Optional[str] = None
    continuity_anchor_url: Optional[str] = None

    _emit(
        on_stage,
        "marketplace_started",
        {
            "message": "Iniciando fluxo Marketplace...",
            "channel": marketplace_channel,
            "operation": operation,
            "total_slots": total_slots,
        },
    )

    for idx, slot in enumerate(slots_plan, start=1):
        slot_id = str(slot["slot_id"])
        slot_type = str(slot["slot_type"])
        color_label = slot.get("color_label")
        slot_reference_bytes = list(slot.get("reference_bytes") or [])
        slot_reference_names = list(slot.get("reference_filenames") or [])
        continuity_anchor_active = False

        # Fluxo em turno: após a capa principal, as próximas fotos seguem a mesma
        # identidade/modelo gerada, mantendo a peça como contrato fixo.
        if operation == "main_variation" and continuity_anchor_bytes and slot_id != "hero_front":
            continuity_anchor_active = True
            anchor_name = continuity_anchor_filename or "continuity_anchor.png"
            slot_reference_bytes = [continuity_anchor_bytes] + slot_reference_bytes
            slot_reference_names = [anchor_name] + slot_reference_names
            slot_reference_bytes = slot_reference_bytes[:14]
            slot_reference_names = slot_reference_names[:14]

        _emit(
            on_stage,
            "creating_listing",
            {
                "message": f"Gerando slot {idx}/{total_slots}: {slot_id}",
                "current": idx,
                "total": total_slots,
                "slot_id": slot_id,
                "slot_type": slot_type,
                "color": color_label,
            },
        )

        slot_prompt = _compose_slot_prompt(
            channel_hint=str(policy.get("channel_style_hint", "")),
            slot_id=slot_id,
            slot_prompt=str(slot.get("slot_prompt", "")),
            user_prompt=prompt,
            operation=operation,
            color_label=color_label,
            prompt_guardrails=list(policy.get("prompt_guardrails") or []),
            continuity_anchor_active=continuity_anchor_active,
        )

        try:
            # Lazy import evita acoplamento pesado em import-time e melhora testabilidade.
            from agent_runtime.pipeline_v2 import run_pipeline_v2
            from agent_runtime.pipeline_v2_support import persist_v2_history

            # ── Resolver art direction específica do slot ─────────────────────
            slot_art_cfg = _SLOT_ART_DIRECTION.get(slot_id, {})
            # Forçar balanceada para todos os slots pelo Orchestrator a não ser que slot declare estrita
            effective_fidelity = str(slot_art_cfg.get("fidelity_override") or "balanceada")
            effective_pose = str(slot_art_cfg.get("pose_flex_override") or normalized_pose)

            slot_art_request: dict[str, Any] = {}
            preferred_pose_ids = list(slot_art_cfg.get("preferred_pose_ids") or [])
            preferred_camera_ids = list(slot_art_cfg.get("preferred_camera_ids") or [])
            custom_hint = str(slot_art_cfg.get("custom_context_hint") or "")
            angle_directive = str(slot_art_cfg.get("angle_directive") or "")

            if preferred_pose_ids:
                slot_art_request["preferred_pose_ids"] = preferred_pose_ids
            if preferred_camera_ids:
                slot_art_request["preferred_camera_ids"] = preferred_camera_ids
            directive_hints: dict[str, Any] = {}
            if custom_hint:
                directive_hints["custom_context_hint"] = custom_hint
            if angle_directive:
                directive_hints["angle_directive"] = angle_directive
            if directive_hints:
                slot_art_request["directive_hints"] = directive_hints

            raw = run_pipeline_v2(
                uploaded_bytes=slot_reference_bytes,
                uploaded_filenames=slot_reference_names,
                prompt=slot_prompt,
                preset=normalized_preset,
                scene_preference=normalized_scene,
                fidelity_mode=effective_fidelity,
                pose_flex_mode=effective_pose,
                n_images=1,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                art_direction_request=slot_art_request if slot_art_request else None,
                on_stage=None,
            )
            persist_v2_history(
                raw,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                preset=normalized_preset,
                scene_preference=normalized_scene,
                fidelity_mode=normalized_fidelity,
                pose_flex_mode=normalized_pose,
                marketplace_channel=marketplace_channel,
                marketplace_operation=operation,
                slot_id=slot_id,
            )
            first_image = (raw.get("images") or [None])[0]
            if not first_image:
                failed_slots += 1
                results.append(
                    {
                        "slot_id": slot_id,
                        "slot_type": slot_type,
                        "color": color_label,
                        "status": "error",
                        "error": "Pipeline não retornou imagem para o slot",
                    }
                )
                continue

            completed_slots += 1
            image_payload = {
                "index": int(first_image.get("index", 1) or 1),
                "filename": first_image.get("filename"),
                "url": first_image.get("url"),
                "size_kb": first_image.get("size_kb"),
                "mime_type": first_image.get("mime_type"),
            }

            if operation == "main_variation" and (slot_id == "hero_front" or continuity_anchor_bytes is None):
                anchor_path = _output_path_from_url(str(first_image.get("url") or ""))
                if anchor_path and anchor_path.exists():
                    try:
                        continuity_anchor_bytes = anchor_path.read_bytes()
                        continuity_anchor_filename = str(first_image.get("filename") or anchor_path.name)
                        continuity_anchor_url = str(first_image.get("url") or "")
                        _log.info("[marketplace] continuity anchor salvo: %s (%d bytes)", continuity_anchor_filename, len(continuity_anchor_bytes))
                    except Exception as anchor_exc:
                        _log.warning("[marketplace] falha ao ler anchor %s: %s", anchor_path, anchor_exc)
                        # Mantém anchor anterior se houver; não sobrescreve com None
                else:
                    _log.warning("[marketplace] anchor path não encontrado: %s", anchor_path)

            results.append(
                {
                    "slot_id": slot_id,
                    "slot_type": slot_type,
                    "color": color_label,
                    "status": "done",
                    "session_id": raw.get("session_id"),
                    "pipeline_mode": raw.get("pipeline_mode"),
                    "image": image_payload,
                    "debug_report_url": raw.get("report_url"),
                }
            )
        except Exception as slot_exc:
            failed_slots += 1
            results.append(
                {
                    "slot_id": slot_id,
                    "slot_type": slot_type,
                    "color": color_label,
                    "status": "error",
                    "error": str(slot_exc),
                }
            )

    response = {
        "session_id": orchestrator_session,
        "pipeline_version": "marketplace_v1",
        "marketplace_channel": marketplace_channel,
        "operation": operation,
        "detected_colors": detected_colors,
        "slots": results,
        "summary": {
            "requested_slots": total_slots,
            "completed_slots": completed_slots,
            "failed_slots": failed_slots,
        },
        "config": {
            "preset": normalized_preset,
            "scene_preference": normalized_scene,
            "fidelity_mode": normalized_fidelity,
            "pose_flex_mode": normalized_pose,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "identity_anchor_mode": "hero_turn_chain" if operation == "main_variation" else "per_color_chain",
            "identity_anchor_url": continuity_anchor_url,
            "requested_preset": (runtime_profile.get("requested") or {}).get("preset"),
            "requested_scene_preference": (runtime_profile.get("requested") or {}).get("scene_preference"),
            "requested_fidelity_mode": (runtime_profile.get("requested") or {}).get("fidelity_mode"),
            "requested_pose_flex_mode": (runtime_profile.get("requested") or {}).get("pose_flex_mode"),
        },
    }
    _emit(
        on_stage,
        "done",
        {
            "message": "Fluxo Marketplace finalizado",
            "completed_slots": completed_slots,
            "failed_slots": failed_slots,
            "total_slots": total_slots,
        },
    )
    return response
