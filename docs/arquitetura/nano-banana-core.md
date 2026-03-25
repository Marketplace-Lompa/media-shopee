# Nano Banana Core

Status: draft conceitual  
Última consolidação: 2026-03-24  
Escopo: fundação teórica e arquitetural para o cérebro central de prompting, políticas e orquestração do projeto.  
Não é implementação. Não substitui documentação oficial do Gemini API.

---

## 1. Objetivo

Definir o `Nano Banana Core` como a camada central de teoria, boas práticas e políticas operacionais sobre Gemini Image dentro do projeto.

Este documento existe para resolver um problema específico:

- hoje temos conhecimento espalhado entre skill do Codex, instruções hardcoded, docs soltos e aprendizados operacionais;
- no futuro, o produto precisará evoluir para múltiplos domínios, múltiplos workflows e ambiente de produção mais robusto;
- portanto, precisamos de uma fonte de verdade conceitual única antes de implementar qualquer refactor maior.

Tese principal:

> O `Nano Banana Core` não deve ser apenas um wrapper de modelo.  
> Ele deve ser a camada de política, planejamento e guardrails que governa como o produto usa Gemini Image.

---

## 2. O que é o Nano Banana Core

`Nano Banana Core` é a camada central responsável por transformar intenção de negócio e contexto visual em um plano confiável de geração/edição.

Ele deve responder, de forma consistente, perguntas como:

- qual modelo usar;
- quantas referências usar;
- qual o papel de cada referência;
- o que deve ficar travado;
- o que pode mudar;
- como estruturar o prompt;
- quando usar chat/multi-turn;
- quando usar grounding;
- quando usar batch;
- o que é capacidade oficial do Gemini e o que é camada de plataforma.

Em outras palavras:

- o modelo gera a resposta visual;
- o `Nano Banana Core` decide a política e o plano de execução.

---

## 3. Fonte de Verdade

Este documento consolida conhecimento a partir de:

### 3.1 Fontes oficiais externas

- [Gemini API — Nano Banana image generation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- [Batch API](https://ai.google.dev/gemini-api/docs/batch-api)
- [Models overview](https://ai.google.dev/gemini-api/docs/models)

### 3.2 Fontes internas do projeto

- skill global `~/.codex/skills/nano-banana/SKILL.md`
- [Decisão de modelo padrão](../decisoes/modelo-padrao.md)
- [API discoveries](../learnings/api-discoveries.md)
- [Plano original do Studio Local](../planos/app-studio-local.md)

### 3.3 Regra de precedência

Em caso de conflito:

1. documentação oficial do Gemini;
2. ADRs e decisões do projeto;
3. learnings operacionais;
4. skills e playbooks auxiliares.

---

## 4. Baseline oficial consolidado

Esta seção resume o que é mais útil para o projeto segundo a documentação oficial revisada em 2026-03-24.

### 4.1 Mapa oficial de modelos

| Nome de produto | Model ID | Papel principal |
|---|---|---|
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | modelo padrão geral para geração e edição com melhor equilíbrio entre qualidade, velocidade e custo |
| Nano Banana Pro | `gemini-3-pro-image-preview` | produção premium, instruções complexas, layouts ricos e texto mais exigente |
| Nano Banana | `gemini-2.5-flash-image` | volume alto, baixa latência e workflows rápidos |

### 4.2 Diretriz oficial de escolha de modelo

Segundo a documentação oficial de image generation:

- `gemini-3.1-flash-image-preview` deve ser o modelo padrão para a maioria dos casos;
- `gemini-3-pro-image-preview` é indicado para assets mais complexos e exigência maior de qualidade/composição;
- `gemini-2.5-flash-image` é indicado para velocidade e escala.

### 4.3 Referências visuais

Gemini 3 image models suportam até 14 referências totais, com budgets por tipo:

- `gemini-3.1-flash-image-preview`
  - até 10 referências de objeto com alta fidelidade
  - até 4 referências de personagem para consistência
- `gemini-3-pro-image-preview`
  - até 6 referências de objeto com alta fidelidade
  - até 5 referências de personagem
- `gemini-2.5-flash-image`
  - funciona melhor com até 3 imagens de entrada

### 4.4 Resoluções

- `gemini-3.1-flash-image-preview`: `512`, `1K`, `2K`, `4K`
- `gemini-3-pro-image-preview`: `1K`, `2K`, `4K`
- `gemini-2.5-flash-image`: 1024px (`1K` na prática operacional do projeto)

### 4.5 Edição conversacional e multi-turn

A documentação oficial recomenda chat/multi-turn para iteração de imagem.

Isso é importante porque:

- a edição iterativa faz parte do produto;
- Gemini 3 usa `thought signatures`;
- para edição multi-turn, essas assinaturas são críticas para preservar contexto visual e lógica de composição entre turnos.

Diretriz arquitetural:

- sempre preferir SDK oficial e histórico de chat padrão quando houver multi-turn;
- não tratar multi-turn como detalhe opcional de interface;
- multi-turn é capacidade central do core.

### 4.6 Grounding

Capacidades oficiais mais relevantes:

- `google_search` pode ser usado com geração de imagem;
- `gemini-3.1-flash-image-preview` suporta grounding com Google Image Search;
- grounding com Image Search não pode ser usado para buscar pessoas reais;
- o response inclui `groundingMetadata`, incluindo `searchEntryPoint` e `groundingChunks`.

### 4.7 Batch

O Batch API é indicado para geração não urgente em grande volume:

- custo reduzido versus chamadas síncronas padrão;
- turnaround alvo de até 24 horas;
- melhor para lotes grandes e workflows assíncronos de produção.

### 4.8 Prompting oficial

A orientação oficial mais importante é:

> descrever a cena, e não despejar listas de keywords.

A doc também reforça:

- usar linguagem fotográfica quando o objetivo é realismo;
- iterar com pequenas mudanças;
- usar instruções step-by-step para cenas complexas;
- preferir “semantic negative prompting”, descrevendo o desejado positivamente.

---

## 5. O papel do Core no produto

O `Nano Banana Core` deve ser o cérebro central de primeiros princípios.  
Ele não é uma skill de moda. Ele não é uma UI. Ele não é um router HTTP.

Ele deve ser a camada que centraliza:

- teoria oficial do stack Gemini Image;
- regras universais de prompting;
- políticas de referência e lock;
- critérios de escolha de modelo;
- fronteira entre Gemini oficial e features de wrapper;
- contratos conceituais consumidos por domínios e workflows.

Em resumo:

- `core` = conhecimento universal e política;
- `domain` = gramática do negócio;
- `workflow` = comportamento orientado à tarefa;
- `runtime` = execução técnica.

---

## 6. Princípios do Nano Banana Core

### 6.1 Modelo não é política

O modelo não deve decidir sozinho:

- estratégia de referência;
- prioridade entre fidelidade e liberdade;
- quem controla identidade;
- quando usar grounding;
- quando usar batch;
- quando usar conversa multi-turn.

Essas decisões devem nascer no core.

### 6.2 Referência é tipada

Toda referência precisa ter papel explícito.

Papéis mínimos:

- `base_composition`
- `subject_identity`
- `character_consistency`
- `object_fidelity`
- `garment_fidelity`
- `logo_or_text`
- `palette_or_style`
- `scene_context`

Sem papel explícito, a referência vira ruído.

### 6.3 Locks vêm antes da criatividade

O sistema deve definir, antes do prompt final:

- o que é imutável;
- o que é ajustável;
- o que pode variar livremente.

### 6.4 Core não confunde oficial com wrapper

Tudo que for Krea, Higgsfield, treinamento, LoRA, Elements, World Context, Soul ID ou abstrações similares deve ser classificado fora do core oficial do Gemini, salvo confirmação explícita em doc oficial.

### 6.5 Task-first model selection

A escolha do modelo deve partir da tarefa:

- geração rápida;
- geração premium;
- edição iterativa;
- composição complexa;
- produção em escala;
- grounding com imagem;
- texto dentro da imagem.

### 6.6 Multi-turn é parte da arquitetura

Conversational editing não é apenas UX.  
É parte da estratégia de qualidade.

### 6.7 Auditabilidade é obrigatória

Cada decisão do core precisa ser explicável:

- por que escolheu o modelo;
- por que escolheu aquele budget de referências;
- qual lock foi aplicado;
- qual plano de prompt foi usado;
- qual fonte externa foi usada em grounding.

---

## 7. Limites do Core

O `Nano Banana Core` não deve conter:

- vocabulário profundo de uma categoria específica, como construção de tricô, modelagem de vestido ou regras de joalheria;
- regras operacionais específicas de um canal, como slots Shopee ou Mercado Livre;
- layout de UI;
- detalhes de fila, worker, infra AWS, ou contrato HTTP final;
- textos de marketing;
- decisões editoriais de uma categoria específica.

Esses elementos pertencem a outras camadas.

---

## 8. Separação arquitetural recomendada

### 8.1 Core

Responsável por:

- abstrações universais;
- capacidades oficiais;
- model policy;
- reference policy;
- lock policy;
- prompt planning policy;
- grounding policy;
- batch policy;
- platform boundary policy.

### 8.2 Domain skills

Exemplos:

- `fashion`
- `beauty`
- `accessories`
- `home_decor`
- `electronics`

Responsável por:

- gramática do objeto;
- materiais e construção;
- restrições semânticas do domínio;
- sinais de fidelidade;
- defaults visuais da categoria.

### 8.3 Workflow skills

Exemplos:

- `marketplace`
- `free_mode`
- `edit_mode`
- `ugc`
- `catalog_clean`
- `campaign`

Responsável por:

- objetivo operacional;
- formato de saída;
- regras de composição do caso de uso;
- metas comerciais;
- validação específica do fluxo.

### 8.4 Platform adapters

Responsável por:

- mapear o plano do core para Gemini oficial;
- ou para wrappers futuros, se existirem;
- sem poluir a teoria do core com features específicas de plataforma.

### 8.5 Runtime infra

Responsável por:

- API;
- filas;
- observabilidade;
- persistência;
- workers;
- storage;
- cloud deployment.

---

## 9. Contratos conceituais sugeridos

Esta seção ainda é conceitual.  
Ela serve para orientar futura implementação.

### 9.1 `CreateContext`

Representa a intenção de criação.

Campos sugeridos:

- `category`
- `workflow`
- `task_type`
- `user_intent`
- `delivery_target`
- `requested_output`
- `business_constraints`

### 9.2 `ReferenceAsset`

Representa cada entrada visual.

Campos sugeridos:

- `id`
- `source`
- `role`
- `type`
- `priority`
- `must_preserve`
- `fidelity_weight`
- `notes`

### 9.3 `LockPolicy`

Define o que precisa permanecer estável.

Campos sugeridos:

- `identity_lock`
- `object_lock`
- `garment_lock`
- `logo_lock`
- `text_lock`
- `composition_lock`
- `lighting_lock`

### 9.4 `ModelDecision`

Explica a seleção de modelo.

Campos sugeridos:

- `chosen_model`
- `reason`
- `latency_class`
- `cost_class`
- `supports_grounding`
- `supports_image_search`
- `supports_high_fidelity_refs`
- `supports_chat_history`

### 9.5 `PromptPlan`

Plano antes do prompt final.

Campos sugeridos:

- `prompt_mode`
- `prompt_layers`
- `required_clauses`
- `forbidden_patterns`
- `reference_resolution_strategy`
- `grounding_strategy`
- `output_spec`

### 9.6 `ExecutionPlan`

Plano de execução final do job.

Campos sugeridos:

- `model`
- `request_shape`
- `reference_budget`
- `use_chat`
- `use_grounding`
- `use_batch`
- `expected_artifacts`

### 9.7 `AuditTrace`

Telemetria explicável do core.

Campos sugeridos:

- `decision_version`
- `model_decision`
- `reference_decision`
- `lock_decision`
- `prompt_decision`
- `grounding_decision`
- `warnings`

---

## 10. Pipeline conceitual do Core

O pipeline do `Nano Banana Core` deve seguir esta ordem:

1. `normalize intent`
   - limpar e estruturar a intenção do usuário
2. `classify task`
   - geração, edição, composição, grounding, produção em lote
3. `resolve domain profile`
   - carregar especialização de domínio
4. `assign reference roles`
   - classificar cada referência
5. `build lock policy`
   - definir o que não pode mudar
6. `choose model`
   - selecionar o modelo com base na tarefa
7. `build prompt plan`
   - montar a arquitetura do prompt
8. `build execution plan`
   - decidir sync/async/chat/batch/grounding
9. `emit audit trace`
   - registrar o porquê de cada decisão

---

## 11. Aplicação ao projeto atual

Hoje o projeto já possui peças que apontam para esse core, mas ainda de forma espalhada:

- [app/backend/agent_runtime/constants.py](../../app/backend/agent_runtime/constants.py)
  - contém parte importante do vocabulário e das regras de prompting;
- [app/backend/agent.py](../../app/backend/agent.py)
  - hoje concentra parte da montagem de contexto e da chamada ao Gemini;
- [app/backend/edit_agent.py](../../app/backend/edit_agent.py)
  - contém uma variante especializada para edição;
- [app/backend/config.py](../../app/backend/config.py)
  - concentra parte da decisão de modelo default;
- [docs/learnings/api-discoveries.md](../learnings/api-discoveries.md)
  - contém aprendizados operacionais úteis, mas ainda não organizados como política de core.

Conclusão:

- o conhecimento existe;
- mas ainda não existe um `Nano Banana Core` explícito e centralizado;
- este documento é o primeiro passo para consolidá-lo.

---

## 12. O que permanece no Core vs o que sai para skills focadas

### Permanece no Core

- teoria universal de Nano Banana;
- critérios de escolha de modelo;
- políticas de referência;
- políticas de lock;
- regras de prompting universal;
- regras de grounding;
- regras de batch;
- separação oficial vs wrapper;
- contratos conceituais;
- guardrails de qualidade e coerência.

### Sai do Core

- construção de vestuário específica;
- gramática de tecidos e caimento específicos de moda;
- regras de maquiagem, pele e beleza;
- regras de produto por categoria;
- regras de canal/marketplace;
- checklists comerciais específicos de workflow.

### Vai para skills de domínio

- `fashion`
- futuras categorias como `beauty`, `accessories`, `home`, `electronics`

### Vai para skills de workflow

- `marketplace`
- `edit`
- `ugc`
- `catalog_clean`
- `campaign`

---

## 13. Regras operacionais recomendadas para o futuro runtime

Mesmo antes da implementação, estas diretrizes devem orientar decisões futuras:

### 13.1 Preferir SDK oficial para multi-turn

Motivo:

- thought signatures são críticas para edição conversacional em Gemini 3 image;
- usar o SDK oficial reduz risco operacional.

### 13.2 Nunca colapsar budgets de referência em uma regra única

Motivo:

- cada modelo tem comportamento e limites práticos diferentes;
- fidelidade de objeto e consistência de personagem concorrem por budget.

### 13.3 Core deve produzir plano antes do prompt

Motivo:

- separa política de redação;
- torna o sistema auditável;
- facilita testes.

### 13.4 Grounding deve ser uma decisão de política

Motivo:

- grounding tem custo;
- grounding com imagem tem restrições;
- nem todo prompt se beneficia dele.

### 13.5 Batch deve ser estratégia explícita, não fallback implícito

Motivo:

- altera SLA do produto;
- muda UX;
- muda a expectativa de entrega.

---

## 14. Limitações e cautelas

### 14.1 Preview models

Os modelos principais de Gemini 3 image continuam em preview e podem mudar de comportamento, disponibilidade, preço e limites.

### 14.2 Docs oficiais mudam

O core deve ser versionado e revisado periodicamente com base nas docs oficiais.

### 14.3 Learnings locais não substituem fonte oficial

Exemplo:

- um aprendizado de produção pode apontar uma regra útil;
- mas ele deve ser classificado como `observação operacional`, não como fato oficial, até confirmação externa.

---

## 15. Roadmap recomendado

### Fase 0 — agora

Objetivo:

- consolidar teoria e princípios em documento versionado.

Entrega:

- este documento.

### Fase 1 — fundação de contratos

Objetivo:

- introduzir contratos explícitos de contexto, referência, lock e decisão.

Entrega sugerida:

- tipos e contratos internos, sem grande refactor.

### Fase 2 — policy engine

Objetivo:

- mover decisões dispersas para um motor de política central.

Entrega sugerida:

- `model_policy`
- `reference_policy`
- `lock_policy`
- `prompt_policy`

### Fase 3 — plugins de domínio

Objetivo:

- acoplar `fashion` como skill de domínio sobre o core.

Entrega sugerida:

- `domain/fashion`
- registry de domínio
- defaults por categoria.

### Fase 4 — workflows explícitos

Objetivo:

- separar claramente `free mode`, `marketplace`, `edit`, `ugc`, etc.

### Fase 5 — produção cloud

Objetivo:

- subir o runtime em ambiente mais robusto, potencialmente AWS, mantendo o core stateless, versionado, testável e observável.

---

## 16. Decisão atual

Decisão recomendada para o projeto:

1. `nano-banana` passa a ser tratado como o núcleo conceitual universal;
2. `fashion` passa a ser tratado como domínio especializado em cima desse núcleo;
3. workflows como marketplace e edição passam a consumir o core, e não carregar sua própria teoria solta;
4. nenhuma implementação deve preceder a consolidação conceitual do core.

---

## 17. Resumo executivo

`Nano Banana Core` deve ser o cérebro central do sistema, mas não como “um prompt gigante”.

Ele deve ser:

- uma constituição teórica;
- uma camada de política;
- uma base para contratos futuros;
- um ponto de separação entre core universal, domínio e workflow;
- uma fonte de verdade para futuras decisões de runtime.

O documento atual formaliza essa visão para que o projeto evolua com menos improviso e menos acoplamento oculto.

---

## 18. Referências

### Oficiais

- Google AI for Developers — [Nano Banana image generation](https://ai.google.dev/gemini-api/docs/image-generation)
- Google AI for Developers — [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- Google AI for Developers — [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- Google AI for Developers — [Batch API](https://ai.google.dev/gemini-api/docs/batch-api)
- Google AI for Developers — [Models overview](https://ai.google.dev/gemini-api/docs/models)

### Internas

- skill global `~/.codex/skills/nano-banana/SKILL.md`
- [Decisão de modelo padrão](../decisoes/modelo-padrao.md)
- [API discoveries](../learnings/api-discoveries.md)
- [Plano original do Studio Local](../planos/app-studio-local.md)
