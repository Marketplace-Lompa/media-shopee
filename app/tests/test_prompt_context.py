from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.prompt_context import build_generate_context_text
from agent_runtime.constants import build_reference_knowledge


def test_build_generate_context_text_preserves_core_block_order() -> None:
    context = build_generate_context_text(
        has_images=True,
        has_prompt=True,
        uploaded_images_count=1,
        user_prompt="foto premium de ecommerce",
        pool_context="pool ready",
        aspect_ratio="4:5",
        resolution="1536",
        profile="profile anchor",
        diversity_target={"profile_id": "runtime-profile"},
        guided_enabled=False,
        guided_brief=None,
        guided_set_mode="unica",
        guided_set_detection={},
        structural_contract={
            "enabled": True,
            "front_opening": "open",
            "garment_length": "hip",
            "silhouette_volume": "regular",
            "hem_shape": "straight",
            "sleeve_type": "set-in",
            "must_keep": ["front opening"],
            "confidence": 0.9,
        },
        look_contract=None,
        grounding_research="grounding text",
        grounding_effective=True,
        grounding_context_hint="cardigan",
        grounding_mode="full",
        mode_defaults_text="Active visual mode: Natural.",
        reference_knowledge="REFERENCE_KNOWLEDGE_BLOCK",
    )

    mode_index = context.index("<MODE>")
    mode_presets_index = context.index("<MODE_PRESETS>")
    pool_index = context.index("<POOL_CONTEXT>")
    output_index = context.index("<OUTPUT_PARAMETERS>")
    diversity_index = context.index("<DIVERSITY_TARGET>")
    grounding_index = context.index("<GROUNDING_RESULTS>")
    triage_hint_index = context.index("<TRIAGE_HINT>")
    grounding_constraints_index = context.index("<GROUNDING_CONSTRAINTS>")
    reference_index = context.index("REFERENCE_KNOWLEDGE_BLOCK")
    final_instruction_index = context.index("Return ONLY valid JSON matching the schema. No markdown, no explanation.")

    assert mode_index < mode_presets_index < pool_index < output_index < diversity_index
    assert diversity_index < grounding_index < triage_hint_index < grounding_constraints_index
    assert grounding_constraints_index < reference_index < final_instruction_index


def test_build_generate_context_text_skips_optional_blocks_when_inputs_are_empty() -> None:
    context = build_generate_context_text(
        has_images=False,
        has_prompt=False,
        uploaded_images_count=0,
        user_prompt=None,
        pool_context="",
        aspect_ratio="1:1",
        resolution="1024",
        profile="profile anchor",
        diversity_target=None,
        guided_enabled=False,
        guided_brief=None,
        guided_set_mode="unica",
        guided_set_detection={},
        structural_contract={},
        look_contract=None,
        grounding_research="",
        grounding_effective=False,
        grounding_context_hint=None,
        grounding_mode="off",
        mode_defaults_text=None,
        reference_knowledge="REFERENCE_KNOWLEDGE_BLOCK",
    )

    assert "<MODE_PRESETS>" not in context
    assert "<POOL_CONTEXT>" not in context
    assert "<GUIDED_BRIEF>" not in context
    assert "<STRUCTURAL_CONTRACT>" not in context
    assert "<LOOK_CONTRACT>" not in context
    assert "<GROUNDING_RESULTS>" not in context
    assert "<TRIAGE_HINT>" not in context
    assert "<GROUNDING_CONSTRAINTS>" not in context


def test_build_generate_context_text_uses_text_only_diversity_rules_without_reference_leak() -> None:
    context = build_generate_context_text(
        has_images=False,
        has_prompt=True,
        uploaded_images_count=0,
        user_prompt="vestido premium para ecommerce",
        pool_context="",
        aspect_ratio="4:5",
        resolution="1536",
        profile="features blend 'Camila' and 'Dandara Silva'",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "profile_hint": "features blend 'Camila' and 'Dandara Silva'",
            "presence_energy": "warm",
            "presence_tone": "commercial",
            "casting_state": {
                "age": "late 20s to early 30s",
                "skin": "warm medium skin",
                "face_structure": "balanced everyday facial proportions with soft natural asymmetry",
                "hair": "natural medium-brown hair with loose lived-in movement",
                "makeup": "minimal everyday makeup",
                "expression": "soft relaxed expression",
                "presence": "relatable everyday Brazilian presence",
                "signature": "sig-123",
                "difference_instruction": "This casting should clearly differ from recent outputs in hair silhouette, face impression, and age energy.",
                "recent_avoid": ["polished blowout finish"],
            },
            "scene_state": {
                "world_family": "residential_daylight",
                "microcontext": "window-side residential corner with quiet lived-in order",
                "emotional_register": "soft lived-in ease",
                "material_language": "light wood + matte wall + soft textile",
                "background_density": "restrained",
                "brazil_anchor": "credible Brazilian apartment atmosphere",
                "scene_signature": "sig-scene-123",
            },
            "capture_state": {
                "framing_intent": "three_quarter",
                "camera_family": "natural_digital",
                "geometry_intent": "three_quarter_eye_level",
                "capture_feel": "natural digital commercial feel",
                "lens_language": "natural digital lens feel",
                "subject_separation": "gentle natural depth",
                "body_relation": "three-quarter proportion with clear upper-to-skirt transition",
                "angle_logic": "eye-level body relation",
                "garment_priority": "favor neckline, sleeve architecture, and waist-to-skirt transition",
                "capture_signature": "sig-capture-123",
            },
            "pose_state": {
                "pose_family": "relaxed",
                "stance_logic": "grounded relaxed stance with breathable body space",
                "weight_shift": "gentle weight shift into one hip",
                "arm_logic": "one hand lightly grazing the skirt while the other stays relaxed and clear of the waistline",
                "torso_orientation": "slight torso turn that keeps the garment readable",
                "head_direction": "head open toward camera with relaxed attention",
                "gesture_intention": "relaxed human presence",
                "garment_interaction": "keep hands and body placement clear of key garment construction details",
                "surface_direction": "with a soft weight shift, one hand lightly grazing the skirt, and a slight torso turn that keeps the waist and sleeves visible",
                "pose_signature": "sig-pose-123",
            },
            "styling_state": {
                "completion_level": "commercially complete natural styling",
                "footwear_strategy": "minimal tan leather sandals",
                "accessory_restraint": "light personal styling only",
                "look_finish": "natural complete look without overstyling",
                "styling_interference": "low styling interference",
                "hero_balance": "garment remains the hero while the look feels resolved",
                "footwear_required": True,
                "styling_signature": "sig-styling-123",
            },
            "coordination_state": {
                "master_intent": "warm believable commercial ease",
                "presence_world_fusion": "relatable everyday Brazilian presence inside soft lived-in ease",
                "camera_body_fusion": "natural digital commercial feel matched to relaxed human presence",
                "styling_world_balance": "natural complete look without overstyling with restrained background support",
                "garment_priority_rule": "garment remains the hero while the look feels resolved",
                "visual_tension": "gentle natural depth + grounded relaxed stance with breathable body space",
                "synthesis_rule": "All visible choices must feel like the same photograph with one commercial intention, not separate good ideas described in sequence.",
                "bridge_clause": "The warm setting, relaxed body direction, and clean capture work together to keep the garment believable and visually primary.",
                "coordination_signature": "sig-coordination-123",
            },
        },
        guided_enabled=False,
        guided_brief=None,
        guided_set_mode="unica",
        guided_set_detection={},
        structural_contract={},
        look_contract=None,
        grounding_research="",
        grounding_effective=False,
        grounding_context_hint=None,
        grounding_mode="off",
        mode_defaults_text="Active visual mode: Natural.",
        reference_knowledge="REFERENCE_KNOWLEDGE_BLOCK",
    )

    assert "<MODE_PRESETS>" in context
    assert "GARMENT-ONLY REFERENCE MODE:" not in context
    assert "Discard the reference model" not in context
    # Diretivas unificadas
    assert "Model persona anchor:" in context
    assert "Presence:" in context
    assert "MODE_PRESETS" in context
    assert "directly usable by the image generator" in context
    assert "believable, non-stereotyped way" in context
    assert "Never mention preset labels" in context
    assert "invent a fresh specific solution" in context
    assert "OPERATIONAL DIRECTION" in context
    assert "invention budget:" in context
    assert "primary emphasis:" in context
    assert "subject surface budget:" in context
    assert "scene surface budget:" in context
    assert "capture surface budget:" in context
    assert "styling surface budget:" in context
    assert "pose surface budget:" in context
    assert "guardrail behavior:" in context
    assert "without naming modes or preset mechanics" in context
    assert "CASTING LATENT STATE" in context
    assert "SCENE LATENT STATE" in context
    assert "CAPTURE LATENT STATE" in context
    assert "POSE LATENT STATE" in context
    assert "STYLING LATENT STATE" in context
    assert "ART DIRECTION COORDINATION STATE" in context
    assert "generic apartment, street, or premium backdrop" in context
    assert "choose how the camera should look at the garment" in context
    assert "apparent age" in context
    assert "specific stance or gesture" in context
    assert "complete the look with fashion judgment" in context
    assert "one authored image direction" in context
    assert "natural relational phrase" in context
    assert "recent avoid:" in context
    assert "family_id" not in context


def test_build_generate_context_text_reference_mode_uses_mode_presets_and_name_blending() -> None:
    """Fase 2: ref mode recebe MODE_PRESETS + Name Blending (como text_mode)."""
    context = build_generate_context_text(
        has_images=True,
        has_prompt=True,
        uploaded_images_count=3,
        user_prompt="foto premium de cropped",
        pool_context="pool ready",
        aspect_ratio="4:5",
        resolution="1536",
        profile="features blend 'Juliana' and 'Raissa'",
        diversity_target={
            "profile_id": "natural:natural_commercial",
            "profile_hint": "features blend 'Juliana' and 'Raissa'",
            "presence_energy": "confident",
            "presence_tone": "editorial",
        },
        guided_enabled=False,
        guided_brief=None,
        guided_set_mode="unica",
        guided_set_detection={},
        structural_contract={
            "enabled": True,
            "garment_subtype": "cropped_top",
        },
        look_contract=None,
        grounding_research="",
        grounding_effective=False,
        grounding_context_hint=None,
        grounding_mode="off",
        mode_defaults_text="Active visual mode: Natural.",
        reference_knowledge="REFERENCE_KNOWLEDGE_BLOCK",
    )

    # MODE_PRESETS presente no ref mode
    assert "<MODE_PRESETS>" in context
    # Bloco GARMENT-ONLY com regras anti-cópia
    assert "GARMENT-ONLY REFERENCE MODE:" in context
    assert "Discard the reference model completely" in context
    # Name Blending e presence axes presentes
    assert "Juliana" in context
    assert "Raissa" in context
    assert "Presence: confident, editorial." in context
    # Direção para seguir MODE_PRESETS
    assert "MODE_PRESETS" in context
    assert "Follow those directions" in context
    # Sem scenario/pose literais hardcoded no ref mode
    assert "Place new model in scenario:" not in context
    assert "Use pose:" not in context


# ═══════════════════════════════════════════════════════════════════════════════
# Testes de build_reference_knowledge (filtragem inteligente de seções)
# ═══════════════════════════════════════════════════════════════════════════════

def test_build_reference_knowledge_excludes_garment_vocab_for_simple_text_brief() -> None:
    """Brief simples sem menção a material/têxtil → exclui GARMENT VOCABULARY."""
    rk = build_reference_knowledge(user_prompt="vestido preto elegante", has_images=False)
    assert "BRAZILIAN TERM MAPPING" in rk
    assert "SHOT COMPOSITION" in rk
    assert "MODEL & SCENE" in rk
    assert "REALISM LEVERS" in rk
    # Garment vocabulary pesado NÃO deve estar presente
    assert "chunky cable-knit" not in rk
    assert "brioche stitch" not in rk
    assert "GARMENT DESCRIPTION" not in rk


def test_build_reference_knowledge_includes_garment_vocab_when_material_keyword_present() -> None:
    """Brief com keyword de material → inclui GARMENT VOCABULARY."""
    rk = build_reference_knowledge(user_prompt="blusa de tricô bege", has_images=False)
    assert "GARMENT DESCRIPTION" in rk
    assert "chunky cable-knit" in rk

    rk2 = build_reference_knowledge(user_prompt="vestido de renda", has_images=False)
    assert "GARMENT DESCRIPTION" in rk2


def test_build_reference_knowledge_always_includes_garment_vocab_with_images() -> None:
    """Com imagens de referência → sempre inclui GARMENT VOCABULARY."""
    rk = build_reference_knowledge(user_prompt="vestido preto simples", has_images=True)
    assert "GARMENT DESCRIPTION" in rk
    assert "chunky cable-knit" in rk


def test_build_reference_knowledge_handles_none_prompt() -> None:
    """None prompt (modo 3 sem texto) → funciona sem erro, exclui garment vocab."""
    rk = build_reference_knowledge(user_prompt=None, has_images=False)
    assert "BRAZILIAN TERM MAPPING" in rk
    assert "GARMENT DESCRIPTION" not in rk


def test_build_reference_knowledge_compact_text_mode_keeps_only_vocabulary_and_mapping() -> None:
    rk = build_reference_knowledge(
        user_prompt="vestido midi de linho verde oliva",
        has_images=False,
        compact_text_mode=True,
    )

    assert "BRAZILIAN TERM MAPPING" in rk
    assert "TEXT MODE NOTE" in rk
    assert "SHOT COMPOSITION" not in rk
    assert "MODEL & SCENE" not in rk
    assert "REALISM LEVERS" not in rk
