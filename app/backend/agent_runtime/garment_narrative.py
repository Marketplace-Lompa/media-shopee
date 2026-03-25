from __future__ import annotations

import re
from typing import Optional


def sanitize_garment_narrative(text: str, structural_contract: Optional[dict]) -> str:
    narrative = re.sub(r"\s+", " ", (text or "").strip())
    if not narrative:
        return ""

    contract = structural_contract or {}
    subtype = str(contract.get("garment_subtype", "unknown")).strip().lower()
    sleeve_type = str(contract.get("sleeve_type", "unknown")).strip().lower()
    must_keep = " ".join(str(x).lower() for x in (contract.get("must_keep", []) or []))
    is_draped_wrap = (
        subtype in {"ruana_wrap", "poncho", "cape"}
        or sleeve_type == "cape_like"
        or "continuous neckline-to-front edge" in must_keep
        or "rounded cocoon side drop" in must_keep
    )

    if is_draped_wrap:
        replacements = [
            (r"(?i)\b(?:striped\s+)?(?:crochet|knit)?\s*(?:cocoon\s+)?shrug\b", "draped knit wrap"),
            (r"(?i)\b(?:oversized\s+)?cocoon cardigan\b", "draped knit wrap"),
            (r"(?i)\bcardigan\b", "draped knit wrap"),
            (r"(?i)\b(?:integrated\s+)?(?:wide\s+)?(?:batwing|dolman)\s+sleeves?\b", "fluid draped arm coverage"),
            (r"(?i)\bopen-front cocoon silhouette\b", "open draped cocoon silhouette"),
            (r"(?i)\bopen front\b", "soft open front edge"),
            (r"(?i)\b(?:continuous\s+)?(?:ribbed\s+)?collar\b", "continuous knitted edge"),
            (r"(?i)\bcollar band\b", "knitted edge finish"),
            (r"(?i)\b(draped)\s*\1\b", r"\1"),
            (r"(?i)\b(draped)(draped)\b", r"\1"),
        ]
        for pattern, replacement in replacements:
            narrative = re.sub(pattern, replacement, narrative)

    if subtype == "other" and re.search(r"(?i)\b(?:shrug|cardigan)\b", narrative):
        return ""

    return narrative.strip(" .,")
