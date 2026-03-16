# Execução Multi-Agente — Marketplace (Shopee/ML)

Data: 2026-03-15

## Objetivo

Executar o plano de Marketplace com dois workstreams paralelos, sem conflito de arquivos:

1. **Agente A (Codex aqui)**: backend, regras de negócio, orquestração de shots.
2. **Agente B (outro agente)**: UX/frontend da sessão Marketplace.

---

## Divisão de responsabilidade

## Agente A (Codex) — Backend/Core

Escopo:

1. Criar resolver de política e receitas de shot:
   - `main_variation` (5 slots fixos)
   - `color_variations` (3 slots por cor)
2. Implementar orquestrador marketplace com child jobs de `n_images=1`.
3. Criar endpoint assíncrono dedicado para Marketplace.
4. Centralizar validação de parâmetros de geração (`aspect_ratio`, `resolution`, `n_images`) e aplicar de forma consistente no backend.
5. Retornar payload com:
   - status por slot,
   - cores detectadas,
   - erros parciais por slot.

Arquivos-alvo (backend):

1. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/routers/` (novo router marketplace)
2. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/` (orquestrador/policy)
3. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/models.py` (schemas novos)
4. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/config.py` e utilitários de validação (consistência)

## Agente B (Outro Agente) — Frontend/UX

Escopo:

1. Criar modo Marketplace na tela `Criar` (sem nova aba).
2. Implementar fluxo guiado em 3 passos:
   - Canal + operação
   - Upload de referências
   - Resumo de geração + confirmação
3. Em `operation=main_variation`:
   - mostrar que serão geradas 5 fotos fixas.
4. Em `operation=color_variations`:
   - mostrar instrução obrigatória:
     - usar referências da variação principal + fotos das cores;
   - mostrar total previsto: `3 x N_cores_detectadas`.
5. Esconder `QTD` manual no modo Marketplace.
6. Integrar com endpoint assíncrono novo de Marketplace.

Arquivos-alvo (frontend):

1. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/frontend/src/components/ChatInput.tsx`
2. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/frontend/src/components/ChatInput.css`
3. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/frontend/src/hooks/useJobQueue.ts`
4. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/frontend/src/lib/api.ts`
5. `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/frontend/src/types/index.ts`

---

## Contrato de API congelado (para evitar retrabalho)

Request (`POST /marketplace/async`, multipart/form-data):

1. `marketplace_channel`: `shopee | mercado_livre`
2. `operation`: `main_variation | color_variations`
3. `prompt` (opcional)
4. `aspect_ratio` (default `4:5`)
5. `resolution` (default `1K`)
6. `base_images[]` (obrigatório)
7. `color_images[]` (obrigatório quando `operation=color_variations`)
8. `preset` (default `marketplace_lifestyle`)
9. `scene_preference` (default `auto_br`)
10. `fidelity_mode` (default `estrita` para marketplace)
11. `pose_flex_mode` (default `controlled` para marketplace)

Resposta de status do job (`GET /marketplace/jobs/{id}`):

1. `status`: `queued | running | done | error`
2. `stage`
3. `event` com progresso
4. `response` (quando done), contendo:
   - `marketplace_channel`
   - `operation`
   - `detected_colors[]`
   - `slots[]`:
     - `slot_id`
     - `slot_type`
     - `color` (quando aplicável)
     - `status`
     - `image` (quando sucesso)
     - `error` (quando falha)
   - `summary`:
     - `requested_slots`
     - `completed_slots`
     - `failed_slots`

---

## Ordem de merge recomendada

1. Merge backend (Agente A) primeiro, publicando contrato final.
2. Rebase do frontend (Agente B) no backend merged.
3. Ajustes finais de integração e testes E2E.

---

## Prompt pronto para o outro agente (copiar e colar)

Você vai implementar a camada **frontend/UX** da sessão Marketplace no projeto MEDIA-SHOPEE, sem mexer no backend.

Objetivo UX:
1. Fluxo dentro de `Criar` (sem nova aba).
2. Passo 1: escolher canal (`Shopee` ou `Mercado Livre`) e operação (`Variação principal` ou `Variações de cor`).
3. Passo 2: upload de referências.
4. Passo 3: resumo/confirmar geração.

Regras:
1. `main_variation`: informar que gera 5 fotos fixas.
2. `color_variations`: informar que gera 3 fotos por cor detectada.
3. Exibir texto de ajuda obrigatório:
   - “Use as referências da variação principal + as fotos das cores para gerar as variações.”
4. Esconder `QTD` manual no modo Marketplace.
5. Integrar chamadas com `/marketplace/async` e polling em `/marketplace/jobs/{id}`.

Arquivos permitidos:
1. `app/frontend/src/components/ChatInput.tsx`
2. `app/frontend/src/components/ChatInput.css`
3. `app/frontend/src/hooks/useJobQueue.ts`
4. `app/frontend/src/lib/api.ts`
5. `app/frontend/src/types/index.ts`

Critérios de aceite:
1. Fluxo visual limpo, sem poluição.
2. Não quebrar fluxo atual de geração padrão.
3. Mostrar estado de loading e erro por execução.
4. Build frontend sem erro de tipo.
