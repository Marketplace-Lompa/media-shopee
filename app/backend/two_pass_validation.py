"""
Validation harness do fluxo experimental two-pass.

Uso:
  PYTHONPATH=app/backend app/.venv/bin/python app/backend/two_pass_validation.py \
    --folder docs/roupa-referencia-teste
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, List

from google.genai import types

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.reference_selector import select_reference_subsets
from agent_runtime.two_pass_flow import build_structural_hint, build_two_pass_edit_prompt
from generator import edit_image, generate_images
from pipeline_effectiveness import classify_visual_context
from routers.generate import _build_strict_reference_prompt


BASE_EVAL_SCHEMA = {
    "type": "object",
    "required": [
        "garment_fidelity",
        "silhouette_fidelity",
        "texture_fidelity",
        "construction_fidelity",
        "natural_model_score",
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
        "natural_model_score": {"type": "number"},
        "photorealism_score": {"type": "number"},
        "commercial_quality_score": {"type": "number"},
        "overall_score": {"type": "number"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
}

EDIT_EVAL_SCHEMA = {
    "type": "object",
    "required": [
        "garment_fidelity",
        "silhouette_fidelity",
        "texture_fidelity",
        "construction_fidelity",
        "model_change_strength",
        "environment_change_strength",
        "innerwear_change_strength",
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
        "innerwear_change_strength": {"type": "number"},
        "photorealism_score": {"type": "number"},
        "commercial_quality_score": {"type": "number"},
        "overall_score": {"type": "number"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
}


def _load_images(folder: Path) -> tuple[list[str], list[bytes]]:
    files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}])
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


def _evaluate_base_generation(reference_bytes: list[bytes], generated_image_path: str, prompt: str) -> dict[str, Any]:
    parts: List[types.Part] = []
    for img in reference_bytes[:6]:
        parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_bytes(img), data=img)))
    gen_path = Path(generated_image_path)
    parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_path(gen_path), data=gen_path.read_bytes())))
    parts.append(
        types.Part(
            text=(
                "The first images are garment references. The last image is a generated fashion candidate. "
                "Evaluate the candidate against the references. Ignore the original reference person identity and background. "
                "Focus on garment fidelity, silhouette, construction, texture, model naturalness, photorealism, and commercial catalog quality. "
                "Return concise JSON only. Prompt used:\n"
                f"{prompt[:1800]}"
            )
        )
    )
    resp = generate_structured_json(
        parts=parts,
        schema=BASE_EVAL_SCHEMA,
        temperature=0.1,
        max_tokens=700,
        thinking_budget=0,
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, dict):
        return parsed
    text = "".join(getattr(part, "text", "") for part in (getattr(resp, "parts", None) or []))
    return json.loads(text)


def _evaluate_edit(
    reference_bytes: list[bytes],
    base_image_path: str,
    edited_image_path: str,
    base_prompt: str,
    edit_prompt: str,
) -> dict[str, Any]:
    parts: List[types.Part] = []
    for img in reference_bytes[:6]:
        parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_bytes(img), data=img)))

    base_path = Path(base_image_path)
    edited_path = Path(edited_image_path)
    parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_path(base_path), data=base_path.read_bytes())))
    parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_path(edited_path), data=edited_path.read_bytes())))
    parts.append(
        types.Part(
            text=(
                "The first images are garment references. The next image is the chosen stage-1 faithful base image. "
                "The last image is the stage-2 edited output. Evaluate whether the edited output preserves the garment while clearly changing model identity, environment, and innerwear. "
                "Ignore the original reference person identity and background. "
                "Return concise JSON only. Base prompt:\n"
                f"{base_prompt[:900]}\n\nEdit prompt:\n{edit_prompt[:900]}"
            )
        )
    )
    resp = generate_structured_json(
        parts=parts,
        schema=EDIT_EVAL_SCHEMA,
        temperature=0.1,
        max_tokens=800,
        thinking_budget=0,
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, dict):
        return parsed
    text = "".join(getattr(part, "text", "") for part in (getattr(resp, "parts", None) or []))
    return json.loads(text)


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
    edit_prompt: str,
    base_candidates: list[dict[str, Any]],
    best_base: dict[str, Any],
    edited_result: dict[str, Any],
    edited_evaluation: dict[str, Any],
) -> None:
    summary = {
        "selector_stats": selector_output.get("stats", {}),
        "selected_names": selector_output.get("selected_names", {}),
        "base_prompt": base_prompt,
        "edit_prompt": edit_prompt,
        "base_candidates": base_candidates,
        "best_base": best_base,
        "edited_result": edited_result,
        "edited_evaluation": edited_evaluation,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Two-Pass Validation",
        "",
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Selector",
        "",
        f"- Base generation: {', '.join(selector_output.get('selected_names', {}).get('base_generation', []))}",
        f"- Strict single-pass eval refs: {', '.join(selector_output.get('selected_names', {}).get('strict_single_pass', []))}",
        f"- Edit anchors: {', '.join(selector_output.get('selected_names', {}).get('edit_anchors', []))}",
        "",
        "## Stage 1 - Base Candidates",
        "",
    ]

    for idx, candidate in enumerate(base_candidates, start=1):
        evaluation = candidate.get("evaluation", {}) or {}
        lines.extend(
            [
                f"### Candidate {idx}",
                "",
                f"- Image: `{candidate.get('path')}`",
                f"- Overall: {evaluation.get('overall_score')}",
                f"- Garment fidelity: {evaluation.get('garment_fidelity')}",
                f"- Silhouette: {evaluation.get('silhouette_fidelity')}",
                f"- Texture: {evaluation.get('texture_fidelity')}",
                f"- Construction: {evaluation.get('construction_fidelity')}",
                f"- Commercial quality: {evaluation.get('commercial_quality_score')}",
                f"- Summary: {evaluation.get('summary')}",
                "",
            ]
        )

    best_eval = best_base.get("evaluation", {}) or {}
    edited_eval = edited_evaluation or {}
    lines.extend(
        [
            "## Stage 1 Winner",
            "",
            f"- Image: `{best_base.get('path')}`",
            f"- Overall: {best_eval.get('overall_score')}",
            f"- Garment fidelity: {best_eval.get('garment_fidelity')}",
            "",
            "## Stage 2 - Edited Result",
            "",
            f"- Image: `{edited_result.get('path')}`",
            f"- Overall: {edited_eval.get('overall_score')}",
            f"- Garment fidelity: {edited_eval.get('garment_fidelity')}",
            f"- Model change: {edited_eval.get('model_change_strength')}",
            f"- Environment change: {edited_eval.get('environment_change_strength')}",
            f"- Innerwear change: {edited_eval.get('innerwear_change_strength')}",
            f"- Photorealism: {edited_eval.get('photorealism_score')}",
            f"- Commercial quality: {edited_eval.get('commercial_quality_score')}",
            f"- Summary: {edited_eval.get('summary')}",
            "",
            "## Base Prompt",
            "",
            "```text",
            base_prompt,
            "```",
            "",
            "## Edit Prompt",
            "",
            "```text",
            edit_prompt,
            "```",
            "",
            "## Stage 2 Issues",
            "",
        ]
    )
    for issue in edited_eval.get("issues", []) or []:
        lines.append(f"- {issue}")

    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida o fluxo experimental two-pass com selector automatico.")
    parser.add_argument("--folder", required=True, help="Pasta com imagens de referencia")
    parser.add_argument("--base-candidates", type=int, default=2, help="Numero de bases da etapa 1")
    parser.add_argument("--scene-type", default="interno", choices=["interno", "externo"], help="Cena alvo da validacao")
    parser.add_argument("--pose-style", default="tradicional", choices=["tradicional", "criativa"], help="Pose alvo da validacao")
    parser.add_argument("--innerwear", default="clean white crew-neck tee", help="Roupa interna da etapa 2")
    parser.add_argument("--user-prompt", default=None, help="Direcao comercial opcional")
    args = parser.parse_args()

    folder = (ROOT / args.folder).resolve() if not Path(args.folder).is_absolute() else Path(args.folder).resolve()
    names, uploaded = _load_images(folder)

    selector_output = select_reference_subsets(
        uploaded_images=uploaded,
        filenames=names,
        user_prompt=args.user_prompt,
    )
    unified = selector_output.get("unified_triage") or {}
    classifier_summary = classify_visual_context(
        user_prompt=args.user_prompt,
        image_analysis=unified.get("image_analysis", ""),
        has_images=True,
        reference_pack_stats=selector_output.get("stats", {}),
    )

    guided_brief = {
        "scene": {"type": args.scene_type},
        "pose": {"style": args.pose_style},
        "garment": {"set_mode": "unica"},
    }
    structural_contract = unified.get("structural_contract")
    base_prompt = _build_strict_reference_prompt(
        user_prompt=args.user_prompt,
        classifier_summary=classifier_summary,
        guided_brief=guided_brief,
        structural_contract=structural_contract,
    )
    structural_hint = build_structural_hint(structural_contract)
    edit_prompt = build_two_pass_edit_prompt(
        structural_contract,
        scene_type=args.scene_type,
        pose_style=args.pose_style,
        innerwear=args.innerwear,
        user_prompt=args.user_prompt,
    )

    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "docs" / "two_pass_validation" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    base_results = generate_images(
        prompt=base_prompt,
        thinking_level="MINIMAL",
        aspect_ratio="4:5",
        resolution="1K",
        n_images=max(1, min(int(args.base_candidates), 4)),
        uploaded_images=selector_output.get("selected_bytes", {}).get("base_generation", []),
        session_id=f"twopassb_{run_stamp}"[-24:],
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
        base_candidates.append({
            **result,
            "evaluation": evaluation,
        })

    best_base = max(base_candidates, key=_candidate_sort_key)
    edited_results = edit_image(
        source_image_bytes=Path(best_base["path"]).read_bytes(),
        edit_prompt=edit_prompt,
        aspect_ratio="4:5",
        resolution="1K",
        session_id=f"twopasse_{run_stamp}"[-24:],
        reference_images_bytes=selector_output.get("selected_bytes", {}).get("edit_anchors", []),
    )
    edited_result = edited_results[0]
    edited_evaluation = _evaluate_edit(
        reference_bytes=eval_refs,
        base_image_path=best_base["path"],
        edited_image_path=edited_result["path"],
        base_prompt=base_prompt,
        edit_prompt=edit_prompt,
    )

    _write_report(
        run_dir,
        selector_output=selector_output,
        base_prompt=base_prompt,
        edit_prompt=edit_prompt,
        base_candidates=base_candidates,
        best_base=best_base,
        edited_result=edited_result,
        edited_evaluation=edited_evaluation,
    )

    print(json.dumps({
        "run_dir": str(run_dir),
        "selected_names": selector_output.get("selected_names", {}),
        "base_prompt": base_prompt,
        "edit_prompt": edit_prompt,
        "base_candidates": base_candidates,
        "best_base": best_base,
        "edited_result": edited_result,
        "edited_evaluation": edited_evaluation,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
