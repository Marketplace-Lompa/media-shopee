# Google Gemini Image Generation Reference

Verified against the official Google Gemini image-generation docs on 2026-03-12.

## Model mapping

- Nano Banana 2 -> `gemini-3.1-flash-image-preview`
- Nano Banana Pro -> `gemini-3-pro-image-preview`
- Nano Banana -> `gemini-2.5-flash-image`

## Core official capabilities

- Text-to-image generation
- Text-and-image editing
- Multi-turn image editing
- Up to 14 total reference images on Gemini 3 image models
- Google Search grounding for real-time information
- Google Image Search grounding on `gemini-3.1-flash-image-preview`
- 1K, 2K, and 4K output on Gemini 3 image models
- 512 output also available on `gemini-3.1-flash-image-preview`
- Accurate text rendering and layout-aware prompt following

## Thinking and session behavior

- Gemini 3 image models always use thinking; this cannot be disabled in the API.
- The model may generate up to two interim thought images before the final render.
- `gemini-3.1-flash-image-preview` supports `thinkingLevel: minimal|high`.
- `includeThoughts` controls visibility of thought output, not whether thinking is billed.
- All responses include `thought_signature`.
- If you manually replay conversation history, pass `thought_signature` back exactly as received.
- Official SDK chat flows handle thought signatures automatically when you preserve the full response objects.

## Reference-image limits called out in docs

- `gemini-3.1-flash-image-preview`
  - up to 10 high-fidelity object references
  - up to 4 character references for identity consistency
- `gemini-3-pro-image-preview`
  - up to 6 high-fidelity object references
  - up to 5 character references for identity consistency

## Output and configuration reminders

- Default output is text plus image.
- Request image-only output explicitly when needed.
- Editing usually preserves the input image size and ratio unless the prompt or references push it elsewhere.
- New-image generation defaults to square unless you specify ratio or provide a size-defining reference.
- Use uppercase `K` values for image size options like `1K`, `2K`, `4K`.

## Aspect ratio and size notes

Useful reminders from the docs:
- Gemini 3 models default to `1K` output when no different image size is set.
- `gemini-3.1-flash-image-preview` supports `512`, `1K`, `2K`, and `4K`.
- `gemini-3-pro-image-preview` supports `1K`, `2K`, and `4K`.
- In editing workflows, the default aspect ratio is usually the same as the input image.
- The 3.1 Flash preview docs call out extended aspect ratios including very tall and very wide outputs such as `1:8` and `8:1`.

## Prompt categories from the official guide

Generation patterns:
- photorealistic scenes
- stylized illustrations and stickers
- accurate text in images
- product mockups and commercial photography
- minimalist and negative-space compositions
- storyboard or sequential art
- grounded generation with Google Search

Editing patterns:
- adding or removing elements
- targeted inpainting-style changes
- style transfer
- multi-image composition
- high-fidelity detail preservation
- sketch-to-finished-image
- character consistency and multiple views

## Best-practice reminders

- Be hyper-specific.
- Provide context and intent, not only nouns.
- Iterate conversationally.
- Use step-by-step instructions when the request is complex.
- Use semantic negatives: describe the desired absence positively.
- Control the camera with concrete photographic language.

## Common pitfalls

- Community examples often borrow Stable Diffusion style parameters that are not official Gemini image API fields.
- Multi-turn quality can degrade if thought signatures are dropped.
- Character consistency improves with explicit lock instructions and stable references, but still may require iterative correction.
- Long or complex text rendering may need staged prompting.
- Asking for too many simultaneous changes often reduces fidelity.
- The official Google image-generation docs do not present a native LoRA-style training flow for Nano Banana image models; if a user asks for "LoRA", first determine whether they actually need object references, character references, or a third-party platform feature.

## When to prefer Imagen instead

The official docs also direct users to consider Imagen for cases where:
- highly specialized image-generation workflows are already built around Imagen features
- the user specifically wants the Imagen family rather than Gemini's text+image conversational editing workflow

Use this as a model-selection note, not as a blanket recommendation.
