# Skills no Google Antigravity — Guia Completo

## O que são Skills?

**Skills** são pacotes leves e modulares que **estendem as capacidades do agente AI** com conhecimento e fluxos especializados. São a peça intermediária entre:
- **Rules** (passivas, sempre ativas)
- **Workflows** (ativas, acionadas pelo usuário via `/comando`)
- **Skills** (ativas, acionadas automaticamente pelo agente quando detecta relevância)

> [!IMPORTANT]
> Skills são carregadas **sob demanda**: o agente analisa a `description` do frontmatter e decide se aquela skill é relevante para a tarefa atual. Isso otimiza performance e precisão.

---

## Estrutura de uma Skill

```
.agent/skills/
└── nome-da-skill/
    ├── SKILL.md          # (obrigatório) Definição principal
    ├── scripts/          # (opcional) Scripts Python/Bash/Node
    ├── examples/         # (opcional) Exemplos de uso
    └── resources/        # (opcional) Templates, docs, configs
```

### Escopos

| Escopo | Localização | Disponibilidade |
|--------|-------------|-----------------|
| **Workspace** | `<workspace-root>/.agent/skills/` | Apenas neste projeto |
| **Global** | `~/.gemini/antigravity/skills/` | Todos os projetos |

---

## O arquivo `SKILL.md`

É o "cérebro" da skill. Composto por duas partes:

### 1. YAML Frontmatter (metadados)

```yaml
---
name: nome-da-skill
description: >
  Descrição clara do que a skill faz e QUANDO deve ser usada.
  Escrita em 3ª pessoa para facilitar matching semântico.
---
```

> [!TIP]
> A `description` é a **única parte indexada** pelo roteador de alto nível do agente. Escreva de forma que, ao ler, o agente entenda SE deve ativá-la para a tarefa atual.

### 2. Corpo Markdown (instruções)

Instruções detalhadas, step-by-step, convenções e padrões que o agente deve seguir ao executar a skill. Pode incluir:
- Pré-requisitos
- Passos de execução
- Exemplos de código
- Referências a scripts da pasta `scripts/`

---

## Comparação: Rules vs Workflows vs Skills

| Aspecto | Rules | Workflows | Skills |
|---------|-------|-----------|--------|
| **Ativação** | Automática (sempre on) | Manual pelo usuário (`/comando`) | Automática pelo agente (por relevância) |
| **Local** | `.agent/rules/` | `.agent/workflows/` | `.agent/skills/` |
| **Formato** | `.md` com frontmatter | `.md` com frontmatter | Pasta com `SKILL.md` |
| **Uso** | Regras globais, padrões de código | Tarefas repetitivas sob demanda | Capacidades especializadas |
| **Contexto** | Sempre carregado | Carregado quando invocado | Carregado quando relevante |

---

## Exemplo Prático: Skill de Formatação de Commits

```
.agent/skills/
└── git-formatter/
    ├── SKILL.md
    └── scripts/
        └── format_commit.sh
```

### `SKILL.md`:
```yaml
---
name: git-formatter
description: >
  Formats Git commit messages following Conventional Commits standard.
  Should be used when the user asks to commit changes or create
  a commit message.
---
```

```markdown
# Git Commit Formatter

## Quando Usar
Quando o usuário pedir para fazer commit de mudanças.

## Formato
Usar Conventional Commits:
- `feat:` para novas features
- `fix:` para correções
- `docs:` para documentação
- `refactor:` para refatoração

## Execução
1. Analise as mudanças no staging (`git diff --staged`)
2. Determine o tipo de mudança
3. Gere a mensagem de commit no formato correto
4. Execute o commit
```

---

## Como Criar uma Skill

1. Crie a pasta dentro de `.agent/skills/` (workspace) ou `~/.gemini/antigravity/skills/` (global)
2. Crie o arquivo `SKILL.md` com frontmatter YAML (name + description)
3. Escreva instruções claras no corpo markdown
4. Opcionalmente adicione `scripts/`, `examples/` e `resources/`
5. O agente detectará automaticamente a skill quando for relevante

> [!NOTE]
> **Dica de escrita:** A `description` no frontmatter deve ser descritiva o suficiente para matching semântico. Use termos que o usuário provavelmente usaria ao solicitar aquela capacidade.

---

## Boas Práticas

- **Uma responsabilidade por skill** — não misturar múltiplas capacidades
- **Description clara** — é o critério de ativação automática
- **Scripts auxiliares** — para lógica complexa, use scripts em `scripts/`
- **Exemplos** — facilita o agente entender o output esperado
- **Escopo correto** — use global para skills universais, workspace para projeto-específicas
