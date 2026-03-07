# UX Metrics and Measurement

## Purpose

Definir como medir qualidade de UX alem da revisao visual subjetiva. O agente deve saber quais metricas capturar, como interpreta-las e quando usa-las para justificar decisoes.

## Categorias de Metricas

### 1. Performance Percebida (Velocidade Sentida)

Nao e so sobre milissegundos; e sobre como o usuario percebe a velocidade.

#### Core Web Vitals (Google)
- **LCP (Largest Contentful Paint):** Bom < 2.5s, Ruim > 4s
  - O que mede: quando o maior elemento visivel renderiza
  - Afeta: primeira impressao de velocidade
  - Como melhorar: otimizar hero image, font-display swap, server response time

- **FID / INP (Interaction to Next Paint):** Bom < 200ms, Ruim > 500ms
  - O que mede: responsividade a interacao do usuario
  - Afeta: sensacao de que "funciona" vs "travou"
  - Como melhorar: evitar long tasks JS, otimizar event handlers

- **CLS (Cumulative Layout Shift):** Bom < 0.1, Ruim > 0.25
  - O que mede: estabilidade visual (quanto o layout pula)
  - Afeta: confianca e leitura
  - Como melhorar: dimensoes explicitas em imagens/videos, font-display, skeleton estavel

#### Metricas Complementares
- **TTFB (Time to First Byte):** velocidade do servidor
- **FCP (First Contentful Paint):** primeiro pixel util na tela
- **TTI (Time to Interactive):** quando a pagina responde a input

#### Como o Agente Usa
- Em auditoria: medir CLS via Playwright (`page.evaluate` + `PerformanceObserver`)
- Em reconstrucao: garantir LCP < 2.5s (hero renderiza rapido, fonts carregam)
- Em review: layout shift ao carregar dados -> `Finding: Medium-High`

### 2. Metricas de Usabilidade (Eficacia)

#### Task Completion Rate
- Percentual de usuarios que completam a tarefa alvo
- Medir: formularios submetidos, compras finalizadas, onboarding completado
- Referencia: > 90% para tarefas criticas

#### Time on Task
- Tempo para completar uma tarefa especifica
- Menos tempo = melhor (para tarefas utilitarias)
- Mais tempo pode ser positivo em conteudo (leitura, exploracao)

#### Error Rate
- Frequencia de erros do usuario por tarefa
- Tipo de erros: validacao, clique errado, abandono de fluxo
- Alta taxa = interface confusa ou deceptive patterns

#### Learnability
- Performance na primeira vez vs repetida
- Curva de aprendizado acentuada = complexidade desnecessaria
- Medir: tarefas completadas na 1a vs 3a tentativa

### 3. Metricas de Engajamento (Retencao)

#### Bounce Rate
- Percentual que sai sem interagir
- Alto bounce em landing: hero/CTA fracos, loading lento, proposta de valor confusa
- Contexto importa: blog post com alto bounce pode ser ok (leu e saiu satisfeito)

#### Scroll Depth
- Quanto da pagina o usuario percorre
- Util para landing pages e conteudo editorial
- Drop significativo = conteudo fraco ou layout monotono naquela secao

#### Engagement Rate (GA4)
- Sessoes com >10s, ou evento de conversao, ou >1 pageview
- Mais util que bounce rate para SPAs

#### Retention Metrics
- DAU/MAU ratio: stickiness do produto
- Cohort retention: usuarios voltando ao longo do tempo

### 4. Metricas de Satisfacao (Percepcao)

#### SUS (System Usability Scale)
- Questionario padrao de 10 itens, escala 1-5
- Score 0-100; acima de 68 = acima da media
- Util para comparar antes/depois de redesign

#### NPS (Net Promoter Score)
- "De 0 a 10, quanto recomendaria?"
- Promoters (9-10) - Detractors (0-6) = NPS
- Mede lealdade, nao usabilidade diretamente

#### CSAT (Customer Satisfaction)
- "Quao satisfeito com [experiencia]?"
- Mais especifico que NPS, util pos-interacao

#### CES (Customer Effort Score)
- "Quao facil foi [tarefa]?"
- Baixo esforco = boa UX
- Mais acionavel que NPS para melhorias de interface

### 5. Metricas de Acessibilidade

#### Automated Score
- Lighthouse Accessibility Score (0-100)
- axe-core violations count por pagina
- Referencia: 90+ como minimo aceitavel

#### Manual Audit Coverage
- Percentual de componentes auditados manualmente
- Automated pega ~30-40% dos problemas reais
- Manual necessario para: logica de leitura, qualidade de alt text, fluxo de teclado

#### Compliance Level
- WCAG 2.1 AA: minimo obrigatorio
- WCAG 2.1 AAA: aspiracional para contrastes e texto
- WCAG 2.2: recomendado para novos projetos

### 6. Metricas Visuais (Especificas do Agente)

#### Consistencia de Tokens
- Quantos valores unicos de spacing existem? (ideal: 8-12 da escala)
- Quantas cores unicas fora do sistema de tokens?
- Quantos tamanhos de fonte distintos?
- Magic numbers detectados (valores inline sem token)

#### Hierarquia Visual Score (Qualitativo)
- CTA principal e o elemento mais proeminente? (sim/nao)
- Titulo domina a secao? (sim/nao)
- Elementos secundarios nao competem? (sim/nao)
- Score: 3/3 = strong, 2/3 = adequate, 1/3 = weak

#### Responsiveness Score
- Overflow horizontal em algum breakpoint? (critico se sim)
- Layout shift entre breakpoints suave ou quebrado?
- Conteudo priorizado corretamente em mobile?

#### Motion Coherence
- Animacoes tem proposito? (orientar atencao, feedback, transicao)
- Timing consistente entre componentes similares?
- `prefers-reduced-motion` respeitado?

## Framework de Medicao por Etapa do Agente

### Auditoria
| O que medir | Ferramenta | Criterio |
|---|---|---|
| CLS | Playwright + PerformanceObserver | < 0.1 |
| Overflow horizontal | `scrollWidth > clientWidth` | false em todos viewports |
| Contraste | axe-core ou manual | AA compliance |
| Touch targets | computed dimensions | >= 40px |
| Heading hierarchy | DOM extraction | sequential, no gaps |
| Focus order | Tab walkthrough | logical sequence |

### Reconstrucao
| O que medir | Ferramenta | Criterio |
|---|---|---|
| LCP | Lighthouse ou Playwright | < 2.5s |
| Token consistency | grep/regex em CSS | 0 magic numbers ideal |
| Component reuse | code analysis | < 3 duplicacoes |
| Breakpoint coverage | 3 viewport screenshots | no overflow, readable |

### Review
| Achado | Metrica | Severidade |
|---|---|---|
| CLS > 0.25 | Performance | High |
| Overflow horizontal | Layout | High |
| Contraste < 4.5:1 | Accessibility | High |
| Touch target < 40px | Interaction | Medium |
| Magic numbers > 5 | Consistency | Medium |
| Heading skip | Semantics | Medium |
| No loading state | UX States | Medium |

## Playwright Probes para Metricas

### CLS Measurement
```javascript
const cls = await page.evaluate(() => {
  return new Promise(resolve => {
    let clsValue = 0;
    const observer = new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) clsValue += entry.value;
      }
    });
    observer.observe({ type: 'layout-shift', buffered: true });
    setTimeout(() => { observer.disconnect(); resolve(clsValue); }, 3000);
  });
});
```

### Overflow Detection
```javascript
const hasOverflow = await page.evaluate(() => {
  return document.documentElement.scrollWidth > document.documentElement.clientWidth;
});
```

### Touch Target Audit
```javascript
const smallTargets = await page.evaluate(() => {
  const interactives = document.querySelectorAll('a, button, input, select, textarea, [role="button"]');
  return Array.from(interactives).filter(el => {
    const rect = el.getBoundingClientRect();
    return rect.width < 40 || rect.height < 40;
  }).map(el => ({ tag: el.tagName, text: el.textContent?.slice(0,30), w: rect.width, h: rect.height }));
});
```

## Anti-Patterns de Medicao

- Medir so Lighthouse score sem entender o que cada metrica significa
- Comparar CLS entre paginas com conteudo completamente diferente
- Usar bounce rate isolado sem contexto de tipo de pagina
- Otimizar metricas de vaidade (pageviews) em vez de task completion
- Confundir "sem erros de acessibilidade automatizados" com "acessivel"
