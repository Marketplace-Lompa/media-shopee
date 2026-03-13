# Model And Feature Matrix

Verified on 2026-03-12 from official Google docs plus current platform pages.

## Official Google model mapping

| Public name | Official model ID | Best fit |
|---|---|---|
| Nano Banana | `gemini-2.5-flash-image` | fast ideation and lower-latency generation |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | best default balance for most workflows |
| Nano Banana Pro | `gemini-3-pro-image-preview` | premium fidelity and harder composition/text tasks |

## Official Google capability view

| Capability | `gemini-2.5-flash-image` | `gemini-3.1-flash-image-preview` | `gemini-3-pro-image-preview` |
|---|---|---|---|
| Text-to-image | yes | yes | yes |
| Image editing | yes | yes | yes |
| Multi-turn editing | yes | yes | yes |
| Google Search grounding | limited/current docs check | yes | yes |
| Google Image Search grounding | no | yes | no current official signal |
| Output sizes | 1024-class | 512, 1K, 2K, 4K | 1K, 2K, 4K |
| Up to 14 references | no current official framing | yes | yes |
| Controllable `thinkingLevel` | no | `minimal`, `high` | no equivalent publicly highlighted |
| Best use | speed | balanced production work | hardest quality tasks |

## Reference image guidance

Official docs call out:

`gemini-3.1-flash-image-preview`
- up to 10 high-fidelity object references
- up to 4 character references

`gemini-3-pro-image-preview`
- up to 6 high-fidelity object references
- up to 5 character references

## Aspect ratio notes

Official reminders:
- editing usually keeps the input image ratio
- new-image generation defaults to square when no ratio is established
- `gemini-3.1-flash-image-preview` adds extra wide and extra tall ratios like `1:8` and `8:1`

## Thinking and session notes

Official reminders:
- Gemini 3 image models always use thinking
- thinking cannot be disabled in the API
- `includeThoughts` controls visibility, not whether thinking occurs
- multi-turn quality is safest when the SDK manages response history or when you preserve `thought_signature` manually

## Platform-side add-ons that people often confuse with Google-native features

| Feature phrase | Usually native Google? | Usually platform-side? | Notes |
|---|---|---|---|
| LoRA training | no | yes | often Krea or another wrapper |
| Seed / steps / CFG-like controls | no public Gemini image API signal | yes | often diffusion-family wrappers |
| Context mode | ambiguous | often yes | may mean moodboard/session memory/reference boards |
| Elements | no public Gemini image API signal | yes | reusable asset/object abstraction in a wrapper UI |
| Soul ID | no | yes | Higgsfield layer |
| Moodboard | no | yes | Higgsfield layer |
| Paint tool | no current official naming | yes | platform interaction layer |
| Flux Kontext | no | yes | separate model family offered by Krea |

## Platform routing matrix for clothing and products

| Need | Google-native closest concept | Krea layer | Higgsfield layer |
|---|---|---|---|
| Exact garment repeated across scenes | object references + multi-turn | `Elements`, possibly `Object` training | `Elements` if available, otherwise Product/Fashion workflow |
| Same model across scenes | character references + multi-turn | image prompt or character-style workflow | `Soul ID` |
| Same campaign logic and tone | conversational context | `Context` | `World Context` |
| Insert product into scene | multi-image composition | image prompt / edit / Elements | `Product Placement` / `Banana Placement` |
| Many references with assigned roles | up to 14 refs on Gemini 3 | image prompt + prompt routing | `Multi Reference` |

## Recommendation shortcuts

Use `gemini-3.1-flash-image-preview` when:
- the user wants one strong default
- multiple references matter
- grounded generation may help
- you want 4K without immediately jumping to the heaviest option

Use `gemini-3-pro-image-preview` when:
- premium asset fidelity matters
- text rendering and difficult layout are central
- the user is willing to trade more speed/cost for better compliance

Use `gemini-2.5-flash-image` when:
- fast iteration matters most
- the task is simple
- the workflow is high-volume
