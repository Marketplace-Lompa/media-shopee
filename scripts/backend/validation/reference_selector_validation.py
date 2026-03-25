"""
Validation harness do selector automatico de referencias.

Uso:
  app/.venv/bin/python scripts/backend/validation/reference_selector_validation.py \
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

ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.reference_selector import select_reference_subsets
from generator import generate_images
from pipeline_effectiveness import classify_visual_context
from routers.generate import _build_strict_reference_prompt


EVAL_SCHEMA = {
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


def _load_images(folder: Path) -> tuple[list[str], list[bytes]]:
    files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}])
    if not files:
        raise RuntimeError(f"Nenhuma imagem encontrada em {folder}")
    return [p.name for p in files], [p.read_bytes() for p in files]


def _evaluate_generation(reference_bytes: list[bytes], generated_image_path: str, prompt: str) -> dict[str, Any]:
    parts: List[types.Part] = []
    for img in reference_bytes[:6]:
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img)))
    gen_bytes = Path(generated_image_path).read_bytes()
    parts.append(types.Part(inline_data=types.Blob(mime_type="image/png", data=gen_bytes)))
    parts.append(
        types.Part(
            text=(
                "Evaluate the generated fashion image against the garment references. "
                "Ignore the original reference person identity and background. "
                "Focus on garment fidelity, silhouette, construction, texture, natural model realism, and commercial catalog quality. "
                "Return concise JSON only. Prompt used:\n"
                f"{prompt[:1800]}"
            )
        )
    )
    resp = generate_structured_json(
        parts=parts,
        schema=EVAL_SCHEMA,
        temperature=0.1,
        max_tokens=700,
        thinking_budget=0,
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, dict):
        return parsed
    text = "".join(getattr(part, "text", "") for part in (getattr(resp, "parts", None) or []))
    return json.loads(text)


def _write_report(run_dir: Path, selector_output: dict[str, Any], prompt: str, image_path: str, evaluation: dict[str, Any]) -> None:
    summary = {
        "selector_stats": selector_output.get("stats", {}),
        "selected_names": selector_output.get("selected_names", {}),
        "prompt": prompt,
        "image_path": image_path,
        "evaluation": evaluation,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Reference Selector Validation",
        "",
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Stats",
        "",
        f"- Raw count: {selector_output.get('stats', {}).get('raw_count')}",
        f"- Unique count: {selector_output.get('stats', {}).get('unique_count')}",
        f"- Duplicate count: {selector_output.get('stats', {}).get('duplicate_count')}",
        f"- Complex garment: {selector_output.get('stats', {}).get('complex_garment')}",
        "",
        "## Selected Subsets",
        "",
        f"- Base generation: {', '.join(selector_output.get('selected_names', {}).get('base_generation', []))}",
        f"- Strict single-pass: {', '.join(selector_output.get('selected_names', {}).get('strict_single_pass', []))}",
        f"- Edit anchors: {', '.join(selector_output.get('selected_names', {}).get('edit_anchors', []))}",
        "",
        "## Generated Proof",
        "",
        f"- Image: `{image_path}`",
        f"- Overall score: {evaluation.get('overall_score')}",
        f"- Garment fidelity: {evaluation.get('garment_fidelity')}",
        f"- Silhouette fidelity: {evaluation.get('silhouette_fidelity')}",
        f"- Texture fidelity: {evaluation.get('texture_fidelity')}",
        f"- Construction fidelity: {evaluation.get('construction_fidelity')}",
        f"- Commercial quality: {evaluation.get('commercial_quality_score')}",
        "",
        "## Prompt",
        "",
        "```text",
        prompt,
        "```",
        "",
        "## Issues",
        "",
    ]
    for issue in evaluation.get("issues", []) or []:
        lines.append(f"- {issue}")
    lines.extend(
        [
            "",
            "## Selector Items",
            "",
        ]
    )
    for item in selector_output.get("items", []):
        lines.extend(
            [
                f"### {item.get('filename')}",
                "",
                f"- role: {item.get('role')}",
                f"- worn_score: {item.get('worn_score')}",
                f"- detail_score: {item.get('detail_score')}",
                f"- garment_focus: {item.get('garment_focus')}",
                f"- silhouette_readability: {item.get('silhouette_readability')}",
                f"- construction_readability: {item.get('construction_readability')}",
                f"- texture_readability: {item.get('texture_readability')}",
                f"- styling_leak_risk: {item.get('styling_leak_risk')}",
                f"- background_noise: {item.get('background_noise')}",
                f"- reason: {item.get('reason')}",
                "",
            ]
        )
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida o selector automatico de referencias.")
    parser.add_argument("--folder", required=True, help="Pasta com imagens de referencia")
    args = parser.parse_args()

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
    prompt = _build_strict_reference_prompt(
        user_prompt=None,
        classifier_summary=classifier_summary,
        guided_brief={"scene": {"type": "interno"}, "pose": {"style": "tradicional"}, "garment": {"set_mode": "unica"}},
        structural_contract=unified.get("structural_contract"),
    )

    structural_hint = ""
    contract = unified.get("structural_contract") or {}
    hint_parts = [contract.get("garment_subtype", "")]
    if contract.get("silhouette_volume"):
        hint_parts.append(f"{contract['silhouette_volume']} silhouette")
    if contract.get("sleeve_type") and contract.get("sleeve_type") != "set-in":
        hint_parts.append(f"{contract['sleeve_type']} sleeves")
    structural_hint = ", ".join(part for part in hint_parts if part)

    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "docs" / "reference_selector_validation" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    generated = generate_images(
        prompt=prompt,
        thinking_level="MINIMAL",
        aspect_ratio="4:5",
        resolution="1K",
        n_images=1,
        uploaded_images=selector_output.get("selected_bytes", {}).get("base_generation", []),
        session_id=f"refsel_{run_stamp}"[-24:],
        structural_hint=structural_hint or None,
    )
    image_path = generated[0]["path"]
    evaluation = _evaluate_generation(
        reference_bytes=selector_output.get("selected_bytes", {}).get("base_generation", []),
        generated_image_path=image_path,
        prompt=prompt,
    )

    _write_report(run_dir, selector_output, prompt, image_path, evaluation)
    print(json.dumps({
        "run_dir": str(run_dir),
        "selected_names": selector_output.get("selected_names", {}),
        "image_path": image_path,
        "evaluation": evaluation,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
