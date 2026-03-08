---
description: Registra aprendizados da sessão atual — erros corrigidos, comportamentos descobertos, padrões identificados — para evitar regressões em sessões futuras.
---

# Workflow /train — Auto-aprendizado da sessão

## Objetivo
Consolidar os aprendizados práticos da sessão atual (erros, correções, descobertas) nos arquivos de referência corretos por categoria, consultados automaticamente em sessões futuras.

## Quando usar
- Ao final de uma sessão de desenvolvimento
- Após corrigir um erro não óbvio
- Após descobrir um comportamento não documentado de API
- Após qualquer ajuste que corrigiu uma suposição errada

---

## Passos

### 1. Ler os logs de aprendizados existentes
Leia **todos** os arquivos em `docs/learnings/` para entender o que já foi registrado e evitar duplicatas.

### 2. Identificar os aprendizados da sessão
Analise a conversa atual e identifique:
- ❌ **Erros cometidos** → o que estava errado e por quê
- ✅ **Correções aplicadas** → o que foi feito para corrigir
- 🔍 **Descobertas** → comportamentos não documentados
- ⚙️ **Padrões identificados** → boas práticas emergentes do uso real

### 3. Classificar e rotear para o arquivo correto

Cada aprendizado vai para o arquivo da sua categoria:

| Categoria | Arquivo | Conteúdo |
|---|---|---|
| `api` | `docs/learnings/api-discoveries.md` | Erros/comportamentos da Google AI API, modelos, billing, safety |
| `agente` | `docs/learnings/agent-pipeline.md` | Bugs do pipeline agent→generator→frontend, Pydantic, modos |
| `frontend` / `ux` | `docs/learnings/frontend-ux.md` | CSS, cascade, componentes, estados, UX |
| `tooling` / `devops` | `docs/learnings/tooling.md` | Git, venv, terminal, CI/CD, ambiente |

**Regra de ouro:** se o aprendizado é sobre como a API se comporta → `api-discoveries.md`. Se é sobre como o nosso código orquestra a API → `agent-pipeline.md`. Se é visual → `frontend-ux.md`. Se é infra/ferramentas → `tooling.md`.

### 4. Formatar e adicionar

Adicione ao índice rápido do arquivo e crie a seção detalhada:

```markdown
### [YYYY-MM-DD] Título curto do aprendizado

**Severidade:** 🔴 Crítico (causa erro) | 🟡 Importante (comportamento inesperado) | 🟢 Dica (otimização)

**Contexto:** O que estava sendo feito quando o problema foi encontrado.

**Problema:** Descrição exata do erro ou comportamento inesperado.

**Solução:** O que foi feito para corrigir.

**Regra:**
> Frase imperativa para sessões futuras.
```

### 5. Atualizar documentações impactadas (se necessário)
Se o aprendizado corrige uma documentação existente (ex: skills, agente, configs), edite o arquivo com a correção.

### 6. Confirmar com o usuário
Liste os aprendizados registrados por arquivo e pergunte se há mais algo a documentar.

---

## Estrutura dos arquivos

```
docs/
└── learnings/
    ├── api-discoveries.md    ← API: modelos, billing, safety, rate limits
    ├── agent-pipeline.md     ← Pipeline: agent.py, generator.py, modos, Pydantic
    ├── frontend-ux.md        ← Frontend: CSS, componentes, estados, UX
    └── tooling.md            ← Tooling: git, venv, terminal, CI/CD
```

## Exemplo de resposta esperada

```
📚 /train executado — 5 aprendizados registrados:

api-discoveries.md:
  1. 🔴 Nano Banana 2: MEDIUM não existe → só MINIMAL e HIGH

agent-pipeline.md:
  2. 🔴 GeneratedImage sem campo url → imagens pretas
  3. 🔴 Ternário Python engole MODE 2

frontend-ux.md:
  4. 🟡 :focus-visible global cria borda dupla

tooling.md:
  5. 🟡 2>&1 mascara progresso

Algum outro aprendizado da sessão a documentar?
```
