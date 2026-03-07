# Case 04: Sanny Framer Rebuild (Editorial Dark / Alternative Direction)

## Date

2026-02-25

## Context

Objetivo: analisar `https://sanny-template.framer.website/` e criar uma reconstrução local similar, mantendo a assinatura dark/editorial da referência e levando a direção visual para um resultado **um pouco mais alternativo**, sem perder legibilidade/UX.

Projeto local criado:

- `/Users/lompa-marketplace/Documents/Design/sanny-ux-sim`
- Porta: `3008`

## Style Classification (Global KB)

### Eixos principais

- `disruptivo`: `medio`
- `medido`: `medio`
- `minimalista`: `leve`
- `profissional_clean`: `medio`

### Eixos complementares

- `motion_expressivo`: `medio`
- `densidade_informacao`: `medio`
- `playful`: `medio`
- `corporativo`: `baixo`

### Rationale (1-liner)

Template dark/editorial com tipografia agressiva e elementos collage, mais autoral e menos “clean SaaS”, porém ainda controlado para conversão.

## Evidence Collected

### Measured

- Screenshots Playwright desktop/tablet/mobile da referência (`case-runs/case-04-sanny-analysis/ux-review`)
- Metadados por viewport (overflow, scroll, headings/CTAs)
- Capturas Playwright da implementação local:
  - `pass1` (primeira versão)
  - `pass2` (após ajustes de mobile hero/promo)

### Observed

- Hero dark com tipografia oversized e alto contraste
- Card promocional estilo collage sobreposto ao hero
- Layout mais livre/editorial (menos grid “corporativo” rígido)
- Sequência de painéis dark/light e seções em cards grandes arredondados

### Inferred

- Organização interna de alguns elementos decorativos (collage/figuras) reproduzida de forma original
- Distribuição de conteúdo em seções posteriores simplificada para manter implementabilidade e clareza

## Implementation Notes

- Rebuild com React + TypeScript + Vite + `framer-motion`
- Direção visual intencionalmente:
  - dark de alto contraste
  - tipografia hero dominante
  - painéis arredondados e componentes com “peso” editorial
  - card promocional collage como elemento de tensão visual
- Estrutura implementada:
  - hero + navegação capsule
  - statement section
  - “How it works” (3 steps)
  - services grid
  - fit cards
  - case strip
  - team grid
  - faq + contact
  - footer CTA

## UX Review (Pass1 -> Pass2)

## Pass1 Findings (critical for mobile)

- `Major`: card promocional flutuante no mobile estava invadindo a copy/CTA do hero.
- `Minor`: largura útil da copy no mobile ficou pequena demais por causa da reserva de espaço para o card.

## Pass2 Fixes Applied

- Reposicionamento do card promocional mobile para uma área abaixo do bloco principal (mantendo clima editorial).
- Remoção da compressão excessiva da copy e dos CTAs.
- Reequilíbrio das larguras no mobile para preservar legibilidade e conversão.

## Pass2 Result

- Sem overflow horizontal em desktop/tablet/mobile.
- Hero mobile mantém a identidade alternativa sem sacrificar CTA/copy.
- Desktop/tablet preservam assinatura visual forte e composição dark.

## Promotion to Global Rules

- Em layouts editoriais com elementos sobrepostos, no mobile a prioridade deve ser:
  1. headline
  2. CTA
  3. copy
  4. ornamento/overlays
- Em vez de apenas reduzir escala de overlays, muitas vezes a solução correta é **reposicionar**.
- “Alternativo” precisa de guardrail: impacto visual não pode destruir leitura do hero.

## Next Iteration Ideas

- Medir com mais precisão o espaçamento e offsets do card collage da referência.
- Adicionar micro-motion editorial (parallax leve/tilt sutil) condicionado a `prefers-reduced-motion`.
