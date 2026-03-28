# Plano de Implementação: Limpeza da Arquitetura Soul-First

Este plano visa remover as inconsistências e dívidas técnicas deixadas pela transição para a nova arquitetura modular ("O Túnel").

## Fase 1: Desinchar o Roteador (`routers/generate.py`)
**Objetivo:** Transmitir toda a responsabilidade de orquestração para o `generation_flow.py`, tornando o roteador uma camada delgada (Thin Layer).

1. **Remover a Função Legada:** Deletar completamente a monstruosa função `_run_generate_pipeline` (~480 linhas) que orquestra manualmente o fluxo antigo.
2. **Remover Bifurcação (`use_v2`):** Erradicar a checagem `if use_v2:` e a função `should_use_generation_flow`. Transformar TODAS as rotas (`/` e `/async`) para que despachem os dados invariavelmente para a ponte `_run_v2_pipeline_and_persist`, delegando 100% da inteligência para o `generation_flow.py`.

## Fase 2: Poda dos Fantasmas (Engines Legadas)
**Objetivo:** A arquitetura nova governa a cena e a pose via *Souls semânticas* contidas em `modes.py`. Logo, motores antigos não devem mais existir.

1. **Deleção Física:** 
   - Excluir `agent_runtime/scene_engine.py`.
   - Excluir `agent_runtime/pose_engine.py`.
2. **Desintegração do Builder:**
   - Modificar ou excluir iterativamente `agent_runtime/target_builder.py`.
   - Transferir responsabilidades remanescentes úteis para módulos puramente dependentes da `mode_identity_soul.py` / `model_soul.py`.

## Fase 3: Desintoxicação do Cérebro (`agent.py`)
**Objetivo:** Limpar os rastros do `target_builder.py` e da arquitetura antiga dentro do próprio Cérebro.

1. **Remoção de Imports:** Cortar as ligações de imports como `_sample_diversity_target` ou `build_mode_diversity_target` originadas do `target_builder`.
2. **Refatoração do Setup:** Reorganizar a construção da variável `diversity_target` para que ela seja montada dinamicamente via `modes.py` ou `model_soul.py`.

---

**Critérios de Êxito (DoD):**
* As rotas da API funcionam estritamente usando o "Túnel" (`generation_flow.py`).
* O projeto roda sem dar `ModuleNotFoundError` pelas engines excluídas.
* Menos complexidade ciclomática na orquestração principal.
