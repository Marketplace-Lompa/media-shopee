"""
Mass test harness para a peça da pasta poncho-teste.

Objetivo:
- Rodar o pipeline real sem prompt N vezes usando o mesmo conjunto de referências.
- Persistir prompt, metadados e imagem gerada por rodada.
- Avaliar cada geração com Gemini Vision comparando contra as referências.
- Consolidar diagnóstico em JSON + Markdown.

Uso:
  PYTHONPATH=app/backend app/.venv/bin/python app/backend/poncho_mass_test.py --runs 3
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from google.genai import types

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.gemini_client import generate_structured_json
from routers.generate import _run_generate_pipeline


PONCHO_DIR = ROOT / "app" / "tests" / "output" / "poncho-teste"
REPORTS_DIR = ROOT / "docs" / "poncho_mass_tests"

EVAL_SCHEMA = {
    "type": "object",
    "required": [
        "garment_type_match",
        "silhouette_fidelity",
        "texture_pattern_fidelity",
        "construction_fidelity",
        "model_change_score",
        "pose_catalog_score",
        "brazilian_scene_plausibility",
        "scene_change_score",
        "overall_fidelity",
        "main_failures",
        "summary",
    ],
    "properties": {
        "garment_type_match": {"type": "number"},
        "silhouette_fidelity": {"type": "number"},
        "texture_pattern_fidelity": {"type": "number"},
        "construction_fidelity": {"type": "number"},
        "model_change_score": {"type": "number"},
        "pose_catalog_score": {"type": "number"},
        "brazilian_scene_plausibility": {"type": "number"},
        "scene_change_score": {"type": "number"},
        "overall_fidelity": {"type": "number"},
        "main_failures": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
}


@dataclass
class RunArtifact:
    index: int
    session_id: str
    prompt: str
    base_prompt: str
    camera_and_realism: str
    image_path: str
    grounding: dict[str, Any]
    reason_codes: list[str]
    prompt_compiler_debug: dict[str, Any]
    image_analysis: str
    evaluation: dict[str, Any]


def _load_reference_bytes(limit: int) -> list[bytes]:
    refs = []
    files = sorted(
        [p for p in PONCHO_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    )[:limit]
    for p in files:
        refs.append(p.read_bytes())
    if not refs:
        raise RuntimeError(f"Nenhuma referência encontrada em {PONCHO_DIR}")
    return refs


def _extract_history_entry(session_id: str, image_url: str) -> dict[str, Any]:
    history_path = ROOT / "app" / "outputs" / "history.json"
    if not history_path.exists():
        return {}
    try:
        rows = json.loads(history_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    for row in rows:
        if row.get("session_id") == session_id and row.get("url") == image_url:
            return row
    return {}


def _image_path_from_response(session_id: str, filename: str) -> str:
    return str(ROOT / "app" / "outputs" / session_id / filename)


def _evaluate_generation(
    reference_bytes: list[bytes],
    generated_image_path: str,
    prompt: str,
) -> dict[str, Any]:
    parts: List[types.Part] = []
    for img in reference_bytes[:6]:
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img)))
    gen_bytes = Path(generated_image_path).read_bytes()
    parts.append(types.Part(inline_data=types.Blob(mime_type="image/png", data=gen_bytes)))
    parts.append(
        types.Part(
            text=(
                "You are evaluating fashion garment fidelity.\n"
                "First images: reference garment photos only. Last image: generated result.\n"
                "Ignore the person, ignore the original reference background, and focus on the garment.\n"
                "Score from 0.0 to 1.0:\n"
                "- garment_type_match: same clothing category / subtype\n"
                "- silhouette_fidelity: same shape, drape, sleeve architecture, hem behavior\n"
                "- texture_pattern_fidelity: same knit/crochet texture, stripe direction, tactile depth\n"
                "- construction_fidelity: same opening/closure logic and overall garment build\n"
                "- model_change_score: generated person is clearly different from the apparent reference person\n"
                "- pose_catalog_score: pose is commercially useful for catalog/e-commerce and shows garment clearly\n"
                "- brazilian_scene_plausibility: background feels like a plausible Brazilian commercial/editorial location, not generic AI fantasy\n"
                "- scene_change_score: generated environment is clearly different from apparent reference environment\n"
                "- overall_fidelity: overall commercial usefulness for replacing the model while preserving garment identity\n"
                "Critical penalties:\n"
                "- If the generated garment introduces cardigan lapels, blazer-like fronts, or sewn jacket structure that do not exist in reference, reduce garment_type_match and construction_fidelity sharply.\n"
                "- If the generated garment introduces separate long sleeve tubes or coat-like sleeves where the reference uses a continuous draped panel, reduce silhouette_fidelity sharply.\n"
                "- If the generated face/hair/beauty cluster still resembles the apparent reference person too closely, reduce model_change_score sharply.\n"
                "Return concise JSON only. Prompt used:\n"
                f"{prompt[:1800]}"
            )
        )
    )
    resp = generate_structured_json(
        parts=parts,
        schema=EVAL_SCHEMA,
        temperature=0.1,
        max_tokens=800,
        thinking_budget=0,
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, dict):
        return parsed
    text = ""
    for part in (getattr(resp, "parts", None) or []):
        if getattr(part, "text", None):
            text += part.text
    return json.loads(text)


def _prompt_flags(prompt: str) -> dict[str, Any]:
    low = prompt.lower()
    return {
        "duplicate_features_blend": low.count("features blend") >= 2,
        "contains_front_panel_open": "front panel fully open" in low,
        "contains_bottom_complement": any(x in low for x in ["wide-leg cropped pants", "dark trousers", "jeans", "leggings"]),
        "contains_catalog_cover": "catalog cover" in low,
        "scenario_shopping_district": "shopping district" in low,
    }


def _write_markdown_report(run_dir: Path, artifacts: list[RunArtifact]) -> Path:
    overall_scores = [float(a.evaluation.get("overall_fidelity", 0.0) or 0.0) for a in artifacts]
    silhouette_scores = [float(a.evaluation.get("silhouette_fidelity", 0.0) or 0.0) for a in artifacts]
    texture_scores = [float(a.evaluation.get("texture_pattern_fidelity", 0.0) or 0.0) for a in artifacts]
    model_change_scores = [float(a.evaluation.get("model_change_score", 0.0) or 0.0) for a in artifacts]
    pose_catalog_scores = [float(a.evaluation.get("pose_catalog_score", 0.0) or 0.0) for a in artifacts]
    brazil_scene_scores = [float(a.evaluation.get("brazilian_scene_plausibility", 0.0) or 0.0) for a in artifacts]
    scene_change_scores = [float(a.evaluation.get("scene_change_score", 0.0) or 0.0) for a in artifacts]

    lines = [
        "# Poncho Mass Test Report",
        "",
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Reference folder: `{PONCHO_DIR}`",
        f"- Runs: {len(artifacts)}",
        "",
        "## Aggregate",
        "",
        f"- Overall fidelity avg: {statistics.mean(overall_scores):.3f}",
        f"- Silhouette fidelity avg: {statistics.mean(silhouette_scores):.3f}",
        f"- Texture fidelity avg: {statistics.mean(texture_scores):.3f}",
        f"- Model change avg: {statistics.mean(model_change_scores):.3f}",
        f"- Pose catalog avg: {statistics.mean(pose_catalog_scores):.3f}",
        f"- Brazilian scene plausibility avg: {statistics.mean(brazil_scene_scores):.3f}",
        f"- Scene change avg: {statistics.mean(scene_change_scores):.3f}",
        "",
        "## Runs",
        "",
    ]

    for a in artifacts:
        flags = _prompt_flags(a.prompt)
        lines.extend(
            [
                f"### Run {a.index}",
                "",
                f"- Session: `{a.session_id}`",
                f"- Image: `{a.image_path}`",
                f"- Overall fidelity: {float(a.evaluation.get('overall_fidelity', 0.0)):.3f}",
                f"- Silhouette: {float(a.evaluation.get('silhouette_fidelity', 0.0)):.3f}",
                f"- Texture: {float(a.evaluation.get('texture_pattern_fidelity', 0.0)):.3f}",
                f"- Construction: {float(a.evaluation.get('construction_fidelity', 0.0)):.3f}",
                f"- Model change: {float(a.evaluation.get('model_change_score', 0.0)):.3f}",
                f"- Pose catalog: {float(a.evaluation.get('pose_catalog_score', 0.0)):.3f}",
                f"- BR scene plausibility: {float(a.evaluation.get('brazilian_scene_plausibility', 0.0)):.3f}",
                f"- Scene change: {float(a.evaluation.get('scene_change_score', 0.0)):.3f}",
                f"- Prompt flags: `{json.dumps(flags, ensure_ascii=False)}`",
                f"- Failures: {', '.join(a.evaluation.get('main_failures', []) or []) or 'none'}",
                f"- Summary: {a.evaluation.get('summary', '')}",
                "",
                "Prompt:",
                "",
                "```text",
                a.prompt,
                "```",
                "",
            ]
        )

    report_path = run_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--refs", type=int, default=12)
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--resolution", default="1K")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = REPORTS_DIR / time.strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    reference_bytes = _load_reference_bytes(args.refs)
    artifacts: list[RunArtifact] = []

    print(f"[MASS TEST] refs={len(reference_bytes)} runs={args.runs} dir={run_dir}")

    for i in range(1, args.runs + 1):
        print(f"[MASS TEST] run {i}/{args.runs}...")
        response = _run_generate_pipeline(
            prompt=None,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            n_images=1,
            grounding_strategy="auto",
            use_grounding=False,
            guided_brief=None,
            uploaded_bytes=reference_bytes,
            on_stage=None,
        )
        image = response.images[0]
        hist = _extract_history_entry(response.session_id, image.url)
        prompt = response.optimized_prompt
        base_prompt = hist.get("base_prompt") or ""
        camera_and_realism = hist.get("camera_and_realism") or ""
        image_path = _image_path_from_response(response.session_id or "", image.filename)
        evaluation = _evaluate_generation(reference_bytes, image_path, prompt)

        artifact = RunArtifact(
            index=i,
            session_id=response.session_id or "",
            prompt=prompt,
            base_prompt=base_prompt,
            camera_and_realism=camera_and_realism,
            image_path=image_path,
            grounding=response.grounding or {},
            reason_codes=response.reason_codes or [],
            prompt_compiler_debug=response.prompt_compiler_debug.model_dump() if response.prompt_compiler_debug else {},
            image_analysis=(response.classifier_summary or {}).get("image_analysis", ""),
            evaluation=evaluation,
        )
        artifacts.append(artifact)

        (run_dir / f"run_{i:02d}.json").write_text(
            json.dumps(
                {
                    "session_id": artifact.session_id,
                    "prompt": artifact.prompt,
                    "base_prompt": artifact.base_prompt,
                    "camera_and_realism": artifact.camera_and_realism,
                    "image_path": artifact.image_path,
                    "grounding": artifact.grounding,
                    "reason_codes": artifact.reason_codes,
                    "prompt_compiler_debug": artifact.prompt_compiler_debug,
                    "evaluation": artifact.evaluation,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            "[MASS TEST] "
            f"run={i} overall={float(evaluation.get('overall_fidelity', 0.0)):.3f} "
            f"silhouette={float(evaluation.get('silhouette_fidelity', 0.0)):.3f} "
            f"texture={float(evaluation.get('texture_pattern_fidelity', 0.0)):.3f}"
        )

    summary = {
        "runs": len(artifacts),
        "overall_fidelity_avg": statistics.mean(float(a.evaluation.get("overall_fidelity", 0.0) or 0.0) for a in artifacts),
        "silhouette_fidelity_avg": statistics.mean(float(a.evaluation.get("silhouette_fidelity", 0.0) or 0.0) for a in artifacts),
        "texture_fidelity_avg": statistics.mean(float(a.evaluation.get("texture_pattern_fidelity", 0.0) or 0.0) for a in artifacts),
        "construction_fidelity_avg": statistics.mean(float(a.evaluation.get("construction_fidelity", 0.0) or 0.0) for a in artifacts),
        "model_change_avg": statistics.mean(float(a.evaluation.get("model_change_score", 0.0) or 0.0) for a in artifacts),
        "pose_catalog_avg": statistics.mean(float(a.evaluation.get("pose_catalog_score", 0.0) or 0.0) for a in artifacts),
        "brazilian_scene_plausibility_avg": statistics.mean(float(a.evaluation.get("brazilian_scene_plausibility", 0.0) or 0.0) for a in artifacts),
        "scene_change_avg": statistics.mean(float(a.evaluation.get("scene_change_score", 0.0) or 0.0) for a in artifacts),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = _write_markdown_report(run_dir, artifacts)
    print(f"[MASS TEST] summary={json.dumps(summary, ensure_ascii=False)}")
    print(f"[MASS TEST] report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
