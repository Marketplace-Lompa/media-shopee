---
name: pipeline-trace-observability
description: Rode o pipeline real com referencias visuais e observabilidade completa por etapa para inspecionar selector, triage, planner, Stage 1, Stage 2, retries e surfaces finais via report.json e scripts/diagnostics/run_pipeline_trace.py.
---

# Pipeline Trace Observability

Use esta skill quando o usuario pedir para:

- investigar inconsistencias de prompt no fluxo com upload
- comparar `mode`s no pipeline real
- entender o que o planner retornou vs o que foi para o Nano
- auditar `Stage 1`, `Stage 2`, retries e surfaces da UX
- validar se o problema nasceu no agente, na montagem do prompt ou no transporte

## Fonte de verdade

- Script oficial: `python3 scripts/diagnostics/run_pipeline_trace.py`
- Artefato principal: `app/outputs/<trace_id>/summary.json`
- Artefato por sessao: `app/outputs/v2diag_<session_id>/report.json`

Nao conclua nada olhando apenas a imagem final ou a superficie da UX. Sempre abra o `report.json`.

## Comando base

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

## Fluxo de leitura obrigatorio

1. `request`
   - confirme `prompt`, `mode`, `scene_preference`, `fidelity_mode`, `n_images`, `aspect_ratio`, `resolution`
2. `selector` e `triage`
   - veja quais referencias entraram na analise e quais foram para `edit_anchors`
   - confira `garment_hint`, `image_analysis`, `structural_contract`, `set_detection`
3. `planner`
   - leia `planner.input.instruction_prompt`
   - compare `planner.output.parsed_response_payload` com `planner.plan`
   - confirme `fallback_applied`
4. `stage1`
   - abra `stage1.orchestration.base_scene_prompt`
   - confirme `stage1.transport.generator_effective_prompt`
   - revise `stage1.selection.candidate_assessments`
   - se houver retry, leia `stage1.retry_attempts`
5. `stage2`
   - abra `stage2.prepared_prompt`
   - confira `stage2.transport.initial.executor_text_blocks`
   - leia `stage2.runs[].applied_edit_prompt`
   - se houver retry, leia `stage2.runs[].recovery.events`
6. `response_surfaces`
   - compare `optimized_prompt`, `stage1_prompt`, `edit_prompt`, `modal_prompt_surface`, `gallery_prompt_surface`

## Perguntas que a analise deve responder

Depois de cada run, responda explicitamente:

1. O que o planner recebeu?
2. O que o planner retornou?
3. Qual prompt real foi para o Nano no `Stage 1`?
4. Qual prompt real foi para o Nano no `Stage 2`?
5. Algum retry alterou o prompt?
6. O problema nasceu no agente, na montagem do prompt, no transporte ou na surface da UX?
7. Qual `mode` performou melhor para esse conjunto de referencias?

## Regras operacionais

- Use o mesmo `refs-folder` e o mesmo `prompt` ao comparar `mode`s.
- Cite sempre os caminhos absolutos do `summary.json` e dos `report.json` usados na conclusao.
- Quando houver truncagem, compare primeiro `planner.output.parsed_response_payload` com `stage1.orchestration.base_scene_prompt` e `planner.plan.stage2_scene_context`.
- Quando houver diferenca entre UX e runtime, use `response_surfaces.surface_labels` e `surface_sources` como prova.
- Nao proponha ajuste no pipeline sem antes localizar a etapa exata onde a inconsistência apareceu.

## Artefatos auxiliares uteis

- `app/outputs/v2diag_<session_id>/prompts/stage1_effective_prompt.txt`
- `app/outputs/v2diag_<session_id>/prompts/stage2_primary_prompt.txt`
- `app/outputs/v2diag_<session_id>/prompts/stage2_applied_prompt.txt`

## Referencia

- Guia operacional: `docs/diagnostics/pipeline-trace-observability.md`
