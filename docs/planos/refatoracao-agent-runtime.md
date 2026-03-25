# Plano de Refatoração do `agent.py` (Aprimorado, Incremental e Seguro)

## 1. Diagnóstico de Risco no Plano Anterior
O diagnóstico de “arquivo monolítico” está correto, mas o plano anterior tinha riscos de execução:

1. Migração ampla demais (quase “big-bang”).
2. Proposta de diretório `app/backend/agent/` pode conflitar com o módulo atual `app/backend/agent.py` no import path.
3. Não definia gates claros de regressão por fase.
4. Não separava refatoração estrutural de mudanças comportamentais (alto risco de alterar qualidade sem perceber).

Conclusão: refatorar sim, mas em fases pequenas, com compatibilidade e rollback simples.

---

## 2. Objetivo da Refatoração
Reduzir complexidade e custo de manutenção de `app/backend/agent.py` sem perder:

1. Fidelidade da peça.
2. Flexibilidade de modelo/cenário/pose.
3. Realismo fotográfico.
4. Robustez de grounding.

**Regra operacional:** nesta frente, mudar estrutura primeiro; comportamento só quando explicitamente previsto.

---

## 3. Arquitetura-Alvo (Sem Conflito de Import)
Manter `app/backend/agent.py` como fachada estável (assinatura de `run_agent` intacta) e extrair para um pacote com nome sem conflito:

```text
app/backend/
├── agent.py                          # fachada/orquestração (mantém API atual)
└── agent_runtime/
    ├── constants.py                  # schemas, pools, keywords, templates
    ├── parser.py                     # _extract_response_text, _decode_agent_response, json helpers
    ├── compiler.py                   # _compile_prompt_v2 e helpers de budget/composição
    ├── structural.py                 # normalize/prune/resolve structural conflicts
    ├── camera.py                     # seleção/normalização de camera_and_realism
    ├── diversity.py                  # _sample_diversity_target
    ├── grounding.py                  # _run_grounding_research + helpers de busca/formatação
    ├── visual_refs.py                # coleta/download de imagens web/playwright/html
    └── gemini_client.py              # wrappers de chamadas Gemini (typed I/O)
```

---

## 4. Estratégia de Execução (Fases)

### Fase 0 — Baseline e segurança
1. Congelar baseline com smoke de fluxo:
   - `run_agent` com referência + sem prompt.
   - `run_agent` com prompt textual.
   - grounding `auto/on/off`.
2. Registrar baseline mínimo:
   - tempo médio do `run_agent`.
   - tamanho médio do prompt final.
   - campos críticos no retorno (`prompt`, `base_prompt`, `camera_and_realism`, `grounding`).

### Fase 1 — Extração de constantes (zero mudança comportamental)
Mover para `agent_runtime/constants.py`:
1. `AGENT_RESPONSE_SCHEMA`, `UNIFIED_VISION_SCHEMA`.
2. keywords de cena/câmera/grounding.
3. templates e pools estáticos.

Critério: diff funcional nulo.

### Fase 2 — Extração de funções puras (baixo risco)
Mover para módulos dedicados:
1. `parser.py`: parsing/decoding JSON.
2. `camera.py`: camera/realism profile e normalização.
3. `structural.py`: prune/resolve/compress.
4. `compiler.py`: `_compile_prompt_v2` e helpers de budget.

Critério: mesmos outputs para os mesmos inputs de teste.

### Fase 3 — Extração de I/O de grounding/visual
Mover para:
1. `grounding.py`: pesquisa, forced search, pose extraction.
2. `visual_refs.py`: html/playwright/download.

Critério:
1. sem quebra de `grounding_mode`.
2. `effective/sources/reason_codes` preservados.

### Fase 4 — Wrapper Gemini e redução de acoplamento
Criar `gemini_client.py` com funções explícitas:
1. `generate_structured_json(...)`
2. `generate_text_with_tools(...)`
3. `generate_multimodal(...)`

Objetivo: eliminar chamada SDK espalhada e facilitar mock/teste.

### Fase 5 — Limpeza final do `agent.py`
`agent.py` fica apenas com:
1. assinatura pública `run_agent`.
2. montagem de contexto.
3. orquestração de módulos.
4. logging final.

Meta: reduzir de ~3000 linhas para ~500-800 linhas.

---

## 5. Regras de Não-Regressão
Durante a refatoração:

1. Não alterar contrato de `run_agent`.
2. Não renomear campos públicos do retorno.
3. Não trocar sem necessidade a política de grounding.
4. Não misturar “refatoração estrutural” com tuning criativo no mesmo commit.

---

## 6. Plano de Testes por Fase

### Testes mínimos obrigatórios
1. Compilação:
   - `python3 -m compileall app/backend`
2. Smoke local:
   - geração com referência sem prompt (`grounding=auto`)
   - geração com prompt textual sem referência
3. Integridade de retorno:
   - `prompt` não vazio
   - `camera_and_realism` presente
   - `grounding` com campos esperados

### Testes de regressão comportamental
1. Prompt final sem contradições estruturais.
2. Sem texto + referência mantém capa catálogo.
3. Grounding sem fonte não injeta contexto fraco.

---

## 7. Critérios de Aceite da Refatoração
1. `agent.py` significativamente menor e legível.
2. Módulos extraídos com responsabilidade clara.
3. Sem regressão funcional nos fluxos principais.
4. Tempo médio do `run_agent` igual ou melhor (não piorar >10%).
5. Rollback simples por fase.

---

## 8. Ordem Recomendada de MTs
1. MT-R1: extrair `constants.py`.
2. MT-R2: extrair `parser.py` e `camera.py`.
3. MT-R3: extrair `structural.py` e `compiler.py`.
4. MT-R4: extrair `grounding.py`.
5. MT-R5: extrair `visual_refs.py`.
6. MT-R6: introduzir `gemini_client.py`.
7. MT-R7: limpar `agent.py` (fachada final).
8. MT-R8: bateria final de smoke + checklist de contrato.

---

## 9. Observação de Escopo
Este plano é de refatoração estrutural.  
Ajustes de criatividade/flexibilidade (cover-first, budget dinâmico, cenário menos rígido) devem ser aplicados em frente separada para não mascarar regressões de arquitetura.
