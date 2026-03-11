"""
Triagem visual — inferência de geometria, hint de peça, detecção de conjunto e triagem unificada.

Extraído de agent.py para manter o orquestrador enxuto.
Todas as funções são chamadas por run_agent() e pelos routers (via import direto).
"""
import re
import json
from typing import Optional, List

from google.genai import types

from agent_runtime.gemini_client import (
    generate_structured_json,
    generate_multimodal,
)
from agent_runtime.parser import (
    _extract_response_text,
    _decode_agent_response,
)
from agent_runtime.structural import (
    _normalize_structural_contract,
    _normalize_set_detection,
    _enum_or_default,
)
from agent_runtime.constants import (
    SET_DETECTION_SCHEMA,
    STRUCTURAL_CONTRACT_SCHEMA,
    UNIFIED_VISION_SCHEMA,
)


def _infer_text_mode_shot(user_prompt: Optional[str]) -> str:
    text = (user_prompt or "").lower()
    if any(k in text for k in ["macro", "close-up", "detalhe", "textura", "fio", "tecido"]):
        return "close-up"
    if any(k in text for k in ["hero", "capa", "full body", "corpo inteiro", "look completo"]):
        return "wide"
    if any(k in text for k in ["medium", "waist", "cintura", "busto", "meio corpo"]):
        return "medium"
    return "wide"


# ── Garment hint (curto, para montar queries de grounding) ───────────────────

def _infer_garment_hint(uploaded_images: List[bytes]) -> str:
    """Classificação curta da peça para montar queries de grounding quando não há prompt."""
    try:
        parts = []
        for img_bytes in uploaded_images:
            parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)
                )
            )
        parts.append(types.Part(text=(
            "Identify the garment type and silhouette in at most 8 words. "
            "Use terms like ruana, poncho aberto, batwing cardigan, dolman sleeve. "
            "Return plain text only."
        )))
        response = generate_multimodal(
            parts=parts,
            temperature=0.1,
            max_tokens=60,
        )
        hint = _extract_response_text(response).strip()
        hint = re.sub(r"\s+", " ", hint)
        return hint[:120]
    except Exception:
        return ""


# ── Structural contract (geometria da peça) ──────────────────────────────────

def _infer_structural_contract_from_images(uploaded_images: List[bytes], user_prompt: Optional[str]) -> dict:
    """
    Extrai geometria da peça (proporção/forma) para reduzir drift estrutural no prompt final.
    Não depende de tipo específico de roupa.
    """
    if not uploaded_images:
        return _normalize_structural_contract({})

    parts: List[types.Part] = []
    for img_bytes in uploaded_images:
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)))

    user_txt = (user_prompt or "").strip()
    instruction = (
        "Analyze garment geometry from these references and return strict JSON only. "
        "FIRST identify the garment_subtype. Use one of: "
        "standard_cardigan, ruana_wrap, poncho, cape, kimono, bolero, vest, jacket, pullover, dress, other. "
        "CLASSIFICATION RULE: if the garment lacks separate sewn-in sleeves and the arms are covered "
        "by a continuous draped fabric panel, it is ruana_wrap or poncho — NOT standard_cardigan. "
        "standard_cardigan requires separately constructed and sewn sleeve tubes. "
        "Then analyze: sleeve_type (set-in, raglan, dolman_batwing, drop_shoulder, cape_like), "
        "sleeve_length (sleeveless, cap, short, elbow, three_quarter, long), "
        "front_opening (open, partial, closed), hem_shape (straight, rounded, asymmetric, cocoon), "
        "garment_length (cropped, waist, hip, upper_thigh, mid_thigh, knee_plus), "
        "silhouette_volume (fitted, regular, oversized, draped, structured), "
        "must_keep (brief visual cues list), confidence (0.0-1.0), "
        "has_pockets (boolean: true if any pocket is clearly visible, false if garment has no pockets). "
        "Focus purely on structure, avoiding fabric pattern names or decorative details."
    )
    if user_txt:
        instruction += f" User context: {user_txt[:220]}"
    parts.append(types.Part(text=instruction))

    _empty = _normalize_structural_contract({})

    try:
        response = generate_structured_json(
            parts=parts,
            schema=STRUCTURAL_CONTRACT_SCHEMA,
            temperature=0.1,
            max_tokens=800,
            thinking_budget=0
        )
        parsed = _decode_agent_response(response)
    except Exception as e:
        err_msg = str(e)
        print(f"[AGENT] ⚠️ Structural contract inference failed: {err_msg}")
        # Fallback: tentar extrair campos parciais de JSON truncado
        if "raw=" in err_msg or "raw={" in err_msg:
            try:
                raw_start = err_msg.find("raw=") + 4
                raw_fragment = err_msg[raw_start:].replace("\\n", "\n").replace('\\"', '"')
                for suffix in ("}", '"}', '"]}'):
                    try:
                        parsed = json.loads(raw_fragment + suffix)
                        print(f"[AGENT] 🔧 Structural contract repaired from truncated JSON (suffix={suffix})")
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    return _empty
            except Exception:
                return _empty
        else:
            return _empty

    # Reutiliza a mesma normalizer da triagem unificada — single source of truth
    # para validação de campos, has_pockets, confidence, enabled, etc.
    return _normalize_structural_contract(parsed)


# ── Set pattern detection (conjunto coordenado) ─────────────────────────────

def _infer_set_pattern_from_images(uploaded_images: List[bytes], user_prompt: Optional[str]) -> dict:
    """
    Detecta se a referência sugere conjunto de ROUPAS por padrão visual (cor/textura/motivo).
    Ignora acessórios como critério de conjunto.
    """
    if not uploaded_images:
        return {
            "is_garment_set": False,
            "set_pattern_score": 0.0,
            "detected_garment_roles": [],
            "set_pattern_cues": [],
            "set_lock_mode": "off",
        }

    parts: List[types.Part] = []
    for img_bytes in uploaded_images:
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)))

    user_txt = (user_prompt or "").strip()
    text_instruction = (
        "Analyze whether the clothing in these references forms a coordinated garment set based on repeated "
        "visual pattern cues (color palette, texture/stitch family, motif spacing, construction coherence). "
        "Use ONLY garment pieces as evidence. Ignore accessories (scarves, bags, belts, hats, jewelry, shoes) "
        "as set-defining elements. For detected_garment_roles, use descriptive multi-word labels "
        "(e.g., 'ribbed cardigan', 'pleated midi skirt'), NOT generic single-word labels like 'top' or 'bottom'. "
        "Return strict JSON."
    )
    if user_txt:
        text_instruction += f" User context: {user_txt[:200]}"
    parts.append(types.Part(text=text_instruction))

    try:
        response = generate_structured_json(
            parts=parts,
            schema=SET_DETECTION_SCHEMA,
            temperature=0.1,
            max_tokens=800,
            thinking_budget=0
        )
        parsed = _decode_agent_response(response)
        is_set = bool(parsed.get("is_garment_set", False))
        score = float(parsed.get("set_pattern_score", 0.0) or 0.0)
        roles = [str(x) for x in (parsed.get("detected_garment_roles", []) or []) if str(x)]
        cues = [str(x) for x in (parsed.get("set_pattern_cues", []) or []) if str(x)]
        score = max(0.0, min(1.0, score))
        lock_mode = "explicit" if (is_set and score >= 0.68 and len(roles) >= 2) else ("generic" if is_set else "off")
        return {
            "is_garment_set": is_set,
            "set_pattern_score": round(score, 3),
            "detected_garment_roles": roles[:5],
            "set_pattern_cues": cues[:4],
            "set_lock_mode": lock_mode,
        }
    except Exception as e:
        err_msg = str(e)
        print(f"[GUIDED] ⚠️ set-pattern inference failed: {err_msg}")
        repaired: Optional[dict] = None
        if "raw=" in err_msg:
            try:
                raw_start = err_msg.find("raw=") + 4
                fragment = err_msg[raw_start:].replace("\\n", "\n").replace('\\"', '"')
                for suffix in ("}", '"}', '"]}', "]}", '"}]}'):
                    try:
                        repaired = json.loads(fragment + suffix)
                        print(f"[GUIDED] 🔧 set-pattern JSON repaired (suffix={suffix!r})")
                        break
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass
        if repaired is not None:
            is_set = bool(repaired.get("is_garment_set", False))
            score = max(0.0, min(1.0, float(repaired.get("set_pattern_score", 0.0) or 0.0)))
            roles = [str(x) for x in (repaired.get("detected_garment_roles", []) or []) if str(x)]
            cues = [str(x) for x in (repaired.get("set_pattern_cues", []) or []) if str(x)]
            lock_mode = "explicit" if (is_set and score >= 0.68 and len(roles) >= 2) else ("generic" if is_set else "off")
            return {
                "is_garment_set": is_set,
                "set_pattern_score": round(score, 3),
                "detected_garment_roles": roles[:5],
                "set_pattern_cues": cues[:4],
                "set_lock_mode": lock_mode,
            }
        return {
            "is_garment_set": False,
            "set_pattern_score": 0.0,
            "detected_garment_roles": [],
            "set_pattern_cues": [],
            "set_lock_mode": "off",
        }


# ── Triagem visual unificada (1 chamada = hint + contract + set) ─────────────

def _infer_unified_vision_triage(
    uploaded_images: List[bytes],
    user_prompt: Optional[str],
) -> Optional[dict]:
    """
    UMA única chamada Gemini que substitui as 3 chamadas visuais separadas:
      _infer_garment_hint + _infer_structural_contract_from_images + _infer_set_pattern_from_images

    Retorna dict com: garment_hint, image_analysis, structural_contract, set_detection.
    Retorna None se falhar — run_agent() cai no fallback individual.
    """
    if not uploaded_images:
        return None

    parts: List[types.Part] = []
    for img_bytes in uploaded_images:
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)))

    user_txt = (user_prompt or "").strip()
    instruction = (
        "Analyze these garment reference images and return strict JSON with ALL five fields.\n\n"
        "1. garment_hint: identify the garment type and silhouette in 8 words max "
        "(e.g. ruana, poncho aberto, batwing cardigan, dolman sleeve). Plain text.\n\n"
        "2. image_analysis: 2-3 sentences describing the GARMENT visible in the reference. "
        "Include: dominant colors and color temperature (warm/cool/neutral), "
        "fabric texture appearance, overall aesthetic mood, and suggested styling context. "
        "Focus on visual qualities that inform casting and scenario decisions. "
        "Do NOT describe the person wearing the garment — focus 100% on the clothing.\n\n"
        "3. structural_contract: analyze garment GEOMETRY only. "
        "garment_subtype: one of standard_cardigan|ruana_wrap|poncho|cape|kimono|bolero|vest|"
        "jacket|pullover|dress|other. "
        "RULE: if arms are covered by continuous draped panel (no separate sewn sleeves) → ruana_wrap or poncho. "
        "If the neckline flows directly into the front opening as the same knitted edge, treat it as draped wrap geometry, not a tailored collar or cardigan lapel. "
        "For draped wraps, measure garment_length by the lowest outer side drop, not by the folded inner front edge. "
        "If the outer silhouette curves into a soft envelope or cocoon-like side drop, prefer rounded or cocoon over straight. "
        "sleeve_type: set-in|raglan|dolman_batwing|drop_shoulder|cape_like. "
        "sleeve_length: sleeveless|cap|short|elbow|three_quarter|long. "
        "front_opening: open|partial|closed. hem_shape: straight|rounded|asymmetric|cocoon. "
        "garment_length: cropped|waist|hip|upper_thigh|mid_thigh|knee_plus. "
        "silhouette_volume: fitted|regular|oversized|draped|structured. "
        "must_keep: up to 4 brief GEOMETRY cues only, such as continuous neckline-to-front edge, broad uninterrupted back panel, rounded cocoon side drop, or arm coverage formed by the same draped panel. "
        "Do NOT use generic cues like 'open front', 'knit texture', or simple stripe mentions unless they are structurally critical. "
        "confidence: 0.0-1.0. "
        "has_pockets: boolean — true if ANY pocket (patch, welt, side-seam) is clearly visible "
        "on the garment; false if the garment has NO visible pockets whatsoever.\n\n"
        "4. set_detection: do these references show a COORDINATED GARMENT SET "
        "(matching color/texture/pattern across separate garment pieces)? Ignore accessories. "
        "is_garment_set: bool. set_pattern_score: 0.0-1.0. "
        "detected_garment_roles: list. set_pattern_cues: list.\n\n"
        "5. garment_aesthetic: casting/scenario intelligence for the garment. "
        "color_temperature: warm|cool|neutral (dominant color feel). "
        "formality: casual|smart_casual|formal. "
        "season: summer|mid_season|winter (most natural occasion). "
        "vibe: boho_artisanal|urban_chic|romantic|bold_edgy|minimalist|beachwear_resort|sport_casual."
    )
    if user_txt:
        instruction += f"\n\nUser context: {user_txt[:200]}"
    parts.append(types.Part(text=instruction))

    try:
        response = generate_structured_json(
            parts=parts,
            schema=UNIFIED_VISION_SCHEMA,
            temperature=0.1,
            max_tokens=1200,
            thinking_budget=0
        )
        parsed = _decode_agent_response(response)
        if not isinstance(parsed, dict):
            print("[AGENT] ⚠️  unified_vision_triage: response not a dict")
            return None

        garment_hint   = re.sub(r"\s+", " ", str(parsed.get("garment_hint") or "").strip())[:120]
        image_analysis = str(parsed.get("image_analysis") or "").strip()[:500]

        # garment_aesthetic: normalizar com fallback seguro por campo
        _VALID_COLOR_TEMP = {"warm", "cool", "neutral"}
        _VALID_FORMALITY = {"casual", "smart_casual", "formal"}
        _VALID_SEASON = {"summer", "mid_season", "winter"}
        _VALID_VIBE = {
            "boho_artisanal", "urban_chic", "romantic", "bold_edgy",
            "minimalist", "beachwear_resort", "sport_casual",
        }
        raw_aesthetic = parsed.get("garment_aesthetic") or {}
        if not isinstance(raw_aesthetic, dict):
            raw_aesthetic = {}
        garment_aesthetic = {
            "color_temperature": raw_aesthetic.get("color_temperature", "neutral")
                if raw_aesthetic.get("color_temperature") in _VALID_COLOR_TEMP else "neutral",
            "formality": raw_aesthetic.get("formality", "casual")
                if raw_aesthetic.get("formality") in _VALID_FORMALITY else "casual",
            "season": raw_aesthetic.get("season", "mid_season")
                if raw_aesthetic.get("season") in _VALID_SEASON else "mid_season",
            "vibe": raw_aesthetic.get("vibe", "minimalist")
                if raw_aesthetic.get("vibe") in _VALID_VIBE else "minimalist",
        }

        result = {
            "garment_hint":        garment_hint,
            "image_analysis":      image_analysis,
            "structural_contract": _normalize_structural_contract(parsed.get("structural_contract") or {}),
            "set_detection":       _normalize_set_detection(parsed.get("set_detection") or {}),
            "garment_aesthetic":   garment_aesthetic,
        }
        print(
            f"[AGENT] ✅ unified_vision_triage: success "
            f"(hint='{garment_hint[:60]}' aesthetic={garment_aesthetic})"
        )
        return result
    except Exception as e:
        print(f"[AGENT] ⚠️  unified_vision_triage: failed ({e}), using fallback")
        return None
