# Autotest V2 Report

- **Timestamp:** 2026-03-11 22:08:50
- **References:** `../../docs/roupa-referencia-teste` (3 runs)
- **Preset:** marketplace_lifestyle
- **Scene:** auto_br
- **Fidelity:** balanceada
- **Self-correction:** ON
- **Corrections applied:** 2

## Aggregate Scores

| Metric | Avg | Min | Max | Pass Rate |
|--------|-----|-----|-----|-----------|
| garment_fidelity | 0.95 | 0.95 | 0.95 | 100% |
| silhouette_fidelity | 0.90 | 0.90 | 0.90 |  |
| texture_fidelity | 0.92 | 0.92 | 0.92 |  |
| construction_fidelity | 0.97 | 0.95 | 1.00 |  |
| model_change_strength | 1.00 | 1.00 | 1.00 | 100% |
| environment_change_strength | 1.00 | 1.00 | 1.00 | 100% |
| innerwear_change_strength | 1.00 | 1.00 | 1.00 |  |
| pose_vitality | 0.67 | 0.60 | 0.80 | 33% |
| creative_impact | 0.85 | 0.85 | 0.85 | 100% |
| brazilian_scene_authenticity | 0.92 | 0.90 | 0.95 | 100% |
| commercial_readiness | 0.93 | 0.90 | 0.95 |  |
| photorealism_score | 0.94 | 0.92 | 0.98 |  |
| overall_score | 0.92 | 0.91 | 0.92 |  |

## Self-Correction Effectiveness

| Metric | First Half | Second Half | Delta |
|--------|-----------|-------------|-------|
| garment_fidelity | 0.95 | 0.95 | +0.00 |
| silhouette_fidelity | 0.90 | 0.90 | +0.00 |
| texture_fidelity | 0.92 | 0.92 | +0.00 |
| construction_fidelity | 0.95 | 0.97 | +0.03 |
| model_change_strength | 1.00 | 1.00 | +0.00 |
| environment_change_strength | 1.00 | 1.00 | +0.00 |
| innerwear_change_strength | 1.00 | 1.00 | +0.00 |
| pose_vitality | 0.60 | 0.70 | +0.10 |
| creative_impact | 0.85 | 0.85 | +0.00 |
| brazilian_scene_authenticity | 0.95 | 0.90 | -0.05 |
| commercial_readiness | 0.90 | 0.95 | +0.05 |
| photorealism_score | 0.92 | 0.95 | +0.03 |
| overall_score | 0.91 | 0.92 | +0.01 |

## Corrections Applied

| Run | Metric | Score | Action |
|-----|--------|-------|--------|
| 1 | pose_vitality | 0.6 | boost pose_vitality |
| 3 | pose_vitality | 0.6 | boost pose_vitality |

## Diversity Analysis

| Dimension | Unique | Pool | Coverage |
|-----------|--------|------|----------|
| casting_family | 3 | 5 | 60% |
| scene_family | 3 | 4 | 75% |
| pose_family | 3 | 4 | 75% |
| camera_profile | 3 | 3 | 100% |
| lighting_profile | 3 | 5 | 60% |
| styling_profile | 3 | 3 | 100% |

**Overall diversity score:** 78.3%

## Individual Runs

### Run 1
- Session: `a6a4ac9d`
- Elapsed: 130.1s
- Art direction: casting=br_mature_elegant, scene=br_recife_balcony, pose=standing_3q_relaxed, camera=phone_clean
- garment_fidelity: 0.95
- silhouette_fidelity: 0.9
- texture_fidelity: 0.92
- construction_fidelity: 0.95
- model_change_strength: 1.0
- environment_change_strength: 1.0
- innerwear_change_strength: 1.0
- pose_vitality: 0.6 **LOW**
- creative_impact: 0.85
- brazilian_scene_authenticity: 0.95
- commercial_readiness: 0.9
- photorealism_score: 0.92
- overall_score: 0.91
- Summary: The final output is a highly successful transformation. The garment's unique ruana/cocoon construction and striped crochet texture are preserved with exceptional fidelity. The model swap is complete and follows the prompt's specific age and ethnicity requirements perfectly. The Brazilian balcony setting feels authentic and provides a high-end lifestyle context that significantly improves upon the base generation's studio feel.

### Run 2
- Session: `483876c7`
- Elapsed: 138.2s
- Art direction: casting=br_warm_commercial, scene=br_curitiba_cafe, pose=paused_mid_step, camera=fujifilm_candid
- garment_fidelity: 0.95
- silhouette_fidelity: 0.9
- texture_fidelity: 0.92
- construction_fidelity: 0.95
- model_change_strength: 1.0
- environment_change_strength: 1.0
- innerwear_change_strength: 1.0
- pose_vitality: 0.8
- creative_impact: 0.85
- brazilian_scene_authenticity: 0.9
- commercial_readiness: 0.95
- photorealism_score: 0.92
- overall_score: 0.92
- Summary: The final output is a high-quality commercial image that successfully translates the reference ruana wrap into a lifestyle context. The garment's unique striped crochet texture and cocoon silhouette are preserved with high fidelity. The model swap is complete and effective, and the cafe environment feels authentic to a modern Brazilian urban setting.

### Run 3
- Session: `d3e6e107`
- Elapsed: 145.7s
- Art direction: casting=br_soft_editorial, scene=br_pinheiros_living, pose=standing_full_shift, camera=canon_balanced
- garment_fidelity: 0.95
- silhouette_fidelity: 0.9
- texture_fidelity: 0.92
- construction_fidelity: 1.0
- model_change_strength: 1.0
- environment_change_strength: 1.0
- innerwear_change_strength: 1.0
- pose_vitality: 0.6 **LOW**
- creative_impact: 0.85
- brazilian_scene_authenticity: 0.9
- commercial_readiness: 0.95
- photorealism_score: 0.98
- overall_score: 0.92
- Summary: The final output is a high-quality commercial image that perfectly preserves the identity of the crochet ruana. The stripe scale, stitch texture, and cocoon silhouette are maintained with high precision. The model swap is complete and successful, and the environment feels like an authentic, high-end Brazilian apartment. The pose is a standard catalog stance, which is appropriate for commercial readiness but lacks high dynamism.
