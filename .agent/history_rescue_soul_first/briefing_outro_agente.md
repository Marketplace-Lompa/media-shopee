# Briefing Técnico: Consolidação Soul-First do `catalog_clean`

> Este documento foi gerado pelo agente de auditoria arquitetural após mapear exaustivamente o pipeline Soul-First do MEDIA-SHOPEE. O objetivo é dar ao agente executor uma base factual verificada contra o código real.

---

## 1. Raio-X da Arquitetura Atual

### Fluxo SEM imagem (text-only)

```
mode → souls → briefings → agente (Gemini Flash) → compiler → generate_images (Nano Banana)
```

| Etapa | Módulo | Função | Linha |
|-------|--------|--------|-------|
| Resolve mode | `modes.py` | `get_mode()` | L177 |
| Monta briefing | `creative_brief_builder.py` | `build_creative_brief_for_mode()` | L50+ |
| System instruction | `prompt_context.py` | `build_system_instruction()` | — |
| Contexto textual | `prompt_context.py` | `build_generate_context_text()` | L507 |
| Prompt Agent (LLM) | `agent.py` | `run_agent()` | — |
| Compilação final | `compiler.py` | `_compile_prompt_v2()` | L129 |
| Geração | `generator.py` | `generate_images()` | — |

**O Prompt Agent (Gemini Flash) é o diretor criativo.** Ele recebe os estados latentes das engines como sementes e sintetiza um prompt coerente. O compiler pós-processa (truncagem, gaze, prosa de cenário) mas NÃO inventa.

### Fluxo COM imagem (reference mode) — COMO FUNCIONA HOJE

```
triage → curation_policy → Stage 1 (base fiel com roupa) → Stage 2 (edit criativo determinístico) → gate/repair
```

| Etapa | Módulo | Função | Linha |
|-------|--------|--------|-------|
| Triagem | `reference_selector.py` | `select_reference_subsets()` | generation_flow.py L470 |
| Guardrails | `curation_policy.py` | `derive_art_direction_selection_policy()` | generation_flow.py L511+ |
| Stage 1 prompt | `fidelity.py` | `build_stage1_prompt()` | L561 |
| Stage 1 geração | `generator.py` | `generate_images()` com referências visuais | — |
| Stage 1 gate | `fidelity_gate.py` | `pick_best_stage1_candidate()` | — |
| Stage 2 edit | `fidelity.py` | `compile_edit_prompt()` | L451 |
| Stage 2 geração | `generator.py` | `edit_image()` | generation_flow.py L973+ |
| Stage 2 gate | `fidelity_gate.py` | `evaluate_visual_fidelity()` | — |
| Recovery | `fidelity_gate.py` | `_run_stage2_recovery()` | — |

> [!IMPORTANT]
> **No fluxo com imagem, o Prompt Agent (LLM texto) NÃO roda.** O "diretor criativo" é uma montagem determinística em `compile_edit_prompt()` (fidelity.py L451), que concatena: locks + guards + pattern_lock + reference_policy + mode_guardrails + art_direction_soul + texture_clause.

---

## 2. Espinha Criativa Compartilhada

Ambos os fluxos compartilham a mesma fonte de identidade:

| Componente | Text-Only | Reference Mode |
|------------|-----------|----------------|
| `modes.py` (ModeConfig) | ✅ via `get_mode()` | ✅ via `get_mode()` |
| `creative_brief_builder.py` | ✅ → alimenta Prompt Agent | ✅ → alimenta `art_direction_soul` no edit_prompt |
| `mode_identity_soul.py` | ✅ via `prompt_context.py` | ❌ NÃO USADO — o identity vai pro context do Agent, que não roda |
| `model_soul.py` | ✅ via `prompt_context.py` | ❌ NÃO INJETADO no edit_prompt |
| Engines (5x) | ✅ via briefing → Agent | ✅ via briefing → `art_soul_briefing`, mas consumidos como resumo raso |
| `coordination_engine.py` | ✅ fusão autoral ativa | ⚠️ Existe no briefing mas subutilizada |

---

## 3. Análise de Coerência do Plano

### ✅ O que está correto e pode ser seguido

| Afirmação do plano | Verificação |
|---------------------|-------------|
| "A triagem já acontece antes de tudo em generation_flow.py (line 470)" | ✅ Confirmado — `select_reference_subsets()` L470 |
| "O corredor de transferência está claramente separado" | ✅ Confirmado — `_run_stage2_iteration()` L973 |
| "O shell de transferência está em fidelity.py (line 451)" | ✅ Confirmado — `compile_edit_prompt()` L451 |
| "O compiler injeta direção demais" | ✅ Parcialmente — ver detalhes abaixo |
| Regra "descobrir → imaginar → vestir" | ✅ Mental model coerente |
| Fluxo text-only "mode → souls → briefings → agente → compiler" | ✅ Exatamente o que existe |
| Tradução por módulo (reference_selector = "escolhe referências", etc.) | ✅ Precisa — pode ser usada como documentação |
| Separação brief vs preset na nomenclatura | ✅ Necessária e correta |

### ⚠️ Pontos que precisam de atenção

#### 3.1. A ordem dos blocos em `prompt_context.py` NÃO está tão errada quanto o plano sugere

O plano diz que a ordem está errada em `prompt_context.py (line 545)`. Na realidade, a ordem atual (L536-575) é:

```
1. MODE_BLOCK (tarefa/constraints de alto nível)
2. STRUCTURAL_CONTRACT  ← já está em segundo!
3. MODE_IDENTITY
4. SEMANTIC_BRIEFS
5. MODE_PRESETS
6. POOL_CONTEXT
7. OUTPUT_PARAMS
8. DIVERSITY_TARGET
```

O `STRUCTURAL_CONTRACT` **já está em segundo lugar**. O que pode ser questionado é `MODE_PRESETS` vindo depois de `MODE_IDENTITY` e `SEMANTIC_BRIEFS` — mas isso faz sentido se os presets são guardrails (devem ser lidos depois da direção semântica).

**Recomendação:** Antes de reordenar, executar o teste de integração (seção 5) para ver a ordem real impressa e decidir se precisa mudar.

#### 3.2. O modelo "imaginar → vestir" é REDESIGN, não reorganização

Hoje:
- **Stage 1:** Gera base **COM a roupa já vestida** (referências visuais entram na geração)
- **Stage 2:** Edita a base — substitui modelo/cenário/pose, **preservando a roupa**

O plano propõe:
- **Passo 2-3:** Agent cria imagem-base (pessoa/cenário/pose sem roupa transferida)
- **Passo 4:** Fidelity transfere a roupa para a base

**Isso inverte a lógica.** Hoje a roupa nasce na imagem desde o Stage 1. No plano, a roupa é transferida depois.

> [!WARNING]
> Se o objetivo agora é apenas **consolidar a arquitetura do catalog_clean em place** (como o plano diz na seção 8: "anti-overengineering"), a inversão Stage 1 ↔ Stage 2 NÃO deveria ser implementada neste passo. Isso é redesign futuro. O piloto deveria focar em: (a) reordenar blocos no prompt_context, (b) limpar cláusulas criativas do compiler, (c) converter estados latentes em mini-briefings semânticos.

#### 3.3. O compiler tem 4 cláusulas criativas que deveriam sair

Em `compiler.py` L129-306, quando `has_images=True`:

| Cláusula | Linha | Tipo real | Ação recomendada |
|----------|-------|-----------|------------------|
| `anti_copy_model` | L199 | Guardrail ✅ | Manter |
| `quality_model` (model_presence) | L264-270, L292 | Direção criativa ❌ | Mover para agent/briefing |
| `quality_gaze` | L272-280, L303 | Direção criativa ❌ | Mover para agent/briefing |
| `quality_scene` | L305 | Direção criativa ❌ | Mover para agent/briefing |
| `pose_body_directed` | L296-301 | Direção criativa ❌ | Mover para agent/briefing |
| `frame_occupancy` | L306 | Guardrail ✅ | Manter |
| `model_profile` | L241-243 | Guardrail de diversidade ✅ | Manter |
| `garment_fidelity_anchor` | L188-193 | Guardrail ✅ | Manter |

**Nota:** Para o `catalog_clean` especificamente, `quality_scene` já é pulada (L304: `if mode_id != "catalog_clean"`). Isso confirma que o compiler já tem exceções mode-specific.

#### 3.4. Peças faltantes no modelo proposto

O plano lista 4 semantic briefs: scene, model, pose, capture. Mas existem 6 engines:

| Engine | Status no plano | Decisão necessária |
|--------|-----------------|---------------------|
| `scene_engine` | ✅ → scene_brief | — |
| `model_soul` | ✅ → model_brief | Continua compartilhado (seção 7 do plano) |
| `pose_engine` | ✅ → pose_brief | — |
| `capture_engine` | ✅ → capture_brief | — |
| `styling_completion_engine` | ❓ Não mencionado | Absorvido por model_brief? Ou é 5º brief? |
| `coordination_engine` | ❓ Não mencionado | Continua como síntese? Ou o agent absorve? |

**Recomendação:** Não implementar sem decidir. Perguntar ao usuário.

#### 3.5. `curation_policy.py` não tem destino definido

O raio-X mostrou que `curation_policy.py` acumula policy (budgets, guard config, candidate counts) + art direction (selection policy com guardrails). O plano do catalog_clean não diz onde ele cai.

**Recomendação:** Deixar intocado no piloto.

---

## 4. Regras de Segurança para Implementação

1. **NÃO fazer o Prompt Agent rodar no fluxo com imagem agora** — isso é redesign futuro
2. **NÃO inverter Stage 1 ↔ Stage 2** — a lógica "imaginar → vestir" requer validação de qualidade no Nano Banana
3. **NÃO mexer em `curation_policy.py`** — sem destino definido no piloto
4. **NÃO generalizar para outros modes** — catalog_clean é piloto isolado
5. **NÃO mover arquivos de pasta** — consolidar lógica em place primeiro
6. **VALIDAR com o teste de integração** (seção 5) antes e depois de cada mudança

---

## 5. Teste de Integração de Referência

O comando abaixo é a régua de validação. Deve ser executado **antes** e **depois** de cada mudança para comparar output:

```bash
PYTHONPATH=/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend \
/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/.venv/bin/python - <<'PY'
from pathlib import Path
from agent import run_agent
from agent_runtime.creative_brief_builder import build_creative_brief_for_mode
from agent_runtime.modes import get_mode, describe_mode_defaults
from agent_runtime.prompt_context import build_generate_context_text

img_path = Path('/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/roupa-referencia-teste/referencia2.jpeg')
img_bytes = img_path.read_bytes()
mode = get_mode('catalog_clean')
brief = build_creative_brief_for_mode(mode, user_prompt='')

context = build_generate_context_text(
    has_images=True,
    has_prompt=False,
    uploaded_images_count=1,
    user_prompt='',
    pool_context='',
    aspect_ratio='4:5',
    resolution='1K',
    profile=brief.get('profile_hint',''),
    diversity_target=brief,
    guided_enabled=False,
    guided_brief=None,
    guided_set_mode='',
    guided_set_detection={},
    structural_contract={
        'enabled': True,
        'garment_subtype': 'ruana_wrap',
        'silhouette_volume': 'draped',
        'front_opening': 'open',
        'garment_length': 'upper_thigh',
        'must_keep': [
            'continuous neckline-to-front edge',
            'broad uninterrupted back panel',
            'horizontal stripe alignment',
        ],
    },
    look_contract=None,
    grounding_research='',
    grounding_effective=False,
    grounding_context_hint=None,
    grounding_mode='lexical',
    mode_defaults_text=describe_mode_defaults(mode),
    reference_knowledge='',
    mode_id=mode.id,
    garment_hint='',
)

# Validar ordem dos blocos
end = context.find('<DIVERSITY_TARGET>')
print('CONTEXT_ORDER_SNIPPET:\n', context[:end])

# Validar output do agent
res = run_agent(
    user_prompt='',
    uploaded_images=[img_bytes],
    pool_context='',
    aspect_ratio='4:5',
    resolution='1K',
    mode='catalog_clean',
)
print('\nSHOT_TYPE:', res.get('shot_type'))
print('\nIMAGE_ANALYSIS:\n', res.get('image_analysis'))
print('\nPROMPT_START:\n', str(res.get('prompt',''))[:2200])
print('\nUSED_CLAUSES_LAST:\n',
      res.get('prompt_compiler_debug', {}).get('used_clauses', [])[-12:])
PY
```

### O que validar no output:

| Aspecto | O que procurar |
|---------|----------------|
| **CONTEXT_ORDER_SNIPPET** | A sequência dos blocos XML deve seguir a ordem proposta |
| **SHOT_TYPE** | Deve ser `wide` para catalog_clean (full_body) |
| **IMAGE_ANALYSIS** | Deve conter a triagem visual da peça de referência |
| **PROMPT_START** | Deve refletir a identidade soul do catalog_clean |
| **USED_CLAUSES_LAST** | Revela quais cláusulas o compiler injetou — usar para confirmar remoções |

---

## 6. Estado do Repositório

- **Commit atual:** `794db19` — `refactor: remove marketplace_orchestrator e limpa arquitetura soul-first`
- **Branch:** `main`
- **Working tree:** Limpa (nada pendente)
- **Arquivos deletados neste commit:** `marketplace_orchestrator.py`, `marketplace_policy.py`, `routers/marketplace.py`, `test_marketplace_policy.py`
- **Pipeline versão:** v2
- **Geração de imagens:** Nano Banana (Gemini Imagen)
- **Prompt Agent:** Gemini Flash via `agent.py`
