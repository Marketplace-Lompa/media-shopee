---
name: frames
description: >
  Skill for generating start and end frame pairs for AI video models
  like Veo3, Kling, Runway, and similar tools. Purely technical prompt
  engineering focused on creating controlled variations of the same image
  to produce smooth, natural-looking video when used as keyframes.
  Should be used when the goal is to create image pairs that serve as
  first and last frames for video interpolation, ensuring identity
  consistency, physics coherence, and natural motion between frames.
  Relevant for: video ads, product videos, fashion lookbook videos,
  social media reels, any scenario requiring AI-generated video from
  keyframe pairs.
---

# Video Frame Engineering

## Core Philosophy

> **A great video starts with two great photos that tell a story of motion.**

Video generation models like Veo3 and Kling don't create motion from nothing — they **interpolate** between states. The quality of the output is directly proportional to how well the start and end frames communicate what motion should happen between them.

**The goal is to create two images that are clearly the same scene, same moment, but separated by a precise, intentional delta of change.**

---

## The Delta Principle

The "delta" is the **difference** between Frame A (start) and Frame B (end). Too little delta = static, boring video. Too much delta = incoherent, glitchy video.

### The Delta Spectrum

```
[No Delta]          [Sweet Spot]              [Too Much]
Frame A = Frame B   Frame A → plausible → B   Frame A ≠ Frame B
Still image         Smooth natural video       Glitch, morph, artifact
```

### Delta Calibration by Video Model

| Model | Ideal Delta | Notes |
|-------|-------------|-------|
| **Veo3** | Medium — handles moderate changes well | Good with camera movement, lighting shifts |
| **Kling 2.0** | Low to Medium — prefers subtle changes | Excels at subject micro-movement, facial expression |
| **Runway Gen-4** | Medium to High — handles larger deltas | Good with scene transitions, dramatic changes |

> ⚠️ **Golden Rule:** If you can't describe the motion between frames in one simple sentence, the delta is too complex.

### Video Duration Calibration

The delta size must be proportional to the desired video duration. Small deltas produce short clips (2-3s) that feel choppy and "picotado" when stitched together. **Default to 5-8 seconds** for smooth, cinematic results.

| Duration | Delta Size | Spatial Displacement | Best For |
|----------|-----------|---------------------|----------|
| **2-3s** | Micro — blink, slight smile, weight shift | < 1 meter | Beauty shots, transitions, B-roll inserts |
| **5-8s** ⭐ | Medium — walking sequence, camera orbit, full gesture | 3-8 meters | **Default. Product videos, fashion reels, social media** |
| **8-12s** | Large — full scene traversal, dramatic reveal | 8-15 meters | Hero content, brand films, cinematic ads |

> ⭐ **Default Rule:** Always calibrate for **5-8 seconds** unless the user specifies otherwise. This avoids the "slideshow effect" of stitching micro-clips together.

**Video prompt must always include duration:**
```
"5 to 8 seconds, smooth continuous shot"
```

---

## The 6 Types of Delta

Every frame pair uses one or more of these delta types. **Never combine more than 2 types** in a single pair — video models struggle with simultaneous multi-axis changes.

### Type 1: Camera Movement Delta

The subject stays still. The camera moves.

| Movement | Frame A | Frame B | Video Result |
|----------|---------|---------|--------------|
| **Pan right** | Subject on left of frame | Subject on right of frame | Camera glides horizontally |
| **Pan up / Tilt up** | Framing at waist level | Framing at face level | Camera rises smoothly |
| **Dolly in (zoom)** | Wide shot, full body | Medium shot, waist up | Camera moves toward subject |
| **Dolly out** | Medium close-up | Wide shot with environment | Camera pulls back |
| **Orbit** | Subject at 0° angle | Subject at 30-45° angle | Camera circles around |
| **Crane up** | Eye level angle | Slightly elevated angle | Camera rises above |

**Prompt Pattern:**
```
Frame A: [Full scene description]. Shot from [position/angle A].
Frame B: Same scene, same moment. Shot from [position/angle B]. 
Everything identical except camera position.
```

**Key constraint:** The subject, clothing, lighting, and expression must be **pixel-identical** between frames. Only the perspective changes.

### Type 2: Subject Movement Delta

The camera stays still. The subject moves.

| Movement | Frame A | Frame B | Video Result |
|----------|---------|---------|--------------|
| **Walking** | Right foot forward | Left foot forward (1-2 steps later) | Natural stride |
| **Head turn** | Looking left | Looking right (or at camera) | Gentle head rotation |
| **Hair toss** | Hair settled | Hair lifted mid-toss | Wind/movement effect |
| **Hand gesture** | Hand at side | Hand raised or adjusting garment | Natural gesture |
| **Weight shift** | Weight on left hip | Weight on right hip | Casual sway |
| **Sit to stand** | Seated position | Standing position | Rising motion |

**Prompt Pattern:**
```
Frame A: [Subject description] in [pose A]. [Setting]. [Lighting].
Frame B: Same person, same clothing, same setting, same lighting. 
Now in [pose B]. The transition between poses is [simple, single-axis movement].
```

**Key constraint:** Only ONE body part or axis changes. Don't combine "head turn + arm raise + step forward" — pick one.

### Type 3: Expression Delta

Everything stays still. Only the face changes.

| Expression | Frame A | Frame B | Video Result |
|------------|---------|---------|--------------|
| **Neutral to smile** | Relaxed, neutral face | Gentle smile, eyes crinkling | Warming expression |
| **Looking away to camera** | Eyes directed off-frame | Eyes meeting the camera | Engaging eye contact |
| **Serious to laugh** | Composed expression | Mid-laugh, natural joy | Burst of laughter |
| **Blink** | Eyes open | Eyes half-closed | Natural blink cycle |
| **Surprise** | Calm expression | Eyebrows raised, mouth slightly open | Reaction moment |

**Prompt Pattern:**
```
Frame A: [Subject description] with [expression A]. [Everything else identical].
Frame B: Exact same person, position, clothing, lighting. 
Expression changed to [expression B]. Nothing else changes.
```

**Key constraint:** Expression deltas work best alone. Don't combine with body movement.

### Type 4: Fabric / Garment Movement Delta

Subject and camera still. Clothing responds to wind or gravity.

| Movement | Frame A | Frame B | Video Result |
|----------|---------|---------|--------------|
| **Wind catch** | Dress hanging naturally | Dress billowing to the side | Breeze effect |
| **Coat opening** | Jacket closed | Jacket open, revealing inner layer | Reveal effect |
| **Scarf flutter** | Scarf draped on shoulders | Scarf lifted by wind | Dynamic accessory |
| **Skirt swirl** | Skirt at rest | Skirt mid-twirl, fabric fanned out | Spinning motion |
| **Hair + fabric combo** | Hair and fabric at rest | Both caught in same wind direction | Environmental wind |

**Prompt Pattern:**
```
Frame A: [Subject] wearing [garment at rest]. No wind, fabric hanging naturally. 
Frame B: Same person, same position. A gentle breeze from [direction] 
catches the [garment element], lifting/pushing it [direction]. 
Hair responds to the same breeze consistently.
```

**Key constraint:** Wind direction must be consistent across all affected elements (hair, fabric, accessories must all respond to the same wind).

### Type 5: Lighting / Time Delta

Subject and composition stay still. Light changes.

| Change | Frame A | Frame B | Video Result |
|--------|---------|---------|--------------|
| **Sunrise / Sunset progression** | Golden hour, warm side light | Dusk, deeper warm tones | Time lapse feel |
| **Cloud passing** | Direct sunlight, sharp shadows | Diffused light, soft shadows | Natural light shift |
| **Neon flicker** | Neon sign at full brightness | Neon sign dimmer, different color | Urban atmosphere |
| **Light on / off** | Room with window light only | Room with warm lamp turned on | Interior mood shift |
| **Shadow shift** | Shadow at 45° angle | Shadow at 60° angle (time passed) | Subtle time passage |

**Prompt Pattern:**
```
Frame A: [Scene] with [lighting condition A]. 
Frame B: Identical scene, identical subject position. 
Lighting changed to [condition B]. All shadows and 
reflections are consistent with the new light source.
```

### Type 6: Environment / Parallax Delta

Subject still. Background shifts (suggesting camera or subject movement through space).

| Change | Frame A | Frame B | Video Result |
|--------|---------|---------|--------------|
| **Background parallax** | Background objects position A | Same objects shifted slightly | Depth and movement |
| **People passing** | Background clear | Person walking through background | Life and activity |
| **Vehicle passing** | Empty street | Car mid-frame in background | Urban energy |
| **Seasonal hint** | Green leaves | Leaves slightly yellowed | Subtle time passage |

---

## Frame Consistency Rules

The #1 failure mode is **inconsistency between frames**. Video models amplify any difference into jarring visual artifacts.

### What MUST Stay Identical Between Frames

| Element | Tolerance |
|---------|-----------|
| **Subject identity** | 0% change — same person, same face, same features |
| **Clothing** | 0% change — same garment, same color, same pattern |
| **Accessories** | 0% change — same jewelry, bag, shoes |
| **Setting / Location** | 0% change — same place, same background elements |
| **Color grading** | 0% change — same warmth, contrast, saturation |
| **Aspect ratio** | 0% change — identical dimensions |
| **Resolution** | 0% change — identical quality |

### What CAN Change (The Delta)

Only the elements you intentionally specify as your delta type. Everything else is frozen.

### Consistency Enforcement Language

Always include one of these locks in both frame prompts:

```
"Maintain absolute identity consistency — same person, same clothing, 
same setting, same lighting temperature, same color grading. 
The ONLY change is [your specific delta]."
```

```
"This is the exact same scene, same moment. Nothing has changed 
except [your specific delta]. Preserve every other detail with 
100% fidelity."
```

---

## The Frame Pair Prompt Template

### Standard Template

```
=== FRAME A (Start Frame) ===

[Style/aesthetic]. [Subject full description — model, clothing, expression, pose]. 
[Setting/environment with specific details]. [Lighting description]. 
[Camera angle and lens]. [Specific position/state of the delta element].

=== FRAME B (End Frame) ===

Identical scene to Frame A. Same person, same clothing, same setting, 
same lighting, same camera lens, same color grading. 

THE ONLY CHANGE: [Precise description of what changed — the delta]. 

Everything else remains pixel-identical to Frame A.
```

### Minimal Template (For Fast Iteration)

```
Frame A: [Scene]. [Subject at state A].
Frame B: Same scene. [Subject at state B]. Nothing else changes.
```

---

## Motion Complexity Tiers

Use these tiers to calibrate how ambitious your frame pair should be.

### Tier 1 — Micro Motion (Safest, Highest Success Rate)

Barely perceptible changes that create subtle, elegant video.

- Blink
- Slight smile
- Wind catching a single strand of hair
- Breathing (chest rising slightly)
- Gentle weight shift

**Best for:** Beauty shots, product focus, contemplative mood.

### Tier 2 — Natural Motion (Reliable, Standard Use)

Clear but simple single-axis movement.

- Head turn (30° maximum)
- Camera dolly in or out
- Single hand gesture
- Fabric responding to breeze
- Walking 1-2 steps

**Best for:** Fashion videos, product demos, social media content.

### Tier 3 — Dynamic Motion (Moderate Risk, High Impact)

More dramatic changes that push video model capabilities.

- Full body turn (front to 3/4 or profile)
- Sitting down or standing up
- Hair toss + wind combo
- Camera orbit 30-45°
- Lighting transition (golden hour to dusk)

**Best for:** Hero content, brand videos, cinematic ads.

### Tier 4 — Complex Motion (High Risk, Expert Only)

Ambitious changes that require elite prompt control.

- Full walking sequence (3+ steps)
- Garment removal/addition (jacket on → off)
- Multiple simultaneous deltas
- Environment change (indoor → outdoor)
- Dramatic lighting shift

**Best for:** Only when lower tiers can't achieve the story. Expect multiple iterations.

---

## Common Failures and Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Identity shift** (face changes between frames) | Insufficient identity lock | Add explicit: `"same person with identical facial features"` |
| **Clothing color shift** | Color not precisely described | Use exact color terms, not generic (`"dusty sage"` not `"green"`) |
| **Teleporting movement** | Delta too large | Reduce the motion — use a smaller delta between A and B |
| **Ghosting / double exposure** | Multiple deltas competing | Isolate to single delta type |
| **Physics violation** | Wind direction inconsistent, shadow mismatch | Specify physics explicitly (`"wind from left"`, `"sun from upper right"`) |
| **Background change** | Background not locked | Add `"identical background, every element in the same position"` |
| **Aspect ratio mismatch** | Not specified in both | State aspect ratio in both Frame A and Frame B prompts |
| **Style drift** | Different aesthetic words in A vs B | Copy-paste the style/aesthetic block identically in both prompts |

---

## Platform-Specific Notes

### Veo3
- Accepts start + end frame pairs natively
- Handles camera movement deltas exceptionally well
- Prefer 16:9 or 9:16 aspect ratios
- Medium delta performs best
- Supports text/dialogue generation — can add speech to frame pairs

### Kling 2.0
- Excels at subject micro-movement and expression changes
- Keep deltas small to medium for best results
- Strong at fabric movement interpolation
- 1:1 and 9:16 aspect ratios common for short-form content

### Runway Gen-4
- Handles larger deltas than competitors
- Good at camera movement interpolation
- Can handle moderate multi-delta combinations
- Supports motion brush for targeted movement areas

---

## Integration with Other Skills

```
┌──────────────┐
│    frames     │ ← Delta engineering, motion planning, frame consistency
├──────────────┤
│  ecommerce   │ ← Poses, scenarios, composition (for the base shot)
├──────────────┤
│     moda     │ ← Garment precision (preserved identically across frames)
├──────────────┤
│   realismo   │ ← Authenticity (applied equally to both frames)
└──────────────┘
```

**Workflow:**
1. Design the base shot using `ecommerce` (pose, scenario, composition)
2. Describe the garment using `moda` (fabric, construction, behavior)
3. Apply `realismo` for authentic look
4. Use `frames` to split into Frame A + Frame B with chosen delta
5. Generate both frames
6. Feed into video model (Veo3 / Kling / Runway)
