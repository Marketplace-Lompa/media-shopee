# Prompt Cookbook

Use these as starting points, not rigid formulas. Replace every bracketed field with concrete instructions.

## 1. Editorial portrait

```text
A photorealistic editorial portrait of [subject], [pose/expression], in [environment].
Lighting: [key light direction], [soft/hard], [warm/cool], with subtle fill and realistic shadow falloff.
Camera: [close-up/medium/full-body], [35mm/50mm/85mm], eye-level perspective, natural depth of field.
Styling: [wardrobe], [textures], [hair/makeup details].
Mood: [specific tone].
Composition: [subject placement], [negative space use].
Keep anatomy natural, skin texture realistic, and all surfaces physically coherent.
Output: [aspect ratio], [resolution].
```

## 2. Ecommerce product hero

```text
A premium studio product photograph of [product] on [surface/background].
Show accurate package geometry, exact logo placement, crisp label readability, realistic reflections, and believable material response.
Lighting: high-end commercial studio setup with [softbox/rim light/backlight].
Camera: [50mm/85mm/macro], [front/three-quarter/top-down].
Composition: clean hero shot with immediate thumbnail readability and controlled negative space for copy.
Do not alter the product proportions or branding.
Output: [marketplace ratio].
```

## 3. Beauty close-up

```text
A high-resolution beauty close-up of [subject], emphasizing [skin/hair/lips/eyes].
Lighting: diffused key light with controlled highlights and natural skin texture.
Camera: macro beauty shot, shallow depth of field, precise focus on [area].
Retain realistic pores, subtle vellus hair, and natural facial proportions.
Background: minimal and unobtrusive.
```

## 4. Fashion campaign image

```text
A luxury fashion campaign photograph of [model] wearing [look], standing in [location].
Lighting: [golden hour/window light/studio spotlight], with shadows consistent with the key light.
Camera: [full-body/three-quarter], [35mm/50mm], editorial framing.
Materials: preserve the exact drape, texture, and sheen of [fabric].
Mood: [precise art direction].
The final image should look like a real magazine campaign, not a collage.
```

## 5. Food photography

```text
A commercial food photograph of [dish/drink] on [surface], styled for [menu/ad/social].
Lighting: appetizing side light with realistic specular highlights and soft shadow depth.
Camera: [top-down/45-degree/macro], high detail in texture and garnish.
Keep ingredients fresh-looking, physically plausible, and color-balanced.
```

## 6. Interior scene

```text
A photorealistic interior photograph of [room type], designed in [style].
Lighting: [time of day], with natural window behavior and believable bounce light.
Camera: wide interior shot from [viewpoint], straight verticals, realistic lens behavior.
Materials: wood grain, fabric weave, metal finish, and glass reflections must feel true to life.
```

## 7. Poster with text

```text
Create a [poster/banner/flyer] for [brand/concept] with the exact text "[TEXT]".
Use [font mood] typography placed in the [top/bottom/left/right/center] of the frame.
Visual style: [minimal/editorial/retro/futurist].
Ensure the text is fully legible and intentionally designed, with strong hierarchy and clean spacing.
Background image: [subject/scene].
```

## 8. High-fidelity product edit

```text
Using the provided image, change only [target element] to [new result].
Keep the product shape, label geometry, logo placement, camera angle, lighting direction, and all other elements exactly the same.
Do not add props, redesign the packaging, or shift the framing.
```

## 9. Apparel swap

```text
Using the provided portrait, change only the outfit to [new garment description].
Keep the same person, face, pose, background, framing, skin tone, lighting, and camera perspective.
Make the fabric behavior realistic and consistent with the body's posture.
```

## 10. Multi-reference campaign composite

```text
Create one final photorealistic image using:
- Image 1 for the model identity and pose
- Image 2 for the outfit and textile details
- Image 3 for the handbag/product details
- Image 4 for the location mood and palette

Blend everything into one coherent editorial photograph with consistent perspective, lighting, scale, and shadows.
Do not make it look like a collage.
```

## 11. Character turnaround

```text
Create a character sheet for the same character shown in the reference.
Generate [front/profile/three-quarter/back] views while preserving identity, hairstyle, costume details, proportions, and color palette.
Use a clean neutral background and consistent lighting across all views.
```

## 12. Sketch to polished render

```text
Turn this rough sketch into a polished [photo/illustration/product render].
Preserve the composition and key forms of the sketch while refining materials, lighting, and final detail.
The result should feel production-ready, not over-stylized.
```

## 13. Exact garment with reusable element

```text
Use the uploaded garment element as the exact clothing source of truth.
Preserve the silhouette, neckline, sleeve length, seam placement, hem line, print scale, and fabric texture exactly.
Dress the subject in this exact garment in a photoreal [editorial/ecommerce/campaign] scene.
Change only pose, camera, and environment.
Do not redesign, simplify, merge, or reinterpret the piece.
```

## 14. Same model plus same garment

```text
Use Image 1 as the identity reference for the model.
Use the garment element as the exact clothing reference.
Preserve the face identity, body proportions, and the garment construction details exactly.
Generate one coherent real photograph with consistent lighting and natural fabric behavior.
```

## 15. Context-led campaign brief

```text
Campaign context:
- Brand tone: [luxury / minimal / sporty / youth]
- Environment: [studio / street / resort / interior]
- Lighting: [soft daylight / hard flash / golden hour]
- Output: [hero banner / PDP / paid social / poster]
- Styling rule: keep the garment unchanged and premium-looking

Use the garment element as the exact product reference in every generation.
```

## Rewrite rules

When the user gives a weak prompt, improve it by:
- replacing generic adjectives with visual evidence
- adding camera language
- adding lighting behavior
- naming locked elements
- separating composition from subject description
- adding explicit output purpose

## Strong control phrases

Use these when needed:
- `Keep everything else unchanged.`
- `Preserve the exact logo placement and package proportions.`
- `Ensure the final result looks like a single real photograph.`
- `Maintain identity consistency across all outputs.`
- `Do not introduce extra objects or reinterpret the design.`

## Phrases to avoid unless the user insists

- `ultra realistic`
- `best quality`
- `masterpiece`
- `8k` when the model/platform does not actually support it
- long lists of style buzzwords without scene logic
