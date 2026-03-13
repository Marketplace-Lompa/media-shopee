# Autotest V2 Report

- **Timestamp:** 2026-03-11 22:45:38
- **References:** `../../docs/roupa-referencia-teste` (1 runs)
- **Preset:** catalog_clean
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
| construction_fidelity | 0.95 | 0.95 | 0.95 |  |
| model_change_strength | 1.00 | 1.00 | 1.00 | 100% |
| environment_change_strength | 1.00 | 1.00 | 1.00 | 100% |
| innerwear_change_strength | 1.00 | 1.00 | 1.00 |  |
| pose_vitality | 0.40 | 0.40 | 0.40 | 0% |
| creative_impact | 0.70 | 0.70 | 0.70 | 100% |
| brazilian_scene_authenticity | 0.60 | 0.60 | 0.60 | 0% |
| commercial_readiness | 0.85 | 0.85 | 0.85 |  |
| photorealism_score | 0.90 | 0.90 | 0.90 |  |
| overall_score | 0.82 | 0.82 | 0.82 |  |

## Corrections Applied

| Run | Metric | Score | Action |
|-----|--------|-------|--------|
| 1 | pose_vitality | 0.4 | boost pose_vitality |
| 1 | brazilian_scene_authenticity | 0.6 | boost scene_authenticity |

## Diversity Analysis

| Dimension | Unique | Pool | Coverage |
|-----------|--------|------|----------|
| casting_family | 1 | 5 | 20% |
| scene_family | 1 | 4 | 25% |
| pose_family | 1 | 4 | 25% |
| camera_profile | 1 | 3 | 33% |
| lighting_profile | 1 | 5 | 20% |
| styling_profile | 1 | 3 | 33% |

**Overall diversity score:** 26.1%

## Individual Runs

### Run 1
- Session: `5d84883b`
- Elapsed: 136.4s
- Art direction: casting=br_afro_modern, scene=br_showroom_sp, pose=front_relaxed_hold, camera=canon_balanced
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
- Issues: pose_is_stiff_and_mannequin_like
- Summary: The pipeline successfully preserved the complex striped crochet texture and the specific cocoon-like construction of the ruana. The model change is absolute, meeting the prompt's requirement for a Brazilian woman with short curls. While the image is commercially ready and photorealistic, the pose is quite static and the environment feels like a generic studio rather than a specific Brazilian location.
