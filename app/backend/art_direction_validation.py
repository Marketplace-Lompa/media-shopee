"""
Validation harness do art direction sampler experimental.

Uso:
  PYTHONPATH=app/backend app/.venv/bin/python app/backend/art_direction_validation.py \
    --folder docs/roupa-referencia-teste \
    --base-image app/outputs/castbase_20260311_192658/gen_castbase_20260311_192658_1.png
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

from agent_runtime.art_direction_sampler import reset_art_direction_memory, sample_art_direction
from agent_runtime.reference_selector import select_reference_subsets
from agent_runtime.two_pass_flow import (
    build_art_direction_two_pass_edit_prompt,
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
    best_base: dict[str, Any],
    base_prompt: str,
    selector_output: dict[str, Any],
    garment_material: str,
    garment_color: str,
    results: list[dict[str, Any]],
) -> None:
    payload = {
        "selected_names": selector_output.get("selected_names", {}),
        "selector_stats": selector_output.get("stats", {}),
        "base_prompt": base_prompt,
        "best_base": best_base,
        "garment_material": garment_material,
        "garment_color": garment_color,
        "results": results,
    }
    (run_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Art Direction Sampler Validation",
        "",
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Base Winner",
        "",
        f"- Image: `{best_base.get('path')}`",
        f"- Score: {(best_base.get('evaluation') or {}).get('overall_score')}",
        "",
        "## Variants",
        "",
    ]

    for result in results:
        evaluation = result.get("evaluation", {}) or {}
        art_direction = result.get("art_direction", {}) or {}
        summary = art_direction.get("summary", {}) or {}
        lines.extend(
            [
                f"### {result.get('variant')}",
                "",
                f"- Image: `{(result.get('output') or {}).get('path')}`",
                f"- Overall: {evaluation.get('overall_score')}",
                f"- Garment fidelity: {evaluation.get('garment_fidelity')}",
                f"- Model change: {evaluation.get('model_change_strength')}",
                f"- Environment change: {evaluation.get('environment_change_strength')}",
                f"- Casting: {summary.get('casting_family')}",
                f"- Scene: {summary.get('scene_family')}",
                f"- Pose: {summary.get('pose_family')}",
                f"- Camera: {summary.get('camera_profile')}",
                f"- Lighting: {summary.get('lighting_profile')}",
                f"- Styling: {summary.get('styling_profile')}",
                "",
                "```text",
                result.get("edit_prompt", ""),
                "```",
                "",
            ]
        )

    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida o art direction sampler experimental.")
    parser.add_argument("--folder", required=True, help="Pasta com imagens de referencia")
    parser.add_argument("--base-image", default="", help="Imagem-base pronta para pular a etapa 1")
    parser.add_argument("--base-candidates", type=int, default=2, help="Numero de bases se precisar gerar")
    parser.add_argument("--n-variants", type=int, default=3, help="Numero de variantes de art direction")
    parser.add_argument("--reset-state", action="store_true", help="Reseta a memoria do sampler antes da rodada")
    parser.add_argument("--user-prompt", default="", help="Direcao comercial opcional")
    parser.add_argument("--garment-material", default="crochet knit wool blend", help="Texto do material para o kernel")
    parser.add_argument("--garment-color", default="olive green and dusty rose striped yarn", help="Texto de cor para o kernel")
    args = parser.parse_args()

    if args.reset_state:
        reset_art_direction_memory()

    folder = (ROOT / args.folder).resolve() if not Path(args.folder).is_absolute() else Path(args.folder).resolve()
    names, uploaded = _load_images(folder)

    selector_output = select_reference_subsets(uploaded_images=uploaded, filenames=names)
    unified = selector_output.get("unified_triage") or {}
    classifier_summary = classify_visual_context(
        user_prompt=args.user_prompt or None,
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
        user_prompt=args.user_prompt or None,
        classifier_summary=classifier_summary,
        guided_brief=guided_brief,
        structural_contract=structural_contract,
    )
    structural_hint = build_structural_hint(structural_contract)

    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "docs" / "art_direction_validation" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.base_image:
        base_path = (ROOT / args.base_image).resolve() if not Path(args.base_image).is_absolute() else Path(args.base_image).resolve()
        best_base = {
            "path": str(base_path),
            "evaluation": {"overall_score": None},
        }
    else:
        base_results = generate_images(
            prompt=base_prompt,
            thinking_level="MINIMAL",
            aspect_ratio="4:5",
            resolution="1K",
            n_images=max(1, min(int(args.base_candidates), 4)),
            uploaded_images=selector_output.get("selected_bytes", {}).get("base_generation", []),
            session_id=f"adbase_{run_stamp}"[-24:],
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

    eval_refs = selector_output.get("selected_bytes", {}).get("strict_single_pass", []) or selector_output.get("selected_bytes", {}).get("base_generation", [])
    edit_anchors = selector_output.get("selected_bytes", {}).get("edit_anchors", [])
    results: list[dict[str, Any]] = []

    for idx in range(max(1, int(args.n_variants))):
        art_direction = sample_art_direction(
            seed_hint=f"{run_stamp}:{idx}",
            user_prompt=args.user_prompt or None,
            commit=True,
        )
        edit_prompt = build_art_direction_two_pass_edit_prompt(
            structural_contract,
            art_direction=art_direction,
            garment_material=args.garment_material,
            garment_color=args.garment_color,
            user_prompt=args.user_prompt or None,
        )
        edited = edit_image(
            source_image_bytes=Path(best_base["path"]).read_bytes(),
            edit_prompt=edit_prompt,
            aspect_ratio="4:5",
            resolution="1K",
            session_id=f"artsmp_{run_stamp}_{idx}"[-24:],
            reference_images_bytes=edit_anchors,
        )[0]
        evaluation = _evaluate_edit(
            reference_bytes=eval_refs,
            base_image_path=best_base["path"],
            edited_image_path=edited["path"],
            base_prompt=base_prompt,
            edit_prompt=edit_prompt,
        )
        results.append(
            {
                "variant": f"art_{idx + 1}",
                "art_direction": art_direction,
                "edit_prompt": edit_prompt,
                "output": edited,
                "evaluation": evaluation,
            }
        )

    _write_report(
        run_dir,
        best_base=best_base,
        base_prompt=base_prompt,
        selector_output=selector_output,
        garment_material=args.garment_material,
        garment_color=args.garment_color,
        results=results,
    )
    print(json.dumps({"run_dir": str(run_dir), "best_base": best_base, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
