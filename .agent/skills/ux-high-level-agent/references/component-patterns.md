# Modern Component Patterns (UX High-Level)

## Purpose

Catalogar componentes e composicoes recorrentes para reconstrucoes high-fidelity e sistemas de UI modernos.

## Composition Strategy

- Construir por camadas: tokens -> primitives -> composites -> sections.
- Modelar componente pela funcao de UX, nao apenas pela aparencia.
- Separar `content`, `layout`, `visual style`, `motion`, `states`.

## Core Patterns for Fintech / SaaS Landing + Product Mockups

## 1. Sticky Nav (Glass/Paper Hybrid)

### UX role

- Manter orientacao e CTA de conversao visiveis.

### Rules

- Fundo semi-opaco + blur leve.
- Sombra discreta para separacao do canvas.
- CTA unico forte na direita.
- Menu colapsavel em mobile com alvos claros.

## 2. Hero with Dotted Canvas + Dual CTA

### UX role

- Comunicar proposta de valor + acao principal + prova visual.

### Rules

- Titulo com escala agressiva e alta legibilidade.
- Subtitulo com largura limitada e contraste medio.
- CTA principal (filled/dark) + CTA secundario (ghost/text).
- Ornamento pontilhado de baixo contraste para profundidade sem ruido.

## 3. Device/Product Mockup with Scroll-Linked Tilt

### UX role

- Criar impacto inicial e transicao para secao de prova.

### Rules

- Entrar inclinado e alinhar com scroll para reforcar materialidade.
- Usar perspectiva no wrapper correto (muitas referencias aplicam transform em wrapper interno).
- Medir transform real quando a fidelidade for importante.
- Preservar legibilidade interna do mockup (conteudo nao pode virar textura).

## 4. Metric Cards / Stats Grid

### UX role

- Gerar prova quantitativa escaneavel.

### Rules

- 2x2 ou 1xN responsivo.
- Numero grande + label curta + texto de suporte.
- Cor usar como marcador de categoria, nao como fundo pesado.
- Dotted/light texture opcional com opacidade baixa.

## 5. Problem -> Handle -> Solution Flow Cards

### UX role

- Transformar dor em narrativa de produto.

### Rules

- Tres colunas com bullets e setas de fluxo.
- Cores semaforicas (red/blue/green) apenas em marcadores.
- Manter copy curta e acionavel.

## 6. Feature Split Block (Copy + Visual Demo)

### UX role

- Explicar capacidade do produto com evidencia visual contextual.

### Rules

- Alternar lado do visual por secao para criar ritmo.
- Usar visual cards empilhados (accounts, budgets, expenses) em canvas suave.
- Transformar bullets em pills escaneaveis.
- Incluir CTA de aprofundamento sem competir com CTA global.

## 7. Savings Bento Grid

### UX role

- Mostrar recursos complementares sem repetir layout de feature.

### Rules

- Variar spans (tall/wide) para ritmo visual.
- Misturar tipos de componente: progresso, insights, chips, timeline.
- Preservar consistencia de raio/sombra/borda.

## 8. Pricing Cards with Highlighted Plan

### UX role

- Apoiar decisao rapida e comparacao.

### Rules

- Um plano com destaque claro (badge + sombra + contraste).
- Preco dominante, subtitulo secundario.
- Lista de features curta, semanticamente consistente.

## 9. FAQ Accordion

### UX role

- Reduzir atrito final de conversao.

### Rules

- Trigger com area clicavel ampla.
- Indicador de estado (chevron) animado.
- Conteudo expandido com transicao curta e previsivel.

## 10. Floating Promo/Widget (Use Carefully)

### UX role

- Simular marketplace badge / quick actions.

### Rules

- Tratar como elemento de menor prioridade que o conteudo principal.
- Reduzir tamanho/contraste/oclusao em mobile.
- Permitir fechar facilmente.

## 11. Editorial Dark Hero with Collage Overlay

### UX role

- Criar assinatura visual forte (creative-tech / AI agency) com impacto tipografico.

### Rules

- Hero dark de alto contraste com headline oversized.
- Overlay collage/card promocional como tensao visual, sem bloquear CTA/headline.
- No mobile, preferir reposicionar o overlay em vez de manter sobre a copy.
- Manter CTA primario claramente visivel apesar da composicao agressiva.

## 12. Custom Cursor / Pointer Signature (Desktop-only)

### UX role

- Reforcar identidade visual de templates autorais/editoriais sem alterar layout.

### Rules

- Ativar apenas para `pointer: fine` e breakpoints desktop.
- Fornecer estados claros (`default`, `hover`, `press`) e opcionalmente label contextual (`Open`, `View`, `Type`).
- Nao quebrar interacao em inputs/textarea; permitir leitura de contexto de texto.
- Tratar como enhancement: a UI deve continuar excelente sem o cursor customizado.

## Motion Signatures (Recommended)

- Hero reveal: `opacity + y` com easing suave (`easeOut`) e duracao curta/media.
- Scroll-linked mockup: `useScroll + useTransform + useSpring`.
- Accordion: `height + opacity`.
- Progress bars/rings: animate on view, sem exagero de bounce.
- Custom cursor: follower com smoothing leve; evitar trail excessivo que prejudique precisao.

## Component Review Questions

- Este componente reforca a tarefa do usuario ou apenas preenche layout?
- O estado visual comunica prioridade corretamente?
- O componente continua legivel no mobile?
- A animacao ajuda compreensao ou so adiciona ruido?
- O componente e reutilizavel com props/variants?
