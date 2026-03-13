---
name: nano-banana
description: Use when the user asks for Gemini/Nano Banana image generation or editing help, including realistic prompt design, model selection between Nano Banana, Nano Banana 2, and Nano Banana Pro, multi-image workflows, multi-turn sessions, Context/Elements workflows on Krea or Higgsfield, or comparisons with platform layers such as Krea and Higgsfield.
---

# Nano Banana

Use this skill when the task involves Google's Gemini image-generation stack ("Nano Banana"), especially for realistic prompt engineering, image editing, multi-reference composition, grounded generation, or separating official Gemini API behavior from third-party platform features.

## Quick Start

If the user asks for a Nano Banana workflow, answer in this order:
1. identify whether the request is about Google-native features, a platform wrapper, or community tooling
2. choose the model family
3. gather constraints and locked elements
4. write or rewrite the prompt with high-fidelity instructions
5. call out unsupported assumptions explicitly
6. cite official or platform sources when the request depends on current capabilities

If the user asks for a comparison or research brief, organize the answer into:
- `Official Gemini`
- `Platform layer`
- `Community/projects`
- `What this means in practice`

## Scope

Run this skill for:
- prompt writing or rewriting for `gemini-2.5-flash-image`, `gemini-3.1-flash-image-preview`, or `gemini-3-pro-image-preview`
- text-to-image, image-to-image, inpainting-style edits, multi-turn image editing, and character consistency workflows
- choosing between Nano Banana, Nano Banana 2, and Nano Banana Pro
- explaining limits, aspect ratios, resolutions, grounding, or thought-signature behavior
- deciding whether a clothing/product workflow should use `Context`, `Elements`, multi-reference prompts, character locks, or an `Object` LoRA-like path
- checking whether community parameters like `seed`, `steps`, `guidance_scale`, `LoRA`, or "context mode" are actually native to Google or only available on a platform wrapper
- comparing Google-native capabilities with ecosystem layers such as Krea and Higgsfield

Default stance:
- prefer official Google docs as the source of truth for model capabilities and API behavior
- browse the web for "latest", "new", pricing, platform availability, or ecosystem comparisons
- separate conclusions into `official Gemini`, `platform layer`, and `community/project` when answering

## Intake Checklist

Before writing prompts or recommendations, gather these inputs:
- target outcome: new image, edit, extension, composite, character sheet, storyboard, marketing asset
- realism level: documentary, ecommerce, editorial, cinematic, surreal, illustration
- consistency target: exact garment, exact product, same person, same campaign look, same brand language, or only similar vibes
- subject locks: face, body proportions, SKU shape, logo, packaging, typography, background
- camera locks: shot type, lens feel, focal distance, framing, perspective
- lighting locks: direction, softness, color temperature, time of day, practical lights
- reference roles: which image is the base, which image controls subject identity, which image controls outfit, which image controls product, which image controls palette
- delivery format: marketplace main image, ad creative, landing hero, thumbnail, portrait, reel cover, poster
- output constraints: aspect ratio, resolution, transparent background, visible text, language

If the user provides very little information, infer the minimum needed and say what you assumed.

## Workflow

### 1. Verify the layer first

Before giving advice, determine which layer the user is asking about:
- `official Gemini API`: model IDs, request fields, limits, grounding, thought signatures, resolutions, aspect ratios
- `platform layer`: Krea, Higgsfield, fal, Photoshop integrations, AI Studio UX, etc.
- `community layer`: GitHub wrappers, prompt libraries, MCP servers, datasets, hackathon kits

Never merge these layers into one feature list.

### 2. Pick the model

Use this default model-selection rule:
- `gemini-3.1-flash-image-preview` ("Nano Banana 2"): best default for most developer workflows, good speed/quality balance, supports Google Image Search grounding, 512 to 4K output, and controllable `thinkingLevel`
- `gemini-3-pro-image-preview` ("Nano Banana Pro"): use for highest-fidelity asset work, harder prompt following, richer text rendering, and complex multi-image composition
- `gemini-2.5-flash-image` ("Nano Banana"): use when speed, low latency, or high-volume iteration matters more than advanced controls

Use this decision shortcut:
- choose `gemini-2.5-flash-image` for fast ideation, many quick variations, or budget-sensitive batch work
- choose `gemini-3.1-flash-image-preview` for most production prompting, image editing, grounded tasks, and multi-reference work
- choose `gemini-3-pro-image-preview` when typography, premium product polish, or very complex composition matters more than turnaround time

### 3. Structure the request

For image work, gather:
- goal: generate, edit, extend, combine, preserve, localize, or restyle
- fidelity target: photoreal, editorial, product, icon, illustration, storyboard
- locked elements: person, object, logo, text, background, aspect ratio
- references: how many images, what each one controls, and what must stay unchanged
- output constraints: ratio, size, text accuracy, language, transparency expectations, delivery context

If the user is vague, make reasonable assumptions and state them after the work.

### 4. Prefer multi-turn for editing

For iterative edits in official Gemini:
- prefer chat or full response-history workflows instead of isolated one-shot calls
- preserve `thought_signature` exactly when manually replaying history
- if using the official Google SDK chat flow, let the SDK carry signatures automatically

Use a multi-turn loop like this:
1. establish the locked identity or product baseline
2. change one variable at a time
3. after each output, restate the locked elements before making the next edit
4. if fidelity drifts, re-anchor with the original reference and a "change only X" instruction
5. if text rendering matters, treat the text as an explicit design object, not as ambient scene detail

### 5. Report with explicit boundaries

When answering, use this order:
1. What is officially supported by Google
2. What is added by Krea, Higgsfield, or another platform
3. What is community practice or an experimental wrapper
4. What you infer from the available evidence

### 6. Match the playbook to the task

Use these playbooks:
- `new generation`: scene-building prompt, camera control, material realism, mood, output specs
- `single-image edit`: locked-subject prompt with "change only" language
- `multi-image composition`: assign a role to each reference and define what must remain unchanged
- `character consistency`: stable face reference, view specification, wardrobe lock, pose delta
- `text in image`: separate text content, typographic style, layout placement, and legibility requirements
- `grounded generation`: explicitly say what must be looked up versus what is pure visual direction
- `platform audit`: separate model-native features from wrapper features and mention the platform by name

### 7. Deliver an actionable result

When the user wants execution-ready material, default to one of these outputs:
- 1 polished master prompt
- 3 prompt variants with different creative risk levels
- a prompt plus negative/guard instructions
- a step-by-step multi-turn workflow
- a model recommendation matrix with rationale
- a comparison table across Google, Krea, and Higgsfield layers

## Response Format

For prompt requests, prefer this response shape:
1. `Modelo recomendado`
2. `Prompt principal`
3. `Variações`
4. `Instruções de trava`
5. `Observações de plataforma`

For research requests, prefer:
1. `O que é oficial`
2. `O que a plataforma adiciona`
3. `O que é comunidade`
4. `Riscos de confusão`

For debugging capability questions, prefer:
1. `Suportado hoje`
2. `Não suportado nativamente`
3. `Suportado apenas em wrapper`
4. `Como contornar`

## Naming Map For Consistency Workflows

Use these terms consistently when explaining workflows:

- `Context`
  -> a briefing or memory layer for campaign rules, style direction, scene logic, brand language, and reusable constraints
- `Elements`
  -> reusable asset references for garments, products, logos, props, or scene objects that should recur consistently
- `Multi Reference`
  -> multiple uploaded images with explicit roles such as identity, outfit, composition, palette, or product
- `Character lock`
  -> identity preservation for a person, mascot, or recurring avatar
- `Object lock`
  -> preservation of an exact product, garment, prop, or SKU
- `Object LoRA`
  -> trained weights or adapter meant to reproduce a specific object consistently across many outputs
- `Style LoRA`
  -> a trained aesthetic, not a guarantee of exact SKU fidelity
- `Soul ID`
  -> Higgsfield's identity layer for recurring people/characters
- `Product Placement` / `Banana Placement`
  -> platform-side placement flows for inserting products or objects into scenes
- `World Context`
  -> Higgsfield's wrapper-side scene knowledge and placement abstraction, not a Google API field

When the user says "train roupa", translate it before answering:
- exact same clothing piece -> `Element` or `Object lock`
- same collection mood -> `Context` or style guidance
- same model wearing the same piece -> `Character lock` plus `Element`
- true reusable training -> `Object LoRA` on a platform that supports it

## Official Gemini Facts

Keep these facts straight:
- Nano Banana 2 maps to `gemini-3.1-flash-image-preview`
- Nano Banana Pro maps to `gemini-3-pro-image-preview`
- Nano Banana maps to `gemini-2.5-flash-image`
- generated images include SynthID watermarking
- Gemini 3 image models always use thinking; you can inspect or tune some of it, but you cannot disable it in the API
- `gemini-3.1-flash-image-preview` supports `thinkingLevel` values `minimal` and `high`
- Gemini 3 image models support up to 14 total references, split between high-fidelity object references and character-consistency references
- Google Search grounding is supported for real-time information; Google Image Search grounding is specific to `gemini-3.1-flash-image-preview`
- default output is mixed text plus image; image-only output must be requested explicitly
- aspect ratio usually follows the input when editing; otherwise it defaults to square unless you specify a target ratio or provide a correctly sized reference
- if you need the latest exact limits, re-check the official docs because preview models and limits may change
- the official prompt guide emphasizes describing scenes, not dumping keywords
- Google positions `gemini-3.1-flash-image-preview` as the best default balance for many use cases
- `gemini-2.5-flash-image` works best with fewer input images than the Gemini 3 preview models
- for text-heavy outputs, iterating in stages often works better than asking for every design and copy constraint at once

Load `references/google-gemini-image-generation.md` when you need the official capability table, prompt categories, or configuration reminders.

## Prompt Construction Rules

Build strong prompts in layers:
1. subject and action
2. environment and context
3. camera and composition
4. lighting and mood
5. material and texture fidelity
6. hard constraints
7. output spec

Do not rely on vague adjectives such as:
- beautiful
- cinematic
- realistic
- premium

Instead, translate them into visible instructions:
- lens and distance
- lighting direction and softness
- material finish and texture
- subject placement
- specific atmosphere
- what must not change

Convert low-signal user requests like this:
- `make it more realistic`
  -> define skin texture, lens, depth of field, lighting consistency, natural body proportions, realistic shadows
- `make it luxury`
  -> specify brushed metal, clean acrylic, controlled reflections, high-key studio lighting, restrained composition
- `make it viral`
  -> specify thumbnail readability, bold silhouette separation, central subject hierarchy, social-safe crop

## Task Playbooks

### New image generation

Use when there is no source image.

Checklist:
- identify the subject and action
- define the environment and what story the scene tells
- define shot type and lens feel
- define lighting and realism level
- define exactly what the output is for

Minimum viable structure:

```text
[shot type] of [subject] [doing what], in [environment].
Lighting: [description].
Camera: [lens/framing/perspective].
Materials and textures: [details].
Mood: [specific emotional tone].
Output: [aspect ratio/resolution/use case].
```

### Single-image edit

Use when the user wants fidelity preserved.

Checklist:
- identify the exact editable element
- restate what must remain locked
- preserve framing, identity, perspective, and lighting unless asked otherwise
- forbid incidental changes

Core edit language:

```text
Using the provided image, change only [target element] to [new result].
Keep [identity/product/logo/background/framing/lighting] exactly the same.
Do not modify any other part of the image.
```

### Multi-image composition

Use when several references play different roles.

Checklist:
- assign one role per image
- decide which image owns identity
- decide which image owns composition
- define how conflicts should be resolved
- state "one coherent photograph, not a collage" for realism workflows

Composition scaffold:

```text
Use Image 1 for the face and pose.
Use Image 2 for the outfit and fabric behavior.
Use Image 3 for the product/logo details.
Use Image 4 for the color palette and set dressing.
Blend all elements into one physically coherent final photograph.
```

### Text inside image

Use when the user needs readable typography.

Rules:
- isolate the exact text string
- define font style, placement, and visual hierarchy
- say the text must remain legible
- if complex copy is required, recommend staged iteration

Prompt pattern:

```text
Create [design type] with the exact text "[TEXT]".
Set the text in [font style] and place it [location].
Ensure the text is fully legible and intentionally designed, not incidental scene detail.
```

### Grounded generation

Use when live facts matter.

Rules:
- specify which information comes from Search
- specify which elements are purely stylistic
- if using Google Image Search grounding, mention attribution/display obligations when relevant

### Character consistency

Use when the same person or mascot must persist.

Rules:
- lock the face identity first
- change only one major variable at a time
- specify view, expression, pose, wardrobe, and background independently
- repeat "preserve identity" in every iteration if the user is chasing a campaign set

### Product fidelity

Use when SKU shape, label, and packaging matter more than stylistic freedom.

Rules:
- define package geometry
- define exact materials and finish
- define logo preservation
- define what cannot be stylized away
- use a plain background or controlled set when marketplace compliance matters

### Garment and apparel consistency

Use when the same clothing item must recur across multiple images.

Decision rule:
- exact same garment in many scenes -> start with `Elements` or object references
- exact same garment on the same person -> use `Character lock` plus `Element`
- campaign-level tone without exact SKU preservation -> use `Context`
- very high volume or repeated failure with references alone -> escalate to platform training such as `Object LoRA`

Dataset rules for a garment reference pack:
- use only the exact same garment, not adjacent variants
- include front, back, side, 45-degree, close-up fabric, seam, collar, hem, and print details
- prefer high-resolution shots with the garment clearly readable
- avoid mixing multiple colorways unless the goal is to generalize across them
- if text or logos on the garment must survive, include tight close-ups
- choose either isolated product shots or on-body references intentionally; do not mix casually

Workflow:
1. lock the garment as the object to preserve
2. separately lock the model identity if needed
3. define what may change: pose, camera, location, styling, or lighting
4. forbid redesign language
5. iterate in small changes if fidelity drifts

## Platform Layer Rules

When the user mentions Krea, Higgsfield, or similar platforms:
- treat LoRA training, style training, reusable session parameters, moodboards, Soul ID, or Flux Kontext as platform capabilities unless the official Google docs say otherwise
- do not describe `seed`, `steps`, `guidance_scale`, LoRA strength, or "context mode" as native Google Gemini image API parameters without proof
- if a feature exists on Krea or Higgsfield, name the platform explicitly in the answer
- if a platform markets a capability using Google model names, distinguish the underlying Google model from the wrapper workflow the platform adds
- if the user asks for a "mode" that does not exist in official docs, translate it into the nearest actual concept before answering

Use these translations carefully:
- `context mode`
  -> may mean multi-turn context, reference-image context, moodboard-style reference boards, or wrapper memory
- `LoRA mode`
  -> often means platform style training or custom style application, not a Google-native Gemini image parameter
- `control mode`
  -> may refer to platform-side editing tools, masks, compositing, or seedable diffusion controls from a different model family

### Krea-specific notes

Treat the following as Krea layer unless re-verified elsewhere:
- the public Nano Banana tool UI currently exposes `Context` and `Elements`
- style/LoRA training
- style strength controls
- Flux Kontext knobs
- platform session history and parameter reuse
- up to 15 image prompts in Krea's own workflow language
- Paint control inside Krea

How to route Krea requests:
- `Context`
  -> use for campaign brief, art direction, scene logic, styling rules, and persistent instructions
- `Elements`
  -> use for exact garments, products, logos, props, or reusable visual assets
- `Object` training
  -> use when an exact product or garment must survive many generations and Elements alone are not enough
- `Style` training
  -> use when the user wants a collection aesthetic, not exact object fidelity
- `Character` training
  -> use when the user wants the same person or designed character to recur

Important Krea nuance:
- Krea's general image docs show Nano Banana as a reasoning model without explicit `style reference` or `character reference` toggles, even though the model can interpret uploaded images and prompts very well
- Krea's training docs describe style codes and LoRA training as platform features that apply across Krea workflows; do not present them as Google-native Nano Banana controls

### Higgsfield-specific notes

Treat the following as Higgsfield layer:
- World Context
- Soul ID
- Moodboards
- Banana Placement
- Product Placement
- Multi Reference
- Fashion Factory
- prompt frameworks based on spatial anchors, negative constraints, and physics-based prompting
- orchestration between image generation and downstream video/aesthetic workflows

How to route Higgsfield requests:
- `World Context`
  -> use for scene knowledge, relationship logic, and contextual placement of known people, brands, or objects
- `Elements`
  -> if the app exposes it, treat it as a reusable asset/product/object layer analogous to object references
- `Soul ID`
  -> use for model or character identity
- `Fashion Factory`
  -> use when starting from a product/garment image for fashion scenes
- `Product Placement` / `Banana Placement`
  -> use when inserting products or objects into a scene
- `Multi Reference`
  -> use when several images have different roles and composition logic matters

Important Higgsfield nuance:
- public crawled marketing pages clearly expose `World Context`, `Multi Reference`, `Product Placement`, `Banana Placement`, `Fashion Factory`, and `Soul ID`
- I did not find a standalone public Higgsfield documentation page dedicated to `Elements`; if the in-app UI shows it, treat it as a Higgsfield asset abstraction, not a Google-native model parameter

Load `references/platform-ecosystem.md` when comparing Krea, Higgsfield, GitHub projects, or community prompt ecosystems.
Load `references/model-and-feature-matrix.md` when you need a side-by-side capability view.
Load `references/prompt-cookbook.md` when the user wants richer prompt examples.
Load `references/project-watchlist.md` when the user asks for tools, repos, MCP servers, or ecosystem scouting.
Load `references/elements-context-garments.md` when the user wants exact product or clothing consistency workflows.

## Prompt Recipes

Use prompts that describe a scene, not just keyword piles. Favor physical, photographic, and spatial detail.

### Photoreal editorial

```text
A photorealistic editorial portrait of [subject], [pose/expression], in [environment].
Lighting: [light source, direction, softness, color temperature].
Camera: [shot type], [lens], [distance], [depth of field].
Wardrobe/materials: [specific textures, fabrics, finishes].
Composition: [framing, negative space, subject position].
Mood: [precise emotional tone].
Keep anatomy natural, skin texture realistic, and background elements physically coherent.
Output: [aspect ratio], [resolution], [text/no text].
```

### Product image

```text
A high-end commercial product photograph of [product] on [surface/background].
Show accurate materials, crisp label readability, realistic reflections, and premium studio lighting.
Camera: [macro/50mm/85mm], [angle].
Composition: [hero shot, centered/off-center, negative space location].
Brand constraints: preserve the exact logo, preserve package proportions, do not alter [locked element].
Output for [landing page/ad/social/poster] in [aspect ratio].
```

### Garment element lock

```text
Use the attached garment element as the exact clothing reference.
Preserve the silhouette, neckline, sleeve length, seam placement, hem length, print scale, fabric texture, and material sheen exactly.
Style the same garment on the subject in a photoreal [editorial/ecommerce/campaign] scene.
Change only pose, camera angle, environment, and styling details that do not alter the garment itself.
Do not redesign, simplify, fuse, or reinterpret the clothing item.
```

### High-fidelity edit

```text
Using the provided image, change only [target element] to [new description].
Keep the person's identity, pose, framing, lighting direction, skin tone, and all non-target details exactly the same.
Preserve the original aspect ratio and camera perspective.
Do not introduce extra accessories, background changes, or typography unless explicitly requested.
```

### Multi-image composition

```text
Create one final image using:
- Image 1 as the base composition and camera angle
- Image 2 as the outfit/material reference
- Image 3 as the product/logo reference
- Image 4 as the color palette reference

The final result should look like one coherent real photograph, not a collage.
Preserve the face identity from Image 1.
Match lighting and shadows consistently across all imported elements.
```

### Reliable prompt additions

Use these control patterns when helpful:
- `Keep everything else unchanged.`
- `Preserve the original framing and aspect ratio.`
- `Treat the text as a designed element that must remain legible.`
- `Make the scene physically plausible and commercially polished.`
- `Do not reinterpret the logo; place it faithfully.`
- `Preserve the garment silhouette, cut, and construction details exactly.`
- `Use the uploaded element as the source of truth for the product.`

### Spatial-anchor additions

When composition matters, add anchors like:
- `Place the subject in the left third of the frame.`
- `Keep the product centered with 20 percent breathing room above the cap.`
- `The handbag sits on the table in the foreground, the model stands two meters behind it.`
- `The headline occupies the upper-right quadrant without overlapping the subject.`

### Physics and realism additions

When realism matters, add:
- `Shadows must follow the key light direction consistently.`
- `Reflective materials should show believable specular highlights.`
- `Fabric folds should respond naturally to gravity and pose.`
- `Glass, metal, and plastic should retain distinct material behavior.`
- `Avoid collage artifacts, duplicated anatomy, or impossible overlaps.`

### Marketplace-safe additions

For ecommerce or ad production, add:
- `Keep the product shape and branding faithful to the reference.`
- `Use a clean commercial composition with immediate thumbnail readability.`
- `Do not add extra props unless specified.`
- `Preserve the exact front-facing label geometry.`

## Troubleshooting

If the result looks generic:
- add lens, lighting, material, and composition details
- replace adjectives with observable instructions

If identity drifts:
- reassert the base reference role
- reduce the number of simultaneous changes
- repeat what must remain unchanged

If the product deforms:
- lock geometry, label placement, cap shape, and logo treatment
- ask for a clean studio setup instead of a complex scene

If the garment drifts:
- switch from pure prompting to `Elements` or explicit object references
- restate silhouette, seams, hem, neckline, print, and fabric behavior
- avoid changing too many styling variables at once
- if drift persists across many jobs, consider platform-side `Object` training

If the typography fails:
- shorten the text
- stage the design in two passes
- define the exact placement and font tone

If the scene looks like a collage:
- assign one composition owner image
- specify consistent lighting and perspective
- explicitly ask for one coherent photograph

If the user confuses platform features with official features:
- acknowledge the desired capability
- name the platform that provides it
- map it to the closest official Gemini concept if possible
- say clearly when no Google-native equivalent exists

## Guardrails

- Do not invent unsupported API parameters.
- Do not present platform pricing, rate limits, or availability without fresh browsing.
- When the user asks for "latest" or "new", verify current docs and platform pages first.
- If the user wants production-ready prompts, optimize for realism, camera control, material realism, spatial anchors, and locked constraints.
- If the user wants research, include links and clearly label which claims are official versus inferred.
- If the user wants the "latest" state of any preview model or platform release, browse first.
- Keep official facts and platform abstractions in separate sections.
- Prefer a smaller number of high-signal prompts over long lists of weak prompts.
- When possible, explain why a prompt is structured a certain way so the user can iterate independently.

## References

Read only what is needed:
- `references/google-gemini-image-generation.md`
- `references/platform-ecosystem.md`
- `references/model-and-feature-matrix.md`
- `references/prompt-cookbook.md`
- `references/project-watchlist.md`
- `references/elements-context-garments.md`
