# Fase 2 - Fluxo Two-Pass Automatico com Selector

Data: 2026-03-11

## Objetivo

Transformar a receita manual que levou ao `editmix01` em um fluxo automatico de validacao, ainda isolado do pipeline de producao.

A meta desta fase foi:

1. usar o selector automatico da fase 1
2. gerar mais de uma base fiel da roupa
3. escolher automaticamente a melhor base
4. editar modelo, innerwear e ambiente sem perder a peca

## O que foi implementado

Arquivos novos:

- `app/backend/agent_runtime/two_pass_flow.py`
- `app/backend/two_pass_validation.py`

Ajuste importante:

- `app/backend/generator.py`

O `generator.py` agora detecta corretamente `image/png`, `image/jpeg` e `image/webp` nas referencias e na etapa de edicao. Isso era relevante porque a etapa 2 usa uma imagem-base gerada em `png`.

## Desenho do fluxo

### Etapa 1 - Selecao automatica de referencias

O fluxo reaproveita:

- `select_reference_subsets()`

Subsets usados:

- `base_generation`: refs para gerar a melhor base fiel
- `strict_single_pass`: refs para avaliar fidelidade da roupa
- `edit_anchors`: refs de detalhe para travar a peca na edicao

### Etapa 2 - Geração de multiplas bases

O harness roda:

- `generate_images()`
- `thinking_level=MINIMAL`
- `aspect_ratio=4:5`
- `resolution=1K`
- `n_images=2`

As 2 candidatas da etapa 1 sao avaliadas automaticamente contra o subset `strict_single_pass`.

### Etapa 3 - Escolha automatica da melhor base

A escolha da base vencedora usa:

1. `overall_score`
2. `garment_fidelity`
3. `construction_fidelity`

Ou seja:

- primeiro ganha a melhor leitura geral
- em empate, ganha a base mais fiel
- em novo empate, ganha a base com melhor construcao

### Etapa 4 - Edicao da base vencedora

O harness roda:

- `edit_image()`
- `reference_images_bytes=edit_anchors`

Prompt da edicao:

- curto
- positivo
- com locks estruturais do `structural_contract`
- focado em trocar modelo, innerwear e contexto

## Comando de validacao

```bash
PYTHONPATH=app/backend app/.venv/bin/python app/backend/two_pass_validation.py \
  --folder docs/roupa-referencia-teste
```

## Rodada validada

Run dir:

- `docs/two_pass_validation/20260311_181242`

Arquivos principais:

- `docs/two_pass_validation/20260311_181242/report.md`
- `docs/two_pass_validation/20260311_181242/summary.json`

Outputs:

- base candidata 1:
  - `app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_1.png`
- base candidata 2:
  - `app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_2.png`
- edit final:
  - `app/outputs/twopasse_20260311_181242/edit_twopasse_20260311_181242_1.png`

## Selector usado na rodada

Subsets automaticos escolhidos:

- `base_generation`
  - `IMG_3326.jpg`
  - `IMG_3323.jpg`
  - `IMG_3324.jpg`
  - `IMG_3330.jpg`
- `strict_single_pass`
  - `IMG_3326.jpg`
  - `IMG_3324.jpg`
  - `referencia.jpeg`
  - `referencia2.jpeg`
- `edit_anchors`
  - `referencia.jpeg`
  - `referencia2.jpeg`

Leitura:

- a etapa 1 escolheu `4` vistas vestindo coerentes para montar a melhor base
- a avaliacao usou `2` vistas vestindo `+ 2` detalhes
- a edicao ficou ancorada nas `2` melhores refs de detalhe

## Prompt da etapa 1

```text
Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment. Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible, clean premium indoor composition, soft natural daylight. Preserve exact garment geometry, texture continuity, and construction details. Garment identity anchor: ruana_wrap, draped silhouette, open front opening, cocoon hem behavior, cape_like sleeve architecture. Catalog-ready minimal styling with the garment as the hero piece. Keep accessories subtle and secondary to the garment. Build new styling independent from the reference person's lower-body look, footwear, and props unless explicitly requested.
```

## Prompt da etapa 2

```text
Keep the garment exactly the same: same overall garment identity, same knit or crochet texture continuity, same stitch pattern and fiber relief, same pattern placement and stripe scale if present, same open-front construction, same draped fluid silhouette, same cape-like arm coverage, same rounded cocoon hem behavior, keep the garment ending around the upper thigh relative to the model body, preserve these structural cues: continuous neckline-to-front edge, broad uninterrupted back panel, rounded cocoon side drop, arm coverage formed by draped panel. Replace the model with a clearly different adult woman with different face, skin tone, and hair. Change the inner top to a clean white crew-neck tee. Place her in a bright premium indoor catalog environment with natural window light. Use a standing pose with full garment visibility. Keep the image highly photorealistic, premium fashion catalog quality, with natural skin texture and realistic body proportions.
```

## Scores

### Base candidata 1

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.90`
- `construction_fidelity`: `0.85`
- `overall_score`: `0.92`

### Base candidata 2

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.95`
- `construction_fidelity`: `0.90`
- `overall_score`: `0.94`

Base vencedora:

- `app/outputs/twopassb_20260311_181242/gen_twopassb_20260311_181242_2.png`

### Edit final

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.95`
- `construction_fidelity`: `0.90`
- `model_change_strength`: `1.00`
- `environment_change_strength`: `0.80`
- `innerwear_change_strength`: `1.00`
- `photorealism_score`: `0.95`
- `commercial_quality_score`: `0.95`
- `overall_score`: `0.93`

## Leitura humana da rodada

A rodada automatica conseguiu reproduzir a logica que estava funcionando manualmente:

- a base vencedora preservou muito bem a ruana
- a etapa 2 trocou a modelo com clareza
- a roupa interna virou uma camiseta branca limpa
- a imagem final continuou com leitura comercial forte

Ponto importante:

- o `environment_change_strength` ficou em `0.80`, nao em `1.00`

Isso faz sentido porque o prompt da validacao pediu outro ambiente premium indoor, e nao uma mudanca radical para externo ou outro contexto visual muito distante. Ou seja:

- a mudanca de ambiente existiu
- mas continuou dentro da mesma familia visual de catalogo

## Conclusao

A fase 2 confirmou que o fluxo abaixo ja pode ser tratado como receita automatizavel:

1. selector automatico escolhe o subset
2. gerar `2` bases fiéis
3. escolher a melhor base por avaliacao
4. editar a base com `edit_anchors`

O resultado desta rodada foi a primeira evidencia forte de que o selector automatico da fase 1 ja esta bom o bastante para alimentar um `two-pass` reproduzivel.

## Proximo passo natural

Levar esse fluxo experimental para um orquestrador de validacao mais completo, com:

- presets de cena
- presets de pose
- opcional de `2` candidatas na etapa 2
- comparacao humana vs score automatico
