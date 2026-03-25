from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.garment_narrative import sanitize_garment_narrative


def test_sanitize_garment_narrative_rewrites_draped_wrap_terms() -> None:
    narrative = sanitize_garment_narrative(
        "striped crochet cocoon shrug with open front and ribbed collar",
        {
            "garment_subtype": "ruana_wrap",
            "sleeve_type": "cape_like",
            "must_keep": ["continuous neckline-to-front edge"],
        },
    )

    lowered = narrative.lower()
    assert "draped knit wrap" in lowered
    assert "soft open front edge" in lowered
    assert "continuous knitted edge" in lowered


def test_sanitize_garment_narrative_drops_invalid_cardigan_when_subtype_is_other() -> None:
    narrative = sanitize_garment_narrative(
        "oversized cardigan with soft texture",
        {
            "garment_subtype": "other",
            "sleeve_type": "unknown",
            "must_keep": [],
        },
    )

    assert narrative == ""
