"""
gemini_client — wrapper async para Google GenAI.

Mudanças de performance:
  - Todas as chamadas usam client.aio (não bloqueia event loop).
  - Semáforo global (GOOGLE_API_SEMAPHORE) limita requests simultâneos.
  - Backoff inteligente com jitter para erros 429 (quota).
  - Funções sync legadas mantidas para compatibilidade durante migração.
"""
import os
import time
import asyncio
import random
from typing import List, Any, Optional

from google import genai
from google.genai import types

from config import MODEL_AGENT, SAFETY_CONFIG

_GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not _GOOGLE_AI_API_KEY:
    raise ValueError("A variável de ambiente GOOGLE_AI_API_KEY não está configurada ou está vazia.")

_client = genai.Client(
    api_key=_GOOGLE_AI_API_KEY,
    http_options={'timeout': 120_000}  # SDK espera ms → 120s
)

# Semáforo global: protege quota da API (max N requests simultâneos ao Google)
GOOGLE_API_SEMAPHORE = asyncio.Semaphore(10)

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


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc or "").strip().lower()
    return "429" in text or "quota" in text or "rate" in text or "resource exhausted" in text


# ── Async core (nova, desbloqueia event loop) ──────────────────────────────────

async def _generate_content_async(
    *,
    model: str,
    parts: List[types.Part],
    config: types.GenerateContentConfig,
    max_attempts: int = 4,
) -> Any:
    """Chamada async com semáforo, retry inteligente e jitter."""
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            async with GOOGLE_API_SEMAPHORE:
                return await _client.aio.models.generate_content(
                    model=model,
                    contents=[types.Content(role="user", parts=parts)],
                    config=config,
                )
        except Exception as exc:
            last_error = exc
            is_quota = _is_rate_limit_error(exc)
            is_transient = _is_transient_provider_error(exc)

            if attempt >= max_attempts or (not is_transient and not is_quota):
                raise

            if is_quota:
                # Punição pesada + jitter para 429
                sleep_time = (2.0 ** attempt) + random.uniform(0.5, 2.0)
                print(f"[GEMINI_CLIENT] ⚠️ Quota 429 (attempt={attempt}/{max_attempts}). "
                      f"Aguardando {sleep_time:.1f}s... | {type(exc).__name__}: {exc}")
            else:
                sleep_time = (1.2 * attempt) + random.uniform(0.1, 0.5)
                print(f"[GEMINI_CLIENT] transient failure; retrying "
                      f"(attempt={attempt + 1}/{max_attempts}) | error: {type(exc).__name__}: {exc}")

            await asyncio.sleep(sleep_time)

    if last_error:
        raise last_error
    raise RuntimeError("Gemini request failed without response")


# ── Async public API ───────────────────────────────────────────────────────────

async def generate_structured_json_async(
    parts: List[types.Part],
    schema: dict,
    temperature: float = 0.1,
    max_tokens: int = 1200,
    thinking_budget: int = 0
) -> Any:
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        safety_settings=SAFETY_CONFIG,
        response_mime_type="application/json",
        response_json_schema=schema,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
    )
    return await _generate_content_async(model=MODEL_AGENT, parts=parts, config=config)


async def generate_multimodal_async(
    parts: List[types.Part],
    temperature: float = 0.1,
    max_tokens: int = 60,
    thinking_budget: int = 0
) -> Any:
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        safety_settings=SAFETY_CONFIG,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
    )
    return await _generate_content_async(model=MODEL_AGENT, parts=parts, config=config)


async def generate_with_system_instruction_async(
    parts: List[types.Part],
    system_instruction: str,
    schema: Optional[dict] = None,
    temperature: float = 0.75,
    max_tokens: int = 8192
) -> Any:
    if schema:
        try:
            return await _generate_content_async(
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

    return await _generate_content_async(
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


# ── Sync legacy wrappers (compatibilidade durante migração) ────────────────────
# Estes são chamados por pipeline_v2.py e outros módulos que ainda são sync.
# Delegam para a versão sync do client (sem .aio) para não precisar de event loop.

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
            is_quota = _is_rate_limit_error(exc)
            is_transient = _is_transient_provider_error(exc)

            if attempt >= max_attempts or (not is_transient and not is_quota):
                raise

            if is_quota:
                sleep_time = (2.0 ** attempt) + random.uniform(0.5, 2.0)
                print(f"[GEMINI_CLIENT] ⚠️ Quota 429 (attempt={attempt}/{max_attempts}). "
                      f"Aguardando {sleep_time:.1f}s... | {type(exc).__name__}: {exc}")
            else:
                sleep_time = (1.2 * attempt) + random.uniform(0.1, 0.5)
                print(f"[GEMINI_CLIENT] transient failure; retrying "
                      f"(attempt={attempt + 1}/{max_attempts}) | error: {type(exc).__name__}: {exc}")

            time.sleep(sleep_time)

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
