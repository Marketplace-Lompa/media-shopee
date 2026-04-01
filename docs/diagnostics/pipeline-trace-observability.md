# Pipeline Trace Observability

## Objetivo

Padronizar como qualquer agente deste workspace deve investigar o pipeline V2 com upload de referencias, sem depender de leitura indireta da UX ou de inferencias a partir da imagem final.

A fonte de verdade da investigacao e:

- o runner `scripts/diagnostics/run_pipeline_trace.py`
- o `summary.json` da trace
- o `report.json` de cada sessao `v2diag_<session_id>`

## Quando usar

Use este fluxo quando houver:

- prompt estranho no modal ou na galeria
- diferenca entre o que o planner parece decidir e o que a imagem final mostra
- suspeita de truncagem, duplicidade ou perda de contexto entre `planner`, `Stage 1` e `Stage 2`
- comparacao entre `catalog_clean`, `natural`, `lifestyle` e `editorial_commercial`
- necessidade de saber se a falha nasceu no agente, na montagem do prompt, no transporte ou na surface da UX

## Runner oficial

```bash
python3 scripts/diagnostics/run_pipeline_trace.py \
  --refs-folder <pasta-das-referencias> \
  --prompt "<prompt opcional>" \
  --mode catalog_clean \
  --mode natural \
  --scene-preference auto_br \
  --fidelity-mode balanceada \
  --n-images 1 \
  --aspect-ratio 4:5 \
  --resolution 1K \
  --repeat 1
```

### Parametros principais

- `--refs-folder`: pasta com as referencias visuais reais do produto
- `--prompt`: prompt do usuario que sera mantido fixo entre os `mode`s
- `--mode`: repetivel; rode o mesmo bundle com dois ou mais `mode`s
- `--repeat`: permite repeticoes do mesmo `mode`
- `--scene-preference`, `--fidelity-mode`, `--n-images`, `--aspect-ratio`, `--resolution`: devem permanecer identicos quando o objetivo for comparacao

## Artefatos gerados

### Trace

Em `app/outputs/trace_<id>/`:

- `summary.json`
- `summary.md`

### Sessao

Em `app/outputs/v2diag_<session_id>/`:

- `report.json`
- `prompts/stage1_effective_prompt.txt`
- `prompts/stage2_primary_prompt.txt`
- `prompts/stage2_applied_prompt.txt`
- `inputs/` com os packs de referencia persistidos

## Ordem correta de leitura

### 1. Entrada

Abra:

- `request.inputs`
- `request.resolution`

Confirme os parametros reais da run.

### 2. Selector e triage

Abra:

- `selector.stats`
- `selector.selected_names`
- `selector.selected_counts`
- `triage.outputs`

Perguntas:

- quais imagens entraram na analise?
- quais foram para `edit_anchors`?
- a identidade estrutural da peça foi entendida corretamente?

### 3. Planner

Abra:

- `planner.input.instruction_prompt`
- `planner.output.raw_response_text` quando existir
- `planner.output.parsed_response_payload`
- `planner.output.normalized_plan`
- `planner.plan`

Perguntas:

- o agente retornou algo coerente?
- a normalizacao degradou o que o agente disse?
- houve `fallback_applied`?

### 4. Stage 1

Abra:

- `stage1.orchestration.base_scene_prompt`
- `stage1.transport.generator_effective_prompt`
- `stage1.transport.generator_text_blocks`
- `stage1.selection`

Perguntas:

- o prompt montado bate com o retorno do planner?
- o prompt real enviado ao Nano e o mesmo da orquestracao?
- a base escolhida foi a melhor candidata?

### 5. Stage 1 retry

Se existir:

- `stage1.retry_attempts`

Perguntas:

- houve patch no prompt?
- o retry mudou o resultado ou so repetiu o problema?

### 6. Stage 2

Abra:

- `stage2.prepared_prompt`
- `stage2.transport.initial`
- `stage2.transport.selected`
- `stage2.runs[]`

Perguntas:

- qual foi o prompt humano montado?
- qual foi o payload textual real enviado ao Nano?
- o `source_prompt_context` chegou inteiro ou truncado?
- o replacement respeitou as referencias e a base?

### 7. Stage 2 recovery

Se existir:

- `stage2.runs[].recovery.events`

Perguntas:

- qual patch foi aplicado?
- qual prompt mudou?
- qual tentativa venceu?

### 8. Response surfaces

Abra:

- `response_surfaces`
- `response_payload`

Perguntas:

- o que a UX esta mostrando hoje?
- isso coincide com o prompt real do pipeline?
- existe diferenca entre `optimized_prompt`, `stage1_prompt` e `edit_prompt`?

## Regra de analise

Nao conclua que o agente “retornou errado” antes de comparar:

1. `planner.output.parsed_response_payload`
2. `stage1.orchestration.base_scene_prompt`
3. `planner.plan.stage2_scene_context`
4. `stage2.transport.initial.trimmed_source_prompt_context`

Se o planner estiver limpo e a degradacao aparecer so depois, o problema e de montagem ou transporte, nao do agente.

## Formato minimo de conclusao

Ao final da investigacao, responda sempre:

1. qual bundle foi usado
2. quais `mode`s foram comparados
3. caminhos dos `report.json`
4. o que o planner retornou
5. o que foi para o Nano no `Stage 1`
6. o que foi para o Nano no `Stage 2`
7. em qual etapa a inconsistência nasceu
8. qual `mode` performou melhor

## Observacao

Esta documentacao nao substitui o script nem o `report.json`. Ela existe para padronizar o ritual de investigacao. A verdade do pipeline continua nos artefatos gerados em runtime.
