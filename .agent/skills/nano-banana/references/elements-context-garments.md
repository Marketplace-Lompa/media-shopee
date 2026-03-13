# Elements, Context, And Garment Consistency

Verified on 2026-03-12 using current public Google, Krea, and Higgsfield pages. This file is for practical routing and terminology, not as proof that a wrapper feature is native to the underlying Google model.

## Quick translation table

| User says | Best interpretation | Use first |
|---|---|---|
| "train this roupa" | exact garment consistency | `Elements` or object references |
| "quero a mesma roupa em varias fotos" | same SKU across scenes | `Element` plus object-lock prompting |
| "quero a mesma modelo com a mesma roupa" | model identity plus garment consistency | `Character lock` + `Element` |
| "quero a mesma linguagem visual da colecao" | campaign/world consistency | `Context` |
| "quero algo tipo lora" | reusable learned object or style | platform training, usually `Object` or `Style` |

## What each primitive is good for

### Context

Use for:
- campaign direction
- environment rules
- brand tone
- art direction
- what can and cannot change at the scene level
- logic between multiple references

Do not rely on Context alone for:
- exact SKU replication
- exact logo geometry
- fine garment construction details

### Elements

Use for:
- exact garments
- product bottles, packages, bags, shoes, jewelry
- logos or props that must recur
- reusable objects that should appear consistently across many scenes

Best practice:
- treat the element as the source of truth
- use high-resolution references
- avoid mixing near-duplicate but different SKUs

### Multi Reference

Use for:
- one image for model identity
- one image for garment
- one image for color palette
- one image for composition

Best practice:
- assign one role per image explicitly
- choose one image as the composition owner

### Object LoRA

Use for:
- repeated long-term reuse of the same product or garment
- high-volume production where manual re-anchoring becomes expensive
- cases where references alone keep drifting

Do not confuse with:
- `Elements`
- prompt-only object locking
- Google-native Gemini image features

## Krea mapping

Publicly visible and documented signals:
- the Nano Banana tool UI publicly shows `Context` and `Elements`
- Krea has official training docs for `Style`, `Object`, `Character`, and `Default`
- Krea training is a platform capability, not a Google-native Nano Banana API feature

Recommended Krea route for garments:
1. create or upload the clothing item as an `Element`
2. use `Context` for campaign instructions and styling rules
3. if a person must stay the same, add a person reference or character workflow
4. if fidelity still drifts after iteration, escalate to `Object` training

When to choose each Krea training type:
- `Object`
  -> exact product or garment
- `Style`
  -> collection look, fashion language, material mood
- `Character`
  -> same model/character identity

## Higgsfield mapping

Publicly visible and documented signals:
- Higgsfield exposes `World Context`, `Multi Reference`, `Product Placement`, `Banana Placement`, `Fashion Factory`, and `Soul ID` on current public pages
- public crawls did not expose a standalone documentation page for `Elements`, so if you see it in-app treat it as a wrapper-side reusable asset abstraction

Recommended Higgsfield route for garments:
1. use `Soul ID` if the same model identity must persist
2. use `Elements` or product-like asset inputs if available in your UI
3. use `Fashion Factory` when starting from a clean garment/product image
4. use `Multi Reference` when identity, garment, and scene each need different references
5. use `World Context` for campaign logic and known-world placement

## Garment dataset checklist

For best fidelity, collect:
- front view
- back view
- both side views
- 45-degree angle
- close-up of fabric texture
- close-up of seam construction
- close-up of collar, cuff, hem, buttons, zipper, or print
- one clean full-body on-body reference if drape matters
- one isolated product image if exact garment shape matters

Avoid:
- mixed colorways unless intentional
- low-resolution compressed marketplace screenshots
- inconsistent lighting that changes material perception
- multiple SKUs in one dataset

## Prompt patterns

### Element-first garment prompt

```text
Use the uploaded garment element as the exact clothing source of truth.
Preserve silhouette, neckline, seam placement, sleeve length, hem line, print scale, and fabric behavior exactly.
Place the garment on the subject in a photoreal campaign scene.
Change only pose, background, and camera angle.
Do not redesign or simplify the piece.
```

### Context brief for a campaign

```text
Campaign context:
- Brand tone: [minimal/luxury/youthful/editorial]
- Environment: [studio / street / resort / interior]
- Lighting: [soft daylight / hard flash / golden hour]
- Styling rules: [keep wardrobe premium / clean / neutral / bold]
- Output purpose: [ecommerce / ad / hero banner / social]

When using the garment element, preserve the item exactly across all generations.
```

### Same model plus same garment

```text
Use Image 1 as the identity reference for the model.
Use the garment element as the exact clothing reference.
Preserve the model's face and body proportions, and preserve the garment's construction details exactly.
Generate a coherent real photograph with consistent lighting and natural fabric behavior.
```
