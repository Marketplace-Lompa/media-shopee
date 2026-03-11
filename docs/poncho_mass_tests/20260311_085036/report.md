# Poncho Mass Test Report

- Timestamp: 2026-03-11 08:52:58
- Reference folder: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste`
- Runs: 2

## Aggregate

- Overall fidelity avg: 0.815
- Silhouette fidelity avg: 0.775
- Texture fidelity avg: 0.925
- Model change avg: 1.000
- Pose catalog avg: 0.950
- Brazilian scene plausibility avg: 0.900
- Scene change avg: 1.000

## Runs

### Run 1

- Session: `8c50ca9f`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/8c50ca9f/gen_8c50ca9f_1.png`
- Overall fidelity: 0.750
- Silhouette: 0.700
- Texture: 0.900
- Construction: 0.750
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment introduces a more structured, jacket-like front edge compared to the raw, draped edge of the reference, The silhouette in the generated image appears more like a cardigan with defined armholes rather than the continuous draped panel/ruana construction of the original
- Summary: The generated image successfully captures the color palette and the specific crochet/knit stripe texture. However, it loses some of the 'ruana' essence by adding more structure to the front opening and making the sleeves look more like traditional set-in sleeves rather than a draped wrap.

Prompt:

```text
RAW photo, A fresh-faced Brasília native Vogue Brasil talent, features blend 'Nayara' and 'Juliana Ferreira' open-front ruana-wrap construction soft open front edge with uninterrupted drape hip length relative to model body draped fluid silhouette asymmetric hem single continuous body panel draped from shoulder to hem, with arm coverage formed by the same panel horizontal stripes knit texture open front pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible subtle 3/4 angle toward camera, weight on back foot, front panel clear exact texture, stitch, and fiber relief high-waist dark leggings, ankle boots polished model, natural expression engaging eye contact elegant open-air courtyard with dappled natural light and clean background subject sharp, background softly defocused, balanced natural light. Sony A7R IV, 50mm f/1.8 lens. Soft natural lighting with dappled shadows. Professional e-commerce realism, visible knit fiber texture, natural fabric drape, unretouched skin with visible pores.
```

### Run 2

- Session: `ec765e1a`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/ec765e1a/gen_ec765e1a_1.png`
- Overall fidelity: 0.880
- Silhouette: 0.850
- Texture: 0.950
- Construction: 0.800
- Model change: 1.000
- Pose catalog: 1.000
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment adds a more defined vertical collar/lapel band compared to the raw edge of the reference, The drape at the hips is slightly more structured than the original fluid wrap
- Summary: The generated image successfully captures the complex striped knit texture and the overall ruana-style construction. The model and scene are completely transformed into a professional catalog setting. The main deviation is a slightly more formal collar construction than the reference's simple draped edge.

Prompt:

```text
RAW photo, A contemporary Mineira Lança Perfume lookbook model, features blend 'Renata' and 'Bruna Macedo' open-front ruana-wrap construction soft open front edge with uninterrupted drape hip length relative to model body draped fluid silhouette asymmetric hem single continuous body panel draped from shoulder to hem, with arm coverage formed by the same panel horizontal stripes knit texture open front pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible gentle step forward, relaxed arms, confident gaze, garment fully visible exact texture, stitch, and fiber relief wide-leg cropped pants, simple flats polished model, natural expression warm near-camera look with relaxed expression serene home studio with large diffused window light and simple backdrop shallow depth of field, warm backlight rim, clean negative space. Sony A7III, 50mm f/1.8 lens. High-fidelity skin realism with visible natural pores and subtle texture. The knit fabric shows a dense, uniform gauge with natural wear creases where it drapes. Soft-focus background bokeh.
```
