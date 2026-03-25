# Modes, Presets & Overlays — Arquitetura de Variação Visual

> **Status:** Design consolidado (pré-implementação)
> **Escopo:** Prompt Agent · categoria `fashion` · todos os cenários (text-only, image, mixed)
> **Última atualização:** 2025-03-25
> **Revisão:** v4 — taxonomia de 3 entidades (Mode / Preset / Overlay) formalizada

---

## 1. Taxonomia: 3 Entidades

O sistema de variação visual opera em **3 camadas com responsabilidades distintas**.
Confundir essas camadas é a principal fonte de overengineering e convergência visual.

### 1.1 Mode (linguagem de negócio / UX)

> *"Que tipo de imagem o usuário quer?"*

Um mode é uma **receita operacional exposta ao usuário**. Descreve um resultado
visual de negócio — não um controle técnico.

O usuário não sabe (nem precisa saber) o que é `capture_style` ou `pose_energy`.
Ele sabe que quer "foto de catálogo", "foto para Instagram" ou "detalhe de tecido".

- Linguagem: **negócio e UX**
- Interface: **botão/selector simples**
- Exemplos: `Catálogo`, `Natural`, `Lifestyle`, `Detalhe`

### 1.2 Preset (linguagem interna / Prompt Agent)

> *"Como a estrutura visual interna é montada?"*

Um preset é um **eixo estrutural** que define a espinha dorsal da variação visual.
Cada preset mapeia para **1 ou 2 pontos de injeção** no pipeline.

- Linguagem: **motor / Prompt Agent**
- Interface: **não exposto na V1** (candidato a "ajustes avançados" na V2)
- Exemplos: `capture_style`, `scenario_pool`, `pose_energy`, `casting_profile`, `framing_profile`

### 1.3 Overlay (ajuste fino / transversal)

> *"Qual ajuste fino de acabamento é aplicado?"*

Um overlay é um **modificador transversal** que entra por cima dos presets sem
redefinir a estrutura visual. Modula acabamento e comportamento.

- Linguagem: **interna, mas pode ser exposta como slider simples**
- Interface: **embutido no mode na V1** (candidato a slider explícito na V2)
- Exemplo principal: `finish_level` (clean / subtle / textured)

### 1.4 Relação Entre as 3 Entidades

```
┌─────────────────────────────────────────────────────┐
│  MODE (UX)                                          │
│  "catalog_natural"                                  │
│                                                     │
│  ┌─── PRESETS (estrutura) ────────────────────────┐ │
│  │  capture_style   = natural_commercial          │ │
│  │  scenario_pool   = urban_clean                 │ │
│  │  pose_energy     = relaxed                     │ │
│  │  casting_profile = commercial_natural          │ │
│  │  framing_profile = three_quarter               │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  ┌─── OVERLAY (acabamento) ───────────────────────┐ │
│  │  finish_level    = subtle                      │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 1.5 Por Que `realismo` É Overlay e Não Preset

O antigo `realism_level` era o eixo mais perigoso porque **vazava para tudo**:
textura de pele, direção de luz, tratamento, tipo de modelo, cenário. Ele agia
como um multiplicador difuso que reintroduzia a mesma assinatura por vários caminhos.

Como **overlay `finish_level`**, ele controla **apenas** polimento visual
(skin texture, grain, artefatos de captura). Não afeta cenário, pose, casting
nem enquadramento.

### 1.6 O Que NÃO É um Mode

Operações como `color_variation`, `marketplace_set` ou `edit_existing` **não são
modes**. Modes definem assinatura visual. Essas operações são **workflows** —
fluxos com lógica própria que podem usar qualquer mode como base.

---

## 2. Modes

### 2.1 `catalog_clean` — Catálogo Rígido

**Resultado:** Leitura total da peça, pouco ruído, pose controlada, fundo
previsível, utilidade máxima.

**Caso de uso:** Mercado Livre, catálogos formais, marketplaces com regras.

```yaml
# Presets
capture_style:    studio_clean
scenario_pool:    studio
pose_energy:      static
casting_profile:  agency_polished
framing_profile:  full_body | three_quarter
# Overlay
finish_level:     clean
```

**Referência visual:** Renner, C&A, Riachuelo.

### 2.2 `catalog_natural` — E-commerce Natural (DEFAULT)

**Resultado:** Comercial mas não clínico. Sensação humana, e-commerce-ready.
Resolve o maior volume de uso.

**Caso de uso:** Shopee, listagens padrão, e-commerce do dia a dia.

```yaml
# Presets
capture_style:    natural_commercial
scenario_pool:    urban_clean | indoor_casual
pose_energy:      relaxed
casting_profile:  commercial_natural
framing_profile:  three_quarter | full_body
# Overlay
finish_level:     subtle
```

**Referência visual:** Amaro, Zattini.

### 2.3 `lifestyle_commercial` — Lifestyle que Vende

**Resultado:** Hero, social, conteúdo aspiracional — mas **a peça ainda vende**.
Não é editorial vazio.

**Caso de uso:** Instagram, hero de site, social, campanha acessível.

```yaml
# Presets
capture_style:    natural_commercial | phone_social
scenario_pool:    urban_real | nature_soft | indoor_casual
pose_energy:      candid | dynamic
casting_profile:  commercial_natural | casual_relational
framing_profile:  environmental_wide | editorial_mid
# Overlay
finish_level:     subtle
```

**Referência visual:** Farm Rio lifestyle, Instagrams de marca.

### 2.4 `detail_focus` — Detalhe de Produto

**Resultado:** Destaque de tecido, textura, acabamento, caimento localizado.
A peça é protagonista absoluta.

**Caso de uso:** Fotos complementares de anúncio, gallery shots, zoom de textura.

```yaml
# Presets
capture_style:    studio_clean | natural_commercial
scenario_pool:    minimal
pose_energy:      static
casting_profile:  qualquer (neutro)
framing_profile:  detail_crop
# Overlay
finish_level:     textured
```

### 2.5 `campaign_hero` — Campanha Premium *(Fase 2)*

```yaml
# Presets
capture_style:    soft_editorial
scenario_pool:    selecionado por brief
pose_energy:      dynamic
casting_profile:  agency_polished | commercial_natural
framing_profile:  editorial_mid | environmental_wide
# Overlay
finish_level:     subtle | clean
```

---

## 3. Presets (5 Eixos Estruturais)

### 3.1 `capture_style` — Linguagem de Captura

| Valor | Descrição |
|---|---|
| `studio_clean` | Estúdio controlado, luz direcionada, fundo clean |
| `natural_commercial` | Luz disponível, ambiente real clean, lente prime |
| `soft_editorial` | Estética de filme suave, profundidade intencional |
| `phone_social` | Captura de celular, imperfeições naturais |

**Dono:** `camera.py` (primário) · `constants.py` RK levers (secundário)

### 3.2 `scenario_pool` — Ambiente / Cenário

| Valor | Exemplos |
|---|---|
| `studio` | Cyclorama branco, softbox, fundo neutro |
| `urban_clean` | Downtown clean, café, shopping district, loft |
| `urban_real` | Rua movimentada, escadaria, feira, calçada |
| `indoor_casual` | Quarto, espelho, cozinha, sala com luz natural |
| `nature_soft` | Parque, praia, jardim botânico |
| `minimal` | Cenário quase inexistente — foco total no detalhe |

**Dono:** `diversity.py` (único)

### 3.3 `pose_energy` — Energia Corporal

| Valor | Descrição |
|---|---|
| `static` | Parada, catálogo, contrapposto clássico |
| `relaxed` | Em pé mas natural, peso deslocado, braços soltos |
| `dynamic` | Andando, virando, em movimento intencional |
| `candid` | Momento capturado, ajustando roupa, rindo |

**Dono:** `diversity.py` (primário) · `compiler.py` (secundário)

### 3.4 `casting_profile` — Tipo de Casting

| Valor | Descrição |
|---|---|
| `agency_polished` | Modelo de agência, presença editorial, alta produção |
| `commercial_natural` | Profissional mas acessível, e-commerce premium |
| `casual_relational` | Mulher real, relatable, sem pretensão |

**Dono:** `diversity.py` (primário) · `prompt_context.py` (secundário)

### 3.5 `framing_profile` — Composição do Frame

| Valor | Descrição | Uso típico |
|---|---|---|
| `full_body` | Cabeça aos pés | Capa de anúncio, catálogo |
| `three_quarter` | Cabeça até meio da coxa | E-commerce padrão |
| `editorial_mid` | Cintura para cima, intencional | Lifestyle, campanha |
| `detail_crop` | Close-up no tecido/detalhe | Fotos complementares |
| `environmental_wide` | Modelo menor, contexto grande | Hero de site |

**Dono:** `compiler.py` (primário) · `camera.py` framing label (secundário)

---

## 4. Overlay

### 4.1 `finish_level` — Nível de Acabamento

Controla **apenas polimento visual**: skin texture, grain, artefatos de captura.
**NÃO** afeta cenário, pose, casting nem enquadramento.

| Valor | Descrição |
|---|---|
| `clean` | Pele lisa, sem grain, zero artefatos |
| `subtle` | Textura sutil de pele, grain mínimo |
| `textured` | Poros visíveis, creases de tecido, grain intencional |

**Dono:** `camera.py` (primário) · `constants.py` RK levers (secundário)

**Na V1:** embutido no mode (cada mode define seu finish_level).
**Na V2:** pode ser exposto como slider independente.

---

## 5. Mapa de Responsabilidade

Cada eixo tem no máximo 2 donos. Se precisar de 3+, está impuro.

```
Entidade / Eixo      │ Dono Primário      │ Dono Secundário    │ Não toca
─────────────────────┼────────────────────┼────────────────────┼──────────────
capture_style        │ camera.py          │ constants.py (RK)  │ diversity.py
scenario_pool        │ diversity.py       │ —                  │ camera.py
pose_energy          │ diversity.py       │ compiler.py        │ camera.py
casting_profile      │ diversity.py       │ prompt_context.py  │ compiler.py
framing_profile      │ compiler.py        │ camera.py          │ diversity.py
finish_level         │ camera.py          │ constants.py (RK)  │ diversity.py
```

---

## 6. Fluxo no Pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│  Frontend                                                            │
│  └→ mode="catalog_natural"                                          │
│                                                                      │
│  agent.py                                                            │
│  └→ get_mode("catalog_natural") → ModeConfig                        │
│       │                                                              │
│       ├─→ diversity.py              ← scenario_pool                 │
│       │                                pose_energy                   │
│       │                                casting_profile               │
│       │                                                              │
│       ├─→ constants.py (RK)         ← capture_style                 │
│       │                                finish_level                  │
│       │                                                              │
│       ├─→ camera.py                 ← capture_style                 │
│       │                                framing_profile               │
│       │                                finish_level                  │
│       │                                                              │
│       └─→ compiler.py              ← framing_profile                │
│                                       pose_energy                    │
│                                                                      │
│  Resultado: prompt com assinatura visual coerente ao mode            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. UX

### V1 — Seleção de Mode

```
┌──────────────────────────────────────────────────────────────┐
│  Estilo Visual                                               │
│                                                              │
│  [□ Catálogo] [■ Natural] [□ Lifestyle] [□ Detalhe]         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### V2 — Ajustes Avançados

```
┌──────────────────────────────────────────────────────────────┐
│  ▸ Ajustes avançados                                         │
│                                                              │
│  Captura:       [estúdio ●○○ celular]                        │
│  Cenário:       [estúdio ○●○ rua]                            │
│  Pose:          [parada ○●○ candid]                          │
│  Casting:       [editorial ○●○ casual]                       │
│  Enquadramento: [corpo inteiro ○●○ detalhe]                  │
│  ─────────────────────────────────────                       │
│  Acabamento:    [limpo ○●○ texturizado]                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Plano de Implementação

### Fase 0 — Base Limpa ✅ CONCLUÍDA
- [x] Modularizar REFERENCE_KNOWLEDGE em blocos
- [x] build_system_instruction condicional
- [x] DIVERSITY_TARGET sem reference rules em text-only
- [x] MODE 1 semântico (não-procedural)
- [x] Neutralizar anchor phrase e CAPTURE ARTIFACTS

### Fase 1 — ModeConfig + 4 Modes
1. Criar `presets.py` com tipos, `ModeConfig`, e definições de overlay
2. Registrar 4 modes: `catalog_clean`, `catalog_natural`, `lifestyle_commercial`, `detail_focus`
3. `get_mode()` + `list_modes()`
4. Testes unitários
5. **Sem integração** — nenhum arquivo existente é alterado

### Fase 2 — Integração no Pipeline
1. `diversity.py` — pools indexadas por `scenario_pool`, `pose_energy`, `casting_profile`
2. `camera.py` — `capture_style` + `framing_profile` + `finish_level` como hints
3. `compiler.py` — `framing_profile` como controle de composição
4. `constants.py` — filtra RK levers por `capture_style` / `finish_level`
5. Testes de integração por mode

### Fase 3 — API + Frontend
1. `mode` como campo no body da API
2. Selector de mode no frontend (4 opções)
3. Mode `campaign_hero` (5ª opção)

### Fase 4 — Presets e Overlay Avançados
1. Presets expostos como "ajustes avançados"
2. `finish_level` como slider separado
3. Guardrails para combinações inválidas

---

## 9. Decisões Consolidadas

| # | Decisão | Resolução |
|---|---|---|
| 1 | Taxonomia | **3 entidades:** Mode (UX) · Preset (estrutura) · Overlay (acabamento) |
| 2 | Modes V1 | **4:** catalog_clean, catalog_natural, lifestyle_commercial, detail_focus |
| 3 | Presets core | **5:** capture_style, scenario_pool, pose_energy, casting_profile, framing_profile |
| 4 | Overlay | **1:** finish_level (clean / subtle / textured) |
| 5 | Default | `catalog_natural` |
| 6 | Realismo | **NÃO é mode, NÃO é preset** → é overlay `finish_level` |
| 7 | Mode afeta edit_agent? | ❌ Não |
| 8 | Presets expostos na V1? | ❌ Não — só modes |
| 9 | Mode persiste na sessão? | ✅ Sim |

---

## 10. Glossário

| Termo | Definição |
|---|---|
| **Mode** | Receita operacional de negócio (UX). Ex: `catalog_natural` |
| **Preset** | Eixo estrutural interno do pipeline. Ex: `capture_style` |
| **Overlay** | Ajuste fino transversal que entra por cima dos presets. Ex: `finish_level` |
| **ModeConfig** | Dataclass que mapeia um mode para seus presets + overlay |
| **Pool** | Lista de opções de onde o diversity sampler puxa valores |
| **Dono** | Arquivo do pipeline responsável por consumir um eixo |
| **Guardrail** | Validação que impede combinações inválidas |

---

## 11. Histórico

| Data | Versão | Mudança |
|---|---|---|
| 2025-03-25 | v1 | Documento inicial — 8 eixos, 3 modes |
| 2025-03-25 | v2 | Revisão ortogonalidade — 5 eixos + 1 secundário |
| 2025-03-25 | v3 | Revisão regras de negócio — 4 modes, valores refinados |
| 2025-03-25 | v4 | Taxonomia de 3 entidades: Mode / Preset / Overlay. Realismo formalizado como overlay `finish_level`. Separação explícita entre UX, estrutura e acabamento. |
