# Validacao Prompt-Only de Linguagem Marketplace

Data: 2026-03-11

## Objetivo

Testar se o fluxo atual consegue aproximar a imagem final da linguagem de anuncios vencedores de marketplace no Brasil usando apenas prompt, sem referencias extras de pesquisa visual.

Hipotese:

- talvez o Nano 2 ja tenha repertorio suficiente para responder a descricoes como:
  - `top-performing Mercado Livre Brasil fashion listing`
  - `top-performing Shopee Brasil fashion listing`
  - `high-performing SHEIN Brasil knitwear product photo`

## Setup

Base fiel usada:

- `app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_2.png`

Anchors da roupa:

- `docs/roupa-referencia-teste/referencia.jpeg`
- `docs/roupa-referencia-teste/referencia2.jpeg`

Nao foram usadas refs extras de modelo, pose ou cenario.

Ou seja:

- mesma base
- mesmas refs de roupa
- unica variavel = prompt de etapa 2

## Rodada

Run dir:

- `docs/prompt_only_marketplace_validation/20260311_190045`

Resumo:

- `docs/prompt_only_marketplace_validation/20260311_190045/summary.json`

## Variantes

### Mercado Livre

Arquivo:

- `app/outputs/0311_190045mercado_livre/edit_0311_190045mercado_livre_1.png`

Direcao:

- frontal
- indoor neutro
- foco em clareza comercial e conversao

Scores:

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.95`
- `construction_fidelity`: `0.95`
- `environment_change_strength`: `0.80`
- `overall_score`: `0.93`

Leitura:

- bom resultado
- muito limpo
- forte leitura de produto
- mais util para baseline de e-commerce puro

### Shopee

Arquivo:

- `app/outputs/mkt20260311_190045shopee/edit_mkt20260311_190045shopee_1.png`

Direcao:

- 3/4 leve
- indoor mais convidativo
- tom mais caloroso e amigavel
- forte apelo visual para mobile

Scores:

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.98`
- `construction_fidelity`: `0.98`
- `environment_change_strength`: `0.90`
- `overall_score`: `0.96`

Leitura:

- melhor resultado da rodada
- boa energia comercial
- imagem mais "clicavel"
- continua legivel para catalogo

### SHEIN

Arquivo:

- `app/outputs/rmkt20260311_190045shein/edit_rmkt20260311_190045shein_1.png`

Direcao:

- 3/4 leve
- indoor minimalista
- linguagem um pouco mais fashion-forward

Scores:

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.90`
- `construction_fidelity`: `0.90`
- `environment_change_strength`: `0.80`
- `overall_score`: `0.93`

Leitura:

- bom polimento
- menos diferenciado que Shopee
- acabou ficando mais proximo de um catalogo clean generico

## Conclusao

O teste validou que:

- sim, o prompt sozinho ja consegue empurrar bem a linguagem visual
- o modelo responde a descricoes de marketplace Brasil sem precisar obrigatoriamente de pesquisa visual

Mas tambem mostrou um limite:

- sem refs extras, o resultado tende a ficar mais generico
- o prompt muda o tom, mas nem sempre muda fortemente a identidade do cenario

Leitura final:

- `Mercado Livre` virou um baseline mais seco e conversion-focused
- `Shopee` foi o melhor equilibrio entre impacto e legibilidade
- `SHEIN` ficou bom, mas menos caracteristico

## Implicacao para produto

Prompt-only funciona como:

- baseline barato
- fallback rapido
- modo inicial para casos sem pesquisa ou sem intake por URL

Mas nao deve ser a unica estrategia para o produto premium.

O caminho mais forte continua sendo:

1. estabilizar a roupa
2. usar prompt bom como base
3. quando necessario, reforcar etapa 2 com refs de pesquisa ou refs reais do anuncio
