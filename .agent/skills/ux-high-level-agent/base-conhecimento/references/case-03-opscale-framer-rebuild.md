# Case 03: Opscale Framer Rebuild (SaaS/AI Enterprise Visual)

## Date

2026-02-25

## Context

Objetivo: analisar `https://opscale.framer.website/` e criar uma reconstrução local similar com linguagem SaaS/AI enterprise, dashboard mockup, bandas de contraste e seções modulares em cards.

Projeto local criado:

- `/Users/lompa-marketplace/Documents/Design/opscale-ux-sim`
- Porta: `3007`

## Style Classification (Global KB)

### Eixos principais

- `disruptivo`: `leve`
- `medido`: `alto`
- `minimalista`: `medio`
- `profissional_clean`: `alto`

### Eixos complementares

- `motion_expressivo`: `medio`
- `densidade_informacao`: `medio`
- `playful`: `leve`
- `corporativo`: `medio`

### Rationale (1-liner)

Landing AI/SaaS bem polida e modular com tom enterprise, contraste controlado e destaque forte para mockup de dashboard.

## Evidence Collected

### Measured

- Screenshots Playwright desktop/tablet/mobile da referência (`case-runs/case-03-opscale-analysis/ux-review`)
- Metadados por captura (overflow, viewport, scroll)
- Capturas Playwright da implementação local (`opscale-ux-sim/analysis/ux-review-pass1`)

### Observed

- Hero claro com badge + CTA lilás
- Grande mockup de dashboard como principal prova visual
- Faixa de trust em fundo preto
- Navegação secundária flutuante escura em formato capsule
- Seções modulares com cards e linguagem AI/analytics

### Inferred

- Composição interna do dashboard (widgets simulados)
- Orbit visual de integrações como expressão da assinatura “Integrate. Automate. Elevate.”

## Implementation Notes

- Rebuild com React + TypeScript + Vite + `framer-motion`
- Linguagem visual baseada em:
  - neutros suaves
  - lilás como cor primária
  - cards modulares com bordas e sombras discretas
- Mockup de dashboard construído como componente original (sidebar, métricas, progresso, funil, upgrade)
- Mobile/tablet com simplificação progressiva do mockup para preservar legibilidade

## UX Review (Post-build)

## What worked

- Hero, trust band e nav flutuante reproduzem bem a assinatura visual da referência.
- Dashboard mockup comunica produto com clareza (boa prova visual do SaaS).
- Sem overflow horizontal em desktop/tablet/mobile nas capturas validadas.
- Ritmo visual consistente entre seções modulares (features, pricing, faq, team/contact).

## Frictions / Tradeoffs

- O mockup local simplifica a complexidade visual do dashboard real (menos densidade e menos microdetalhes).
- O tom enterprise foi mantido, mas com maior clareza de leitura que a referência em alguns pontos (tradeoff intencional).

## Promotion to Global Rules

- Para SaaS/AI enterprise, “faixa de contraste” (hero claro + banda escura de trust) é uma estratégia forte de hierarquia.
- Mockup de produto grande compensa copy mais enxuta quando a prova visual do sistema é essencial.

## Next Iteration Ideas

- Medir spacing e densidade do mockup da referência com mais precisão para calibrar fidelidade interna.
- Adicionar micro-motion mais específica em widgets para reforçar “AI operations” sem poluir.
