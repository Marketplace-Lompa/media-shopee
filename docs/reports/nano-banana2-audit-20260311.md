# Auditoria Nano Banana 2 (2026-03-11)

## Escopo
- Fluxo v2 de geração com referência (`reference_selector` + `pipeline_v2` + `art_direction_sampler` + `two_pass_flow` + `generator`).
- Problemas auditados: baixa criatividade de cenários/poses brasileiros e clonagem de rosto da referência.

## Achados principais
1. O stage 2 ainda recebia imagens `worn_*` em alguns cenários (especialmente peça complexa/estrita), elevando o risco de vazamento de identidade facial.
2. O seletor penalizava pouco `styling_leak_risk`, favorecendo imagens com pessoa muito dominante.
3. Catálogo de art direction era curto (4 cenas, 4 poses), causando repetição visual.
4. `scene_preference` influenciava por afinidade textual, mas sem filtro forte por indoor/outdoor no sampler.
5. Casting variava cabelo/pele/idade, mas sem eixo explícito de geometria facial.

## Aprimoramentos aplicados
- `app/backend/agent_runtime/reference_selector.py`
  - Novo score `identity_safe_score`.
  - Penalidade maior para `styling_leak_risk` e `background_noise`.
  - Novo subset `identity_safe` (prioriza detalhes + worn de baixo risco).
  - `edit_anchors` com fallback orientado a baixo leak.
  - Estatísticas de risco de cópia (`identity_reference_risk`, média/máximo de leak) para modular o guardrail.

- `app/backend/agent_runtime/pipeline_v2.py`
  - Stage 2 passa a priorizar `identity_safe` nas referências de edição.
  - Fallback de referências reforçado para evitar dependência de `worn_*` quando possível.
  - `scene_preference` e `preset` injetados no request efetivo do sampler.
  - Thinking mode por etapa: stage 1 em `MINIMAL`; stage 2 em `HIGH` (ou `MINIMAL` quando fidelidade `estrita`).
  - `reference_guard_strength` dinâmico por risco da referência + regras explícitas de não-cópia de identidade.
  - Estratégia dinâmica de pose (`controlled` | `balanced` | `dynamic`) conforme fidelidade, complexidade da peça e intenção do prompt.
  - Telemetria de observabilidade inclui `effective_art_direction_request`.

- `app/backend/agent_runtime/art_direction_sampler.py`
  - Expansão de catálogo: cenas brasileiras, poses, câmeras, luzes e styling.
  - `scene_preference` e `preset` usados como sinais de afinidade (guia contextual), não como trava rígida.
  - Afinidade textual por matching genérico de tags/tokens normalizados (sem if-else rígido por listas fixas).
  - `directive_hints` para customizar contexto sem alterar código (scene/pose/model/custom hints).
  - Novas poses dinâmicas para aumentar variação mantendo legibilidade da peça.

- `app/backend/agent_runtime/casting_engine.py`
  - Novo eixo `face_structure_options` para reforçar variação facial real.
  - `identity_sentence` passa a incluir geometria facial.

- `app/backend/agent_runtime/two_pass_flow.py`
  - Prompt de stage 2 reforçado para anti-clone e geração de identidade nova.
  - Estilo de cena ajustado para reduzir estética genérica/repetitiva.

- `app/backend/generator.py`
  - Prefixo de referência reforçado: pessoa da referência tratada como manequim anônimo e proibida replicação de identidade.
  - `REFERENCE ROLE MAP` explícito no payload multimodal para separar transferência permitida (peça) e proibida (identidade/pose/background).

## Impacto esperado
- Redução de clonagem facial em jobs com múltiplas referências.
- Maior diversidade real de cenários/poses brasileiros por lote.
- Melhor aderência de `scene_preference` (indoor/outdoor) no resultado final.
- Maior percepção de modelo "nova" entre imagens sucessivas.

## Risco residual
- Se o usuário enviar apenas fotos `worn_front` muito semelhantes e sem detalhes de peça, ainda pode haver alguma transferência de identidade.
- Para casos críticos de volume, considerar pipeline adicional com recorte automático de rosto nas referências antes do envio ao modelo.
