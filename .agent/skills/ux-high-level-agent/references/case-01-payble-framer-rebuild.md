# Case 01: Payble-like Framer Rebuild (Public Render Analysis)

## Date

2026-02-25

## Context

Objetivo: analisar uma landing fintech em Framer (`payble.framer.ai`) e construir uma simulacao em codigo com alta similaridade visual e comportamental, rodando localmente na porta `3005`.

## Constraints and Positioning

- Usar somente evidencia publica (HTML/DOM/screenshot/renderizacao).
- Nao tentar burlar protecoes/anti-bot.
- Implementar codigo original.

## Evidence Collected

### Measured

- HTML publico completo (Framer publish page).
- Screenshots via Playwright em multiplos pontos de scroll.
- Extracao de headings/CTAs/secoes via DOM.
- Probe do mockup hero para medir `transform` real via `getComputedStyle(...).transform`.

### Observed

- Hero com fundo pontilhado, CTA principal escuro, CTA secundario ghost.
- Mockup de tablet/desktop inclinado no inicio e alinhando com o scroll.
- Forte uso de cards brancos com bordas suaves, sombras discretas e metricas coloridas.
- Widget lateral flutuante sobreposto.

## Key Technical Discovery (Important)

O efeito de inclinacao do mockup nao estava no container principal do dispositivo.
O transform foi encontrado no wrapper interno `data-framer-name=\"Ipad Content\"`.

### Measured transform samples (Framer)

- `scrollY=0` -> `matrix3d(... 0.959729, 0.280927 ... -0.280927, 0.959729 ...)`
- `scrollY=520` -> `matrix3d(... 0.998671, 0.0515478 ... )`
- `scrollY=680` -> `matrix3d(... 1, 0, 0 ... )`

Leitura pratica:

- O mockup inicia com tilt de perspectiva (aprox. `rotateX ~16deg`) e reduz para `0`.
- O alinhamento estabiliza por volta de `~680px` de scroll no viewport desktop usado.

## Rebuild Decisions

- Implementar hero device com `framer-motion` e `useScroll/useTransform`.
- Calibrar a curva de tilt com base na medicao Playwright (nao apenas por screenshot).
- Separar componentes por blocos reutilizaveis: nav, hero, mockup, stats, flow 3 colunas, features, pricing, faq, footer, widget.
- Usar tokens e CSS de sistema visual para facilitar migracao.

## UX Review (Post-build)

### What worked

- Similaridade alta na macro-hierarquia visual e na linguagem de cards.
- Efeito de tilt/alinhamento visivel no scroll.
- Zero overflow horizontal em desktop/tablet/mobile nas capturas verificadas.
- Responsividade funcional com simplificacao progressiva da tabela no mobile.

### Frictions found

- Widget lateral flutuante compete com conteudo em telas pequenas (oclusao parcial de cards e textos).
- Contraste de texto secundario sobre o card azul de goal pode cair em alguns trechos.
- Header sticky em breakpoints menores pode sobrepor visualmente o mockup de forma agressiva se o blur/sombra estiverem fortes.

## Promotion to Global Rules

Promover para guias gerais:

- Medir motion signature real quando a animacao for parte central da identidade visual.
- Rodar Playwright + screenshots ao fim de cada etapa importante.
- Fazer critica de UX baseada em evidencia (breakpoint-specific).
- Declarar com honestidade o que foi medido vs inferido.

## Next Iteration Ideas

- Medir easing/timing exatos de outros componentes scroll-linked.
- Adicionar diff visual semantico (referencia vs clone) por zonas da tela.
- Criar script padrao de captura/review para reuso em novos casos.
