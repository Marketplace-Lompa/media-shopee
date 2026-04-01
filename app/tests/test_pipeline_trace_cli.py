from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from pathlib import Path

os.environ.setdefault("GOOGLE_AI_API_KEY", "test-key")


class _Blob:
    def __init__(self, mime_type: str | None = None, data: bytes | None = None):
        self.mime_type = mime_type
        self.data = data


class _Part:
    def __init__(self, text: str | None = None, inline_data: _Blob | None = None, media_resolution=None):
        self.text = text
        self.inline_data = inline_data
        self.media_resolution = media_resolution


class _Content:
    def __init__(self, role: str | None = None, parts=None):
        self.role = role
        self.parts = parts or []


class _Simple:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Client:
    def __init__(self, *args, **kwargs):
        self.models = _Simple(generate_content=lambda *a, **k: None)


google_mod = sys.modules.get("google") or types.ModuleType("google")
genai_mod = sys.modules.get("google.genai") or types.ModuleType("google.genai")
genai_types_mod = sys.modules.get("google.genai.types") or types.ModuleType("google.genai.types")

genai_types_mod.Blob = _Blob
genai_types_mod.Part = _Part
genai_types_mod.Content = _Content
genai_types_mod.MediaResolution = _Simple(MEDIA_RESOLUTION_HIGH="high")
genai_types_mod.GenerateContentConfig = _Simple
genai_types_mod.ImageConfig = _Simple
genai_types_mod.ThinkingConfig = _Simple
genai_types_mod.SafetySetting = _Simple
genai_types_mod.HarmCategory = _Simple(
    HARM_CATEGORY_SEXUALLY_EXPLICIT="sex",
    HARM_CATEGORY_HARASSMENT="harassment",
    HARM_CATEGORY_HATE_SPEECH="hate",
    HARM_CATEGORY_DANGEROUS_CONTENT="danger",
)
genai_types_mod.HarmBlockThreshold = _Simple(BLOCK_NONE="none")
genai_types_mod.Tool = _Simple
genai_types_mod.GoogleSearch = _Simple
genai_types_mod.SearchTypes = _Simple
genai_types_mod.ImageSearch = _Simple
genai_mod.Client = _Client
genai_mod.types = genai_types_mod
google_mod.genai = genai_mod

sys.modules["google"] = google_mod
sys.modules["google.genai"] = genai_mod
sys.modules["google.genai.types"] = genai_types_mod


def _load_cli_module() -> object:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "diagnostics" / "run_pipeline_trace.py"
    spec = importlib.util.spec_from_file_location("run_pipeline_trace", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_pipeline_trace_generates_summary_files(monkeypatch, tmp_path) -> None:
    module = _load_cli_module()

    refs_dir = tmp_path / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "look.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "planner": {
                    "plan": {"summary": {"creative_source": "reference_planner"}},
                    "input": {"instruction_prompt": "planner input"},
                    "output": {"raw_response_text": "{\"ok\":true}"},
                },
                "stage1": {
                    "transport": {
                        "generator_effective_prompt": "stage1 transport",
                        "generator_text_blocks": ["stage1 transport"],
                    }
                },
                "stage2": {
                    "runs": [
                        {
                            "edit_prompt": "stage2 primary",
                            "applied_edit_prompt": "stage2 applied",
                            "transport": {
                                "selected": {
                                    "executor_text_blocks": ["BASE", "EDIT GOAL"],
                                }
                            },
                        }
                    ]
                },
                "response_surfaces": {
                    "modal_prompt_surface": "stage1 transport",
                    "gallery_prompt_surface": "stage2 primary",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "run_generation_flow",
        lambda **kwargs: {
            "session_id": "sess01",
            "report_path": str(report_path),
            "report_url": "/outputs/v2diag_sess01/report.json",
        },
    )

    summary = module.run_pipeline_trace(
        [
            "--refs-folder",
            str(refs_dir),
            "--mode",
            "catalog_clean",
            "--mode",
            "natural",
            "--repeat",
            "1",
            "--output-dir",
            str(tmp_path / "trace_out"),
        ]
    )

    assert len(summary["runs"]) == 2
    assert Path(summary["summary_json_path"]).exists()
    assert Path(summary["summary_md_path"]).exists()
    assert summary["runs"][0]["stage1_transport_prompt"] == "stage1 transport"
    assert summary["runs"][0]["stage2_applied_prompt"] == "stage2 applied"
