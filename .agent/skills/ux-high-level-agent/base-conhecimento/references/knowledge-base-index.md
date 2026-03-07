# UX Knowledge Base Index

## Purpose

Usar esta base como memoria evolutiva do agente/skill de UX.
Registrar casos reais, promover padroes reutilizaveis e evitar perda de aprendizado entre projetos.

## Update Rules (Markdown-first)

### After each meaningful case

- Criar ou atualizar um arquivo `case-XX-<slug>.md`.
- Registrar fatos medidos, inferencias, decisoes e gaps.
- Linkar screenshots/artefatos locais quando existirem.
- Promover aprendizados estaveis para os guias gerais abaixo.

### Promote patterns, not anecdotes

- Promover para guias gerais apenas o que se repetir ou tiver alto valor.
- Manter detalhes especificos do projeto no arquivo de caso.

### Separate evidence from interpretation

- Marcar claramente:
  - `Measured`: obtido via Playwright/DOM/CSS computed style.
  - `Observed`: visto em screenshot/render.
  - `Inferred`: aproximacao adotada na implementacao.

## File Taxonomy

- `case-*.md`: casos reais, experimentos, learnings.
- `playwright-*.md`: workflows de captura/medicao.
- `design-*.md`: heuristicas, criterios visuais, regras de qualidade, tokens.
- `component-*.md`: padroes de UI, composicao e motion.
- `visual-identity-*.md`: analise de identidade visual, repertorio e guidelines.
- `accessibility-*.md`: WCAG, ARIA, acessibilidade cognitiva, inclusao.
- `ux-states-*.md`: estados de interface e edge cases.
- `ux-metrics-*.md`: medicao de qualidade de UX.
- `ux-writing-*.md`: microcopy, tom de voz, escrita de interface.
- `agent-*.md`: governanca do skill/agente e estrategia de evolucao.
- `architectural-*.md`: contratos entre camadas do agente.
- `../exemplos/case-XX-*`: snapshots de projetos completos reutilizaveis.

## Current Core References

### Guias e Heuristicas
- `design-rules-and-heuristics.md` (regras visuais + performance UX + cognitive load + dark mode)
- `component-patterns.md` (18 patterns incluindo forms, nav, feedback, skeleton, dashboard)
- `accessibility-and-inclusion.md` (WCAG 2.1/2.2, ARIA patterns, cognitiva)
- `ux-states-and-edge-cases.md` (9 estados: loading, empty, error, success, partial, disabled, destructive, offline)
- `design-tokens-system.md` (hierarquia 3 niveis + dark mode mapping)
- `ux-metrics-and-measurement.md` (Core Web Vitals, usabilidade, probes Playwright)
- `ux-writing-and-microcopy.md` (CTAs, forms, errors, tom de voz)

### Identidade Visual e Repertorio
- `visual-identity-and-guidelines.md`
- `visual-identity-behance-uiux-trend-scan.md`
- `design-reference-platforms-catalog.md`

### Pipeline e Automacao
- `playwright-ux-review-loop.md`

### Arquitetura e Governanca
- `architectural-contracts.md`
- `agent-architecture-and-governance.md`

### Casos
- `case-01-payble-framer-rebuild.md`
- `case-02-taaskhub-framer-audit.md`
- `case-03-opscale-framer-rebuild.md`
- `case-04-sanny-framer-rebuild.md`

### Exemplos
- `../exemplos/INDEX.md`

## Case Naming Convention

Usar:

- `case-01-...`
- `case-02-...`
- `case-03-...`
- `case-04-...`

Incrementar sequencialmente.
Preferir slugs curtos e descritivos (ex.: `framer-fintech-rebuild`, `dashboard-density-refactor`).

## Minimum Case Template

Usar esta estrutura minima em novos casos:

1. Contexto e objetivo
2. Evidencias coletadas
3. Observacoes de UX (fatos)
4. Medicoes tecnicas (se houver)
5. Implementacao e tradeoffs
6. Critica de UX apos screenshots
7. O que promover para regras gerais
8. Proximos testes

## Governance Reminder

- Manter esta base em Markdown para facilitar diffs, revisao e migracao entre repositorios.
- Preferir muitos arquivos pequenos e navegaveis a um arquivo unico gigante.
- Manter a biblioteca `exemplos/` enxuta (sem dependencias locais) para facilitar sync e reuso.
