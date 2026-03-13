from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from google.genai import types

from agent_runtime.fidelity_gate import (
    build_visual_fidelity_gate_policy,
    evaluate_visual_fidelity,
)
from agent_runtime.gemini_client import generate_structured_json
from agent_runtime.parser import _decode_agent_response
from agent_runtime.structural import has_set_member
from config import OUTPUTS_DIR, ROOT_DIR


REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["verdict", "summary", "findings", "recommended_actions"],
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["ok", "attention", "fail"],
        },
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["severity", "category", "title", "evidence", "refinement"],
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "category": {"type": "string"},
                    "title": {"type": "string"},
                    "evidence": {"type": "string"},
                    "refinement": {"type": "string"},
                },
            },
        },
        "recommended_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


def _report_path_for_session(session_id: str) -> Path:
    return OUTPUTS_DIR / f"v2diag_{session_id}" / "report.json"


def latest_reviewable_session_id() -> Optional[str]:
    reports = sorted(
        OUTPUTS_DIR.glob("v2diag_*/report.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not reports:
        return None
    return reports[0].parent.name.replace("v2diag_", "", 1)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mime_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def _find_unique_file(filename: str) -> Optional[Path]:
    clean = str(filename or "").strip()
    if not clean:
        return None
    matches: list[Path] = []
    for base in (ROOT_DIR / "docs", ROOT_DIR / "app" / "outputs"):
        if not base.exists():
            continue
        for candidate in base.rglob(clean):
            if candidate.is_file():
                matches.append(candidate)
    if not matches:
        return None
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def _resolve_asset_group(session_id: str, group_name: str, fallback_names: list[str]) -> list[Path]:
    group_dir = OUTPUTS_DIR / f"v2diag_{session_id}" / "inputs" / group_name
    if group_dir.exists():
        return sorted([path for path in group_dir.iterdir() if path.is_file()])

    resolved: list[Path] = []
    for name in fallback_names:
        match = _find_unique_file(name)
        if match is not None:
            resolved.append(match)
    return resolved


def _materialize_asset_group(session_id: str, group_name: str, source_paths: list[Path]) -> list[str]:
    group_dir = OUTPUTS_DIR / f"v2diag_{session_id}" / "inputs" / group_name
    group_dir.mkdir(parents=True, exist_ok=True)
    urls: list[str] = []
    for idx, source in enumerate(source_paths, start=1):
        ext = source.suffix.lower() or ".jpg"
        target = source
        if not str(source).startswith(str(group_dir)):
            target = group_dir / f"{idx:02d}_{source.stem}{ext}"
            if not target.exists():
                target.write_bytes(source.read_bytes())
        urls.append(f"/outputs/v2diag_{session_id}/inputs/{group_name}/{target.name}")
    return urls


def _safe_context_excerpt(report: dict[str, Any]) -> str:
    request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
    selector = report.get("selector", {}) if isinstance(report.get("selector"), dict) else {}
    stage1 = report.get("stage1", {}) if isinstance(report.get("stage1"), dict) else {}
    stage2_runs = (((report.get("stage2") or {}) if isinstance(report.get("stage2"), dict) else {}).get("runs") or [])
    first_run = stage2_runs[0] if stage2_runs and isinstance(stage2_runs[0], dict) else {}
    context = {
        "prompt": request.get("prompt"),
        "preset": request.get("preset"),
        "scene_preference": request.get("scene_preference"),
        "fidelity_mode": request.get("fidelity_mode"),
        "pose_flex_mode": request.get("pose_flex_mode"),
        "reference_guard_strength": request.get("reference_guard_strength"),
        "uploaded_filenames": request.get("uploaded_filenames"),
        "selector_stats": selector.get("stats"),
        "selected_names": selector.get("selected_names"),
        "structural_contract": (selector.get("unified_triage") or {}).get("structural_contract"),
        "set_detection": (selector.get("unified_triage") or {}).get("set_detection"),
        "stage1_prompt": stage1.get("prompt"),
        "stage2_art_direction": first_run.get("art_direction_summary"),
        "stage2_edit_prompt": first_run.get("edit_prompt"),
    }
    return json.dumps(context, ensure_ascii=False)


def _fallback_review(report: dict[str, Any]) -> dict[str, Any]:
    request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
    selector = report.get("selector", {}) if isinstance(report.get("selector"), dict) else {}
    triage = (selector.get("unified_triage") or {}) if isinstance(selector.get("unified_triage"), dict) else {}
    structural = (triage.get("structural_contract") or {}) if isinstance(triage.get("structural_contract"), dict) else {}
    set_detection = (triage.get("set_detection") or {}) if isinstance(triage.get("set_detection"), dict) else {}
    stage1_prompt = str(((report.get("stage1") or {}) if isinstance(report.get("stage1"), dict) else {}).get("prompt", "") or "")
    findings: list[dict[str, str]] = []

    if bool((selector.get("stats") or {}).get("small_input_mode")):
        findings.append(
            {
                "severity": "medium",
                "category": "reference_coverage",
                "title": "Pouca cobertura estrutural de referência",
                "evidence": "O job foi executado com entrada pequena e sem âncoras de detalhe dedicadas.",
                "refinement": "Persistir e revisar sempre pelo menos uma referência frontal e uma referência de detalhe/estrutura da peça.",
            }
        )

    if has_set_member(
        set_detection,
        "scarf",
        include_policies={"must_include"},
        member_classes={"coordinated_accessory", "garment"},
    ) and "scarves" in stage1_prompt.lower():
        findings.append(
            {
                "severity": "high",
                "category": "prompt_conflict",
                "title": "Prompt base conflita com o set detectado",
                "evidence": "A triagem detectou set com scarf, mas o prompt base ainda contém uma proibição genérica de scarf.",
                "refinement": "Quando `set_detection` indicar set explícito, preservar scarf/segunda peça no stage 1 e no stage 2.",
            }
        )

    if str(structural.get("garment_subtype", "") or "").strip().lower() == "ruana_wrap":
        lowered_prompt = stage1_prompt.lower()
        has_explicit_ruana_guards = all(
            phrase in lowered_prompt for phrase in (
                "not a closed poncho",
                "do not invent separate sewn sleeves",
                "vertical sleeve slits",
            )
        )
        if not has_explicit_ruana_guards:
            findings.append(
                {
                    "severity": "high",
                    "category": "structure_guard",
                    "title": "Guarda estrutural do ruana ainda é ambígua",
                    "evidence": "O contrato fala em `ruana_wrap` e `cape_like`, mas não proíbe explicitamente corpo fechado, manga costurada ou fenda vertical inventada.",
                    "refinement": "Adicionar cláusulas negativas explícitas: não fechar o corpo, não criar manga separada e não inventar fenda vertical de manga.",
                }
            )

    verdict = "attention" if findings else "ok"
    summary = (
        "Revisão baseada no relatório do job; imagens de referência do bundle não estavam disponíveis para comparação visual completa."
        if findings else
        "Nenhum conflito estrutural evidente foi encontrado apenas pelo relatório."
    )
    return {
        "verdict": verdict,
        "summary": summary,
        "findings": findings,
        "recommended_actions": [row["refinement"] for row in findings[:3]],
    }


def _merge_review_payloads(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    merged_findings: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for review in (primary, secondary):
        for row in review.get("findings", []) or []:
            title = str(row.get("title", "") or "").strip().lower()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            merged_findings.append(row)

    recommended_actions: list[str] = []
    seen_actions: set[str] = set()
    for review in (primary, secondary):
        for action in review.get("recommended_actions", []) or []:
            normalized = str(action or "").strip()
            if not normalized or normalized in seen_actions:
                continue
            seen_actions.add(normalized)
            recommended_actions.append(normalized)

    verdict_priority = {"ok": 0, "attention": 1, "fail": 2}
    primary_verdict = str(primary.get("verdict", "ok") or "ok")
    secondary_verdict = str(secondary.get("verdict", "ok") or "ok")
    verdict = primary_verdict if verdict_priority.get(primary_verdict, 0) >= verdict_priority.get(secondary_verdict, 0) else secondary_verdict

    summary_parts = [
        str(primary.get("summary", "") or "").strip(),
        str(secondary.get("summary", "") or "").strip(),
    ]
    summary = " ".join(part for part in summary_parts if part)

    return {
        "verdict": verdict,
        "summary": summary.strip(),
        "findings": merged_findings,
        "recommended_actions": recommended_actions,
    }


def _compact_gate_result(gate_result: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not isinstance(gate_result, dict) or not gate_result:
        return None
    return {
        "available": bool(gate_result.get("available")),
        "verdict": gate_result.get("verdict"),
        "fidelity_score": gate_result.get("fidelity_score"),
        "issue_codes": gate_result.get("issue_codes", []),
        "summary": gate_result.get("summary"),
        "recovery_applied": bool(gate_result.get("recovery_applied")),
    }


def _build_review_gate_payload(
    *,
    report: dict[str, Any],
    original_refs: list[Path],
    base_path: Optional[Path],
    final_paths: list[Path],
    force_recompute: bool = False,
) -> dict[str, Any]:
    selector = report.get("selector", {}) if isinstance(report.get("selector"), dict) else {}
    request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
    triage = (selector.get("unified_triage") or {}) if isinstance(selector.get("unified_triage"), dict) else {}
    structural_contract = (triage.get("structural_contract") or {}) if isinstance(triage.get("structural_contract"), dict) else {}
    set_detection = (triage.get("set_detection") or {}) if isinstance(triage.get("set_detection"), dict) else {}
    selector_stats = selector.get("stats", {}) if isinstance(selector.get("stats"), dict) else {}
    stage1 = report.get("stage1", {}) if isinstance(report.get("stage1"), dict) else {}
    stage2_runs = (((report.get("stage2") or {}) if isinstance(report.get("stage2"), dict) else {}).get("runs") or [])

    gate_policy = report.get("fidelity_gate")
    if not isinstance(gate_policy, dict):
        gate_policy = build_visual_fidelity_gate_policy(
            structural_contract=structural_contract,
            set_detection=set_detection,
            selector_stats=selector_stats,
            fidelity_mode=str(request.get("fidelity_mode", "balanceada") or "balanceada"),
            pose_flex_mode=str(request.get("pose_flex_mode", "auto") or "auto"),
        )

    reference_bytes = [path.read_bytes() for path in original_refs[:4] if path.exists()]
    stage1_gate = None if force_recompute else (stage1.get("fidelity_gate") if isinstance(stage1.get("fidelity_gate"), dict) else None)
    if not stage1_gate and reference_bytes and base_path is not None and base_path.exists():
        stage1_gate = evaluate_visual_fidelity(
            stage="stage1",
            reference_images=reference_bytes,
            candidate_image_path=str(base_path),
            structural_contract=structural_contract,
            set_detection=set_detection,
            prompt=str(stage1.get("prompt", "") or ""),
        )

    stage2_payloads: list[dict[str, Any]] = []
    for idx, item in enumerate(stage2_runs, start=1):
        if not isinstance(item, dict):
            continue
        gate_result = None if force_recompute else (item.get("fidelity_gate") if isinstance(item.get("fidelity_gate"), dict) else None)
        result_path_text = str(((item.get("result") or {}) if isinstance(item.get("result"), dict) else {}).get("path", "") or "")
        if not gate_result and reference_bytes and base_path is not None and base_path.exists() and result_path_text:
            result_path = Path(result_path_text)
            if result_path.exists():
                gate_result = evaluate_visual_fidelity(
                    stage="stage2",
                    reference_images=reference_bytes,
                    base_image_path=str(base_path),
                    candidate_image_path=str(result_path),
                    structural_contract=structural_contract,
                    set_detection=set_detection,
                    prompt=str(item.get("edit_prompt", "") or ""),
                )
        recovery = item.get("recovery") if isinstance(item.get("recovery"), dict) else {}
        compact = _compact_gate_result(gate_result) or {
            "available": False,
            "verdict": None,
            "fidelity_score": None,
            "issue_codes": [],
            "summary": None,
            "recovery_applied": False,
        }
        compact["index"] = int(item.get("index", idx) or idx)
        compact["recovery_applied"] = bool(recovery.get("applied"))
        compact["selected"] = recovery.get("selected")
        stage2_payloads.append(compact)

    return {
        "enabled": bool(gate_policy.get("enabled")),
        "reasons": list(gate_policy.get("reasons", []) or []),
        "stage1": {
            **(_compact_gate_result(stage1_gate) or {
                "available": False,
                "verdict": None,
                "fidelity_score": None,
                "issue_codes": [],
                "summary": None,
                "recovery_applied": False,
            }),
            "recovery_applied": bool(((stage1.get("recovery") or {}) if isinstance(stage1.get("recovery"), dict) else {}).get("applied")),
        },
        "stage2_runs": stage2_payloads,
    }


def review_job_session(session_id: str, *, refresh: bool = False) -> dict[str, Any]:
    report_path = _report_path_for_session(session_id)
    if not report_path.exists():
        raise FileNotFoundError(f"Relatório do job {session_id} não encontrado")

    review_path = report_path.parent / "review.json"
    if review_path.exists() and not refresh:
        cached = _load_json(review_path)
        if isinstance(cached, dict) and cached.get("gate") is not None:
            return cached

    report = _load_json(report_path)
    request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
    selector = report.get("selector", {}) if isinstance(report.get("selector"), dict) else {}
    selected_names = selector.get("selected_names", {}) if isinstance(selector.get("selected_names"), dict) else {}

    original_refs = _resolve_asset_group(session_id, "original_references", list(request.get("uploaded_filenames", []) or []))
    base_refs = _resolve_asset_group(session_id, "base_generation", list(selected_names.get("base_generation", []) or []))
    edit_refs = _resolve_asset_group(session_id, "edit_anchors", list(selected_names.get("edit_anchors", []) or []))
    identity_refs = _resolve_asset_group(session_id, "identity_safe", list(selected_names.get("identity_safe", []) or []))

    base_path_raw = str((((report.get("stage1") or {}) if isinstance(report.get("stage1"), dict) else {}).get("result") or {}).get("path", "") or "")
    base_path = Path(base_path_raw) if base_path_raw else None
    if base_path is not None and not base_path.exists():
        base_path = None

    final_paths: list[Path] = []
    for item in (((report.get("response") or {}) if isinstance(report.get("response"), dict) else {}).get("images") or []):
        if not isinstance(item, dict):
            continue
        path_text = str(item.get("path", "") or "")
        path = Path(path_text) if path_text else None
        if path is not None and path.exists():
            final_paths.append(path)

    original_ref_urls = _materialize_asset_group(session_id, "original_references", original_refs)
    base_ref_urls = _materialize_asset_group(session_id, "base_generation", base_refs)
    edit_ref_urls = _materialize_asset_group(session_id, "edit_anchors", edit_refs)
    identity_ref_urls = _materialize_asset_group(session_id, "identity_safe", identity_refs)
    gate_payload = _build_review_gate_payload(
        report=report,
        original_refs=original_refs,
        base_path=base_path,
        final_paths=final_paths,
        force_recompute=refresh,
    )
    assets = {
        "original_references": original_ref_urls,
        "selected_base_references": base_ref_urls,
        "selected_edit_anchors": edit_ref_urls,
        "selected_identity_safe": identity_ref_urls,
        "base_image": (((report.get("stage1") or {}) if isinstance(report.get("stage1"), dict) else {}).get("result") or {}).get("url"),
        "final_images": [str(item.get("url")) for item in (((report.get("response") or {}) if isinstance(report.get("response"), dict) else {}).get("images") or []) if isinstance(item, dict) and item.get("url")],
        "reuse_reference_urls": original_ref_urls,
    }

    fallback_review = _fallback_review(report)
    review = fallback_review
    visual_inputs_available = bool(original_refs and base_path is not None and final_paths)
    if visual_inputs_available:
        try:
            parts: list[types.Part] = [
                types.Part(
                    text=(
                        "Review this fashion generation job for garment fidelity. "
                        "Compare original references, the selected base image, and the final generated image. "
                        "Focus on structural fidelity of the garment, not model identity. "
                        "Look for errors like wrong subtype, closed-vs-open front mistakes, invented sleeve slits, "
                        "lost coordinated set pieces, wrong hem behavior, or silhouette drift. "
                        "Return strict JSON only."
                    )
                ),
                types.Part(text="Job context: " + _safe_context_excerpt(report)),
                types.Part(text="Original garment references:"),
            ]
            for idx, path in enumerate(original_refs[:3], start=1):
                parts.append(types.Part(text=f"Original reference {idx}"))
                parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type=_mime_type_for_path(path), data=path.read_bytes()),
                        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                    )
                )
            parts.append(types.Part(text="Selected base image:"))
            parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type=_mime_type_for_path(base_path), data=base_path.read_bytes()),  # type: ignore[arg-type]
                    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                )
            )
            parts.append(types.Part(text="Final generated image:"))
            parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type=_mime_type_for_path(final_paths[0]), data=final_paths[0].read_bytes()),
                    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                )
            )
            response = generate_structured_json(
                parts=parts,
                schema=REVIEW_SCHEMA,
                temperature=0.1,
                max_tokens=1800,
                thinking_budget=128,
            )
            review = _merge_review_payloads(_decode_agent_response(response), fallback_review)
        except Exception:
            review = fallback_review

    payload = {
        "session_id": session_id,
        "written_at": int(report.get("written_at", 0) or 0),
        "report_url": f"/outputs/v2diag_{session_id}/report.json",
        "report_path": str(report_path),
        "assets": assets,
        "context": {
            "prompt": request.get("prompt"),
            "preset": request.get("preset"),
            "scene_preference": request.get("scene_preference"),
            "fidelity_mode": request.get("fidelity_mode"),
            "pose_flex_mode": request.get("pose_flex_mode"),
            "reference_guard_strength": request.get("reference_guard_strength"),
            "selected_names": selected_names,
            "structural_contract": (selector.get("unified_triage") or {}).get("structural_contract"),
            "set_detection": (selector.get("unified_triage") or {}).get("set_detection"),
        },
        "gate": gate_payload,
        "review": review,
    }
    review_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
