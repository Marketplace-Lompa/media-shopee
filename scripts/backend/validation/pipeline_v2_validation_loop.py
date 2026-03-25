"""
Loop continuo de validacao autocorretiva em cima do pipeline_v2.

Uso:
  app/.venv/bin/python scripts/backend/validation/pipeline_v2_validation_loop.py \
    --folder docs/roupa-referencia-teste \
    --target-accepted 2 \
    --max-attempts 4 \
    --reset-memory
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

from google.genai import types

ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.art_direction_sampler import get_art_direction_catalog, reset_art_direction_memory
from agent_runtime.casting_engine import get_casting_catalog
from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.pipeline_v2 import run_pipeline_v2


FINAL_EVAL_SCHEMA = {
    "type": "object",
    "required": [
        "garment_fidelity",
        "silhouette_fidelity",
        "texture_fidelity",
        "construction_fidelity",
        "model_change_strength",
        "environment_change_strength",
        "pose_liveliness",
        "visual_impact",
        "photorealism_score",
        "commercial_quality_score",
        "overall_score",
        "issues",
        "summary",
    ],
    "properties": {
        "garment_fidelity": {"type": "number"},
        "silhouette_fidelity": {"type": "number"},
        "texture_fidelity": {"type": "number"},
        "construction_fidelity": {"type": "number"},
        "model_change_strength": {"type": "number"},
        "environment_change_strength": {"type": "number"},
        "pose_liveliness": {"type": "number"},
        "visual_impact": {"type": "number"},
        "photorealism_score": {"type": "number"},
        "commercial_quality_score": {"type": "number"},
        "overall_score": {"type": "number"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
}


def _load_images(folder: Path) -> tuple[list[str], list[bytes]]:
    files = sorted(
        [
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
    )
    if not files:
        raise RuntimeError(f"Nenhuma imagem encontrada em {folder}")
    return [p.name for p in files], [p.read_bytes() for p in files]


def _mime_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def _mime_from_bytes(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _pick_reference_bytes_by_names(
    uploaded_filenames: list[str],
    uploaded_bytes: list[bytes],
    selected_names: list[str],
) -> list[bytes]:
    pairs = list(zip(uploaded_filenames, uploaded_bytes))
    selected: list[bytes] = []
    for name in selected_names:
        for filename, blob in pairs:
            if filename == name:
                selected.append(blob)
                break
    return selected or uploaded_bytes[:4]


def _evaluate_final_variant(
    *,
    reference_bytes: list[bytes],
    base_image_path: str,
    final_image_path: str,
    base_prompt: str,
    edit_prompt: str,
) -> dict[str, Any]:
    parts: list[types.Part] = []
    for img in reference_bytes[:6]:
        parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_bytes(img), data=img)))

    base_path = Path(base_image_path)
    final_path = Path(final_image_path)
    parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_path(base_path), data=base_path.read_bytes())))
    parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_path(final_path), data=final_path.read_bytes())))
    parts.append(
        types.Part(
            text=(
                "The first images are garment references. The next image is the chosen faithful base image from stage 1. "
                "The last image is the final pipeline output. Evaluate whether the final output preserves the garment while "
                "creating a clearly different Brazilian woman, a distinct environment, and a more alive commercial pose. "
                "Focus on garment fidelity, construction, model change, environment change, pose liveliness, visual impact, "
                "photorealism, and commercial quality. Return JSON only.\n\n"
                f"Base prompt:\n{base_prompt[:900]}\n\nFinal prompt:\n{edit_prompt[:1200]}"
            )
        )
    )
    resp = generate_structured_json(
        parts=parts,
        schema=FINAL_EVAL_SCHEMA,
        temperature=0.1,
        max_tokens=900,
        thinking_budget=0,
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, dict):
        return parsed
    text = "".join(getattr(part, "text", "") for part in (getattr(resp, "parts", None) or []))
    return json.loads(text)


def _quick_pose_score(pose_family: str) -> float:
    mapping = {
        "paused_mid_step": 0.9,
        "standing_3q_relaxed": 0.84,
        "standing_full_shift": 0.8,
        "front_relaxed_hold": 0.74,
    }
    return mapping.get(str(pose_family or ""), 0.76)


def _quick_impact_score(scene_family: str) -> float:
    mapping = {
        "br_curitiba_cafe": 0.9,
        "br_recife_balcony": 0.88,
        "br_pinheiros_living": 0.86,
        "br_showroom_sp": 0.78,
    }
    return mapping.get(str(scene_family or ""), 0.8)


def _quick_evaluation_from_report(report: dict[str, Any]) -> dict[str, Any]:
    stage1 = report.get("stage1", {}) or {}
    stage2_runs = list((report.get("stage2", {}) or {}).get("runs", []) or [])
    final_run = stage2_runs[0] if stage2_runs else {}
    base_assessment = stage1.get("assessment", {}) or {}
    final_assessment = final_run.get("assessment", {}) or {}
    summary = final_run.get("art_direction_summary", {}) or {}
    stage1_candidate = float(base_assessment.get("candidate_score", 0.0) or 0.0)
    stage1_technical = float(base_assessment.get("technical_score", 0.0) or 0.0)
    stage2_candidate = float(final_assessment.get("candidate_score", 0.0) or 0.0)
    stage2_technical = float(final_assessment.get("technical_score", 0.0) or 0.0)
    garment_fidelity = round(min(stage1_candidate, stage2_candidate), 3)
    construction_fidelity = round(min(stage1_technical, stage2_technical), 3)
    pose_liveliness = round(_quick_pose_score(str(summary.get("pose_family", "") or "")), 3)
    visual_impact = round(_quick_impact_score(str(summary.get("scene_family", "") or "")), 3)
    overall = round(
        max(
            0.0,
            min(
                1.0,
                0.38 * garment_fidelity
                + 0.20 * construction_fidelity
                + 0.16 * pose_liveliness
                + 0.16 * visual_impact
                + 0.10 * stage2_candidate,
            ),
        ),
        3,
    )
    # model_change_strength e environment_change_strength são métricas de
    # avaliação visual (prompt strategy) — não podem ser inferidas de metadados.
    # Requerem avaliação multimodal real (_evaluate_final_variant).
    # O quick gate NÃO deve inventar valores para elas.
    return {
        "garment_fidelity": garment_fidelity,
        "silhouette_fidelity": garment_fidelity,
        "texture_fidelity": stage2_candidate,
        "construction_fidelity": construction_fidelity,
        "model_change_strength": None,  # requer avaliação visual
        "environment_change_strength": None,  # requer avaliação visual
        "pose_liveliness": pose_liveliness,
        "visual_impact": visual_impact,
        "photorealism_score": stage2_technical,
        "commercial_quality_score": stage2_candidate,
        "overall_score": overall,
        "issues": [],
        "summary": "Quick gate derived from stage assessments and art direction summary. "
                   "model_change and environment_change require visual confirmation.",
    }


def _diversity_score(summary: dict[str, Any], accepted_summaries: list[dict[str, Any]]) -> float:
    if not accepted_summaries:
        return 1.0

    def _similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
        score = 0.0
        if a.get("scene_family") == b.get("scene_family"):
            score += 0.35
        if a.get("casting_family") == b.get("casting_family"):
            score += 0.30
        if a.get("pose_family") == b.get("pose_family"):
            score += 0.20
        if a.get("styling_profile") == b.get("styling_profile"):
            score += 0.10
        if a.get("camera_profile") == b.get("camera_profile"):
            score += 0.05
        return min(1.0, score)

    worst_similarity = max(_similarity(summary, other) for other in accepted_summaries)
    return round(max(0.0, 1.0 - worst_similarity), 3)


def _accept_result(
    evaluation: dict[str, Any],
    diversity_score: float,
    *,
    min_garment: float,
    min_construction: float,
    min_pose: float,
    min_impact: float,
    min_diversity: float,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if float(evaluation.get("garment_fidelity", 0.0) or 0.0) < min_garment:
        reasons.append("low_garment_fidelity")
    if float(evaluation.get("construction_fidelity", 0.0) or 0.0) < min_construction:
        reasons.append("low_construction_fidelity")
    if float(evaluation.get("pose_liveliness", 0.0) or 0.0) < min_pose:
        reasons.append("low_pose_liveliness")
    if float(evaluation.get("visual_impact", 0.0) or 0.0) < min_impact:
        reasons.append("low_visual_impact")
    if diversity_score < min_diversity:
        reasons.append("low_diversity")
    return (not reasons, reasons)


def _scene_preference_for_scene(scene: dict[str, Any]) -> str:
    tags = set(str(tag) for tag in (scene.get("tags") or []))
    if "outdoor" in tags or "balcony" in tags:
        return "outdoor_br"
    if "indoor" in tags or "showroom" in tags or "cafe" in tags or "apartment" in tags:
        return "indoor_br"
    return "auto_br"


def _preset_for_scene(scene: dict[str, Any], prefer_recovery: bool) -> str:
    if prefer_recovery:
        return "catalog_clean"
    tags = set(str(tag) for tag in (scene.get("tags") or []))
    if "showroom" in tags or "premium" in tags:
        return "premium_lifestyle"
    if "cafe" in tags or "lifestyle" in tags or "balcony" in tags:
        return "marketplace_lifestyle"
    return "premium_lifestyle"


def _choose_next_targets(
    *,
    attempt_index: int,
    scenes: list[dict[str, Any]],
    poses: list[dict[str, Any]],
    casting_families: list[dict[str, Any]],
    accepted_attempts: list[dict[str, Any]],
    previous_attempt: Optional[dict[str, Any]],
) -> dict[str, Any]:
    used_scene_ids = {a.get("art_direction_summary", {}).get("scene_family") for a in accepted_attempts}
    used_pose_ids = {a.get("art_direction_summary", {}).get("pose_family") for a in accepted_attempts}
    used_casting_ids = {a.get("art_direction_summary", {}).get("casting_family") for a in accepted_attempts}

    recovery_mode = False
    need_livelier_pose = False
    if previous_attempt:
        rejection_reasons = set(previous_attempt.get("rejection_reasons", []))
        recovery_mode = bool({"low_garment_fidelity", "low_construction_fidelity"} & rejection_reasons)
        need_livelier_pose = bool({"low_pose_liveliness", "low_visual_impact"} & rejection_reasons)

    scene_candidates = [scene for scene in scenes if scene.get("id") not in used_scene_ids] or scenes
    if recovery_mode:
        scene_candidates = [
            scene for scene in scene_candidates
            if "showroom" in set(scene.get("tags") or []) or "apartment" in set(scene.get("tags") or [])
        ] or scene_candidates
    scene = scene_candidates[attempt_index % len(scene_candidates)]

    pose_candidates = [pose for pose in poses if pose.get("id") not in used_pose_ids] or poses
    if need_livelier_pose:
        pose_candidates = [
            pose for pose in pose_candidates
            if "movement" in set(pose.get("tags") or []) or "lifestyle" in set(pose.get("tags") or [])
        ] or pose_candidates
    if not recovery_mode and not need_livelier_pose:
        pose_candidates = [
            pose for pose in pose_candidates
            if "stable" in set(pose.get("tags") or []) and "lifestyle" in set(pose.get("tags") or [])
        ] or pose_candidates
    pose = pose_candidates[attempt_index % len(pose_candidates)]

    casting_candidates = [family for family in casting_families if family.get("id") not in used_casting_ids] or casting_families
    casting = casting_candidates[attempt_index % len(casting_candidates)]

    correction_notes: list[str] = []
    if previous_attempt:
        rejection_reasons = set(previous_attempt.get("rejection_reasons", []))
        if "low_garment_fidelity" in rejection_reasons or "low_construction_fidelity" in rejection_reasons:
            correction_notes.append("Keep the ruana silhouette exact, with unchanged cocoon side drop and cape-like arm coverage.")
        if "low_pose_liveliness" in rejection_reasons:
            correction_notes.append("Use a more alive but still readable commercial pose, with subtle motion or a natural stance shift.")
        if "low_visual_impact" in rejection_reasons:
            correction_notes.append("Increase the sense of premium impact and lifestyle energy without compromising realism.")
        if "low_diversity" in rejection_reasons:
            correction_notes.append("Clearly differentiate this result from previous accepted outputs in scene, model impression, and pose energy.")

    prompt_parts = [
        f"Target scene direction: {scene.get('description', '')}.",
        str(pose.get("pose_description", "") or "").strip(),
        "Prioritize a clearly different Brazilian woman, a convincing real environment, and strong garment readability.",
    ]
    prompt_parts.extend(note for note in correction_notes if note)

    return {
        "preset": _preset_for_scene(scene, recovery_mode),
        "scene_preference": _scene_preference_for_scene(scene),
        "fidelity_mode": "estrita" if recovery_mode else "balanceada",
        "prompt": " ".join(part.strip() for part in prompt_parts if part.strip()),
        "art_direction_request": {
            "forced_casting_family_id": casting.get("id"),
            "preferred_scene_ids": [scene.get("id")],
            "preferred_pose_ids": [pose.get("id")],
        },
        "target_scene": scene.get("id"),
        "target_pose": pose.get("id"),
        "target_casting": casting.get("id"),
    }


def _write_report(run_dir: Path, payload: dict[str, Any]) -> None:
    (run_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Pipeline V2 Continuous Validation Loop",
        "",
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Folder: `{payload.get('folder')}`",
        f"- Uploaded files: {', '.join(payload.get('uploaded_filenames', []))}",
        f"- Accepted: {payload.get('accepted_count')} / {payload.get('attempt_count')}",
        "",
        "## Attempts",
        "",
    ]

    for attempt in payload.get("attempts", []):
        evaluation = attempt.get("evaluation", {}) or {}
        confirmed = attempt.get("confirmed_evaluation", {}) or {}
        lines.extend(
            [
                f"### Attempt {attempt.get('attempt_index')}",
                "",
                f"- Accepted: {attempt.get('accepted')}",
                f"- Rejection reasons: {', '.join(attempt.get('rejection_reasons', [])) or '-'}",
                f"- Preset: {attempt.get('preset')}",
                f"- Scene preference: {attempt.get('scene_preference')}",
                f"- Fidelity mode: {attempt.get('fidelity_mode')}",
                f"- Uploaded files: {', '.join(attempt.get('uploaded_filenames', []))}",
                f"- Selector base refs: {', '.join(attempt.get('selected_names', {}).get('base_generation', []))}",
                f"- Selector strict refs: {', '.join(attempt.get('selected_names', {}).get('strict_single_pass', []))}",
                f"- Selector edit anchors: {', '.join(attempt.get('selected_names', {}).get('edit_anchors', []))}",
                f"- Base image: `{attempt.get('base_image_path')}`",
                f"- Final image: `{attempt.get('final_image_path')}`",
                f"- Report: `{attempt.get('report_path')}`",
                f"- Art direction: {json.dumps(attempt.get('art_direction_summary', {}), ensure_ascii=False)}",
                f"- Diversity score: {attempt.get('diversity_score')}",
                f"- Quick garment fidelity: {evaluation.get('garment_fidelity')}",
                f"- Quick construction fidelity: {evaluation.get('construction_fidelity')}",
                f"- Quick pose liveliness: {evaluation.get('pose_liveliness')}",
                f"- Quick visual impact: {evaluation.get('visual_impact')}",
                f"- Quick overall: {evaluation.get('overall_score')}",
                f"- Quick summary: {evaluation.get('summary')}",
                f"- Confirmed overall: {confirmed.get('overall_score') if confirmed else '-'}",
                f"- Confirmed garment fidelity: {confirmed.get('garment_fidelity') if confirmed else '-'}",
                f"- Confirmed pose liveliness: {confirmed.get('pose_liveliness') if confirmed else '-'}",
                f"- Confirmed summary: {confirmed.get('summary') if confirmed else '-'}",
                "",
            ]
        )

    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _build_payload(
    *,
    folder: Path,
    uploaded_filenames: list[str],
    attempts: list[dict[str, Any]],
    accepted_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "folder": str(folder),
        "uploaded_filenames": uploaded_filenames,
        "attempt_count": len(attempts),
        "accepted_count": len(accepted_attempts),
        "attempts": attempts,
        "accepted_final_images": [item.get("final_image_path") for item in accepted_attempts],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Roda um loop continuo de validacao autocorretiva sobre o pipeline_v2.")
    parser.add_argument("--folder", required=True, help="Pasta com imagens de referencia")
    parser.add_argument("--target-accepted", type=int, default=2, help="Numero de resultados aceitos desejado")
    parser.add_argument("--max-attempts", type=int, default=4, help="Numero maximo de tentativas")
    parser.add_argument("--aspect-ratio", default="4:5", help="Aspect ratio do teste")
    parser.add_argument("--resolution", default="1K", help="Resolucao do teste")
    parser.add_argument("--reset-memory", action="store_true", help="Reseta a memoria do sampler antes da rodada")
    parser.add_argument("--min-garment", type=float, default=0.90, help="Threshold minimo de garment fidelity")
    parser.add_argument("--min-construction", type=float, default=0.88, help="Threshold minimo de construction fidelity")
    parser.add_argument("--min-pose", type=float, default=0.80, help="Threshold minimo de pose liveliness")
    parser.add_argument("--min-impact", type=float, default=0.84, help="Threshold minimo de visual impact")
    parser.add_argument("--min-diversity", type=float, default=0.55, help="Threshold minimo de diversidade")
    parser.add_argument("--confirm-accepted", action="store_true", help="Roda confirmacao multimodal detalhada para os resultados aceitos")
    args = parser.parse_args()

    if args.reset_memory:
        reset_art_direction_memory()

    folder = (ROOT / args.folder).resolve() if not Path(args.folder).is_absolute() else Path(args.folder).resolve()
    uploaded_filenames, uploaded_bytes = _load_images(folder)

    catalog = get_art_direction_catalog()
    scenes = list(catalog.get("scenes", []))
    poses = list(catalog.get("poses", []))
    casting_families = get_casting_catalog()

    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "docs" / "pipeline_v2_validation_loop" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    attempts: list[dict[str, Any]] = []
    accepted_attempts: list[dict[str, Any]] = []
    previous_attempt: Optional[dict[str, Any]] = None

    for attempt_index in range(1, max(1, int(args.max_attempts)) + 1):
        plan = _choose_next_targets(
            attempt_index=attempt_index - 1,
            scenes=scenes,
            poses=poses,
            casting_families=casting_families,
            accepted_attempts=accepted_attempts,
            previous_attempt=previous_attempt,
        )

        raw = run_pipeline_v2(
            uploaded_bytes=uploaded_bytes,
            uploaded_filenames=uploaded_filenames,
            prompt=plan["prompt"],
            preset=plan["preset"],
            scene_preference=plan["scene_preference"],
            fidelity_mode=plan["fidelity_mode"],
            n_images=1,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            art_direction_request=plan["art_direction_request"],
        )

        report_path = str(raw.get("report_path") or "")
        if not report_path:
            raise RuntimeError("pipeline_v2 nao retornou report_path")

        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        stage1 = report.get("stage1", {}) or {}
        stage2_runs = list((report.get("stage2", {}) or {}).get("runs", []) or [])
        if not stage2_runs:
            raise RuntimeError("Relatorio do pipeline_v2 nao contem runs de stage2")
        final_run = stage2_runs[0]

        selected_names = report.get("selector", {}).get("selected_names", {}) or {}
        judge_reference_bytes = _pick_reference_bytes_by_names(
            uploaded_filenames=uploaded_filenames,
            uploaded_bytes=uploaded_bytes,
            selected_names=list(selected_names.get("strict_single_pass", []) or selected_names.get("base_generation", [])),
        )
        evaluation = _quick_evaluation_from_report(report)

        art_direction_summary = final_run.get("art_direction_summary", {}) or {}
        diversity_score = _diversity_score(
            art_direction_summary,
            [item.get("art_direction_summary", {}) or {} for item in accepted_attempts],
        )
        accepted, rejection_reasons = _accept_result(
            evaluation,
            diversity_score,
            min_garment=float(args.min_garment),
            min_construction=float(args.min_construction),
            min_pose=float(args.min_pose),
            min_impact=float(args.min_impact),
            min_diversity=float(args.min_diversity),
        )

        attempt_record = {
            "attempt_index": attempt_index,
            "accepted": accepted,
            "rejection_reasons": rejection_reasons,
            "preset": plan["preset"],
            "scene_preference": plan["scene_preference"],
            "fidelity_mode": plan["fidelity_mode"],
            "prompt": plan["prompt"],
            "art_direction_request": plan["art_direction_request"],
            "uploaded_filenames": report.get("request", {}).get("uploaded_filenames", uploaded_filenames),
            "selected_names": selected_names,
            "selector_stats": report.get("selector", {}).get("stats", {}),
            "base_image_path": (stage1.get("result") or {}).get("path"),
            "final_image_path": (final_run.get("result") or {}).get("path"),
            "report_path": report_path,
            "report_url": raw.get("report_url"),
            "art_direction_summary": art_direction_summary,
            "evaluation": evaluation,
            "diversity_score": diversity_score,
        }
        attempts.append(attempt_record)
        previous_attempt = attempt_record
        if accepted:
            accepted_attempts.append(attempt_record)
        _write_report(
            run_dir,
            _build_payload(
                folder=folder,
                uploaded_filenames=uploaded_filenames,
                attempts=attempts,
                accepted_attempts=accepted_attempts,
            ),
        )
        if len(accepted_attempts) >= max(1, int(args.target_accepted)):
            break

    if args.confirm_accepted:
        for attempt in accepted_attempts:
            report_path = str(attempt.get("report_path") or "")
            report = json.loads(Path(report_path).read_text(encoding="utf-8"))
            stage1 = report.get("stage1", {}) or {}
            stage2_runs = list((report.get("stage2", {}) or {}).get("runs", []) or [])
            if not stage2_runs:
                continue
            final_run = stage2_runs[0]
            selected_names = report.get("selector", {}).get("selected_names", {}) or {}
            judge_reference_bytes = _pick_reference_bytes_by_names(
                uploaded_filenames=uploaded_filenames,
                uploaded_bytes=uploaded_bytes,
                selected_names=list(selected_names.get("strict_single_pass", []) or selected_names.get("base_generation", [])),
            )
            attempt["confirmed_evaluation"] = _evaluate_final_variant(
                reference_bytes=judge_reference_bytes,
                base_image_path=str((stage1.get("result") or {}).get("path") or ""),
                final_image_path=str((final_run.get("result") or {}).get("path") or ""),
                base_prompt=str(stage1.get("prompt") or ""),
                edit_prompt=str(final_run.get("edit_prompt") or ""),
            )

    payload = _build_payload(
        folder=folder,
        uploaded_filenames=uploaded_filenames,
        attempts=attempts,
        accepted_attempts=accepted_attempts,
    )
    _write_report(run_dir, payload)
    print(json.dumps({"run_dir": str(run_dir), **payload}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
