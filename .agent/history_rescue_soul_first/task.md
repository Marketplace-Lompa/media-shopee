# Tasks: Limpeza da Arquitetura Soul-First

- [/] Deletar módulos iterados legado (`scene_engine.py`, `pose_engine.py`)
- [ ] Refatorar o roteador gigante `routers/generate.py`
  - [ ] Remover `_run_generate_pipeline`
  - [ ] Adaptar `/generate` e `/generate/async` para usar apenas `generation_flow`
- [ ] Refatorar `agent_runtime/target_builder.py` 
  - [ ] Remover dependências do `scene_engine` e `pose_engine`
  - [ ] Refatorar a construção dos targets
- [ ] Refatorar o Cérebro `agent.py`
  - [ ] Substituir inputs arcaicos do `target_builder` por integrações limpas via `modes.py` e `model_soul.py`
- [ ] Verificar integridade (`ModuleNotFoundError`) do projeto
