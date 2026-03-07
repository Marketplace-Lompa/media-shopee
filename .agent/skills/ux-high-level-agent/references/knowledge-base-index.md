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
- `design-*.md`: heuristicas, criterios visuais, regras de qualidade.
- `component-*.md`: padroes de UI, composicao e motion.
- `visual-identity-*.md`: analise de identidade visual, repertorio e guidelines.
- `agent-*.md`: governanca do skill/agente e estrategia de evolucao.
- `../exemplos/case-XX-*`: snapshots de projetos completos reutilizaveis.

## Current Core References

- `case-01-payble-framer-rebuild.md`
- `case-02-taaskhub-framer-audit.md`
- `../exemplos/case-03-opscale-ux-sim` (snapshot local + captures)
- `../exemplos/case-04-sanny-ux-sim` (snapshot local + captures)
- `playwright-ux-review-loop.md`
- `design-rules-and-heuristics.md`
- `component-patterns.md`
- `visual-identity-and-guidelines.md`
- `../../../base-conhecimento-principal-ux/references/visual-identity-behance-uiux-trend-scan.md` (trend scan de repertorio)
- `../../../base-conhecimento-principal-ux/references/design-reference-platforms-catalog.md` (catalogo de fontes de referencia)
- `agent-architecture-and-governance.md`
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
