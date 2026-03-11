# Como Chegamos ao Resultado `editmix01`

Data: 2026-03-11

## Objetivo

Documentar o caminho exato que levou ao resultado:

- `app/outputs/editmix01/edit_editmix01_1.png`

Esse resultado foi importante porque ficou mais perto do objetivo real do produto:

- trocar modelo
- trocar roupa interna
- trocar ambiente
- manter alta fidelidade da peca

## Problema que precisavamos resolver

Durante os testes, apareceu um tradeoff claro:

- os melhores resultados de fidelidade da roupa ainda herdavam demais a foto original
- o melhor resultado em troca de modelo/ambiente ainda simplificava demais o cardigan/ruana

Em resumo:

- `050d2787` trocava melhor o contexto, mas perdia parte da verdade da peca
- `c3` mantinha muito melhor a peca, mas ainda lembrava demais a referencia original

Por isso, a hipotese testada foi:

- nao tentar resolver tudo em um unico passo
- primeiro travar a roupa
- depois editar apenas identidade e contexto

## Resultado final escolhido

Arquivo final:

- `app/outputs/editmix01/edit_editmix01_1.png`

Imagem-base usada para a edicao:

- `app/outputs/matrix_20260311_170921_3/gen_matrix_20260311_170921_3_1.png`

## Linha do tempo

### Etapa 1 - Encontrar uma imagem-base com roupa muito fiel

Entre os resultados da bateria curta, a melhor base para edicao foi:

- `app/outputs/matrix_20260311_170921_3/gen_matrix_20260311_170921_3_1.png`

Ela foi escolhida porque:

- manteve muito bem a leitura de ruana/wrap
- preservou o volume cocoon
- preservou melhor o padrao de listras
- preservou melhor o caimento lateral

Refs usadas nessa geracao-base:

- `docs/roupa-referencia-teste/IMG_3324.jpg`
- `docs/roupa-referencia-teste/IMG_3326.jpg`
- `docs/roupa-referencia-teste/IMG_3327.jpg`
- `docs/roupa-referencia-teste/IMG_3323.jpg`

Configuracao da geracao-base:

- modelo: `gemini-3.1-flash-image-preview`
- funcao: `generate_images()`
- `thinking_level`: `MINIMAL`
- `aspect_ratio`: `4:5`
- `resolution`: `1K`
- `n_images`: `1`

Prompt da geracao-base:

```text
Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment. Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible, clean premium indoor composition, soft natural daylight. Preserve exact garment geometry, drape, sleeve architecture, hem behavior, stripe scale, and stitch pattern. Garment identity anchor: ruana_wrap, draped silhouette, open front opening, cocoon hem behavior, cape_like sleeve architecture. Catalog-ready minimal styling with the garment as the hero piece. Keep accessories subtle and secondary to the garment. Build new styling independent from the reference person's lower-body look, footwear, and props unless explicitly requested.
```

`structural_hint` usado na chamada:

```text
ruana_wrap, draped silhouette, cape_like sleeve architecture, cocoon hem
```

## Etapa 2 - Testar se dava para resolver em single-pass

Antes de editar a imagem-base, foi testado um caminho de geracao unica:

- `app/outputs/anonmix01/gen_anonmix01_1.png`

Ideia:

- usar 2 fotos vestindo com desidentificacao leve de rosto
- combinar com 2 refs de detalhe da peca
- manter prompt curto

Refs usadas:

- `docs/roupa-referencia-teste/IMG_3324.jpg` com blur leve no topo
- `docs/roupa-referencia-teste/IMG_3326.jpg` com blur leve no topo
- `docs/roupa-referencia-teste/referencia.jpeg`
- `docs/roupa-referencia-teste/referencia2.jpeg`

Conclusao:

- nao foi suficiente
- ainda ficou proximo demais da linguagem da referencia
- nao resolveu a troca de roupa interna do jeito necessario

Esse teste foi importante porque mostrou que o problema nao era apenas "melhorar prompt".

## Etapa 3 - Editar a melhor imagem fiel

Depois disso, foi feito o teste decisivo:

- pegar uma imagem muito fiel da roupa
- rodar uma segunda etapa de edicao para trocar apenas:
  - modelo
  - roupa interna
  - ambiente

Arquivo de entrada:

- `app/outputs/matrix_20260311_170921_3/gen_matrix_20260311_170921_3_1.png`

Refs extras passadas na edicao:

- `docs/roupa-referencia-teste/referencia.jpeg`
- `docs/roupa-referencia-teste/referencia2.jpeg`

Configuracao da edicao:

- modelo: `gemini-3.1-flash-image-preview`
- funcao: `edit_image()`
- `aspect_ratio`: `4:5`
- `resolution`: `1K`
- `session_id`: `editmix01`

Prompt exato da edicao:

```text
Keep the garment exactly the same: same crochet knit texture, same olive and beige stripe pattern, same open-front ruana construction, same draped cocoon silhouette, same hem behavior. Replace the model with a clearly different adult woman with different face, skin tone, and hair. Change the inner top to a clean white crew-neck tee. Place her in a bright premium indoor catalog environment with natural window light. Keep full garment visible, highly photorealistic, premium fashion catalog quality.
```

## Por que esse caminho funcionou melhor

Porque cada passo resolveu uma coisa diferente:

- a geracao-base resolveu a fidelidade estrutural da roupa
- a edicao resolveu a troca de identidade e de ambiente

No single-pass, o modelo precisava decidir tudo ao mesmo tempo:

- quem e a nova modelo
- qual e o novo ambiente
- qual e a nova roupa interna
- como preservar a roupa principal

No two-pass, isso ficou separado:

1. primeiro a roupa foi estabilizada
2. depois a identidade e o contexto foram reescritos

## Comparacao direta

### `050d2787`

Arquivo:

- `app/outputs/050d2787/gen_050d2787_1.png`

Acertou:

- troca de modelo
- troca de ambiente
- imagem comercial forte

Errou:

- perdeu parte da verdade estrutural da peca
- simplificou demais o comportamento do cardigan/ruana

### `c3`

Arquivo:

- `app/outputs/matrix_20260311_170921_3/gen_matrix_20260311_170921_3_1.png`

Acertou:

- fidelidade muito forte da roupa

Errou:

- ainda parecia proximo demais da referencia original

### `editmix01`

Arquivo:

- `app/outputs/editmix01/edit_editmix01_1.png`

Acertou:

- manteve melhor a roupa do que `050d2787`
- trocou melhor modelo, innerwear e ambiente do que `c3`

Leitura final:

- ainda nao e a solucao final do produto
- mas foi a melhor aproximacao pratica do "melhor dos dois mundos"

## Receita reproducivel

Se quisermos repetir essa logica em outro caso parecido, a sequencia recomendada e:

1. Curar um subconjunto curto de refs para gerar a roupa com alta fidelidade.
2. Escolher a melhor imagem-base pelo olhar humano.
3. Rodar uma segunda etapa de `edit_image()`.
4. Na edicao, travar explicitamente:
   - textura
   - padrao
   - construcao
   - silhueta
   - hem behavior
5. Pedir separadamente a troca de:
   - modelo
   - roupa interna
   - ambiente
6. Passar refs de detalhe da peca na etapa de edicao.

## Conclusao

O resultado `editmix01` nao veio de um prompt unico "perfeito".

Veio de uma decisao de pipeline:

- `gerar fiel` primeiro
- `editar identidade/contexto` depois

Essa foi a primeira evidencia forte de que o produto real provavelmente deve seguir uma arquitetura `two-pass`, e nao apenas uma chamada unica de geracao.
