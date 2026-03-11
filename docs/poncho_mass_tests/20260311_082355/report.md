# Poncho Mass Test Report

- Timestamp: 2026-03-11 08:27:31
- Reference folder: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste`
- Runs: 3

## Aggregate

- Overall fidelity avg: 0.817
- Silhouette fidelity avg: 0.800
- Texture fidelity avg: 0.883
- Model change avg: 1.000
- Pose catalog avg: 0.933
- Brazilian scene plausibility avg: 0.833
- Scene change avg: 1.000

## Runs

### Run 1

- Session: `8105c3d0`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/8105c3d0/gen_8105c3d0_1.png`
- Overall fidelity: 0.700
- Silhouette: 0.700
- Texture: 0.800
- Construction: 0.600
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": true, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: stripe orientation changed from horizontal/diagonal to vertical, sleeve construction changed from a continuous draped panel to a more defined set-in sleeve look, drape behavior is stiffer in the generated image compared to the fluid reference
- Summary: The generated garment maintains the knit texture and color palette well, but fails significantly on the stripe orientation, which is vertical in the output instead of horizontal. The silhouette is also more structured and less 'poncho-like' than the original.

Prompt:

```text
RAW photo, A striking Brazilian model with a Northeastern vibe, her facial features a beautiful natural blend reminiscent of 'Marina' and 'Valentina Gomes' She is wearing an oversized front panel fully open and draping hip length relative to model body draped fluid silhouette straight hem arm coverage from a continuous draped panel horizontal stripes knit texture pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible gentle step forward, relaxed arms, confident gaze, garment fully visible exact texture, stitch, and fiber relief fitted dark trousers, minimal footwear polished model, natural expression warm near-camera look with relaxed expression bright minimalist apartment with neutral decor and clean background golden hour side light, subject crisp, environment blurred, interior setting. Sony A7III, 85mm f/1.8. Natural daylight from a large window, soft shadows. Focus on fabric grain and knit intersections. Unretouched skin texture with visible pores.
```

### Run 2

- Session: `f2657de8`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/f2657de8/gen_f2657de8_1.png`
- Overall fidelity: 0.900
- Silhouette: 0.900
- Texture: 0.950
- Construction: 0.850
- Model change: 1.000
- Pose catalog: 1.000
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": true, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment has a slightly more structured shawl collar than the reference, The drape at the hem is more rounded in the generation compared to the flatter reference hem
- Summary: The AI successfully captured the complex horizontal stripe pattern and the specific knit texture of the crochet-style cardigan. The silhouette is largely preserved, though the generated version appears slightly more tailored around the neck. The model and scene transition are excellent for a commercial catalog look.

Prompt:

```text
RAW photo, a sophisticated Carioca São Paulo Fashion Week casting aesthetic model, her facial features are a beautiful natural blend reminiscent of 'Bruna' and 'Letícia Ferreira' She is front panel fully open and draping hip length relative to model body draped fluid silhouette straight hem arm coverage from a continuous draped panel horizontal stripes knit texture preserve garment geometry: opening behavior, sleeve architecture, hem shape, garment length pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible slight body turn with direct eye contact, clean garment silhouette exact texture, stitch, and fiber relief high-waist dark leggings, ankle boots polished model, natural expression engaging eye contact cozy premium cafe terrace with tidy warm-lit composition shallow depth of field, warm backlight rim, clean negative space. Sony A7R IV, 50mm f/1.8 lens, soft natural morning light, visible fabric fiber texture, natural skin pores and subtle peach fuzz, shallow depth of field with blurred architectural background.
```

### Run 3

- Session: `b41fa693`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/b41fa693/gen_b41fa693_1.png`
- Overall fidelity: 0.850
- Silhouette: 0.800
- Texture: 0.900
- Construction: 0.850
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 0.700
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": true, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment has a more structured, blazer-like collar/lapel compared to the simple draped edge of the original, The stripe orientation on the front panels is horizontal in the generation but diagonal/chevron-like in the reference
- Summary: The AI successfully captured the knit texture and color palette of the striped cardigan. While the overall silhouette is preserved, the generation introduced a more formal lapel structure and changed the stripe direction on the front panels from diagonal to horizontal.

Prompt:

```text
RAW photo, an elegant Sulista Vogue Brasil editorial talent, her facial features are a beautiful natural blend reminiscent of Taís and Dandara Ferreira. front panel fully open and draping hip length relative to model body draped fluid silhouette straight hem arm coverage from a continuous draped panel horizontal stripes knit texture preserve garment geometry: opening behavior, sleeve architecture, hem shape, garment length pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible balanced frontal stance, arms natural, garment front fully readable exact texture, stitch, and fiber relief fitted dark trousers, minimal footwear polished model, natural expression warm near-camera look with relaxed expression upscale fashion showroom with neutral white background and diffused light golden hour side light, subject crisp, environment blurred, interior setting. Sony A7III, 85mm f/1.8 lens, visible natural pores, fabric responding to gravity with natural wear creases, soft bokeh. subtle film grain and mild lens halation.
```
