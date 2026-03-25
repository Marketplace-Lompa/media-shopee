"""
Triagem visual — inferência de geometria, hint de peça, detecção de conjunto e triagem unificada.

Extraído de agent.py para manter o orquestrador enxuto.
Todas as funções são chamadas por run_agent() e pelos routers (via import direto).
"""
import re
import json
from io import BytesIO
from typing import Any, Optional, List

from google.genai import types
from PIL import Image, ImageOps

# Limite conservador para imagens enviadas ao triage — evita timeout httpx com refs pesadas
_TRIAGE_LONG_EDGE = 1024
_TRIAGE_MAX_BYTES = 800_000


def _compress_for_triage(image_bytes: bytes) -> bytes:
    """Redimensiona e comprime imagem para envio ao triage. Evita timeout com refs ~4MB."""
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in {"RGB", "L"}:
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if "A" in img.getbands():
                    bg.paste(img, mask=img.getchannel("A"))
                else:
                    bg.paste(img.convert("RGB"))
                img = bg
            else:
                img = img.convert("RGB")
            w, h = img.size
            if max(w, h) > _TRIAGE_LONG_EDGE:
                scale = _TRIAGE_LONG_EDGE / float(max(w, h))
                img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
            for quality in (85, 78, 70):
                out = BytesIO()
                img.save(out, format="JPEG", quality=quality, optimize=True)
                data = out.getvalue()
                if len(data) <= _TRIAGE_MAX_BYTES:
                    return data
            return data
    except Exception:
        return image_bytes

from agent_runtime.gemini_client import (
    generate_structured_json,
    generate_multimodal,
)
from agent_runtime.parser import (
    _extract_response_text,
    _decode_agent_response,
    try_repair_truncated_json,
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

_VALID_LIGHTING_SOURCE_STYLE = {
    "flat_catalog",
    "soft_catalog",
    "natural_diffused",
    "directional_natural",
    "mixed_interior",
}
_VALID_LIGHTING_HARDNESS = {"soft", "medium", "hard"}
_VALID_LIGHTING_DIRECTION = {"frontal", "side", "top", "mixed"}
_VALID_LIGHTING_CONTRAST = {"low", "medium", "high"}
_VALID_LIGHTING_RISK = {"low", "medium", "high"}


def _normalize_lighting_signature(payload: Optional[dict]) -> dict:
    raw = payload if isinstance(payload, dict) else {}
    source_style = str(raw.get("source_style", "") or "").strip().lower()
    light_hardness = str(raw.get("light_hardness", "") or "").strip().lower()
    light_direction = str(raw.get("light_direction", "") or "").strip().lower()
    contrast_level = str(raw.get("contrast_level", "") or "").strip().lower()
    integration_risk = str(raw.get("integration_risk", "") or "").strip().lower()
    return {
        "source_style": source_style if source_style in _VALID_LIGHTING_SOURCE_STYLE else "soft_catalog",
        "light_hardness": light_hardness if light_hardness in _VALID_LIGHTING_HARDNESS else "soft",
        "light_direction": light_direction if light_direction in _VALID_LIGHTING_DIRECTION else "mixed",
        "contrast_level": contrast_level if contrast_level in _VALID_LIGHTING_CONTRAST else "medium",
        "integration_risk": integration_risk if integration_risk in _VALID_LIGHTING_RISK else "medium",
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


def resolve_prompt_agent_visual_triage(
    *,
    uploaded_images: List[bytes],
    user_prompt: Optional[str],
    guided_enabled: bool,
    guided_set_mode: str,
    structural_contract_hint: Optional[dict] = None,
    unified_vision_triage_result: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Resolve a triagem visual consumida pelo Prompt Agent.

    Mantém a lógica atual em um ponto único, sem deixar run_agent() decidir
    entre contrato externo, triagem unificada ou fallback manual.
    """
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
    garment_hint = ""
    image_analysis = ""
    look_contract: dict[str, Any] = {}

    if uploaded_images:
        unified: Optional[dict[str, Any]] = None
        has_external_contract = isinstance(structural_contract_hint, dict) and bool(structural_contract_hint)

        if has_external_contract:
            structural_contract = structural_contract_hint or {}
            garment_hint = _infer_garment_hint(uploaded_images)
            print("[AGENT] unified_vision_triage: skipped (external structural_contract_hint provided)")
        elif isinstance(unified_vision_triage_result, dict) and unified_vision_triage_result:
            unified = unified_vision_triage_result
            print("[AGENT] unified_vision_triage: using pre-computed result")
        else:
            unified = _infer_unified_vision_triage(uploaded_images, user_prompt)

        if unified:
            structural_contract = unified["structural_contract"]
            garment_hint = unified["garment_hint"]
            image_analysis = unified.get("image_analysis", "")
            look_contract = unified.get("look_contract", {})
            set_detection = unified["set_detection"]
            if guided_enabled and guided_set_mode == "conjunto":
                if set_detection.get("set_lock_mode") == "off":
                    set_detection["set_lock_mode"] = "generic"
                guided_set_detection = set_detection
        elif not has_external_contract:
            print("[AGENT] unified_vision_triage: fallback")
            structural_contract = _infer_structural_contract_from_images(uploaded_images, user_prompt)
            if guided_enabled and guided_set_mode == "conjunto":
                guided_set_detection = _infer_set_pattern_from_images(uploaded_images, user_prompt)
                if guided_set_detection.get("set_lock_mode") == "off":
                    guided_set_detection["set_lock_mode"] = "generic"
            garment_hint = _infer_garment_hint(uploaded_images)
    elif guided_enabled and guided_set_mode == "conjunto":
        guided_set_detection = _infer_set_pattern_from_images([], user_prompt)

    return {
        "structural_contract": structural_contract,
        "guided_set_detection": guided_set_detection,
        "garment_hint": garment_hint,
        "image_analysis": image_analysis,
        "look_contract": look_contract,
    }


# ── Garment hint (curto, para montar queries de grounding) ───────────────────

def _infer_garment_hint(uploaded_images: List[bytes]) -> str:
    """Classificação curta da peça para montar queries de grounding quando não há prompt."""
    try:
        parts = []
        for img_bytes in uploaded_images:
            parts.append(
                types.Part(
                    inline_data=types.Blob(mime_type="image/jpeg", data=_compress_for_triage(img_bytes))
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
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=_compress_for_triage(img_bytes))))

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
        repaired = try_repair_truncated_json(err_msg)
        if repaired is not None:
            print(f"[AGENT] 🔧 Structural contract repaired from truncated JSON")
            return _normalize_structural_contract(repaired)
        return _empty

    # Reutiliza a mesma normalizer da triagem unificada — single source of truth
    # para validação de campos, has_pockets, confidence, enabled, etc.
    return _normalize_structural_contract(parsed)


# ── Set pattern detection (conjunto coordenado) ─────────────────────────────

def _infer_set_pattern_from_images(uploaded_images: List[bytes], user_prompt: Optional[str]) -> dict:
    """
    Detecta se a referência sugere conjunto coordenado por DNA têxtil/padrão visual.
    Diferencia peça coordenada real de roupa de baixo e acessório irrelevante.
    """
    if not uploaded_images:
        return _normalize_set_detection({})

    parts: List[types.Part] = []
    for img_bytes in uploaded_images:
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=_compress_for_triage(img_bytes))))

    user_txt = (user_prompt or "").strip()
    text_instruction = (
        "Analyze whether these references contain a coordinated fashion set based on repeated textile DNA: "
        "same yarn/fabric family, same stitch texture, same motif logic, same stripe order, same finishing, "
        "and repetition across multiple references. "
        "Important: a matching scarf or shawl DOES count as part of the set if it clearly shares the same textile DNA "
        "as the hero garment. Inner tops, basic layering pieces, jewelry, belts, bags, shoes, and unrelated accessories "
        "must be marked for exclusion unless they repeat the same textile DNA and are consistently shown as part of the product. "
        "Return strict JSON with: "
        "is_garment_set, set_pattern_score, set_mode (off|probable|explicit), primary_piece_role, detected_garment_roles, "
        "set_pattern_cues, and set_members. "
        "Each set_members item must include role, member_class (garment|coordinated_accessory|styling_layer|unrelated_accessory), "
        "include_policy (must_include|optional|exclude), render_separately, fusion_forbidden, confidence. "
        "Use descriptive multi-word role labels such as 'striped knit scarf' or 'textured pullover'."
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
        return _normalize_set_detection(parsed if isinstance(parsed, dict) else {})
    except Exception as e:
        err_msg = str(e)
        print(f"[GUIDED] ⚠️ set-pattern inference failed: {err_msg}")
        repaired = try_repair_truncated_json(err_msg)
        if repaired is not None:
            return _normalize_set_detection(repaired)
        return _normalize_set_detection({})


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
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=_compress_for_triage(img_bytes))))

    user_txt = (user_prompt or "").strip()
    instruction = (
        "Analyze these garment reference images and return strict JSON with ALL five fields.\n\n"
        "1. garment_hint: identify the garment type and silhouette in 8 words max "
        "(e.g. ruana, poncho aberto, batwing cardigan, dolman sleeve). Plain text.\n\n"
        "2. image_analysis: 2-3 sentences describing the GARMENT visible in the reference. "
        "Include: (a) dominant colors with specific names, (b) EXACT surface pattern geometry — "
        "if the garment has stripes, describe direction as it exists in the CONSTRUCTION (not just how it appears when draped): "
        "e.g. 'diagonal chevron stripes radiating outward from center panel', 'concentric oval stripes', "
        "'straight horizontal stripes', 'vertical stripes', 'argyle', 'solid' — be precise about direction and geometry, "
        "(c) textile construction type (crochet/knit/woven/printed), texture weight and stitch relief, "
        "(d) overall aesthetic mood and styling context. "
        "Focus on visual qualities that directly inform pattern fidelity and casting decisions. "
        "Do NOT describe the person — focus 100% on the clothing.\n\n"
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
        "edge_contour: clean|soft_curve|undulating|scalloped|angular, based only on the MACRO outer silhouette line. "
        "Do not call it undulating or scalloped just because of crochet stitch texture, ribbing, or tiny handmade ripples if the overall outline still reads smooth. "
        "drop_profile: even|side_drop|high_low|cocoon_side_drop, based on where the longest visible fall sits. "
        "opening_continuity: continuous|broken|lapel_like, based on whether the neckline/opening reads as one uninterrupted edge. "
        "must_keep: up to 4 brief GEOMETRY cues only, such as continuous neckline-to-front edge, broad uninterrupted back panel, rounded cocoon side drop, or arm coverage formed by the same draped panel. "
        "Do not use border-texture cues like scalloped crochet trim unless they visibly change the garment outline at silhouette scale. "
        "Do NOT use generic cues like 'open front', 'knit texture', or simple stripe mentions unless they are structurally critical. "
        "confidence: 0.0-1.0. "
        "has_pockets: boolean — true if ANY pocket (patch, welt, side-seam) is clearly visible "
        "on the garment; false if the garment has NO visible pockets whatsoever.\n\n"
        "4. set_detection: do these references show a COORDINATED SET with repeated textile DNA across separate product members? "
        "A matching scarf or shawl counts only if it clearly shares the same yarn/stitch/pattern DNA as the main garment and is shown consistently. "
        "Inner tops, basic layers, jewelry, bags, belts, hats, and shoes should be excluded unless they repeat that same textile DNA. "
        "Return: is_garment_set (bool), set_pattern_score (0.0-1.0), set_mode (off|probable|explicit), primary_piece_role, "
        "detected_garment_roles, set_pattern_cues, and set_members. "
        "Each set_members item must include role, member_class (garment|coordinated_accessory|styling_layer|unrelated_accessory), "
        "include_policy (must_include|optional|exclude), render_separately, fusion_forbidden, confidence.\n\n"
        "5. garment_aesthetic: casting/scenario intelligence for the garment. "
        "color_temperature: warm|cool|neutral (dominant color feel). "
        "formality: casual|smart_casual|formal. "
        "season: summer|mid_season|winter (most natural occasion). "
        "vibe: boho_artisanal|urban_chic|romantic|bold_edgy|minimalist|beachwear_resort|sport_casual.\n\n"
        "6. lighting_signature: infer the lighting behavior seen on the garment references so the next stage can choose a compatible scene. "
        "source_style: flat_catalog|soft_catalog|natural_diffused|directional_natural|mixed_interior. "
        "light_hardness: soft|medium|hard. "
        "light_direction: frontal|side|top|mixed. "
        "contrast_level: low|medium|high. "
        "integration_risk: low|medium|high, where high means the garment lighting would look pasted into many unrelated scenes unless the camera/lighting choice is carefully controlled.\n\n"
        "7. look_contract: fashion styling constraints to ensure the generated outfit is coherent with THIS garment. "
        "Analyze the garment's weight, structure, texture, formality, and seasonality. Then determine:\n"
        "- bottom_style: the most cohesive type of bottom garment (e.g. 'calça de alfaiataria', 'jeans wide-leg', 'saia lápis', 'calça de couro', 'bermuda estruturada'). "
        "Choose based on visual weight balance: heavy/structured top → slim/structured bottom. Flowy top → volume is ok.\n"
        "- bottom_color: 1-3 best-fitting colors (e.g. 'preto, cinza antracite, caramelo')\n"
        "- color_family: palette logic (e.g. 'neutros escuros com acento quente', 'monocromático', 'contraste suave')\n"
        "- season: outono-inverno|primavera-verao|transicional\n"
        "- occasion: casual-urbano|work-casual|elegante|esportivo|praia\n"
        "- forbidden_bottoms: list 3-5 SPECIFIC bottom types that would look INCOHERENT with this garment "
        "(e.g. 'saia plissada chiffon', 'shorts esportivo', 'calça esportiva', 'saia evasê floral'). Be specific, not generic.\n"
        "- accessories: concise suggestion (e.g. 'cinto fino caramelo, bota cano curto, brincos simples')\n"
        "- style_keywords: 3-4 words describing the garment's style DNA (e.g. ['estruturado', 'urbano', 'outono'])\n"
        "- confidence: 0.0-1.0"
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
        lighting_signature = _normalize_lighting_signature(parsed.get("lighting_signature"))

        # look_contract: normalizar com fallback seguro
        _raw_lc = parsed.get("look_contract") or {}
        if not isinstance(_raw_lc, dict):
            _raw_lc = {}
        look_contract = {
            "bottom_style":      str(_raw_lc.get("bottom_style") or "").strip()[:120],
            "bottom_color":      str(_raw_lc.get("bottom_color") or "").strip()[:80],
            "color_family":      str(_raw_lc.get("color_family") or "").strip()[:80],
            "season":            str(_raw_lc.get("season") or "transicional").strip()[:40],
            "occasion":          str(_raw_lc.get("occasion") or "casual-urbano").strip()[:60],
            "forbidden_bottoms": [
                str(x).strip() for x in (_raw_lc.get("forbidden_bottoms") or [])
                if isinstance(x, str) and x.strip()
            ][:6],
            "accessories":       str(_raw_lc.get("accessories") or "").strip()[:150],
            "style_keywords":    [
                str(x).strip() for x in (_raw_lc.get("style_keywords") or [])
                if isinstance(x, str) and x.strip()
            ][:5],
            "confidence":        float(_raw_lc.get("confidence") or 0.0),
        }

        result = {
            "garment_hint":        garment_hint,
            "image_analysis":      image_analysis,
            "structural_contract": _normalize_structural_contract(parsed.get("structural_contract") or {}),
            "set_detection":       _normalize_set_detection(parsed.get("set_detection") or {}),
            "garment_aesthetic":   garment_aesthetic,
            "lighting_signature":  lighting_signature,
            "look_contract":       look_contract,
        }
        print(
            f"[AGENT] ✅ unified_vision_triage: success "
            f"(hint='{garment_hint[:60]}' aesthetic={garment_aesthetic} lighting={lighting_signature})"
        )
        if look_contract.get("confidence", 0) > 0.5:
            print(
                f"[STYLE] 👗 look_contract: bottom={look_contract['bottom_style']!r} "
                f"forbidden={look_contract['forbidden_bottoms']} "
                f"conf={look_contract['confidence']:.2f}"
            )
        return result
    except Exception as e:
        print(f"[AGENT] ⚠️  unified_vision_triage: failed ({e}), using fallback")
        return None
