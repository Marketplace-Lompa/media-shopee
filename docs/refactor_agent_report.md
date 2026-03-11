# Refatoracao agent.py — Relatorio Final (MT-R8)

**Data:** 2026-03-11
**Escopo:** Extracao de inferencia visual e diversity scheduler de `agent.py` para `agent_runtime/`

---

## 1. Antes / Depois

### agent.py

| Metrica | Antes | Depois | Delta |
|---|---|---|---|
| Linhas | 972 | 528 | -444 (-46%) |
| Funcoes | `run_agent` + 7 helpers | `run_agent` apenas | -7 funcoes |
| Imports | 40+ linhas (incluindo json, random, re, BytesIO, requests, PIL) | 25 linhas (somente dependencias do orquestrador) | -15 imports mortos |
| Responsabilidade | Orquestrador + inferencia visual + diversity + helpers | Somente orquestrador: montagem de contexto, chamada de modulos, compilacao, retorno/telemetria | Single Responsibility |

### Novos modulos criados

| Arquivo | Linhas | Conteudo |
|---|---|---|
| `agent_runtime/triage.py` | 312 | `_infer_garment_hint`, `_infer_structural_contract_from_images`, `_infer_set_pattern_from_images`, `_infer_unified_vision_triage`, `_infer_text_mode_shot` |
| `agent_runtime/diversity.py` | 100 | `_sample_diversity_target` + globals anti-repeat |

### Modulos agent_runtime/ (visao completa)

| Modulo | Linhas | Responsabilidade |
|---|---|---|
| `triage.py` | 312 | Inferencia visual (hint, structural, set, unified) |
| `constants.py` | 371 | Schemas, system instruction, reference knowledge |
| `compiler.py` | 505 | Compilador de prompt V2 (P1-P4 + word budget) |
| `structural.py` | 296 | Normalizacao + pruner + `_enum_or_default` (canonical) |
| `grounding.py` | 286 | Pesquisa de grounding (Google Search) |
| `camera.py` | 215 | Camera/realism profiles e composicao |
| `gemini_client.py` | 112 | Client SDK Gemini (structured JSON, multimodal, text+tools) |
| `parser.py` | 105 | Extracao e decode de responses Gemini |
| `diversity.py` | 100 | Latent Space Casting + scheduling |
| **Total** | **2302** | |
| **agent.py** | **528** | Orquestrador |
| **Grand Total** | **2830** | |

---

## 2. Riscos Encontrados e Correcoes

### R1: `_enum_or_default` duplicada (CORRIGIDO)

**Problema:** Funcao identica existia em `structural.py` (signature `Optional[str]`) e `triage.py` (signature `Any`).
**Correcao:** Versao canonica em `structural.py` com signature `Any` (mais flexivel). `triage.py` importa de `structural.py`.
**Risco residual:** Nenhum.

### R2: `reason_codes` ausente no grounding default (CORRIGIDO)

**Problema:** O dict `grounding_meta` default em `run_agent()` nao incluia `reason_codes: []`. Quando grounding nao era ativado, consumidores que esperavam `result["grounding"]["reason_codes"]` recebiam KeyError.
**Correcao:** Adicionado `"reason_codes": []` ao default.
**Risco residual:** Nenhum.

### R3: Codigo F1 redundante (CORRIGIDO)

**Problema:** `result["image_analysis"] = _unified_image_analysis` aparecia duas vezes — uma incondicional (linha 930) e outra condicional (linhas 939-941). A condicional era dead code.
**Correcao:** Removida a verificacao condicional redundante.
**Risco residual:** Nenhum.

### R4: Imports externos apontando para `agent` em vez de `agent_runtime` (CORRIGIDO)

**Problema:** 5 arquivos importavam funcoes movidas diretamente de `agent.py`:
- `agent_runtime/grounding.py` — `from agent import _infer_garment_hint`
- `routers/stream.py` — `from agent import _infer_unified_vision_triage`
- `routers/generate.py` — `from agent import _infer_unified_vision_triage`
- `edit_agent.py` — `from agent import REFERENCE_KNOWLEDGE`
- `test_profile_injection.py` — `from agent import _sample_diversity_target`

**Correcao:** Todos atualizados para importar de `agent_runtime.triage`, `agent_runtime.constants`, ou `agent_runtime.diversity`.
**Risco residual:** Nenhum.

### R5: Imports mortos em agent.py (CORRIGIDO)

**Problema:** `import re` e `import random` permaneciam em agent.py apos a extracao, mas nenhuma funcao em `run_agent()` os utiliza.
**Correcao:** Removidos.
**Risco residual:** Nenhum.

### R6: `has_pockets` perdido no fallback individual (CORRIGIDO)

**Problema:** `_infer_structural_contract_from_images()` duplicava ~70 linhas de validacao manual que `_normalize_structural_contract()` ja fazia — incluindo `has_pockets`. No caminho da triagem unificada, `has_pockets` era preservado; no fallback individual (quando a unificada falhava), o campo sumia.
**Correcao:** Substituida a validacao manual por `_normalize_structural_contract(parsed)` — single source of truth. Fallback agora retorna `_normalize_structural_contract({})` em vez de dict hardcoded incompleto.
**Beneficio colateral:** `triage.py` caiu de 385 para 312 linhas (-73 linhas de logica duplicada removidas).
**Risco residual:** Nenhum.

### R7: TESTE 3 com path hardcoded inexistente (CORRIGIDO)

**Problema:** `test_profile_injection.py` TESTE 3 dependia de `outputs/e58c3eae/ref_*.jpg` — path instavel que nao existe na maioria dos ambientes. O teste era sempre pulado, dando falsa seguranca sobre `run_agent()` com imagens.
**Correcao:** Path alterado para `app/tests/output/poncho-teste/IMG_*.jpg` — fixture estavel com imagens reais de ruana/poncho crochet (~3-5 MB cada).
**Evidencia:** TESTE 3 agora roda e valida: unified triage (ruana_wrap conf=0.95), `features blend` no prompt, `model_profile` nas clausulas, `no_pockets` aplicado, `camera_and_realism` limpo.
**Risco residual:** Nenhum.

---

## 3. Smoke Tests — Evidencias

### compileall

```
$ python3 -m compileall app/backend -q
(sem erros)
```

### test_profile_injection.py (3 testes)

```
TESTE 1: _sample_diversity_target() compacto     ✅ (6/6 profiles, max 15w)
TESTE 2: _compile_prompt_v2() injeta model_profile ✅ (5 clausulas, features blend OK)
TESTE 3: run_agent() com imagem real               ✅ (ruana_wrap, features blend, no_pockets, camera limpo)
```

### SMOKE 1: Referencia sem prompt (MODE 2)

```
pipeline_mode:    reference_mode
shot_type:        wide
thinking_level:   HIGH
realism_level:    2
camera_profile:   catalog_natural
prompt:           1051 chars (152 words)
structural:       enabled=True subtype=ruana_wrap sleeve=cape_like/elbow conf=0.95
image_analysis:   "A woman is wearing a striped, open-front crochet wrap..."
grounding:        mode=off engine=none effective=False reason_codes=[]
compiler_debug:   final_words=152 base_budget=143 camera_words=22
```

**Resultado:** Contrato completo. Triagem unificada funcionando. Structural contract com `has_pockets` presente.

### SMOKE 2: Prompt textual sem referencia (MODE 1)

```
pipeline_mode:    text_mode
shot_type:        wide
thinking_level:   MINIMAL
realism_level:    2
camera_profile:   catalog_clean
prompt:           1225 chars (185 words)
structural:       disabled (sem imagens)
grounding:        mode=off engine=none effective=False reason_codes=[]
compiler_debug:   final_words=185 base_budget=195 camera_words=25
```

**Resultado:** Contrato completo. Diversity target com name blends funcionando.

### Validacao de contrato (ambos os smokes)

Campos obrigatorios verificados:
- [x] `prompt` (string, >30 chars)
- [x] `base_prompt` (string, >20 chars)
- [x] `camera_and_realism` (string, >10 chars)
- [x] `grounding` (dict com `effective`, `mode`, `engine`, `reason_codes`)
- [x] `pipeline_mode`
- [x] `shot_type`
- [x] `thinking_level`
- [x] `realism_level`
- [x] `structural_contract`
- [x] `diversity_target`
- [x] `prompt_compiler_debug` (com `final_words`)

---

## 4. O que NAO mudou

- `run_agent()` signature — preservada (inclusive `unified_vision_triage_result`)
- `scenarios` list em diversity.py — preservada
- Anti-repeat rotation logic — preservada
- Return type `dict` — preservado
- Call sites em routers (`run_agent`, `normalize_prompt_text`) — sem alteracao
- `_compile_prompt_v2` — sem alteracao
- Generator / image pipeline — sem alteracao

---

## 5. Pendencias

| Item | Status | Risco |
|---|---|---|
| Grounding com `use_grounding=True` nao testado neste smoke (depende de API Google Search) | Aceitavel | Baixo — logica de grounding nao foi alterada, so o import de `_infer_garment_hint` |
| MODE 3 (sem prompt, sem imagens) nao testado | Aceitavel | Baixo — path trivial, sem inferencia visual |
| Guided mode nao testado neste smoke | Aceitavel | Baixo — guided_brief path nao foi alterado |

---

## 6. Conclusao

A refatoracao reduziu `agent.py` de 972 para 528 linhas (-46%) sem regressao de contrato. Todas as funcoes extraidas vivem em modulos coesos (`triage.py`, `diversity.py`) com zero duplicacao de codigo. 7 riscos encontrados durante a extracao e review foram corrigidos — incluindo `has_pockets` perdido no fallback e o TESTE 3 que estava permanentemente pulado. O teste de integracao agora cobre o fluxo real de `run_agent()` com imagens.
