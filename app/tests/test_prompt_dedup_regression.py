"""Regression tests — Anti-duplicação de casting surface.

Reproduz o cenário real do bug: o Prompt Agent gera uma prosa narrativa rica
descrevendo a modelo, e o casting_state contém os mesmos dados estruturados.
O prompt final NÃO deve conter blocos duplicados (ex: "She appears..." redundante).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_result import finalize_prompt_agent_result


# ── Helpers ──────────────────────────────────────────────────────────────

def _count_occurrences(text: str, token: str) -> int:
    """Conta quantas vezes um token aparece (case-insensitive)."""
    return len(re.findall(re.escape(token), text, re.IGNORECASE))


def _count_she_appears_blocks(text: str) -> int:
    """Conta blocos 'She appears as a woman' / 'She has a face' no prompt."""
    return len(re.findall(r"\bShe (?:appears|has)\b", text, re.IGNORECASE))


def _call_finalize(prompt: str, casting_state: dict, mode_id: str = "natural") -> dict:
    """Wrapper para chamar finalize_prompt_agent_result com os defaults do teste."""
    return finalize_prompt_agent_result(
        result={
            "prompt": prompt,
            "shot_type": "medium",
        },
        has_images=False,
        has_prompt=True,
        user_prompt="foto premium",
        structural_contract={},
        guided_brief=None,
        guided_enabled=False,
        guided_set_mode="unica",
        guided_set_detection={},
        grounding_mode="off",
        pipeline_mode="text_mode",
        aspect_ratio="4:5",
        pose="standing pose",
        grounding_pose_clause="",
        profile="profile anchor",
        scenario="studio scene",
        diversity_target={"casting_state": casting_state},
        mode_id=mode_id,
    )


# ── Cenário do bug real: prosa rica + casting completo ───────────────────

RICH_PROMPT = (
    "RAW photo, a vibrant 28-year-old Brazilian woman with a heart-shaped face, "
    "high cheekbones and softly arched brows, framed by dark chocolate shoulder-length waves "
    "with a natural side part. Her deep honey-tan skin has a natural satin finish with "
    "light freckles across her nose and cheeks. She has a compact athletic frame with "
    "balanced shoulder-to-hip proportions and a quiet attentive expression with a neutral "
    "relaxed mouth, wearing an olive green linen midi dress in a minimalist studio."
)

FULL_CASTING_STATE = {
    "age": "late 20s",
    "face_structure": "heart-shaped face with high cheekbones",
    "hair": "dark chocolate shoulder-length waves with a natural side part",
    "presence": "balanced shoulders and waist",
    "expression": "neutral mouth and quiet attention",
    "beauty_read": "warm honey skin with light freckles",
    "body": "compact athletic frame with medium waist-to-hip ratio",
}


def test_rich_prompt_does_not_duplicate_face_traits():
    """Quando a prosa já descreve a face completamente, NÃO re-injetar."""
    result = _call_finalize(RICH_PROMPT, FULL_CASTING_STATE)
    low = result["prompt"].lower()

    # "heart-shaped" deve aparecer no máximo 1x
    assert _count_occurrences(low, "heart-shaped") <= 1, (
        f"Duplicação de 'heart-shaped': {_count_occurrences(low, 'heart-shaped')}x"
    )
    # "high cheekbones" deve aparecer no máximo 1x
    assert _count_occurrences(low, "high cheekbones") <= 1, (
        f"Duplicação de 'high cheekbones': {_count_occurrences(low, 'high cheekbones')}x"
    )


def test_rich_prompt_does_not_duplicate_hair_traits():
    """Quando a prosa já descreve o cabelo, NÃO re-injetar."""
    result = _call_finalize(RICH_PROMPT, FULL_CASTING_STATE)
    low = result["prompt"].lower()

    assert _count_occurrences(low, "chocolate") <= 1, (
        f"Duplicação de 'chocolate': {_count_occurrences(low, 'chocolate')}x"
    )
    assert _count_occurrences(low, "shoulder-length") <= 1, (
        f"Duplicação de 'shoulder-length': {_count_occurrences(low, 'shoulder-length')}x"
    )


def test_rich_prompt_does_not_duplicate_skin_traits():
    """Quando a prosa já descreve pele/beauty, NÃO re-injetar."""
    result = _call_finalize(RICH_PROMPT, FULL_CASTING_STATE)
    low = result["prompt"].lower()

    assert _count_occurrences(low, "honey") <= 1, (
        f"Duplicação de 'honey': {_count_occurrences(low, 'honey')}x"
    )
    assert _count_occurrences(low, "freckles") <= 2, (
        f"Excesso de 'freckles': {_count_occurrences(low, 'freckles')}x (máx 2)"
    )


def test_rich_prompt_does_not_duplicate_body_traits():
    """Quando a prosa já descreve o corpo, NÃO re-injetar."""
    result = _call_finalize(RICH_PROMPT, FULL_CASTING_STATE)
    low = result["prompt"].lower()

    assert _count_occurrences(low, "compact athletic") <= 1, (
        f"Duplicação de 'compact athletic': {_count_occurrences(low, 'compact athletic')}x"
    )


def test_rich_prompt_limits_she_appears_blocks():
    """O prompt final deve ter no máximo 1 bloco 'She appears/has'."""
    result = _call_finalize(RICH_PROMPT, FULL_CASTING_STATE)
    count = _count_she_appears_blocks(result["prompt"])
    assert count <= 1, (
        f"Excesso de blocos 'She appears/has': {count}x (máx 1)"
    )


def test_rich_prompt_respects_word_budget():
    """O prompt final NÃO deve exceder 280 palavras (budget seguro para Nano Banana 2)."""
    result = _call_finalize(RICH_PROMPT, FULL_CASTING_STATE)
    word_count = len(result["prompt"].split())
    assert word_count <= 280, (
        f"Budget estourado: {word_count} palavras (máx 280)"
    )


# ── Cenário inverso: prosa esparsa DEVE receber injeção ──────────────────

SPARSE_PROMPT = (
    "RAW photo, a Brazilian woman with warm natural presence, "
    "wearing an olive green linen midi dress."
)


def test_sparse_prompt_still_receives_casting_injection():
    """Quando a prosa é esparsa, os traits do casting DEVEM ser injetados."""
    result = _call_finalize(SPARSE_PROMPT, FULL_CASTING_STATE)
    low = result["prompt"].lower()

    # Pelo menos 3 dos 5 markers principais devem estar presentes
    markers_present = sum(1 for m in [
        "heart-shaped",
        "chocolate",
        "honey",
        "compact athletic",
        "quiet attention",
    ] if m in low)

    assert markers_present >= 3, (
        f"Insuficiente: apenas {markers_present}/5 markers injetados na prosa esparsa"
    )


def test_sparse_prompt_gets_casting_surface_source():
    """Em prosa esparsa, casting_surface deve ser registrado como fonte usada."""
    result = _call_finalize(SPARSE_PROMPT, FULL_CASTING_STATE)
    used_sources = {
        item["source"]
        for item in result.get("prompt_compiler_debug", {}).get("used_clauses", [])
    }
    # casting_surface OU human_surface_floor devem estar presentes
    assert "casting_surface" in used_sources or "human_surface_floor" in used_sources, (
        f"Nenhuma fonte de casting encontrada: {used_sources}"
    )


# ── Fix P1: freckles não viram regra implícita ───────────────────────────

def test_explicit_freckles_are_preserved_without_forced_spatial_qualifier():
    """Quando freckles vêm explicitamente, elas podem ser preservadas sem localização forçada."""
    # Prosa sem menção a freckles — forçar injeção via casting
    sparse_no_freckles = (
        "RAW photo, a Brazilian woman wearing an olive green linen midi dress "
        "in a minimalist studio."
    )
    casting_with_freckles = {
        "age": "late 20s",
        "face_structure": "heart-shaped face",
        "hair": "dark brown waves",
        "expression": "gentle smile",
        "beauty_read": "warm honey skin with light freckles",
        "body": "balanced proportions",
    }
    result = _call_finalize(sparse_no_freckles, casting_with_freckles)
    low = result["prompt"].lower()

    if "freckles" in low:
        assert "freckles" in low


def test_sparse_prompt_without_explicit_freckles_uses_neutral_skin_realism():
    """Quando não há freckles explícitas, o fallback neutro não deve inventá-las."""
    sparse_prompt = (
        "RAW photo, a Brazilian woman wearing an olive green linen midi dress "
        "in a minimalist studio."
    )
    sparse_casting = {
        "age": "late 20s",
        "face_structure": "defined facial structure",
        "hair": "dark brown waves",
    }
    result = _call_finalize(sparse_prompt, sparse_casting)
    low = result["prompt"].lower()

    assert "warm honey skin" in low
    assert "freckles" not in low


# ── Rescue Gate: sentences mistas devem sobreviver ───────────────────────

from agent_runtime.prompt_result import _is_human_identity_dump_sentence


def test_rescue_gate_wearing_sentence_is_not_dump():
    """Sentence com identidade + wearing NÃO deve ser dump."""
    sentence = (
        "RAW photo, a Brazilian woman in her late 20s with defined facial "
        "structure wearing a long-sleeved knit pullover."
    )
    assert _is_human_identity_dump_sentence(sentence) is False, (
        "Sentence mista (identidade + wearing) foi incorretamente classificada como dump"
    )


def test_rescue_gate_raw_photo_sentence_is_not_dump():
    """Sentence com RAW photo + identidade NÃO deve ser dump."""
    sentence = (
        "RAW photo, a warm Brazilian woman in her late 20s with "
        "soft almond eyes and honey skin."
    )
    assert _is_human_identity_dump_sentence(sentence) is False, (
        "Sentence com RAW photo foi incorretamente classificada como dump"
    )


def test_rescue_gate_pure_identity_is_still_dump():
    """Sentence de identidade pura (sem roupa/pose/RAW) DEVE ser dump."""
    sentences = [
        "She appears as a woman in her late 20s with defined facial structure.",
        "A vibrant Brazilian woman in her late 20s with warm honey skin.",
        "She has body with broad shoulders and a narrow waist, athletic-lean build.",
    ]
    for sentence in sentences:
        assert _is_human_identity_dump_sentence(sentence) is True, (
            f"Sentence pura de identidade NÃO foi classificada como dump: {sentence[:60]}"
        )


def test_rescue_gate_pose_sentence_is_not_dump():
    """Sentence com identidade + pose explícita NÃO deve ser dump."""
    sentence = (
        "A Brazilian woman in her late 20s, shifting her weight slightly "
        "to one side with a neutral relaxed expression."
    )
    assert _is_human_identity_dump_sentence(sentence) is False, (
        "Sentence mista (identidade + pose) foi incorretamente classificada como dump"
    )


def test_rescue_gate_preserves_raw_photo_in_final_prompt():
    """RAW photo presente na sentence mista deve sobreviver no prompt final."""
    prompt_with_raw = (
        "RAW photo, a Brazilian woman in her late 20s with defined facial "
        "structure wearing an olive green linen midi dress in a minimalist studio."
    )
    result = _call_finalize(prompt_with_raw, FULL_CASTING_STATE)
    low = result["prompt"].lower()
    assert "raw photo" in low, (
        f"'RAW photo' perdido no prompt final: {result['prompt'][:120]}..."
    )


def test_rescue_gate_preserves_garment_in_final_prompt():
    """Garment lead na sentence mista deve sobreviver no prompt final."""
    prompt_with_garment = (
        "RAW photo, a Brazilian woman in her late 20s wearing a geometric "
        "knit pullover in an urban studio."
    )
    result = _call_finalize(prompt_with_garment, FULL_CASTING_STATE)
    low = result["prompt"].lower()
    assert "pullover" in low, (
        f"'pullover' perdido no prompt final: {result['prompt'][:120]}..."
    )
