---
name: realismo
description: >
  Skill for generating photorealistic images indistinguishable from reality.
  Should be used when the goal is to create photos that look like they were
  taken by a real person with a real phone or camera — not by a professional
  studio and not by AI. Applies calculated human imperfections to break the
  "artificial perfection" that exposes AI-generated images.
  Relevant for: product photos, lifestyle, lookbook, social media,
  e-commerce, catalog, any scenario where the image must look authentic
  and organic.
---

# Imperceptible Realism

## Core Philosophy

> **Perfection is the enemy of realism.**

AI images fail to look real not because of lack of quality, but because of **excess quality**. Real photos taken by real people carry subtle imperfection markers that our brain unconsciously recognizes as "authentic." When these markers are absent, something feels "off" — even if the viewer can't explain what.

**The goal of this skill is not to generate a beautiful photo. It is to generate a photo that no one questions.**

---

## The Imperfect Authenticity Principle

Every real photo carries 3 layers of imperfection:

### 1. Equipment Imperfection
The camera or phone leaves its mark:
- Slight chromatic aberration at the edges
- Subtle grain/noise (especially in shadows)
- Micro-focus variation (not everything is perfectly sharp)
- JPEG compression (subtle artifacts in high-contrast areas)
- Slight lens distortion (barrel distortion from phone wide-angle)

### 2. Photographer Imperfection
The person taking the photo is not perfect:
- Composition **almost** centered, but not mathematically perfect
- Horizon **slightly** tilted (0.5° to 2°)
- Subject unintentionally cropped (top of head, foot, elbow)
- Captured moment between poses (not the "best moment")
- Subject distance is not the ideal studio distance

### 3. Environment Imperfection
The real world doesn't cooperate:
- Background objects that weren't "cleaned" (cup on table, loose hair strand)
- Mixed lighting (natural + artificial light blending)
- Unwanted reflections on surfaces (glasses, storefronts, screens)
- Shadows in slightly inconsistent directions
- Micro-movement (slight motion blur on extremities: hair, hands)

---

## How to Apply: The 7 Levers of Realism

When building any prompt that needs to look real, inject at least **3 of the 7 levers** below. Never use all of them at once — overdoing imperfection is just as artificial as perfection.

### Lever 1: Real Device + Lens
State that the photo was taken with a specific device **and lens combination**.

**Concept:** The model adjusts aberration, grain, compression, and perspective to simulate the optical characteristics of that device. The lens specification is equally important — it changes how texture is compressed and rendered.

**Device × Context pairing:**

| Context | Device | Why |
|---|---|---|
| Social/lifestyle authentic | Samsung Galaxy, iPhone 14, Xiaomi Redmi | Visible phone characteristics (barrel distortion, aggressive sharpening) |
| E-commerce semi-pro | Sony A7 III, Fujifilm X-T4 | Clean color science, slight film feel |
| Fashion editorial | Leica M11, Sony FX3 | Cinematic grain, color depth without studio perfection |
| Extreme color fidelity | Hasselblad X2D | ⚠️ Pulls toward studio perfection — avoid for authentic lifestyle |

**Lens pairing for textile work:**

| Goal | Lens | Effect |
|---|---|---|
| Fashion shot (garment + model) | `85mm f/1.8` | Compresses depth, highlights fabric texture, natural bokeh |
| Fabric detail / macro | `macro lens, close focus` | Reveals individual fiber and stitch at 1:1 scale |
| Environmental fashion | `35mm f/2.0` | Wide context with slight organic distortion |
| Intimate mid-shot | `50mm f/2.8` | Neutral, documentary feel |

> 💡 **Macro lens = obrigatório** para shots de detalhe de trama (tricô, crochê, rendas). Sem ele, o modelo gera textura interpolada, não fibras reais.

### Lever 2: Uncontrolled Lighting
Describe lighting that **happens**, not lighting that was **designed**.

**Concept:** Studio lighting (softbox, ring light) screams "professional production." Natural lighting with inconsistencies screams "real moment."

Useful elements:
- Light coming through a window, creating hard shadows on one side
- Mix of warm (tungsten) and cool (daylight) light
- Unintentional backlight (subject partially silhouetted)
- Ambient lighting (ceiling light, storefront, partial sunset)

### Lever 3: Organic Composition
Describe framing that a **real** person would do.

**Concept:** Professional photographers use rule of thirds, leading lines, and calculated negative space. Real people point the phone and press the button.

Useful elements:
- Subject slightly off-center
- Something at the edge of the frame that shouldn't be there
- Angle slightly above or below eye level
- Slight digital zoom (instead of optimal focal length)

### Lever 4: Surface Texture
Describe textures with **natural defects**.

**Concept:** AI tends to generate homogeneous, uniform surfaces. The real world has texture variation on everything.

Useful elements:
- Skin with visible pores, slight oiliness, sun marks
- Fabric with micro-wrinkles from use, not "freshly ironed"
- Surfaces with subtle dust, fingerprints, microscopic scratches
- Hair with loose strands and flyaways (not perfectly styled)

### Lever 5: Moment, Not Pose
Describe action **between** moments, not **at** the perfect moment.

**Concept:** Most real photos capture the instant before or after the "ideal moment." It's the "almost-smile," the hand still in motion, the gaze that hasn't found the camera yet.

Useful elements:
- Mid-action (in the middle of a gesture, not at the final position)
- Gaze directed at something off-frame (not at the camera)
- Ambiguous facial expression (not the perfect smile)
- Relaxed and asymmetrical posture

### Lever 6: Imperfect Depth
Describe focus that **almost** got it right.

**Concept:** Phone autofocus and consumer cameras sometimes focus on the wrong point — on the background instead of the subject, on the shoulder instead of the eye. A microscopically wrong focus is the strongest marker of a real photo.

Useful elements:
- Focus on chest/shoulder instead of eyes
- Foreground slightly soft, background sharp (opposite of expected)
- One hand sharp, the other slightly out of focus
- Slightly irregular bokeh (not perfectly circular)

### Lever 7: Capture Artifacts
Describe marks from the real capture process.

**Concept:** Every real photo carries evidence that it was captured, processed, and compressed by a real technology chain.

Useful elements:
- Subtle film grain or digital noise in shadows
- Slight purple fringing in high-contrast areas
- Visible JPEG compression in sky gradients
- Uncorrected white balance (slightly too warm or too cool)
- Natural lens vignetting

### Lever 8: Grain Injection (pós-geração — corrige AI Softness)

**Conceito:** Imagens geradas por IA às vezes sofrem de "AI Softness" — uma nitidez artificial ou suavidade excessiva nas fibras e superfícies que delata a origem digital. A Grain Injection ancora a imagem na realidade quebrando essa homogeneidade.

**Quando usar:** após gerar uma imagem de tecido texturizado que parece "plástico" ou "pintado" nas fibras.

**No prompt:**
```
Subtle monochromatic grain (1-3%), natural fiber micro-texture visible, 
no AI smoothing on fabric surface, yarn filaments individually distinct.
```

**Em pós-processamento (Photoshop/Lighroom):**
1. Aplicar filtro de ruído monocromático (**1–3%**) sobre a imagem
2. Usar filtro "Mínimo" na máscara de camada para esconder frangias brancas/pretas nas bordas da roupa
3. Resultado: textura de fibra âncora na percepção de realidade

> ⚠️ Não exagere. Acima de 4% de grain o efeito se torna visível como artifício — especialmente em pele.

---

## Anti-Patterns: What NOT to Do

These practices destroy realism and turn the image into "obvious AI":

| ❌ Anti-Pattern | Why it destroys realism |
|----------------|------------------------|
| `"perfect lighting"` | Perfect lighting doesn't exist in the real world |
| `"flawless skin"` | Skin without imperfections = wax mannequin |
| `"symmetrical composition"` | Perfect symmetry = digital rendering |
| `"studio backdrop"` | Clean background = professional session |
| `"8K, ultra HD, masterpiece"` | Quality tags force the model into "AI mode" |
| `"anatomically perfect"` | Anatomical perfection is inhuman |
| `"professional photography"` | Pulls the model toward studio aesthetics |
| Multiple art styles | `"hyperrealistic cinematic watercolor"` is incoherent |
| Perfect smile | Stock photo smiles are the #1 fake marker |

---

## Calibrating Intensity

Not every image needs the same level of "amateurism." Calibrate according to context:

### Level 1 — Casual Authentic (social media, lifestyle)
Use **5-7 levers** at high intensity.
Should look like: selfie, friend's photo, Instagram story.

### Level 2 — Semi-Professional (e-commerce, catalog)
Use **3-4 levers** at moderate intensity.
Should look like: photo taken with a good phone by someone who understands a bit of photography, but isn't professional. The type of photo an indie brand would post.

### Level 3 — Natural Professional (editorial, lookbook)
Use **2-3 levers** at subtle intensity.
Should look like: independent magazine editorial, fashion blog. Well-photographed, but not over-produced.

---

## Mental Validation Checklist

Before finalizing a prompt, run through this checklist:

- [ ] **Does the photo have at least one thing "wrong"?** (If everything is perfect, it's AI)
- [ ] **Is the lighting mixed or natural?** (If it's studio lighting, it's AI)
- [ ] **Is the subject between moments?** (If they're in the perfect pose, it's AI)
- [ ] **Is there something in the background that "shouldn't be there"?** (If the background is clean, it's AI)
- [ ] **Is the focus microscopically off?** (If everything is 100% sharp, it's AI)
- [ ] **Is the composition organic?** (If it's mathematically centered, it's AI)
- [ ] **Did I avoid forced quality tags?** (`8K`, `masterpiece`, `ultra HD`)

---

## Integration with Other Workflows

This skill is a **conceptual layer** that applies on top of any other workflow or prompt. It does not replace the description of the subject, clothing, or setting — it **adds the authenticity layer** that makes the difference between "impressive AI" and "real photo."

**Recommended flow:**
1. Build the base prompt (subject, clothing, setting, action)
2. Apply the realism levers from this skill
3. Remove any term that breaks authenticity (checklist above)
4. Review: "If I saw this photo on Instagram, would I be suspicious?"
