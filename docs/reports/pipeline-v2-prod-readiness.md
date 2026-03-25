# Pipeline V2 Prod Readiness

Date: 2026-03-13

## Goal

Capture the exact fine-tuning help that had to be applied during the Nano Banana 2 pipeline refinement, and convert that help into explicit system rules, production defaults, and release gates.

This document answers:

1. What did a human still have to "help" the pipeline do?
2. Which of those interventions have already been absorbed into the system?
3. What still remains partially manual before full production autonomy?

## Human Help -> System Rule

| Human help needed | Why it was needed | System rule added | Main code |
| --- | --- | --- | --- |
| Distinguish creative direction from hard garment fidelity | The pipeline was still describing too much of the final scene/pose instead of letting the model create | Stage 2 now uses open creative briefs for scene/pose, but keeps garment structure locked | `app/backend/agent_runtime/two_pass_flow.py` |
| Prevent face cloning from references | The model still drifted toward copying identity | References are explicitly garment-only; identity transfer is a hard failure | `app/backend/agent_runtime/two_pass_flow.py` |
| Prevent repetitive casting energy | Good outputs were clustering around similar hair/face energy | Casting anti-repeat and affinity were strengthened | `app/backend/agent_runtime/casting_engine.py` |
| Prevent "stock-photo cheerfulness" | More open prompts were producing generic smiling lifestyle shots | Style brief now suppresses stock-photo energy, props, and exaggerated friendliness | `app/backend/agent_runtime/two_pass_flow.py` |
| Lock ruana macro silhouette | The ruana kept drifting in hem logic, side drop, and opening continuity | Added `edge_contour`, `drop_profile`, and `opening_continuity` to the structural contract | `app/backend/agent_runtime/constants.py`, `app/backend/agent_runtime/triage.py`, `app/backend/agent_runtime/structural.py` |
| Separate border texture from outer contour | Crochet trim was being misread as a macro undulating silhouette | Triage and normalization now distinguish micro edge texture from macro outline | `app/backend/agent_runtime/triage.py`, `app/backend/agent_runtime/structural.py` |
| Prevent false sleeves/slits on draped wraps | The model could reinterpret draped wraps as sewn sleeves | Specialized draped-wrap structural guards and repair patches were added | `app/backend/agent_runtime/two_pass_flow.py`, `app/backend/agent_runtime/fidelity_gate.py` |
| Prevent inner-layer hallucination on closed-front tops | Closed pullovers could receive a visible undershirt/collar in stage 2 | Closed-neckline guard blocks visible undershirt/layered necklines when `front_opening=closed` | `app/backend/agent_runtime/two_pass_flow.py` |
| Retry when creativity damaged garment fidelity | Good art direction could still preserve the wrong garment | Visual gate and fidelity repair loop now run inside the official job flow | `app/backend/agent_runtime/fidelity_gate.py`, `app/backend/agent_runtime/pipeline_v2.py` |
| Audit the result inside the application | "Looks good" was previously too manual | Review bundle and app review panel now expose the official job audit | `app/backend/review_engine.py`, `app/backend/routers/review.py`, `app/frontend/src/components/ReviewPanel.tsx` |

## Golden Cases

### 1. Ruana Wrap

Reference family:
- `docs/roupa-referencia-teste/*`

Golden sessions:
- `6313a5f7`
- `456ed631`

Why they matter:
- validated draped piece fidelity
- validated `soft_curve`, `side_drop` / `cocoon_side_drop`
- validated continuous opening
- validated scarf/set preservation when anchors were clear

Winning behavior:
- `preset=premium_lifestyle`
- `fidelity_mode=estrita`
- `pose_flex_mode=balanced`
- open scene/pose creativity
- hard garment structure

### 2. Fitted Textured Pullover

Reference family:
- `/Users/lompa-marketplace/Documents/Ecommerce/Shopee/blusa modal textura/*`

Golden sessions:
- `7d1a2b7d`
- `fe31ca59`

Why they matter:
- validated a non-draped, closed-front, fitted knit top
- validated mock neck, cuffs, hem, waist length
- validated geometric front texture preservation
- validated the closed-neckline guard

Winning behavior:
- `preset=premium_lifestyle`
- `scene_preference=indoor_br`
- `fidelity_mode=estrita`
- `pose_flex_mode=balanced`
- no visible undershirt for closed-neck pieces

## What Is Still Partially Manual

These items are better than before, but not yet fully autonomous:

1. Reference pack curation
- The system performs better when the pack includes:
  - 1 strong frontal anchor
  - 1 oblique or side anchor
  - 1 detail anchor when texture matters
- A human still picks the "best" pack more reliably than the system in edge cases.

2. Aesthetic ranking of "gold"
- The gate is now reliable for structural fidelity.
- The final judgment of "premium enough to be gold" still has some human taste involved.

3. Scene preference as a hard rule
- `scene_preference` is still soft guidance in the art-direction layer.
- This is acceptable for controlled rollout, but not yet a strict production policy.

## Production Defaults By Garment Family

### Draped Wraps (`ruana_wrap`, `cape_like`)

Recommended defaults:
- `preset=premium_lifestyle`
- `fidelity_mode=estrita`
- `pose_flex_mode=balanced`

Required structural emphasis:
- `edge_contour`
- `drop_profile`
- `opening_continuity`

Reference pack recommendation:
- 1 frontal worn reference
- 1 side/oblique worn reference
- 1 detail or set anchor

### Closed-Front Fitted Knit Tops (`pullover`, textured modal knit)

Recommended defaults:
- `preset=premium_lifestyle`
- `scene_preference=indoor_br`
- `fidelity_mode=estrita`
- `pose_flex_mode=balanced`

Required structural emphasis:
- neckline integrity
- cuff and hem ribbing
- fitted silhouette
- front texture panel logic

Reference pack recommendation:
- 1 frontal worn reference
- 1 oblique worn reference
- 1 close-up texture anchor when available

## Release Checklist

The flow is ready for a controlled production rollout when all items below hold:

1. Structural contract is coherent
- subtype, sleeve logic, hem logic, and opening logic all match the garment family

2. Stage-2 does not break stage-1 fidelity
- retries are acceptable
- the final selected result must pass the visual gate

3. Closed-front pieces show no false inner collar

4. Draped pieces preserve macro contour
- no invented waviness
- no false sleeves
- no false slits

5. Textured pieces preserve front-panel logic
- relief can soften slightly
- pattern logic must remain intact

6. Model identity is clearly new
- no reference face cloning

7. The result is premium enough to be merchandisable
- commercial readability
- garment remains the hero
- scene does not dominate the frame

## Current Assessment

Status: ready for controlled production rollout

Rationale:
- validated on draped wrap family
- validated on fitted textured pullover family
- key structural failure modes are now explicitly modeled
- the main remaining gap is reference-pack autonomy, not core fidelity behavior

## Recommended Next Step

Move forward with:

1. controlled prod rollout
2. monitoring via review bundle
3. one more garment-family validation only if the rollout scope expands beyond knitwear / soft apparel
