from __future__ import annotations

from typing import Any, Callable

from agent_runtime.parser import _decode_agent_response, _extract_response_text


def decode_prompt_agent_response(
    *,
    response: Any,
    context_text: str,
    call_prompt_model: Callable[[str, float], Any],
) -> dict:
    """
    Decodifica a resposta do Prompt Agent com retry leve quando o JSON vem inválido.
    """
    try:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict) and ("base_prompt" in parsed or "prompt" in parsed):
            print("[AGENT] ✅ JSON via response.parsed (schema enforced)")
            return parsed
    except Exception:
        pass

    try:
        parsed = _decode_agent_response(response)
        print("[AGENT] ✅ JSON via _decode_agent_response (parser robusto)")
        return parsed
    except Exception as primary_error:
        print(f"[AGENT] ⚠️  JSON parse failed (attempt 1): {primary_error}")
        raw_preview = _extract_response_text(response)[:320].replace("\n", "\\n")
        print(f"[AGENT] ⚠️  Raw preview: {raw_preview}")

    retry_context = (
        context_text
        + "\n\n[RETRY TRIGGERED]: The previous response was not valid JSON. You MUST return EXACTLY ONE valid JSON object, without markdown wrappers like ```json"
    )
    response_retry = call_prompt_model(retry_context, 0.2)
    try:
        parsed = _decode_agent_response(response_retry)
        print("[AGENT] ✅ JSON parse recovered on retry without grounding context.")
        return parsed
    except Exception as retry_error:
        raw_retry = _extract_response_text(response_retry)[:320].replace("\n", "\\n")
        print(f"[AGENT] ❌ JSON parse failed (attempt 2): {retry_error}")
        print(f"[AGENT] ❌ Retry raw preview: {raw_retry}")
        raise ValueError(f"AGENT_JSON_INVALID: {retry_error}") from retry_error
