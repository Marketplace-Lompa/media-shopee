# Two-Pass Validation

- Timestamp: 2026-03-11 18:13:52

## Selector

- Base generation: IMG_3326.jpg, IMG_3323.jpg, IMG_3324.jpg, IMG_3330.jpg
- Strict single-pass eval refs: IMG_3326.jpg, IMG_3324.jpg, referencia.jpeg, referencia2.jpeg
- Edit anchors: referencia.jpeg, referencia2.jpeg

## Stage 1 - Base Candidates

### Candidate 1

- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_1.png`
- Overall: 0.92
- Garment fidelity: 0.95
- Silhouette: 0.9
- Texture: 0.9
- Construction: 0.85
- Commercial quality: 0.95
- Summary: The generated image shows exceptional fidelity to the reference garment's striped pattern, color palette (olive green and dusty rose), and crochet texture. The cocoon-like silhouette and draped construction are accurately translated into a professional catalog setting. The model and lighting are highly realistic, meeting commercial standards.

### Candidate 2

- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_2.png`
- Overall: 0.94
- Garment fidelity: 0.95
- Silhouette: 0.9
- Texture: 0.95
- Construction: 0.9
- Commercial quality: 0.95
- Summary: The generated image shows exceptional fidelity to the reference garment, accurately capturing the specific green and pink striped knit pattern and texture. The silhouette correctly interprets the ruana/wrap construction with the appropriate drape and sleeve architecture. The model and lighting are highly realistic, meeting professional commercial catalog standards.

## Stage 1 Winner

- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_2.png`
- Overall: 0.94
- Garment fidelity: 0.95

## Stage 2 - Edited Result

- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/twopasse_20260311_181242/edit_twopasse_20260311_181242_1.png`
- Overall: 0.93
- Garment fidelity: 0.95
- Model change: 1.0
- Environment change: 0.8
- Innerwear change: 1.0
- Photorealism: 0.95
- Commercial quality: 0.95
- Summary: The edit successfully preserves the garment's specific knit texture, stripe pattern, and cocoon silhouette while completely changing the model's identity and the environment. The innerwear was correctly updated to a white crew-neck tee as requested, and the overall image quality is high-end catalog standard.

## Base Prompt

```text
Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment. Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible, clean premium indoor composition, soft natural daylight. Preserve exact garment geometry, texture continuity, and construction details. Garment identity anchor: ruana_wrap, draped silhouette, open front opening, cocoon hem behavior, cape_like sleeve architecture. Catalog-ready minimal styling with the garment as the hero piece. Keep accessories subtle and secondary to the garment. Build new styling independent from the reference person's lower-body look, footwear, and props unless explicitly requested.
```

## Edit Prompt

```text
Keep the garment exactly the same: same overall garment identity, same knit or crochet texture continuity, same stitch pattern and fiber relief, same pattern placement and stripe scale if present, same open-front construction, same draped fluid silhouette, same cape-like arm coverage, same rounded cocoon hem behavior, keep the garment ending around the upper thigh relative to the model body, preserve these structural cues: continuous neckline-to-front edge, broad uninterrupted back panel, rounded cocoon side drop, arm coverage formed by draped panel. Replace the model with a clearly different adult woman with different face, skin tone, and hair. Change the inner top to a clean white crew-neck tee. Place her in a bright premium indoor catalog environment with natural window light. Use a standing pose with full garment visibility. Keep the image highly photorealistic, premium fashion catalog quality, with natural skin texture and realistic body proportions.
```

## Stage 2 Issues
