# Plano de Alinhamento — Modo Lifestyle (Abstrato)

## Filosofia Central

O lifestyle é a **zona intermediária**: a modelo **sabe** que está sendo fotografada, mas está **vivendo**, não posando. O fotógrafo é alguém do seu círculo social, não um profissional contratado. A foto acontece **porque o momento é bonito**, não porque foi planejada.

> **Contrato Estrutural:** A modelo deve estar **em ação ou fazendo algo**. Sem atividade em andamento, o lifestyle colapsa para natural (parada/alheia) ou editorial (posada/performática). A ação é o que define o gênero.

> **Regra de Ouro:** Define a fronteira filosófica, deixa o Gemini preencher os detalhes criativos.

---

## Alterações por Camada

### 1. `mode_identity_soul.py` (P1)

**Estado atual (L41-47):** Já correto na essência ("influencer's photographer", "mid-life", "DOING something").

**Ajuste — adicionar fronteiras filosóficas:**
- Reforçar que **NÃO é editorial** — a modelo não está performando para câmera
- Reforçar que **NÃO é paparazzi** — ela tem consciência da foto
- Reforçar **aspiração alcançável** — é desejável mas crível como pessoa real
- Toda direção criativa concreta (qual momento, qual cenário, qual ação) pertence ao Gemini

**Texto-guia (soul directive, não hardcode):**
```
"lifestyle is the middle ground between candid and editorial.
The model is aware of the camera but engaged in life, not performing for it.
The photographer is someone from her social circle, not a hired professional.
The model MUST be doing something — an activity in progress is the structural contract of this mode.
Without visible action, the image collapses into 'natural' (idle) or 'editorial' (posed).
The aspiration must feel achievable — she is desirable but believable as a real person.
The scene is a co-protagonist: it tells WHERE she is and WHY she is there.
YOU decide the specific moment, action, setting, and finishing — this soul only sets the energy boundaries."
```

---

### 2. `model_soul.py` (P0)

**Estado atual:** Universal para todos os modes, sem overlay lifestyle. Overlay existe apenas para `editorial_commercial`.

**Ajuste — overlay condicional para lifestyle:**
- Maquiagem: **intencional mas não editorial** — ela se arrumou, mas não para um shooting
- Energia: **autoconfiança social** — ela está confortável consigo mesma, não apresentando-se
- Visual: **personalidade, não perfeição** — traços individuais, não modelo de casting genérica
- NÃO ditar itens específicos (cor de batom, tipo de penteado) — isso é decisão do Gemini

**Texto-guia:**
```
if mode == "lifestyle":
    overlay = (
        "Her makeup should feel intentional but not editorial — "
        "she prepared for her day, not for a photoshoot. "
        "Her energy is socially self-assured, not performative. "
        "She has visual personality through individual traits, not casting-call perfection."
    )
```

---

### 3. `scene_soul.py` (P0)

**Estado atual:** Universal. "Follow the active MODE_IDENTITY to decide how much the environment should speak."

**Ajuste — overlay condicional para lifestyle:**
- O cenário deve ter **narrativa implícita** — por que ela está ali?
- O ambiente é **co-protagonista**, não pano de fundo
- A cena deve sentir como um **lugar real onde pessoas reais vão** — nem doméstico e silencioso (natural), nem curado e premium (editorial)
- NÃO ditar locais específicos — o Gemini escolhe contextos vivos

**Texto-guia:**
```
if mode == "lifestyle":
    overlay = (
        "The scene is a co-protagonist — it implies a reason for being there, "
        "not just a backdrop. The environment should feel like a place real people "
        "choose to go, with social energy and lived texture. "
        "Avoid both the quiet domesticity of 'natural' and the curated premium of 'editorial'. "
        "YOU choose the specific location — the soul only requires it to feel socially alive."
    )
```

---

### 4. `pose_soul.py` (P0 → promovido)

**Estado atual (L41-47):** "Let the body imply life, momentum, and approachable desirability. Caught mid-moment rather than arranged."

**Ajuste — ação é contrato, não sugestão:**
- A modelo **deve estar em ação** — o body language nasce de uma atividade em progresso, não de uma posição estática
- Diferença vs. natural: no lifestyle, a modelo pode ter **consciência leve da câmera**, mas o corpo está ocupado com algo
- Diferença vs. editorial: a pose nasce da **atividade**, não da composição visual
- **Estática = quebra de contrato** — se o corpo não implica atividade, não é lifestyle
- NÃO listar ações específicas — o Gemini decide qual atividade

**Texto-guia (extensão do existente):**
```
if mode == "lifestyle":
    overlay = (
        "The model must be mid-activity — her body language originates from something she is doing, "
        "not from standing still or being positioned. A static, idle pose breaks the lifestyle contract. "
        "Unlike 'natural', she may show brief camera-awareness — a passing glance or half-smile — "
        "but her body remains shaped by her activity, not by the camera. "
        "Unlike 'editorial', the pose originates from action, not from visual composition. "
        "YOU choose the specific activity and gesture."
    )
```

---

### 5. `capture_soul.py` (P1)

**Estado atual (L41-47):** "Socially alive, mid-moment. Closer to elevated phone or BTS instinct than formal studio."

**Ajuste — reforçar mood e proximidade:**
- A câmera está **socialmente próxima** — distância de quem conhece a pessoa
- O mood tende a **warm tones e luz ambiente** — não controlada, não crua
- Leve profundidade de campo (background softened, like portrait mode)
- NÃO ditar hora do dia, modelo de câmera, ou ISO — o Gemini decide a linguagem visual

**Texto-guia (extensão do existente):**
```
if mode == "lifestyle":
    overlay = (
        "The camera is at a social distance — close enough to imply familiarity, "
        "not observational distance. "
        "Favor warm ambient mood over controlled studio light or raw harshness. "
        "A softened background (portrait-mode instinct) helps separate the subject from the scene "
        "while keeping the environment readable. "
        "YOU decide the specific camera language, angle, and light quality."
    )
```

---

### 6. `styling_soul.py` (P2)

**Estado atual (L49-55):** "Desirable, current, and lived-in. Small finishing touches help sell the lifestyle."

**Ajuste — elevar papel de acessórios sem ditar quais:**
- No lifestyle, os elementos complementares **contam a história do momento** — são parte da narrativa, não apenas completude commercial
- O calçado é **parte do look**, não utilitário (diferença do natural)
- NÃO listar objetos específicos — o Gemini escolhe o que cabe na história

**Texto-guia (extensão do existente):**
```
if mode == "lifestyle":
    overlay = (
        "Accessories and finishing elements are narrative tools — they help tell the story "
        "of where she is going and what she is doing. "
        "Footwear is part of the look statement, not just functional coverage. "
        "YOU choose which elements serve the story."
    )
```

---

### 7. `creative_brief_builder.py` (P1)

**Estado atual dos pools lifestyle:**
```python
"scenario_pool": ("textured_city", "beach_coastal", "market_feira", 
                  "rooftop_terrace", "tropical_garden", "nature_open_air"),
```

**Ajustes sugeridos:**
- `market_feira` é mais "natural" que "lifestyle" — considerar substituir por pool com **energia social urbana**
- `nature_open_air` é genérico — considerar substituir por pool com **narrativa de encontro social ao ar livre**
- `casting_profile` tem `editorial_presence` que pode puxar muito — considerar manter apenas `natural_commercial`
- `framing_profile` deveria incluir `full_body` para mostrar o look completo
- `capture_geometry` deveria ter opção de **proximidade social**, não apenas `environmental_wide_observer`

> [!IMPORTANT]
> Não é criar novos pools com nomes literais. É ajustar a **composição do mix** para representar melhor a energia lifestyle, e considerar expandir os `emotional_register` e `material_language` dos pools existentes para incluir vocabulário mais socialmente vibrante.

---

### 8. `prompt_result.py` — Footwear Fallback (P2)

**Estado atual:** "discreet commercially coherent footwear" (genérico para todos os modes).

**Ajuste:** Footer condicional para lifestyle que comunica **calçado como extensão do look**, não como item funcional ou discreto.

**Texto-guia:**
```
if mode == "lifestyle":
    footwear_hint = "footwear that extends the look's personality"
else:
    footwear_hint = "discreet commercially coherent footwear"
```

---

## Resumo de Prioridades

| # | Camada | Tipo de Mudança | Prioridade |
|---|---|---|---|
| 1 | `model_soul.py` | Overlay condicional lifestyle | P0 |
| 2 | `scene_soul.py` | Overlay condicional lifestyle | P0 |
| 3 | `pose_soul.py` | Overlay de ação como contrato estrutural | P0 |
| 4 | `mode_identity_soul.py` | Extensão de fronteiras filosóficas + contrato de ação | P1 |
| 5 | `capture_soul.py` | Overlay de mood e proximidade | P1 |
| 6 | `creative_brief_builder.py` | Ajuste de composição de pools | P1 |
| 7 | `styling_soul.py` | Extensão de papel de acessórios | P2 |
| 8 | `prompt_result.py` | Footwear fallback condicional | P2 |

---

## Regras de Implementação (Anti-Hardcode)

1. **Nenhum item literal** nos overlays (nomes de lugar, peças de roupa, marcas, cores)
2. **Nenhuma ação prescrita** (não ditar "segurando café" ou "andando na rua")
3. **Cada overlay termina** com variação de: "YOU choose the specific [X] — this soul only sets the energy boundaries"
4. **Overlays são fronteiras**, não receitas — definem o que NÃO PODE ser, e a energia geral do que DEVE sentir
5. **Pools podem ser ajustados**, mas usando vocabulário abstrato dos emotional registers, não cenários literais novos
