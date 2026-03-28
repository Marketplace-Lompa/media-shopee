"""
Resolver grounded de casting para diversidade real de modelos humanas.

Esta camada pesquisa sinais públicos do mercado brasileiro e sintetiza uma
direção de casting ORIGINAL para o job atual. Ela não substitui a model_soul:
apenas adiciona repertório, anti-colapso e uma direção concreta de casting.
"""
from __future__ import annotations

from typing import Any, Optional

from google.genai import types

from config import MODEL_AGENT, SAFETY_CONFIG
from agent_runtime.gemini_client import _generate_content_with_retry, generate_structured_json
from agent_runtime.mode_identity_soul import get_mode_identity_soul
from agent_runtime.model_soul import get_model_soul
from agent_runtime.parser import _decode_agent_response, _extract_response_text, try_repair_truncated_json

_NATURAL_PRESTIGE_DRIFT_TOKENS = (
    "architect",
    "designer",
    "curator",
    "gallery",
    "brutalist",
    "academic",
    "intellectual",
    "premium",
    "luxury",
    "pinterest",
    "fashion-forward",
    "corporate",
)


_CANDIDATE_SCHEMA = {
    "type": "object",
    "required": [
        "label",
        "age_logic",
        "face_geometry",
        "skin_logic",
        "hair_logic",
        "body_logic",
        "presence_logic",
        "expression_logic",
        "makeup_logic",
        "beauty_logic",
        "platform_presence",
        "commercial_read",
        "distinction_markers",
        "rationale",
    ],
    "properties": {
        "label": {"type": "string"},
        "age_logic": {"type": "string"},
        "face_geometry": {"type": "string"},
        "skin_logic": {"type": "string"},
        "hair_logic": {"type": "string"},
        "body_logic": {"type": "string"},
        "presence_logic": {"type": "string"},
        "expression_logic": {"type": "string"},
        "makeup_logic": {"type": "string"},
        "beauty_logic": {"type": "string"},
        "platform_presence": {"type": "string"},
        "commercial_read": {"type": "string"},
        "distinction_markers": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
}

CASTING_DIRECTION_SCHEMA = {
    "type": "object",
    "required": [
        "research_signals",
        "market_fit_summary",
        "candidate_directions",
        "chosen_label",
        "chosen_direction",
        "profile_hint",
        "casting_state",
        "anti_collapse_signals",
        "confidence",
    ],
    "properties": {
        "research_signals": {"type": "array", "items": {"type": "string"}},
        "market_fit_summary": {"type": "string"},
        "candidate_directions": {"type": "array", "items": _CANDIDATE_SCHEMA},
        "chosen_label": {"type": "string"},
        "chosen_direction": _CANDIDATE_SCHEMA,
        "profile_hint": {"type": "string"},
        "casting_state": {
            "type": "object",
            "required": ["age", "face_structure", "hair", "presence", "expression", "beauty_read"],
            "properties": {
                "age": {"type": "string"},
                "face_structure": {"type": "string"},
                "hair": {"type": "string"},
                "presence": {"type": "string"},
                "expression": {"type": "string"},
                "beauty_read": {"type": "string"},
            },
        },
        "anti_collapse_signals": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
}


def _clean_text(value: Any, *, limit: int = 220) -> str:
    return " ".join(str(value or "").strip().split())[:limit].strip()


def _clean_list(values: Any, *, limit: int = 6, item_limit: int = 120) -> list[str]:
    items = []
    for value in values or []:
        cleaned = _clean_text(value, limit=item_limit)
        if cleaned:
            items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def _extract_grounding_titles(response: Any) -> list[str]:
    titles: list[str] = []
    try:
        candidate = response.candidates[0] if response.candidates else None
        grounding_metadata = getattr(candidate, "grounding_metadata", None) if candidate else None
        chunks = getattr(grounding_metadata, "grounding_chunks", None) or []
        for chunk in chunks:
            web = getattr(chunk, "web", None)
            title = getattr(web, "title", None) if web else None
            if title:
                titles.append(str(title).strip())
    except Exception:
        pass
    return titles[:8]


def _normalize_candidate(raw: Optional[dict[str, Any]]) -> dict[str, Any]:
    payload = raw or {}
    return {
        "label": _clean_text(payload.get("label"), limit=60),
        "age_logic": _clean_text(payload.get("age_logic"), limit=90),
        "face_geometry": _clean_text(payload.get("face_geometry"), limit=140),
        "skin_logic": _clean_text(payload.get("skin_logic"), limit=140),
        "hair_logic": _clean_text(payload.get("hair_logic"), limit=160),
        "body_logic": _clean_text(payload.get("body_logic"), limit=140),
        "presence_logic": _clean_text(payload.get("presence_logic"), limit=140),
        "expression_logic": _clean_text(payload.get("expression_logic"), limit=140),
        "makeup_logic": _clean_text(payload.get("makeup_logic"), limit=140),
        "beauty_logic": _clean_text(payload.get("beauty_logic"), limit=140),
        "platform_presence": _clean_text(payload.get("platform_presence"), limit=140),
        "commercial_read": _clean_text(payload.get("commercial_read"), limit=140),
        "distinction_markers": _clean_list(payload.get("distinction_markers"), limit=4, item_limit=80),
        "rationale": _clean_text(payload.get("rationale"), limit=180),
    }


def _derive_casting_state(candidate: dict[str, Any]) -> dict[str, str]:
    return {
        "age": _clean_text(candidate.get("age_logic"), limit=60),
        "face_structure": _clean_text(candidate.get("face_geometry"), limit=140),
        "hair": _clean_text(candidate.get("hair_logic"), limit=160),
        "presence": _clean_text(candidate.get("presence_logic"), limit=140),
        "expression": _clean_text(candidate.get("expression_logic"), limit=140),
        "beauty_read": _clean_text(candidate.get("beauty_logic"), limit=140),
    }


def _derive_profile_hint(candidate: dict[str, Any]) -> str:
    parts = [
        _clean_text(candidate.get("age_logic"), limit=60),
        _clean_text(candidate.get("face_geometry"), limit=90),
        _clean_text(candidate.get("hair_logic"), limit=100),
        _clean_text(candidate.get("beauty_logic"), limit=80),
        _clean_text(candidate.get("platform_presence"), limit=80),
    ]
    return _clean_text(", ".join(part for part in parts if part), limit=240)


def _normalize_casting_direction(payload: Optional[dict[str, Any]]) -> dict[str, Any]:
    raw = payload or {}
    candidates = [
        normalized
        for normalized in (_normalize_candidate(item) for item in (raw.get("candidate_directions") or []))
        if normalized.get("label")
    ][:3]

    chosen_label = _clean_text(raw.get("chosen_label"), limit=60)
    chosen_direction = _normalize_candidate(raw.get("chosen_direction") if isinstance(raw.get("chosen_direction"), dict) else {})
    if not chosen_direction.get("label") and chosen_label:
        for candidate in candidates:
            if candidate.get("label") == chosen_label:
                chosen_direction = candidate
                break
    if not chosen_direction.get("label") and candidates:
        chosen_direction = candidates[0]
    if not chosen_label and chosen_direction.get("label"):
        chosen_label = chosen_direction["label"]

    raw_casting_state = raw.get("casting_state") if isinstance(raw.get("casting_state"), dict) else {}
    casting_state = {
        "age": _clean_text(raw_casting_state.get("age"), limit=60),
        "face_structure": _clean_text(raw_casting_state.get("face_structure"), limit=140),
        "hair": _clean_text(raw_casting_state.get("hair"), limit=160),
        "presence": _clean_text(raw_casting_state.get("presence"), limit=140),
        "expression": _clean_text(raw_casting_state.get("expression"), limit=140),
        "beauty_read": _clean_text(raw_casting_state.get("beauty_read"), limit=140),
    }
    if not any(casting_state.values()):
        casting_state = _derive_casting_state(chosen_direction)

    profile_hint = _clean_text(raw.get("profile_hint"), limit=240) or _derive_profile_hint(chosen_direction)

    return {
        "research_signals": _clean_list(raw.get("research_signals"), limit=8, item_limit=160),
        "market_fit_summary": _clean_text(raw.get("market_fit_summary"), limit=180),
        "candidate_directions": candidates,
        "chosen_label": chosen_label,
        "chosen_direction": chosen_direction,
        "profile_hint": profile_hint,
        "casting_state": casting_state,
        "anti_collapse_signals": _clean_list(raw.get("anti_collapse_signals"), limit=6, item_limit=120),
        "confidence": max(0.0, min(1.0, float(raw.get("confidence") or 0.0))),
    }


def _get_mode_casting_mandate(mode_id: Optional[str]) -> str:
    normalized = str(mode_id or "natural").strip().lower()
    if normalized == "catalog_clean":
        return (
            "Choose a commercially appealing woman whose face, body, and garment readability are immediately clear. "
            "She should feel brand-safe, attractive, and trustworthy for mainstream Brazilian ecommerce. "
            "Differentiate within that high-conversion band rather than escaping into severity, anonymity, or maturity inflation."
        )
    if normalized == "natural":
        return (
            "Choose a woman who feels real and lightly unproduced, but still beautiful, warm, contemporary, and commercially desirable. "
            "Natural means less staged and less beauty-set-up, not older, drained, severe, prestige-coded, or anti-beauty. "
            "She should still read as someone who could convert fashion in Shopee, TikTok, or Instagram through approachable attractiveness, not rarefied taste signaling."
        )
    if normalized == "lifestyle":
        return (
            "Choose a woman whose social presence feels active, contemporary, and creator-native. "
            "She should feel attractive, memorable, and commercially strong in social-commerce life, not generic, corporate, or conceptually austere."
        )
    if normalized == "editorial_commercial":
        return (
            "Choose a woman with stronger visual character and sharper fashion authority, while keeping clear desirability and sellability. "
            "Editorial-commercial strength should come from distinctive beauty and presence, not from aging her up or making her severe by default."
        )
    return (
        "Choose a commercially effective, attractive, high-trust Brazilian woman for mainstream social-commerce. "
        "Differentiate her clearly, but keep her inside a believable, desirable, creator-friendly market band."
    )


def _get_market_fit_band(mode_id: Optional[str]) -> str:
    normalized = str(mode_id or "natural").strip().lower()
    base = (
        "NON-NEGOTIABLE MARKET BAND:\n"
        "- The woman must feel commercially strong for Brazilian social-commerce fashion imagery.\n"
        "- She must read as clearly adult, attractive, trustworthy, memorable, and socially native.\n"
        "- Keep the center of gravity in the mainstream high-conversion creator/seller/presenter band for Shopee, TikTok, and Instagram.\n"
        "- Diversity must happen INSIDE that band, not by leaving it.\n"
        "- Do not solve originality with age inflation, austerity, severity, drained beauty, overt intellectualization, or hyper-corporate energy unless the garment clearly justifies it.\n"
        "- When the user asks for elegant, polished, refined, or sophisticated, translate that as desirable and commercially aspirational, not older or rigid.\n"
    )
    if normalized == "natural":
        return (
            base
            + "- In natural mode, lower production and lower status signaling are good, but the woman must still feel beautiful, current, and creator-relevant.\n"
            + "- Prefer a face that feels warm and credible in real life over a face that feels stern, drained, or deliberately serious.\n"
            + "- Avoid prestige-coded creative-class cues such as designer, architect, curator, concept-store, or premium-luxury energy.\n"
            + "- Keep the commercial read accessible, desirable, and everyday-social rather than elite, rarefied, or niche-taste.\n"
        )
    if normalized == "catalog_clean":
        return (
            base
            + "- In catalog_clean, keep beauty clean, legible, and broadly appealing. Avoid drifting into anonymous mannequin logic or mature luxury codes.\n"
        )
    if normalized == "lifestyle":
        return (
            base
            + "- In lifestyle, she should feel socially visible and naturally magnetic, like someone whose presence already works inside product-led social media.\n"
        )
    if normalized == "editorial_commercial":
        return (
            base
            + "- In editorial_commercial, sharpen distinction and taste, but keep her desirable and commercially usable rather than coldly conceptual.\n"
        )
    return base


def _needs_natural_market_recenter(payload: dict[str, Any], mode_id: Optional[str]) -> bool:
    if str(mode_id or "").strip().lower() != "natural":
        return False
    chosen = payload.get("chosen_direction") or {}
    haystack = " ".join(
        str(item or "").strip().lower()
        for item in (
            payload.get("market_fit_summary"),
            payload.get("profile_hint"),
            chosen.get("label"),
            chosen.get("presence_logic"),
            chosen.get("beauty_logic"),
            chosen.get("platform_presence"),
            chosen.get("commercial_read"),
            chosen.get("rationale"),
        )
    )
    return any(token in haystack for token in _NATURAL_PRESTIGE_DRIFT_TOKENS)


def resolve_casting_direction(
    *,
    mode_id: Optional[str],
    user_prompt: Optional[str],
    garment_hint: Optional[str],
    image_analysis: Optional[str],
    structural_contract: Optional[dict[str, Any]],
    garment_aesthetic: Optional[dict[str, Any]] = None,
    has_images: bool = False,
) -> dict[str, Any]:
    garment_text = _clean_text(garment_hint, limit=140)
    analysis_text = _clean_text(image_analysis, limit=500)
    contract = structural_contract or {}
    aesthetic = garment_aesthetic or {}
    mode_lines = get_mode_identity_soul(mode_id)
    model_soul = get_model_soul(garment_context=garment_text, mode_id=mode_id or "")
    mode_casting_mandate = _get_mode_casting_mandate(mode_id)
    market_fit_band = _get_market_fit_band(mode_id)
    prompt_text = _clean_text(user_prompt, limit=240) or "none"
    research_instruction = (
        "Use Google Search grounding first and return a compact research memo for Brazilian social-commerce casting.\n"
        "Focus on visual patterns only. Do not cite or imitate real people in the memo.\n"
        "Search for recent public signals across Brazilian female social-commerce creators, ecommerce presenters, marketplace sellers, beauty/fashion/lifestyle UGC, and mobile-first product imagery.\n"
        "Stay inside the market band below while mapping strengths, clichés, and open opportunities.\n"
        "Return plain text, not JSON.\n\n"
        "<MODE_IDENTITY>\n" + "\n".join(mode_lines) + "\n</MODE_IDENTITY>\n\n"
        "<MODE_CASTING_MANDATE>\n" + mode_casting_mandate + "\n</MODE_CASTING_MANDATE>\n\n"
        "<MARKET_FIT_BAND>\n" + market_fit_band + "</MARKET_FIT_BAND>\n\n"
        "<JOB_CONTEXT>\n"
        f"- mode_id: {str(mode_id or 'natural').strip().lower()}\n"
        f"- user_prompt: {prompt_text}\n"
        f"- garment_hint: {garment_text or 'unknown'}\n"
        f"- image_analysis: {analysis_text or 'unknown'}\n"
        f"- garment_subtype: {str(contract.get('garment_subtype') or 'unknown')}\n"
        f"- silhouette_volume: {str(contract.get('silhouette_volume') or 'unknown')}\n"
        f"- garment_length: {str(contract.get('garment_length') or 'unknown')}\n"
        f"- garment_formality: {str(aesthetic.get('formality') or 'unknown')}\n"
        f"- garment_season: {str(aesthetic.get('season') or 'unknown')}\n"
        f"- garment_vibe: {str(aesthetic.get('vibe') or 'unknown')}\n"
        f"- reference_mode: {'true' if has_images else 'false'}\n"
        "</JOB_CONTEXT>\n\n"
        "Return this compact memo with exactly these sections:\n"
        "1. SIGNALS: exactly 5 bullets covering recurring high-conversion visual signals, clichés, and underused opportunities.\n"
        "2. DESIRABILITY BAND: exactly 3 bullets defining the beauty/commercial center of gravity for this job.\n"
        "3. CANDIDATE SPREAD: exactly 3 short materially different casting directions, all still inside the same desirable social-commerce band.\n"
        "4. ANTI-COLLAPSE: up to 5 default patterns to avoid for this job.\n"
        "Keep it concise.\n"
    )

    def _call_json_model(raw_instruction: str, *, temperature: float, max_attempts: int) -> Any:
        # Usa o mesmo caminho de schema enforcement já validado pelo styling resolver.
        # max_attempts é mantido na assinatura por compatibilidade com os retries locais.
        _ = max_attempts
        return generate_structured_json(
            parts=[types.Part(text=raw_instruction)],
            schema=CASTING_DIRECTION_SCHEMA,
            temperature=temperature,
            max_tokens=2200,
            thinking_budget=0,
        )

    grounded_response = _generate_content_with_retry(
        model=MODEL_AGENT,
        parts=[types.Part(text=research_instruction)],
        config=types.GenerateContentConfig(
            temperature=0.35,
            max_output_tokens=1000,
            safety_settings=SAFETY_CONFIG,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_modalities=["TEXT"],
        ),
        max_attempts=3,
    )
    grounded_memo = _clean_text(_extract_response_text(grounded_response), limit=2200)
    if not grounded_memo:
        return {}

    instruction = (
        "Synthesize a grounded casting direction for this job.\n"
        "You are not writing the final image prompt yet. You are solving only the HUMAN CASTING.\n"
        "Use the grounded research memo below as contextual evidence, but create an original woman.\n"
        "Do not imitate or name any real person.\n"
        "Map the space before you choose: produce three materially different candidate directions before selecting one.\n"
        "The three candidates must differ in at least three dimensions among: age energy, face geometry, skin read, hair behavior, body read, polish level, and social presence.\n"
        "All three candidates must remain inside the high-conversion beauty/commercial band for Brazilian social-commerce.\n"
        "Avoid collapsing into the safest default of polished brunette waves, generic warm smile, and creator-beauty portrait logic unless the product context truly justifies it.\n"
        "Do NOT solve distinction by aging her up, making her severe, academic, architectural, drained, corporate, or conceptually intellectual unless the garment context explicitly demands that.\n"
        "The winning direction must remain beautiful, commercially effective, trustworthy, socially native, believable, and distinct.\n"
        "Prioritize the winner in this order: market fit, garment fit, mode fit, distinction.\n\n"
        "<MODE_IDENTITY>\n" + "\n".join(mode_lines) + "\n</MODE_IDENTITY>\n\n"
        "<MODEL_SOUL>\n" + model_soul + "\n</MODEL_SOUL>\n\n"
        "<MODE_CASTING_MANDATE>\n" + mode_casting_mandate + "\n</MODE_CASTING_MANDATE>\n\n"
        "<MARKET_FIT_BAND>\n" + market_fit_band + "</MARKET_FIT_BAND>\n\n"
        "<GROUNDED_RESEARCH_MEMO>\n" + grounded_memo + "\n</GROUNDED_RESEARCH_MEMO>\n\n"
        "<JOB_CONTEXT>\n"
        f"- mode_id: {str(mode_id or 'natural').strip().lower()}\n"
        f"- user_prompt: {prompt_text}\n"
        f"- garment_hint: {garment_text or 'unknown'}\n"
        f"- image_analysis: {analysis_text or 'unknown'}\n"
        f"- garment_subtype: {str(contract.get('garment_subtype') or 'unknown')}\n"
        f"- silhouette_volume: {str(contract.get('silhouette_volume') or 'unknown')}\n"
        f"- garment_length: {str(contract.get('garment_length') or 'unknown')}\n"
        f"- garment_formality: {str(aesthetic.get('formality') or 'unknown')}\n"
        f"- garment_season: {str(aesthetic.get('season') or 'unknown')}\n"
        f"- garment_vibe: {str(aesthetic.get('vibe') or 'unknown')}\n"
        "</JOB_CONTEXT>\n\n"
        "OUTPUT RULES:\n"
        "- research_signals: exactly 5 short lines distilled from the memo.\n"
        "- market_fit_summary: one short line on why the winner stays commercially right for Brazilian social-commerce.\n"
        "- candidate_directions: exactly 3 options, all original and materially different.\n"
        "- Every candidate must feel attractive, saleable, and socially native.\n"
        "- Use beauty_logic, platform_presence, and commercial_read to keep the winner in the correct market band.\n"
        "- Let differentiation come from geometry, skin read, hair behavior, polish level, and presence rather than age inflation.\n"
        "- chosen_direction: the best direction for this specific garment and mode.\n"
        "- profile_hint: one compact sentence summarizing the chosen casting direction.\n"
        "- casting_state: compact fields for downstream enforcement.\n"
        "- anti_collapse_signals: list the default patterns to avoid for this job.\n"
        "- Keep every field compact. Prefer short phrases over full paragraphs.\n"
        "- Keep candidate_directions especially short: each field should usually stay under 12 words.\n"
        "- distinction_markers should have at most 3 items.\n"
        "- Return strict JSON only.\n"
    )
    try:
        response = _call_json_model(instruction, temperature=0.35, max_attempts=3)
        parsed = _decode_agent_response(response)
    except Exception as exc:
        err_msg = str(exc)
        print(f"[MODEL_GROUNDING] ⚠️ first parse failed: {err_msg}")
        repaired = try_repair_truncated_json(err_msg)
        if repaired is not None:
            parsed = repaired
            response = None
        else:
            retry_instruction = (
                instruction
                + "\n\n[RETRY TRIGGERED]: The previous response was not valid JSON. "
                "Return EXACTLY one compact JSON object with the requested keys and nothing else. "
                "Do not exceed the minimum detail needed."
            )
            retry_response = _call_json_model(retry_instruction, temperature=0.2, max_attempts=2)
            try:
                parsed = _decode_agent_response(retry_response)
                response = retry_response
            except Exception as retry_exc:
                raw_preview = _extract_response_text(retry_response)[:600].replace("\n", " ")
                print(f"[MODEL_GROUNDING] ❌ retry parse failed: {retry_exc} | raw={raw_preview}")
                return {}

    normalized = _normalize_casting_direction(parsed if isinstance(parsed, dict) else {})
    if not normalized.get("chosen_direction") or not (normalized.get("chosen_direction") or {}).get("label"):
        compact_instruction = (
            instruction
            + "\n\n[COMPACT RECOVERY]: The previous output was incomplete. "
            "Use extremely compact phrasing. research_signals=5 items only. "
            "candidate_directions=3 very short options. chosen_direction short but complete."
        )
        try:
            recovery_response = _call_json_model(compact_instruction, temperature=0.2, max_attempts=2)
            recovery_parsed = _decode_agent_response(recovery_response)
            normalized = _normalize_casting_direction(recovery_parsed if isinstance(recovery_parsed, dict) else {})
            response = recovery_response
        except Exception as recovery_exc:
            print(f"[MODEL_GROUNDING] ❌ compact recovery failed: {recovery_exc}")
            return {}
    if not normalized.get("chosen_direction") or not (normalized.get("chosen_direction") or {}).get("label"):
        return {}

    if _needs_natural_market_recenter(normalized, mode_id):
        recenter_instruction = (
            instruction
            + "\n\n[MARKET RECENTER]: The previous solution drifted into prestige-coded or creative-class casting."
            " Re-solve the JSON while keeping the woman attractive, socially native, accessible, and high-conversion for mainstream Brazilian social-commerce."
            " In natural mode specifically, avoid architect/designer/curator/intellectual/luxury-coded energy."
            " Keep her beautiful and current, with approachable everyday desirability."
        )
        try:
            recenter_response = _call_json_model(recenter_instruction, temperature=0.2, max_attempts=2)
            recenter_parsed = _decode_agent_response(recenter_response)
            recentered = _normalize_casting_direction(recenter_parsed if isinstance(recenter_parsed, dict) else {})
            if recentered.get("chosen_direction") and (recentered.get("chosen_direction") or {}).get("label"):
                normalized = recentered
                response = recenter_response
        except Exception as recenter_exc:
            print(f"[MODEL_GROUNDING] ⚠️ market recenter failed: {recenter_exc}")

    normalized["grounding_titles"] = _extract_grounding_titles(grounded_response)
    if normalized.get("confidence", 0.0) > 0.0:
        chosen = normalized.get("chosen_direction") or {}
        print(
            "[MODEL_GROUNDING] ✅ "
            f"label={normalized.get('chosen_label') or chosen.get('label') or 'unknown'} "
            f"age={chosen.get('age_logic', '')[:40]} "
            f"hair={chosen.get('hair_logic', '')[:50]} "
            f"conf={normalized['confidence']:.2f}"
        )
    return normalized
