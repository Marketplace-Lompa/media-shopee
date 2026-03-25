# Arquitetura Serverless: Diagnóstico e Roadmap

> **Data:** 2026-03-16
> **Contexto:** Studio Local / Nano Banana 2 — pipeline FastAPI + Gemini GenAI
> **Status atual:** Arquitetura stateful — funciona perfeitamente em VPS/EC2 dedicado, mas é incompatível com Serverless na forma atual.

---

## TL;DR

O núcleo de IA da aplicação (Fidelity Gate, Curation Policy, Gemini Client, Orquestrador, Two-Pass Flow) é de altíssimo nível e bem modularizado. O problema está exclusivamente na **camada de infraestrutura**, que possui 4 anti-patterns letais para ambientes serverless.

---

## 🚨 Os 4 Gargalos Letais

### 1. Amnésia de Memória — `job_manager.py`

**O problema:**
```
POST /marketplace/async → Contêiner A → salva job em _JOBS (RAM)
GET  /marketplace/jobs/123 → Load Balancer → Contêiner B → _JOBS vazio → 404
```

Em serverless com múltiplas instâncias, o dicionário `_JOBS` não é compartilhado. Cada contêiner tem sua própria memória isolada. O polling do React cai em instâncias diferentes e o job nunca é encontrado.

**Impacto:** Todos os jobs falham intermitentemente em produção com carga real.

---

### 2. Cemitério de Arquivos — `app/outputs/`, `pool.json`, `history.json`

**O problema:**
- Disco local em serverless é efêmero — some quando a instância escala a zero
- `asyncio.Lock()` protege contra concorrência *dentro de um processo*, não entre contêineres
- Dois contêineres simultâneos escrevendo em `pool.json` = corrupção silenciosa

**Impacto:** Histórico, pool de referências e imagens geradas são perdidos no próximo cold start.

---

### 3. Morte Súbita de Background Tasks

**O problema:**
```python
# job_manager.py — padrão atual
asyncio.create_task(run_marketplace_orchestration(...))
return {"job_id": job_id, "status": "queued"}  # ← CPU congela aqui em Lambda/Vercel
```

Em AWS Lambda e Vercel, no exato momento em que a resposta HTTP é enviada, a CPU do contêiner é congelada a 0%. O pipeline de 60-90s para no meio da geração.

**Impacto:** 100% dos jobs ficam travados em `running` para sempre.

---

### 4. Falso Rate Limit — `asyncio.Semaphore`

**O problema:**
```
20 instâncias × Semaphore(3) = 60 chamadas simultâneas ao Gemini
→ 429 Quota Exceeded imediato
```

O semáforo controla concorrência *por processo*. Em serverless com auto-scaling horizontal, o controle é multiplicado pelo número de instâncias ativas — que é imprevisível.

**Impacto:** Picos de tráfego causam quota exceeded no Gemini de forma não determinística.

---

## 🏗️ Arquitetura Serverless Ideal (Event-Driven GCP)

Manter na GCP é a escolha racional: zero egress cost entre serviços + menor latência para o Gemini API.

```
┌─────────────────────────────────────────────────────────────┐
│                        USUÁRIO / REACT                       │
│              Adaptive Polling (3-5s interval)               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  API (FastAPI) │  ← Cloud Run
                    │  Cloud Run     │
                    └───────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
   ┌──────▼──────┐  ┌───────▼──────┐  ┌──────▼──────┐
   │  Upload     │  │  Job no      │  │  Publica    │
   │  refs no    │  │  Firestore   │  │  evento no  │
   │  GCS        │  │  (queued)    │  │  Cloud      │
   └─────────────┘  └──────────────┘  │  Tasks      │
                                      └──────┬──────┘
                                             │
                                    ┌────────▼────────┐
                                    │  WORKER         │  ← Cloud Run (interno)
                                    │  Cloud Run      │
                                    │                 │
                                    │  1. Baixa refs  │
                                    │     do GCS      │
                                    │  2. Roda        │
                                    │     Orquestrador│
                                    │  3. Salva       │
                                    │     outputs GCS │
                                    │  4. Atualiza    │
                                    │     Firestore   │
                                    │     (done, urls)│
                                    └─────────────────┘
```

### Mapeamento de responsabilidades

| Responsabilidade | Atual | Ideal (GCP) |
|---|---|---|
| Compute Web/API | Uvicorn / FastAPI | Cloud Run (FastAPI) |
| Compute Worker | ThreadPoolExecutor | Cloud Run (endpoint interno) |
| Fila / Mensageria | Nenhuma | Cloud Tasks ou Pub/Sub |
| Storage de imagens | `app/outputs/` | Google Cloud Storage (GCS) |
| Database de Jobs | `_JOBS` dict RAM | Firestore ou Cloud SQL |
| Database de Pool/History | `pool.json` / `history.json` | Firestore ou PostgreSQL |
| Rate Limit Global | `asyncio.Semaphore` | Limite nativo Cloud Tasks |

---

## ⚡ Atalho de Ouro: Cloud Run com CPU Always Allocated

Se o objetivo é ir para a nuvem **agora** sem reescrever toda a camada de mensageria, o Google Cloud Run oferece 3 configurações que salvam a arquitetura de background atual:

| Configuração | O que resolve |
|---|---|
| **CPU Always Allocated** | CPU nunca congela após resposta HTTP → background tasks continuam rodando |
| **Session Affinity** | Load balancer roteia polling do mesmo usuário para o mesmo contêiner → mitiga amnésia do `_JOBS` |
| **Timeout até 60 min** | Mantém SSE stream e jobs longos vivos |

> ⚠️ Session Affinity é uma mitigação, não uma solução. Em deploys/restarts, o contêiner muda e o job some. Para produção real, Firestore é obrigatório.

**Mínimo obrigatório mesmo com Cloud Run:** abstrair storage e banco de dados (disco e RAM continuam efêmeros mesmo com CPU Always Allocated).

---

## 🗺️ Mapa de Refatoração (O Que Fazer)

### Passo 1 — StorageProvider (Adapter Pattern)

```python
# Hoje
filepath.write_bytes(image_data)

# Amanhã — mesma interface, plugável
class StorageProvider(Protocol):
    def save(self, key: str, data: bytes) -> str: ...  # retorna URL
    def load(self, key: str) -> bytes: ...

class LocalDiskStorage:
    def save(self, key, data) -> str:
        path = OUTPUTS_DIR / key
        path.write_bytes(data)
        return f"/outputs/{key}"

class GCSStorageProvider:
    def save(self, key, data) -> str:
        blob = self._bucket.blob(key)
        blob.upload_from_string(data)
        return f"https://storage.googleapis.com/{self._bucket_name}/{key}"
```

O `generator.py` e o `marketplace_orchestrator.py` recebem o provider por injeção — sem saber se é disco ou GCS.

---

### Passo 2 — Substituir JSONs por Banco de Dados

| Arquivo atual | Substituto | Motivo |
|---|---|---|
| `_JOBS` (RAM) | Redis (TTL 24h) | Status efêmero, acesso O(1), TTL automático |
| `history.json` | PostgreSQL / Firestore | Persistência, queries por data/usuário |
| `pool.json` | PostgreSQL / Firestore | Consistência em escritas concorrentes |

---

### Passo 3 — Manter Adaptive Polling no Frontend

O polling atual do React é a abordagem **correta e mais resiliente** para serverless — mais tolerante a falhas do que WebSockets (que desconectam em API Gateways). Ajustar para intervalo de 3-5 segundos.

---

## 📋 Ordem de Prioridade

```
Hoje (se for subir em Cloud Run amanhã):
  1. Habilitar CPU Always Allocated + Session Affinity + Timeout 60min
  2. Implementar StorageProvider adapter (Local → GCS)
  3. Migrar _JOBS para Redis

Próximas semanas (produção real):
  4. Migrar history.json e pool.json para PostgreSQL/Firestore
  5. Separar API e Worker em Cloud Run services distintos
  6. Implementar Cloud Tasks para rate limiting global do Gemini

Longo prazo:
  7. Event-driven completo com Pub/Sub
  8. Observability (Cloud Monitoring, structured logs)
```

---

## ✅ O Que NÃO Precisa Mudar

- Pipeline de IA (Fidelity Gate, Curation Policy, Two-Pass Flow, Art Direction Sampler)
- Orquestrador marketplace e lógica de slots
- Gemini client e retry logic
- Prompts e triage
- Frontend React e estrutura de componentes

A refatoração é **100% de infraestrutura** — o core de IA permanece intacto.
