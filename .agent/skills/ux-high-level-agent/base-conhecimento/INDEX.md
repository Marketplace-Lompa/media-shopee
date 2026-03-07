# Base Global de Conhecimento UX/Design

## Papel desta base (Cerebro Global)

Esta base e o cerebro principal de conhecimento de UX/Design.
Ela guarda padroes, casos, classificacoes e heuristicas de forma independente da skill.

- A `skill` = camada operacional (como executar).
- A base global = memoria evolutiva (o que aprendemos e como classificamos).

## Navegacao Rapida

### Indices

- `indices/cases-index.md` (catalogo geral de casos)
- `indices/cases-by-style.md` (casos agrupados por perfil visual/estilo)

### Documentacao da arquitetura (recomendada)

- `README.md` (entrada da base global / cerebro)
- `docs/arquitetura-do-agente-autonomo.md`
- `docs/fluxo-de-aprendizado-e-evolucao.md`
- `docs/guia-de-acoplamento-em-projetos.md`
- `docs/integracao-mcp-codex-review.md` (como o Design Agent se integra ao Codex Review via MCP)

### Taxonomias

- `taxonomias/style-levels.md` (eixos de estilo e niveis)

### Referencias Core (Guias e Heuristicas)

- `references/design-rules-and-heuristics.md` (regras visuais + performance UX + cognitive load + dark mode)
- `references/component-patterns.md` (18 patterns: nav, hero, cards, forms, tables, feedback, skeleton, dashboard)
- `references/accessibility-and-inclusion.md` (WCAG 2.1/2.2, ARIA, cognitiva, dark mode a11y)
- `references/ux-states-and-edge-cases.md` (9 estados de UI: loading, empty, error, success, partial, disabled, destructive, offline)
- `references/design-tokens-system.md` (hierarquia 3 niveis: primitivos, semanticos, componente + dark mode)
- `references/ux-metrics-and-measurement.md` (Core Web Vitals, usabilidade, engajamento, metricas visuais)
- `references/ux-writing-and-microcopy.md` (CTAs, headlines, forms, errors, toasts, tom de voz)
- `references/visual-identity-and-guidelines.md` (extracao de identidade visual + guidelines)
- `references/visual-identity-behance-uiux-trend-scan.md` (trends 2025-2026)
- `references/design-reference-platforms-catalog.md`
- `references/playwright-ux-review-loop.md` (capture, naming, checklist, sanitizacao)
- `references/architectural-contracts.md` (EvidenceBundle, UXProfile, ScreenIntentSpec, TokenSpec)
- `references/agent-architecture-and-governance.md` (layers, modes, evolution triggers)

### Referencias de Casos

- `references/case-01-payble-framer-rebuild.md`
- `references/case-02-taaskhub-framer-audit.md`
- `references/case-03-opscale-framer-rebuild.md`
- `references/case-04-sanny-framer-rebuild.md`

### Exemplos (snapshots de projetos)

- `../skills/ux-high-level-agent/exemplos/INDEX.md`

## Regras de Atualizacao (Markdown-first)

### Depois de cada caso relevante

- Criar/atualizar `references/case-XX-<slug>.md`.
- Registrar `Measured`, `Observed`, `Inferred`.
- Adicionar classificacao de estilo (eixos + niveis).
- Atualizar `indices/cases-index.md` e `indices/cases-by-style.md`.
- Linkar snapshot em `exemplos/` quando houver projeto local.

### Promover padroes, nao casos isolados

- O que for recorrente vai para guias gerais.
- O que for especifico fica no arquivo do caso.

## Convencao de Casos

- `case-01-...`
- `case-02-...`
- `case-03-...`
- `case-04-...`

Incremento sequencial e slug curto/descritivo.

## Template Minimo por Caso (obrigatorio)

1. Contexto e objetivo
2. Evidencias coletadas
3. Classificacao de estilo (global)
4. Observacoes de UX (fatos)
5. Medicoes tecnicas (se houver)
6. Implementacao e tradeoffs
7. Critica de UX apos screenshots
8. Promocoes para regras gerais
9. Proximos testes

## Governanca

- Markdown-first para diffs, revisao e migracao.
- Arquivos pequenos, navegaveis e indexados.
- Classificacao de estilo deve ser consistente entre casos (usar `taxonomias/style-levels.md`).
