"""
Validation harness do casting engine experimental.

Uso:
  PYTHONPATH=app/backend app/.venv/bin/python app/backend/casting_engine_validation.py \
    --folder docs/roupa-referencia-teste
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.casting_engine import reset_brazilian_casting_state, select_brazilian_casting_profile
from agent_runtime.reference_selector import select_reference_subsets
from agent_runtime.two_pass_flow import (
    build_parameterized_two_pass_edit_prompt,
    build_structural_hint,
)
from generator import edit_image, generate_images
from pipeline_effectiveness import classify_visual_context
from routers.generate import _build_strict_reference_prompt
from two_pass_validation import _evaluate_base_generation, _evaluate_edit


def _load_images(folder: Path) -> tuple[list[str], list[bytes]]:
    files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}])
    if not files:
        raise RuntimeError(f"Nenhuma imagem encontrada em {folder}")
    return [p.name for p in files], [p.read_bytes() for p in files]


def _candidate_sort_key(candidate: dict[str, Any]) -> tuple[float, float, float]:
    evaluation = candidate.get("evaluation", {}) or {}
    return (
        float(evaluation.get("overall_score", 0.0) or 0.0),
        float(evaluation.get("garment_fidelity", 0.0) or 0.0),
        float(evaluation.get("construction_fidelity", 0.0) or 0.0),
    )


def _write_report(
    run_dir: Path,
    *,
    selector_output: dict[str, Any],
    base_prompt: str,
    scene_description: str,
    pose_description: str,
    base_candidates: list[dict[str, Any]],
    best_base: dict[str, Any],
    casting_results: list[dict[str, Any]],
) -> None:
    payload = {
        "selector_stats": selector_output.get("stats", {}),
        "selected_names": selector_output.get("selected_names", {}),
        "base_prompt": base_prompt,
        "scene_description": scene_description,
        "pose_description": pose_description,
        "base_candidates": base_candidates,
        "best_base": best_base,
        "casting_results": casting_results,
    }
    (run_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Casting Engine Validation",
        "",
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Shared Scene",
        "",
        f"- Scene description: {scene_description}",
        f"- Pose description: {pose_description}",
        "",
        "## Base Winner",
        "",
        f"- Image: `{best_base.get('path')}`",
        f"- Score: {(best_base.get('evaluation') or {}).get('overall_score')}",
        "",
        "## Casting Variants",
        "",
    ]

    for result in casting_results:
        evaluation = result.get("evaluation", {}) or {}
        profile = result.get("casting_profile", {}) or {}
        lines.extend(
            [
                f"### {profile.get('family_label')} - {result.get('variant')}",
                "",
                f"- Image: `{(result.get('output') or {}).get('path')}`",
                f"- Overall: {evaluation.get('overall_score')}",
                f"- Model change: {evaluation.get('model_change_strength')}",
                f"- Garment fidelity: {evaluation.get('garment_fidelity')}",
                f"- Family: {profile.get('family_id')}",
                f"- Age: {profile.get('age')}",
                f"- Skin: {profile.get('skin')}",
                f"- Hair: {profile.get('hair')}",
                f"- Makeup: {profile.get('makeup')}",
                f"- Expression: {profile.get('expression')}",
                "",
                "```text",
                result.get("edit_prompt", ""),
                "```",
                "",
            ]
        )

    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida o casting engine experimental.")
    parser.add_argument("--folder", required=True, help="Pasta com imagens de referencia")
    parser.add_argument("--base-candidates", type=int, default=2, help="Numero de bases da etapa 1")
    parser.add_argument("--n-castings", type=int, default=3, help="Numero de perfis de casting a testar")
    parser.add_argument("--reset-state", action="store_true", help="Reseta a memoria curta do casting engine antes da rodada")
    parser.add_argument(
        "--scene-description",
        default="refined Brazilian premium showroom with softly textured neutral walls, pale stone floor, clean daylight, and minimal decor",
        help="Descricao compartilhada de cena para isolar casting",
    )
    parser.add_argument(
        "--pose-description",
        default="Use a clean standing catalog pose with full garment visibility.",
        help="Descricao compartilhada de pose para isolar casting",
    )
    args = parser.parse_args()

    if args.reset_state:
        reset_brazilian_casting_state()

    folder = (ROOT / args.folder).resolve() if not Path(args.folder).is_absolute() else Path(args.folder).resolve()
    names, uploaded = _load_images(folder)

    selector_output = select_reference_subsets(uploaded_images=uploaded, filenames=names)
    unified = selector_output.get("unified_triage") or {}
    classifier_summary = classify_visual_context(
        user_prompt=None,
        image_analysis=unified.get("image_analysis", ""),
        has_images=True,
        reference_pack_stats=selector_output.get("stats", {}),
    )
    guided_brief = {
        "scene": {"type": "interno"},
        "pose": {"style": "tradicional"},
        "garment": {"set_mode": "unica"},
    }
    structural_contract = unified.get("structural_contract")
    base_prompt = _build_strict_reference_prompt(
        user_prompt=None,
        classifier_summary=classifier_summary,
        guided_brief=guided_brief,
        structural_contract=structural_contract,
    )
    structural_hint = build_structural_hint(structural_contract)

    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "docs" / "casting_engine_validation" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    base_results = generate_images(
        prompt=base_prompt,
        thinking_level="MINIMAL",
        aspect_ratio="4:5",
        resolution="1K",
        n_images=max(1, min(int(args.base_candidates), 4)),
        uploaded_images=selector_output.get("selected_bytes", {}).get("base_generation", []),
        session_id=f"castbase_{run_stamp}"[-24:],
        structural_hint=structural_hint,
    )

    eval_refs = selector_output.get("selected_bytes", {}).get("strict_single_pass", []) or selector_output.get("selected_bytes", {}).get("base_generation", [])
    base_candidates: list[dict[str, Any]] = []
    for result in base_results:
        evaluation = _evaluate_base_generation(
            reference_bytes=eval_refs,
            generated_image_path=result["path"],
            prompt=base_prompt,
        )
        base_candidates.append({**result, "evaluation": evaluation})

    best_base = max(base_candidates, key=_candidate_sort_key)
    casting_results: list[dict[str, Any]] = []

    for idx in range(max(1, int(args.n_castings))):
        casting_profile = select_brazilian_casting_profile(
            seed_hint=f"{run_stamp}:{idx}",
            commit=True,
        )
        edit_prompt = build_parameterized_two_pass_edit_prompt(
            structural_contract,
            casting_profile=casting_profile,
            scene_description=args.scene_description,
            pose_description=args.pose_description,
            innerwear="clean white crew-neck tee",
        )
        edited = edit_image(
            source_image_bytes=Path(best_base["path"]).read_bytes(),
            edit_prompt=edit_prompt,
            aspect_ratio="4:5",
            resolution="1K",
            session_id=f"casting_{run_stamp}_{idx}"[-24:],
            reference_images_bytes=selector_output.get("selected_bytes", {}).get("edit_anchors", []),
        )[0]
        evaluation = _evaluate_edit(
            reference_bytes=eval_refs,
            base_image_path=best_base["path"],
            edited_image_path=edited["path"],
            base_prompt=base_prompt,
            edit_prompt=edit_prompt,
        )
        casting_results.append(
            {
                "variant": f"cast_{idx + 1}",
                "casting_profile": casting_profile,
                "edit_prompt": edit_prompt,
                "output": edited,
                "evaluation": evaluation,
            }
        )

    _write_report(
        run_dir,
        selector_output=selector_output,
        base_prompt=base_prompt,
        scene_description=args.scene_description,
        pose_description=args.pose_description,
        base_candidates=base_candidates,
        best_base=best_base,
        casting_results=casting_results,
    )
    print(json.dumps({"run_dir": str(run_dir), "best_base": best_base, "casting_results": casting_results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
