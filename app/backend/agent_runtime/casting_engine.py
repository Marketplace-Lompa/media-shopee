"""
Casting engine experimental para a etapa 2.

Objetivo:
- gerar perfis brasileiros variados sem cair em presets fixos de "mesma pessoa"
- manter familias controladas de casting
- aplicar anti-repeat local via memoria curta
"""
from __future__ import annotations

import hashlib
import itertools
import json
import time
from pathlib import Path
from typing import Any, Optional

# Resolve OUTPUTS_DIR localmente para evitar importar config.py
# (config.py depende de google.genai.types que pode não estar disponível em testes)
_OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "outputs"
_CASTING_STATE_FILE = _OUTPUTS_DIR / "casting_engine_state.json"

_DEFAULT_STATE = {
    "history": [],
    "last_family_id": "",
    "cursor": 0,
}

_CASTING_FAMILIES: list[dict[str, Any]] = [
    # ── 1. Social Creator (genérica, pele média) ──────────────────────
    {
        "id": "br_social_creator",
        "label": "BR Social Creator",
        "presence": "charismatic Brazilian creator presence",
        "age_options": ["mid 20s", "late 20s to early 30s"],
        "skin_options": ["warm medium skin", "light-medium neutral skin", "golden tan skin"],
        "face_structure_options": [
            "balanced attractive facial structure with natural asymmetry",
            "soft oval face with lively cheek definition and expressive brows",
            "gentle face geometry with engaging everyday charisma",
        ],
        "hair_options": [
            "soft styled brunette hair with natural movement and a casual finish",
            "smooth dark hair with a lightly polished social-media-ready finish",
            "natural chestnut waves with relaxed everyday volume",
        ],
        "makeup_options": ["fresh natural makeup", "soft everyday glam makeup"],
        "expression_options": ["captivating relaxed expression", "subtle engaging smile", "camera-aware casual confidence"],
        "recent_avoid": ["runway severity", "editorial calm expression"],
    },
    # ── 2. Afro (consolidada — pele escura, cabelo crespo/cacheado) ───
    {
        "id": "br_afro",
        "label": "BR Afro",
        "presence": "charismatic contemporary Brazilian presence",
        "age_options": ["mid 20s", "late 20s", "late 20s to early 30s"],
        "skin_options": ["deep rich brown skin", "medium-deep warm skin", "dark warm skin"],
        "face_structure_options": [
            "balanced attractive facial planes with natural asymmetry and expressive eyes",
            "high cheekbones with a strong elegant jawline",
            "soft cheek definition with engaging everyday charisma",
            "defined facial planes with expressive brow architecture",
        ],
        "hair_options": [
            "defined natural curls with lively volume",
            "a rounded afro with natural shape and charismatic texture",
            "short sculpted natural curls with a crisp silhouette",
            "soft natural curls with casual polished definition",
            "shoulder-length natural curls with controlled volume",
        ],
        "makeup_options": ["fresh natural makeup", "clean luminous makeup", "soft everyday glam makeup"],
        "expression_options": ["captivating relaxed expression", "subtle engaging smile", "calm self-assured expression", "confident modern gaze"],
        "recent_avoid": ["straight sleek hair", "editorial severity"],
    },
    # ── 3. Morena Clara (tipo mais comum no Brasil) ───────────────────
    {
        "id": "br_morena_clara",
        "label": "BR Morena Clara",
        "presence": "warm relatable Brazilian presence",
        "age_options": ["mid 20s", "late 20s", "early 30s"],
        "skin_options": ["warm olive-medium skin", "light caramel skin", "soft tan skin"],
        "face_structure_options": [
            "rounded cheeks with a gentle jawline and warm features",
            "balanced oval face with soft natural brow depth",
            "gentle face geometry with subtle cheek warmth",
        ],
        "hair_options": [
            "long straight dark brown hair with natural shine",
            "shoulder-length dark hair with subtle ends movement",
            "dark brunette hair with a soft blowout and middle part",
            "natural dark brown layers with loose everyday finish",
        ],
        "makeup_options": ["minimal natural makeup", "fresh everyday makeup"],
        "expression_options": ["approachable natural smile", "relaxed composed expression", "warm everyday confidence"],
        "recent_avoid": ["platinum blonde", "very curly texture"],
    },
    # ── 4. Loira Natural (brasileira mel/dourado) ─────────────────────
    {
        "id": "br_loira_natural",
        "label": "BR Loira Natural",
        "presence": "naturally radiant Brazilian presence",
        "age_options": ["mid 20s", "late 20s to early 30s"],
        "skin_options": ["sun-kissed light skin", "warm golden-light skin", "light skin with natural warmth"],
        "face_structure_options": [
            "soft oval face with gentle cheek definition",
            "balanced facial proportions with a naturally open expression",
            "delicate jawline with subtle brow arch",
        ],
        "hair_options": [
            "honey-blonde waves with natural Brazilian highlights",
            "soft golden-brown hair with sun-lightened ends",
            "natural dirty-blonde hair with loose beachy texture",
            "warm caramel-blonde shoulder-length hair with natural movement",
        ],
        "makeup_options": ["fresh bronzed makeup", "minimal sun-kissed makeup"],
        "expression_options": ["warm open smile", "relaxed sunlit expression", "casual confident gaze"],
        "recent_avoid": ["very dark hair", "sharp editorial look"],
    },
    # ── 5. Ruiva (ruiva brasileira) ───────────────────────────────────
    {
        "id": "br_ruiva",
        "label": "BR Ruiva",
        "presence": "distinctive warm Brazilian presence",
        "age_options": ["mid 20s", "late 20s", "early 30s"],
        "skin_options": ["fair warm skin with light freckles", "light neutral skin with soft warmth", "light-medium skin with peachy undertone"],
        "face_structure_options": [
            "soft rounded face with gentle natural asymmetry",
            "balanced features with subtle cheek warmth and expressive eyes",
            "oval face geometry with gentle brow definition",
        ],
        "hair_options": [
            "natural copper-red shoulder-length hair with soft texture",
            "warm auburn waves with natural volume",
            "dark ginger hair with a loose everyday finish",
            "soft reddish-brown hair with natural highlights",
        ],
        "makeup_options": ["minimal natural makeup", "soft warm-toned makeup"],
        "expression_options": ["gentle confident expression", "subtle warm smile", "calm natural gaze"],
        "recent_avoid": ["very dark skin", "short cropped hair"],
    },
    # ── 6. Cabocla (miscigenada, traços indígenas/europeus) ───────────
    {
        "id": "br_cabocla",
        "label": "BR Cabocla",
        "presence": "grounded authentic Brazilian presence",
        "age_options": ["mid 20s", "late 20s to early 30s", "early 30s"],
        "skin_options": ["warm bronze skin", "medium tawny skin", "sun-warmed medium skin"],
        "face_structure_options": [
            "wide cheekbones with a softly tapered chin",
            "balanced strong facial structure with prominent cheekbones",
            "gentle rounded face with warm lived-in character",
        ],
        "hair_options": [
            "straight dark black hair with natural thickness",
            "long dark hair with a simple center part and natural weight",
            "dark brown straight hair with subtle natural body",
        ],
        "makeup_options": ["almost no visible makeup", "subtle earth-toned makeup"],
        "expression_options": ["calm composed expression", "serene natural gaze", "quiet grounded confidence"],
        "recent_avoid": ["glossy blowout finish", "heavy glamour makeup"],
    },
    # ── 7. Nikkei (nipo-brasileira) ───────────────────────────────────
    {
        "id": "br_nikkei",
        "label": "BR Nikkei",
        "presence": "contemporary Brazilian nikkei presence",
        "age_options": ["mid 20s", "late 20s", "early 30s"],
        "skin_options": ["light warm skin", "soft ivory-warm skin", "light-medium warm skin"],
        "face_structure_options": [
            "delicate bone structure with soft angular jaw",
            "balanced features with gentle cheek planes and serene brow line",
            "oval face geometry with refined proportions",
        ],
        "hair_options": [
            "straight dark hair with natural shine and blunt ends",
            "sleek shoulder-length black hair with a clean part",
            "soft dark hair with a subtle layered cut and natural weight",
        ],
        "makeup_options": ["minimal clean makeup", "fresh understated makeup"],
        "expression_options": ["calm composed expression", "gentle restrained smile", "quiet modern confidence"],
        "recent_avoid": ["very curly hair", "heavy bronzed makeup"],
    },
    # ── 8. Sulista (descendência europeia, gaúcha/catarinense) ────────
    {
        "id": "br_sulista",
        "label": "BR Sulista",
        "presence": "polished contemporary Brazilian presence",
        "age_options": ["mid 20s", "late 20s to early 30s"],
        "skin_options": ["fair neutral skin", "light skin with soft pink undertone", "light olive skin"],
        "face_structure_options": [
            "defined cheekbones with a softly angular jawline",
            "oval face with gentle European-inspired proportions",
            "balanced facial structure with subtle brow prominence",
        ],
        "hair_options": [
            "light brown straight hair with natural shine",
            "dark blonde shoulder-length hair with a casual finish",
            "soft chestnut waves with a polished natural part",
            "medium-brown hair with loose relaxed movement",
        ],
        "makeup_options": ["refined neutral makeup", "minimal fresh makeup"],
        "expression_options": ["composed confident expression", "subtle approachable expression", "quiet sophisticated gaze"],
        "recent_avoid": ["very dark skin tones", "afro texture"],
    },
    # ── 9. Nordestina (nordeste brasileiro, pele bronzeada/morena) ────
    {
        "id": "br_nordestina",
        "label": "BR Nordestina",
        "presence": "warm authentic Brazilian nordeste presence",
        "age_options": ["mid 20s", "late 20s", "early 30s"],
        "skin_options": ["warm tanned skin", "medium sun-bronzed skin", "cinnamon-warm medium skin"],
        "face_structure_options": [
            "warm rounded face with natural sun-kissed character",
            "balanced features with gentle cheek fullness and expressive eyes",
            "strong gentle bone structure with authentic asymmetry",
        ],
        "hair_options": [
            "thick dark wavy hair with natural volume",
            "long dark hair with loose natural curls at the ends",
            "dark brown hair with a sun-lightened subtle ombré effect",
            "natural dark waves with beach-textured movement",
        ],
        "makeup_options": ["minimal sun-kissed makeup", "almost no visible makeup"],
        "expression_options": ["warm genuine smile", "relaxed open expression", "casual easygoing confidence"],
        "recent_avoid": ["platinum blonde", "very pale skin"],
    },
    # ── 10. Mulata Cacheada (mestiça, cabelo cacheado, pele média) ────
    {
        "id": "br_mulata_cacheada",
        "label": "BR Mulata Cacheada",
        "presence": "vibrant contemporary Brazilian presence",
        "age_options": ["mid 20s", "late 20s", "late 20s to early 30s"],
        "skin_options": ["warm medium-brown skin", "caramel medium skin", "golden medium-deep skin"],
        "face_structure_options": [
            "soft rounded cheeks with gentle jaw definition",
            "balanced mixed-heritage features with warm natural expression",
            "gentle face geometry with lively cheek warmth",
        ],
        "hair_options": [
            "defined medium curls with natural bounce and volume",
            "loose curly hair with honey-brown highlights",
            "shoulder-length curly hair with natural frizz-free definition",
            "voluminous curly hair with a casual side part",
        ],
        "makeup_options": ["fresh glowing makeup", "soft natural makeup"],
        "expression_options": ["captivating warm smile", "relaxed radiant expression", "engaging casual confidence"],
        "recent_avoid": ["straight sleek hair", "editorial severity"],
    },
    # ── 11. Mature Elegante (40+, tom elegante único) ─────────────────
    {
        "id": "br_mature_elegante",
        "label": "BR Mature Elegante",
        "presence": "elegant mature Brazilian presence",
        "age_options": ["late 30s", "early 40s", "mid 40s"],
        "skin_options": ["medium olive skin", "medium warm skin", "light-medium neutral skin"],
        "face_structure_options": [
            "refined angular cheekbones with a composed jawline",
            "balanced mature facial structure with gentle temple contour",
            "elongated oval face with subtle nasolabial definition and wisdom",
        ],
        "hair_options": [
            "a sleek jaw-length dark bob with a clean center part",
            "polished shoulder-length dark hair with a smooth finish",
            "natural dark hair with silver-touched highlights and quiet elegance",
            "simple dark hair tucked behind the ears with understated movement",
        ],
        "makeup_options": ["understated refined makeup", "minimal elegant makeup"],
        "expression_options": ["confident composed expression", "elegant calm expression", "warm self-assured gaze"],
        "recent_avoid": ["messy casual texture", "youthful creator energy"],
    },
    # ── 12. Everyday Natural (cotidiana sem produção) ─────────────────
    {
        "id": "br_everyday_natural",
        "label": "BR Everyday Natural",
        "presence": "relatable everyday Brazilian presence",
        "age_options": ["mid 20s to early 30s", "early 30s"],
        "skin_options": ["warm medium skin", "light-medium neutral skin", "soft warm beige skin"],
        "face_structure_options": [
            "balanced everyday facial proportions with soft natural asymmetry",
            "gentle oval face with ordinary jaw softness and subtle brow depth",
            "natural cheek structure with a calm unpolished face impression",
        ],
        "hair_options": [
            "slightly messy dark brown shoulder-length hair with natural separation",
            "simple straight dark hair tucked behind one ear with everyday texture",
            "natural medium-brown hair with loose lived-in movement",
        ],
        "makeup_options": ["minimal everyday makeup", "almost no visible makeup"],
        "expression_options": ["neutral everyday expression", "soft relaxed expression"],
        "recent_avoid": ["polished blowout finish", "soft editorial expression"],
    },
    # ── 13. Minimal Premium (catalog refinado) ────────────────────────
    {
        "id": "br_minimal_premium",
        "label": "BR Minimal Premium",
        "presence": "refined premium-catalog presence",
        "age_options": ["late 20s to early 30s", "early 30s"],
        "skin_options": ["light olive skin", "light-medium neutral skin"],
        "face_structure_options": [
            "defined cheekbones with a softly narrow jawline",
            "oval face geometry with gentle brow depth",
            "balanced facial proportions with a slightly elongated chin",
        ],
        "hair_options": [
            "straight dark brown shoulder-length hair tucked behind the ears",
            "sleek dark chestnut long bob with a center part",
            "smooth espresso-brown collarbone-length hair with a clean finish",
        ],
        "makeup_options": ["refined neutral makeup", "minimal clean makeup"],
        "expression_options": ["calm sophisticated expression", "quiet confident gaze"],
        "recent_avoid": ["long natural curly hair", "golden tan waves"],
    },
    # ── 14. Warm Commercial (ondas castanhas comercial) ───────────────
    {
        "id": "br_warm_commercial",
        "label": "BR Warm Commercial",
        "presence": "polished commercial presence",
        "age_options": ["mid-to-late 20s", "late 20s to early 30s"],
        "skin_options": ["golden tan skin", "warm medium skin"],
        "face_structure_options": [
            "rounded cheeks with a softly tapered jawline",
            "heart-shaped face with gentle chin definition",
            "balanced oval face with subtle smile lines",
        ],
        "hair_options": [
            "long loose chestnut waves with a natural side part",
            "soft medium-brown waves over the shoulders",
            "dark honey-brown wavy hair with a polished blowout finish",
        ],
        "makeup_options": ["fresh natural makeup", "soft radiant makeup"],
        "expression_options": ["warm composed expression", "subtle approachable expression"],
        "recent_avoid": ["sleek jaw-length bob", "tight natural coils"],
    },
    # ── 15. Soft Editorial (editorial suave) ──────────────────────────
    {
        "id": "br_soft_editorial",
        "label": "BR Soft Editorial",
        "presence": "soft premium-editorial presence",
        "age_options": ["mid 20s", "late 20s"],
        "skin_options": ["fair neutral skin", "light olive skin", "soft warm beige skin"],
        "face_structure_options": [
            "soft oval facial structure with delicate jaw contour",
            "slightly narrow face with gentle cheek projection",
            "balanced brow-to-chin proportions with subtle asymmetry",
        ],
        "hair_options": [
            "a dark wavy shoulder-length cut with soft movement",
            "a collarbone-length dark brunette cut with airy texture",
            "soft loose waves with a subtle side part",
        ],
        "makeup_options": ["sheer editorial makeup", "subtle fresh makeup"],
        "expression_options": ["soft editorial expression", "subtle introspective gaze"],
        "recent_avoid": ["friendly polished smile", "a sleek jaw-length dark bob"],
    },
]


def get_casting_catalog() -> list[dict[str, Any]]:
    return [dict(item) for item in _CASTING_FAMILIES]


def _load_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_state() -> dict[str, Any]:
    state = _load_json(_CASTING_STATE_FILE, _DEFAULT_STATE)
    if not isinstance(state, dict):
        return dict(_DEFAULT_STATE)
    history = state.get("history", [])
    if not isinstance(history, list):
        history = []
    return {
        "history": history,
        "last_family_id": str(state.get("last_family_id", "") or ""),
        "cursor": int(state.get("cursor", 0) or 0),
    }


def reset_brazilian_casting_state() -> None:
    _save_json(_CASTING_STATE_FILE, dict(_DEFAULT_STATE))


def commit_brazilian_casting_profile(profile: dict[str, Any], *, window: int = 8) -> None:
    state = _safe_state()
    history = list(state.get("history", []))
    family_id = str(profile.get("family_id", "") or "")
    signature = str(profile.get("signature", "") or "")
    hair = str(profile.get("hair", "") or "")
    if not family_id or not signature:
        return
    history.append(
        {
            "family_id": family_id,
            "signature": signature,
            "hair": hair,
            "timestamp": int(time.time()),
        }
    )
    history = history[-max(8, window):]
    _save_json(
        _CASTING_STATE_FILE,
        {
            "history": history,
            "last_family_id": family_id,
            "cursor": int(state.get("cursor", 0) or 0) + 1,
        },
    )


def _stable_int(seed: str) -> int:
    return int(hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8], 16)


def _build_family_variants(family: dict[str, Any]) -> list[dict[str, str]]:
    combos: list[dict[str, str]] = []
    for age, skin, face_structure, hair, makeup, expression in itertools.product(
        family["age_options"],
        family["skin_options"],
        family["face_structure_options"],
        family["hair_options"],
        family["makeup_options"],
        family["expression_options"],
    ):
        signature = "|".join([family["id"], age, skin, face_structure, hair, makeup, expression])
        combos.append(
            {
                "age": age,
                "skin": skin,
                "face_structure": face_structure,
                "hair": hair,
                "makeup": makeup,
                "expression": expression,
                "signature": signature,
            }
        )
    return combos


def _family_affinity(user_prompt: Optional[str], family: dict[str, Any]) -> int:
    text = str(user_prompt or "").strip().lower()
    if not text:
        return 0
    score = 0
    family_id = family["id"]
    if "premium" in text or "catalog" in text or "sofistic" in text or "ensaio" in text:
        if family_id in {"br_minimal_premium", "br_soft_editorial", "br_sulista"}:
            score += 2
    if "ugc" in text or "cameraroll" in text or "selfie" in text or "cliente real" in text or "cotidiano" in text:
        if family_id in {"br_everyday_natural", "br_social_creator", "br_morena_clara", "br_nordestina"}:
            score += 3
    if "influencer" in text or "creator" in text or "criadora" in text or "conteudo" in text or "cativante" in text:
        if family_id in {"br_social_creator", "br_morena_clara", "br_loira_natural"}:
            score += 4
    if "autentic" in text or "natural" in text:
        if family_id in {"br_warm_commercial", "br_everyday_natural", "br_morena_clara", "br_nordestina", "br_cabocla"}:
            score += 1
    if "madura" in text or "40" in text or "elegante" in text:
        if family_id == "br_mature_elegante":
            score += 3
    if "editorial" in text or "sofisticada" in text:
        if family_id in {"br_minimal_premium", "br_soft_editorial"}:
            score += 2
    if "comercial" in text or "marketplace" in text or "amig" in text:
        if family_id in {"br_warm_commercial", "br_morena_clara"}:
            score += 2
    if "minimal" in text or "clean" in text:
        if family_id == "br_minimal_premium":
            score += 2
    return score


def _profile_family_bias(
    family_id: str,
    operational_profile: Optional[dict[str, Any]] = None,
) -> int:
    profile = operational_profile or {}
    guardrail = str(profile.get("guardrail_profile", "") or "")
    if guardrail == "strict_catalog":
        if family_id in {"br_minimal_premium", "br_warm_commercial", "br_afro", "br_mature_elegante", "br_sulista"}:
            return 3
        if family_id == "br_everyday_natural":
            return -1
    if guardrail == "natural_commercial":
        if family_id in {"br_everyday_natural", "br_social_creator", "br_morena_clara", "br_nordestina", "br_mulata_cacheada", "br_cabocla"}:
            return 3
        if family_id in {"br_minimal_premium", "br_soft_editorial"}:
            return -1
    if guardrail == "lifestyle_permissive":
        if family_id in {"br_social_creator", "br_morena_clara", "br_loira_natural", "br_everyday_natural", "br_nordestina", "br_mulata_cacheada"}:
            return 3
    if guardrail == "editorial_controlled":
        if family_id in {"br_soft_editorial", "br_afro", "br_minimal_premium", "br_mature_elegante", "br_sulista", "br_nikkei"}:
            return 3
        if family_id == "br_everyday_natural":
            return -1
    return 0


def _variant_budget_window(variants: list[dict[str, str]], invention_budget: float) -> list[dict[str, str]]:
    if len(variants) <= 8:
        return variants
    if invention_budget < 0.3:
        return variants[:8]
    if invention_budget < 0.5:
        return variants[:16]
    return variants


def _render_identity_sentence(family: dict[str, Any], variant: dict[str, str]) -> str:
    return (
        f"a distinctly different adult Brazilian woman in her {variant['age']} with "
        f"{variant['skin']}, {variant['face_structure']}, {variant['hair']}, {variant['makeup']}, "
        f"{variant['expression']}, and {family['presence']}"
    )


def select_brazilian_casting_profile(
    *,
    seed_hint: str = "",
    user_prompt: Optional[str] = None,
    forced_family_id: Optional[str] = None,
    preferred_family_ids: Optional[list[str]] = None,
    avoid_family_ids: Optional[list[str]] = None,
    window: int = 8,
    commit: bool = True,
    operational_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    state = _safe_state()
    history = list(state.get("history", []))
    recent = history[-max(3, window):]
    recent_family_counts: dict[str, int] = {}
    recent_signatures = {str(item.get("signature", "")) for item in recent if isinstance(item, dict)}
    recent_hair = [str(item.get("hair", "")) for item in recent if isinstance(item, dict)]

    for item in recent:
        if not isinstance(item, dict):
            continue
        family_id = str(item.get("family_id", "") or "")
        if family_id:
            recent_family_counts[family_id] = recent_family_counts.get(family_id, 0) + 1

    profile = operational_profile or {}
    invention_budget = float(profile.get("invention_budget", 0.5) or 0.5)

    candidates = list(_CASTING_FAMILIES)
    if forced_family_id:
        candidates = [family for family in candidates if family["id"] == forced_family_id] or candidates
    preferred_ids = [str(item).strip() for item in (preferred_family_ids or []) if str(item).strip()]
    avoid_ids = {str(item).strip() for item in (avoid_family_ids or []) if str(item).strip()}
    if preferred_ids and not forced_family_id:
        preferred = [family for family in candidates if family["id"] in set(preferred_ids)]
        if preferred:
            candidates = preferred
    if avoid_ids and len(candidates) > 1:
        pruned = [family for family in candidates if family["id"] not in avoid_ids]
        if pruned:
            candidates = pruned

    last_family_id = str(state.get("last_family_id", "") or "")
    candidates.sort(
        key=lambda family: (
            recent_family_counts.get(family["id"], 0),
            1 if family["id"] == last_family_id else 0,
            -(_family_affinity(user_prompt, family) + _profile_family_bias(family["id"], profile)),
            family["id"],
        )
    )

    least_count = recent_family_counts.get(candidates[0]["id"], 0) if candidates else 0
    best_candidates = [
        family for family in candidates
        if recent_family_counts.get(family["id"], 0) == least_count
    ] or candidates
    if len(best_candidates) > 1 and last_family_id:
        filtered = [family for family in best_candidates if family["id"] != last_family_id]
        if filtered:
            best_candidates = filtered

    seed = _stable_int(seed_hint or f"{time.time():.0f}")
    cursor = int(state.get("cursor", 0) or 0)
    best_candidates.sort(
        key=lambda family: (
            -(_family_affinity(user_prompt, family) + _profile_family_bias(family["id"], profile)),
            family["id"],
        )
    )
    family = best_candidates[(cursor + seed) % len(best_candidates)]

    variants = _build_family_variants(family)
    variants.sort(key=lambda item: item["signature"])
    variants = _variant_budget_window(variants, invention_budget)
    fresh_variants = [item for item in variants if item["signature"] not in recent_signatures] or variants
    variant = fresh_variants[(cursor + seed) % len(fresh_variants)]

    identity_sentence = _render_identity_sentence(family, variant)
    recent_avoid = [item for item in family.get("recent_avoid", []) if item and item not in recent_hair][:2]

    result = {
        "family_id": family["id"],
        "family_label": family["label"],
        "age": variant["age"],
        "skin": variant["skin"],
        "face_structure": variant["face_structure"],
        "hair": variant["hair"],
        "makeup": variant["makeup"],
        "expression": variant["expression"],
        "presence": family["presence"],
        "signature": variant["signature"],
        "identity_sentence": identity_sentence,
        "difference_instruction": (
            "This casting should clearly differ from recent outputs in hair silhouette, face impression, and age energy."
        ),
        "recent_avoid": recent_avoid,
        "debug": {
            "recent_family_counts": recent_family_counts,
            "recent_hair": recent_hair[-4:],
            "seed_hint": seed_hint,
        },
    }

    if commit:
        commit_brazilian_casting_profile(result, window=window)

    return result
