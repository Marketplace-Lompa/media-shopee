# Visual Identity Trend Scan (Behance UI/UX Gallery)

## Contexto

Estudo de repertorio visual a partir da galeria curada de UI/UX do Behance:

- Fonte: [Behance UI/UX Galleries](https://www.behance.net/galleries/ui-ux)
- Objetivo: extrair sinais recorrentes de identidade visual e UX para orientar o agente
- Data da captura: 2026-02-25

## Metodo (Evidence-first)

### Measured

- Captura Playwright multi-breakpoint (desktop/tablet/mobile) + fullpage
- Extração automatizada de cards visiveis e links (`/gallery/...`)
- Abertura de amostra de projetos para metadados (titulos/tags/tokens textuais)

### Observed

- Leitura visual das miniaturas/cards e da composição da galeria
- Identificação de clusters de estilo e linguagem

### Inferred

- Diretrizes de uso do repertorio para criação original
- Novos clusters/tags internos para nossa taxonomia

## Artefatos Locais

- Capturas: `/Users/lompa-marketplace/Documents/Design/case-runs/behance-uiux-gallery-deep-dive/ux-review`
- Extração estruturada: `/Users/lompa-marketplace/Documents/Design/case-runs/behance-uiux-gallery-deep-dive/analysis/behance-uiux-cards.json`
- Script de extração: `/Users/lompa-marketplace/Documents/Design/case-runs/behance-uiux-gallery-deep-dive/analysis/extract-behance-uiux-cards.mjs`

## Recorte Coletado (Measured)

- `24` cards visiveis/únicos capturados no recorte da galeria
- `8` projetos abertos em amostra para leitura de metadados
- Sem overflow horizontal nas capturas da pagina da galeria (desktop/mobile)

### Keywords em slugs (recorte visivel)

- `website`: 7
- `ai`: 5
- `brand` / `branding`: 8 (somado)
- `dashboard`: 2
- `app`: 2
- `saas`: 2
- `crypto` / `wallet` / `fintech`: 3 (somado por termos)

Leitura: mesmo dentro de “UI/UX”, a curadoria mistura fortemente **website + branding + product UI**, nao apenas interfaces de produto puras.

## Clusters de Linguagem Visual (Observed)

## 1. Brand + Product Hybrid (muito recorrente)

Projetos que combinam:

- identidade visual / logo / art direction
- landing page / website
- telas de produto/app/dashboard

Sinais:

- narrativa em camadas (brand -> site -> produto)
- maior consistência de cor e tipografia entre marketing e UI
- maior valor para direções “premium” e “produto com marca forte”

## 2. AI / SaaS Proof-led Interfaces

Sinais:

- dashboards/cards densos como prova de produto
- hero acompanhado de screenshot/mockup cedo
- tags e copy ligadas a AI, SaaS, analytics, automation

Implicacao para o agente:

- em casos de SaaS/AI, priorizar “prova visual” antes de ornamentação pesada

## 3. Fintech / Crypto Dark Premium

Sinais:

- fundos escuros ou gradientes profundos
- highlights frios/neon
- mockups mobile com dados financeiros
- foco em contraste e sensação de confiança + performance

Risco:

- exagero visual pode reduzir legibilidade de dados e hierarquia do CTA

## 4. Editorial / Creative Website Directions

Sinais:

- tipografia expressiva e layouts menos rígidos
- composições com colagem/imagem de impacto
- maior presença de “mood” e art direction

Aplicação:

- ótimo repertorio para pedidos “mais alternativo”, “mais autoral”, “menos template”

## 5. System / Components / Iconography Entries

Sinais:

- grids de ícones/sistemas
- peças focadas em consistência de UI kit

Aplicação:

- útil para reforçar rigor sistêmico quando o projeto está visualmente forte mas inconsistente

## Padrões de Identidade Visual Relevantes (Observed)

## Tipografia

- Headlines grandes e pesadas continuam dominando (especialmente em heros de marketing)
- Combinação comum:
  - headline muito forte
  - subtitulo neutro/cinzento
  - CTA com alto contraste
- Uso frequente de grotescas modernas em pesos altos (700/800+)

## Cor e Contraste

- Duas trilhas dominantes:
  - `clean light + accent` (SaaS corporativo)
  - `dark premium + neon/pastel accent` (AI/fintech/creative)
- Acentos isolados (1-2 cores fortes) performam melhor que paletas “arco-iris” sem hierarquia

## Composição

- Grid modular/bento aparece forte em showcases e dashboards
- Mockups de device continuam como linguagem de prova e contexto
- Mistura de blocos claros/escuros cria ritmo sem depender de motion

## Superfícies

- Cantos arredondados predominantes
- Sombras suaves e profundidade controlada
- Gradientes e blur usados como “atmosfera”, não só decoração

## UX / Narrative Patterns (Observed)

- Prova de produto cedo (screenshot/mockup) aumenta credibilidade visual
- Casos fortes alternam:
  - bloco emocional/hero
  - bloco de credibilidade (logos, métricas, UI)
  - bloco de explicação
- Integração de branding + UI gera percepção de maturidade (não só “tela bonita”)

## Diretrizes Promovidas para o Agente (Inferred)

## 1. Reference Ingestion Rule

Quando usar Behance como repertorio:

- coletar pelo menos `3-5` referências de estilos próximos
- extrair padrões convergentes
- sintetizar em regras/tokens antes de desenhar

Nao usar uma única peça como blueprint.

## 2. Cluster-first, not Piece-first

Classificar referência primeiro por cluster:

- `brand_product_hybrid`
- `proof_led_saas`
- `dark_fintech_premium`
- `editorial_alternativo`
- `system_component_rigor`

Depois gerar direção original.

## 3. Identity Before Components

Antes de escolher componente, fixar:

- assinatura tipográfica
- modelo de contraste
- intensidade de art direction
- papel de mockups/prova

Isso evita layout “bonito porém genérico”.

## 4. Responsive Guardrail for Strong Art Direction

Em direções mais autorais/editoriais:

- preservar headline e CTA
- reposicionar overlays e colagens no mobile (não só reduzir)
- manter ornamentos como secundários ao fluxo de conversão

## 5. Evidence Labels in Trend-Based Decisions

Usar sempre:

- `Measured` (captura/DOM/tokens)
- `Observed` (visual)
- `Inferred` (diretriz)

Para evitar transformar gosto em regra.

## Anti-padroes ao usar Behance como referencia

- Copiar layout 1:1 de uma peça de portfolio
- Copiar “efeito visual” sem reproduzir a hierarquia/objetivo de UX
- Misturar 4 estilos fortes no mesmo projeto
- Priorizar mockup bonito e enfraquecer CTA/copy
- Ignorar adaptação mobile de overlays e composições editoriais

## Impacto na Pipeline (Promover)

- Adicionar modo de “reference scan” para galerias:
  - capturas multi-breakpoint
  - extração de cards + slugs + tags
  - amostragem de projetos
  - clusterização e síntese
- Salvar relatório em Markdown e promover apenas padrões estáveis

## Limitacoes

- Recorte representa apenas a fatia visivel da galeria capturada no momento
- Behance favorece apresentação visual (nem sempre reflete produção real)
- Motion/interação profunda dos projetos nem sempre é observável nas thumbs

