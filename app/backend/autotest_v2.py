"""
Autotest V2 — Loop de teste continuo e autocorretivo para o pipeline V2.

Roda run_pipeline_v2() repetidamente com as mesmas referencias, varia a
direcao artistica, avalia cada resultado via Gemini Vision, e se autocorrige
entre iteracoes.

Uso:
  cd app/backend
  python autotest_v2.py --refs ../tests/output/poncho-teste --runs 8
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from google.genai import types

from agent_runtime.art_direction_sampler import (
    _CAMERA_PROFILES,
    _LIGHTING_PROFILES,
    _POSE_FAMILIES,
    _SCENE_FAMILIES,
    _STYLING_PROFILES,
    reset_art_direction_memory,
)
from agent_runtime.casting_engine import _CASTING_FAMILIES
from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.pipeline_v2 import run_pipeline_v2

# ── Output ───────────────────────────────────────────────────────────────────
AUTOTEST_DIR = ROOT / "docs" / "autotest"

# ── Thresholds ───────────────────────────────────────────────────────────────
DEFAULT_THRESHOLDS: dict[str, float] = {
    "garment_fidelity": 0.85,
    "model_change_strength": 0.85,
    "environment_change_strength": 0.85,
    "pose_vitality": 0.70,
    "creative_impact": 0.70,
    "brazilian_scene_authenticity": 0.70,
}

# ── Pool sizes (for diversity coverage) ──────────────────────────────────────
POOL_SIZES: dict[str, int] = {
    "casting_family": len(_CASTING_FAMILIES),
    "scene_family": len(_SCENE_FAMILIES),
    "pose_family": len(_POSE_FAMILIES),
    "camera_profile": len(_CAMERA_PROFILES),
    "lighting_profile": len(_LIGHTING_PROFILES),
    "styling_profile": len(_STYLING_PROFILES),
}

# ── Eval schema ──────────────────────────────────────────────────────────────
_SCORE_FIELDS = [
    "garment_fidelity",
    "silhouette_fidelity",
    "texture_fidelity",
    "construction_fidelity",
    "model_change_strength",
    "environment_change_strength",
    "innerwear_change_strength",
    "pose_vitality",
    "creative_impact",
    "brazilian_scene_authenticity",
    "commercial_readiness",
    "photorealism_score",
    "overall_score",
]

AUTOTEST_EVAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": _SCORE_FIELDS + ["issues", "summary"],
    "properties": {
        **{f: {"type": "number"} for f in _SCORE_FIELDS},
        "issues": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
}

EVAL_PROMPT_TEMPLATE = (
    "You are evaluating a fashion image generation pipeline. "
    "The first {n_refs} images are REFERENCE garment photos showing the original garment. "
    "The next image is the STAGE-1 BASE generation (faithful to garment). "
    "The final image is the STAGE-2 EDITED output (art-directed final result). "
    "Ignore the reference person identity and background. Focus on the garment and the quality of the final edited result.\n"
    "Score each dimension from 0.0 to 1.0:\n"
    "- garment_fidelity: same garment category, design, and visual identity\n"
    "- silhouette_fidelity: same shape, drape, sleeve architecture, hem behavior\n"
    "- texture_fidelity: same knit/crochet texture, stitch pattern, fiber relief\n"
    "- construction_fidelity: same opening/closure logic, garment build\n"
    "- model_change_strength: generated person is CLEARLY different from reference person (face, hair, skin, age)\n"
    "- environment_change_strength: generated background is CLEARLY different from reference environment\n"
    "- innerwear_change_strength: inner top was changed as directed\n"
    "- pose_vitality: how dynamic, alive, and natural the model pose feels (stiff=0.2, relaxed=0.5, dynamic movement=0.8+)\n"
    "- creative_impact: how memorable, impactful, and editorial-quality the overall composition is\n"
    "- brazilian_scene_authenticity: environment feels like a real Brazilian location (apartment, cafe, balcony), not generic AI\n"
    "- commercial_readiness: image could be used directly as a marketplace product listing\n"
    "- photorealism_score: natural skin texture, realistic lighting, no AI artifacts\n"
    "- overall_score: holistic commercial quality considering all dimensions\n"
    "Critical penalties:\n"
    "- If garment introduces cardigan/blazer structure not in reference, reduce garment_fidelity sharply\n"
    "- If face/hair still resembles reference person, reduce model_change_strength sharply\n"
    "- If pose is stiff and mannequin-like, reduce pose_vitality sharply\n"
    "Return JSON only.\n"
    "Base prompt:\n{base_prompt}\n\nEdit prompt:\n{edit_prompt}"
)

# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class CorrectionState:
    fidelity_mode: str = "balanceada"
    preset: str = "marketplace_lifestyle"
    scene_preference: str = "auto_br"
    extra_prompt_clauses: list[str] = field(default_factory=list)
    art_direction_request: dict[str, Any] = field(default_factory=dict)
    corrections_log: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RunResult:
    index: int
    session_id: str
    evaluation: dict[str, Any]
    art_direction_summary: dict[str, Any]
    corrections_applied: list[dict[str, Any]]
    stage1_prompt: str
    edit_prompt: str
    image_path: str
    base_image_path: str
    elapsed_seconds: float
    error: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _load_reference_images(refs_dir: Path, limit: int = 20) -> tuple[list[bytes], list[str]]:
    files = sorted(
        p for p in refs_dir.iterdir()
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
    )[:limit]
    if not files:
        raise RuntimeError(f"Nenhuma imagem de referencia em {refs_dir}")
    return [p.read_bytes() for p in files], [p.name for p in files]


def _mime_from_bytes(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _mime_from_path(path: Path) -> str:
    s = path.suffix.lower()
    if s == ".png":
        return "image/png"
    if s == ".webp":
        return "image/webp"
    return "image/jpeg"


# ── Evaluation ───────────────────────────────────────────────────────────────


def _evaluate_run(
    reference_bytes: list[bytes],
    base_image_path: str,
    edited_image_path: str,
    stage1_prompt: str,
    edit_prompt: str,
) -> dict[str, Any]:
    """Avalia resultado via Gemini Vision com schema estendido."""
    parts: List[types.Part] = []

    # References (max 6)
    refs_used = reference_bytes[:6]
    for img in refs_used:
        parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_from_bytes(img), data=img)))

    # Base image (stage 1)
    base_p = Path(base_image_path)
    if base_p.exists():
        parts.append(types.Part(inline_data=types.Blob(
            mime_type=_mime_from_path(base_p), data=base_p.read_bytes(),
        )))

    # Edited image (stage 2 — final)
    edit_p = Path(edited_image_path)
    parts.append(types.Part(inline_data=types.Blob(
        mime_type=_mime_from_path(edit_p), data=edit_p.read_bytes(),
    )))

    # Eval prompt
    parts.append(types.Part(text=EVAL_PROMPT_TEMPLATE.format(
        n_refs=len(refs_used),
        base_prompt=stage1_prompt[:900],
        edit_prompt=edit_prompt[:900],
    )))

    try:
        resp = generate_structured_json(
            parts=parts,
            schema=AUTOTEST_EVAL_SCHEMA,
            temperature=0.1,
            max_tokens=900,
            thinking_budget=0,
        )
        parsed = getattr(resp, "parsed", None)
        if isinstance(parsed, dict):
            return parsed
        text = "".join(getattr(part, "text", "") for part in (getattr(resp, "parts", None) or []))
        return json.loads(text)
    except Exception as exc:
        print(f"  [EVAL] falhou: {exc}")
        return {f: 0.0 for f in _SCORE_FIELDS} | {"issues": ["evaluation_failed"], "summary": str(exc)}


# ── Self-correction ──────────────────────────────────────────────────────────

_CORRECTION_RULES: list[tuple[str, float, str, str]] = [
    # (metric, threshold, prompt_clause, log_label)
    ("garment_fidelity", 0.85, "", "fidelity→estrita"),
    ("model_change_strength", 0.85, "Completely different model, no facial resemblance", "boost model_change"),
    ("environment_change_strength", 0.85, "", "force scene rotation"),
    ("pose_vitality", 0.70, "Dynamic energetic pose with natural movement", "boost pose_vitality"),
    ("creative_impact", 0.70, "Striking editorial composition with bold framing", "boost creative_impact"),
    ("brazilian_scene_authenticity", 0.70, "Authentic recognizable Brazilian location", "boost scene_authenticity"),
]

# Scene rotation order when environment_change is low
_SCENE_ROTATION = ["auto_br", "indoor_br", "outdoor_br"]


def _apply_corrections(
    state: CorrectionState,
    evaluation: dict[str, Any],
    run_index: int,
    last_art_summary: dict[str, Any],
) -> CorrectionState:
    """Inspeciona scores e ajusta state para proxima iteracao."""
    for metric, threshold, clause, label in _CORRECTION_RULES:
        score = float(evaluation.get(metric, 0.0) or 0.0)
        if score >= threshold:
            continue

        correction = {"run": run_index, "metric": metric, "score": round(score, 3), "action": label}

        if metric == "garment_fidelity":
            if state.fidelity_mode != "estrita":
                state.fidelity_mode = "estrita"
                state.corrections_log.append(correction)

        elif metric == "environment_change_strength":
            # Rotate scene preference
            cur_idx = _SCENE_ROTATION.index(state.scene_preference) if state.scene_preference in _SCENE_ROTATION else 0
            state.scene_preference = _SCENE_ROTATION[(cur_idx + 1) % len(_SCENE_ROTATION)]
            # Exclude the scene that just scored low
            last_scene = last_art_summary.get("scene_family", "")
            if last_scene:
                existing = state.art_direction_request.get("preferred_scene_ids", [])
                all_scenes = [s["id"] for s in _SCENE_FAMILIES if s["id"] != last_scene]
                state.art_direction_request["preferred_scene_ids"] = all_scenes if all_scenes else existing
            state.corrections_log.append(correction)

        elif metric == "pose_vitality":
            state.art_direction_request["preferred_pose_ids"] = ["paused_mid_step", "standing_full_shift"]
            if clause and clause not in state.extra_prompt_clauses:
                state.extra_prompt_clauses.append(clause)
            state.corrections_log.append(correction)

        elif metric == "creative_impact":
            if state.preset != "premium_lifestyle":
                state.preset = "premium_lifestyle"
            if clause and clause not in state.extra_prompt_clauses:
                state.extra_prompt_clauses.append(clause)
            state.corrections_log.append(correction)

        else:
            if clause and clause not in state.extra_prompt_clauses:
                state.extra_prompt_clauses.append(clause)
                state.corrections_log.append(correction)

    return state


def _build_run_prompt(state: CorrectionState) -> Optional[str]:
    """Concatena clauses de correcao em um prompt (max 200 chars)."""
    if not state.extra_prompt_clauses:
        return None
    combined = ". ".join(state.extra_prompt_clauses)
    return combined[:200]


# ── Diversity metrics ────────────────────────────────────────────────────────


def _compute_diversity_metrics(results: list[RunResult]) -> dict[str, Any]:
    dimensions: dict[str, list[str]] = {
        "casting_family": [],
        "scene_family": [],
        "pose_family": [],
        "camera_profile": [],
        "lighting_profile": [],
        "styling_profile": [],
    }

    for r in results:
        summary = r.art_direction_summary or {}
        for dim in dimensions:
            val = summary.get(dim, "unknown")
            dimensions[dim].append(val)

    metrics: dict[str, Any] = {}
    for dim, values in dimensions.items():
        unique = set(values)
        pool = POOL_SIZES.get(dim, 1)
        from collections import Counter
        counts = Counter(values)
        overrepresented = [k for k, v in counts.items() if v > 2]
        metrics[dim] = {
            "unique": len(unique),
            "pool": pool,
            "coverage_pct": round(100 * len(unique) / pool, 1) if pool else 0,
            "values": values,
            "overrepresented": overrepresented,
        }

    coverages = [m["coverage_pct"] for m in metrics.values()]
    metrics["overall_diversity_score"] = round(statistics.mean(coverages), 1) if coverages else 0
    return metrics


# ── Output writers ───────────────────────────────────────────────────────────


def _write_run_json(run_dir: Path, result: RunResult) -> None:
    data = {
        "index": result.index,
        "session_id": result.session_id,
        "evaluation": result.evaluation,
        "art_direction_summary": result.art_direction_summary,
        "corrections_applied": result.corrections_applied,
        "stage1_prompt": result.stage1_prompt,
        "edit_prompt": result.edit_prompt,
        "image_path": result.image_path,
        "base_image_path": result.base_image_path,
        "elapsed_seconds": result.elapsed_seconds,
        "error": result.error,
    }
    path = run_dir / f"run_{result.index:02d}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_summary_json(
    run_dir: Path,
    results: list[RunResult],
    diversity: dict[str, Any],
    corrections_log: list[dict[str, Any]],
) -> None:
    # Aggregate scores
    aggregated: dict[str, dict[str, float]] = {}
    for f in _SCORE_FIELDS:
        values = [float(r.evaluation.get(f, 0.0) or 0.0) for r in results]
        aggregated[f] = {
            "avg": round(statistics.mean(values), 3) if values else 0,
            "min": round(min(values), 3) if values else 0,
            "max": round(max(values), 3) if values else 0,
            "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0,
        }

    # Pass rates
    pass_rates: dict[str, float] = {}
    for metric, threshold in DEFAULT_THRESHOLDS.items():
        scores = [float(r.evaluation.get(metric, 0.0) or 0.0) for r in results]
        passing = sum(1 for s in scores if s >= threshold)
        pass_rates[metric] = round(100 * passing / len(scores), 1) if scores else 0

    # Self-correction effectiveness (first half vs second half)
    mid = len(results) // 2
    first_half = results[:mid] if mid else results
    second_half = results[mid:] if mid else []
    effectiveness = {}
    if first_half and second_half:
        for f in _SCORE_FIELDS:
            fh = statistics.mean([float(r.evaluation.get(f, 0) or 0) for r in first_half])
            sh = statistics.mean([float(r.evaluation.get(f, 0) or 0) for r in second_half])
            effectiveness[f] = {"first_half": round(fh, 3), "second_half": round(sh, 3), "delta": round(sh - fh, 3)}

    data = {
        "total_runs": len(results),
        "scores": aggregated,
        "pass_rates": pass_rates,
        "self_correction_effectiveness": effectiveness,
        "corrections_count": len(corrections_log),
        "corrections": corrections_log,
        "diversity": {k: v for k, v in diversity.items() if k != "overall_diversity_score"},
        "overall_diversity_score": diversity.get("overall_diversity_score", 0),
    }
    (run_dir / "summary.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_report_markdown(
    run_dir: Path,
    results: list[RunResult],
    diversity: dict[str, Any],
    corrections_log: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    lines: list[str] = []
    lines.append("# Autotest V2 Report\n")
    lines.append(f"- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **References:** `{args.refs}` ({len(results)} runs)")
    lines.append(f"- **Preset:** {args.preset}")
    lines.append(f"- **Scene:** {args.scene}")
    lines.append(f"- **Fidelity:** {args.fidelity}")
    lines.append(f"- **Self-correction:** {'ON' if args.correct else 'OFF'}")
    lines.append(f"- **Corrections applied:** {len(corrections_log)}")
    lines.append("")

    # Aggregate table
    lines.append("## Aggregate Scores\n")
    lines.append("| Metric | Avg | Min | Max | Pass Rate |")
    lines.append("|--------|-----|-----|-----|-----------|")
    for f in _SCORE_FIELDS:
        values = [float(r.evaluation.get(f, 0) or 0) for r in results]
        avg = statistics.mean(values) if values else 0
        mn = min(values) if values else 0
        mx = max(values) if values else 0
        threshold = DEFAULT_THRESHOLDS.get(f)
        pr = ""
        if threshold and values:
            passing = sum(1 for v in values if v >= threshold)
            pr = f"{100 * passing / len(values):.0f}%"
        lines.append(f"| {f} | {avg:.2f} | {mn:.2f} | {mx:.2f} | {pr} |")
    lines.append("")

    # Self-correction effectiveness
    mid = len(results) // 2
    if mid and len(results) > mid:
        lines.append("## Self-Correction Effectiveness\n")
        lines.append("| Metric | First Half | Second Half | Delta |")
        lines.append("|--------|-----------|-------------|-------|")
        for f in _SCORE_FIELDS:
            fh = statistics.mean([float(r.evaluation.get(f, 0) or 0) for r in results[:mid]])
            sh = statistics.mean([float(r.evaluation.get(f, 0) or 0) for r in results[mid:]])
            delta = sh - fh
            sign = "+" if delta >= 0 else ""
            lines.append(f"| {f} | {fh:.2f} | {sh:.2f} | {sign}{delta:.2f} |")
        lines.append("")

    # Corrections log
    if corrections_log:
        lines.append("## Corrections Applied\n")
        lines.append("| Run | Metric | Score | Action |")
        lines.append("|-----|--------|-------|--------|")
        for c in corrections_log:
            lines.append(f"| {c['run']} | {c['metric']} | {c['score']} | {c['action']} |")
        lines.append("")

    # Diversity
    lines.append("## Diversity Analysis\n")
    lines.append("| Dimension | Unique | Pool | Coverage |")
    lines.append("|-----------|--------|------|----------|")
    for dim in POOL_SIZES:
        d = diversity.get(dim, {})
        lines.append(f"| {dim} | {d.get('unique', 0)} | {d.get('pool', 0)} | {d.get('coverage_pct', 0):.0f}% |")
    lines.append(f"\n**Overall diversity score:** {diversity.get('overall_diversity_score', 0):.1f}%\n")

    overrep = []
    for dim in POOL_SIZES:
        d = diversity.get(dim, {})
        for item in d.get("overrepresented", []):
            overrep.append(f"{dim}: {item}")
    if overrep:
        lines.append("**Over-represented (>2x in set):** " + ", ".join(overrep) + "\n")

    # Individual runs
    lines.append("## Individual Runs\n")
    for r in results:
        lines.append(f"### Run {r.index}")
        lines.append(f"- Session: `{r.session_id}`")
        lines.append(f"- Elapsed: {r.elapsed_seconds:.1f}s")
        art = r.art_direction_summary or {}
        lines.append(f"- Art direction: casting={art.get('casting_family', '?')}, "
                      f"scene={art.get('scene_family', '?')}, "
                      f"pose={art.get('pose_family', '?')}, "
                      f"camera={art.get('camera_profile', '?')}")
        ev = r.evaluation or {}
        for f in _SCORE_FIELDS:
            val = ev.get(f, 0)
            threshold = DEFAULT_THRESHOLDS.get(f)
            flag = ""
            if threshold and float(val or 0) < threshold:
                flag = " **LOW**"
            lines.append(f"- {f}: {val}{flag}")
        issues = ev.get("issues", [])
        if issues:
            lines.append(f"- Issues: {', '.join(issues)}")
        summary = ev.get("summary", "")
        if summary:
            lines.append(f"- Summary: {summary}")
        if r.corrections_applied:
            lines.append(f"- Corrections: {json.dumps(r.corrections_applied, ensure_ascii=False)}")
        if r.error:
            lines.append(f"- **ERROR:** {r.error}")
        lines.append("")

    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _copy_images(run_dir: Path, results: list[RunResult]) -> None:
    img_dir = run_dir / "images"
    img_dir.mkdir(exist_ok=True)
    for r in results:
        if r.image_path and Path(r.image_path).exists():
            ext = Path(r.image_path).suffix
            shutil.copy2(r.image_path, img_dir / f"run_{r.index:02d}_final{ext}")
        if r.base_image_path and Path(r.base_image_path).exists():
            ext = Path(r.base_image_path).suffix
            shutil.copy2(r.base_image_path, img_dir / f"run_{r.index:02d}_base{ext}")


# ── Print helpers ────────────────────────────────────────────────────────────

_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _color_score(val: float, threshold: float = 0.80) -> str:
    c = _GREEN if val >= threshold else (_YELLOW if val >= threshold - 0.10 else _RED)
    return f"{c}{val:.2f}{_RESET}"


def _print_run_summary(result: RunResult) -> None:
    ev = result.evaluation
    parts = [
        f"run={result.index}",
        f"overall={_color_score(float(ev.get('overall_score', 0) or 0))}",
        f"fidelity={_color_score(float(ev.get('garment_fidelity', 0) or 0), 0.85)}",
        f"model_chg={_color_score(float(ev.get('model_change_strength', 0) or 0), 0.85)}",
        f"env_chg={_color_score(float(ev.get('environment_change_strength', 0) or 0), 0.85)}",
        f"vitality={_color_score(float(ev.get('pose_vitality', 0) or 0), 0.70)}",
        f"impact={_color_score(float(ev.get('creative_impact', 0) or 0), 0.70)}",
        f"elapsed={result.elapsed_seconds:.0f}s",
    ]
    print(f"  {_BOLD}[RESULT]{_RESET} {' | '.join(parts)}")


def _print_final_summary(results: list[RunResult], diversity: dict[str, Any], run_dir: Path) -> None:
    print(f"\n{_BOLD}{'=' * 60}{_RESET}")
    print(f"{_BOLD}AUTOTEST V2 — FINAL SUMMARY{_RESET}")
    print(f"{'=' * 60}")
    print(f"Runs: {len(results)}")
    print(f"Output: {run_dir}\n")

    print(f"{'Metric':<32} {'Avg':>6} {'Min':>6} {'Max':>6}")
    print("-" * 56)
    for f in _SCORE_FIELDS:
        values = [float(r.evaluation.get(f, 0) or 0) for r in results]
        if not values:
            continue
        avg = statistics.mean(values)
        threshold = DEFAULT_THRESHOLDS.get(f, 0.80)
        print(f"{f:<32} {_color_score(avg, threshold):>15} {min(values):>6.2f} {max(values):>6.2f}")

    print(f"\n{_BOLD}Diversity:{_RESET} {diversity.get('overall_diversity_score', 0):.1f}% coverage")
    for dim in POOL_SIZES:
        d = diversity.get(dim, {})
        print(f"  {dim}: {d.get('unique', 0)}/{d.get('pool', 0)}")


# ── Main ─────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Autotest V2 — loop continuo e autocorretivo")
    p.add_argument("--refs", required=True, help="Diretorio com imagens de referencia")
    p.add_argument("--runs", type=int, default=8, help="Numero de iteracoes (default: 8)")
    p.add_argument("--preset", default="marketplace_lifestyle",
                   choices=["catalog_clean", "marketplace_lifestyle", "premium_lifestyle"])
    p.add_argument("--scene", default="auto_br", choices=["auto_br", "indoor_br", "outdoor_br"])
    p.add_argument("--fidelity", default="balanceada", choices=["balanceada", "estrita"])
    p.add_argument("--n-images", type=int, default=1, help="Imagens por run (default: 1)")
    p.add_argument("--aspect-ratio", default="4:5")
    p.add_argument("--resolution", default="1K")
    p.add_argument("--correct", action="store_true", default=True, help="Habilitar autocorrecao (default)")
    p.add_argument("--no-correct", dest="correct", action="store_false", help="Desabilitar autocorrecao")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Resolve refs dir
    refs_dir = Path(args.refs)
    if not refs_dir.is_absolute():
        refs_dir = Path.cwd() / refs_dir
    if not refs_dir.is_dir():
        print(f"[ERRO] Diretorio nao encontrado: {refs_dir}")
        return 1

    # Output dir
    run_dir = AUTOTEST_DIR / time.strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "images").mkdir(exist_ok=True)

    print(f"{_BOLD}[AUTOTEST V2]{_RESET} refs={refs_dir} runs={args.runs} preset={args.preset} "
          f"scene={args.scene} fidelity={args.fidelity} correct={'ON' if args.correct else 'OFF'}")
    print(f"Output: {run_dir}\n")

    # Load references
    ref_bytes, ref_names = _load_reference_images(refs_dir)
    print(f"Loaded {len(ref_bytes)} reference images: {', '.join(ref_names[:5])}{'...' if len(ref_names) > 5 else ''}\n")

    # Reset art direction memory for clean diversity
    reset_art_direction_memory()
    print("Art direction memory reset.\n")

    # Init correction state
    state = CorrectionState(
        fidelity_mode=args.fidelity,
        preset=args.preset,
        scene_preference=args.scene,
    )

    results: list[RunResult] = []

    for i in range(1, args.runs + 1):
        print(f"{_CYAN}{_BOLD}── Run {i}/{args.runs} ──{_RESET}")

        # Build prompt from corrections
        run_prompt = _build_run_prompt(state)
        if run_prompt:
            print(f"  prompt: {run_prompt[:80]}...")

        snapshot_corrections = list(state.corrections_log)

        # Run pipeline
        started = time.time()
        try:
            response = run_pipeline_v2(
                uploaded_bytes=ref_bytes,
                uploaded_filenames=ref_names,
                prompt=run_prompt,
                preset=state.preset,
                scene_preference=state.scene_preference,
                fidelity_mode=state.fidelity_mode,
                n_images=args.n_images,
                aspect_ratio=args.aspect_ratio,
                resolution=args.resolution,
                art_direction_request=state.art_direction_request or None,
                on_stage=lambda stage, data: print(f"  [{stage}] {data.get('message', '')}"),
            )
        except Exception as exc:
            elapsed = time.time() - started
            print(f"  {_RED}[FAILED]{_RESET} {exc}")
            result = RunResult(
                index=i, session_id="", evaluation={f: 0.0 for f in _SCORE_FIELDS},
                art_direction_summary={}, corrections_applied=[], stage1_prompt="",
                edit_prompt="", image_path="", base_image_path="",
                elapsed_seconds=round(elapsed, 2), error=str(exc),
            )
            results.append(result)
            _write_run_json(run_dir, result)
            continue

        elapsed = time.time() - started

        # Extract paths
        images = response.get("images", [])
        image_path = str(images[0].get("path", "")) if images else ""
        base_image_info = response.get("base_image") or {}
        base_image_path = str(base_image_info.get("path", ""))
        art_summary = response.get("art_direction_summary", {})

        print(f"  art: casting={art_summary.get('casting_family', '?')} "
              f"scene={art_summary.get('scene_family', '?')} "
              f"pose={art_summary.get('pose_family', '?')}")

        # Evaluate
        print(f"  [evaluating...]")
        evaluation = _evaluate_run(
            reference_bytes=ref_bytes,
            base_image_path=base_image_path,
            edited_image_path=image_path,
            stage1_prompt=response.get("stage1_prompt", ""),
            edit_prompt=response.get("edit_prompt", ""),
        )

        # Build result
        new_corrections = [c for c in state.corrections_log if c not in snapshot_corrections]
        result = RunResult(
            index=i,
            session_id=response.get("session_id", ""),
            evaluation=evaluation,
            art_direction_summary=art_summary,
            corrections_applied=new_corrections,
            stage1_prompt=response.get("stage1_prompt", ""),
            edit_prompt=response.get("edit_prompt", ""),
            image_path=image_path,
            base_image_path=base_image_path,
            elapsed_seconds=round(elapsed, 2),
        )
        results.append(result)
        _write_run_json(run_dir, result)
        _print_run_summary(result)

        # Self-correct
        if args.correct:
            before = len(state.corrections_log)
            state = _apply_corrections(state, evaluation, i, art_summary)
            after = len(state.corrections_log)
            if after > before:
                new = state.corrections_log[before:]
                for c in new:
                    print(f"  {_YELLOW}[CORRECTION]{_RESET} {c['metric']}={c['score']} → {c['action']}")

        print()

    # Final output
    successful = [r for r in results if not r.error]
    if not successful:
        print(f"{_RED}[AUTOTEST] Nenhum run bem-sucedido.{_RESET}")
        return 1

    diversity = _compute_diversity_metrics(successful)
    _copy_images(run_dir, successful)
    _write_summary_json(run_dir, successful, diversity, state.corrections_log)
    _write_report_markdown(run_dir, successful, diversity, state.corrections_log, args)
    _print_final_summary(successful, diversity, run_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
