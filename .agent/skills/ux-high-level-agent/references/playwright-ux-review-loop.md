# Playwright UX Review Loop

## Goal

Padronizar captura visual e critica de UX em etapas de UI para reduzir regressao e opiniao subjetiva.

## When to Use

Usar sempre que houver:

- nova tela
- mudanca relevante de layout
- refinamento de motion
- ajuste responsivo
- clone/reconstrucao de referencia visual

## Stage Gate (Mandatory for UI Work)

Ao concluir uma etapa importante:

1. Rodar local
2. Capturar screenshots via Playwright
3. Verificar metricas de viewport/overflow
4. Fazer critica de UX (findings concretos)
5. Corrigir issues relevantes
6. Revalidar screenshot se a correção alterar layout

## Recommended Capture Set

### Viewports

- Desktop: `1440x900`
- Tablet: `834x1112`
- Mobile: `390x844`

### Scroll points (suggested)

- `top`
- `hero-progress` (meio da animacao hero)
- `hero-aligned`
- `mid-content`
- `feature-section`
- `pricing/faq` (se existir)

## Minimum Metrics to Record

Registrar por screenshot (JSON ou console):

- `innerWidth`
- `innerHeight`
- `scrollY`
- `scrollHeight`
- `body.scrollWidth`
- `documentElement.scrollWidth`
- `hasHorizontalOverflow`

## Overlay Sanitization (Framer and Similar)

Para reviews de UX por screenshot, remover overlays promocionais fixos que poluem a analise visual do layout:

- badge inferior do Framer (`#__framer-badge-container`, `.__framer-badge`)
- promos de template/marketplace no canto inferior (ex.: `Remove This Buy Promo`)

Regras:

- Remover apenas overlays promocionais externos ao conteudo principal.
- Nao remover elementos do proprio produto/tela que o usuario precisa avaliar.
- Registrar quantos overlays foram ocultados por captura.

Observacao:

- Heuristica generica por texto/posicao ajuda, mas seletores explicitos para Framer melhoram robustez.

## UX Critique Template (Use Evidence)

### Findings first

Para cada achado:

- severidade (`High`, `Medium`, `Minor`)
- problema visivel
- impacto de UX
- viewport/scroll onde ocorre
- causa provavel (se clara)
- correção sugerida

### Focus areas

- Overflow/clipping
- Header overlap indevido
- CTA prominence
- Contraste e legibilidade
- Ritmo vertical (spacing)
- Densidade de tabela/lista
- Touch targets no mobile
- Motion coherence (entrada, scroll, hover)

## Motion Measurement (Use When Fidelity Matters)

Se um efeito visual for caracteristico da referencia:

- Probar `getComputedStyle(el).transform`
- Medir em varios `scrollY`
- Descobrir se o transform esta no elemento alvo ou em wrapper
- Calibrar clone com valores medidos (ou aproximacao declarada)

## Custom Cursor / Pointer Validation (Special Case)

Capturas padrao de screenshot normalmente **nao** mostram o ponteiro do mouse.
Se o projeto tiver cursor customizado (desktop-only), criar uma validacao dedicada:

- abrir viewport desktop
- mover `page.mouse` para pontos estrategicos (hero, CTA, card, input)
- aguardar poucos ms para follower/smoothing estabilizar
- capturar screenshot especifica de verificacao

Regra:

- validar cursor customizado separadamente da pipeline padrao de layout
- nao usar isso como substituto da revisao de layout/responsividade

## Honesty Rule

Sempre declarar:

- `Medido via Playwright`
- `Observado em screenshot`
- `Inferido para simulacao`

## Output Expectations

Ao finalizar etapa importante de UI, entregar:

- URL local
- lista de screenshots capturados
- resumo curto de UX review
- problemas encontrados (se houver)
- confirmacao de overflow horizontal (sim/nao)
- informacao de overlays ocultados (se aplicavel)
- se houver cursor customizado: screenshot de validacao do cursor (desktop)

## Reference Gallery Scan Mode (Behance and Similar)

Quando o pedido for pesquisa de repertorio/identidade visual (ex.: Behance), adaptar a pipeline:

1. Capturar galeria (multi-breakpoint + fullpage)
2. Extrair cards/links visiveis
3. Abrir amostra de projetos para tags/metadados
4. Sintetizar clusters de estilo e guidelines
5. Promover achados para a base global

Importante:

- isso complementa (nao substitui) a pipeline de review de layout para projetos locais
- tratar resultado como repertorio e direcao, nao especificacao literal de implementacao
