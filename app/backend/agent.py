"""
Prompt Agent — Gemini Flash (texto).

3 modos de operação:
  MODO 1: Usuário deu prompt → agente refina aplicando skills
  MODO 2: Usuário enviou imagens → agente descreve e cria prompt (Fidelity Lock)
  MODO 3: Sem prompt nem imagens → agente gera do zero via contexto do pool

Saída JSON:
  {
    "prompt": str,
    "thinking_level": "MINIMAL" | "HIGH",
    "thinking_reason": str,        # pt-BR
    "shot_type": "wide" | "medium" | "close-up" | "auto",
    "realism_level": 1 | 2 | 3
  }
"""
import re
import json
import random
from html import unescape
from io import BytesIO
from urllib.parse import urlencode, urljoin
from typing import Any, Optional, List

import requests
from PIL import Image

from google import genai
from google.genai import types

from config import GOOGLE_AI_API_KEY, MODEL_AGENT, SAFETY_CONFIG
from guided_mode import guided_capture_to_shot, guided_summary

from agent_runtime.parser import (
    _extract_balanced_json,
    _safe_json_loads,
    _parse_json,
    _extract_response_text,
    _decode_agent_response,
)
from agent_runtime.camera import (
    _CAMERA_REALISM_KEYWORDS,
    _CAMERA_REALISM_PROFILE_DEFAULTS,
    _ANALOG_EDITORIAL_HINTS,
    _NATURAL_CATALOG_HINTS,
    _CAMERA_PERSONA_STRIP_SIGNALS,
    _extract_camera_realism_block,
    _camera_framing_label,
    _select_camera_realism_profile,
    _default_camera_realism_block,
    _normalize_camera_realism_block,
    _compose_prompt_with_camera,
)
from agent_runtime.structural import (
    _normalize_structural_contract,
    _normalize_set_detection,
    normalize_prompt_text,
)
from agent_runtime.compiler import (
    _compile_prompt_v2,
)

from agent_runtime.visual_refs import _collect_grounded_reference_images
from agent_runtime.grounding import (
    _extract_search_results_from_duckduckgo,
    _duckduckgo_search,
    _build_forced_grounding_queries,
    _format_forced_grounding_text,
    _extract_pose_clause,
    _run_grounding_research,
)

from agent_runtime.constants import (
    AGENT_RESPONSE_SCHEMA,
    SET_DETECTION_SCHEMA,
    STRUCTURAL_CONTRACT_SCHEMA,
    UNIFIED_VISION_SCHEMA,
    SYSTEM_INSTRUCTION,
    REFERENCE_KNOWLEDGE,
    _SLEEVE_TYPE_PHRASES,
    _SLEEVE_LEN_PHRASES,
    _HEM_PHRASES,
    _LENGTH_PHRASES,
    _VOLUME_PHRASES,
    _FRONT_OPENING_PHRASES,
    _RESIDUAL_NEG_RE,
    _LABEL_STRIP_RE,
    _NEG_CLAUSE_RE,
    _WITHOUT_MAP,
    _CATALOG_STANCE_POOL,
    _OUTDOOR_URBAN_KW,
    _OUTDOOR_NATURE_KW,
    _INDOOR_KW,
    _POSE_KEYWORDS,
)

import os as _os
client = genai.Client(api_key=GOOGLE_AI_API_KEY)

# Controla a engine de coleta de imagens no grounding full.
# off (padrão) — sem coleta de imagens; grounding textual apenas
# html          — requests leve (sem Chromium); fallback html scraping
# playwright    — Playwright sync + fallback html (comportamento original)







_last_profile_idx: int = -1
_last_scenario_idx: int = -1
_last_pose_idx: int = -1
def _sample_diversity_target() -> tuple[str, str, str]:
    """
    Latent Space Casting: gera persona brasileira única via Name Blending dinâmico.
    Não hardcoda traços físicos — âncora por nome + vibe geográfica + tier de agência
    para que o modelo puxe clusters de beleza real do espaço latente.
    """
    global _last_profile_idx, _last_scenario_idx, _last_pose_idx

    # ── 1. Name Blending: pares de nomes + sobrenome para identidade facial única ──
    _FIRST_NAMES = [
        "Camila", "Dandara", "Isadora", "Juliana", "Taís", "Valentina",
        "Yasmin", "Nayara", "Marina", "Luiza", "Bruna", "Aline",
        "Letícia", "Sofia", "Gabriela", "Fernanda", "Renata", "Bianca",
    ]
    _SURNAMES = [
        "Silva", "Costa", "Souza", "Albuquerque", "Ribeiro",
        "Ferreira", "Lima", "Gomes", "Macedo", "Coutinho",
    ]

    # ── 2. Vibe geográfica: puxa fenótipo e lifestyle organicamente ──────────────
    _VIBES = [
        "chic Paulistana",
        "radiant Baiana",
        "sophisticated Carioca",
        "elegant Sulista",
        "striking Northeastern",
        "contemporary Mineira",
        "fresh-faced Brasília native",
    ]

    # ── 3. Casting tier: garante beleza de alto impacto no espaço latente ────────
    _AGENCIES = [
        "Ford Models Brazil new face",
        "Vogue Brasil editorial talent",
        "premium e-commerce lookbook model",
        "São Paulo Fashion Week casting aesthetic",
        "high-end commercial beauty",
        "FARM Rio campaign face",
        "Lança Perfume lookbook model",
    ]

    # ── 4. Poses cinestésicas ────────────────────────────────────────────────────
    poses = [
        "classic editorial contrapposto, relaxed asymmetrical shoulders, fluid weight shift",
        "dynamic mid-stride walking motion, elegant and confident catalog movement",
        "effortless lookbook posture, relaxed limbs, candid and approachable",
        "subtle fashion stance, chin slightly tilted, confident direct gaze at camera",
        "caught mid-turn, garment flowing naturally, effortless off-duty model vibe",
    ]

    # ── 5. Cenários catalog-friendly ─────────────────────────────────────────────
    scenarios = [
        "bright minimalist studio aesthetic with large windows and soft daylight",
        "upscale modern downtown with clean architecture and soft depth of field",
        "cozy high-end café terrace with warm ambient lighting",
        "charming shopping district at golden hour with softly blurred boutique storefronts",
        "lush botanical garden pathway with dappled natural sunlight",
        "rooftop garden terrace with city skyline in late afternoon light",
        "warm neutral living room with soft window light and clean decor",
    ]

    # Anti-repeat rotation
    po_choices = [i for i in range(len(poses)) if i != _last_pose_idx]
    s_choices = [i for i in range(len(scenarios)) if i != _last_scenario_idx]

    _last_pose_idx = random.choice(po_choices)
    _last_scenario_idx = random.choice(s_choices)
    _last_profile_idx = 0  # não usado — perfil é gerado dinamicamente abaixo

    # ── Montagem da persona: compacto ~14w — name blend + vibe + tier ────────────
    # Skin realism ("visible pores, peach fuzz") fica no DIVERSITY_TARGET block
    # que o Gemini inclui no camera_and_realism; não precisa duplicar aqui.
    n1, n2 = random.sample(_FIRST_NAMES, 2)
    surname = random.choice(_SURNAMES)
    vibe = random.choice(_VIBES)
    agency = random.choice(_AGENCIES)

    profile_prompt = (
        f"A {vibe} {agency}, "
        f"features blend '{n1}' and '{n2} {surname}'."
    )

    return profile_prompt, scenarios[_last_scenario_idx], poses[_last_pose_idx]



def _enum_or_default(value: Any, allowed: set[str], default: str = "unknown") -> str:
    v = str(value or "").strip().lower()
    return v if v in allowed else default


def _infer_structural_contract_from_images(uploaded_images: List[bytes], user_prompt: Optional[str]) -> dict:
    """
    Extrai geometria da peça (proporção/forma) para reduzir drift estrutural no prompt final.
    Não depende de tipo específico de roupa.
    """
    base = {
        "enabled": False,
        "confidence": 0.0,
        "garment_subtype": "unknown",
        "sleeve_type": "unknown",
        "sleeve_length": "unknown",
        "front_opening": "unknown",
        "hem_shape": "unknown",
        "garment_length": "unknown",
        "silhouette_volume": "unknown",
        "must_keep": [],
    }
    if not uploaded_images:
        return base

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

    try:
        response = client.models.generate_content(
            model=MODEL_AGENT,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=800,
                safety_settings=SAFETY_CONFIG,
                response_mime_type="application/json",
                response_json_schema=STRUCTURAL_CONTRACT_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
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
                # Tentar completar JSON truncado com }
                for suffix in ("}", '"}', '"]}'): 
                    try:
                        parsed = json.loads(raw_fragment + suffix)
                        print(f"[AGENT] 🔧 Structural contract repaired from truncated JSON (suffix={suffix})")
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    return base
            except Exception:
                return base
        else:
            return base

    garment_subtype = _enum_or_default(
        parsed.get("garment_subtype"),
        {
            "standard_cardigan", "ruana_wrap", "poncho", "cape",
            "kimono", "bolero", "vest", "jacket", "blazer",
            "pullover", "t_shirt", "blouse", "dress", "skirt",
            "pants", "shorts", "jumpsuit", "other", "unknown",
        },
    )
    sleeve_type = _enum_or_default(
        parsed.get("sleeve_type"),
        {"set-in", "raglan", "dolman_batwing", "drop_shoulder", "cape_like", "unknown"},
    )
    sleeve_length = _enum_or_default(
        parsed.get("sleeve_length"),
        {"sleeveless", "cap", "short", "elbow", "three_quarter", "long", "unknown"},
    )
    front_opening = _enum_or_default(parsed.get("front_opening"), {"open", "partial", "closed", "unknown"})
    hem_shape = _enum_or_default(parsed.get("hem_shape"), {"straight", "rounded", "asymmetric", "cocoon", "unknown"})
    garment_length = _enum_or_default(
        parsed.get("garment_length"),
        {"cropped", "waist", "hip", "upper_thigh", "mid_thigh", "knee_plus", "unknown"},
    )
    silhouette_volume = _enum_or_default(
        parsed.get("silhouette_volume"),
        {"fitted", "regular", "oversized", "draped", "structured", "unknown"},
    )

    try:
        confidence = float(parsed.get("confidence", 0.0) or 0.0)
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    must_keep_raw = list(parsed.get("must_keep", []) or [])
    must_keep = []
    for item in must_keep_raw:
        txt = str(item or "").strip()
        if not txt:
            continue
        must_keep.append(txt[:84])
        if len(must_keep) >= 4:
            break

    known_fields = [
        sleeve_type != "unknown",
        sleeve_length != "unknown",
        front_opening != "unknown",
        hem_shape != "unknown",
        garment_length != "unknown",
        silhouette_volume != "unknown",
    ]
    enabled = confidence >= 0.45 and any(known_fields)

    return {
        "enabled": enabled,
        "confidence": round(confidence, 3),
        "garment_subtype": garment_subtype,
        "sleeve_type": sleeve_type,
        "sleeve_length": sleeve_length,
        "front_opening": front_opening,
        "hem_shape": hem_shape,
        "garment_length": garment_length,
        "silhouette_volume": silhouette_volume,
        "must_keep": must_keep,
    }


def _infer_text_mode_shot(user_prompt: Optional[str]) -> str:
    text = (user_prompt or "").lower()
    if any(k in text for k in ["macro", "close-up", "detalhe", "textura", "fio", "tecido"]):
        return "close-up"
    if any(k in text for k in ["hero", "capa", "full body", "corpo inteiro", "look completo"]):
        return "wide"
    if any(k in text for k in ["medium", "waist", "cintura", "busto", "meio corpo"]):
        return "medium"
    return "wide"


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
        response = client.models.generate_content(
            model=MODEL_AGENT,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=60,
                safety_settings=SAFETY_CONFIG,
            ),
        )
        hint = _extract_response_text(response).strip()
        hint = re.sub(r"\s+", " ", hint)
        return hint[:120]
    except Exception:
        return ""


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
        "as set-defining elements. Return strict JSON."
    )
    if user_txt:
        text_instruction += f" User context: {user_txt[:200]}"
    parts.append(types.Part(text=text_instruction))

    try:
        response = client.models.generate_content(
            model=MODEL_AGENT,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=800,
                safety_settings=SAFETY_CONFIG,
                response_mime_type="application/json",
                response_json_schema=SET_DETECTION_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
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
        # Repair: tenta fechar JSON truncado e extrair campos parciais
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
            cues  = [str(x) for x in (repaired.get("set_pattern_cues", []) or []) if str(x)]
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
        "Analyze these garment reference images and return strict JSON with ALL four fields.\n\n"
        "1. garment_hint: identify the garment type and silhouette in 8 words max "
        "(e.g. ruana, poncho aberto, batwing cardigan, dolman sleeve). Plain text.\n\n"
        "2. image_analysis: one sentence high-level description of what is visible.\n\n"
        "3. structural_contract: analyze garment GEOMETRY only. "
        "garment_subtype: one of standard_cardigan|ruana_wrap|poncho|cape|kimono|bolero|vest|"
        "jacket|pullover|dress|other. "
        "RULE: if arms are covered by continuous draped panel (no separate sewn sleeves) → ruana_wrap or poncho. "
        "sleeve_type: set-in|raglan|dolman_batwing|drop_shoulder|cape_like. "
        "sleeve_length: sleeveless|cap|short|elbow|three_quarter|long. "
        "front_opening: open|partial|closed. hem_shape: straight|rounded|asymmetric|cocoon. "
        "garment_length: cropped|waist|hip|upper_thigh|mid_thigh|knee_plus. "
        "silhouette_volume: fitted|regular|oversized|draped|structured. "
        "must_keep: up to 4 brief visual cues. confidence: 0.0-1.0. "
        "has_pockets: boolean — true if ANY pocket (patch, welt, side-seam) is clearly visible "
        "on the garment; false if the garment has NO visible pockets whatsoever.\n\n"
        "4. set_detection: do these references show a COORDINATED GARMENT SET "
        "(matching color/texture/pattern across separate garment pieces)? Ignore accessories. "
        "is_garment_set: bool. set_pattern_score: 0.0-1.0. "
        "detected_garment_roles: list. set_pattern_cues: list."
    )
    if user_txt:
        instruction += f"\n\nUser context: {user_txt[:200]}"
    parts.append(types.Part(text=instruction))

    try:
        response = client.models.generate_content(
            model=MODEL_AGENT,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1200,
                safety_settings=SAFETY_CONFIG,
                response_mime_type="application/json",
                response_json_schema=UNIFIED_VISION_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        parsed = _decode_agent_response(response)
        if not isinstance(parsed, dict):
            print("[AGENT] ⚠️  unified_vision_triage: response not a dict")
            return None

        garment_hint   = re.sub(r"\s+", " ", str(parsed.get("garment_hint") or "").strip())[:120]
        image_analysis = str(parsed.get("image_analysis") or "").strip()[:300]
        result = {
            "garment_hint":        garment_hint,
            "image_analysis":      image_analysis,
            "structural_contract": _normalize_structural_contract(parsed.get("structural_contract") or {}),
            "set_detection":       _normalize_set_detection(parsed.get("set_detection") or {}),
        }
        print(f"[AGENT] ✅ unified_vision_triage: success (hint='{garment_hint[:60]}')")
        return result
    except Exception as e:
        print(f"[AGENT] ⚠️  unified_vision_triage: failed ({e}), using fallback")
        return None


def run_agent(
    user_prompt: Optional[str],
    uploaded_images: Optional[List[bytes]],
    pool_context: str,
    aspect_ratio: str,
    resolution: str,
    use_grounding: bool = False,
    grounding_mode: str = "lexical",
    grounding_context_hint: Optional[str] = None,
    diversity_target: Optional[dict] = None,
    guided_brief: Optional[dict] = None,
    structural_contract_hint: Optional[dict] = None,
) -> dict:
    """
    Executa o Prompt Agent e retorna:
    {
        "prompt": str,
        "thinking_level": "MINIMAL" | "HIGH",
        "thinking_reason": str,
        "shot_type": "wide" | "medium" | "close-up" | "auto",
        "realism_level": 1 | 2 | 3,
    }
    """
    has_prompt = bool(user_prompt and user_prompt.strip())
    has_images = bool(uploaded_images)
    pipeline_mode = "reference_mode" if has_images else "text_mode"
    guided_enabled = bool(guided_brief and guided_brief.get("enabled"))
    guided_set_mode = str((((guided_brief or {}).get("garment") or {}).get("set_mode") or "")).strip().lower()
    guided_set_detection = {
        "is_garment_set": False,
        "set_pattern_score": 0.0,
        "detected_garment_roles": [],
        "set_pattern_cues": [],
        "set_lock_mode": "off",
    }
    structural_contract = {
        "enabled": False,
        "confidence": 0.0,
        "sleeve_type": "unknown",
        "sleeve_length": "unknown",
        "front_opening": "unknown",
        "hem_shape": "unknown",
        "garment_length": "unknown",
        "silhouette_volume": "unknown",
        "must_keep": [],
    }
    has_pool = bool(
        pool_context
        and "No reference" not in pool_context
        and "POOL_RUNTIME_DISABLED" not in pool_context
    )

    # ── Triagem visual unificada: UMA chamada Gemini por run_agent() ─────────
    # Consolida _infer_garment_hint + _infer_structural_contract + _infer_set_pattern
    # em uma única chamada. Fallback seguro para as funções individuais se falhar.
    _unified: Optional[dict] = None
    _unified_garment_hint: str = ""
    if has_images:
        if isinstance(structural_contract_hint, dict) and structural_contract_hint:
            # structural_contract já fornecido externamente — ainda roda unificada para hint/set
            structural_contract = structural_contract_hint
            _unified_garment_hint = _infer_garment_hint(uploaded_images or [])
            print(f"[AGENT] unified_vision_triage: skipped (external structural_contract_hint provided)")
        else:
            _unified = _infer_unified_vision_triage(uploaded_images or [], user_prompt)
            if _unified:
                structural_contract   = _unified["structural_contract"]
                _unified_garment_hint = _unified["garment_hint"]
                # set_detection: aplica override de lock_mode se necessário
                _sd = _unified["set_detection"]
                if guided_enabled and guided_set_mode == "conjunto":
                    if _sd.get("set_lock_mode") == "off":
                        _sd["set_lock_mode"] = "generic"
                    guided_set_detection = _sd
            else:
                # Fallback individual
                print("[AGENT] unified_vision_triage: fallback")
                structural_contract = _infer_structural_contract_from_images(uploaded_images or [], user_prompt)
                if guided_enabled and guided_set_mode == "conjunto":
                    guided_set_detection = _infer_set_pattern_from_images(uploaded_images or [], user_prompt)
                    if guided_set_detection.get("set_lock_mode") == "off":
                        guided_set_detection["set_lock_mode"] = "generic"
                _unified_garment_hint = _infer_garment_hint(uploaded_images or [])
    elif guided_enabled and guided_set_mode == "conjunto":
        # Sem imagens: set detection sem triagem visual
        guided_set_detection = _infer_set_pattern_from_images([], user_prompt)

    if has_images:
        # FIX: ternário separado para não engolir o MODE 2
        if has_prompt:
            extra_text = f'User text to incorporate: "{user_prompt}".'
        else:
            extra_text = (
                "No text from user. Extract ONLY the garment (color, fabric, structure, pattern) "
                "from the reference images. The person/model shown in the reference is NOT the "
                "subject — completely ignore her appearance. Build the hero shot around the "
                "DIVERSITY_TARGET new model profile, scenario, and pose."
            )
        mode_info = (
            f"MODE 2 — User sent {len(uploaded_images)} reference image(s). "
            f"Extract GARMENT ONLY from the reference (do NOT use the reference person's appearance). "
            f"The reference model is a placeholder — she will be fully replaced by DIVERSITY_TARGET. "
            f"{extra_text}"
        )
    elif has_prompt:
        mode_info = (
            f'MODE 1 — Refine this user prompt for e-commerce conversion: "{user_prompt}". '
            "Prioritize coherent scenario, polished model presentation, and clear garment visibility."
        )
    else:
        mode_info = (
            "MODE 3 — No prompt or images. Generate a clean, commercially attractive catalog prompt. "
            "Prefer coherent composition and direct visual focus on the garment."
        )

    # ── Construção da Mensagem em Blocos (Mitiga "lost in the middle") ──
    blocks: List[str] = []

    blocks.append(f"<MODE>\n{mode_info}\n</MODE>")

    if has_pool:
        blocks.append(f"<POOL_CONTEXT>\n{pool_context}\n</POOL_CONTEXT>")

    blocks.append(f"<OUTPUT_PARAMETERS>\naspect_ratio={aspect_ratio}\nresolution={resolution}\n</OUTPUT_PARAMETERS>")

    # Profile: SEMPRE gera dinamicamente via name blending (ignora _PROFILE_POOL estático
    # que produz AI Face com anatomia explícita). Scenario/pose: usa diversity_target
    # para preservar lógica anti-repeat do select_diversity_target.
    profile, _fb_scenario, _fb_pose = _sample_diversity_target()
    if diversity_target:
        scenario = diversity_target.get("scenario_prompt", "") or _fb_scenario
        pose = diversity_target.get("pose_prompt", "") or _fb_pose
    else:
        scenario = _fb_scenario
        pose = _fb_pose

    div_block = "<DIVERSITY_TARGET>\n"
    if diversity_target:
        div_block += f"Model profile ID: {diversity_target.get('profile_id', 'RUNTIME')}.\n"
    div_block += (
        # ── GARMENT-ONLY REFERENCE MODE ─────────────────────────────────────────────
        # A pessoa/modelo na imagem de referência NÃO faz parte deste produto.
        # O compilador deve extrair APENAS a peça e construir uma modelo nova do zero.
        "GARMENT-ONLY REFERENCE MODE — CRITICAL RULES:\n"
        "  1. Reference images = garment source ONLY (color, fabric, structure, pattern).\n"
        "  2. The model/person visible in the reference is NOT the subject. Discard her completely.\n"
        "  3. DO NOT copy reference model's face, skin tone, hair, body shape, height, or pose.\n"
        "  4. DO NOT describe or reference the person shown — treat reference as if she were a mannequin.\n"
        f"  5. GENERATE A BRAND NEW MODEL: {profile}\n"
        f"  6. Place new model in scenario: {scenario}\n"
        f"  7. Use pose: {pose}\n"
        "  8. In base_prompt: open with the new model profile BEFORE garment description.\n"
        "     Example: 'RAW photo, [new model profile]. Wearing a [garment from reference]...'\n"
        "</DIVERSITY_TARGET>"
    )
    blocks.append(div_block)

    if guided_enabled:
        garment = (guided_brief or {}).get("garment", {}) or {}
        model = (guided_brief or {}).get("model", {}) or {}
        scene = (guided_brief or {}).get("scene", {}) or {}
        pose_cfg = (guided_brief or {}).get("pose", {}) or {}
        capture = (guided_brief or {}).get("capture", {}) or {}
        fidelity_mode = str((guided_brief or {}).get("fidelity_mode", "balanceada")).strip().lower()
        
        guided_str = (
            "<GUIDED_BRIEF>\n"
            "[Deterministic constraints, must obey]\n"
            f"- model_age_range: {model.get('age_range', '25-34')}\n"
            f"- set_mode: {garment.get('set_mode', 'unica')}\n"
            f"- scene_type: {scene.get('type', 'externo')}\n"
            f"- pose_style: {pose_cfg.get('style', 'tradicional')}\n"
            f"- capture_distance: {capture.get('distance', 'media')}\n"
            f"- fidelity_mode: {fidelity_mode}\n"
            "If set_mode is conjunto, map garment-set pieces via repeated color/texture/motif cues from references."
        )
        if guided_set_mode == "conjunto" and has_images:
            guided_str += (
                "\n\n[GUIDED SET DETECTION]\n"
                f"- set_pattern_score: {guided_set_detection.get('set_pattern_score', 0.0)}\n"
                f"- detected_garment_roles: {', '.join(guided_set_detection.get('detected_garment_roles', []) or []) or 'unknown'}\n"
                f"- set_pattern_cues: {', '.join(guided_set_detection.get('set_pattern_cues', []) or []) or 'unknown'}\n"
                f"- set_lock_mode: {guided_set_detection.get('set_lock_mode', 'generic')}"
            )
        guided_str += "\n</GUIDED_BRIEF>"
        blocks.append(guided_str)

    if has_images and structural_contract.get("enabled"):
        cues = ", ".join(structural_contract.get("must_keep", []) or []) or "none"
        sc_str = (
            "<STRUCTURAL_CONTRACT>\n"
            "[Preserve garment geometry from references]\n"
            f"- garment_subtype: {structural_contract.get('garment_subtype', 'unknown')}\n"
            f"- sleeve_type: {structural_contract.get('sleeve_type', 'unknown')}\n"
            f"- sleeve_length: {structural_contract.get('sleeve_length', 'unknown')}\n"
            f"- front_opening: {structural_contract.get('front_opening', 'unknown')}\n"
            f"- hem_shape: {structural_contract.get('hem_shape', 'unknown')}\n"
            f"- garment_length: {structural_contract.get('garment_length', 'unknown')}\n"
            f"- silhouette_volume: {structural_contract.get('silhouette_volume', 'unknown')}\n"
            f"- confidence: {structural_contract.get('confidence', 0.0)}\n"
            f"- must_keep_cues: {cues}\n"
            "Treat these as shape/proportion constraints. Maintain sleeve/hem proportions exactly. "
            "Pay special attention to garment_subtype — it defines the construction method.\n"
            "</STRUCTURAL_CONTRACT>"
        )
        blocks.append(sc_str)

    # Grounding: chamada separada de pesquisa antes do agente
    grounding_research = ""
    grounding_meta = {
        "effective": False,
        "queries": [],
        "sources": [],
        "engine": "none",
        "source_engine": "none",
        "mode": "off",
        "grounded_images_count": 0,
        "visual_ref_engine": "none",
    }
    grounded_images: List[bytes] = []
    grounding_pose_clause: str = ""
    if use_grounding:
        print("[AGENT] 🔍 Running grounding research (separate call)...")
        try:
            grounding_data = _run_grounding_research(
                uploaded_images=uploaded_images or [],
                user_prompt=user_prompt,
                mode=grounding_mode,
                garment_hint_override=_unified_garment_hint,
            )
            grounding_research = grounding_data.get("text", "")
            grounding_pose_clause = grounding_data.get("pose_clause", "")
            grounded_images = list(grounding_data.get("grounded_images", []) or [])
            grounding_meta = {
                "effective": bool(grounding_data.get("effective")),
                "queries": grounding_data.get("queries", []),
                "sources": grounding_data.get("sources", []),
                "engine": grounding_data.get("engine", "none"),
                "source_engine": grounding_data.get("source_engine", grounding_data.get("engine", "none")),
                "mode": grounding_mode,
                "grounded_images_count": int(grounding_data.get("grounded_images_count", 0) or 0),
                "visual_ref_engine": grounding_data.get("visual_ref_engine", "none"),
                "reason_codes": grounding_data.get("reason_codes", []),
            }
        except Exception as e:
            print(f"[AGENT] ⚠️  Grounding research failed: {e}")
            grounding_research = ""
            grounded_images = []

    if grounding_research and grounding_meta.get("effective"):
        blocks.append(
            "<GROUNDING_RESULTS>\n"
            "[Use this to correctly identify the garment]\n"
            f"{grounding_research}\n"
            "</GROUNDING_RESULTS>"
        )
    if grounding_context_hint:
        blocks.append(
            "<TRIAGE_HINT>\n"
            f"Garment hypothesis: {grounding_context_hint}. Keep this silhouette strictly.\n"
            "</TRIAGE_HINT>"
        )

    if grounding_mode == "full" and has_images:
        _sc_attrs = [
            ("front_opening",    "front opening"),
            ("garment_length",   "garment length"),
            ("silhouette_volume","volume"),
            ("hem_shape",        "hem shape"),
            ("sleeve_type",      "sleeve type"),
        ]
        _sc_parts = [
            f"{label}: {structural_contract.get(attr, 'unknown')}"
            for attr, label in _sc_attrs
            if structural_contract.get(attr, "unknown") not in ("unknown", "", None)
        ]
        
        sil_str = "<GROUNDING_CONSTRAINTS>\n"
        if _sc_parts:
            sil_str += "Silhouette constraints (detected from reference images): " + ", ".join(_sc_parts) + ".\n"
            sil_str += "Maintain these geometry attributes in the generated image.\n"
        else:
            sil_str += (
                "Silhouette constraints: maintain the detected garment geometry "
                "(opening behavior, sleeve architecture, hem shape, garment length) "
                "from reference images.\n"
            )
        sil_str += "</GROUNDING_CONSTRAINTS>"
        blocks.append(sil_str)

    blocks.append(REFERENCE_KNOWLEDGE)
    blocks.append("Return ONLY valid JSON matching the schema. No markdown, no explanation.")

    context_text = "\n\n".join(blocks)

    def _build_parts(context: str) -> List[types.Part]:
        parts: List[types.Part] = []
        if has_images:
            for img_bytes in (uploaded_images or []):
                parts.append(
                    types.Part(
                        inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)
                    )
                )
        parts.append(types.Part(text=context))
        return parts

    def _call_prompt_model(context: str, temperature: float) -> Any:
        # Tenta com schema enforced; fallback para mime-only se SDK rejeitar
        try:
            return client.models.generate_content(
                model=MODEL_AGENT,
                contents=[types.Content(role="user", parts=_build_parts(context))],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=temperature,
                    max_output_tokens=8192,
                    safety_settings=SAFETY_CONFIG,
                    response_mime_type="application/json",
                    response_json_schema=AGENT_RESPONSE_SCHEMA,
                ),
            )
        except (TypeError, ValueError) as schema_err:
            # SDK/modelo não suporta response_json_schema → fallback sem schema
            print(f"[AGENT] ⚠️  Schema enforcement failed ({schema_err}), falling back to mime-only")
            return client.models.generate_content(
                model=MODEL_AGENT,
                contents=[types.Content(role="user", parts=_build_parts(context))],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=temperature,
                    max_output_tokens=8192,
                    safety_settings=SAFETY_CONFIG,
                    response_mime_type="application/json",
                ),
            )

    response = _call_prompt_model(context_text, temperature=0.75)

    # ── DECODE: caminho principal (schema) → fallback robusto (_parse_json) ──
    result = None
    # 1) Tenta response.parsed (disponível com schema enforced)
    try:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict) and ("base_prompt" in parsed or "prompt" in parsed):
            result = parsed
            print("[AGENT] ✅ JSON via response.parsed (schema enforced)")
    except Exception:
        pass

    # 2) Fallback: parser robusto existente (lida com respostas malformadas/vazias)
    if result is None:
        try:
            result = _decode_agent_response(response)
            print("[AGENT] ✅ JSON via _decode_agent_response (parser robusto)")
        except Exception as primary_error:
            print(f"[AGENT] ⚠️  JSON parse failed (attempt 1): {primary_error}")
            raw_preview = _extract_response_text(response)[:320].replace("\n", "\\n")
            print(f"[AGENT] ⚠️  Raw preview: {raw_preview}")

            # 3) Retry: mantemos todo_ o contexto estruturado (inclusive XML tags) mas reforçamos o JSON
            retry_context = (
                context_text
                + "\n\n[RETRY TRIGGERED]: The previous response was not valid JSON. You MUST return EXACTLY ONE valid JSON object, without markdown wrappers like ```json"
            )

            response_retry = _call_prompt_model(retry_context, temperature=0.2)
            try:
                result = _decode_agent_response(response_retry)
                print("[AGENT] ✅ JSON parse recovered on retry without grounding context.")
            except Exception as retry_error:
                raw_retry = _extract_response_text(response_retry)[:320].replace("\n", "\\n")
                print(f"[AGENT] ❌ JSON parse failed (attempt 2): {retry_error}")
                print(f"[AGENT] ❌ Retry raw preview: {raw_retry}")
                raise ValueError(f"AGENT_JSON_INVALID: {retry_error}") from retry_error

    # Validações de segurança
    if result.get("thinking_level") not in ["MINIMAL", "HIGH"]:
        result["thinking_level"] = "MINIMAL"

    if result.get("shot_type") not in ["wide", "medium", "close-up", "auto"]:
        result["shot_type"] = "auto"

    guided_distance = str(((guided_brief or {}).get("capture") or {}).get("distance", "")).strip().lower()
    guided_pose_style = str(((guided_brief or {}).get("pose") or {}).get("style", "")).strip().lower()
    guided_pose_creative = guided_enabled and guided_pose_style == "criativa"
    guided_shot = guided_capture_to_shot(guided_distance) if guided_enabled else None
    # guided_shot só substitui o default quando há texto explícito ou pose criativa.
    if guided_shot and (has_prompt or guided_pose_creative):
        result["shot_type"] = guided_shot
    # Permite variabilidade baseada no contexto no lugar de lock "wide"
    elif pipeline_mode == "text_mode" and result.get("shot_type") == "auto":
        result["shot_type"] = _infer_text_mode_shot(user_prompt)

    if result.get("realism_level") not in [1, 2, 3]:
        result["realism_level"] = 2

    base_prompt_raw = str(result.get("base_prompt", "") or "").strip()
    legacy_prompt_raw = str(result.get("prompt", "") or "").strip()
    if not base_prompt_raw:
        base_prompt_raw = legacy_prompt_raw
    if not base_prompt_raw:
        base_prompt_raw = "RAW photo, polished e-commerce catalog composition with garment-first framing."

    camera_realism_raw = str(result.get("camera_and_realism", "") or "").strip()
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(legacy_prompt_raw)
    if not camera_realism_raw:
        camera_realism_raw = _extract_camera_realism_block(base_prompt_raw)
    camera_profile = _select_camera_realism_profile(
        has_images=has_images,
        has_prompt=has_prompt,
        user_prompt=user_prompt,
        base_prompt=base_prompt_raw,
        camera_text=camera_realism_raw,
    )
    camera_realism = _normalize_camera_realism_block(
        camera_realism_raw,
        str(result.get("shot_type", "auto")),
        profile=camera_profile,
    )
    camera_words = _count_words(camera_realism)
    base_budget = max(80, 220 - camera_words)
    if has_images and not has_prompt:
        # 165w acomoda P1 (~40w) + 5 cover clauses (~56w) + model_profile (~14w)
        # + quality_model (~12w) + quality_texture (~9w) + scene/gaze (~20w) = ~151w.
        target_budget = 165
        base_budget = max(80, target_budget - camera_words)

    compiled_base_prompt, compiler_debug = _compile_prompt_v2(
        prompt=base_prompt_raw,
        has_images=has_images,
        has_prompt=has_prompt,
        contract=structural_contract if has_images else None,
        guided_brief=guided_brief if guided_enabled else None,
        guided_enabled=guided_enabled,
        guided_set_detection=guided_set_detection if guided_enabled and guided_set_mode == "conjunto" else None,
        grounding_mode=grounding_mode,
        pipeline_mode=pipeline_mode,
        word_budget=base_budget,
        pose_hint=grounding_pose_clause,
        profile_hint=profile,
        scenario_hint=scenario if (has_images and not has_prompt) else "",
    )
    final_prompt = _compose_prompt_with_camera(compiled_base_prompt, camera_realism)
    result["base_prompt"] = compiled_base_prompt
    result["camera_and_realism"] = camera_realism
    result["camera_profile"] = camera_profile
    result["prompt"] = final_prompt
    compiler_debug["camera_words"] = camera_words
    compiler_debug["base_budget"] = base_budget
    compiler_debug["camera_profile"] = camera_profile
    compiler_debug["final_words"] = _count_words(final_prompt)
    result["prompt_compiler_debug"] = compiler_debug

    result["grounding"] = grounding_meta
    result["pipeline_mode"] = pipeline_mode
    result["model_profile_id"] = diversity_target.get("profile_id") if diversity_target else None
    result["diversity_target"] = diversity_target or {}
    result["guided_summary"] = guided_summary(
        guided_brief if guided_enabled else None,
        result.get("shot_type"),
        set_detection=guided_set_detection if guided_enabled and guided_set_mode == "conjunto" else None,
    )
    result["structural_contract"] = structural_contract
    result["_grounded_images"] = grounded_images

    # ── Log de observabilidade ─────────────────────────────────────
    prompt_text = result.get("prompt", "")
    print(f"\n{'='*60}")
    print(f"[AGENT] Mode: {'MODE 2 (images)' if has_images else 'MODE 1' if has_prompt else 'MODE 3'}")
    print(f"[AGENT] Images sent: {len(uploaded_images) if uploaded_images else 0}")
    print(f"[AGENT] Pool context: {'Yes' if has_pool else 'No'}")
    print(f"[AGENT] Thinking: {result.get('thinking_level')} | Shot: {result.get('shot_type')} | Realism: {result.get('realism_level')}")
    analysis = result.get("image_analysis", "")
    if analysis:
        print(f"[AGENT] 🔍 Image Analysis: {analysis}")
    if guided_enabled and guided_set_mode == "conjunto":
        print(
            "[AGENT] 🧩 Set detection:"
            f" score={guided_set_detection.get('set_pattern_score')}"
            f" roles={guided_set_detection.get('detected_garment_roles')}"
            f" lock={guided_set_detection.get('set_lock_mode')}"
        )
    if has_images and structural_contract.get("enabled"):
        print(
            "[AGENT] 📐 Structural contract:"
            f" subtype={structural_contract.get('garment_subtype')}"
            f" sleeve={structural_contract.get('sleeve_type')}/{structural_contract.get('sleeve_length')}"
            f" hem={structural_contract.get('hem_shape')}"
            f" length={structural_contract.get('garment_length')}"
            f" conf={structural_contract.get('confidence')}"
        )
    print(f"[AGENT] Prompt ({len(prompt_text)} chars): {prompt_text[:300]}{'…' if len(prompt_text) > 300 else ''}")
    print(f"{'='*60}\n")

    return result
