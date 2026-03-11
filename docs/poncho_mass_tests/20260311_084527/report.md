# Poncho Mass Test Report

- Timestamp: 2026-03-11 08:48:18
- Reference folder: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste`
- Runs: 2

## Aggregate

- Overall fidelity avg: 0.675
- Silhouette fidelity avg: 0.675
- Texture fidelity avg: 0.825
- Model change avg: 0.800
- Pose catalog avg: 0.900
- Brazilian scene plausibility avg: 0.850
- Scene change avg: 1.000

## Runs

### Run 1

- Session: `979f05a2`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/979f05a2/gen_979f05a2_1.png`
- Overall fidelity: 0.500
- Silhouette: 0.500
- Texture: 0.700
- Construction: 0.400
- Model change: 0.900
- Pose catalog: 0.900
- BR scene plausibility: 0.800
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": true}`
- Failures: The generated garment has a structured cardigan/jacket opening with lapel-like edges not present in the reference, The stripe direction is altered from horizontal to a chevron/diagonal pattern at the front, The continuous draped panel construction of the original ruana is lost in favor of a more traditional sweater-jacket silhouette
- Summary: The generated image fails to capture the unique construction of the reference garment. While the colors and knit texture are similar, the original is a draped ruana/wrap with a continuous panel, whereas the AI generated a structured cardigan with distinct lapels and a different stripe orientation.

Prompt:

```text
RAW photo, An elegant Sulista high-end commercial beauty, features blend 'Sofia' and 'Aline Gomes' open-front ruana-wrap construction soft open front edge with uninterrupted drape hip length relative to model body draped fluid silhouette asymmetric hem single continuous body panel draped from shoulder to hem, with arm coverage formed by the same panel horizontal stripes knit texture open front pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible balanced frontal stance, arms natural, garment front fully readable exact texture, stitch, and fiber relief fitted dark trousers, minimal footwear polished model, natural expression engaging eye contact upscale shopping district at golden hour with blurred storefronts shallow depth of field, warm backlight rim, clean negative space. Shot on Sony A7III, 85mm f/1.8 lens. Golden hour rim light, soft bokeh with blurred storefronts. Natural unretouched skin realism with visible pores and subtle peach fuzz. Fabric shows natural movement and weave texture.
```

### Run 2

- Session: `5fe71a23`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/5fe71a23/gen_5fe71a23_1.png`
- Overall fidelity: 0.850
- Silhouette: 0.850
- Texture: 0.950
- Construction: 0.800
- Model change: 0.700
- Pose catalog: 0.900
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated model's facial features still retain significant resemblance to the reference person, The construction of the front edge is slightly more structured/hemmed than the raw crochet edge of the reference
- Summary: The garment fidelity is high, particularly in the reproduction of the specific green and pink striped crochet texture. The silhouette correctly captures the ruana-style drape rather than a structured cardigan. The model change is moderate but could be more distinct.

Prompt:

```text
RAW photo, A contemporary Mineira Lança Perfume lookbook model, features blend 'Renata' and 'Bruna Macedo' open-front ruana-wrap construction soft open front edge with uninterrupted drape hip length relative to model body draped fluid silhouette asymmetric hem single continuous body panel draped from shoulder to hem, with arm coverage formed by the same panel horizontal stripes knit texture open front pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible contrapposto hip shift, relaxed shoulders, catalog-clean front reveal exact texture, stitch, and fiber relief wide-leg cropped pants, simple flats polished model, natural expression warm near-camera look with relaxed expression light-filled modern loft with white walls and natural wood floor even soft light, gentle bokeh background, centered composition. Shot on Sony A7III, 50mm f/1.8 lens. Natural soft light from large windows. Realistic skin texture with visible pores and subtle natural tone variations. The knit fabric shows realistic drape and natural fiber detail.
```
