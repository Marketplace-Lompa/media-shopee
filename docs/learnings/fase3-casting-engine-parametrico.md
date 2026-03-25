# Fase 3: Casting Engine Parametrico

Data da validacao: 11 de marco de 2026

## Objetivo

Resolver a repeticao da mesma "modelo brasileira" na etapa 2 do fluxo `two-pass`, sem cair em presets fixos de pessoa.

## Abordagem

Foi criado um `casting engine` experimental para o fluxo de validacao, ainda fora do pipeline de producao.

Arquivos principais:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/casting_engine.py`
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/two_pass_flow.py`
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/scripts/backend/validation/casting_engine_validation.py`

## Como o engine funciona

O engine nao escolhe "uma modelo fixa". Ele escolhe uma combinacao parametrica dentro de familias de casting:

- `br_minimal_premium`
- `br_warm_commercial`
- `br_afro_modern`
- `br_mature_elegant`
- `br_soft_editorial`

Cada familia define ranges de:

- idade visual
- tom de pele
- cabelo
- maquiagem
- expressao
- presenca comercial

O engine tambem aplica `anti-repeat` local:

- guarda memoria curta em `app/outputs/casting_engine_state.json`
- evita repetir familia recente
- evita repetir assinatura completa recente
- adiciona clausulas negativas no prompt para nao parecer com outputs recentes

## Receita validada

1. Etapa 1: gerar a melhor base fiel da peca com o subset automatico de referencias.
2. Etapa 2: escolher um perfil brasileiro via `casting engine`.
3. Compilar um prompt de edicao com:
   - locks estruturais da roupa
   - identidade parametrica da modelo
   - instrucao de diferenca em relacao aos outputs recentes
   - cena fixa
   - pose fixa
4. Editar a base usando apenas `edit_anchors` da roupa.

## Rodada validada

Relatorio:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/casting_engine_validation/20260311_192658/report.md`
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/casting_engine_validation/20260311_192658/summary.json`

Base vencedora:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/castbase_20260311_192658/gen_castbase_20260311_192658_1.png`
- `overall_score: 0.94`

Cena compartilhada:

- `refined Brazilian premium showroom with softly textured neutral walls, pale stone floor, clean daylight, and minimal decor`

Pose compartilhada:

- `Use a clean standing catalog pose with full garment visibility.`

## Resultados

### 1. BR Soft Editorial

Imagem:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/asting_20260311_192658_0/edit_asting_20260311_192658_0_1.png`

Perfil:

- idade: `late 20s`
- pele: `light olive skin`
- cabelo: `soft loose waves with a subtle side part`
- score geral: `0.92`

Leitura:

- mudou bem o rosto e a energia facial
- ainda ficou muito perto da mesma familia de cenario do restante

### 2. BR Afro Modern

Imagem:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/asting_20260311_192658_1/edit_asting_20260311_192658_1_1.png`

Perfil:

- idade: `late 20s`
- pele: `medium-deep warm skin`
- cabelo: `short sculpted natural curls with a crisp silhouette`
- score geral: `0.93`

Leitura:

- variou bem a silhueta de cabelo
- manteve fidelidade muito alta da roupa
- confirmou que o engine consegue produzir uma persona diferente sem destruir a peca

### 3. BR Mature Elegant

Imagem:

- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/asting_20260311_192658_2/edit_asting_20260311_192658_2_1.png`

Perfil:

- idade: `early 40s`
- pele: `medium olive skin`
- cabelo: `a sharp dark chin-length bob tucked behind one ear`
- score geral: `0.93`

Leitura:

- foi a melhor variacao de idade visual
- confirmou que o sistema consegue sair da mesma persona jovem/cacheada repetida
- o fundo ainda permaneceu muito parecido com as outras rodadas

## Conclusao

O `casting engine` parametricamente controlado funcionou.

O ganho real foi:

- variar melhor rosto
- variar melhor cabelo
- variar melhor faixa etaria visual
- manter a roupa estavel

O limite atual ficou claro:

- o problema de repeticao agora esta mais no `scene engine` do que no casting

## Decisao

Esta fase valida a direcao correta para o agente:

- manter `casting` como motor parametrico com anti-repeat
- nao usar presets fixos de pessoa
- separar `casting`, `scene` e `pose` em motores distintos

## Proximo passo

Implementar um `scene engine` com a mesma filosofia:

- familias de cena
- ranges internos
- anti-repeat
- compatibilidade com categoria/peca

So depois vale plugar isso no pipeline principal.
