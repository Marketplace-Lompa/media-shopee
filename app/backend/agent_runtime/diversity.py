"""
Diversity sampling — Latent Space Casting para modelos brasileiras.

Gera persona única via Name Blending dinâmico + vibe geográfica + casting tier.
Não hardcoda traços físicos — âncora por nome + região para que o modelo
puxe clusters de beleza real do espaço latente.

Extraído de agent.py para manter o orquestrador enxuto.
"""
import random


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
        "Brazilian new face",
        "editorial beauty",
        "premium e-commerce lookbook model",
        "premium Brazilian catalog model",
        "high-end commercial beauty",
        "contemporary campaign face",
        "lookbook model",
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
