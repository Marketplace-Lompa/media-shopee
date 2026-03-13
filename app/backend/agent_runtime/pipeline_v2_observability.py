from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from config import OUTPUTS_DIR


def write_v2_observability_report(session_id: str, payload: dict[str, Any]) -> dict[str, str]:
    report_dir = OUTPUTS_DIR / f"v2diag_{session_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.json"

    body = dict(payload)
    body["session_id"] = session_id
    body["written_at"] = int(time.time() * 1000)

    report_path.write_text(
        json.dumps(body, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "report_path": str(report_path),
        "report_url": f"/outputs/{report_dir.name}/{report_path.name}",
    }
