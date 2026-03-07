# Case 02: TaaskHub Framer Audit (Pipeline Hardening)

## Date

2026-02-25

## Context

Objetivo: executar a pipeline de analise visual em `https://taaskhub.framer.website/`, produzir review critica de UX por screenshots e usar o caso para endurecer a pipeline reutilizavel da skill.

## What Was Executed

- Captura HTML publico (Framer page metadata).
- Captura de scroll/DOM com script de analise geral.
- Pipeline de screenshots multi-breakpoint com Playwright:
  - desktop / tablet / mobile
  - pontos de scroll padronizados
  - metricas de overflow por captura

## Key Pipeline Learnings (Important)

## 1. Output path ambiguity in generic analyzer

O script inicial salvava em `analysis/` relativo ao `cwd`, o que gerou artefatos em pasta errada quando executado fora do contexto esperado.

### Promotion

Padrao novo: usar `--out-dir` explicito em scripts de pipeline reutilizaveis.

## 2. Framer overlays are not one thing

Existem pelo menos dois tipos de overlays promocionais que poluem screenshots:

- `#__framer-badge-container` (badge inferior / \"Made in Framer\")
- promo widget fixo do template (ex.: `data-framer-name=\"Remove This Buy Promo\"`)

Uma heuristica generica por texto/posicao nao foi suficiente para todos os casos.

### Promotion

Adicionar sanitizacao com seletores explicitos para widgets Framer conhecidos, alem de heuristica generica.

## 3. Clean screenshots matter for honest UX review

Sem remover overlays promocionais, a review visual fica contaminada (oclusao de cards/CTAs).
Remover overlays de marketplace/badge melhora a analise do layout real sem alterar o conteudo de produto.

## UX Review (Evidence-based)

## What works well

- `High` visual polish de hero para landing SaaS template:
  - tipografia forte e legivel
  - CTA primario/segundario claros
  - espacamento generoso
- Navegacao limpa com CTA destacado.
- Sem overflow horizontal em desktop/tablet/mobile nas capturas executadas.
- Boa adaptação do hero no mobile (reflow limpo, CTA empilhado e legivel).
- Cartoes/grades com linguagem visual consistente (borda suave, fundo claro, raio uniforme).

## Findings

### Minor: Hero subtitle line breaks feel slightly awkward on mobile

No mobile, o subtitulo quebra em linhas com ritmo um pouco irregular (linha curta isolada), o que reduz fluidez de leitura.

Impacto:

- Baixo impacto funcional, mas afeta refinamento visual premium.

Sugestao:

- Ajustar largura do bloco de copy ou `font-size/line-height` no breakpoint mobile para melhorar o rag das linhas.

### Minor: Decorative side badges/arrows near hero compete on small screens

Elementos decorativos (“Charles/You” e setas) continuam visiveis no mobile e disputam atencao com o bloco de copy/CTA.

Impacto:

- Baixo a medio (dependendo do objetivo de conversao no mobile).

Sugestao:

- Reduzir escala/opacidade ou ocultar alguns ornamentos abaixo de um breakpoint.

### Minor: Header + hero vertical spacing on tablet is efficient but dense

No tablet, nav + hero ficam visualmente corretos, mas a transicao para o primeiro bloco pode parecer compacta para um template premium.

Impacto:

- Baixo (estetico/ritmo), sem quebrar usabilidade.

Sugestao:

- Testar aumento sutil do espacamento abaixo do CTA ou antes do grid de stats/cards.

## No major layout breakages found in sampled screens

- Sem clipping relevante.
- Sem overflow horizontal.
- Sem colapso de estrutura nos breakpoints capturados.

## Pipeline Changes Implemented

Script novo:

- `scripts/playwright_ux_capture.mjs`

Capacidades:

- `--url`
- `--out-dir` explicito
- `--label`
- capturas multi-breakpoint padronizadas
- metricas por captura (`hasHorizontalOverflow`, viewport, scroll)
- opcao `--full-page`
- sanitizacao de badges/promos Framer conhecidos

## Suggested Next Iteration

- Adicionar `--scrolls` customizavel (lista/JSON) para sites com hero muito alto ou muito baixo.
- Exportar um `review.md` stub com checklist preenchivel por viewport.
- Adicionar modo diff visual (baseline vs nova iteracao) para trabalhar refinamentos.
