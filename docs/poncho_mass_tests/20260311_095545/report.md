# Poncho Mass Test Report

- Timestamp: 2026-03-11 09:58:49
- Reference folder: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste`
- Runs: 2

## Aggregate

- Overall fidelity avg: 0.765
- Silhouette fidelity avg: 0.725
- Texture fidelity avg: 0.875
- Model change avg: 1.000
- Pose catalog avg: 0.950
- Brazilian scene plausibility avg: 0.950
- Scene change avg: 1.000

## Runs

### Run 1

- Session: `3250bfd5`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/3250bfd5/gen_3250bfd5_1.png`
- Overall fidelity: 0.650
- Silhouette: 0.600
- Texture: 0.800
- Construction: 0.600
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 1.000
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": true, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": true}`
- Failures: The generated garment introduces a structured lapel/collar that is not present in the original cocoon wrap, The sleeve architecture changed from a continuous draped panel to a more defined set-in sleeve look, The generated garment features pockets which are absent in the reference
- Summary: The generated image captures the color palette and stripe pattern well, but fails on the specific construction of the cocoon wrap. It has transformed a simple draped shawl/wrap into a more structured cardigan with lapels and pockets, losing the unique batwing/continuous panel silhouette of the original piece.

Prompt:

```text
RAW photo, A chic Paulistana editorial beauty, features blend 'Camila' and 'Isadora Ribeiro' Wearing Textured draped knit wrap with alternating olive and dusty rose stripes. Features a draped cocoon silhouette, soft open front edge, and fluid draped arm coverage with a soft, airy open-stitch construction front panel fully open and draping waist length relative to model body draped fluid silhouette cocoon hem batwing/dolman sleeve volume elbow-length sleeves continuous neckline-to-front edge rounded cocoon side drop wide batwing arm opening preserve garment geometry: opening behavior, sleeve architecture, hem shape, garment length pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible contrapposto hip shift, relaxed shoulders, catalog-clean front reveal exact texture, stitch, and fiber relief upscale shopping district at golden hour with blurred storefronts polished model, natural expression engaging eye contact dappled natural light revealing fabric texture and depth wide-leg cropped pants, simple flats even soft light, gentle bokeh background, centered composition. Sony A7III, 85mm f/1.8 lens. Golden hour rim lighting, soft natural shadows. Visible natural skin pores, subtle peach fuzz, and realistic fabric tension with natural wear creases. subtle film grain and mild lens halation.
```

### Run 2

- Session: `bf5a2a28`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/bf5a2a28/gen_bf5a2a28_1.png`
- Overall fidelity: 0.880
- Silhouette: 0.850
- Texture: 0.950
- Construction: 0.800
- Model change: 1.000
- Pose catalog: 1.000
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": true, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment has a slightly more structured front edge compared to the raw draped edge of the reference, The cocoon taper at the hem is slightly more pronounced in the AI version than the reference
- Summary: The AI successfully captured the complex knit texture and the specific olive/rose stripe pattern. The silhouette is very close, maintaining the batwing/cocoon shape, though it adds a slightly more defined 'border' to the front opening that isn't as prominent in the original. The model and scene are completely transformed into a professional catalog aesthetic.

Prompt:

```text
RAW photo, A fresh-faced Brasília native editorial model, features blend 'Nayara' and 'Juliana Ferreira' Wearing Horizontal draped knit wrap in olive green and dusty rose. Features an open-weave texture, fluid draped arm coverage, and a draped chrysalis silhouette that tapers at the waist front panel fully open and draping waist length relative to model body draped fluid silhouette cocoon hem batwing/dolman sleeve volume elbow-length sleeves continuous neckline-to-front edge rounded cocoon side drop wide batwing arm opening preserve garment geometry: opening behavior, sleeve architecture, hem shape, garment length pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible gentle step forward, relaxed arms, confident gaze, garment fully visible exact texture, stitch, and fiber relief serene home studio with large diffused window light and simple backdrop polished model, natural expression direct confident gaze at camera dappled natural light revealing fabric texture and depth fitted dark trousers, minimal footwear shallow depth of field, warm backlight rim, clean negative space. Sony A7R IV, 85mm f/1.8 lens, soft natural window light. High realism with visible natural skin pores, subtle peach fuzz, and intricate yarn fiber definition showing realistic fabric tension. subtle film grain and mild lens halation.
```
