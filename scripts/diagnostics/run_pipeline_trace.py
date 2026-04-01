from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.generation_flow import run_generation_flow
from config import OUTPUTS_DIR

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o pipeline V2 com observabilidade completa por mode.",
    )
    parser.add_argument("--refs-folder", required=True, help="Pasta com as referências visuais do produto.")
    parser.add_argument("--prompt", default="", help="Prompt opcional do usuário.")
    parser.add_argument("--mode", action="append", required=True, help="Mode repetível.")
    parser.add_argument("--scene-preference", default="auto_br")
    parser.add_argument("--fidelity-mode", default="balanceada")
    parser.add_argument("--n-images", type=int, default=1)
    parser.add_argument("--aspect-ratio", default="4:5")
    parser.add_argument("--resolution", default="1K")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--output-dir", default="", help="Diretório opcional para salvar os sumários.")
    return parser.parse_args(argv)


def _load_reference_payloads(refs_folder: str) -> tuple[list[bytes], list[str]]:
    folder = Path(refs_folder).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Pasta de referências não encontrada: {folder}")

    files = sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in _IMAGE_EXTENSIONS)
    if not files:
        raise FileNotFoundError(f"Nenhuma imagem suportada encontrada em {folder}")

    return [path.read_bytes() for path in files], [path.name for path in files]


def _extract_report_summary(report: dict[str, Any]) -> dict[str, Any]:
    planner = report.get("planner") or {}
    planner_input = planner.get("input") or {}
    planner_output = planner.get("output") or {}
    stage1 = report.get("stage1") or {}
    stage2 = report.get("stage2") or {}
    response_surfaces = report.get("response_surfaces") or {}
    stage2_runs = list(stage2.get("runs") or [])
    first_run = stage2_runs[0] if stage2_runs else {}

    return {
        "planner_summary": ((planner.get("plan") or {}).get("summary") or {}),
        "planner_instruction_prompt": planner_input.get("instruction_prompt") or "",
        "planner_raw_response_text": planner_output.get("raw_response_text") or "",
        "stage1_transport_prompt": ((stage1.get("transport") or {}).get("generator_effective_prompt") or ""),
        "stage1_transport_blocks": ((stage1.get("transport") or {}).get("generator_text_blocks") or []),
        "stage2_primary_prompt": first_run.get("edit_prompt") or "",
        "stage2_applied_prompt": first_run.get("applied_edit_prompt") or "",
        "stage2_transport_blocks": ((((first_run.get("transport") or {}).get("selected") or {}).get("executor_text_blocks")) or []),
        "modal_prompt_surface": response_surfaces.get("modal_prompt_surface") or "",
        "gallery_prompt_surface": response_surfaces.get("gallery_prompt_surface") or "",
    }


def _write_summary_markdown(
    *,
    trace_id: str,
    summary: dict[str, Any],
) -> str:
    lines = [
        f"# Pipeline Trace {trace_id}",
        "",
        f"- Prompt: {summary.get('prompt') or '(vazio)'}",
        f"- Scene preference: {summary.get('scene_preference')}",
        f"- Fidelity mode: {summary.get('fidelity_mode')}",
        f"- Aspect ratio: {summary.get('aspect_ratio')}",
        f"- Resolution: {summary.get('resolution')}",
        "",
    ]
    for run in summary.get("runs", []):
        lines.extend(
            [
                f"## Mode `{run.get('mode')}` · repeat {run.get('repeat_index')}",
                "",
                f"- Session: `{run.get('session_id')}`",
                f"- Report: `{run.get('debug_report_path')}`",
                f"- Planner summary: `{json.dumps(run.get('planner_summary') or {}, ensure_ascii=False)}`",
                f"- Stage 1 prompt: `{(run.get('stage1_transport_prompt') or '')[:220]}`",
                f"- Stage 2 prompt: `{(run.get('stage2_applied_prompt') or '')[:220]}`",
                f"- Modal surface: `{(run.get('modal_prompt_surface') or '')[:220]}`",
                f"- Gallery surface: `{(run.get('gallery_prompt_surface') or '')[:220]}`",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def run_pipeline_trace(argv: list[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    uploaded_bytes, uploaded_filenames = _load_reference_payloads(args.refs_folder)

    trace_id = f"trace_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if str(args.output_dir or "").strip()
        else OUTPUTS_DIR / trace_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, Any]] = []
    for mode in args.mode:
        for repeat_index in range(1, max(1, int(args.repeat or 1)) + 1):
            raw = run_generation_flow(
                uploaded_bytes=list(uploaded_bytes),
                uploaded_filenames=list(uploaded_filenames),
                prompt=args.prompt or None,
                mode=mode,
                scene_preference=args.scene_preference,
                fidelity_mode=args.fidelity_mode,
                n_images=args.n_images,
                aspect_ratio=args.aspect_ratio,
                resolution=args.resolution,
                observability_context={
                    "transport": "cli",
                    "request_inputs": {
                        "prompt": args.prompt,
                        "mode": mode,
                        "scene_preference": args.scene_preference,
                        "fidelity_mode": args.fidelity_mode,
                        "n_images": args.n_images,
                        "aspect_ratio": args.aspect_ratio,
                        "resolution": args.resolution,
                    },
                    "resolved_request": {
                        "mode": mode,
                        "scene_preference": args.scene_preference,
                        "fidelity_mode": args.fidelity_mode,
                    },
                },
            )
            report_path = Path(str(raw.get("report_path") or "")).resolve()
            report = json.loads(report_path.read_text(encoding="utf-8"))
            run_summary = {
                "mode": mode,
                "repeat_index": repeat_index,
                "session_id": raw.get("session_id"),
                "debug_report_path": str(report_path),
                "debug_report_url": raw.get("report_url"),
                **_extract_report_summary(report),
            }
            runs.append(run_summary)

    summary = {
        "trace_id": trace_id,
        "prompt": args.prompt,
        "scene_preference": args.scene_preference,
        "fidelity_mode": args.fidelity_mode,
        "n_images": args.n_images,
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
        "refs_folder": str(Path(args.refs_folder).expanduser().resolve()),
        "runs": runs,
    }
    summary_json_path = output_dir / "summary.json"
    summary_md_path = output_dir / "summary.md"
    summary_json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_md_path.write_text(_write_summary_markdown(trace_id=trace_id, summary=summary), encoding="utf-8")
    summary["summary_json_path"] = str(summary_json_path)
    summary["summary_md_path"] = str(summary_md_path)
    return summary


def main(argv: list[str] | None = None) -> int:
    summary = run_pipeline_trace(argv)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
