# Autotest V2 Report

- **Timestamp:** 2026-03-11 22:18:05
- **References:** `../../docs/roupa-referencia-teste` (3 runs)
- **Preset:** catalog_clean
- **Scene:** auto_br
- **Fidelity:** balanceada
- **Self-correction:** ON
- **Corrections applied:** 2

## Aggregate Scores

| Metric | Avg | Min | Max | Pass Rate |
|--------|-----|-----|-----|-----------|
| garment_fidelity | 0.93 | 0.92 | 0.95 | 100% |
| silhouette_fidelity | 0.89 | 0.88 | 0.90 |  |
| texture_fidelity | 0.94 | 0.92 | 0.95 |  |
| construction_fidelity | 0.92 | 0.90 | 0.95 |  |
| model_change_strength | 1.00 | 1.00 | 1.00 | 100% |
| environment_change_strength | 0.98 | 0.95 | 1.00 | 100% |
| innerwear_change_strength | 0.97 | 0.90 | 1.00 |  |
| pose_vitality | 0.68 | 0.60 | 0.85 | 33% |
| creative_impact | 0.85 | 0.80 | 0.90 | 100% |
| brazilian_scene_authenticity | 0.85 | 0.70 | 0.95 | 100% |
| commercial_readiness | 0.93 | 0.90 | 0.95 |  |
| photorealism_score | 0.97 | 0.95 | 0.98 |  |
| overall_score | 0.92 | 0.89 | 0.94 |  |

## Self-Correction Effectiveness

| Metric | First Half | Second Half | Delta |
|--------|-----------|-------------|-------|
| garment_fidelity | 0.92 | 0.94 | +0.02 |
| silhouette_fidelity | 0.88 | 0.89 | +0.01 |
| texture_fidelity | 0.95 | 0.94 | -0.01 |
| construction_fidelity | 0.90 | 0.93 | +0.03 |
| model_change_strength | 1.00 | 1.00 | +0.00 |
| environment_change_strength | 0.95 | 1.00 | +0.05 |
| innerwear_change_strength | 1.00 | 0.95 | -0.05 |
| pose_vitality | 0.60 | 0.72 | +0.12 |
| creative_impact | 0.80 | 0.88 | +0.07 |
| brazilian_scene_authenticity | 0.70 | 0.93 | +0.23 |
| commercial_readiness | 0.90 | 0.95 | +0.05 |
| photorealism_score | 0.95 | 0.98 | +0.03 |
| overall_score | 0.89 | 0.93 | +0.04 |

## Corrections Applied

| Run | Metric | Score | Action |
|-----|--------|-------|--------|
| 1 | pose_vitality | 0.6 | boost pose_vitality |
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
- Session: `f974cc3d`
- Elapsed: 136.3s
- Art direction: casting=br_soft_editorial, scene=br_showroom_sp, pose=front_relaxed_hold, camera=canon_balanced
- garment_fidelity: 0.92
- silhouette_fidelity: 0.88
- texture_fidelity: 0.95
- construction_fidelity: 0.9
- model_change_strength: 1.0
- environment_change_strength: 0.95
- innerwear_change_strength: 1.0
- pose_vitality: 0.6 **LOW**
- creative_impact: 0.8
- brazilian_scene_authenticity: 0.7
- commercial_readiness: 0.9
- photorealism_score: 0.95
- overall_score: 0.89
- Summary: The final output successfully preserves the complex crochet texture and stripe pattern of the original ruana. The model swap is complete and effective, featuring a distinct Brazilian aesthetic as requested. The silhouette maintains the cocoon-like drape and cape-style arm coverage, though the pose remains somewhat static. The transition from the reference's casual styling to a clean, editorial look is professionally executed.

### Run 2
- Session: `ed0011c8`
- Elapsed: 137.3s
- Art direction: casting=br_warm_commercial, scene=br_pinheiros_living, pose=standing_full_shift, camera=phone_clean
- garment_fidelity: 0.92
- silhouette_fidelity: 0.88
- texture_fidelity: 0.95
- construction_fidelity: 0.9
- model_change_strength: 1.0
- environment_change_strength: 1.0
- innerwear_change_strength: 0.9
- pose_vitality: 0.6 **LOW**
- creative_impact: 0.85
- brazilian_scene_authenticity: 0.9
- commercial_readiness: 0.95
- photorealism_score: 0.98
- overall_score: 0.92
- Summary: The pipeline successfully translated the crochet ruana/wrap into a high-end commercial catalog image. The texture fidelity is exceptional, capturing the specific stitch pattern and stripe scale of the original. The model swap is complete and follows the art direction for a Brazilian aesthetic. The silhouette correctly maintains the cocoon-like drape and cape-style arm coverage. The final image is highly photorealistic and ready for a premium marketplace.

### Run 3
- Session: `15afbaba`
- Elapsed: 135.8s
- Art direction: casting=br_minimal_premium, scene=br_curitiba_cafe, pose=paused_mid_step, camera=fujifilm_candid
- garment_fidelity: 0.95
- silhouette_fidelity: 0.9
- texture_fidelity: 0.92
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
- Summary: The pipeline successfully transformed a casual home photo into a high-end commercial asset. The garment's unique crochet stripe pattern and cocoon silhouette were preserved with high fidelity. The model swap is complete and the final environment (a Brazilian-style cafe) feels authentic and professionally lit. The transition from the reference's black tank top to a white tee in the final edit was executed perfectly.
