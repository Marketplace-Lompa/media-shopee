# Fase 1 - Selector Automatico de Referencias

Data: 2026-03-11

## Objetivo

Automatizar o primeiro passo que vinha sendo feito manualmente nos testes:

- escolher as melhores imagens de referencia para o Nano

Sem depender ainda do ranking final do projeto em producao.

## O que foi implementado

Foi criado um pipeline separado de validacao com dois componentes:

### 1. Selector reutilizavel

Arquivo:

- `app/backend/agent_runtime/reference_selector.py`

Responsabilidades:

- deduplicar imagens por hash
- classificar cada imagem por papel visual
- pontuar cada imagem para uso como referencia do Nano
- selecionar subsets diferentes conforme o objetivo

Papeis visuais usados:

- `worn_front`
- `worn_three_quarter`
- `worn_side`
- `detail_flat`
- `detail_texture`
- `detail_construction`
- `close_crop`
- `noisy_other`

Subsets produzidos:

- `base_generation`
- `strict_single_pass`
- `edit_anchors`

### 2. Harness de validacao

Arquivo:

- `app/backend/reference_selector_validation.py`

Responsabilidades:

- carregar uma pasta de referencias
- rodar o selector automatico
- montar o prompt estrito
- gerar uma prova com o subset escolhido
- avaliar a imagem final
- gravar relatorio em disco

## Politica inicial de selecao

### Regra de flexibilidade por quantidade

- `1` imagem: usar a propria imagem em todos os subconjuntos
- `2` imagens: usar as duas imagens; nao faz sentido descartar agressivamente
- `3+` imagens: ativar a analise completa por papel visual e subset selection

Objetivo:

- manter eficiencia e simplicidade quando a cardinalidade e baixa
- usar inteligencia de selecao apenas quando ela realmente agrega

---

### `base_generation`

Regra:

- escolher `2` vistas frontais/3-4 fortes
- escolher `1` vista diversa util (`side` ou `three_quarter`)
- completar com mais `1` imagem util

Objetivo:

- maximizar leitura de silhueta e drapeado para a etapa de geracao-base

### `strict_single_pass`

Regra:

- escolher `1` frontal forte
- escolher `1` vista diversa util
- adicionar `1` ou `2` refs de detalhe

Objetivo:

- maximizar fidelidade em single-pass curto

### `edit_anchors`

Regra:

- escolher as `2` melhores refs de detalhe

Objetivo:

- travar textura, construcao e padrao na etapa de edicao

## Validacao no caso real

Comando usado:

```bash
PYTHONPATH=app/backend app/.venv/bin/python app/backend/reference_selector_validation.py --folder docs/roupa-referencia-teste
```

Relatorio gerado:

- `docs/reference_selector_validation/20260311_175602/report.md`
- `docs/reference_selector_validation/20260311_175602/summary.json`

## Resultado do selector automatico

### `base_generation`

- `IMG_3323.jpg`
- `IMG_3329.jpg`
- `IMG_3324.jpg`
- `IMG_3328.jpg`

### `strict_single_pass`

- `IMG_3323.jpg`
- `IMG_3324.jpg`
- `referencia.jpeg`
- `referencia2.jpeg`

### `edit_anchors`

- `referencia.jpeg`
- `referencia2.jpeg`

## Prova de geracao

Imagem gerada:

- `app/outputs/refsel_20260311_175602/gen_refsel_20260311_175602_1.png`

Scores:

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.92`
- `construction_fidelity`: `0.95`
- `commercial_quality_score`: `0.96`
- `overall_score`: `0.95`

Leitura:

- o selector automatico nao reproduziu exatamente o mesmo subset manual
- mas chegou em um subset plausivel e de alta performance
- a prova automatica bateu o patamar dos melhores testes manuais

## Conclusao

A fase 1 foi validada.

Ja existe um caminho automatico separado capaz de:

- analisar as referencias
- escolher subsets por funcao
- entregar uma prova forte de performance para o Nano

Isso nao encerra a calibracao fina do selector, mas ja reduz de forma concreta a dependencia da selecao manual.

## Proximo passo natural

Integrar esse selector ao fluxo experimental `two-pass`:

1. `base_generation` para gerar a base fiel
2. `edit_anchors` para travar a roupa na etapa de edicao
