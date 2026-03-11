# Determinismo vs Engenharia de Prompt no Fluxo Two-Pass

Data: 2026-03-11

## Resposta curta

O fluxo atual nao e puramente engenharia de prompt.

Tambem nao e deterministico no resultado final.

A descricao mais correta e:

- deterministico no processo
- probabilistico na imagem final

Ou seja:

- conseguimos controlar a receita
- nao conseguimos garantir o mesmo pixel output a cada execucao

## Tese central

Os testes mostraram que o ganho de qualidade nao veio so de "achar um prompt melhor".

Veio da combinacao de:

- curadoria melhor de referencias
- separacao do problema em 2 etapas
- prompts curtos com lock estrutural
- ancoras visuais de detalhe
- correcao iterativa dos drifts mais comuns

Entao, para este projeto, o ponto mais importante nao e perguntar:

- "qual e o prompt magico?"

E sim:

- "qual parte do fluxo deve ser fixa?"
- "qual parte o agente pode decidir?"
- "qual parte sempre precisa de validacao?"

## O que hoje e controlavel de forma dura

Esses itens sao praticamente deterministas do ponto de vista de produto e engenharia:

### 1. Arquitetura do fluxo

Podemos decidir com 100% de controle se o job roda em:

- single-pass
- two-pass

Nos testes, o melhor equilibrio veio de:

1. gerar primeiro uma imagem-base muito fiel da roupa
2. editar depois modelo, innerwear e ambiente

Essa decisao de arquitetura e deterministica.

### 2. Modelo e endpoint

Podemos fixar:

- `gemini-3.1-flash-image-preview`
- `generate_images()` na etapa 1
- `edit_image()` na etapa 2

Enquanto essa configuracao nao mudar no codigo, o fluxo operacional e reprodutivel.

### 3. Curadoria de referencias

Podemos controlar:

- quantas referencias entram
- quais referencias entram
- a ordem em que entram
- se entram referencias vestindo
- se entram referencias de detalhe plano

Nos testes, isso foi tao importante quanto o prompt.

Exemplo de regra forte:

- usar `2` fotos vestindo coerentes
- adicionar `1` ou `2` refs de detalhe estrutural
- evitar despejar todo o lote no modelo

### 4. Parametros de inferencia

Tambem e controlavel:

- `aspect_ratio`
- `resolution`
- `thinking_level`
- numero de imagens

No fluxo validado, os defaults mais fortes foram:

- `4:5`
- `1K`
- `MINIMAL`

### 5. Templates de prompt

Podemos congelar templates como contrato.

Exemplo:

- prompt curto de geracao fiel
- prompt de edicao para troca de identidade/contexto
- clausulas de lock estrutural
- clausulas de `garment length`
- clausulas de `hem behavior`

Isso nao torna a saida deterministica, mas torna a logica do agente previsivel.

### 6. Regras de selecao do agente

O agente pode seguir regras fixas, por exemplo:

1. deduplicar
2. ranquear refs
3. escolher subset curto
4. gerar base fiel
5. escolher melhor base
6. editar identidade e ambiente

Esse encadeamento pode ser implementado como politica fixa.

## O que continua sendo probabilistico

Aqui esta a parte que nao deve ser tratada como deterministica.

### 1. A geracao da imagem em si

Mesmo com a mesma receita:

- mesmas refs
- mesmo prompt
- mesma resolucao
- mesmo `thinking_level`

o modelo ainda varia.

Nos testes isso apareceu de forma concreta:

- o mesmo setup ficou entre `0.91`, `0.93` e `0.94`

Entao:

- mesma entrada nao implica mesma imagem

### 2. Obediencia do modelo ao prompt

O prompt ajuda muito, mas nao e contrato duro.

Exemplos reais observados:

- uma edicao alongou a roupa mais do que a referencia
- outra manteve demais a linguagem da foto original
- outra trocou bem o ambiente, mas suavizou demais a estrutura da peca

Ou seja:

- o modelo interpreta
- nao apenas executa

### 3. Drift de atributos secundarios

Mesmo quando a roupa principal vai bem, podem variar:

- comprimento
- abertura frontal
- hem behavior
- estrutura da manga
- roupa interna
- cenario
- idade aparente da modelo

Por isso, certos atributos precisam ser explicitamente reforcados.

### 4. Consistencia facial e de identidade

Pedir "modelo diferente" nao garante o quanto ela vai ser diferente.

O modelo pode:

- mudar o rosto de forma forte
- mudar de forma parcial
- manter linguagem facial/pose muito proxima da referencia

## O que e engenharia de prompt

Esses itens dependem principalmente da forma como descrevemos a tarefa:

- tom catalogo/editorial
- tipo de pose
- look interno
- ambiente
- tipo de luz
- distancia da camera
- grau de polimento visual
- reforco de lock estrutural
- reforco de comprimento
- reforco de drapeado

Exemplo real:

- a correcao da `editmix_pose03` para `editmix_pose03b` veio de prompt mais preciso sobre `upper-thigh length` e `rounded cocoon hem`

Isso foi engenharia de prompt.

## O que nao e so engenharia de prompt

Esses fatores tiveram tanto peso quanto o texto:

### 1. Escolha da imagem-base

No fluxo two-pass, a melhor imagem final nao surgiu de um prompt unico.

Ela surgiu porque:

- escolhemos primeiro uma base muito fiel da roupa
- depois editamos identidade/contexto

Isso e decisao de pipeline, nao apenas prompt.

### 2. Escolha das referencias de detalhe

Passar `referencia.jpeg` e `referencia2.jpeg` como ancora na edicao teve impacto real.

Sem isso, a roupa tendia a:

- suavizar textura
- alongar demais
- virar cardigan mais generico

### 3. Separacao em etapas

Separar:

- fidelidade da roupa
- troca de identidade/contexto

foi mais importante do que alongar o prompt.

## Matriz pratica

### Controle duro

Esses itens devem virar contrato do sistema:

- modelo usado
- numero maximo de refs
- ordem das refs
- `4:5`
- `1K`
- `MINIMAL`
- two-pass para casos premium
- subset curto e curado
- template de prompt por etapa

### Controle probabilistico

Esses itens devem ser tratados como variaveis:

- qualidade final da imagem
- aderencia total ao comprimento
- fidelidade total do drapeado
- troca de identidade
- naturalidade fina de maos, cabelo, expressao

### Validacao obrigatoria

Esses itens nao devem ser aceitos sem checagem:

- comprimento correto da roupa
- hem correto
- orientacao e escala das listras
- caimento lateral
- nivel de troca de modelo
- se o ambiente realmente mudou
- se a imagem parece catalogo real

## O que o agente deve decidir

O agente pode decidir com base em heuristica:

- quais refs entram
- se o caso vai para single-pass ou two-pass
- qual prompt template usar
- se precisa de reforco de comprimento
- se precisa de reforco de hem behavior
- se precisa de uma segunda candidata para rerank

## O que o agente nao deve prometer

Nao devemos vender internamente nem externamente que o sistema:

- gera sempre o mesmo resultado
- garante fidelidade perfeita em uma unica chamada
- troca sempre modelo e ambiente sem nenhum drift
- dispensa validacao visual

Essas afirmacoes seriam falsas com o estado atual do fluxo.

## O que deve virar politica de produto

### 1. Processo fixo

O processo deve ser o mais fixo possivel.

Exemplo:

1. curar refs
2. gerar base fiel
3. selecionar melhor base
4. editar identidade/contexto
5. validar fidelidade

### 2. Saida com rerank

Como a imagem final nao e deterministica, faz sentido:

- gerar `2` candidatas em casos importantes
- reranquear por rubrica visual

### 3. QA visual ou rubric estruturada

Antes de confiar no ranking automatico, precisamos de ground truth humano.

Ou seja:

- rubric manual de fidelidade
- comparacao entre rubric humana e score automatico
- calibracao do ranking so depois

## Conclusao

O fluxo atual nao e:

- so prompt engineering

Nem e:

- deterministic image generation

Ele e um fluxo hibrido:

- arquitetura, selecao de refs e templates podem ser controlados de forma dura
- a imagem final continua sendo uma amostra probabilistica do modelo

A estrategia correta para o projeto e:

- maximizar determinismo no processo
- aceitar probabilidade na imagem
- compensar com two-pass, subset curto, locks estruturais e validacao

Essa e a forma mais honesta e tecnicamente correta de descrever o estado atual do sistema.
