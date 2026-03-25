# Pipeline Grounding v2 (Local-First) com Score de Confianca

Status: proposta pronta para implementacao incremental
Ultima revisao: 2026-03-07

---

## 1. Objetivo

Melhorar fidelidade em pecas atipicas (ex: open-front batwing/dolman com cachecol), reduzindo erros de:
- nome da peca (poncho vs cardigan/ruana)
- manga (morcego/dolman virando manga comum)
- barra arredondada perdendo forma
- textura/padrao sendo reinterpretado

Sem travar o fluxo local: se grounding falhar, pipeline continua.

---

## 2. Problema Atual

O pipeline atual faz Agent -> Nano, mas sem um gate objetivo para decidir quando pesquisar referencias externas.
Resultado:
- em peca simples: grounding seria custo/latencia desnecessarios
- em peca atipica: sem grounding, modelo erra silhueta e construcao

---

## 3. Fluxo v2

Fase 0 - Ingestao
- Recebe prompt (opcional) + imagens upload + pool.

Fase 1 - Analise Estrutural (Gemini Agent)
- Extrai hipoteses de peca e construcao:
  - tipo de peca
  - abertura frontal
  - tipo de manga
  - tipo de barra
  - risco de textura

Fase 2 - Triage por score
- Calcula `grounding_score` e define `grounding_mode`:
  - `off`
  - `lexical` (nomenclatura/pose)
  - `full` (inclui download de 2-3 refs visuais)

Fase 3 - Grounding Condicional
- `off`: segue direto para prompt final.
- `lexical`: faz pesquisa textual curta (nome tecnico + termos de pose).
- `full`: pesquisa + Playwright para extrair imagens de referencia de paginas retornadas.

Fase 4 - Prompt Final + Geracao
- Prompt com Fidelity Lock + hard constraints de silhueta.
- Nano recebe:
  1) imagens do usuario
  2) refs do pool
  3) refs de grounding (se `full`)
  4) prompt final

Fase 5 - Verificacao rapida
- Agent compara resultado vs requisitos estruturais (abertura, manga, barra).
- Se falha, 1 tentativa de correcao direcionada.

---

## 4. Score de Confianca

Formula recomendada (0 a 1):

```text
grounding_score =
  0.45 * (1 - silhouette_confidence) +
  0.25 * atypical_shape +
  0.20 * texture_risk +
  0.10 * name_ambiguity
```

Definicoes:
- `silhouette_confidence`: confianca do agent na classificacao da peca (0-1)
- `atypical_shape`: 0 ou 1 (batwing/dolman, open-front incomum, barra cocoon, assimetria)
- `texture_risk`: 0-1 (alto risco de quebrar padrao/estrutura)
- `name_ambiguity`: 0-1 (duvida de nomenclatura)

Thresholds locais:
- `< 0.45` -> `grounding_mode=off`
- `>= 0.45 e < 0.65` -> `grounding_mode=lexical`
- `>= 0.65` -> `grounding_mode=full`

---

## 5. Contrato de Saida do Agent

Adicionar no JSON de `run_agent`:

```json
{
  "prompt": "string",
  "thinking_level": "MINIMAL|HIGH",
  "thinking_reason": "string",
  "shot_type": "wide|medium|close-up|auto",
  "realism_level": 1,
  "image_analysis": "string",
  "garment_hypothesis": "open-front batwing cardigan with matching scarf",
  "silhouette_confidence": 0.42,
  "atypical_shape": 1,
  "texture_risk": 0.8,
  "name_ambiguity": 0.7,
  "grounding_score": 0.74,
  "grounding_mode": "full",
  "grounding_queries": [
    "open-front batwing cardigan crochet",
    "dolman cardigan fashion photography pose"
  ]
}
```

---

## 6. Contrato SSE (UX)

Novos estagios:
- `analyzing`
- `triage_done`
- `researching` (somente quando grounding ativo)
- `prompt_ready`
- `generating`
- `qa_check`
- `done`
- `error`

Payload minimo em `triage_done`:

```json
{
  "stage": "triage_done",
  "grounding_score": 0.74,
  "grounding_mode": "full",
  "garment_hypothesis": "open-front batwing cardigan"
}
```

---

## 7. Playwright no Grounding (modo `full`)

Como usar localmente:
- abrir paginas retornadas pelo grounding
- coletar `img[src]` e `img[srcset]`
- filtrar por tamanho/minimo e MIME imagem
- baixar no maximo 2-3 imagens validas

Guardrails locais:
- timeout por pagina: 4-6s
- max paginas: 3
- max imagens finais: 3
- se tudo falhar: segue sem refs externas (nao quebra pipeline)

---

## 8. Hard Constraints para peca atipica

No prompt final, incluir sem ambiguidades:
- front fully open (never closed like poncho)
- integrated batwing/dolman sleeve silhouette
- rounded cocoon hem preserved
- matching scarf as separate coordinated piece
- replicate stripe/stitch layout from references exactly

Evitar termos genericos:
- evitar "poncho" isolado quando a peca e aberta na frente

---

## 9. Mapeamento de Implementacao

Backend:
- `app/backend/agent.py`
  - calcula score + mode
  - gera queries de grounding
- `app/backend/routers/stream.py`
  - emite `triage_done` e `researching`
  - injeta refs externas no call do generator
- `app/backend/generator.py`
  - aceita `grounded_images` alem de `pool_images/uploaded_images`
- `app/backend/config.py`
  - flags:
    - `ENABLE_GROUNDING=true|false`
    - `GROUNDING_THRESHOLD_LOW=0.45`
    - `GROUNDING_THRESHOLD_HIGH=0.65`

Frontend:
- `app/frontend/src/types/index.ts`
  - incluir novos estados SSE
- `app/frontend/src/App.tsx` e `Gallery.tsx`
  - renderizar etapa `researching` e resultado de triage

---

## 10. Testes de Aceitacao (seu caso)

Caso: cardigan/poncho atipico com cachecol.

Esperado:
- `grounding_mode = full`
- prompt final com termos `open-front` + `batwing/dolman` + `rounded hem`
- imagem final preserva:
  - abertura frontal real
  - manga morcego
  - barra arredondada
  - cachecol separado

Falha:
- frente fechada tipo cobertor/poncho
- manga comum
- barra reta

Se falhar:
- 1 regeneracao com correcao explicita focada em silhueta (sem mudar textura base).

---

## 11. Rollout incremental (local)

Passo 1:
- score + mode sem baixar imagem externa (`off/lexical` apenas)

Passo 2:
- habilitar `full` com Playwright e limite de 2 refs

Passo 3:
- adicionar QA check automatico e 1 retry

Isso permite validar ganho real de fidelidade sem aumentar muito a complexidade de uma vez.

