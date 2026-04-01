# Fluxo End-to-End de Criação de Imagem — MEDIA-SHOPEE (v1)

**Data:** 2026-03-29
**Objetivo:** consolidar o caminho de execução de prompts/casting/geração para suportar diagnóstico do problema de inconsistência no rosto e corpo da modelo.

## 1) Visão geral

A geração de imagem usa um pipeline de duas etapas com validações e reparos automáticos:

1. **Pré-processamento e inferência semântica do prompt** (agente principal + souls de cast/vestuário)
2. **Geração base (Fidelity Stage 1)**
3. **Edição/edição por imagem (Fidelity Stage 2)** com `lock_person` desabilitado por padrão no modo natural
4. **Refinamentos/repair e validação de fidelidade** quando necessário

Os pontos críticos para o problema atual estão concentrados em:

- qualidade e densidade de `casting_direction` (descrição de fisionomia/biometria)
- prioridade/ordem de composição do prompt final
- regras de anti-identidade em `mode` natural
- ponto de truncagem/remoção de blocos do prompt final

---

## 2) Entrada da solicitação e orquestração geral

### 2.1 Entrada da API/serviço
- Entrada de rota chega no backend de geração com metadados da geração (modo, textos de prompt, `lock_person`, referências etc.).
- A orquestração passa por `app/backend/agent_runtime/generation_flow.py`.

### 2.2 Pipeline em `generation_flow.py`
- `GenerationFlow` coordena etapas com funções de montagem de contexto e chamadas de agente.
- No fluxo normal:
  - Valida guardrails e referências visuais
  - Resolve contexto textual e de casting
  - Executa geração Stage 1 via `fidelity.build_stage1_prompt(...)`
  - Gera imagem base (`generate_images`)
  - Prepara Stage 2 via `fidelity.compile_edit_prompt(...)`
  - Edita imagem (`generator.edit_image(...)`, com `lock_person=False` em cenários típicos)
  - Em erro/fidelidade insuficiente: dispara função de reparo (`evaluate_visual_fidelity`, `repair*`) antes de seguir

---

## 3) Construção do contexto semântico (casting/identity)

### 3.1 `agent.py`
- `run_agent(...)` monta estrutura central e executa agentes de linguagem.
- Campo-chave: `casting_direction`.
- Atualiza `diversity_target` com `casting_state` quando disponível (diretiva de identidade/variedade a ser preservada no output).
- Gera parâmetros de contexto que chegam ao compilador de prompt.

### 3.2 `model_grounding.py` (extração e fallback de casting)
- Responsável por extrair atributos físicos estruturados por schema (`CASTING_DIRECTION_SCHEMA`) quando o texto de entrada pede/implica uma identidade.
- Em chamadas atuais, o retorno é normalizado para:
  - `casting_state` (direção de casting)
  - `casting_state.profile_hint`
  - `casting_state.chosen_direction`
- Há fallback para derivar `casting_state` a partir de `chosen_direction` quando vazio,
  mas o fluxo ainda pode acabar com direção fraca/superficial quando a extração inicial é pobre.

### 3.3 `prompt_context.py`
- Função de contexto injeta blocos do modelo no template:
  - `model_soul` (comportamento do modo/modelo de persona)
  - `casting_direction` quando `confidence > 0.35`
  - `diversity_target` com instruções de troca de personagem e liberdade de pose/retrato/ambiente
- O texto de casting é envolvido com `<CASTING_DIRECTION>...</CASTING_DIRECTION>`.

---

## 4) Stage 1 (fidelidade de base)

### 4.1 `fidelity.py`
- `build_stage1_prompt(...)` monta o prompt base a partir de contexto e referências.
- `generate_images(...)` dispara geração inicial.
- É uma etapa útil para materializar rapidamente composição, iluminação e roupa antes de editar.

---

## 5) Stage 2 (edição/patch sobre imagem base)

### 5.1 `fidelity.compile_edit_prompt(...)`
- Recompõe prompt para Stage 2.
- Injeções típicas dessa etapa:
  - `Replace the person in the base image as instructed`
  - preservação estrita da roupa e geometria (caso de lock de vestuário)
  - instruções anti-identidade (`Do not preserve base/reference identity`)
  - instruções de ambiente/pose/iluminação

### 5.2 `generator.py` (`edit_image`)
- Finaliza com chamada para API de imagem.
- `lock_person` e parâmetros de `mode` determinam pressão de substituição total.
- O fluxo grava o texto final em variáveis de diagnóstico (`prompt` final), ainda que não exista telemetria estruturada padronizada para inspeção ponta a ponta.

---

## 6) Compilação final do prompt

### 6.1 `prompt_result.py`
- `PromptResult` consolida texto final de prompt e negativo.
- A compilação principal de string acontece em `_compile_prompt_v2`.
- Há lógica de prioridades e de preenchimento de surface casting via `_maybe_enforce_casting_surface(...)`.
- Dependendo de limite de tamanho/normalização, há risco de perda de atributos menos fortes.

### 6.2 `compiler.py`
- Responsável por ordenar/combinar blocos do prompt.
- O posicionamento de blocos influencia fortemente qual parte o modelo prioriza por attention budget.

---

## 7) Regras de modo e persona

### 7.1 `model_soul.py`
- Define modos de atuação do soul (e.g. natural) e suas diretivas.
- Natural já tende a instruções de “aparência natural/realista” + controle de inconsistências.

### 7.2 `mode_identity_soul.py`
- Aplica regras de identidade (negativas e positivas) por `mode`.
- Modo natural contém anti-regras fortes para não copiar identidade de referência, o que pode competir com a força de detalhes de casting se este vier fraco.

---

## 8) Fluxo de controle e correção de falha

1. Prompt passa pelo agente principal e grounding
2. Criação de `cast/ prompt context`
3. `fidelity Stage 1` (base)
4. Validação de resultado
5. `fidelity Stage 2` com edição da pessoa
6. Validação visual/fidelity
7. Se necessário, gera reparos e rerun

O fluxo atual já tem mecanismos de reparo, mas sem observabilidade padronizada do estado de cast antes da chamada final ao gerador.

---

## 9) Mapa de pontos críticos para o problema reportado (modelo inconsistente)

- **Atenção insuficiente no casting:** texto narrativo rico de roupa tende a dominar, reduzindo foco no rosto/corpo.
- **`casting_direction` fraco/baixo volume semântico:** se o agente retorna pouco conteúdo objetivo, o modelo perde âncoras de fisionomia.
- **Conflito anti-identidade natural:** negações fortes removem atributos positivos e podem achatar sinais anatômicos.
- **Truncagem de prompt:** perda de blocos de casting em cenários de limite de tamanho.
- **Ordem de blocos de compilação:** casting e roupa podem se “misturar” em prioridade, gerando bleed/saída genérica.

---

## 10) Mapa Mermaid (sequência simplificada)

```mermaid
flowchart LR
  A[Cliente / Requisição API] --> B[GenerationFlow]
  B --> C[agent.py: resolve context + cast]
  C --> D[model_grounding.py: CASTING_DIRECTION_SCHEMA]
  C --> E[prompt_context.py: model_soul + diversity_target + casting_direction]
  D --> E
  B --> F[fidelity.py: build_stage1_prompt]
  F --> G[fidelity.py: generate_images (stage1)]
  G --> H[fidelity.py: compile_edit_prompt]
  H --> I[generation_flow: edit_image]
  I --> J[generator.py: edit_image]
  J --> K[API de imagem]
  K --> L[generation_flow: evaluate_visual_fidelity]
  L --> M{Passou?}
  M -->|Não| N[repair + regenerate]
  M -->|Sim| O[Saída final]
  I --> P[prompt_result.py + compiler.py]
```

---

## 11) O papel do `model_soul`

`model_soul` está no fluxo principal:
- influenciando regras de tom/realismo e estilo do rosto
- participando da composição em `prompt_context.py`
- cooperando com `mode_identity_soul` para anti-identidade

Portanto, **sim, ele entra no fluxo e pode ser um ponto de ajuste direto** quando ocorre perda de detalhe anatômico.

---

## 12) Ponto de ancoragem para próxima etapa (próximas ações)

Para continuar os ajustes, sugerimos atacar nesta ordem:
1. Garantir preenchimento mínimo de `casting_direction` sempre com 3–5 atributos objetivos válidos.
2. Isolar blocos no compilador (`roupa` vs `casting`) para não haver bleed de atenção.
3. Reduzir/qualificar anti-identidade em `natural` quando existir cast forte.
4. Adicionar telemetria estruturada do cast final antes de enviar para a geração.
5. Validar lote de 20 seeds + KPI de variabilidade de fisionomia.

---

## 13) Observação de risco residual

Este documento descreve o estado atual sem executar mudanças de código. As próximas mudanças devem seguir validação incremental de KPI e manter o lock de vestuário intacto.
