# Validacao Manual de Grounding Brasil na Etapa 2

Data: 2026-03-11

## Objetivo

Testar manualmente a hipotese de que a pesquisa de referencias brasileiras deve entrar na etapa 2 do fluxo:

1. a peca ja esta estabilizada
2. a pesquisa passa a mirar modelo humana, pose e cenario
3. essa pesquisa deve melhorar o resultado final de catalogo sem destruir a fidelidade da roupa

## Ponto de partida

Base usada:

- `app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_2.png`

Essa base veio do fluxo automatico da fase 2 e ja tinha:

- `garment_fidelity`: `0.95`
- `overall_score`: `0.94`

## Logica do teste

Nesta rodada, a pesquisa NAO foi sobre a peca.

A peca ja era conhecida:

- `ruana_wrap`
- `open front`
- `draped silhouette`
- `cape-like arm coverage`
- `upper-thigh length`

Entao a pesquisa foi sobre o universo visual de saida:

- modelo brasileira
- linguagem de beleza e cabelo
- pose comercial
- indoor premium brasileiro

## Fontes pesquisadas

Foram usadas paginas de campanhas/editoriais da Way Model:

- [Meet Iohany Alves](https://waymodel.com.br/en/noticias/meet-iohany-alves)
- [Ariane Norbel para Principessa](https://waymodel.com.br/noticias/ariane-norbel-principessa)
- [Vivica em editorial para Mylena Saza](https://waymodel.com.br/noticias/vivica-em-editorial-pro-mylena-saza)
- [Kely Ferro por Mariana Valente](https://waymodel.com.br/noticias/kely-ferro-por-mariana-valente)
- [Rafaela Rocha Hering Campaign](https://waymodel.com.br/noticias/rafaela-rocha-hering-campaign)

As imagens baixadas ficaram em:

- `docs/grounding-manual-brasil/raw_refs`

Folha de contato:

- `docs/grounding-manual-brasil/contact_sheet.jpg`

## Refs escolhidas manualmente

Depois da inspecao visual, as refs mais uteis para a etapa 2 foram:

- `docs/grounding-manual-brasil/raw_refs/rafaela_4.jpg`
  - melhor referencia de modelo/vibe brasileira premium
  - cabelo natural cacheado forte
  - leitura de beleza comercial, nao caricatizada

- `docs/grounding-manual-brasil/raw_refs/ariane_4.jpg`
  - melhor referencia de indoor clean
  - ajuda a linguagem de apartamento/showroom claro

- `docs/grounding-manual-brasil/raw_refs/ariane_5.jpg`
  - melhor referencia de postura comercial mais classica

Anchors de roupa mantidas:

- `docs/roupa-referencia-teste/referencia.jpeg`
- `docs/roupa-referencia-teste/referencia2.jpeg`

## Receita usada

Pacote de referencias da etapa 2:

1. `referencia.jpeg`
2. `referencia2.jpeg`
3. `rafaela_4.jpg`
4. `ariane_4.jpg`
5. `ariane_5.jpg`

Ideia:

- as duas primeiras travam a peca
- as tres ultimas ajudam a reescrever modelo, ambiente e linguagem comercial

## Quanto o cenario veio da pesquisa

Sim, o cenario final teve influencia direta da pesquisa, mas nao como copia literal de uma unica foto.

Na pratica, o fundo final veio da combinacao de:

- prompt explicito de ambiente
- refs brasileiras de indoor premium
- interpretacao do proprio Nano 2

A influencia mais forte de cenario veio de:

- `docs/grounding-manual-brasil/raw_refs/ariane_4.jpg`

Essa referencia ajudou principalmente em:

- janela ampla com luz natural
- leitura de apartamento/showroom claro
- branco dominante com piso claro
- atmosfera comercial limpa, sem cara de estudio artificial

A ref `ariane_5.jpg` ajudou mais em:

- postura comercial
- enquadramento limpo
- leitura de anuncio premium

A ref `rafaela_4.jpg` ajudou mais em:

- escolha implicita de perfil de modelo
- cabelo natural cacheado
- vibe brasileira premium sem caricatura

Leitura objetiva:

- a pesquisa influenciou o cenario
- mas o resultado final foi uma linguagem visual guiada, nao uma reproducao direta

Isso e importante para o produto porque:

- reduz risco de ficar preso a uma foto externa especifica
- permite usar referencias de pesquisa como "direcao de arte"
- preserva flexibilidade para o modelo montar uma cena nova e comercial

## Variantes geradas

Run dir:

- `docs/grounding-manual-brasil/20260311_183407`

Resumo:

- `docs/grounding-manual-brasil/20260311_183407/summary.json`

### Variante A

Arquivo:

- `app/outputs/manualbr20260311_183407a/edit_manualbr20260311_183407a_1.png`

Prompt:

```text
Keep the garment exactly the same: same knit or crochet texture continuity, same stitch pattern and fiber relief, same pattern placement and stripe scale, same open-front ruana construction, same draped cocoon silhouette, same rounded cocoon hem behavior, same cape-like arm coverage, and upper-thigh length. Use the extra style references only to guide Brazilian premium catalog mood, model vibe, and scene language. Replace the model with a clearly different adult Brazilian woman with natural Brazilian features, medium-brown skin, long natural curly hair, subtle makeup, and a calm confident expression. Place her in a bright premium Brazilian indoor catalog setting, like a refined Sao Paulo apartment showroom with white walls, pale stone floor, large daylight windows, and subtle wood furniture. Use a standing frontal pose with full garment visibility. Change the inner top to a clean white crew-neck tee. Keep the image highly photorealistic, premium marketplace catalog quality, natural skin texture, and clean e-commerce readability.
```

Scores:

- `garment_fidelity`: `0.95`
- `environment_change_strength`: `1.00`
- `overall_score`: `0.93`

### Variante B

Arquivo:

- `app/outputs/manualbr20260311_183407b/edit_manualbr20260311_183407b_1.png`

Prompt:

```text
Keep the garment exactly the same: same knit or crochet texture continuity, same stitch pattern and fiber relief, same pattern placement and stripe scale, same open-front ruana construction, same draped cocoon silhouette, same rounded cocoon hem behavior, same cape-like arm coverage, and upper-thigh length. Use the extra style references only to guide Brazilian premium catalog mood, model vibe, and scene language. Replace the model with a clearly different adult Brazilian woman with natural Brazilian features, medium-brown skin, long natural curly hair, subtle makeup, and a calm confident expression. Place her in a bright premium Brazilian indoor catalog setting, like a refined Sao Paulo apartment showroom with white walls, pale stone floor, large daylight windows, and subtle wood furniture. Use a natural subtle three-quarter standing pose with full garment visibility. Change the inner top to a clean white crew-neck tee. Keep the image highly photorealistic, premium marketplace catalog quality, natural skin texture, and clean e-commerce readability.
```

Scores:

- `garment_fidelity`: `0.95`
- `environment_change_strength`: `1.00`
- `overall_score`: `0.95`

## Leitura humana

### Variante A

Acertou:

- boa leitura frontal de e-commerce
- modelo diferente da base anterior
- cabelo e expressao mais alinhados com o objetivo Brasil premium
- ambiente clean e comercial

Limite:

- ficou mais padrao
- boa para marketplace, menos sofisticada

### Variante B

Acertou:

- melhor equilibrio entre editorial e comercial
- pose 3/4 leve valorizou o caimento
- continuou legivel para catalogo
- o ambiente ficou mais convincente e refinado

Limite:

- ligeiramente menos "segura" que a frontal para catalogo massivo

## Por que a pose foi conservadora

A pose foi conservadora de proposito.

O objetivo desta rodada nao era explorar toda a diversidade de pose possivel.

O objetivo era isolar a variavel:

- "a pesquisa Brasil melhora modelo e cenario sem quebrar a roupa?"

Como a peca tem drapeado complexo, a pose mexe diretamente em:

- comprimento aparente
- abertura frontal
- comportamento da barra
- volume lateral
- leitura do caimento

Por isso, nesta primeira bateria, foram usados apenas dois niveis seguros:

- frontal limpa
- 3/4 leve

Essas poses foram escolhidas porque:

- mantem a peca totalmente legivel
- reduzem risco de drift estrutural
- facilitam comparar uma variante com a outra
- evitam contaminar a leitura do teste com uma pose agressiva demais

Em outras palavras:

- a decisao foi metodologica, nao estetica

Se a pose fosse mais ousada logo nesta etapa, seria dificil saber se o resultado melhorou ou piorou por causa:

- da pesquisa Brasil
- da nova pose
- da interpretacao do Nano

Conclusao de produto:

- pose conservadora deve ser o default inicial
- pose mais aberta deve entrar depois, como preset controlado
- nao vale abrir "criatividade livre" de pose antes de termos uma matriz de teste bem medida

## Conclusao

Essa rodada validou a hipotese principal:

- pesquisar a etapa 2 faz sentido
- a pesquisa deve ser sobre o universo visual de saida, nao sobre a peca

O ganho observado foi:

- modelo mais brasileira e mais crivel para o mercado local
- indoor premium mais alinhado com Brasil urbano comercial
- pose mais coerente com catalogo sem sacrificar a peca

Leitura final:

- a pesquisa Brasil nao substitui o two-pass
- ela melhora a etapa 2 do two-pass

## Implicacao para o produto

O agente futuro deve operar assim:

1. entender a peca e estabilizar a roupa
2. pesquisar referencias brasileiras de modelo, pose e cenario
3. compilar um prompt curto e controlado
4. editar a base fiel com anchors da roupa + refs de estilo

Essa ordem e a mais promissora para transformar o resultado em algo vendavel para sellers e anunciantes de marketplace no Brasil.

## Proximo passo recomendado

Depois desta rodada, a progressao mais segura e:

1. manter `frontal` e `3/4 leve` como baseline
2. abrir uma bateria especifica so de pose
3. testar presets como:
   - passo leve
   - mao no quadril suave
   - mao ajustando a barra ou manga
   - movimento editorial controlado
4. comparar sempre contra a mesma base da roupa

Assim, o produto evolui em direcao a mais impacto visual sem perder o que ja foi ganho em fidelidade.
