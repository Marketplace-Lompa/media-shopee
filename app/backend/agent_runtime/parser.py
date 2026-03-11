import json
import re
from typing import Optional, Any

def _extract_balanced_json(raw: str) -> Optional[str]:
    """Extrai o primeiro objeto JSON balanceado, ignorando chaves dentro de strings."""
    if not raw:
        return None

    in_string = False
    escaped = False
    depth = 0
    start_idx = -1

    for i, ch in enumerate(raw):
        if escaped:
            escaped = False
            continue

        if ch == "\\":
            escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            if depth == 0:
                start_idx = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start_idx >= 0:
                    return raw[start_idx:i + 1]

    return None


def _safe_json_loads(raw: str) -> dict:
    """Tenta parse padrão e fallback com strict=False (aceita control chars)."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(raw, strict=False)


def _parse_json(raw: str) -> dict:
    """Parser robusto para respostas que podem vir com ruído."""
    if not raw or not raw.strip():
        raise ValueError("AGENT_JSON_INVALID: resposta vazia")

    text = raw.strip()

    # 1) Tentativa direta
    try:
        return _safe_json_loads(text)
    except Exception as e1:
        error_msg = str(e1)

    # 2) Tentativa em bloco markdown ```json ... ```
    if "```" in text:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            candidate = match.group(1)
            try:
                return _safe_json_loads(candidate)
            except Exception as e2:
                error_msg += f" | {e2}"

    # 3) Extrair objeto balanceado
    candidate = _extract_balanced_json(text)
    if candidate:
        try:
            return _safe_json_loads(candidate)
        except Exception as e:
            preview = candidate[:1000].replace("\n", "\\n")
            raise ValueError(f"AGENT_JSON_INVALID: fallbacks failed. Errors: {error_msg} | {e}. candidate={preview}") from e

    preview = text[:1000].replace("\n", "\\n")
    raise ValueError(f"AGENT_JSON_INVALID: no balanced JSON found. Errors: {error_msg}. raw={preview}")


def _extract_response_text(response: Any) -> str:
    """Extrai texto de resposta com fallback seguro."""
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text
    return ""


def _decode_agent_response(response: Any) -> dict:
    """
    Decodifica resposta do modelo priorizando `response.parsed` quando disponível.
    Cai para parser textual robusto como fallback.
    """
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, dict):
        return parsed
    raw = _extract_response_text(response)
    return _parse_json(raw)
