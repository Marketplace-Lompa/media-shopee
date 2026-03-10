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

client = genai.Client(api_key=GOOGLE_AI_API_KEY)

# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# AGENT RESPONSE SCHEMA — enforced pela API do Gemini
# ═══════════════════════════════════════════════════════════════════════════════
AGENT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["prompt", "thinking_level", "shot_type", "realism_level"],
    "properties": {
        "prompt": {
            "type": "string",
            "description": "Optimized English prompt, max 200 words, narrative paragraph. Always start with 'RAW photo,'"
        },
        "thinking_level": {
            "type": "string",
            "enum": ["MINIMAL", "HIGH"]
        },
        "thinking_reason": {
            "type": "string",
            "description": "One sentence in Portuguese explaining the thinking level choice"
        },
        "shot_type": {
            "type": "string",
            "enum": ["wide", "medium", "close-up", "auto"]
        },
        "realism_level": {
            "type": "integer",
            "enum": [1, 2, 3]
        },
        "image_analysis": {
            "type": "string",
            "description": "HIGH-LEVEL garment analysis in Portuguese: category, color, material, silhouette. Required when reference images are present."
        }
    }
}

SET_DETECTION_SCHEMA = {
    "type": "object",
    "required": ["is_garment_set", "set_pattern_score", "detected_garment_roles", "set_pattern_cues"],
    "properties": {
        "is_garment_set": {"type": "boolean"},
        "set_pattern_score": {"type": "number"},
        "detected_garment_roles": {
            "type": "array",
            "items": {"type": "string", "enum": ["top", "bottom", "outerwear", "one_piece", "layer"]},
        },
        "set_pattern_cues": {"type": "array", "items": {"type": "string"}},
    },
}

STRUCTURAL_CONTRACT_SCHEMA = {
    "type": "object",
    "required": [
        "garment_subtype",
        "sleeve_type",
        "sleeve_length",
        "front_opening",
        "hem_shape",
        "garment_length",
        "silhouette_volume",
        "must_keep",
        "confidence",
    ],
    "properties": {
        "garment_subtype": {"type": "string"},
        "sleeve_type": {"type": "string"},
        "sleeve_length": {"type": "string"},
        "front_opening": {"type": "string"},
        "hem_shape": {"type": "string"},
        "garment_length": {"type": "string"},
        "silhouette_volume": {"type": "string"},
        "must_keep": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM INSTRUCTION — concisa, comportamental (regras + modos)
# ═══════════════════════════════════════════════════════════════════════════════
SYSTEM_INSTRUCTION = """
You are an expert prompt engineer for Nano Banana 2 (gemini-3.1-flash-image-preview).
You specialize in Brazilian e-commerce fashion catalog photography.
Your output MUST match the provided JSON schema exactly.

CORE RULES:
1. Always write prompts in English, narrative paragraph, max 200 words.
2. Always start the prompt with "RAW photo," to trigger photorealism.
3. Structure: shot_type framing → model description → garment (3D) → pose → scenario → camera → realism levers.
4. NEVER use quality tags: 8K, ultra HD, masterpiece, best quality.
5. Garment is ALWAYS the visual protagonist.

OPERATING MODES:

MODE 1 — User gave a text prompt:
  Enhance and expand using the REFERENCE KNOWLEDGE provided.
  Do NOT use Fidelity Lock unless reference images are also present.

MODE 2 — User sent reference images (with or without text):
  STEP 1: Analyze images. Fill "image_analysis" with HIGH-LEVEL observations IN PORTUGUESE:
    category, color(s), material family, silhouette/fit.
    DO NOT describe texture patterns, stitches, prints — these CONFUSE the model.
  STEP 2: Start prompt with Fidelity Lock verbatim:
    "REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. KEEP ONLY THE GARMENT from the reference photo — reproduce its exact texture, stitch pattern, color, and construction. REPLACE EVERYTHING ELSE: use a completely different human model (different ethnicity, body type, hair, age), a completely new pose, and a completely different background and scenario. Do NOT replicate the model, pose, or environment from the reference."
  ANTI-CLONING: NEVER reuse person, background, or pose from reference. Always contrast.
  After lock: add MAX 2 reinforcement sentences on fiber/material type and construction — NOT visual patterns.
  NEVER describe in text: stripes, prints, zigzag, diamond, lace pattern, crochet loops.

MODE 3 — No prompt or images:
  Generate a creative catalog prompt using pool context and REFERENCE KNOWLEDGE.

THINKING LEVEL:
  HIGH: complex knitwear, crochet, multi-layer, macro texture, 3+ people, sequins/metallic.
  MINIMAL: solid fabrics, simple garments, clean lifestyle shots.

Consult the [REFERENCE KNOWLEDGE] block in user content for garment vocabulary, model profiles,
scenarios, realism levers, and shot type templates.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE KNOWLEDGE — injetada no conteúdo do usuário, NÃO na system instruction
# ═══════════════════════════════════════════════════════════════════════════════
REFERENCE_KNOWLEDGE = """
[REFERENCE KNOWLEDGE — consult when building prompt]

── GARMENT DESCRIPTION (3 dimensions) ──

DIMENSION 1 — MATERIAL:
  Woven: cotton poplin, linen, silk charmeuse, wool crepe, tweed, jacquard, brocade
  Knit: smooth fine-gauge jersey knit | vertical rib-knit | chunky Aran cable-knit |
        plush brioche stitch | open-stitch knit panel (NOT "lace knit" → generates floral lace)
  Synthetic: mesh, tulle, velvet, vinyl/PU leather, suede, sequined

  ANTI-INFLATION for knitwear:
    Crochet — DO: "flat uniform crochet construction", "open-weave crochet airy construction"
              DON'T: "crochet loops", "3D crochet texture", "puffy", "bobbles"
    Knit — DO: "heavy flat-knit construction dense gauge", "smooth fine-gauge jersey knit"
           DON'T: "cable" unless truly Aran
    Texture tokens: subtle="nearly smooth" | medium="visible rows" | maximum="deep relief"

DIMENSION 2 — CONSTRUCTION:
  Necklines: crew | V-neck | scoop | boat | square | turtleneck | cowl
  Sleeves: set-in | raglan | dolman/batwing | puff | bishop | bell | cap | flutter

DIMENSION 3 — BEHAVIOR:
  drapes loosely | falls straight | holds structure | clings to body |
  billows/catches air | skims the body | stands away from body

── E-COMMERCE SHOT SYSTEM ──

WIDE (hero): Full body head-to-feet, 60-70% frame. Dynamic mid-stride.
  Template: "Full-body wide shot, model mid-stride in [scenario], 3/4 angle."
MEDIUM (detail): Waist-up, neckline + sleeve focus, 50mm bokeh.
  Template: "Medium shot waist up, relaxed expression, soft bokeh."
CLOSE-UP (texture): 80%+ frame is detail, macro focus.
  Template: "Extreme close-up of [detail], macro focus, individual fiber visible."
AUTO: choose what best showcases the garment.

── BRAZILIAN MODEL FRAMEWORK ──

PHENOTYPE POOL (rotate, never repeat):
  A) Sulista europeia: fair skin, pink undertones, light brown hair, green/blue eyes, slim
  B) Parda paulistana: warm olive skin, wavy dark hair, brown eyes, curvy
  C) Afro-brasileira: deep brown skin, natural curly hair, brown eyes, athletic
  D) Nordestina mestiça: golden tan, thick dark waves, hazel eyes, tall lean
  E) Gaúcha italiana: fair olive skin, long dark hair, hazel-green eyes, curvy

Age: early 20s | late 20s | mid 30s | early 40s
Body: athletic | curvy | slim | plus-size | petite | tall and lean

MODEL PRESENTATION (always apply):
  Hair: professionally styled | Skin: healthy, glowing | Expression: warm, confident
  Gaze: engaging eye contact | Posture: poised, shoulders relaxed

SEASONAL COHERENCE:
  Winter knits → boots, dark jeans, muted light | Mid-season → closed shoes, golden hour
  Summer → bare legs, sandals, bright midday

SCENARIOS (rotate):
  Urban: modern downtown | rooftop terrace | shopping district | garden terrace
  Natural: tropical park | café garden | botanical path | mountain town
  Interior: minimalist apartment | cozy café | boutique showroom | warm living room

COLOR STRATEGY: White→dark bg | Black→light bg | Pastels→neutral warm | Saturated→clean minimal

── REALISM LEVERS ──

Level 1 (casual): 5-7 levers, high intensity
Level 2 (e-commerce, DEFAULT): 3-4 levers, moderate
Level 3 (editorial): 2-3 levers, subtle

Anti-perfection: NEVER "perfect lighting", "flawless skin", "8K masterpiece"

Levers: DEVICE="Sony A7III, 85mm f/1.8" | LIGHTING="golden hour rim light" |
  SKIN="visible pores, natural tone variation" | GRAIN="natural digital noise" |
  FABRIC="natural wear creases, fabric responding to movement"

── GROUNDING RESEARCH ──

Garments requiring research: manga morcego/dolman, cardigan assimétrico,
kaftan, ruana/xale, pelerine, bodychain/harness, any unidentifiable garment.
"""


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


_last_profile_idx: int = -1
_last_scenario_idx: int = -1
_last_pose_idx: int = -1


def _sample_diversity_target() -> tuple[str, str, str]:
    global _last_profile_idx, _last_scenario_idx, _last_pose_idx

    profiles = [
        "Afro-Brazilian woman in her late 20s, deep brown skin, styled natural curls, athletic build, warm confident smile and engaging eye contact",
        "Mixed-race São Paulo woman in her mid 20s, warm olive skin, sleek wavy dark hair, curvy figure, soft inviting expression looking at camera",
        "Southern Brazilian woman in her late 20s, fair skin with pink undertones, styled light brown hair, slim frame, bright confident expression",
        "Northeastern mixed-heritage woman in her mid 20s, golden tanned skin, thick dark waves pulled back, tall and lean, radiant smile toward camera",
        "Italian-descent Southern Brazilian woman in her early 30s, fair olive skin, long dark hair well-groomed, curvy figure, poised and warm gaze",
    ]
    scenarios = [
        "bright modern downtown with clean architecture and soft natural light",
        "cozy upscale café terrace with warm ambient lighting",
        "bright minimalist apartment with large windows and soft daylight",
        "charming shopping district at golden hour with boutique storefronts",
        "rooftop garden terrace with city skyline in late afternoon",
        "botanical garden pathway with lush tropical greenery and dappled light",
        "warm living room with neutral decor and soft window light",
    ]
    poses = [
        "mid-stride with relaxed arms, looking at camera with confident smile",
        "3/4 stance with one shoulder slightly forward, warm engaging gaze",
        "natural standing posture with one hand on hip, inviting expression",
        "walking pose with subtle torso twist, playful smile toward camera",
        "leaning lightly against wall, relaxed and approachable, eye contact with camera",
    ]

    # Anti-repeat rotation: pick different index each time
    p_choices = [i for i in range(len(profiles)) if i != _last_profile_idx]
    s_choices = [i for i in range(len(scenarios)) if i != _last_scenario_idx]
    po_choices = [i for i in range(len(poses)) if i != _last_pose_idx]

    _last_profile_idx = random.choice(p_choices)
    _last_scenario_idx = random.choice(s_choices)
    _last_pose_idx = random.choice(po_choices)

    return profiles[_last_profile_idx], scenarios[_last_scenario_idx], poses[_last_pose_idx]


def _apply_quality_locks(
    prompt: str,
    has_images: bool,
    grounding_mode: str,
    pipeline_mode: str,
) -> str:
    """Aplica locks de qualidade visual no prompt final para catálogo."""
    if not prompt:
        return prompt

    locks: List[str] = []
    if has_images:
        locks.extend([
            "E-COMMERCE QUALITY LOCK: use a polished, commercially attractive Brazilian woman with neat hair, subtle professional makeup, clean styling, confident posture, and natural pleasant expression.",
            "GAZE LOCK: prefer direct or near-camera gaze; avoid distracted gaze into empty space unless explicitly requested.",
            "SCENE LOCK: use a clean, bright, minimally cluttered catalog-friendly environment; avoid gritty loft mood and busy background elements.",
            "TEXTURE LOCK: preserve exact yarn/stitch density, stripe spacing, edge definition, and tactile depth from reference garment; do not smooth or reinterpret knit/crochet texture.",
        ])
    elif pipeline_mode == "text_mode":
        locks.extend([
            "E-COMMERCE POLISH DEFAULT: model must look polished and commercially attractive with neat hair, subtle makeup, clean styling, and confident posture.",
            "GAZE DEFAULT: prefer direct or near-camera eye contact unless the user explicitly requests candid/off-camera behavior.",
            "SCENE DEFAULT: use a clean, bright, coherent catalog-friendly environment with minimal clutter.",
        ])
    if grounding_mode == "full":
        locks.append(
            "ATYPICAL SILHOUETTE LOCK: keep front fully open, preserve batwing/dolman volume, keep rounded cocoon hem, and keep scarf as a separate coordinated piece."
        )

    merged = prompt.strip()
    for lock in locks:
        if lock[:36] not in merged:
            merged += f" {lock}"

    # Evita prompts exageradamente longos
    if len(merged) > 2200:
        merged = merged[:2200].rstrip() + "..."
    return merged


def _apply_guided_locks(
    prompt: str,
    guided_brief: Optional[dict],
    has_images: bool,
    set_detection: Optional[dict] = None,
) -> str:
    if not prompt or not guided_brief:
        return prompt

    garment = guided_brief.get("garment", {}) or {}
    scene = guided_brief.get("scene", {}) or {}
    pose = guided_brief.get("pose", {}) or {}
    capture = guided_brief.get("capture", {}) or {}
    fidelity_mode = str(guided_brief.get("fidelity_mode", "balanceada")).strip().lower()

    set_mode = str(garment.get("set_mode", "unica")).strip().lower()
    scene_type = str(scene.get("type", "")).strip().lower()
    pose_style = str(pose.get("style", "")).strip().lower()
    capture_distance = str(capture.get("distance", "")).strip().lower()
    set_detection = set_detection or {}
    set_lock_mode = str(set_detection.get("set_lock_mode", "off") or "off")
    detected_roles = list(set_detection.get("detected_garment_roles", []) or [])

    locks: List[str] = []
    if set_mode == "conjunto":
        locks.append(
            "GUIDED SET LOCK: treat this as a coordinated garment set inferred from repeated color/texture/pattern cues in the reference."
        )
        locks.append(
            "GUIDED SET LOCK: infer set pieces using garment-only evidence; ignore accessories as set-defining elements."
        )
        if set_lock_mode == "explicit" and len(detected_roles) >= 2:
            locks.append(
                f"GUIDED SET LOCK (explicit): preserve coordinated garment roles: {', '.join(detected_roles[:4])}."
            )
        else:
            locks.append(
                "GUIDED SET LOCK (generic): preserve all coordinated garment pieces visible in references even when role naming is uncertain."
            )

    if scene_type == "interno":
        locks.append("GUIDED SCENE LOCK: use an indoor environment only.")
    elif scene_type == "externo":
        locks.append("GUIDED SCENE LOCK: use an outdoor environment only.")

    if pose_style == "tradicional":
        locks.append("GUIDED POSE LOCK: use a traditional catalog pose with stable stance and clear garment visibility.")
    elif pose_style == "criativa":
        locks.append("GUIDED POSE LOCK: use a creative pose while keeping full garment readability for e-commerce.")

    shot = guided_capture_to_shot(capture_distance)
    if shot == "wide":
        locks.append("GUIDED CAPTURE LOCK: framing must be wide/full-body.")
    elif shot == "medium":
        locks.append("GUIDED CAPTURE LOCK: framing must be medium/waist-up.")
    elif shot == "close-up":
        locks.append("GUIDED CAPTURE LOCK: framing must be close-up/detail-focused.")

    if has_images and (set_mode == "conjunto" or fidelity_mode == "estrita"):
        locks.append("GUIDED NEGATIVE LOCK: no extra pockets not present in references.")
        locks.append("GUIDED NEGATIVE LOCK: no front closure if reference garment is open-front.")
        locks.append("GUIDED NEGATIVE LOCK: do not reinterpret texture/stitch when references are present.")

    merged = prompt.strip()
    for lock in locks:
        if lock[:28] not in merged:
            merged += f" {lock}"
    if len(merged) > 2400:
        merged = merged[:2400].rstrip() + "..."
    return merged


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
    for img_bytes in uploaded_images[:8]:
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)))

    user_txt = (user_prompt or "").strip()
    instruction = (
        "Analyze garment geometry from these references and return strict JSON only. "
        "FIRST identify the garment_subtype. Use one of: "
        "standard_cardigan, ruana_wrap, poncho, cape, kimono, bolero, vest, jacket, pullover, dress, other. "
        "CLASSIFICATION RULE: if the garment has NO separate sewn-in sleeves and the arms are covered "
        "by a continuous draped fabric panel, it is ruana_wrap or poncho — NOT standard_cardigan. "
        "standard_cardigan requires separately constructed and sewn sleeve tubes. "
        "Then analyze: sleeve_type (set-in, raglan, dolman_batwing, drop_shoulder, cape_like), "
        "sleeve_length (sleeveless, cap, short, elbow, three_quarter, long), "
        "front_opening (open, partial, closed), hem_shape (straight, rounded, asymmetric, cocoon), "
        "garment_length (cropped, waist, hip, upper_thigh, mid_thigh, knee_plus), "
        "silhouette_volume (fitted, regular, oversized, draped, structured), "
        "must_keep (brief visual cues list), confidence (0.0-1.0). "
        "Do NOT focus on fabric pattern names or decorative details."
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


# ── Descrições construtivas explícitas por subtipo (para o Nano entender) ──
_SUBTYPE_CONSTRUCTION_LOCKS: dict[str, str] = {
    "ruana_wrap": (
        "CONSTRUCTION LOCK: this garment is a RUANA/WRAP — a single continuous rectangular fabric panel "
        "draped over the shoulders with NO separate sewn sleeves. The arm coverage comes from the "
        "width of the panel falling over the arms, creating a batwing/dolman effect. "
        "Do NOT add set-in sleeves, fitted sleeves, or any separate sleeve construction. "
        "The silhouette must show fabric draping freely from shoulder to hem as one piece."
    ),
    "poncho": (
        "CONSTRUCTION LOCK: this garment is a PONCHO — a single piece of fabric with a head opening, "
        "NO separate sleeves. The fabric falls equally on all sides from shoulders. "
        "Do NOT add sleeves of any kind."
    ),
    "cape": (
        "CONSTRUCTION LOCK: this garment is a CAPE — an open-front draped outerwear piece "
        "with NO separate sleeves. Fabric falls from shoulders in a flowing panel."
    ),
    "kimono": (
        "CONSTRUCTION LOCK: this garment is a KIMONO-style wrap — wide, straight-cut body and sleeves "
        "cut as one T-shaped piece. Sleeves are extremely wide rectangular panels, "
        "NOT fitted or tapered. Preserve the boxy, angular construction."
    ),
}


def _apply_structural_locks(prompt: str, has_images: bool, contract: Optional[dict]) -> str:
    if not prompt or not has_images or not contract or not contract.get("enabled"):
        return prompt

    sleeve_type_labels = {
        "set-in": "set-in sleeve",
        "raglan": "raglan sleeve",
        "dolman_batwing": "dolman/batwing sleeve architecture",
        "drop_shoulder": "drop-shoulder sleeve architecture",
        "cape_like": "cape-like sleeve fall",
    }
    sleeve_len_labels = {
        "sleeveless": "sleeveless",
        "cap": "cap sleeve",
        "short": "short sleeve",
        "elbow": "elbow-length sleeve",
        "three_quarter": "three-quarter sleeve",
        "long": "long sleeve",
    }
    hem_labels = {
        "straight": "straight hemline",
        "rounded": "rounded hemline",
        "asymmetric": "asymmetric hemline",
        "cocoon": "cocoon hemline",
    }
    length_labels = {
        "cropped": "cropped body length",
        "waist": "waist-length body",
        "hip": "hip-length body",
        "upper_thigh": "upper-thigh body length",
        "mid_thigh": "mid-thigh body length",
        "knee_plus": "knee-or-below body length",
    }
    volume_labels = {
        "fitted": "fitted body volume",
        "regular": "regular body volume",
        "oversized": "oversized body volume",
        "draped": "draped fluid volume",
        "structured": "structured body volume",
    }

    confidence = float(contract.get("confidence", 0.0) or 0.0)
    garment_subtype = str(contract.get("garment_subtype", "unknown"))
    sleeve_type = str(contract.get("sleeve_type", "unknown"))
    sleeve_length = str(contract.get("sleeve_length", "unknown"))
    front_opening = str(contract.get("front_opening", "unknown"))
    hem_shape = str(contract.get("hem_shape", "unknown"))
    garment_length = str(contract.get("garment_length", "unknown"))
    silhouette_volume = str(contract.get("silhouette_volume", "unknown"))
    must_keep = list(contract.get("must_keep", []) or [])

    locks: List[str] = []

    # ── Subtipo construtivo: lock mais importante ──
    if garment_subtype in _SUBTYPE_CONSTRUCTION_LOCKS:
        locks.append(_SUBTYPE_CONSTRUCTION_LOCKS[garment_subtype])
    elif garment_subtype not in ("unknown", "other"):
        locks.append(f"CONSTRUCTION LOCK: this garment is a {garment_subtype.replace('_', ' ')}; preserve its specific construction.")

    if front_opening == "open":
        locks.append("STRUCTURE LOCK: preserve open-front construction; do not close the front panel.")
    elif front_opening == "closed":
        locks.append("STRUCTURE LOCK: keep front closure behavior; do not open the garment front.")

    # Sleeve locks — skip for subtypes that inherently have no sleeves
    no_sleeve_subtypes = {"ruana_wrap", "poncho", "cape"}
    if garment_subtype not in no_sleeve_subtypes:
        if sleeve_type in sleeve_type_labels:
            locks.append(f"STRUCTURE LOCK: keep {sleeve_type_labels[sleeve_type]} from references.")
        if sleeve_length in sleeve_len_labels:
            locks.append(
                f"STRUCTURE LOCK: keep {sleeve_len_labels[sleeve_length]} proportion based on body landmarks; avoid longer reinterpretation."
            )

    if hem_shape in hem_labels:
        locks.append(f"STRUCTURE LOCK: preserve {hem_labels[hem_shape]}; do not straighten or reshape the hem.")
    if garment_length in length_labels:
        locks.append(f"STRUCTURE LOCK: keep {length_labels[garment_length]} relative to the model body.")
    if silhouette_volume in volume_labels:
        locks.append(f"STRUCTURE LOCK: preserve {volume_labels[silhouette_volume]} seen in references.")

    for cue in must_keep[:3]:
        locks.append(f"STRUCTURE CUE: preserve {cue}.")

    if confidence >= 0.68:
        locks.append(
            "STRUCTURE PRIORITY: if composition conflicts with garment shape, preserve reference garment geometry first."
        )

    merged = prompt.strip()
    for lock in locks:
        if lock[:30] not in merged:
            merged += f" {lock}"
    if len(merged) > 3200:
        merged = merged[:3200].rstrip() + "..."
    return merged


def _infer_text_mode_shot(user_prompt: Optional[str]) -> str:
    text = (user_prompt or "").lower()
    if any(k in text for k in ["macro", "close-up", "detalhe", "textura", "fio", "tecido"]):
        return "close-up"
    if any(k in text for k in ["hero", "capa", "full body", "corpo inteiro", "look completo"]):
        return "wide"
    if any(k in text for k in ["medium", "waist", "cintura", "busto", "meio corpo"]):
        return "medium"
    return "wide"


def _extract_img_candidates_from_html(page_url: str, html_text: str, limit: int = 16) -> List[str]:
    urls: List[str] = []
    seen = set()

    direct_pattern = re.compile(
        r'<img[^>]+(?:src|data-src|data-original|data-lazy-src)=["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    srcset_pattern = re.compile(
        r'<img[^>]+srcset=["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    def _push(url: str):
        if not url:
            return
        u = url.strip()
        if not u or u.startswith("data:"):
            return
        if u.startswith("//"):
            u = f"https:{u}"
        elif u.startswith("/"):
            u = urljoin(page_url, u)
        elif not u.startswith("http://") and not u.startswith("https://"):
            u = urljoin(page_url, u)
        if u in seen:
            return
        seen.add(u)
        urls.append(u)

    for match in direct_pattern.finditer(html_text):
        _push(match.group(1))
        if len(urls) >= limit:
            return urls

    for match in srcset_pattern.finditer(html_text):
        candidates = [c.strip() for c in match.group(1).split(",")]
        for candidate in candidates:
            _push(candidate.split(" ")[0])
            if len(urls) >= limit:
                return urls

    return urls


def _extract_img_candidates_with_playwright(page_url: str, limit: int = 16) -> List[str]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return []

    urls: List[str] = []
    seen = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(page_url, timeout=6000, wait_until="domcontentloaded")
            rows = page.eval_on_selector_all(
                "img",
                "els => els.map(el => ({src: el.getAttribute('src') || '', srcset: el.getAttribute('srcset') || ''}))",
            )
            browser.close()

        def _push(url: str):
            if not url:
                return
            u = url.strip()
            if not u or u.startswith("data:"):
                return
            if u.startswith("//"):
                u = f"https:{u}"
            elif u.startswith("/"):
                u = urljoin(page_url, u)
            elif not u.startswith("http://") and not u.startswith("https://"):
                u = urljoin(page_url, u)
            if u in seen:
                return
            seen.add(u)
            urls.append(u)

        for row in rows:
            _push(row.get("src", ""))
            srcset = row.get("srcset", "")
            if srcset:
                for candidate in srcset.split(","):
                    _push(candidate.strip().split(" ")[0])
            if len(urls) >= limit:
                break
    except Exception:
        return []
    return urls[:limit]


def _is_probably_useful_image(url: str) -> bool:
    low = url.lower()
    blocked_tokens = ("logo", "icon", "avatar", "sprite", "placeholder", "thumb")
    if any(token in low for token in blocked_tokens):
        return False
    return low.endswith((".jpg", ".jpeg", ".png", ".webp", ".avif")) or "image" in low or "img" in low


def _download_image_bytes(url: str, timeout: int = 8) -> Optional[bytes]:
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        })
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "image" not in ctype:
            return None
        data = r.content
        if len(data) < 18_000 or len(data) > 6_000_000:
            return None
        with Image.open(BytesIO(data)) as img:
            w, h = img.size
            if min(w, h) < 320:
                return None
        return data
    except Exception:
        return None


def _collect_grounded_reference_images(
    sources: List[dict],
    max_pages: int = 3,
    max_images: int = 3,
) -> tuple[List[bytes], str]:
    grounded_images: List[bytes] = []
    candidate_urls: List[str] = []
    pages = [s.get("uri", "") for s in sources if s.get("uri")][:max_pages]
    extraction_engine = "html_fallback"

    for page_url in pages:
        urls = _extract_img_candidates_with_playwright(page_url, limit=12)
        if urls:
            extraction_engine = "playwright"
        if not urls:
            try:
                html = requests.get(page_url, timeout=8).text
                urls = _extract_img_candidates_from_html(page_url, html, limit=12)
            except Exception:
                urls = []

        for url in urls:
            if _is_probably_useful_image(url) and url not in candidate_urls:
                candidate_urls.append(url)
        if len(candidate_urls) >= 36:
            break

    for image_url in candidate_urls:
        img_bytes = _download_image_bytes(image_url, timeout=8)
        if not img_bytes:
            continue
        grounded_images.append(img_bytes)
        if len(grounded_images) >= max_images:
            break

    return grounded_images, extraction_engine


def _extract_search_results_from_duckduckgo(html_text: str, limit: int = 5) -> List[dict]:
    """Extrai links/títulos/snippets da versão HTML do DuckDuckGo."""
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    titles = []
    for m in pattern.finditer(html_text):
        title = re.sub(r"<.*?>", "", m.group("title"))
        title = unescape(title).strip()
        href = unescape(m.group("href")).strip()
        if not title or not href:
            continue
        if href.startswith("/"):
            continue
        titles.append({"title": title, "uri": href})
        if len(titles) >= limit:
            break

    snippets = [
        unescape(re.sub(r"<.*?>", "", m.group("snippet"))).strip()
        for m in snippet_pattern.finditer(html_text)
    ]
    for i, row in enumerate(titles):
        row["snippet"] = snippets[i] if i < len(snippets) else ""
    return titles


def _duckduckgo_search(query: str, limit: int = 5) -> List[dict]:
    """Busca web forçada sem depender da tool do Gemini."""
    url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=12)
    response.raise_for_status()
    return _extract_search_results_from_duckduckgo(response.text, limit=limit)


def _infer_garment_hint(uploaded_images: List[bytes]) -> str:
    """Classificação curta da peça para montar queries de grounding quando não há prompt."""
    try:
        parts = []
        for img_bytes in uploaded_images[:4]:
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
    for img_bytes in uploaded_images[:6]:
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
                max_output_tokens=300,
                safety_settings=SAFETY_CONFIG,
                response_mime_type="application/json",
                response_json_schema=SET_DETECTION_SCHEMA,
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
        print(f"[GUIDED] ⚠️ set-pattern inference failed: {e}")
        return {
            "is_garment_set": False,
            "set_pattern_score": 0.0,
            "detected_garment_roles": [],
            "set_pattern_cues": [],
            "set_lock_mode": "off",
        }


def _build_forced_grounding_queries(
    user_prompt: Optional[str],
    garment_hint: str,
    mode: str,
) -> List[str]:
    base = (user_prompt or "").strip()
    hint = garment_hint.strip()
    subject = hint or base or "poncho aberto ruana manga morcego"

    queries = [
        f"{subject} diferença poncho ruana cardigan manga morcego",
        f"{subject} e-commerce fashion photography pose open-front",
    ]
    if mode == "full":
        queries.append(f"{subject} model wearing front open silhouette reference")
    return queries


def _format_forced_grounding_text(queries: List[str], sources: List[dict]) -> str:
    lines = []
    if queries:
        lines.append("Queries executadas:")
        for q in queries[:4]:
            lines.append(f"- {q}")
    if sources:
        lines.append("")
        lines.append("Fontes web relevantes:")
        for src in sources[:6]:
            title = src.get("title", "Untitled")
            uri = src.get("uri", "")
            snippet = src.get("snippet", "")
            row = f"- {title}: {uri}"
            if snippet:
                row += f" | {snippet[:180]}"
            lines.append(row)
    return "\n".join(lines).strip()


def _run_grounding_research(
    uploaded_images: List[bytes],
    user_prompt: Optional[str],
    mode: str,
) -> dict:
    """
    Chamada SEPARADA ao Gemini com Google Search ativo.
    DUAS ETAPAS para contornar regressão do Google (multimodal + grounding quebrado):
      1) _infer_garment_hint: analisa imagens → texto curto (sem grounding)
      2) Chamada TEXT-ONLY com GoogleSearch tool → grounding efetivo
    Retorna contexto textual e metadados de grounding.
    """
    # Etapa 1: identificar a peça via análise visual (sem grounding)
    garment_hint = _infer_garment_hint(uploaded_images) if uploaded_images else ""
    search_subject = garment_hint or user_prompt or "garment fashion"
    print(f"[GROUNDING] 👁️  Garment hint: {garment_hint}")

    # Etapa 2: chamada TEXT-ONLY com Google Search (sem imagens = sem regressão)
    search_prompt = (
        f"You are a fashion expert. I have a garment that is: {search_subject}.\n\n"
        "Use Google Search to find:\n"
        "1. The EXACT garment type name in Portuguese AND English\n"
        "2. The correct silhouette terminology (e.g., batwing sleeves, kimono cardigan, ruana, cape)\n"
        "3. How this type of garment drapes and falls on the body\n"
        "4. How professional photographers typically shoot this garment style\n\n"
        "You MUST search the web. Do NOT rely on your training data alone.\n"
        "Return ONLY plain text, NO markdown. Keep it concise, max 3 paragraphs."
    )

    response = client.models.generate_content(
        model=MODEL_AGENT,
        contents=search_prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
            safety_settings=SAFETY_CONFIG,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    queries: List[str] = []
    sources: List[dict] = []
    effective = False
    engine = "gemini_google_search"
    grounded_images: List[bytes] = []
    visual_ref_engine = "none"

    # Log grounding metadata
    try:
        candidates = getattr(response, "candidates", None)
        if candidates and len(candidates) > 0:
            candidate = candidates[0]
            gm = getattr(candidate, "grounding_metadata", None)
            print(f"[GROUNDING] 🌐 Metadata present: {gm is not None}")
            if gm:
                queries = list(getattr(gm, "web_search_queries", None) or [])
            print(f"[GROUNDING] 🌐 Search queries: {queries}")
            chunks = getattr(gm, 'grounding_chunks', None)
            if chunks:
                print(f"[GROUNDING] 🌐 Sources: {len(chunks)}")
                for i, chunk in enumerate(chunks[:5]):
                    web = getattr(chunk, 'web', None)
                    if web:
                        title = getattr(web, "title", "?")
                        uri = getattr(web, "uri", "?")
                        sources.append({"title": title, "uri": uri, "snippet": ""})
                        print(f"[GROUNDING]   📎 [{i+1}] {title} → {uri}")
            effective = bool(queries or sources)
        else:
            print(f"[GROUNDING] ⚠️  Model did NOT search")
    except Exception as e:
        print(f"[GROUNDING] ⚠️  Error reading metadata: {e}")

    result_text = _extract_response_text(response)
    # Sanitizar: remover markdown residual e truncar
    import re as _re
    result_text = _re.sub(r'[#*`]', '', result_text)
    result_text = result_text.replace('"', "'").replace("{", "(").replace("}", ")")
    result_text = result_text.replace('\n\n\n', '\n\n').strip()
    if len(result_text) > 800:
        result_text = result_text[:800] + '...'

    # Fallback: forçar grounding web com busca externa caso metadata não venha.
    if not effective:
        engine = "forced_duckduckgo"
        garment_hint = _infer_garment_hint(uploaded_images)
        forced_queries = _build_forced_grounding_queries(user_prompt, garment_hint, mode)
        forced_sources: List[dict] = []
        for q in forced_queries:
            try:
                rows = _duckduckgo_search(q, limit=3)
                for row in rows:
                    if row.get("uri") and row["uri"] not in {s.get("uri") for s in forced_sources}:
                        forced_sources.append(row)
            except Exception as e:
                print(f"[GROUNDING] ⚠️  Forced search failed for query '{q}': {e}")
        if forced_sources:
            queries = forced_queries
            sources = forced_sources[:8]
            forced_text = _format_forced_grounding_text(queries, sources)
            if forced_text:
                result_text = f"{result_text}\n\n{forced_text}".strip()
            effective = True
            print(f"[GROUNDING] ✅ Forced web search attached {len(sources)} sources.")
        else:
            print("[GROUNDING] ⚠️  Forced web search returned no sources.")

    if mode == "full" and sources:
        grounded_images, visual_ref_engine = _collect_grounded_reference_images(
            sources=sources,
            max_pages=3,
            max_images=3,
        )
        if grounded_images:
            print(f"[GROUNDING] 🖼️  Visual refs collected: {len(grounded_images)} via {visual_ref_engine}")

    print(f"[GROUNDING] 📝 Research result ({len(result_text)} chars): {result_text[:200]}...")
    return {
        "text": result_text,
        "queries": queries[:8],
        "sources": sources[:8],
        "effective": effective,
        "engine": engine,
        "source_engine": engine,
        "grounded_images": grounded_images,
        "grounded_images_count": len(grounded_images),
        "visual_ref_engine": visual_ref_engine,
    }


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

    if guided_enabled and guided_set_mode == "conjunto" and has_images:
        guided_set_detection = _infer_set_pattern_from_images(uploaded_images or [], user_prompt)
        if guided_set_detection.get("set_lock_mode") == "off":
            guided_set_detection["set_lock_mode"] = "generic"

    if has_images:
        if isinstance(structural_contract_hint, dict) and structural_contract_hint:
            structural_contract = structural_contract_hint
        else:
            structural_contract = _infer_structural_contract_from_images(uploaded_images or [], user_prompt)

    if has_images:
        # FIX: ternário separado para não engolir o MODE 2
        if has_prompt:
            extra_text = f'User text to incorporate: "{user_prompt}".'
        else:
            extra_text = (
                "No text from user. CREATE AUTOMATICALLY a Shopee/marketplace cover-level "
                "e-commerce prompt based EXCLUSIVELY on what you see in the reference images. "
                "Identify the garment, colors, fabric, and create a complete listing hero shot."
            )
        mode_info = (
            f"MODE 2 — User sent {len(uploaded_images)} reference image(s). "
            f"MANDATORY: Apply Fidelity Lock as the FIRST paragraph of the prompt. "
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

    # Construir mensagem
    context_text = mode_info
    if has_pool:
        context_text += f"\n\n{pool_context}"
    context_text += f"\n\nOutput parameters: aspect_ratio={aspect_ratio}, resolution={resolution}"
    if diversity_target:
        profile = diversity_target.get("profile_prompt", "")
        scenario = diversity_target.get("scenario_prompt", "")
        pose = diversity_target.get("pose_prompt", "")
    else:
        profile, scenario, pose = _sample_diversity_target()
    if diversity_target:
        context_text += (
            "\n\nDIVERSITY TARGET (mandatory): "
            f"Model profile ID: {diversity_target.get('profile_id', 'RUNTIME')}."
        )
    else:
        context_text += "\n\nDIVERSITY TARGET (mandatory):"
    context_text += (
        f" Use model profile: {profile}. "
        f" Use scenario: {scenario}. "
        f" Use pose guidance: {pose}. "
        "Do not replicate person/background/pose from references."
    )

    if guided_enabled:
        garment = (guided_brief or {}).get("garment", {}) or {}
        model = (guided_brief or {}).get("model", {}) or {}
        scene = (guided_brief or {}).get("scene", {}) or {}
        pose_cfg = (guided_brief or {}).get("pose", {}) or {}
        capture = (guided_brief or {}).get("capture", {}) or {}
        fidelity_mode = str((guided_brief or {}).get("fidelity_mode", "balanceada")).strip().lower()
        context_text += (
            "\n\n[GUIDED BRIEF — deterministic constraints, must obey]\n"
            f"- model_age_range: {model.get('age_range', '25-34')}\n"
            f"- set_mode: {garment.get('set_mode', 'unica')}\n"
            f"- scene_type: {scene.get('type', 'externo')}\n"
            f"- pose_style: {pose_cfg.get('style', 'tradicional')}\n"
            f"- capture_distance: {capture.get('distance', 'media')}\n"
            f"- fidelity_mode: {fidelity_mode}\n"
            "If set_mode is conjunto, infer garment-set pieces via repeated color/texture/motif cues from references and ignore accessories."
        )
        if guided_set_mode == "conjunto" and has_images:
            context_text += (
                "\n[GUIDED SET DETECTION]\n"
                f"- set_pattern_score: {guided_set_detection.get('set_pattern_score', 0.0)}\n"
                f"- detected_garment_roles: {', '.join(guided_set_detection.get('detected_garment_roles', []) or []) or 'unknown'}\n"
                f"- set_pattern_cues: {', '.join(guided_set_detection.get('set_pattern_cues', []) or []) or 'unknown'}\n"
                f"- set_lock_mode: {guided_set_detection.get('set_lock_mode', 'generic')}\n"
            )

    if has_images and structural_contract.get("enabled"):
        cues = ", ".join(structural_contract.get("must_keep", []) or []) or "none"
        context_text += (
            "\n\n[STRUCTURAL CONTRACT — preserve garment geometry from references]\n"
            f"- garment_subtype: {structural_contract.get('garment_subtype', 'unknown')}\n"
            f"- sleeve_type: {structural_contract.get('sleeve_type', 'unknown')}\n"
            f"- sleeve_length: {structural_contract.get('sleeve_length', 'unknown')}\n"
            f"- front_opening: {structural_contract.get('front_opening', 'unknown')}\n"
            f"- hem_shape: {structural_contract.get('hem_shape', 'unknown')}\n"
            f"- garment_length: {structural_contract.get('garment_length', 'unknown')}\n"
            f"- silhouette_volume: {structural_contract.get('silhouette_volume', 'unknown')}\n"
            f"- confidence: {structural_contract.get('confidence', 0.0)}\n"
            f"- must_keep_cues: {cues}\n"
            "Treat these as shape/proportion constraints. Do not drift sleeve/hem proportions. "
            "Pay special attention to garment_subtype — it defines the construction method."
        )

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
    if use_grounding:
        print("[AGENT] 🔍 Running grounding research (separate call)...")
        try:
            grounding_data = _run_grounding_research(
                uploaded_images=uploaded_images or [],
                user_prompt=user_prompt,
                mode=grounding_mode,
            )
            grounding_research = grounding_data.get("text", "")
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
            }
        except Exception as e:
            print(f"[AGENT] ⚠️  Grounding research failed: {e}")
            grounding_research = ""
            grounded_images = []

    if grounding_research:
        context_text += (
            "\n\nWEB RESEARCH RESULTS (use this to correctly identify the garment):\n"
            f"{grounding_research}"
        )
    if grounding_context_hint:
        context_text += (
            "\n\nTRIAGE HINT (garment hypothesis): "
            f"{grounding_context_hint}. Keep this silhouette strictly."
        )
    if grounding_mode == "full" and has_images:
        context_text += (
            "\n\nCRITICAL SILHOUETTE CONSTRAINTS: front fully open (never closed as poncho), "
            "integrated batwing/dolman sleeves, rounded cocoon hem preserved, matching scarf kept as a separate piece."
        )

    # ── INJEÇÃO DE REFERENCE KNOWLEDGE (budget por shot_type) ──────────
    # Close-up/macro usa menos contexto (foco em textura, não cenário/modelo)
    # Wide/medium/auto usa o conhecimento completo
    context_text += f"\n\n{REFERENCE_KNOWLEDGE}"

    context_text += (
        "\n\nReturn ONLY valid JSON matching the schema. No markdown, no explanation."
    )

    def _build_parts(context: str) -> List[types.Part]:
        parts: List[types.Part] = []
        if has_images:
            for img_bytes in (uploaded_images or [])[:14]:
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

    response = _call_prompt_model(context_text, temperature=0.45)

    # ── DECODE: caminho principal (schema) → fallback robusto (_parse_json) ──
    result = None
    # 1) Tenta response.parsed (disponível com schema enforced)
    try:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict) and "prompt" in parsed:
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

            # 3) Retry sem grounding context (último recurso)
            retry_context = (
                mode_info
                + f"\n\n{REFERENCE_KNOWLEDGE}"
                + f"\n\nOutput parameters: aspect_ratio={aspect_ratio}, resolution={resolution}"
                + "\n\nSTRICT JSON RULES: return one valid JSON object only."
            )
            if has_pool:
                retry_context = mode_info + f"\n\n{pool_context}" + retry_context[len(mode_info):]

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
    guided_shot = guided_capture_to_shot(guided_distance) if guided_enabled else None
    if guided_shot:
        result["shot_type"] = guided_shot
    elif pipeline_mode == "text_mode" and result.get("shot_type") == "auto":
        result["shot_type"] = _infer_text_mode_shot(user_prompt)

    if result.get("realism_level") not in [1, 2, 3]:
        result["realism_level"] = 2

    result["prompt"] = _apply_quality_locks(
        prompt=result.get("prompt", ""),
        has_images=has_images,
        grounding_mode=grounding_mode,
        pipeline_mode=pipeline_mode,
    )
    result["prompt"] = _apply_guided_locks(
        prompt=result.get("prompt", ""),
        guided_brief=guided_brief if guided_enabled else None,
        has_images=has_images,
        set_detection=guided_set_detection if guided_enabled and guided_set_mode == "conjunto" else None,
    )
    result["prompt"] = _apply_structural_locks(
        prompt=result.get("prompt", ""),
        has_images=has_images,
        contract=structural_contract if has_images else None,
    )

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
