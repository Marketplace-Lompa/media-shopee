---
description: Registra aprendizados da sessão atual — erros corrigidos, comportamentos descobertos, padrões identificados — para evitar regressões em sessões futuras.
---

# Workflow /train — Auto-aprendizado da sessão

## Objetivo
Consolidar os aprendizados práticos da sessão atual (erros, correções, descobertas) em um arquivo de referência persistente (`docs/learnings/api-discoveries.md`) que será consultado automaticamente em sessões futuras.

## Quando usar
- Ao final de uma sessão de desenvolvimento
- Após corrigir um erro não óbvio
- Após descobrir um comportamento não documentado de API
- Após qualquer ajuste que corrigiu uma suposição errada

---

## Passos

### 1. Ler o log de aprendizados existente
Leia o arquivo `docs/learnings/api-discoveries.md` para entender o que já foi registrado e evitar duplicatas.

### 2. Identificar os aprendizados da sessão
Analise a conversa atual e identifique:
- ❌ **Erros cometidos** → o que estava errado e por quê
- ✅ **Correções aplicadas** → o que foi feito para corrigir
- 🔍 **Descobertas** → comportamentos de API não documentados
- ⚙️ **Padrões identificados** → boas práticas emergentes do uso real

### 3. Formatar e adicionar ao arquivo de learnings
Adicione cada aprendizado no formato padrão abaixo ao arquivo `docs/learnings/api-discoveries.md`:

```markdown
### [YYYY-MM-DD] Título curto do aprendizado

**Categoria:** `api` | `skill` | `agente` | `tooling` | `fluxo`
**Modelo afetado:** (ex: gemini-3.1-flash-image-preview, gemini-3-flash-preview)
**Severidade:** 🔴 Crítico (causa erro) | 🟡 Importante (comportamento inesperado) | 🟢 Dica (otimização)

**Contexto:** O que estava sendo feito quando o problema foi encontrado.

**Problema:** Descrição exata do erro ou comportamento inesperado.

**Solução:** O que foi feito para corrigir.

**Valor para sessões futuras:** Como isso evita retrabalho.
```

### 4. Atualizar documentações impactadas (se necessário)
Se o aprendizado corrige uma documentação existente (ex: `api/docs/engenharia-prompt.md`, skills, agente), edite o arquivo com a correção.

### 5. Confirmar com o usuário
Liste os aprendizados registrados e pergunte se há mais algo da sessão a documentar antes de fechar.

---

## Estrutura do arquivo de saída

```
docs/
└── learnings/
    └── api-discoveries.md   ← arquivo principal de aprendizados
```

## Exemplo de resposta esperada

```
📚 /train executado — 3 aprendizados registrados:

1. 🔴 [API] Nano Banana 2: MEDIUM não existe → só MINIMAL e HIGH
2. 🟡 [API] Billing obrigatório para modelos de imagem (free tier = limit 0)
3. 🟢 [Tooling] venv deve ser adicionado ao .gitignore antes do primeiro commit

Arquivo atualizado: docs/learnings/api-discoveries.md
Algum outro aprendizado da sessão a documentar?
```
