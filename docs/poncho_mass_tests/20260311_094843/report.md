# Poncho Mass Test Report

- Timestamp: 2026-03-11 09:51:49
- Reference folder: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste`
- Runs: 2

## Aggregate

- Overall fidelity avg: 0.765
- Silhouette fidelity avg: 0.725
- Texture fidelity avg: 0.900
- Model change avg: 1.000
- Pose catalog avg: 0.900
- Brazilian scene plausibility avg: 0.925
- Scene change avg: 1.000

## Runs

### Run 1

- Session: `89eb786a`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/89eb786a/gen_89eb786a_1.png`
- Overall fidelity: 0.880
- Silhouette: 0.850
- Texture: 0.950
- Construction: 0.800
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 0.900
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": false, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment has a slightly more structured front opening compared to the very loose drape of the original, The cocoon shape is a bit more defined/tapered at the bottom than the reference
- Summary: The generated image successfully captures the unique crochet texture and the specific olive/rose stripe pattern of the reference garment. The model and scene are completely transformed into a professional catalog aesthetic. The silhouette is largely accurate, though it appears slightly more tailored than the original's very fluid, unstructured drape.

Prompt:

```text
RAW photo, A striking Northeastern Brazilian model, features blend 'Yasmin' and 'Letícia Souza' Wearing Textured crochet ruana with olive and dusty rose horizontal stripes. Features fluid draped arm coverage, a cocoon silhouette, and flat uniform open-weave construction that drapes loosely She is wearing a single-piece ruana wrap draped over the shoulders. The same knitted edge flows from the neckline directly into the soft front opening. The outer silhouette falls in a rounded cocoon side drop reaching upper-thigh length relative to the model body. Arm coverage is created by the same continuous body panel as the garment, forming a fluid draped wrap over the arms. continuous neckline-to-front edge rounded cocoon side drop ribbed horizontal stripe texture pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible slight body turn with direct eye contact, clean garment silhouette exact texture, stitch, and fiber relief minimalist indoor studio corner with large soft window light polished model, natural expression warm near-camera look with relaxed expression dappled natural light revealing fabric texture and depth tailored neutral chinos, low-profile loafers subject sharp, background softly defocused, balanced natural light. Sony A7III, 85mm f/1.8, natural side-lit window light, visible natural pores, subtle peach fuzz, natural fabric wear creases and fiber realism.
```

### Run 2

- Session: `e9ac12c7`
- Image: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/e9ac12c7/gen_e9ac12c7_1.png`
- Overall fidelity: 0.650
- Silhouette: 0.600
- Texture: 0.850
- Construction: 0.650
- Model change: 1.000
- Pose catalog: 0.900
- BR scene plausibility: 0.950
- Scene change: 1.000
- Prompt flags: `{"duplicate_features_blend": false, "contains_front_panel_open": false, "contains_bottom_complement": true, "contains_catalog_cover": true, "scenario_shopping_district": false}`
- Failures: The generated garment has a structured ribbed collar/lapel that is not present in the original crochet wrap, The sleeve construction in the generated image is more defined like a kimono sleeve rather than the continuous draped panel of the reference, The stripe orientation on the front panels is vertical/diagonal in the generation whereas the reference is horizontal/concentric
- Summary: The generated image successfully captures the color palette and crochet texture, but fails on the specific construction of the wrap. It introduces a structured ribbed opening and more defined sleeve seams that turn the fluid ruana-style wrap into a more conventional cardigan/kimono hybrid. The scene and model change are excellent.

Prompt:

```text
RAW photo, A chic Paulistana editorial beauty, features blend 'Camila' and 'Isadora Ribeiro' Wearing Drapeddraped knit wrap in flat uniform crochet with olive green and dusty rose horizontal stripes. fluid draped arm coverage create a voluminous silhouette with a rhythmic, textured pattern She is wearing a single-piece ruana wrap draped over the shoulders. The same knitted edge flows from the neckline directly into the soft front opening. The outer silhouette falls in a rounded cocoon side drop reaching upper-thigh length relative to the model body. Arm coverage is created by the same continuous body panel as the garment, forming a fluid draped wrap over the arms. continuous neckline-to-front edge rounded cocoon side drop ribbed edge finish pocketless garment — clean surface, zero visible pockets catalog cover, standing pose, garment fully visible subtle 3/4 angle toward camera, weight on back foot, front panel clear exact texture, stitch, and fiber relief lush botanical garden path with gentle backlight and soft greenery polished model, natural expression engaging eye contact dappled natural light revealing fabric texture and depth wide-leg cropped pants, simple flats. Sony A7R IV, 85mm f/1.4 lens. Soft rim lighting, natural skin texture with visible pores and subtle peach fuzz. Realistic fabric drape and tension points at the shoulders. subtle film grain and mild lens halation.
```
