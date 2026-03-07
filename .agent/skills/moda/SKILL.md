---
name: moda
description: >
  Skill for high-fidelity garment reproduction in AI image generation.
  Should be used when the goal is to accurately describe clothing items,
  fabrics, textures, draping, layered constructions (such as lace over
  lining), transparency, fit, and silhouette for maximum visual accuracy.
  Provides a structured vocabulary for textile properties, construction
  details, and light interaction that AI models respond to with higher
  precision. Relevant for: fashion photography, e-commerce product shots,
  lookbooks, catalog images, virtual try-on, any scenario involving
  clothing or textile reproduction.
---

# Fashion Garment Precision

## Core Philosophy

> **Clothing is not a surface — it is a system of layers, structures, and behaviors.**

AI models tend to treat garments as flat textures painted onto a body. Real clothing is a 3D construction with internal structure, multiple fabric layers, and physics-driven draping. The more precisely you describe **how the fabric behaves**, not just how it looks, the more accurate the output.

**The goal of this skill is to give the AI enough structural understanding of a garment to reproduce it as a real piece of clothing — not as a painted texture.**

---

## 🚨 Two Modes: Reference Image vs. Pure Creation

> **This is the most critical decision before writing any garment description.**

### Mode 1 — Reference Image Available (EDIT mode)
When a reference photo exists, **the image is the authority for the garment**. Text description works AGAINST fidelity if it is too detailed.

**Why:** AI image models weight text and image inputs simultaneously. If text describes the garment in high detail, the model re-generates the garment from text and treats the reference image as secondary. The result: a garment that matches the words, not the photo.

**Rule:** Use a Fidelity Lock FIRST, then a MAXIMUM of 2 reinforcement sentences. The reinforcement must follow this distinction:

| ✅ Reinforce in text | ❌ NUNCA descreva em texto (O nano model se confunde) |
|---|---|
| **Fiber/material/vibe**: modal, poliéster, algodão, viscose, couro | **Drawings/Prints**: listras, xadrez, floral, logos, desenhos em geral |
| **Construction type**: tricot, malha fina, malha grossa, tecido plano | **Texture patterns**: zigzag, diamond, openwork, wave, cable |
| **Precise color name** (if ambiguous in image) | **Surface details**: como o ponto do tricô/crochê parece visualmente |
| **Opacity**: `fully opaque fabric` when knit has openwork the AI may render as transparent holes | (anything already visible as solid or patterned in the reference) |

> 🚨 **REGRA CRÍTICA PARA TEXTURAS E ESTAMPAS:** Nunca descreva como o padrão ou textura se parece visualmente (ex: "listrado", "zigzag", "xadrez"). O modelo nano é excelente em puxar a imagem original, mas se você ditar o padrão em texto, ele sobrescreve a imagem por uma versão genérica da IA.
> Para o reforço: descreva apenas a natureza física da peça (ex: "heavy winter knitwear", "fine modal tricot", "cotton poplin").

```
Fidelity Lock template (Mode 1 — goes FIRST in the prompt):
REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. Reproduce the clothing 
exactly as shown in the attached reference photo. Follow the texture and 
stitch pattern exactly as shown — do not invent or describe the pattern, 
copy it from the reference image. Only the model, pose, and background are new.

Reinforcement only (max 2 sentences): [fiber/material] + [construction type] + [precise color].
```

### Mode 2 — No Reference Image (CREATE mode)
When no reference photo exists, use the full 3-Dimension framework below. This is the correct time for detailed garment description.

---

## The 3 Dimensions of Garment Description *(Mode 2 — no reference image)*

Every garment must be described across 3 independent dimensions:

### 1. Material (What it's made of)
The fiber, weave, and finish of the fabric.

### 2. Construction (How it's built)
The seams, closures, layers, and structural elements.

### 3. Behavior (How it moves)
The draping, fall, cling, and reaction to the body and gravity.

> ⚠️ **Most failed garment prompts only describe Dimension 1.** Dimensions 2 and 3 are what separate a "fabric texture" from a "real piece of clothing."

---

## Dimension 1: Material — The Fabric Vocabulary

### Base Fabric Types and Their Visual Signatures

Use these precise terms instead of generic ones. Each carries specific visual characteristics that AI models interpret differently.

#### Woven Fabrics (structured, less stretch)

| Fabric | Visual Signature | Light Behavior |
|--------|-----------------|----------------|
| **Cotton poplin** | Smooth, crisp, visible weave structure | Matte, absorbs light evenly |
| **Cotton chambray** | Soft denim-like, crossweave color variation | Subtle sheen, heathered appearance |
| **Linen** | Visible slub texture, natural wrinkles | Matte with slight luster on folds |
| **Raw denim** | Stiff, deep indigo, white selvedge edge | Dark matte, lighter at stress points |
| **Washed denim** | Soft, faded, whiskering at joints | Varied tones, lighter at creases |
| **Twill** | Diagonal rib pattern on surface | Subtle directional sheen |
| **Satin** | Ultra-smooth, liquid-like surface | High specular shine, deep shadows in folds |
| **Silk charmeuse** | Fluid, slightly clingy | Luminous sheen on one side, matte on reverse |
| **Silk organza** | Stiff, sheer, papery | Translucent, refracts light |
| **Chiffon** | Sheer, floaty, very lightweight | Semi-transparent, ghostly layers |
| **Taffeta** | Stiff, crisp, slight rustle implied | Iridescent sheen, sharp fold lines |
| **Wool crepe** | Matte, slightly grainy surface | Light-absorbing, soft shadows |
| **Wool flannel** | Soft, brushed, slightly fuzzy | Matte, warm appearance |
| **Tweed** | Multicolor flecked, chunky texture | Complex color interaction per thread |
| **Jacquard** | Woven-in pattern with texture variation | Pattern visible via light/shadow interplay |
| **Brocade** | Raised embroidered pattern on woven base | Metallic or contrasting sheen on pattern areas |

#### Knit Fabrics (stretch, drape)

| Fabric | Visual Signature | Yarn Weight Token | Light Behavior |
|--------|-----------------|-------------------|--------------|
| **Jersey** | Smooth, stretchy, slight roll at edges | `fingering weight / fine gauge` | Soft sheen, clings to body contour |
| **Ribbed knit** | Vertical ridges, visible texture columns | `medium gauge` | Light catches on ridges, shadows in valleys |
| **Cable knit / Aran** | Thick twisted rope braids with crossing depth | `bulky / chunky yarn` | Deep shadow between cables, highlight on tops |
| **Brioche** | Plush, reversible, squishy ribbed structure | `medium to bulky` | Directional light reveals layered rib depth |
| **Fair Isle / Jacquard** | Colorwork with crisp color transitions, no color bleeding | `fingering to sport weight` | Even diffuse light to reveal pattern without glare |
| **Openwork / Lace knit** | Delicate eyelets, blocking behavior, ethereal drape | `lace weight` | Backlight reveals transparency and negative space |
| **French terry** | Smooth face, looped pile on reverse | `medium gauge` | Matte face, plush inside visible at cuffs |
| **Waffle knit** | Grid-like 3D texture | `medium gauge` | Strong light-shadow contrast in grid |
| **Ponte** | Dense, structured, thick | `heavy gauge` | Smooth matte, holds shape |
| **Bouclé** | Looped, nubby, textured surface | `chunky / irregular ply` | Complex micro-shadow pattern |

#### Technical / Synthetic Fabrics

| Fabric | Visual Signature | Light Behavior |
|--------|-----------------|----------------|
| **Nylon ripstop** | Visible grid reinforcement pattern | Slight synthetic sheen |
| **Scuba/neoprene** | Thick, spongy, smooth | Matte, volume-holding |
| **Mesh** | Open grid, see-through | Patterned transparency |
| **Tulle** | Fine net, stiff, volumizing | Semi-transparent, layers build opacity |
| **Sequined fabric** | Reflective discs overlapping | Sparkle, strong specular highlights |
| **Vinyl/PU leather** | Glossy, smooth, slightly stiff | High shine, strong reflections |
| **Genuine leather** | Grain texture, natural variation | Matte to semi-gloss, patina |
| **Suede** | Soft napped surface, velvety | Ultra-matte, directional color change when brushed |
| **Velvet** | Dense pile, rich depth | Deep color, directional sheen depending on pile direction |

### Surface Treatments and Finishes

These modifiers change how the base fabric behaves visually:

| Treatment | Effect |
|-----------|--------|
| `stonewashed` | Softened, faded, worn-in look |
| `acid-washed` | Patchy bleached pattern, 80s/90s aesthetic |
| `garment-dyed` | Uneven color absorption, lived-in feel |
| `enzyme-washed` | Ultra-soft, slightly fuzzy surface |
| `coated / waxed` | Added water-resistance sheen, darker appearance |
| `brushed` | Soft, fuzzy surface (like brushed cotton flannel) |
| `mercerized` | Increased luster and color depth |
| `crinkled / crushed` | Permanent wrinkle texture |
| `embossed` | Raised pattern stamped into fabric |
| `distressed` | Intentional wear: fraying, holes, thinning |

---

## Dimension 2: Construction — How It's Built

### Structural Elements Vocabulary

Describing construction tells the AI about the garment's 3D architecture.

#### Seams and Joining

| Term | Description |
|------|-------------|
| `French seam` | Enclosed, no raw edges visible, clean finish |
| `flat-felled seam` | Double-stitched, visible topstitching (like jeans) |
| `serged/overlocked edge` | Finished with thread wrapping, visible on reverse |
| `raw edge / unhemmed` | Unfinished, may fray |
| `blind hem` | Invisible from outside |
| `contrast stitching` | Thread color differs from fabric (topstitch detail) |
| `piping` | Cord encased in fabric strip along seam |
| `binding` | Fabric strip wrapping raw edge (like on a neckline) |

#### Closures

| Term | Description |
|------|-------------|
| `concealed zipper` | Hidden, smooth closure line |
| `exposed metal zipper` | Visible teeth, industrial aesthetic |
| `button placket` | Folded fabric strip with buttonholes |
| `snap buttons` | Metal press-stud closure |
| `drawstring` | Cord threaded through casing |
| `wrap / tie closure` | Fabric ties, creates waist definition |
| `hook and eye` | Tiny metal closure, usually at top of zipper |

#### Necklines, Collars, and Sleeves

Instead of vague terms, use precise construction language:

| Element | Precise Description |
|---------|---------------------|
| **Neckline** | `crew neck`, `V-neck`, `scoop neck`, `boat neck`, `square neck`, `sweetheart`, `halter`, `mock neck`, `turtleneck`, `cowl neck` |
| **Collar** | `point collar`, `spread collar`, `Mandarin/band collar`, `Peter Pan collar`, `shawl collar`, `notch lapel`, `peak lapel` |
| **Sleeve** | `set-in sleeve`, `raglan sleeve`, `dolman/batwing sleeve`, `puff sleeve`, `bishop sleeve`, `bell sleeve`, `cap sleeve`, `flutter sleeve` |
| **Cuff** | `ribbed cuff`, `button cuff`, `French cuff`, `elastic cuff`, `rolled cuff`, `raw edge cuff` |

---

## Dimension 3: Behavior — How It Moves

This is the most neglected and most impactful dimension. Fabric behavior is what makes a garment look "worn" vs "rendered."

### Draping Vocabulary

| Term | When to Use | Visual Result |
|------|-------------|---------------|
| `drapes loosely` | Soft, flowing fabrics (silk, rayon) | Gentle cascading folds |
| `falls straight` | Medium-weight wovens (cotton, linen) | Clean vertical lines |
| `holds structure` | Stiff fabrics (denim, canvas, taffeta) | Defined shape, angular folds |
| `clings to body contour` | Stretch/thin fabrics (jersey, silk) | Reveals body shape underneath |
| `billows / catches air` | Lightweight fabrics in motion (chiffon, organza) | Inflated, floating away from body |
| `puddles at hem` | Excess length on fluid fabric | Fabric pools on floor/surface |
| `skims the body` | Medium drape, not tight not loose | Follows form without clinging |
| `stands away from body` | Stiff or structured garments | Creates gap between fabric and skin |

### Fold and Crease Behavior

| Term | Visual Result |
|------|---------------|
| `soft rounded folds` | Gentle U-shaped curves (silk, jersey) |
| `sharp angular creases` | Hard V-shaped lines (starched cotton, taffeta) |
| `crushed irregular wrinkles` | Random, organic crumpling (linen, gauze) |
| `draped swag folds` | Wide, elegant U-curves (satin, velvet) |
| `knife-edge pleats` | Crisp, repeated parallel folds |
| `accordion pleats` | Tight, even zigzag folds |
| `gathering / ruching` | Fabric bunched along a seam line |
| `natural wear creases` | Wrinkles at elbows, waist, behind knees |

### Body Interaction

| Term | When to Use |
|------|-------------|
| `tension across shoulders` | Fabric pulling slightly at shoulder seams |
| `pulling at buttons` | Slight gap between buttons when seated/moving |
| `bunching at waist` | Excess fabric gathering when tucked |
| `falling off one shoulder` | Casual, asymmetric positioning |
| `riding up` | Hem shifting higher (natural movement) |
| `stretching at joints` | Fabric taut at elbows, knees |

---

## Complex Constructions: Multi-Layer Garments

This is where most AI prompts fail. When a garment has multiple layers, you must describe **each layer independently** and then describe **their relationship**.

### The Layer Stack Pattern

```
Layer 1 (innermost/base): [fabric] + [opacity] + [fit]
Layer 2 (overlay): [fabric] + [transparency level] + [behavior relative to Layer 1]
Relationship: [how they interact visually]
```

### Common Multi-Layer Cases

#### Lace Over Lining
```
Base layer: opaque [color] stretch jersey lining that follows the body contour.
Overlay: [color] floral lace with [scalloped/straight] edges, sitting slightly 
away from the lining. The lace pattern is visible against the contrasting 
lining beneath. Where the lace overlay meets skin (neckline, sleeves), 
the skin is partially visible through the lace openwork.
```

**Key instruction:** Explicitly describe what is visible through the lace — skin or lining — at each zone of the garment.

#### Matching Sets / Two-Piece Layers (e.g., Coat + Scarf)
When a garment consists of two separate but matching pieces (same material/pattern), you **must force the physical separation** so the AI doesn't merge them into one blob.
```
Base piece: [color] [fabric] [garment type, e.g., cardigan/coat] worn open or wrapped.
Accessory piece: matching [color] [fabric] [garment type, e.g., scarf] draped 
AROUND THE NECK, physically separate from the coat. The scarf crosses over the 
chest forming distinct layers on top of the base piece.
```
**Key instruction:** Use words that denote physical layering and separation: "draped around," "layered over," "physically separate," "distinct piece."

#### Sheer Over Opaque
```
Base layer: fitted [color] camisole/slip acting as modesty lining.
Overlay: semi-transparent [fabric] in [color] that reveals the outline 
and color of the layer beneath. Neither fully transparent nor fully opaque — 
a veiled, diffused visibility of the base layer.
```

#### Mesh Panel Construction
```
Main body: opaque [fabric] in [color].
Mesh panels: [location — shoulders/sides/yoke] in tonal or contrast mesh, 
creating a peek of skin within a structured frame. The transition between 
opaque and mesh has [clean seam / raw edge / binding].
```

#### Lined Blazer / Jacket (Partially Visible)
```
Outer shell: structured [fabric] in [color] with [lapel type].
Inner lining: visible at inner facing, cuffs (when rolled), and hem edge. 
Lining in [contrasting color/pattern] — partially visible as a flash of 
detail when the jacket moves or is worn open.
```

#### Layered Tulle / Organza (Volume Building)
```
Multiple layers of [color] tulle stacked to build volume and opacity 
gradient. Innermost layer is most opaque; outer layers become increasingly 
sheer. Each layer's edge is visible as a softer, ghosted duplicate. 
Creating a cloud-like, dimensional volume that gets more transparent 
toward the edges.
```

#### Embroidery / Appliqué on Base
```
Base fabric: [type] in [color], smooth and even.
Surface detail: [embroidered/appliquéd] [motif description] in [thread/fabric type]. 
The embroidery creates raised texture — catching light on the top of the 
stitches while casting micro-shadows around the edges. The thread has 
[matte/sheen/metallic] finish.
```

---

## Light Interaction by Fabric Type

How the AI renders light on fabric is critical. Use these cues:

### The Light Response Matrix

| Fabric Property | Light Response | Prompt Language | 💡 Lighting Pairing |
|-----------------|---------------|-----------------|---------------------|
| **Matte** (cotton, linen) | Absorbs light, soft diffuse | `"absorbs light softly, no specular highlights"` | Diffused natural light |
| **Sheen** (silk, satin) | Directional highlight, smooth gradient | `"luminous sheen along drape direction, highlights follow the folds"` | Backlight para bordas + fill lateral |
| **Metallic** (lamé, sequins) | Strong specular, point reflections | `"catches light with sharp pinpoint reflections"` | Three-point softbox (evita reflexos estourados) |
| **Transparent** (chiffon, organza) | Transmits light through | `"light passes through, creating color-shifted shadow beneath"` | Backlight para revelar transparência |
| **Napped** (velvet, suede) | Directional color shift | `"color shifts deeper/lighter depending on viewing angle and pile direction"` | Side lighting direcional |
| **Textured** (cable knit, tweed) | Complex micro-shadows | `"light creates ridges of highlight and valleys of shadow across the texture"` | Rembrandt lighting (profundidade tátil) |
| **Leather / Couro** | Grain relief, pore depth, diffuse reflection | `"pebble grain texture, matte finish, structural seam shadows"` | Side lighting (enfatiza relevo do grão) |
| **Wool / Cashmere** | Soft halo, long-staple fiber glow | `"dense knit, soft halo at fiber edges, warm matte depth"` | Rembrandt lighting |
| **Reflective** (vinyl, patent) | Mirror-like surface reflection | `"reflects surrounding environment in a distorted, curved mirror"` | Three-point studio |

> 💡 **Regra do par câmera × textura:** Para detalhe de malha/trama, sempre especifique `"macro lens"` no prompt. Para fashion shot com textura visível, use `"85mm f/1.8"` — essa lente comprime a profundidade e destaca a superfície do tecido enquanto desfoca o fundo com bokeh natural.

---

## Common AI Failures with Clothing & How to Fix

| Failure | Why It Happens | Fix |
|---------|---------------|-----|
| **Flat texture, no draping** | Only described material, not behavior | Add Dimension 3 terms (draping, folds, body interaction) |
| **Lace looks painted on** | Didn't describe transparency layers | Use the Layer Stack Pattern with explicit transparency zones |
| **Fabric looks brand new** | No wear indicators | Add `"natural wear creases"`, `"soft from repeated washing"` |
| **Uniform color across garment** | Didn't describe light variation | Add `"color slightly deeper in folds, lighter where fabric catches light"` |
| **Stiff body, no movement** | Pose is static, fabric follows suit | Describe mid-movement fabric behavior (`"skirt caught in a slight breeze"`) |
| **Wrong fabric weight** | Generic description like "dress" | Specify weight: `"lightweight flowing chiffon"` vs `"heavy structured brocade"` |
| **Seams invisible/unrealistic** | Didn't mention construction | Add at least 1-2 construction details (stitching, seam type) |
| **Pattern distortion** | Pattern doesn't follow fabric folds | Add `"pattern follows the contour and folds of the fabric naturally"` |
| **Shiny matte fabric** | Conflicting light cues | Be explicit: `"completely matte cotton, zero specular highlights"` |
| **Transparency wrong** | Unspecified opacity level | State exactly: `"30% transparent — skin tone visible but diffused beneath"` |

---

## The Fidelity Lock System

When reproducing a garment from a reference image, use a **Fidelity Lock** — a structured instruction block that tells the AI exactly what to preserve and what to change.

### Full Fidelity Lock Template

```
GARMENT FIDELITY LOCK:
- Fabric: [exact type] with [texture description]
- Color: [precise color, not generic — e.g., "dusty sage" not "green"]
- Pattern: [exact pattern description following fabric contours]
- Construction: [key details — neckline, sleeves, closure, hem]
- Fit: [how it relates to the body — loose/fitted/oversized]
- Draping: [how the fabric falls and folds]
- Light response: [matte/sheen/metallic — how it reacts to light]

CHANGE FREELY:
- Model appearance, pose, expression
- Background/setting
- Lighting direction and mood
- Camera angle
```

### Minimal Fidelity Lock (Quick Version)

```
Keep the clothing exactly as shown: [fabric type], [color], [key construction detail], 
[draping behavior]. Pattern follows fabric folds naturally. 
Everything else (model, background, pose) is completely new.
```

---

## Garment Description Checklist

Before finalizing any prompt involving clothing, verify:

- [ ] **Fabric type specified?** (not just "dress" but "cotton poplin dress")
- [ ] **Behavior described?** (drapes, clings, holds structure, billows)
- [ ] **Construction details present?** (at least neckline + closure + hem)
- [ ] **Light interaction defined?** (matte, sheen, transparent)
- [ ] **Multi-layer garments: each layer described independently?**
- [ ] **Transparency zones explicit?** (where skin vs lining is visible)
- [ ] **Pattern behavior specified?** (follows folds or remains flat)
- [ ] **Fit described?** (oversized, fitted, relaxed, structured)
- [ ] **Wear state indicated?** (brand new, lived-in, distressed)

---

## Textile Surface Vocabulary *(Mode 1 — Reinforcement tokens for textured garments)*

> 💡 **Thinking Mode:** Para padrões de tricô complexos (Aran, Fair Isle, openwork), o Nano Banana Pro planeja as sombras e a profundidade do ponto *antes* de renderizar os pixels. Isso evita o padrão "colado" onde a trama parece uma textura plana sobre o corpo. Para ativar: mencione `"complex textile construction"` ou `"structured knitwear physics"` no prompt — o modelo prioriza o raciocínio estrutural.

> **When to use this section:** Quando a referência visual existe mas o modelo gera a textura errada — loops inflados, ponto distorcido, peso visual incorreto. Use os tokens desta seção como reforço cirúrgico no prompt (máximo 1–2 frases), NUNCA descrevendo o padrão visual.

### A Regra Anti-Inflação

O Nano Banana tende a "inflaro ponto" de peças texturizadas — loops ficam gordos, redondos e 3D quando a peça real é plana e regular. Isso acontece porque o modelo interpreta "knitwear" como estrutura volumosa por padrão.

**Solução:** usar tokens que descrevem a SUPERFÍCIE e o PESO da construção, não a aparência do ponto.

---

### Crochê

| Vibe da peça real | ✅ Token correto | ❌ Token que gera inflação |
|---|---|---|
| Ponto plano, fileiras regulares, peso médio | `flat uniform crochet construction` | `crochet loops`, `3D crochet texture` |
| Crochê leve, aberto, vazado | `open-weave crochet, airy construction` | `chunky crochet` |
| Crochê grosso mas deitado, não inflado | `coarse flat-stitched crochet panel` | `puffy crochet`, `round bumps` |
| Crochê com listras de cor alternate | `color-band crochet, flat surface` | (nunca descreva as faixas — a imagem mostra) |

> ⚠️ **Anti-trap específico do crochê:** Nunca use `loops`, `bumps`, `rounds`, `bobbles`, `3D`, `dimensional`, `puffy`, `raised rounds` — esses termos ativam a síntese volumosa do Nano.

**Vocabulary avançado (Precision Knitwear):**

| Tipo | Token de precisão | Efeito |
|---|---|---|
| Crochê ponto baixo regular | `flat single-crochet construction, even stitch rows` | Fileiras planas e uniformes |
| Crochê ponto alto | `tall open-stitch crochet, airy vertical loops` | Espaço entre fileiras visível |
| Crochê relevo controlado | `surface relief crochet, controlled stitch depth` | Relevo presente mas não inflado |

---

### Tricô

| Vibe da peça real | ✅ Token correto | ❌ Token que gera erro |
|---|---|---|
| Malha fina, lisa, bem comportada | `smooth fine-gauge jersey knit` | `knit texture`, `visible stitches` |
| Tricô de inverno, grosso mas plano | `heavy flat-knit construction, dense gauge` | `chunky cable knit` (→ gera tranças) |
| Canelado vertical | `vertical rib-knit construction` | `ribbed texture` (muito genérico) |
| Cardigan de malha aberta | `open-stitch knit panel, semi-transparent mesh effect` | `lace knit` (→ gera renda floral) |

> ⚠️ **Anti-trap específico do tricô:** Evite `cable` a menos que a peça seja realmente de tranças — o Nano gera tranças agressivas mesmo com referência. Para tricô grosso sem padrão visual, use `thick flat-knit` ou `heavy solid-color knit`.

**Vocabulary avançado por tipo de ponto:**

| Tipo de ponto | Token de precisão |
|---|---|
| Tranças Aran (cable) | `chunky Aran cable-knit, visible yarn plies, crossing depth defined, soft side shadows within braids` |
| Brioche | `plush brioche stitch, reversible rib structure, high-loft yarn, deep tuck-stitch shadows` |
| Canelado (ribbing) | `vertical rib-knit construction, deep shadows in rib valleys, elastic recovery implied` |
| Fair Isle / colorwork | `crisp color transitions, non-floated color blocks, flat graphic colorwork surface` |
| Openwork / Lace | `delicate lace eyelets, blocking behavior visible, ethereal drape, negative space integral to design` |

**Yarn weight como controle de escala do ponto:**

| Espessura desejada | Token |
|---|---|
| Ponto muito fino, delicado | `fingering weight yarn, fine gauge knit` |
| Ponto médio, versátil | `DK weight / sport weight yarn` |
| Ponto grosso de inverno | `bulky yarn, heavy gauge, chunky construction` |
| Maxi ponto, ultra volumoso | `super bulky yarn, oversized stitch scale` |

---

### Tecido Plano Texturizado

| Vibe da peça real | ✅ Token correto |
|---|---|
| Tweed sem estampa aparente | `heathered woven tweed, flat nubby surface` |
| Canvas/lona pesado | `stiff canvas-weight woven construction` |
| Brocado com relevos | `raised jacquard surface, woven-in texture contrast` |

---

### Tokens de Intensidade de Textura

Quando você precisar calibrar o QUANTO de textura aparece na superfície:

| Nível | Token | Uso |
|---|---|---|
| Mínimo | `subtle surface texture, nearly smooth` | Peças "quentinhas" mas sem textura visual forte |
| Médio | `visible construction texture, even rows` | Tricô/crochê com ponto visível mas regular |
| Máximo | `strongly textured surface, deep construction relief` | Quando a textura é o hero (macro shots, close-ups) |

---

### Textural Anchor — Técnica Multi-Referência (recomendada para textura crítica)

O Nano Banana Pro e 2 suportam **até 14 imagens de referência** na mesma sessão. Para transferência fiel de textura de tecido, use a técnica **Textural Anchor**:

**Setup de referências:**

| Imagem | Papel | O que enviar |
|---|---|---|
| **Ref 1** | Autoridade de identidade/modelo | Foto da pessoa (quando reusar modelo) |
| **Ref 2** | Autoridade de textura | Swatch ou macro close-up do tecido real |
| **Ref 3** (opcional) | Autoridade de silhueta | Sketch ou foto do caimento desejado |

**Interface:** Ajustar o **Influence Slider para 70–80%** ao usar referência de textura. Abaixo de 70% = textura ignorada. Acima de 80% = composição distorcida.

**Template de prompt com Textural Anchor:**
```
IMAGE 1 is the composition to preserve. IMAGE 2 is the exclusive texture 
authority. Apply the exact fabric surface from IMAGE 2 to the garment in 
IMAGE 1: replicate stitch structure, loop size, yarn plies, row regularity, 
and surface flatness exactly as shown. Apply only to the garment surface. 
Keep model, pose, composition, lighting, and scene from IMAGE 1 unchanged.
```

**Para geração do zero (sem imagem de cena):**
```
REFERENCE IMAGE IS THE TEXTURE AUTHORITY. Reproduce the exact fabric 
construction as shown: [flat uniform crochet / brioche / Aran cable — 
descrever a vibe sem o padrão visual]. Generate [modelo + cena + pose].
```

> ⚠️ **Limitação do Gemini App:** O app pode ficar "preso" na primeira imagem durante iterações longas. **Solução:** reiniciar o chat com todas as referências novamente é mais eficiente que insistir em prompts correção. Ferramentas como Weavy ou Higgsfield têm controle de papel por imagem mais preciso para uso profissional.

---

## Integration with Other Skills

This skill works as a **precision layer for garment description**. Combine with:

- **Skill `realismo`**: Apply realism levers to make the fashion photo feel authentic (natural lighting, organic composition, imperfect focus)
- **Workflow `/edit-image`**: Feed garment descriptions from this skill into the base prompt structure
- **Workflow `/puxar-foto-shopee`**: After downloading reference images, use this vocabulary to describe garments with maximum precision

**Recommended flow:**
1. Analyze the garment (visual reference or mental image)
2. Describe using the 3 Dimensions (Material → Construction → Behavior)
3. For complex garments, apply the Layer Stack Pattern
4. Add a Fidelity Lock if reproducing from reference
5. Combine with `realismo` skill for authentic final output
