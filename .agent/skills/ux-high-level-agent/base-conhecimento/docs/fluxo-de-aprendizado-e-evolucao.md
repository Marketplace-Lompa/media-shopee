# Fluxo de Aprendizado e Evolucao (Cerebro Global)

## Ideia central

Cada caso gera:

1. evidencia
2. implementacao
3. critica
4. aprendizado promovido

Sem essa quarta etapa, o agente executa bem mas nao evolui.

## Loop oficial (por caso)

## Etapa 1: Ingestao

- receber URL / screenshots / objetivo
- registrar contexto
- definir criterio de sucesso observavel

## Etapa 2: Coleta de evidencia

- Playwright screenshots
- DOM/headings/CTAs
- metricas de viewport/overflow
- medições especiais (motion/transform) quando necessario

Saida:

- artefatos em `case-runs/` ou `analysis/` do projeto local

## Etapa 3: Reconstrucao / implementacao

- criar sistema visual (tokens)
- criar componentes modulares
- reproduzir assinatura de layout/motion de forma original

## Etapa 3A: Analise de identidade visual e guidelines (quando aplicavel)

- extrair assinatura visual da referencia (tipografia, contraste, composicao, tom, motion)
- classificar estilo (eixos + niveis)
- sintetizar guidelines reutilizaveis (principios, tokens, guardrails, anti-padroes)
- usar referencias externas curadas (ex.: Behance UI/UX) como repertorio, sem copiar

## Etapa 4: Validacao por etapa (obrigatoria)

- rodar local
- capturar desktop/tablet/mobile
- fazer critica UX objetiva
- corrigir problemas relevantes

## Etapa 5: Consolidacao de caso

Atualizar:

- `references/case-XX-*.md`
- classificacao de estilo (eixos + niveis)
- guidelines de identidade visual (quando o caso exigir direcao estetica)
- indices (`cases-index` e `cases-by-style`)
- snapshot em `exemplos/` (sem dependencias/build)

## Etapa 6: Promocao de padroes

Se algo se repetir ou tiver valor alto:

- mover para `design-*.md`
- mover para `component-*.md`
- mover para `playwright-*.md`
- ajustar skill/pipeline

## Separacao obrigatoria de evidencias

Todo caso deve distinguir:

- `Measured`: medido por DOM/computed style/Playwright
- `Observed`: observado visualmente
- `Inferred`: aproximado na implementacao

## Criticidade e promocao

### O que fica so no caso

- detalhes especificos de um template
- tuning local muito particular
- hacks temporarios de layout

### O que sobe para o cerebro global

- padrao de problema responsivo recorrente
- heuristica de hierarquia visual
- tecnica de medicao reutilizavel
- classificacao de estilo util para reuso

## Sinais de evolucao boa

- menos retrabalho visual nos casos seguintes
- maior consistencia entre breakpoints
- mais velocidade de bootstrap em novos casos
- indices/taxonomias realmente ajudam a achar referencias
- pipeline fica mais limpa e menos dependente de memoria humana
