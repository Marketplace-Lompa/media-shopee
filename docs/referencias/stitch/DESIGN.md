# Design System Strategy: The Obsidian Frame

## 1. Overview & Creative North Star
The North Star for this design system is **"The Digital Atelier."** 

Unlike typical AI platforms that rely on neon gradients and "magic" sparkles, this system treats AI as a precision tool—a high-end camera lens or a bespoke tailoring bench. We move beyond the "template" look by embracing **Obsidian Depth**. 

The aesthetic is defined by intentional asymmetry and "The Rule of the Frame." We utilize composition corners and generous whitespace to draw the eye toward the media content, treating the interface not as a dashboard, but as a high-performance gallery. We prioritize tonal authority over structural noise; if a layout feels "boxed in," we have failed.

---

## 2. Colors & Surface Architecture
We operate within a strictly monochromatic, high-contrast spectrum. Our color logic is built on "Obsidian Layering"—using shifts in darkness to define boundaries rather than lines.

### Surface Hierarchy & The "No-Line" Rule
Explicitly prohibit 1px solid borders for sectioning. Boundaries are defined solely through background shifts.
- **Base Layer:** `surface` (#131313) or `surface_container_lowest` (#0e0e0e) for the deep background.
- **The Nested Elevation:** To define a workspace or card, use `surface_container_low` (#1c1b1b) sitting atop the base. For an active state or high-priority element, elevate to `surface_container_high` (#2a2a2a).
- **The Glass & Gradient Rule:** For floating panels (e.g., AI prompt bars or image inspectors), use a semi-transparent `surface_bright` with a 20px `backdrop-blur`. Main CTAs should utilize a subtle linear gradient from `primary` (#ffffff) to `tertiary` (#e2e2e2) at a 15-degree angle to provide a machined, metallic finish.

---

## 3. Typography: The Manrope Scale
The type system is designed for high-performance operations. We use **Manrope** for its geometric precision and modern technicality.

| Level | Token | Weight | Tracking | Intent |
| :--- | :--- | :--- | :--- | :--- |
| **Display** | `display-lg` (3.5rem) | 600 | -0.02em | Hero statements, sparse and impactful. |
| **Headline** | `headline-md` (1.75rem)| 500 | -0.01em | Section entry points. |
| **Title** | `title-sm` (1rem) | 600 | 0.01em | Component headers and card titles. |
| **Body** | `body-md` (0.875rem) | 400 | 0.01em | Primary reading and metadata. |
| **Label** | `label-sm` (0.6875rem)| 700 | 0.05em | ALL CAPS. Technical specs and tags. |

**Editorial Note:** Use `display-lg` with intentional asymmetry (e.g., left-aligned with a 24-unit margin shift) to break the "standard" center-aligned web grid.

---

## 4. Elevation & Depth: Tonal Layering
We reject the 2010s "drop shadow." Depth must feel like ambient light hitting a matte black surface.

- **The Layering Principle:** Place a `surface_container_high` element on a `surface` background. The delta in HEX value provides all the separation needed.
- **Ambient Shadows:** For floating modals, use a shadow with a 40px blur, 0px offset, at 6% opacity using the `on_surface` color. It should feel like a soft glow rather than a dark shadow.
- **The "Ghost Border" Fallback:** If accessibility requires a stroke (e.g., in high-glare environments), use `outline_variant` (#474747) at **15% opacity**. It must be felt, not seen.
- **Corner Radii:** Use the `sm` (0.125rem) scale for technical elements (buttons/inputs) and `lg` (0.5rem) for main containers to mimic professional camera hardware.

---

## 5. Components
Our components are "tools," not "widgets." They must feel tactile and responsive.

### Buttons & Inputs
- **Primary Action:** Solid `primary` (#ffffff) with `on_primary` (#1a1c1c) text. No border. Use `spacing-2.5` for vertical and `spacing-6` for horizontal padding.
- **Secondary Action:** `surface_container_highest` background. 
- **Input Fields:** Use `surface_container_low`. Use the "Composition Corner" icon (top-left and bottom-right) as a focus state indicator instead of a full-ring glow.

### Media Cards & Lists
- **The "No-Divider" Rule:** Forbid the use of divider lines. Separate list items using `spacing-1` of vertical whitespace or a subtle toggle to `surface_container_low` on hover.
- **The Framing Logic:** All media thumbnails must have a `0.5rem` radius and a `1px` inner-inset "ghost border" to ensure white-background media doesn't bleed into the Obsidian UI.

### Precision Components
- **The Status Bead:** For AI processing, use a 4px circular bead of `secondary` (#c8c6c5) with a slow "breathing" opacity animation (40% to 100%).
- **Composition Grids:** An overlay component using `outline_variant` at 10% opacity, allowing users to align media according to the Rule of Thirds.

---

## 6. Do's and Don'ts

### Do
- **Do** use `spacing-20` or `spacing-24` for section breaks. Modern luxury is defined by "wasted" space.
- **Do** use monochromatic imagery. The UI should be the "frame" that lets the user's colorful ecommerce media pop.
- **Do** use `label-sm` for technical metadata (e.g., "ISO 100", "AI SEED: 8829") to reinforce the operational tone.

### Don't
- **Don't** use pure black (#000000). It kills the sense of depth. Use `surface_container_lowest` (#0e0e0e).
- **Don't** use "AI Magic" tropes—no sparkles, no glowing purple gradients, no robotic mascots. This is a tool for professionals, not a toy.
- **Don't** use standard 12-column grids strictly. Allow elements to overlap or offset to create an editorial, magazine-like flow.