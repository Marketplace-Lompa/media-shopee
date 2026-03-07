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

## 13. Form System (Input + Validation + Submit)

### UX role

- Coletar dados do usuario com minimo atrito e maximo feedback.

### Rules

- Label visivel permanente acima do campo (nunca so placeholder)
- Placeholder como exemplo de formato ("joao@empresa.com"), nao como instrucao
- Helper text abaixo do campo para orientar antes do erro
- Validacao inline em tempo real para campos com formato previsivel (email, telefone)
- Erro: cor de destaque (red sutil) + icone + texto especifico proximo ao campo
- Sucesso de campo: checkmark verde discreto (nao exagerar em cada campo)
- Agrupamento: `fieldset` + `legend` para conjuntos relacionados
- Autocomplete attributes para campos padrao (name, email, tel, address)
- Submit: desabilitado durante processamento, texto muda ("Enviando...")
- Formulario longo: multi-step com progress indicator (max 5-7 steps)

### States obrigatorios
- Default, Focus, Filled, Error, Disabled, Loading (quando async validation)

## 14. Navigation Patterns

### UX role

- Orientar o usuario sobre onde esta, o que pode fazer e como voltar.

### 14a. Top Navigation (Horizontal)

- Logo a esquerda, links centrais ou a esquerda, CTA a direita
- Active state claro (underline, bold, ou cor) no item atual
- Collapse para hamburger em mobile (breakpoint: ~768px)
- Hamburger menu: overlay ou slide com alvos de toque >= 44px
- Close button explicito (nao depender so de click-outside)

### 14b. Breadcrumbs

- Usar em hierarquias > 2 niveis
- Formato: `Home > Secao > Sub-secao > Pagina atual`
- Ultimo item (pagina atual) nao e link
- Truncar items intermediarios em mobile com "..." se necessario

### 14c. Tabs

- Usar para conteudo mutuamente exclusivo no mesmo contexto
- Active tab visualmente dominante (borda inferior, cor, contraste)
- Swipeable em mobile (indicar com seta ou truncar visivelmente)
- Nao usar tabs para navegacao entre paginas diferentes
- Keyboard: Arrow keys entre tabs, Tab key para conteudo

### 14d. Sidebar Navigation

- Usar em apps/dashboards com muitas secoes
- Collapsible em tablets, hidden por default em mobile
- Icone + label (nao so icone) para discoverability
- Grupo com separadores ou headers para organizar items

## 15. Feedback Patterns

### UX role

- Confirmar que a acao do usuario teve efeito e informar proximos passos.

### 15a. Toast / Snackbar
- Para feedback nao-critico de acoes (salvar, copiar, toggle)
- Posicao: bottom-center ou bottom-right (consistente em toda app)
- Auto-dismiss: 3-5 segundos
- Max 1-2 na tela simultaneamente
- `aria-live="polite"` para screen readers

### 15b. Inline Alert / Banner
- Para informacao contextual persistente (aviso, status, novidade)
- Cores por tipo: info (blue), success (green), warning (amber), error (red)
- Icone + texto + acao opcional (dismiss ou link)
- Posicao: topo do conteudo relevante, nao topo global

### 15c. Progress Indicator
- Determinate: quando se sabe o total (upload, multi-step form)
- Indeterminate: quando nao se sabe (busca, processamento)
- Linear (bar) para fluxos sequenciais, circular (spinner) para acoes pontuais
- Texto de progresso quando > 3 segundos ("Etapa 2 de 4", "45%")

### 15d. Confirmation Dialog
- Para acoes destrutivas ou irreversiveis
- Titulo: o que vai acontecer ("Deletar projeto?")
- Body: consequencia ("Todos os dados serao removidos")
- Botoes: acao especifica ("Deletar") + cancelar
- Nunca "Sim" / "Nao" / "OK" como labels de botao

## 16. Skeleton / Placeholder Patterns

### UX role

- Manter estabilidade visual durante loading e prevenir CLS.

### Rules

- Reproduzir layout aproximado do conteudo esperado
- Usar cor neutra (gray-100/200) com animacao shimmer sutil
- Dimensoes realistas (nao blocos genericos uniformes)
- Card skeleton: manter proporcoes reais do card final
- List skeleton: 3-5 items placeholder (nao 20)
- Avatar skeleton: circulo do tamanho correto
- Text skeleton: linhas de largura variada (nao todas iguais)
- Fade-out suave ao substituir por conteudo real (nao snap)

## 17. Table / Data Grid (Dense UI)

### UX role

- Apresentar dados estruturados com escaneabilidade e acoes claras.

### Rules

- Header fixo ao scroll vertical
- Sortable columns: indicador de direcao claro (arrow up/down)
- Linhas alternadas em zebra sutil ou separadores leves
- Acoes por row: truncar em menu "..." (nao poluir com 5 botoes por linha)
- Mobile: simplificar para 2-3 colunas essenciais ou transformar em cards
- Selecao: checkbox a esquerda com bulk actions no topo
- Paginacao ou infinite scroll com contagem total visivel
- Empty state da tabela: "Nenhum dado encontrado" + acao relevante

## 18. Dashboard Layout (Information Architecture)

### UX role

- Oferecer visao geral acionavel com acesso rapido a detalhes.

### Rules

- KPI/metrics cards no topo (3-4 numeros principais)
- Graficos contextuais, nao decorativos (cada grafico responde uma pergunta)
- Filtros globais acessiveis mas nao dominantes
- Widgets reorganizaveis quando possivel (customizacao)
- Mobile: stack vertical por prioridade, graficos simplificados
- Loading: skeleton por widget, nao global spinner

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
- Os estados (loading, empty, error, disabled) foram tratados?
- A acessibilidade (keyboard, screen reader, contraste) foi considerada?

## Cross-References (Aprofundamento)

- Tokens para componentes: `design-tokens-system.md`
- Estados de UI detalhados: `ux-states-and-edge-cases.md`
- ARIA patterns por componente: `accessibility-and-inclusion.md`
- Copy/labels para componentes: `ux-writing-and-microcopy.md`
- Regras visuais de qualidade: `design-rules-and-heuristics.md`
