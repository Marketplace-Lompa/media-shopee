# Fase 4: Art Direction Sampler Enxuto

Data da validacao: 11 de marco de 2026

## Objetivo

Testar uma forma enxuta de parametrizar a etapa 2 sem cair em overengineering.

A decisao foi manter:

- stage 1 congelado para fidelidade da peca
- stage 2 controlado por um unico sampler pequeno

Em vez de criar varios motores separados de imediato, foi criado um `art_direction_sampler` que junta:

- casting
- scene
- pose
- camera
- lighting
- styling

## Implementacao

Arquivos:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/art_direction_sampler.py`
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/two_pass_flow.py`
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/scripts/backend/validation/art_direction_validation.py`

O sampler retorna um objeto pequeno, pronto para o prompt da etapa 2:

```json
{
  "casting_family": "...",
  "scene_family": "...",
  "pose_family": "...",
  "camera_profile": "...",
  "lighting_profile": "...",
  "styling_profile": "..."
}
```

## Setup de validacao

Base fiel usada:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/castbase_20260311_192658/gen_castbase_20260311_192658_1.png`

Anchors da roupa:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/roupa-referencia-teste/referencia.jpeg`
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/roupa-referencia-teste/referencia2.jpeg`

Run rapido salvo em:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/art_direction_validation_fast/20260311_195714/summary.json`

## Variantes

### Art 1

Imagem:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/artdir_20260311_195714_0/edit_artdir_20260311_195714_0_1.png`

Combinacao:

- casting: `br_minimal_premium`
- scene: `br_curitiba_cafe`
- pose: `paused_mid_step`
- camera: `fujifilm_candid`
- lighting: `overcast_cafe`
- styling: `soft_blue_trousers`

Scores:

- `overall_score: 0.93`
- `garment_fidelity: 0.90`
- `model_change_strength: 1.00`
- `environment_change_strength: 1.00`

Leitura:

- melhor equilibrio geral da rodada
- cenario ficou realmente diferente
- cara forte de marketplace lifestyle brasileiro

### Art 2

Imagem:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/artdir_20260311_195714_1/edit_artdir_20260311_195714_1_1.png`

Combinacao:

- casting: `br_mature_elegant`
- scene: `br_recife_balcony`
- pose: `standing_3q_relaxed`
- camera: `canon_balanced`
- lighting: `coastal_late_morning`
- styling: `off_white_shorts`

Scores:

- `overall_score: 0.92`
- `garment_fidelity: 0.90`
- `model_change_strength: 1.00`
- `environment_change_strength: 1.00`

Leitura:

- muito boa troca de persona
- varanda brasileira convincente
- forte cara de anuncio real

### Art 3

Imagem:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/artdir_20260311_195714_2/edit_artdir_20260311_195714_2_1.png`

Combinacao:

- casting: `br_soft_editorial`
- scene: `br_recife_balcony`
- pose: `front_relaxed_hold`
- camera: `phone_clean`
- lighting: `coastal_late_morning`
- styling: `off_white_shorts`

Scores:

- `overall_score: 0.92`
- `garment_fidelity: 0.95`
- `model_change_strength: 0.80`
- `environment_change_strength: 1.00`

Leitura:

- melhor preservacao da roupa
- menor variacao de persona
- caiu na mesma familia de varanda da variante anterior

## Conclusao

O sampler unico e enxuto funcionou.

Ganhos:

- controlou melhor o equilibrio entre fidelidade e direcao de arte
- permitiu variar mais do que o prompt solto
- manteve o fluxo simples: selector -> base fiel -> art direction sampler -> edit

Limite atual:

- o anti-repeat de cena ainda nao esta forte o suficiente
- duas variantes ainda cairam na mesma familia de varanda

## Decisao

Essa arquitetura e melhor do que separar tudo agora em varios subsistemas pesados.

O caminho recomendado e:

- manter o `art_direction_sampler` como unico orquestrador da etapa 2
- fortalecer apenas o anti-repeat de cena
- continuar stage 1 congelado

Nao ha necessidade de reintroduzir grounding, rerank complexo ou multiplos loops neste momento.
