# Fluxo ponta a ponta — compilação de prompt final (foco: natural + fallback de casting)

**Objetivo:** garantir que a identidade física da modelo e a fidelidade da peça compitam no mesmo prompt final sem vazar rótulos internos, e sem sobrecarregar cena/câmera no modo `natural`.

## 1) Entradas da corrida

1. `edit_agent` monta o `result` base (`prompt`, `base_prompt`, `camera_and_realism`, `diversity_target`, `garment_narrative`, `mode_id`).
2. `grounding_model`/`model_grounding` alimentam estados de casting (`casting_state`) e poses (`pose_state`) quando existem referências de sessão.
3. `pipeline_mode` e `has_images` definem o contrato de compilação e se entram caminhos de “reference-mode”.

## 2) Normalização inicial de superfícies

1. Escolha de `prompt_source_raw`:
   - `pipeline_mode == text_mode` => fonte canônica é `prompt`.
   - caso contrário => `base_prompt`.
2. Chamada `_strip_reference_prompt_noise(...)`:
   - retira instruções do tipo `Replace the placeholder...`, `Do not preserve...`, `CRITICAL ...`.
3. `garment_narrative` é normalizado por `sanitize_garment_narrative(...)` e truncado por limite de palavras.

## 3) Compilação principal

1. ` _compile_prompt_v2(...)` aplica:
   - integração de `garment_narrative`, `shot_type`, `lighting_hint`, `mode_id`, `casting_state` etc;
   - definição de `base_budget` conforme `camera_and_realism`.
2. Se não for referência textual pura, compõe com câmera via `_compose_prompt_with_camera`.
3. Em `text_mode`/`reference_mode`, aplica injeções de mínimo de superfície:
   - ` _maybe_enforce_casting_surface(...)`
   - `_maybe_enforce_pose_surface(...)` (só se não houver detalhe de pose suficiente)
   - `_maybe_enforce_capture_surface(...)` (não natural/editorial)
   - `_maybe_enforce_coordination_bridge(...)`
   - `_maybe_enforce_text_mode_footwear(...)`
   - refinadores de `catalog_*` (apenas nos modos comerciais)
4. Dedupe leve de sentenças antes do estágio final.

## 4) _finalize_nano_output (camada final aplicada a todo fluxo)

Em `finalize_prompt_agent_result`, ao final da montagem, executa:

```text
final_prompt
  ├─ _strip_internal_labels
  ├─ se mode_id == "natural":
  │    ├─ _strip_terminal_scene_residue
  │    ├─ _dedupe_scene_surface
  │    ├─ _limit_natural_environment_surface
  │    ├─ _soften_natural_expression_surface
  │    └─ _normalize_garment_surface_with_provenance
  └─ _sanitize_prompt_for_nano
       └─ _dedupe_surface_sentences (quando não reference_mode)
```

### Regras críticas do finalizer em natural

- remover resíduos de cena no final (“quiet residential lobby”, “residential lobby” isolado etc.);
- deduplicar superfície de ambiente quando repetir cena;
- limitar 1 pista de cada: ambiente, material, luz;
- neutralizar expressão comercial explícita (smile/closed-mouth/friendly) para tom mais encontrado;
- normalizar adjetivos de roupa sem perder assinatura de padrão:
  - preserva se houver sinais de padrão (`3d`, `diagonal`, `chevron`, `geometric`, `relief`, ...).

## 5) Proteções de observabilidade

- `prompt_compiler_debug["nano_output_rules"]` armazena:
  - `applied`: regras que tocaram o texto
  - `skipped`: regras não aplicadas
- `used_clauses` registra o “nano_finalize”.
- O texto final entra em `result["prompt"]` e `result["base_prompt"]` (em `text_mode`).

## 6) Pontos já validados por teste

- `CASTING CHECKLIST`/`CASTING_DIRECTION` e demais labels internos não aparecem no prompt final.
- Resíduos de cena repetida/sobrando no fim são limpos.
- Expressão comercial é suavizada no modo natural.
- A assinatura de padrão da roupa é mantida, mas termos genéricos (`fitted`, `warm beige`) são removidos quando não suportados por referência.

## 7) Pontos abertos para próxima etapa (próxima tarefa recomendada)

1. Inserir logging dedicado de retorno bruto do Gemini antes e depois do `prompt_result` (sem alterar generator ainda).
2. Rodar lote de resposta do Gemini para cenários com `natural` + `reference_mode` e medir:
   - 0 vazamento de labels internos,
   - consistência de 3–5 atributos de casting,
   - repetição de rosto reduzida (dispersão entre seeds).
3. Congelar um checklist de aprovação no PR: se qualquer regra essencial de roupa cair do contrato, abortar rollout.

