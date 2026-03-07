# Integracao MCP: Design Agent + Codex Review Agent

## Visao geral

O Design Agent se integra ao ecossistema Codex **reutilizando** o MCP server existente do `codex-review-agent`.
Nao existe um servidor MCP separado para UX — o mesmo server gerencia code review E UX review.

```
Cliente MCP (Claude Code / Cowork / qualquer)
  |
  v
codex-review MCP server (mcp-server/index.js)
  |
  ├── task_type: "review"       → Code review (profile default/lompa)
  ├── task_type: "explain"      → Explicacao de codigo
  ├── task_type: "architecture" → Analise de arquitetura
  └── task_type: "ux-review"    → UX/Design audit (profile ux-design + knowledge base)
        |
        v
      codex-adapter.js
        ├── loadReviewProfile("ux-design")  → profiles/ux-design.yml
        ├── loadUXKnowledge()               → 5 referencias da base global
        └── buildPrompt()                   → Prompt com formato de resposta UX
              |
              v
            Codex Desktop (codex exec)
              |
              v
            Resultado com findings categorizados
```

## Projetos envolvidos

| Projeto | Caminho | Papel |
|---------|---------|-------|
| codex-review-agent | `~/Documents/codex-review-agent/` | MCP server, profiles, skills |
| Design Agent | `~/Documents/Design/` | Base de conhecimento UX, skill, scripts Playwright |

Os projetos sao irmaos em `~/Documents/`. O adapter resolve a base de conhecimento via path relativo.

## Pre-requisitos

1. **Codex Desktop** instalado e autenticado
2. **Node.js 18+** para o MCP server
3. **MCP server configurado** no `~/.claude/settings.json`:

```json
"codex-review": {
  "command": "node",
  "args": ["/Users/lompa-marketplace/Documents/codex-review-agent/mcp-server/index.js"]
}
```

4. **Base de conhecimento** presente em `~/Documents/Design/base-conhecimento-principal-ux/`

## Como funciona (passo a passo)

### 1. Cliente submete job

```
submit_analysis_job({
  task_type: "ux-review",
  instruction: "Auditoria de UX do componente Hero...",
  repo_root: "/caminho/do/projeto"
})
```

### 2. Server processa

1. Detecta `task_type === "ux-review"`
2. Auto-atribui profile `ux-design` (se nenhum foi especificado)
3. `buildPrompt()` carrega:
   - Profile `ux-design.yml` (severidade, categorias, checklist)
   - 5 referencias da base de conhecimento (via `loadUXKnowledge()`)
   - Formato de resposta UX (categories, breakpoints, style_assessment, wcag)
4. Escreve prompt em arquivo temporario
5. Spawna `codex exec` com o prompt
6. Retorna `job_id` + `poll_after_ms`

### 3. Cliente faz polling

```
get_analysis_job_status({ job_id: "abc-123" })
→ { status: "running", elapsed_seconds: 15, poll_after_ms: 3000 }
```

Repetir ate `status === "succeeded"` ou `"failed"`.

### 4. Cliente busca resultado

```
get_analysis_job_result({ job_id: "abc-123" })
→ {
    summary: "...",
    findings: [
      {
        severity: "major",
        category: "accessibility",
        title: "Contraste insuficiente no CTA principal",
        body: "[Observed] O botao primario...",
        location: { path: "src/Hero.tsx", start_line: 42, component: "Hero" },
        fix_hint: "Alterar background de #6B7 para #2D5...",
        wcag: "1.4.3 Contrast Minimum"
      }
    ],
    breakpoint_issues: [
      { breakpoint: "mobile", description: "Hero title overflow horizontal" }
    ],
    style_assessment: {
      disruptivo: "leve",
      medido: "alto",
      minimalista: "medio",
      profissional_clean: "alto"
    }
  }
```

## Base de conhecimento injetada

O adapter carrega estas 5 referencias (cap total: 80KB):

| Arquivo | Conteudo |
|---------|----------|
| `design-rules-and-heuristics.md` | Heuristicas visuais, performance percebida, cognitive load, dark mode |
| `accessibility-and-inclusion.md` | WCAG 2.1/2.2, ARIA por componente, a11y cognitiva, probes Playwright |
| `ux-states-and-edge-cases.md` | 9 estados de UI, loading patterns por duracao, edge cases |
| `component-patterns.md` | 18 patterns (nav, hero, cards, forms, tables, feedback, skeleton, dashboard) |
| `design-tokens-system.md` | Hierarquia 3 niveis (primitivos, semanticos, componente), dark mode mapping |

O path e resolvido como: `<codex-review-agent>/../Design/base-conhecimento-principal-ux/`.
Override: variavel de ambiente `UX_KNOWLEDGE_BASE`.

## Profile ux-design.yml

O profile auto-atribuido define:

- **Foco**: hierarquia visual, WCAG AA, responsividade 3 breakpoints, estados de UI, touch targets, motion
- **Evidencia**: classificacao obrigatoria como Measured/Observed/Inferred
- **Eixos de estilo**: 4 obrigatorios (disruptivo, medido, minimalista, profissional_clean)
- **Severidade calibrada**: critical (WCAG fail, layout quebrado) → info (preferencia de estilo)
- **9 categorias**: accessibility, visual-hierarchy, responsive, interaction, states, tokens, performance, microcopy, layout
- **Checklist pre-ship**: 10 itens obrigatorios

## Skills disponiveis

| Skill | Plataforma | Arquivo |
|-------|-----------|---------|
| Code Review | Cowork | `cowork-skill/SKILL.md` |
| UX Review | Cowork | `cowork-skill/UX-SKILL.md` |
| Code Review | Codex Desktop | `skill/SKILL.md` |
| UX Operacional | Design Agent | `skills/ux-high-level-agent/SKILL.md` |

## Troubleshooting

### "UX knowledge base not found"
O adapter nao encontrou `../Design/base-conhecimento-principal-ux/`. Verificar:
- Se o projeto Design existe como irmao do codex-review-agent
- Ou definir `UX_KNOWLEDGE_BASE` no ambiente

### "Codex binary not found"
Codex Desktop nao esta instalado ou nao esta no PATH. Verificar:
- macOS: `/Applications/Codex.app/Contents/Resources/codex`
- Ou `which codex`

### Job "failed" com TIMEOUT
O Codex levou mais de 5 min. Possivel causa:
- Prompt muito grande (muitos arquivos + base UX)
- Repo muito grande para analise completa
- Solucao: passar `files` especificos em vez de repo inteiro

### Findings vazios
O Codex nao encontrou issues ou nao parseou o formato JSON. Verificar:
- Se o repo tem codigo frontend/UI para analisar
- Se a instruction e especifica o suficiente
- Logs em stderr do MCP server

## Evolucao

Para adicionar novos tipos de analise no futuro:

1. Adicionar ao enum em `index.js` (z.enum)
2. Adicionar label em `TASK_LABELS` no `codex-adapter.js`
3. Adicionar response format no `buildPrompt()`
4. Criar profile em `profiles/`
5. Criar skill em `cowork-skill/`
6. Documentar neste guia
