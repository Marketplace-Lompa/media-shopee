# Mode × Preset Matrix — Configurações por Mode

> **Status:** Sincronizado com implementação (`modes.py` rev. 2025-03-25)
> **Escopo:** V1 · `fashion` · modo livre · sem input de imagem
> **Última atualização:** 2025-03-25

---

## 1. Visão Geral

Cada **mode** é uma combinação fixa de **6 presets**. O usuário escolhe o mode;
o sistema resolve os presets internamente.

```
Mode (UX)  ──→  6 Presets (pipeline)  ──→  Prompt final
```

Os presets podem ser overridden via `resolve_mode_with_overrides()` no futuro (V2).

---

## 2. Os 6 Presets e Seus Donos

| # | Preset | Pergunta que responde | Dono Primário | Dono Secundário |
|---|---|---|---|---|
| 1 | `scenario_pool` | Onde a cena acontece? | `diversity.py` | — |
| 2 | `pose_energy` | Qual a energia corporal? | `diversity.py` | `compiler.py` |
| 3 | `casting_profile` | Qual tipo de modelo? | `diversity.py` | `prompt_context.py` |
| 4 | `framing_profile` | Como o corpo ocupa o frame? | `compiler.py` | `camera.py` |
| 5 | `camera_perspective` | Que ângulo/perspectiva? | `camera.py` | — |
| 6 | `lighting_profile` | Que tipo de luz? | `camera.py` | `diversity.py` (hint) |

---

## 3. Valores Implementados por Preset

### 3.1 `scenario_pool` — `ScenarioPool`

| Valor | Pool de cenários |
|---|---|
| `studio` | Estúdio clean, softbox, fundo neutro, controlled backdrop |
| `architectural_clean` | Arquitetura premium, walkway refinado, atmosfera de galeria |
| `urban_clean` | Rooftop, shopping district, terraço neutral, urban rhythm |
| `urban_real` | Calçada real, boulevard, café outdoor, contexto urbano vivido |
| `indoor_lifestyle` | Living room, apartamento, café terrace, atmosfera doméstica |

### 3.2 `pose_energy` — `PoseEnergy`

| Valor | Efeito no `compiler.py` (gaze) | Efeito no `diversity.py` (pool) |
|---|---|---|
| `static` | Calm direct gaze, controlled expression | Catalog stance, balanced, garment legible |
| `relaxed` | Warm near-camera look, relaxed expression | Lookbook posture, subtle stance, weight shift |
| `directed` | Direct confident gaze, composed editorial | Editorial contrapposto, intentional posture, elongated line |
| `candid` | Off-camera spontaneity, engaged expression | Caught mid-turn, mid-stride, moment between poses |

### 3.3 `casting_profile` — `CastingProfile`

| Valor | Pool de vibes regionais | Pool de casting tones |
|---|---|---|
| `polished_commercial` | Paulistana, Carioca, Sulista, Mineira | Premium catalog, high-end beauty, lookbook model |
| `natural_commercial` | Baiana, Brasília, Mineira, Northeastern | Natural premium face, warm lookbook, modern beauty |
| `editorial_presence` | Paulistana, Carioca, Mineira | Editorial beauty, campaign face, fashion-forward |

### 3.4 `framing_profile` — `FramingProfile`

| Valor | Label gerado no prompt | Shot type inferido |
|---|---|---|
| `full_body` | Full-body garment-readable framing | `wide` |
| `three_quarter` | Three-quarter commercial framing | `medium` |
| `editorial_mid` | Mid-frame fashion composition | `medium` |
| `detail_crop` | Detail-led close framing | `close-up` |
| `environmental_wide` | Environment-led wide framing | `medium` |

### 3.5 `camera_perspective` — `CameraPerspective`

| Valor | Label injetado no prompt |
|---|---|
| `eye_level_clean` | Clean eye-level commercial perspective |
| `slight_low_angle` | Subtle low-angle fashion perspective for presence |
| `immersive_observer` | Observational perspective with environmental presence |
| `intimate_close` | Intimate close perspective while keeping garment readability |

### 3.6 `lighting_profile` — `LightingProfile`

| Valor | Label injetado no prompt | Nota |
|---|---|---|
| `studio_even` | Even controlled light with soft shadow falloff | Se scenario não é studio, appenda "studio cleanliness" |
| `soft_daylight` | Soft daylight with gentle contrast | — |
| `golden_hour_soft` | Warm late-afternoon light with soft transitions | Appenda "warm late-afternoon ambience" ao cenário |
| `architectural_diffused` | Diffused architectural light with clean highlights | — |
| `ambient_lifestyle` | Ambient natural light with believable environmental depth | — |

---

## 4. Matrix — Mode × Preset (Valores Reais do Código)

| Preset | 🏷️ `catalog_clean` | 🌿 `natural` *(default)* | 📸 `lifestyle` | ✨ `editorial_commercial` |
|---|---|---|---|---|
| `scenario_pool` | `studio` | `urban_clean` | `indoor_lifestyle` | `architectural_clean` |
| `pose_energy` | `static` | `relaxed` | `candid` | `directed` |
| `casting_profile` | `polished_commercial` | `natural_commercial` | `natural_commercial` | `editorial_presence` |
| `framing_profile` | `full_body` | `three_quarter` | `environmental_wide` | `editorial_mid` |
| `camera_perspective` | `eye_level_clean` | `eye_level_clean` | `immersive_observer` | `slight_low_angle` |
| `lighting_profile` | `studio_even` | `soft_daylight` | `ambient_lifestyle` | `architectural_diffused` |

### Camera realism profile inferido (via `_select_camera_realism_profile`)

| Mode | Profile selecionado |
|---|---|
| `catalog_clean` | `catalog_clean` |
| `natural` | `catalog_natural` |
| `lifestyle` | `catalog_natural` |
| `editorial_commercial` | `editorial_analog` |

---

## 5. Racional por Mode

### 🏷️ Catálogo Clean

**Propósito:** Compliance de marketplace (ML), utilidade máxima, zero ruído.

- **Cenário**: `studio` — fundo previsível, sem distração
- **Pose**: `static` — catalogação padronizada, garment legível
- **Casting**: `polished_commercial` — presença premium de catálogo
- **Framing**: `full_body` — mostrar a peça inteira → shot `wide`
- **Câmera**: `eye_level_clean` — sem distorção, perspectiva neutra
- **Luz**: `studio_even` — iluminação uniforme, sem drama

**Variação entre gerações:** modelo (diversidade étnica via name blending), sutil variação de pose estática.

### 🌿 Natural (DEFAULT)

**Propósito:** Volume principal de e-commerce. Shopee, listagens do dia a dia. Humano sem ser clínico.

- **Cenário**: `urban_clean` — rooftop, shopping district, terraço — real mas clean
- **Pose**: `relaxed` — natural, acessível, não engessada
- **Casting**: `natural_commercial` — warm, moderna, approachable
- **Framing**: `three_quarter` — e-commerce standard → shot `medium`
- **Câmera**: `eye_level_clean` — neutra e confiável
- **Luz**: `soft_daylight` — quente, orgânica, gentle contrast

**Variação entre gerações:** cenário (3 opções no pool), modelo, pose (3 opções), sutil variação de luz.

### 📸 Lifestyle

**Propósito:** Hero, social, aspiracional — a peça ainda vende.

- **Cenário**: `indoor_lifestyle` — living room, apartamento, café — atmosfera vivida
- **Pose**: `candid` — momento capturado, mid-turn, between poses
- **Casting**: `natural_commercial` — warm e relatable
- **Framing**: `environmental_wide` — contexto importa → shot `medium`
- **Câmera**: `immersive_observer` — observacional, presença ambiental
- **Luz**: `ambient_lifestyle` — ambiental, environmental depth, autêntica

**Variação entre gerações:** cenário (3 opções), pose (3 opções candid), modelo — boa variação.

### ✨ Editorial Comercial

**Propósito:** Lookbook, campanha, hero de marca. Premium e dirigido.

- **Cenário**: `architectural_clean` — arquitetura premium, galeria, lines clean
- **Pose**: `directed` — intencional, editorial, contrapposto
- **Casting**: `editorial_presence` — fashion-forward, refined, directed
- **Framing**: `editorial_mid` — composição intencional → shot `medium`
- **Câmera**: `slight_low_angle` — presença, empowerment sutil
- **Luz**: `architectural_diffused` — diffused, clean highlights, shadows refinados

**Variação entre gerações:** cenário (3 opções), pose (3 opções directed), modelo — variação com personalidade.

---

## 6. Fluxo de Resolução no Pipeline

```
Frontend  → mode="natural"
                │
                ▼
agent.py  → get_mode("natural") → ModeConfig
          → resolve_mode_with_overrides(mode_id, diversity_target.preset_defaults)
          → effective_mode
                │
    ┌───────────┼───────────────────────────┐
    ▼           ▼                           ▼
diversity.py   camera.py              compiler.py
  scenario_pool  capture_style+profile    framing_profile
  pose_energy    camera_perspective        pose_energy
  casting_profile lighting_profile         casting_profile
  lighting_profile framing_profile
```

---

## 7. Detail Shots

`detail_focus` não é mode na V1. É um override de framing:

```python
resolve_mode_with_overrides("natural", {
    "framing_profile": "detail_crop",
    "camera_perspective": "intimate_close",
})
```

Qualquer mode pode gerar detalhe via override.

---

## 8. Histórico

| Data | Versão | Mudança |
|---|---|---|
| 2025-03-25 | v1 | Documento criado com matrix teórica |
| 2025-03-25 | v2 | Sincronizado com valores reais de `modes.py`, `diversity.py`, `camera.py`, `compiler.py` |
