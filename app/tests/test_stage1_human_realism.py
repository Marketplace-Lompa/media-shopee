from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw


os.environ.setdefault("GOOGLE_AI_API_KEY", "test-key")

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from agent_runtime.curation_policy import stage1_candidate_count
from pipeline_effectiveness import assess_generated_image


def test_stage1_candidate_count_prefers_two_for_natural_and_lifestyle() -> None:
    assert stage1_candidate_count(fidelity_mode="solta", selector_stats={}, mode="natural") == 2
    assert stage1_candidate_count(fidelity_mode="solta", selector_stats={}, mode="lifestyle") == 2
    assert stage1_candidate_count(fidelity_mode="solta", selector_stats={}, mode="catalog_clean") == 1


def test_assess_generated_image_reports_human_realism_signal(tmp_path) -> None:
    path = tmp_path / "candidate.png"
    img = Image.new("RGB", (800, 1000), (230, 225, 218))
    draw = ImageDraw.Draw(img)
    draw.ellipse((290, 110, 510, 340), fill=(186, 154, 132))
    draw.ellipse((340, 180, 382, 215), fill=(55, 45, 40))
    draw.ellipse((418, 180, 460, 215), fill=(55, 45, 40))
    draw.rectangle((360, 230, 440, 240), fill=(90, 70, 60))
    draw.rectangle((385, 240, 415, 285), fill=(120, 95, 80))
    draw.arc((360, 285, 440, 320), start=10, end=170, fill=(110, 70, 68), width=4)
    draw.rectangle((300, 340, 500, 700), fill=(198, 176, 160))
    draw.rectangle((250, 380, 300, 620), fill=(198, 176, 160))
    draw.rectangle((500, 380, 550, 620), fill=(198, 176, 160))
    draw.rectangle((305, 620, 365, 860), fill=(80, 90, 120))
    draw.rectangle((435, 620, 495, 860), fill=(80, 90, 120))
    img.save(path)

    result = assess_generated_image(str(path), "commercial natural fashion image", {})

    assert "human_realism_score" in result
    assert result["human_realism_score"] > 0.0

