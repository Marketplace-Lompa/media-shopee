# Plano — Studio Local de Geração de Imagens

## Objetivo

Aplicação full-stack local para automatizar o fluxo de geração de imagens de moda para marketplace. O ponto central é um **Agente de Prompt Specialist** que intercepta toda requisição de geração — lê as skills (moda, realismo, ecommerce), analisa as imagens de referência e otimiza o prompt para Nano Banana antes de gerar.

---

## Arquitetura

```
Frontend React (porta 5173)
        ↓
Backend FastAPI (porta 8000)
├── Prompt Agent (Gemini 3.1 Flash — raciocina sobre o prompt)
│   ├── Lê skills: moda.md + realismo.md + ecommerce.md
│   ├── Analisa imagens do pool de referência
│   └── Devolve prompt otimizado (editável pelo usuário)
├── Image Generator (Gemini 3.1 Flash Image — gera a imagem)
│   └── safety_settings: BLOCK_NONE em todas as categorias
├── Session Manager (produtos/sessões por pasta local)
└── Reference Pool Manager (LoRA-like: refs originais + geradas)
```

---

## Fluxo do usuário

```
1. Cria sessão (ex: "camiseta-modal-preta")
2. Faz upload das fotos de referência da peça → pool de referência
3. Abre chat e descreve o que quer ("modelo feminina, pose dinâmica, shopee hero")
4. Agente analisa: skills + imagens de ref → monta prompt otimizado
5. Usuário vê o prompt gerado — pode editar antes de gerar
6. Gera imagem → aparece na galeria
7. Gosta de uma gerada? Adiciona ao pool com 1 clique (LoRA-like)
8. Continua refinando via chat
```

---

## Estrutura de Arquivos a Criar

```
MEDIA-SHOPEE/
└── app/
    ├── backend/
    │   ├── main.py               [NEW] FastAPI app + rotas
    │   ├── agent.py              [NEW] Prompt Agent (Gemini 3.1 Flash)
    │   ├── generator.py          [NEW] Image Generator (Nano Banana 2)
    │   ├── sessions.py           [NEW] CRUD de sessões/produtos
    │   ├── skills_loader.py      [NEW] Carrega skills como contexto do agente
    │   ├── requirements.txt      [NEW] fastapi, uvicorn, google-genai, pillow, python-multipart
    │   └── data/                 [NEW] Pasta de sessões (git-ignored)
    │       └── {sessao}/
    │           ├── refs/         ← fotos originais do produto
    │           ├── generated/    ← imagens geradas
    │           └── pool/         ← refs + geradas que entram no contexto
    └── frontend/
        ├── index.html            [NEW]
        ├── src/
        │   ├── main.jsx          [NEW]
        │   ├── App.jsx           [NEW]
        │   ├── index.css         [NEW] design system minimalista dark
        │   └── components/
        │       ├── Sidebar.jsx       [NEW] lista de sessões
        │       ├── ReferencePool.jsx [NEW] grid de refs + drag & drop
        │       ├── ChatAgent.jsx     [NEW] chat com o agente
        │       ├── PromptEditor.jsx  [NEW] prompt editável antes de gerar
        │       ├── Gallery.jsx       [NEW] imagens geradas
        │       └── GenerateControls.jsx [NEW] proporção, resolução
        └── package.json          [NEW] React + Vite

```

---

## Componentes chave

### 1. Prompt Agent (`agent.py`)

O agente **não gera imagem** — ele raciocina sobre o prompt usando `gemini-3.1-flash` (texto puro, sem custo de imagem).

Contexto injetado no system instruction:
- Skill `moda` completa (vocabulário de tecidos, construção, comportamento)
- Skill `realismo` completa (levers de realismo)
- Skill `ecommerce` completa (shots, poses, cenários BR)
- Documentação Nano Banana (boas práticas de prompt)
- Thumbnails das imagens no pool de referência ativa

Saída: prompt estruturado em inglês, pronto para o gerador, com parâmetros recomendados (proporção, resolução, thinking level).

### 2. Reference Pool + LoRA-like (`sessions.py`)

Cada sessão tem 3 pastas:
- `refs/` — fotos originais da peça (upload manual do usuário)
- `generated/` — tudo que foi gerado nessa sessão
- `pool/` — symlinks ou cópias do que o usuário quer incluir como contexto ativo

O usuário escolhe quais imagens entram no pool (refs e/ou geradas). O agente recebe as imagens do pool como referência visual.

### 3. Image Generator (`generator.py`)

Usa o `gerar_imagem.py` existente como base, com:
- `safety_settings=SAFETY_CONFIG` (BLOCK_NONE em tudo)
- `thinking_level` determinado pelo agente com base na complexidade do prompt
- Salva resultado em `generated/` e retorna base64 para o frontend

### 4. Frontend Design — Dark Minimalista

- Paleta: `#0a0a0a` background, `#151515` panels, `#ffffff` texto, `#7c6af7` accent (violeta)
- Fonte: `Inter` (Google Fonts)
- Layout: sidebar esquerda (sessões) + painel central (refs/chat) + painel direito (galeria)
- Drag & drop nativo para upload de imagens
- Chat com streaming da resposta do agente

---

## Proposed Changes

### Backend

#### [NEW] app/backend/main.py
FastAPI com CORS liberado para localhost, rotas:
- `POST /sessions` — criar sessão
- `GET /sessions` — listar sessões
- `POST /sessions/{id}/refs/upload` — upload de imagens de ref
- `GET /sessions/{id}/pool` — retorna imagens do pool
- `POST /sessions/{id}/pool/add` — move imagem gerada para pool
- `POST /sessions/{id}/agent/chat` — conversa com o agente (gera prompt otimizado)
- `POST /sessions/{id}/generate` — gera imagem com o prompt
- `GET /sessions/{id}/gallery` — lista imagens geradas

#### [NEW] app/backend/agent.py
Sistema de multi-turn com Gemini 3.1 Flash. O agente mantém histórico da conversa por sessão, recebe as skills e imagens de referência no contexto e retorna JSON: `{ prompt, aspect_ratio, resolution, thinking_level, rationale }`.

#### [NEW] app/backend/generator.py
Wrapper do `google-genai` para geração de imagem. Recebe o prompt otimizado pelo agente e os parâmetros, gera, salva e retorna caminho + base64.

#### [NEW] app/backend/skills_loader.py
Lê os arquivos `.agent/skills/*/SKILL.md` em tempo de execução e os formata como system instruction do agente.

#### [NEW] app/backend/requirements.txt
```
fastapi
uvicorn[standard]
google-genai
pillow
python-multipart
python-dotenv
```

### Frontend

#### [NEW] app/frontend/ (React + Vite)
Aplicação minimalista dark com 3 painéis. Sem biblioteca de componentes — CSS vanilla para máximo controle.

---

## Verificação

### 1. Backend (testes manuais via curl)

```bash
# Iniciar backend
cd app/backend && uvicorn main:app --reload --port 8000

# Criar sessão
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "camiseta-teste"}'

# Listar sessões
curl http://localhost:8000/sessions

# Chat com agente (gera prompt otimizado)
curl -X POST http://localhost:8000/sessions/camiseta-teste/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "quero uma foto hero shopee, modelo feminina, pose dinâmica"}'
```

### 2. Frontend

```bash
# Instalar e iniciar
cd app/frontend && npm install && npm run dev
# Abrir http://localhost:5173
```

### 3. Fluxo completo integrado (manual)
1. Criar sessão "teste" pela interface
2. Fazer upload de 2-3 fotos de referência
3. Digitar no chat: _"quero uma foto hero para Shopee, modelo brasileira, pose dinâmica"_
4. Verificar que o agente retorna prompt estruturado com parâmetros
5. Editar o prompt se desejar e clicar em Gerar
6. Verificar que a imagem aparece na galeria
7. Clicar em "Adicionar ao pool" e verificar que a imagem entra no pool de referência

---

## Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Skills muito longas → excede contexto do agente | Resumir/chunkar os SKILLs, priorizar seções mais relevantes |
| Latência alta (agente + gerador em sequência) | Streaming da resposta do agente; progresso visual no frontend |
| Muitas imagens no pool → custo de tokens | Limitar pool a 8 imagens visíveis por padrão; thumbnaills em baixa resolução para o agente |
| Estrutura de pastas local não portável | Caminhos relativos + config via `.env` para facilitar futura hospedagem |

---

## Posso executar?
