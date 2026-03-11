# Poncho Mass Test Report

- Timestamp: 2026-03-11 09:40:43
- Reference folder: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste`
- Runs: 2

## Aggregate

- Overall fidelity avg: 0.690
- Silhouette fidelity avg: 0.625
- Texture fidelity avg: 0.875
- Model change avg: 1.000
- Pose catalog avg: 0.900
- Brazilian scene plausibility avg: 0.900
- Scene change avg: 1.000

## Runs

### Run 1

- Session: `223858c4`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/223858c4/gen_223858c4_1.png`
- Overall fidelity: 0.500
- Silhouette: 0.400
- Texture: 0.800
- Construction: 0.500
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment has set-in sleeves which do not exist in the reference, The reference is a continuous draped wrap/ruana, while the output is a structured cardigan, The stripe orientation on the sleeves is horizontal in the output but diagonal/draped in the reference
- Summary: The AI successfully captured the color palette and crochet texture, but failed significantly on the garment's construction. It transformed a draped, single-panel ruana/wrap into a standard set-in sleeve cardigan, which fundamentally changes the silhouette and design intent.

Prompt:

```text
RAW photo, A radiant Baiana Ford Models Brazil new face, features blend 'Dandara' and 'Taís Costa' Wearing Textured horizontal stripes of olive green and dusty rose in a flat-weave crochet. Oversized cocoon silhouette with fluid draped arm coverage, draping softly with a knit weight She is wearing a single-piece ruana wrap draped over the shoulders. The same knitted edge flows from the neckline directly into the soft front opening. The outer silhouette falls in a rounded cocoon side drop reaching upper-thigh length relative to the model body. Arm coverage is created by the same continuous body panel as the garment, forming a fluid draped wrap over the arms. continuous neckline-to-front edge rounded cocoon side drop ribbed texture stripes pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible balanced frontal stance, arms natural, garment front fully readable exact texture, stitch, and fiber relief bright minimalist apartment with neutral decor and clean background polished model, natural expression warm near-camera look with relaxed expression dappled natural light revealing fabric texture and depth slim straight jeans, clean white sneakers. Sony A7III, 50mm f/1.8 lens. Natural daylight from a large window creates soft shadows. Visible fabric fiber detail and natural skin texture with subtle pores and realistic light falloff.
```

### Run 2

- Session: `b5660ef5`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/b5660ef5/gen_b5660ef5_1.png`
- Overall fidelity: 0.880
- Silhouette: 0.850
- Texture: 0.950
- Construction: 0.800
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment features a more structured, vertical front placket/edge compared to the more fluid, draped opening of the reference, The rounded hem in the generated image is slightly more symmetrical and coat-like than the original wrap
- Summary: The generated image successfully captures the unique crochet texture and the specific olive/rose stripe pattern of the reference. The silhouette is largely accurate, maintaining the cocoon-like drape and continuous arm coverage, though it introduces a slightly more formal front edge construction than the original handmade piece.

Prompt:

```text
RAW photo, A striking Northeastern São Paulo Fashion Week talent, features blend 'Yasmin' and 'Letícia Souza' Wearing draped knit wrap in olive and dusty rose stripes. Flat uniform crochet construction with visible horizontal rows. Voluminous fluid draped arm coverage and draped open-front silhouette with a soft, rounded hem She is wearing a single-piece ruana wrap draped over the shoulders. The same knitted edge flows from the neckline directly into the soft front opening. The outer silhouette falls in a rounded cocoon side drop reaching upper-thigh length relative to the model body. Arm coverage is created by the same continuous body panel as the garment, forming a fluid draped wrap over the arms. continuous neckline-to-front edge rounded cocoon side drop ribbed edge finish pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible slight body turn with direct eye contact, clean garment silhouette exact texture, stitch, and fiber relief bright modern downtown with clean architecture and soft depth of field polished model, natural expression direct confident gaze at camera dappled natural light revealing fabric texture and depth wide-leg cropped pants, simple flats. Sony A7III, 85mm f/1.8. Natural daylight casting soft shadows, shallow depth of field. visible natural pores. Fabric responding naturally to movement with visible fiber texture and weave definition.
```
