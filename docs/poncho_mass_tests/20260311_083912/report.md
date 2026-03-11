# Poncho Mass Test Report

- Timestamp: 2026-03-11 08:41:22
- Reference folder: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste`
- Runs: 2

## Aggregate

- Overall fidelity avg: 0.625
- Silhouette fidelity avg: 0.600
- Texture fidelity avg: 0.825
- Model change avg: 0.650
- Pose catalog avg: 0.925
- Brazilian scene plausibility avg: 0.850
- Scene change avg: 1.000

## Runs

### Run 1

- Session: `5e4c68ae`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/5e4c68ae/gen_5e4c68ae_1.png`
- Overall fidelity: 0.600
- Silhouette: 0.600
- Texture: 0.800
- Construction: 0.500
- Model change: 0.400
- Pose catalog: 0.900
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment has a structured collar/lapel edge that does not exist in the reference, The sleeve construction changed from a continuous draped panel to more defined, set-in style sleeves, The model's facial features still bear a strong resemblance to the reference person
- Summary: The generated image captures the color palette and stripe pattern well, but fails on the construction of the ruana. It introduces a folded lapel and more structured shoulder/sleeve architecture, whereas the reference is a simple, continuous draped panel. The model's face is too similar to the original subject.

Prompt:

```text
RAW photo, a fresh-faced Brasília native Vogue Brasil talent, her facial features are open-front ruana-wrap construction soft open front edge with uninterrupted drape hip length relative to model body draped fluid silhouette asymmetric hem single continuous body panel draped from shoulder to hem, with arm coverage formed by the same panel horizontal stripes textured knit open front pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible balanced frontal stance, arms natural, garment front fully readable exact texture, stitch, and fiber relief high-waist dark leggings, ankle boots polished model, natural expression warm near-camera look with relaxed expression lush botanical garden path with gentle backlight and soft greenery shallow depth of field, warm backlight rim, clean negative space, outdoor setting. Sony A7R IV, 85mm f/1.8 lens. Soft depth of field with creamy bokeh. Natural unretouched skin realism showing subtle pores and peach fuzz. Fabric realism captures the individual yarn twists and the tactile weight of the knit responding to her movement.
```

### Run 2

- Session: `8661325f`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/8661325f/gen_8661325f_1.png`
- Overall fidelity: 0.650
- Silhouette: 0.600
- Texture: 0.850
- Construction: 0.650
- Model change: 0.900
- Pose catalog: 0.950
- BR scene plausibility: 0.800
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: silhouette changed from a wide-draped ruana/wrap to a more structured cardigan-like fit, stripe orientation on the front panels became diagonal/v-shaped instead of horizontal, the continuous panel construction was replaced with more defined sleeve-like tapering
- Summary: The generated garment captures the color palette and knit texture well, but fails on the fundamental construction of the ruana. It introduces a more traditional cardigan silhouette with diagonal stripe patterns on the front, whereas the reference is a simple rectangular wrap with horizontal stripes throughout.

Prompt:

```text
RAW photo, a sophisticated Carioca FARM Rio lookbook model with facial features that are a beautiful natural blend open-front ruana-wrap construction soft open front edge with uninterrupted drape hip length relative to model body draped fluid silhouette asymmetric hem single continuous body panel draped from shoulder to hem, with arm coverage formed by the same panel horizontal stripes knit texture open front pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible contrapposto hip shift, relaxed shoulders, catalog-clean front reveal exact texture, stitch, and fiber relief slim straight jeans, clean white sneakers polished model, natural expression direct confident gaze at camera minimalist indoor studio corner with large soft window light golden hour side light, subject crisp, environment blurred, interior setting. Shot on Sony A7III, 85mm f/1.8 lens. Soft directional lighting creating gentle shadows. visible natural pores and subtle peach fuzz. Natural fabric response to movement with soft creases and realistic drape. Shallow depth of field with a clean, neutral background.
```
