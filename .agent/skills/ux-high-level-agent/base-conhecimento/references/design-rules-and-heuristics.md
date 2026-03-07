# Design Rules and Heuristics (High-Level UX)

## Purpose

Manter nivel profissional de UX visual e interacao.
Evitar layouts \"bonitos\" mas fracos em clareza, ritmo e usabilidade.

## Core Principles

### 1. Clarity over decoration

- Tornar o proximo passo obvio (CTA, navegacao, estado atual).
- Reduzir ruido visual em elementos secundarios.
- Usar decoracao para reforcar hierarquia, nao para competir com ela.

### 2. Systems before pixels

- Definir tokens (cores, spacing, radius, shadows, typography) antes de micro-polir.
- Reutilizar componentes com variacoes, nao duplicar estilos arbitrarios.

### 3. Motion with purpose

- Usar motion para orientar atencao, indicar relacao espacial e reforcar feedback.
- Evitar microanimacoes genericas sem funcao.
- Respeitar `prefers-reduced-motion`.

### 4. Evidence-driven critique

- Revisar pelo comportamento real da UI (screenshots + interacao), nao apenas pelo codigo.
- Priorizar defeitos concretos de UX sobre opinioes esteticas.

## Visual Quality Rubric (Quick Audit)

## Hierarchy

- Titulo principal domina a tela sem competir com nav/ornamentos.
- Subtitulo sustenta contexto e reduz ambiguidade.
- CTA principal e CTA secundario estao claramente diferenciados.

## Rhythm and Spacing

- Blocos mantem ritmo vertical previsivel.
- Espacamentos internos seguem uma escala (ex.: 8/12/16/24/32).
- Seções nao parecem coladas nem excessivamente vazias.

## Surface Language

- Raios e sombras coerentes entre cards/inputs/modals/widgets.
- Bordas discretas ajudam separacao sem \"gritar\".
- Coloridos (blue/pink/green/orange) usados como sinais, nao como fundo dominante em excesso.

## Typography

- Escala de fonte clara por funcao (hero, heading, body, label, meta).
- Peso de fonte consistente por papel sem saltos arbitrarios.
- Comprimento de linha legivel em desktop e mobile.

## Density

- Tabelas/listas em mobile simplificadas em vez de comprimidas.
- Metadados secundarios escondidos/reordenados quando necessario.
- UI financeira/densa preserva legibilidade e escaneabilidade.

## Interaction

- Estados hover/focus/active presentes nos alvos importantes.
- Touch targets >= 40px no mobile para acoes frequentes.
- Accordions/toggles comunicam estado aberto/fechado.

## Responsiveness

- Sem overflow horizontal.
- Sem clipping relevante de CTA/texto.
- Reflows respeitam prioridade de conteudo.

## Performance UX (Velocidade Percebida)

### Principios
- Feedback instantaneo (<100ms) em toda acao direta (click, toggle, input)
- Skeleton screens preferidos sobre spinners para conteudo previsivel
- Conteudo above-the-fold carrega primeiro (priorizar hero/nav/CTA)
- Layout estavel: reservar dimensoes para imagens/videos (prevenir CLS)

### Patterns de Loading
- **Otimista:** mostrar resultado esperado antes da confirmacao do servidor
- **Progressivo:** renderizar parcial e completar (texto antes de imagens)
- **Skeleton:** blocos neutros simulando layout final com shimmer sutil
- **Nenhum indicador:** para acoes < 100ms (nao poluir com loading desnecessario)

### Regras
- Botoes de submit: desabilitar durante processamento + spinner inline
- Nao exibir spinner global para acoes locais (contextualizar)
- Loading > 3s: adicionar mensagem textual de progresso
- Loading > 10s: mover para background com notificacao

## Cognitive Load (Reducao de Esforco Mental)

### Principios
- Limitar opcoes visiveis (5-7 por grupo, preferir 5)
- Progressive disclosure: detalhes sob demanda, nao tudo de uma vez
- Agrupamento por proximidade e whitespace (Gestalt)
- Consistencia de patterns: mesma acao = mesma aparencia em toda interface

### Regras de Decisao
- Defaults inteligentes reduzem decisoes (pre-selecionar opcao mais comum)
- Comparacao: side-by-side com diferenciacao clara (pricing, planos)
- Wizards/steps para fluxos complexos (max 5-7 steps)
- Nao exigir memorizacao entre telas (manter contexto visivel)

### Typography e Legibilidade
- Line-height body: minimo 1.5x (ideal 1.6-1.75)
- Largura de linha: max 80 chars, ideal 60-75
- Paragrafo spacing: 1.5-2x font-size entre blocos
- Contraste de peso tipografico para hierarquia (nao depender so de tamanho)

## Dark Mode Guardrails

### Principios
- Nao inverter cores; remapear hierarquia de superficies
- Superficies elevadas ficam mais claras (ao contrario do light mode)
- Sombras perdem eficacia em dark; usar bordas sutis como alternativa
- Imagens com fundo transparente: verificar visibilidade em ambos os temas

### Regras
- Testar contraste AA em ambos os modos (erro mais comum: texto secondary)
- Cores de feedback (success/error/warning) precisam de ajuste em dark
- `prefers-color-scheme`: deteccao automatica + toggle manual
- Nao usar preto puro (#000) como background (gray-900/950 reduz fadiga)

## Common Failure Modes (Watchlist)

- Hero visualmente forte, mas CTA fraco ou distante demais.
- Mockup bonito cobrindo texto importante no mobile.
- Overlay/editorial collage visualmente forte invadindo headline/copy/CTA no mobile.
- Widget flutuante bloqueando cards/CTA em telas pequenas.
- Header sticky com sombra/blur excessivo degradando legibilidade.
- Cards coloridos com texto secundario sem contraste suficiente.
- Motion de scroll sem sincronismo (parece bug em vez de intencional).

## High-Value Fix Patterns

- Reduzir densidade por breakpoint (colunas -> pilha).
- Simplificar tabela no mobile (2 colunas essenciais).
- Reforcar contraste de texto em cards coloridos.
- Reduzir escala/sombra de elementos flutuantes em telas menores.
- Reposicionar overlays no mobile (muitas vezes melhor que apenas reduzir escala).
- Em layouts alternativos/editoriais, preservar ordem de prioridade: headline -> CTA -> copy -> ornamentos.
- Calibrar timing/easing de motion principal a partir de medicao real quando houver referencia.

## Alternative / Editorial Layout Guardrails

- "Alternativo" nao pode comprometer leitura do hero nem acao principal.
- Elementos de impacto (collage, stickers, promo cards) devem parecer intencionais em desktop e adaptados em mobile.
- Se um overlay cria tensao visual boa no desktop, testar:
  - reposicionamento em mobile
  - reducao de opacidade
  - mudanca de ordem vertical
  antes de remover completamente.

## Custom Cursor Guardrails (When Used)

- Ativar apenas em `pointer: fine` (desktop/laptop com mouse/trackpad).
- Desativar em touch/mobile e respeitar `prefers-reduced-motion` quando houver trail forte.
- Nao esconder cursor nativo em campos de texto se isso prejudicar UX de input.
- Cursor customizado deve comunicar estado (move/open/type) sem virar ruido constante.

## Cross-References (Aprofundamento)

- Acessibilidade detalhada: `accessibility-and-inclusion.md`
- Estados de UI (loading/empty/error/success): `ux-states-and-edge-cases.md`
- Sistema de tokens: `design-tokens-system.md`
- Metricas de qualidade: `ux-metrics-and-measurement.md`
- Escrita de interface: `ux-writing-and-microcopy.md`
- Padroes de componentes: `component-patterns.md`
