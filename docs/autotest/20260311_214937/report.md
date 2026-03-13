# Autotest V2 Report

- **Timestamp:** 2026-03-11 21:56:59
- **References:** `../../docs/roupa-referencia-teste` (3 runs)
- **Preset:** catalog_clean
- **Scene:** auto_br
- **Fidelity:** balanceada
- **Self-correction:** ON
- **Corrections applied:** 3

## Aggregate Scores

| Metric | Avg | Min | Max | Pass Rate |
|--------|-----|-----|-----|-----------|
| garment_fidelity | 0.93 | 0.90 | 0.95 | 100% |
| silhouette_fidelity | 0.89 | 0.85 | 0.92 |  |
| texture_fidelity | 0.95 | 0.92 | 0.98 |  |
| construction_fidelity | 0.93 | 0.90 | 0.95 |  |
| model_change_strength | 1.00 | 1.00 | 1.00 | 100% |
| environment_change_strength | 1.00 | 1.00 | 1.00 | 100% |
| innerwear_change_strength | 1.00 | 1.00 | 1.00 |  |
| pose_vitality | 0.62 | 0.40 | 0.85 | 33% |
| creative_impact | 0.80 | 0.70 | 0.90 | 100% |
| brazilian_scene_authenticity | 0.82 | 0.60 | 0.95 | 67% |
| commercial_readiness | 0.88 | 0.85 | 0.95 |  |
| photorealism_score | 0.93 | 0.90 | 0.98 |  |
| overall_score | 0.88 | 0.82 | 0.94 |  |

## Self-Correction Effectiveness

| Metric | First Half | Second Half | Delta |
|--------|-----------|-------------|-------|
| garment_fidelity | 0.95 | 0.93 | -0.02 |
| silhouette_fidelity | 0.90 | 0.89 | -0.02 |
| texture_fidelity | 0.92 | 0.96 | +0.04 |
| construction_fidelity | 0.95 | 0.93 | -0.02 |
| model_change_strength | 1.00 | 1.00 | +0.00 |
| environment_change_strength | 1.00 | 1.00 | +0.00 |
| innerwear_change_strength | 1.00 | 1.00 | +0.00 |
| pose_vitality | 0.40 | 0.72 | +0.32 |
| creative_impact | 0.70 | 0.85 | +0.15 |
| brazilian_scene_authenticity | 0.60 | 0.93 | +0.33 |
| commercial_readiness | 0.85 | 0.90 | +0.05 |
| photorealism_score | 0.90 | 0.94 | +0.04 |
| overall_score | 0.82 | 0.91 | +0.09 |

## Corrections Applied

| Run | Metric | Score | Action |
|-----|--------|-------|--------|
| 1 | pose_vitality | 0.4 | boost pose_vitality |
| 1 | brazilian_scene_authenticity | 0.6 | boost scene_authenticity |
| 2 | pose_vitality | 0.6 | boost pose_vitality |

## Diversity Analysis

| Dimension | Unique | Pool | Coverage |
|-----------|--------|------|----------|
| casting_family | 3 | 5 | 60% |
| scene_family | 3 | 4 | 75% |
| pose_family | 3 | 4 | 75% |
| camera_profile | 3 | 3 | 100% |
| lighting_profile | 3 | 5 | 60% |
| styling_profile | 2 | 3 | 67% |

**Overall diversity score:** 72.8%

## Individual Runs

### Run 1
- Session: `d5dee0d6`
- Elapsed: 139.3s
- Art direction: casting=br_warm_commercial, scene=br_showroom_sp, pose=front_relaxed_hold, camera=canon_balanced
- garment_fidelity: 0.95
- silhouette_fidelity: 0.9
- texture_fidelity: 0.92
- construction_fidelity: 0.95
- model_change_strength: 1.0
- environment_change_strength: 1.0
- innerwear_change_strength: 1.0
- pose_vitality: 0.4 **LOW**
- creative_impact: 0.7
- brazilian_scene_authenticity: 0.6 **LOW**
- commercial_readiness: 0.85
- photorealism_score: 0.9
- overall_score: 0.82
- Issues: pose_is_somewhat_stiff_and_mannequin_like
- Summary: The pipeline successfully preserved the complex striped crochet texture and the specific ruana/wrap construction. The model swap is complete and effective, and the change from a bodysuit to a white tee and trousers in the final edit significantly improves the commercial appeal. The pose remains a bit static, but the technical fidelity to the garment's stitch pattern and drape is excellent.

### Run 2
- Session: `f7e8b7c0`
- Elapsed: 132.9s
- Art direction: casting=br_soft_editorial, scene=br_pinheiros_living, pose=standing_full_shift, camera=phone_clean
- garment_fidelity: 0.9
- silhouette_fidelity: 0.85
- texture_fidelity: 0.95
- construction_fidelity: 0.9
- model_change_strength: 1.0
- environment_change_strength: 1.0
- innerwear_change_strength: 1.0
- pose_vitality: 0.6 **LOW**
- creative_impact: 0.8
- brazilian_scene_authenticity: 0.9
- commercial_readiness: 0.85
- photorealism_score: 0.9
- overall_score: 0.88
- Summary: The final output successfully transforms the amateur reference into a high-quality editorial image. The garment's unique crochet texture and stripe pattern are preserved with high fidelity. The model swap is complete, featuring a distinct Brazilian aesthetic, and the environment feels authentic and well-composed. The silhouette is slightly more structured than the reference but maintains the core cocoon shape.

### Run 3
- Session: `a27d4ed2`
- Elapsed: 134.7s
- Art direction: casting=br_mature_elegant, scene=br_curitiba_cafe, pose=paused_mid_step, camera=fujifilm_candid
- garment_fidelity: 0.95
- silhouette_fidelity: 0.92
- texture_fidelity: 0.98
- construction_fidelity: 0.95
- model_change_strength: 1.0
- environment_change_strength: 1.0
- innerwear_change_strength: 1.0
- pose_vitality: 0.85
- creative_impact: 0.9
- brazilian_scene_authenticity: 0.95
- commercial_readiness: 0.95
- photorealism_score: 0.98
- overall_score: 0.94
- Summary: The final output is an exceptional example of garment-centric AI editing. The crochet texture, stripe scale, and specific cocoon-like drape of the ruana are preserved with near-perfect fidelity. The model swap is complete and successful, featuring a distinct Brazilian aesthetic in a realistic cafe setting. The transition from the reference's casual styling to the edited version's professional catalog look is seamless.
