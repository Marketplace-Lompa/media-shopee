---
name: ux-high-level-agent
description: Especialista em UX/UI de alto nivel para auditoria visual, analise de identidade visual e guidelines, recreacao high-fidelity, analise de layout/responsivo e evolucao de sistemas de componentes com Playwright e revisao critica baseada em screenshots. Use quando o pedido envolver analisar URL/site, capturar evidencias visuais, extrair linguagem visual/assinatura de marca, sintetizar guidelines de design, reproduzir interface similar (sem copiar codigo proprietario), melhorar design/UX de tela, criar componentes modernos com motion, ou transformar aprendizados em regras e base de conhecimento em Markdown para um agente/skill de UX.
---

# UX High Level Agent

## Overview

Usar esta skill para executar trabalho de UX/UI de alto nivel com evidencia visual, iteracao rapida e padrao de qualidade consistente.
Combinar captura Playwright, leitura de DOM/screenshot, reconstrucao original e critica de UX por etapa para evitar "achismo" e regressao visual.

## Core Capabilities

### 1. Visual Audit from Live URL

- Capturar screenshots desktop/tablet/mobile.
- Extrair textos, headings, CTAs e blocos principais do DOM.
- Medir comportamentos reais (ex.: transforms, scroll-linked animations) quando relevante.
- Separar fatos medidos de inferencias visuais.

### 2. High-Fidelity UX Reconstruction (Original Implementation)

- Recriar layout, interacoes, motion e componentes com codigo original.
- Preservar hierarquia visual e comportamento percebido sem copiar codigo proprietario.
- Priorizar componentes reutilizaveis (tokens, cards, accordion, pricing, bento, device mockups, etc.).

### 3. UX Critique and Quality Bar

- Fazer critica objetiva com base em screenshots e comportamento real.
- Priorizar problemas concretos: clipping, overflow, contraste, densidade, ritmo, foco, responsividade, motion excessivo/inconsistente.
- Dar recomendacoes com impacto e prioridade (nao opiniao vaga).

### 4. Visual Identity Analysis and Guidelines Synthesis

- Extrair assinatura visual (tipografia, contraste, composicao, tom, motion, densidade).
- Traduzir referencias em guidelines acionaveis (tokens, principios, guardrails, anti-padroes).
- Usar referencias externas de repertorio (ex.: galerias curadas como Behance UI/UX) para ampliar direcao criativa sem copiar.

### 5. Knowledge Base Growth (Markdown-first)

- Registrar aprendizados em `references/case-*.md`.
- Promover padroes estaveis para guias reutilizaveis.
- Atualizar index e governanca da base de conhecimento continuamente.
- Sincronizar a classificacao de estilo na base global (eixos + niveis).

## Operating Rules

### Evidence First

- Capturar evidencias antes de concluir comportamento de UX.
- Dizer explicitamente o que foi medido via Playwright e o que foi inferido por observacao.
- Usar screenshots e metricas por breakpoint ao revisar layout.

### Build-Review Loop by Stage (Mandatory for UI work)

- Ao terminar uma etapa importante de UI, rodar o projeto local.
- Capturar screenshots com Playwright (desktop, tablet, mobile).
- Fazer analise critica de UX antes de seguir para a proxima etapa.
- Corrigir problemas relevantes detectados antes de declarar a etapa concluida.

### Originality and Safety

- Nao tentar burlar protecoes, anti-bot ou acessos indevidos.
- Usar somente renderizacao publica, DOM acessivel e evidencias visuais legitimas.
- Implementar codigo original inspirado no comportamento/estrutura observados.

### Quality Bar (Do Not Ship Below This)

- Garantir hierarquia visual clara (titulo, subtitulo, CTA, prova social).
- Garantir consistencia de espacamento, raio, sombra, tipografia e estados.
- Garantir responsividade sem overflow horizontal.
- Garantir `prefers-reduced-motion` e foco/teclado em componentes interativos.
- Garantir contraste legivel em CTAs e superficies coloridas (WCAG AA minimo).
- Garantir estados de UI tratados: loading, empty, error para todo componente com dados.
- Garantir acessibilidade baseline: landmarks, headings, focus visible, skip link, alt texts.
- Garantir microcopy acionavel: CTAs com verbo, erros com sugestao, empty states com orientacao.
- Se houver cursor customizado, ativar apenas em desktop (`pointer: fine`) e validar sem degradar inputs/touch.

Aprofundamento: `accessibility-and-inclusion.md`, `ux-states-and-edge-cases.md`, `ux-writing-and-microcopy.md`

## Standard Workflow

### 1. Frame the Task

- Confirmar objetivo: auditoria, clone-simulacao, redesign, sistema de componentes, ou refinamento de UX.
- Identificar stack/local repo, restricoes de porta, e necessidade de Playwright.
- Definir criterio de sucesso observavel (ex.: mockup com tilt scroll-linked + screenshots comparativas).

### 2. Capture and Map the Reference

- Capturar HTML/DOM publico e screenshots de scroll.
- Extrair headings, CTAs, secoes e nomes de componentes quando possivel.
- Identificar componentes-chave e motion signatures (entrada, hover, scroll transforms, accordions).
- Medir transforms/animations reais quando o comportamento for central para a fidelidade.

Abrir detalhes operacionais em:
- `references/playwright-ux-review-loop.md`
- `references/case-01-payble-framer-rebuild.md` (exemplo real com tilt medido)
- `references/case-02-taaskhub-framer-audit.md` (pipeline de captura/review com sanitizacao de overlays)
- `exemplos/case-03-opscale-ux-sim` (SaaS/AI enterprise, dashboard + contraste)
- `exemplos/case-04-sanny-ux-sim` (editorial dark/alternativo + cursor customizado)

### 2.5. Analyze Visual Identity and Draft Guidelines (When Requested or Useful)

- Identificar assinatura visual dominante:
  - tipo de contraste
  - tipografia (peso, escala, ritmo)
  - linguagem de superfícies (cards, bordas, sombras, blur)
  - composicao (grid, editorial, bento, collage)
  - tom (corporativo, playful, disruptivo, minimalista)
  - motion/pointer signatures
- Sintetizar guidelines reutilizaveis em formato objetivo:
  - principios
  - tokens visuais
  - padroes de componentes
  - guardrails por breakpoint
  - o que evitar
- Quando o objetivo incluir repertorio/criacao de direcao, usar referencias externas curadas (ex.: [Behance UI/UX](https://www.behance.net/galleries/ui-ux)) como insumo de identidade, sem copiar layouts/codigo.

Abrir:
- `references/visual-identity-and-guidelines.md`
- `../../base-conhecimento-principal-ux/references/visual-identity-and-guidelines.md`
- `../../base-conhecimento-principal-ux/references/visual-identity-behance-uiux-trend-scan.md` (quando houver pesquisa de repertorio)
- `../../base-conhecimento-principal-ux/references/design-reference-platforms-catalog.md` (catalogo padrao ouro de fontes)

### 3. Rebuild as System, Not as Screenshot

- Construir tokens visuais (cores, raios, sombras, spacing, tipografia) seguindo hierarquia de 3 niveis.
- Criar componentes modulares antes de polir microdetalhes.
- Implementar motion significativo (nao animacao decorativa generica).
- Preservar legibilidade e UX em breakpoints menores.
- Tratar estados de UI (loading, empty, error) em todo componente com dados.
- Garantir acessibilidade (keyboard, focus, ARIA) em todo interativo.
- Escrever microcopy acionavel (CTAs com verbo, erros com sugestao).

Abrir detalhes de padroes em:
- `../../base-conhecimento-principal-ux/references/design-rules-and-heuristics.md`
- `../../base-conhecimento-principal-ux/references/component-patterns.md`
- `../../base-conhecimento-principal-ux/references/design-tokens-system.md`
- `../../base-conhecimento-principal-ux/references/accessibility-and-inclusion.md`
- `../../base-conhecimento-principal-ux/references/ux-states-and-edge-cases.md`
- `../../base-conhecimento-principal-ux/references/ux-writing-and-microcopy.md`

### 4. Validate and Critique

- Rodar local.
- Capturar screenshots Playwright por breakpoint e pontos de scroll.
- Verificar overflow, clipping, legibilidade, ritmo, CTA prominence, states, motion coherence.
- Verificar acessibilidade: contraste AA, focus visible, landmarks, headings, keyboard navigation.
- Verificar estados de UI: loading, empty, error tratados nos componentes com dados.
- Verificar metricas: CLS < 0.1, touch targets >= 40px, nenhum overflow horizontal.
- Relatar achados por severidade e agir nos problemas concretos.

Abrir:
- `../../base-conhecimento-principal-ux/references/ux-metrics-and-measurement.md` (probes Playwright + criterios)
- `../../base-conhecimento-principal-ux/references/accessibility-and-inclusion.md` (checklist pre-ship)

### 5. Learn and Promote

- Registrar o caso em `references/case-XX-*.md`.
- Promover aprendizagens recorrentes para guias gerais.
- Atualizar o index da base para manter discoverability.
- Atualizar a base global com:
  - classificacao de estilo (`disruptivo`, `medido`, `minimalista`, `profissional_clean`, etc.)
  - indices por caso e por estilo

Abrir:
- `references/knowledge-base-index.md`
- `references/agent-architecture-and-governance.md`
- `../../base-conhecimento-principal-ux/INDEX.md` (cerebro global: indices, taxonomia, docs)

## Deliverable Defaults

- Entregar resultado funcional antes de discutir refinamentos extensos.
- Informar comandos/URL local de execucao.
- Informar limites da simulacao (o que e fiel vs aproximado).
- Informar validacoes executadas (build, screenshots, Playwright, review de UX).

## References Map

### Design e Qualidade Visual
- `../../base-conhecimento-principal-ux/references/design-rules-and-heuristics.md`: heuristicas de UX, performance percebida, cognitive load, dark mode guardrails.
- `../../base-conhecimento-principal-ux/references/component-patterns.md`: 18 patterns (nav, hero, cards, forms, tables, feedback, skeleton, dashboard).
- `../../base-conhecimento-principal-ux/references/design-tokens-system.md`: hierarquia de tokens (primitivos, semanticos, componente) + dark mode mapping.

### Acessibilidade e Inclusao
- `../../base-conhecimento-principal-ux/references/accessibility-and-inclusion.md`: WCAG 2.1/2.2, ARIA patterns por componente, acessibilidade cognitiva, probes Playwright.

### Estados e Edge Cases
- `../../base-conhecimento-principal-ux/references/ux-states-and-edge-cases.md`: 9 estados de UI (loading, empty, error, success, partial, disabled, destructive, offline) + edge cases.

### Metricas e Medicao
- `../../base-conhecimento-principal-ux/references/ux-metrics-and-measurement.md`: Core Web Vitals, metricas de usabilidade, engajamento, metricas visuais do agente, probes Playwright.

### Escrita de Interface
- `../../base-conhecimento-principal-ux/references/ux-writing-and-microcopy.md`: CTAs, headlines, forms, errors, toasts, tom de voz por vertical.

### Identidade Visual e Repertorio
- `../../base-conhecimento-principal-ux/references/visual-identity-and-guidelines.md`: extracao de identidade visual + guidelines.
- `../../base-conhecimento-principal-ux/references/visual-identity-behance-uiux-trend-scan.md`: trends 2025-2026.

### Pipeline e Automacao
- `../../base-conhecimento-principal-ux/references/playwright-ux-review-loop.md`: captura, nomenclatura de screenshots, checklist de revisao.

### Arquitetura e Governanca
- `../../base-conhecimento-principal-ux/references/agent-architecture-and-governance.md`: regras de evolucao do skill/agente.
- `../../base-conhecimento-principal-ux/references/architectural-contracts.md`: EvidenceBundle, UXProfile, ScreenIntentSpec, TokenSpec.
- `../../base-conhecimento-principal-ux/references/knowledge-base-index.md`: indice e protocolo de atualizacao da base.

### Casos e Exemplos
- `../../base-conhecimento-principal-ux/references/case-01-payble-framer-rebuild.md`: fintech, motion scroll-linked.
- `../../base-conhecimento-principal-ux/references/case-02-taaskhub-framer-audit.md`: SaaS template, pipeline completo.
- `../../base-conhecimento-principal-ux/references/case-03-opscale-framer-rebuild.md`: SaaS/AI enterprise.
- `../../base-conhecimento-principal-ux/references/case-04-sanny-framer-rebuild.md`: editorial dark/alternativo.
- `exemplos/INDEX.md`: biblioteca de projetos-base (snapshots).

### Cerebro Global
- `../../base-conhecimento-principal-ux/INDEX.md`: navegacao completa (indices, taxonomia, docs).

## Scripts and Assets (Use Sparingly)

- Adicionar scripts em `scripts/` somente quando o workflow ficar repetitivo e merecer automacao (ex.: captura Playwright padronizada, diff visual, probes de transform).
- Preferir usar `scripts/playwright_ux_capture.mjs` para capturas multi-breakpoint com metricas e sanitizacao de promos/badges do Framer.
- Adicionar assets somente quando forem reutilizados em entregas (ex.: templates base de UI, tokens, componentes starter).
- Guardar projetos de referencia em `exemplos/` como snapshots enxutos (sem dependencias/build) para servir de base de implementacao.
- Manter `SKILL.md` enxuto e mover profundidade para `references/`.

## MCP Integration (Codex Review Agent)

O Design Agent se integra ao fluxo Codex via o mesmo MCP server do code review (`codex-review`).
Isso permite que qualquer cliente MCP (Claude Code, Cowork, etc.) submeta auditorias de UX com acesso a base de conhecimento completa.

### Como funciona

O MCP server `codex-review` agora suporta `task_type: "ux-review"` alem dos tipos existentes (`review`, `explain`, `architecture`).
Quando um job `ux-review` e submetido:

1. O profile `ux-design.yml` e carregado automaticamente (severidade UX, categorias, checklist)
2. A base de conhecimento do Design Agent e injetada como contexto (5 referencias core)
3. O formato de resposta inclui campos UX-especificos (categories, breakpoint_issues, style_assessment, wcag)
4. O Codex executa a analise com todo o conhecimento de design disponivel

### Fluxo (identico ao code review)

```
submit_analysis_job(task_type: "ux-review", ...) -> job_id
  |
get_analysis_job_status(job_id) -> poll ate succeeded
  |
get_analysis_job_result(job_id) -> findings com categorias UX
```

### Arquivos de integracao (no codex-review-agent)

| Arquivo | Funcao |
|---------|--------|
| `mcp-server/index.js` | Enum `ux-review` + auto-profile |
| `mcp-server/codex-adapter.js` | `loadUXKnowledge()` + response format UX |
| `profiles/ux-design.yml` | Profile com severidade, categorias, checklist UX |
| `cowork-skill/UX-SKILL.md` | Skill para plataforma Cowork |

### Base de conhecimento injetada

O adapter carrega automaticamente estas referencias da base global:

1. `design-rules-and-heuristics.md` — heuristicas, performance percebida, cognitive load
2. `accessibility-and-inclusion.md` — WCAG 2.1/2.2, ARIA, probes Playwright
3. `ux-states-and-edge-cases.md` — 9 estados de UI, edge cases
4. `component-patterns.md` — 18 patterns de componentes
5. `design-tokens-system.md` — hierarquia de tokens, dark mode

### Categorias de findings UX

- `accessibility` — violacoes WCAG, ARIA, contraste, focus
- `visual-hierarchy` — titulo, subtitulo, CTA, peso visual
- `responsive` — breakpoints, overflow, layout breaks
- `interaction` — hover, focus, keyboard, touch targets
- `states` — loading, empty, error, success, disabled
- `tokens` — consistencia de spacing, radius, shadow, color
- `performance` — CLS, LCP, skeleton, motion
- `microcopy` — CTAs, erros, empty states, labels
- `layout` — grid, alignment, spacing, density

### Configuracao

O path da base de conhecimento e resolvido automaticamente como projeto irmao:
```
../Design/base-conhecimento-principal-ux/
```
Override via variavel de ambiente: `UX_KNOWLEDGE_BASE=/caminho/absoluto`
