# Arquitetura de Casting, Scene e Pose com Base em Pesquisa Externa

Data: 2026-03-11

## Objetivo

Consolidar, com base em pesquisa externa, qual e a melhor arquitetura para resolver a etapa 2 do pipeline:

- criacao de modelo humana
- criacao de cenario
- criacao de pose

sem cair em:

- repeticao excessiva
- "mesma modelo" para varios usuarios
- mesmo fundo em todas as geracoes
- dependencia de prompt livre demais

## Problema

Os testes praticos mostraram que:

- prompt bom sozinho ajuda
- refs de pesquisa ajudam mais
- presets fixos resolveriam controle, mas tenderiam a repetir demais

Entao o problema real nao e "achar o prompt certo".

O problema real e:

- como gerar variedade controlada
- com consistencia comercial
- sem perder fidelidade da roupa

## O que a pesquisa externa indicou

### 1. Prompt parametrizado e melhor que prompt livre

As docs oficiais do Google para image gen reforcam o uso de atributos/parametros bem definidos, especialmente quando o produto precisa de consistencia.

Fonte:

- [Vertex AI image prompt guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide)

Leitura aplicada ao projeto:

- o usuario nao deve precisar escrever um prompt grande
- o sistema deve traduzir intencao de produto em atributos controlados

### 2. Variacao controlada e um problema real de produto

As docs do Imagen/Vertex tratam controle de amostragem como parte explicita do produto:

- `seed`
- `sampleCount`
- parametros de geracao

Fonte:

- [Generate images with Imagen](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images)

Leitura aplicada ao projeto:

- diversidade nao deve ser "deixar o modelo inventar"
- diversidade precisa ser desenhada como sistema

### 3. Few-shot e estrutura ajudam, mas excesso pode overfit

As estrategias de prompting do Gemini recomendam exemplos e estrutura, mas alertam para overfit e repeticao quando o modelo recebe exemplos demais ou muito fechados.

Fonte:

- [Gemini prompting strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)

Leitura aplicada ao projeto:

- nao vale despejar muitas referencias fixas
- vale usar poucas referencias certas e um compilador de atributos

### 4. Retrieval e melhor que preset fixo

Trabalhos recentes em moda e geracao multimodal apontam para arquiteturas de retrieval antes da geracao.

Fontes:

- [Fashion-RAG](https://arxiv.org/abs/2504.14011)
- [ComposeMe](https://arxiv.org/abs/2509.18092)

Leitura aplicada ao projeto:

- recuperar referencias relevantes antes de gerar melhora controle e personalizacao
- referencias podem ser separadas por funcao:
  - roupa
  - cabelo
  - pose
  - identidade visual

### 5. Atributos estruturados funcionam melhor que pessoa fixa

Papers e repos de moda/geracao humana controlavel mostram que o caminho robusto e modelar atributos, nao individuos fixos.

Fontes:

- [Text2Human](https://github.com/yumingj/Text2Human)
- [DeepFashion-MultiModal](https://github.com/yumingj/DeepFashion-MultiModal)
- [Fashionista](https://github.com/hg1722/fashionista)
- [IMAGDressing](https://github.com/muzishen/IMAGDressing)
- [UniFashion](https://github.com/xiangyu-mm/UniFashion)

Leitura aplicada ao projeto:

- o sistema nao deve ter "modelo brasileira 1, 2, 3"
- o sistema deve trabalhar com atributos:
  - idade visual
  - tom de pele
  - cabelo
  - expressao
  - energia comercial
  - tipo de cenario
  - tipo de pose

## O que isso significa para o projeto

## Nao recomendado

### 1. Presets fixos de modelos

Risco:

- repeticao entre usuarios
- sensacao de catalogo templateado
- mesmo rosto ou mesma familia visual reaparecendo

### 2. Prompt livre como pilar do produto

Risco:

- variancia alta
- pouca explicabilidade
- dificuldade de manter qualidade comercial

### 3. Grounding/web search como fonte primaria da geracao

Risco:

- resultados inconsistentes
- dependencia de open web
- dificuldade de padronizar qualidade visual

## Recomendado

### 1. Retrieval + curadoria

O sistema deve recuperar referencias antes de gerar.

Ordem ideal:

1. imagens do proprio anuncio
2. biblioteca interna curada
3. pesquisa externa como reforco

### 2. Casting engine parametrico

Em vez de modelos fixos, usar familias de casting.

Exemplo de familia:

- `br_urban_clean`
- `br_warm_commercial`
- `br_minimal_premium`
- `br_editorial_soft`
- `br_mature_elegant`

Cada familia define ranges, nao uma pessoa.

### 3. Scene engine parametrico

Em vez de "indoor premium" generico, usar familias de cena:

- apartamento paulista clean
- showroom de marca premium
- studio editorial neutro
- interior aconchegante marketplace
- outdoor urbano leve

### 4. Pose engine por tipo de peca

A pose nao deve ser totalmente livre.

Ela deve respeitar:

- leitura da roupa
- tipo de drapeado
- necessidade de catalogo
- risco estrutural da peca

### 5. Sampler + anti-repeat

O sistema precisa variar dentro de envelopes controlados.

Exemplo:

- sorteia familia de casting
- sorteia atributos internos
- verifica historico recente
- evita repetir:
  - mesma familia
  - mesmo cabelo
  - mesmo tom de pele
  - mesmo fundo
  - mesma pose

## Arquitetura recomendada

Pipeline sugerido:

1. entrada por URL ou upload
2. coleta deterministica de imagens
3. Gemini multimodal para curadoria
4. stage 1: estabilizacao da roupa
5. stage 2: retrieval de estilo + casting/scene/pose engine
6. sampler com anti-repeat
7. edit final

## Papel do Gemini e do Playwright

### Gemini

Serve para:

- analisar imagens
- classificar imagens
- escolher subsets
- ajudar a compilar prompt final

### Playwright

Serve para:

- capturar paginas dinamicas
- extrair galerias reais de marketplace

Nao deve ser o lugar da "inteligencia de direcao de arte".

## Decisao final

Com base na pesquisa externa, a melhor abordagem para o projeto e:

- nao usar presets fixos
- nao usar prompt livre como solucao final
- nao depender de grounding externo como nucleo

E sim:

- `retrieval + atributos estruturados + sampling + anti-repeat`

Essa arquitetura e a que melhor equilibra:

- variedade
- controle
- escalabilidade
- fidelidade da roupa
- realismo comercial

## Proximo passo recomendado

Desenhar no projeto uma estrutura experimental com:

1. familias de casting
2. familias de cenario
3. familias de pose
4. ranges por familia
5. sampler por job
6. memoria curta anti-repeat

Esse e o caminho mais promissor para que o pipeline gere imagens de moda vendaveis para sellers de marketplace no Brasil sem parecer repetitivo.
