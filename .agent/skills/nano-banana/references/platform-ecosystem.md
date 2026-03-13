# Nano Banana Platform And Ecosystem Notes

Verified on 2026-03-12 using current public docs and platform pages. Treat this file as a comparison guide, not as the source of truth for Google-native API parameters.

## Krea

Platform-level observations:
- Krea exposes Google Nano Banana models inside a broader image-generation UI.
- Krea's public Nano Banana tool currently exposes `Context` and `Elements` in the UI.
- Krea's user guide documents session-style workflows, result histories, and parameter reuse/sharing.
- Krea's image-prompt workflow says newer reasoning models such as Nano Banana can understand specific cross-image requests.
- Krea documents support for up to 15 image prompts for Nano Banana within its platform workflow.
- Krea exposes a `Paint` control for Nano Banana inside Krea's UI.
- Krea has official style training / LoRA training endpoints.
- Krea also offers Flux Kontext and Flux Kontext Pro for editing, reasoning, and style-transfer-heavy workflows.

Useful Krea docs:
- `https://docs.krea.ai/api-reference/image/nano-banana-2`
- `https://docs.krea.ai/api-reference/image/nano-banana-pro`
- `https://docs.krea.ai/api-reference/styles/train-a-custom-style-lora`
- `https://docs.krea.ai/api-reference/image/flux-kontext`
- `https://docs.krea.ai/user-guide/features/krea-image`

Important boundary:
- LoRA training, style strength, Flux Kontext settings, and many low-level image controls are Krea features, not Google Gemini image API guarantees.
- Krea's general image docs show Nano Banana as a reasoning model that can use uploaded images through prompting, but not as a model with explicit `style reference` or `character reference` toggles in the same way some other Krea models expose.
- Krea training docs describe styles and LoRAs as platform capabilities that can be applied across Krea workflows; do not present them as Nano Banana-native API parameters.

Useful Krea cues:
- Nano Banana 2 endpoint: `/generate/image/google/nano-banana-flash`
- Supports platform fields like `batchSize`, `imageUrls`, `styleImages`, and `resolution`
- Krea LoRA training supports types such as `Style`, `Object`, and `Character`
- The public tool UI suggests a practical split:
  - `Context` for campaign and scene rules
  - `Elements` for reusable garments, products, props, or logos
  - `Object` training when exact reusable object fidelity needs to be learned more deeply

## Higgsfield

Platform-level observations:
- Higgsfield presents Nano Banana 2 as a fast, reasoning-heavy image model inside a larger creator stack.
- Higgsfield layers workflow features such as Soul ID character consistency and Moodboards for style direction.
- Higgsfield publicly advertises `World Context`, `Multi-Reference Control`, and `Product Placement` around Nano Banana workflows.
- Higgsfield's prompt-guide content emphasizes spatial anchors, negative constraints, and physics-based prompting.
- Higgsfield positions Nano Banana 2 as a good "layout and logic" stage before sending outputs into downstream video workflows.

Useful Higgsfield pages:
- `https://higgsfield.ai/nano-banana-2`
- `https://higgsfield.ai/character`
- `https://higgsfield.ai/moodboard`
- `https://higgsfield.ai/nano-banana-pro-prompt-guide`
- `https://higgsfield.ai/soul-intro`

Important boundary:
- Soul ID, Moodboards, and other orchestration features are Higgsfield product layers, not official Google API flags.
- Public crawls did not expose a standalone documentation page for Higgsfield `Elements`; if the in-app UI shows `Elements`, treat it as a Higgsfield asset abstraction rather than a Google-native feature.

## Useful project and community references

- `apple/pico-banana-400k`: large image-editing dataset with multi-turn and preference subsets; useful for benchmarking or training editing workflows
- `google-gemini/nano-banana-hackathon-kit`: official starter kit and resource hub
- `minimaxir/gemimg`: lightweight wrapper for generating and editing images with Gemini image models
- `ConechoAI/Nano-Banana-MCP`: community MCP server for Nano Banana
- `JimmyLv/awesome-nano-banana`: community prompt and example collection

## How to answer users asking about "new powerful features"

When the user asks about advanced or hidden modes:
- verify whether the capability is on Google docs, a Krea doc, a Higgsfield page, or only a community thread
- name the owner of the feature in the first sentence
- avoid saying "Nano Banana has X" if only the wrapper has it
- map wrapper abstractions to practical meanings:
  - context -> campaign memory, scene rules, or wrapper-side reasoning guidance
  - elements -> reusable product, garment, logo, or object assets
  - moodboard -> structured multi-reference style context
  - Soul ID -> persistent identity control
  - LoRA training -> custom style/object/character adaptation
  - Paint -> direct local editing interaction layer
  - Kontext -> a separate editing-oriented model family exposed by the same platform

## Interpretation rules

- If a user says "Nano Banana supports LoRA", confirm whether they mean Google directly or Krea/Higgsfield/a wrapper.
- If a user asks for "context mode", determine whether they mean:
  - official multi-turn conversation and reference-image context in Gemini, or
  - a platform abstraction such as moodboards, session memory, or layout-first workflows
- If a GitHub project exposes extra knobs, do not assume the underlying Google API offers the same knobs natively.
