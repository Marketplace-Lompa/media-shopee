from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_response import decode_prompt_agent_response


class _FakeResponse:
    def __init__(self, parsed=None, text: str = ""):
        self.parsed = parsed
        self.text = text


def test_decode_prompt_agent_response_prefers_parsed_payload() -> None:
    response = _FakeResponse(parsed={"base_prompt": "RAW photo, test prompt"})
    calls = {"count": 0}

    def fake_call_prompt_model(context: str, temperature: float):
        calls["count"] += 1
        return _FakeResponse(parsed={"base_prompt": "should not happen"})

    result = decode_prompt_agent_response(
        response=response,
        context_text="<MODE>test</MODE>",
        call_prompt_model=fake_call_prompt_model,
    )

    assert result["base_prompt"] == "RAW photo, test prompt"
    assert calls["count"] == 0


def test_decode_prompt_agent_response_retries_when_first_response_is_invalid() -> None:
    calls = {"count": 0}

    def fake_call_prompt_model(context: str, temperature: float):
        calls["count"] += 1
        assert "[RETRY TRIGGERED]" in context
        assert temperature == 0.2
        return _FakeResponse(text='{"base_prompt":"RAW photo, recovered prompt"}')

    result = decode_prompt_agent_response(
        response=_FakeResponse(text="not-json"),
        context_text="<MODE>test</MODE>",
        call_prompt_model=fake_call_prompt_model,
    )

    assert result["base_prompt"] == "RAW photo, recovered prompt"
    assert calls["count"] == 1
