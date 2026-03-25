# Multi-Job Assíncrono — Geração Paralela (Nível 2)

## Problema
A app trava completamente durante a geração. O frontend usa state singleton (`status`) que bloqueia toda a UI. Impossível navegar, ver histórico ou iniciar nova geração enquanto um job roda.

## Objetivo
Permitir múltiplos jobs de geração simultâneos, cada um com progresso independente, sem travar a interface.

---

## Proposta de Mudanças

### Frontend

---

#### [NEW] `useJobManager.ts` — Hook central de gerenciamento de jobs

Novo hook React que substitui o state singleton `status` + `hadResearch` por uma **Map de jobs**:

```ts
interface Job {
  id: string;          // session_id do backend
  status: GenerationStatus;
  hadResearch: boolean;
  payload: GeneratePayload;   // prompt, files, configs (para retry/reuse)
  createdAt: number;
  abortController: AbortController;
}

interface JobManager {
  jobs: Map<string, Job>;
  activeJobIds: string[];     // jobs não-idle/done
  startJob(payload) → string; // retorna jobId
  cancelJob(jobId): void;
  clearJob(jobId): void;
  clearFinished(): void;
}
```

- Cada `startJob` gera um `jobId` temporário (UUID client-side), cria um `AbortController`, e inicia o `fetch` SSE de forma **fire-and-forget**.
- O reader SSE atualiza `jobs.get(jobId).status` conforme eventos chegam.
- Quando o SSE envia `done`, o `session_id` do backend substitui o `jobId` temporário.
- `cancelJob` chama `abortController.abort()` para fechar o SSE stream.

---

#### [MODIFY] `App.tsx` — Substituir state singleton por `useJobManager`

**Antes**:
```ts
const [status, setStatus] = useState<GenerationStatus>({ type: 'idle' });
const [hadResearch, setHadResearch] = useState(false);
// ... handleGenerate com await fetch + reader inline
```

**Depois**:
```ts
const { jobs, activeJobIds, startJob, cancelJob, clearFinished } = useJobManager();
// handleGenerate → startJob(payload) — retorna imediatamente
```

Mudanças concretas:
- `handleGenerate` passa de `async function` que faz `await reader.read()` para uma chamada simples de `startJob(payload)` que retorna instantaneamente.
- Não tem mais `busy` global — cada job tem seu próprio estado.
- `ChatInput` recebe `busy={activeJobIds.length >= MAX_CONCURRENT}` ao invés de derivar do `status.type`.
- `Gallery` recebe `jobs` ao invés de `status`.

---

#### [MODIFY] `ChatInput.tsx` — Sempre desbloqueado

- Prop `status: GenerationStatus` → `busy: boolean` (true só se atingir limite de jobs concorrentes, ex: 3)
- Input **nunca trava** — usuário pode digitar e submeter a qualquer momento.
- Botão de envio mostra badge com número de jobs ativos: `🔄 2`.

---

#### [MODIFY] `Gallery.tsx` — Multi-job progress + grid unificado

Substituir o bloco de stepper único por uma **lista de job cards compactos**:

```
┌─────────────────────────────────────────────┐
│ 🔄 Job #a3b8d1b6 — "ruana verde tricot"     │
│ ████████░░ Gerando 3/4 · 45s                │
├─────────────────────────────────────────────┤
│ 🔄 Job #f2c1e9d4 — "camiseta modal"         │
│ ██░░░░░░░░ Analisando imagens · 12s         │
└─────────────────────────────────────────────┘
```

- Cada job ativo mostra uma barra de progresso compacta (não o stepper full-screen)
- Botão de cancelar (X) em cada job card
- Quando `done`, o card colapsa e as imagens entram no grid automaticamente
- Grid de histórico fica **sempre visível** abaixo dos jobs ativos

---

#### [MODIFY] `types/index.ts` — Novo tipo `Job`

Adicionar interface `Job` e `JobManager` exports. `GenerationStatus` permanece inalterado (cada job tem o seu).

---

### Backend

---

#### [MODIFY] `scripts/dev/start-dev.sh` — Workers uvicorn

```diff
-uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info --limit-concurrency 10 &
+uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info --workers 2 --limit-concurrency 10 &
```

> [!IMPORTANT]
> `--reload` e `--workers N` são mutuamente exclusivos no uvicorn. Para dev usaremos `--reload` sem `--workers`. Em produção adicionaríamos `--workers 2+`. Para resolver no dev, o `asyncio.to_thread` que já usamos garante que o event loop do uvicorn não bloqueia — múltiplos SSE streams vão coexistir no mesmo worker.

**Na prática**: O backend já suporta múltiplos SSE streams simultâneos porque usa `asyncio.to_thread` para as chamadas blocantes (agent, generator). O uvicorn em dev com `--reload` roda no single-worker async, e cada SSE é um async generator que yield's e await's sem bloquear o loop. **Não precisa mudar o backend.**

---

#### Backend: Nenhuma mudança necessária

O `stream.py` já usa `async def event_generator()` + `asyncio.to_thread()` para as chamadas CPU-bound. O event loop do uvicorn pode servir N conexões SSE simultâneas sem problema. O bloqueio era 100% no frontend.

---

## Resumo de Arquivos

| Arquivo | Ação | Impacto |
|---|---|---|
| `hooks/useJobManager.ts` | **NEW** | Hook central, ~120 linhas |
| `App.tsx` | **MODIFY** | Simplifica — remove 100+ linhas de SSE inline |
| `ChatInput.tsx` | **MODIFY** | `status` → `busy: boolean` |
| `Gallery.tsx` | **MODIFY** | Stepper singleton → multi-job cards + grid sempre visível |
| `types/index.ts` | **MODIFY** | Adicionar `Job`, `JobManager` |
| `scripts/dev/start-dev.sh` | **SEM MUDANÇA** | Backend já suporta |
| `stream.py` | **SEM MUDANÇA** | Já é async |

---

## Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| **Rate limit da API Google** | Limitar max concurrent jobs no frontend (ex: 3) |
| **Memória com muitos jobs** | Auto-clear jobs `done` após 5 minutos |
| **AbortController não cancela backend** | Backend já fecha SSE stream na desconexão do client — `StreamingResponse` detecta |
| **Conflito de session_id** | Cada job gera UUID independente no backend |

## Verificação

1. Gerar job A, sem esperar terminar gerar job B
2. Ambos devem mostrar progresso independente
3. Resultados de ambos devem aparecer no grid
4. Input nunca fica desabilitado (exceto se atingir MAX_CONCURRENT=3)
5. Cancelar um job não afeta o outro
