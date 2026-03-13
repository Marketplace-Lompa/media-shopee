import os
import time
from typing import List, Any, Optional

from google import genai
from google.genai import types

from config import MODEL_AGENT, SAFETY_CONFIG

_GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not _GOOGLE_AI_API_KEY:
    raise ValueError("A variável de ambiente GOOGLE_AI_API_KEY não está configurada ou está vazia.")

_client = genai.Client(api_key=_GOOGLE_AI_API_KEY)
_TRANSIENT_PROVIDER_ERRORS = (
    "server disconnected without sending a response",
    "remoteprotocolerror",
    "connection reset",
    "temporarily unavailable",
    "timed out",
    "timeout",
    "503",
    "502",
    "500",
)


def _is_transient_provider_error(exc: Exception) -> bool:
    text = str(exc or "").strip().lower()
    return any(token in text for token in _TRANSIENT_PROVIDER_ERRORS)


def _generate_content_with_retry(
    *,
    model: str,
    parts: List[types.Part],
    config: types.GenerateContentConfig,
    max_attempts: int = 3,
) -> Any:
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return _client.models.generate_content(
                model=model,
                contents=[types.Content(role="user", parts=parts)],
                config=config,
            )
        except Exception as exc:
            last_error = exc
            if attempt >= max_attempts or not _is_transient_provider_error(exc):
                raise
            print(
                "[GEMINI_CLIENT] transient failure; retrying "
                f"(attempt={attempt + 1}/{max_attempts})"
            )
            time.sleep(0.8 * attempt)
    if last_error:
        raise last_error
    raise RuntimeError("Gemini request failed without response")

def generate_structured_json(
    parts: List[types.Part],
    schema: dict,
    temperature: float = 0.1,
    max_tokens: int = 1200,
    thinking_budget: int = 0
) -> Any:
    """Faz a chamada à SDK forçando o formato JSON de resposta."""
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        safety_settings=SAFETY_CONFIG,
        response_mime_type="application/json",
        response_json_schema=schema,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
    )
    return _generate_content_with_retry(model=MODEL_AGENT, parts=parts, config=config)

def generate_multimodal(
    parts: List[types.Part],
    temperature: float = 0.1,
    max_tokens: int = 60,
    thinking_budget: int = 0
) -> Any:
    """Faz a chamada à SDK sem forçar schema, geralmente retornando texto puro ou multimodal misto."""
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        safety_settings=SAFETY_CONFIG,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
    )
    return _generate_content_with_retry(model=MODEL_AGENT, parts=parts, config=config)

def generate_text_with_tools(
    parts: List[types.Part],
    tools: List[Any],
    temperature: float = 0.2,
    max_tokens: int = 400
) -> Any:
    """Faz a chamada à SDK passando ferramentas associadas."""
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        safety_settings=SAFETY_CONFIG,
        tools=tools,
    )
    return _generate_content_with_retry(model=MODEL_AGENT, parts=parts, config=config)

def generate_with_system_instruction(
    parts: List[types.Part],
    system_instruction: str,
    schema: Optional[dict] = None,
    temperature: float = 0.75,
    max_tokens: int = 8192
) -> Any:
    """Faz a requisição utilizando instrução do sistema (usado primordialmente pelo orquestrador final run_agent)."""
    # Se o schema for passado tentamos enforced JSON
    if schema:
        try:
            return _generate_content_with_retry(
                model=MODEL_AGENT,
                parts=parts,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    safety_settings=SAFETY_CONFIG,
                    response_mime_type="application/json",
                    response_json_schema=schema,
                ),
            )
        except (TypeError, ValueError) as schema_err:
            print(f"[GEMINI_CLIENT] ⚠️ Schema enforcement failed ({schema_err}), falling back to mime-only")

    # Fallback mime-only (ou caso uso thel sem schema estrito)
    return _generate_content_with_retry(
        model=MODEL_AGENT,
        parts=parts,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
            safety_settings=SAFETY_CONFIG,
            response_mime_type="application/json",
        ),
    )
