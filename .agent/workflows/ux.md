---
description: Dispara a skill review-uiux consolidada para auditoria de frontend. Use /ux para revisão manual, ou é acionado automaticamente quando o trabalho envolve UI/UX/frontend.
---

# Workflow /ux — UI/UX Review

## Quando usar

- Explicitamente via comando `/ux`
- **Automaticamente** ao final de qualquer etapa que crie ou modifique:
  - Componentes React (`.tsx`, `.jsx`)
  - Estilos (`.css`, `index.css`, `globals.css`)
  - Páginas inteiras ou layouts
  - Sistema de design / tokens
  - O frontend em geral (`app/frontend/`)

---

## Passos

### 1. Ler a skill consolidada

Leia o arquivo `.agent/skills/review-uiux/SKILL.md` antes de executar qualquer análise.

### 2. Identificar o escopo

Determine o que será revisado:
- Se o usuário especificou um componente/arquivo → focar nele
- Se foi chamado após uma etapa de build → revisar tudo que foi alterado nessa etapa
- Se chamado sem contexto → revisar o frontend completo (`app/frontend/src/`)

### 3. Discovery — mapear stack e design system

Antes de julgar, identificar:
- Arquivo de tokens/estilos: `app/frontend/src/index.css` ou equivalente
- Framework e bibliotecas em uso
- Padrões existentes no projeto (não impor sistema externo)

### 4. Capturar evidência visual (se o servidor estiver rodando)

Se o frontend estiver acessível localmente (ex: `http://localhost:5173`):

```bash
# Verificar se está no ar
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173

# Se estiver no ar, capturar screenshots headless por breakpoint:
# Desktop 1440×900 | Tablet 834×1112 | Mobile 390×844
node .agent/skills/ux-high-level-agent/scripts/playwright_ux_capture.mjs \
  --url http://localhost:5173 \
  --out-dir /tmp/ux-review \
  --label studio-frontend
```

Se o servidor não estiver rodando, executar análise estática de código.

### 5. Avaliar nas 7 dimensões

Conforme definido na skill `review-uiux`:

1. **Design System Compliance** — tokens vs magic numbers
2. **UX & Usabilidade** — heurísticas Nielsen
3. **Acessibilidade** — WCAG 2.1 AA
4. **Performance** — imports, render, LCP/CLS/INP
5. **Motion & Interação** — `prefers-reduced-motion`, touch targets ≥ 40px
6. **Arquitetura** — coesão, separação de camadas, type safety
7. **Completude de estados** — loading, empty, error, success

### 6. Entregar o relatório

Formato padrão da skill:

```markdown
# UI/UX Review — [escopo]

**Stack**: React + TypeScript + Vite + Framer Motion
**Design System**: Vanilla CSS + tokens customizados
**Evidência**: Playwright headless / Análise estática

## Score Geral: X/10

## Findings por Severidade
### CRITICAL | HIGH | MEDIUM | LOW

## Nielsen's Heuristics Score

## UI States Coverage

## Top 3 Quick Wins

## Top 3 Melhorias Estratégicas
```

### 7. Agir nos findings (se autorizado)

- **CRITICAL / HIGH**: corrigir antes de prosseguir para próxima etapa
- **MEDIUM**: registrar e corrigir no próximo ciclo
- **LOW**: anotar para backlog
- Após correção: re-capturar screenshots e confirmar resolução

---

## Integração com o Loop Build → Review

Este workflow é parte do ciclo obrigatório de qualidade:

```
Build UI → /ux → Fix CRITICAL/HIGH → Re-validate → Próxima etapa
```

Nunca declarar uma etapa de frontend concluída sem ter passado pelo `/ux`.

---

## Referências rápidas

| Recurso | Caminho |
|---|---|
| Skill consolidada | `.agent/skills/review-uiux/SKILL.md` |
| Design tokens | `.agent/skills/ux-high-level-agent/base-conhecimento/references/design-tokens-system.md` |
| Component patterns | `.agent/skills/ux-high-level-agent/base-conhecimento/references/component-patterns.md` |
| Design heuristics | `.agent/skills/ux-high-level-agent/base-conhecimento/references/design-rules-and-heuristics.md` |
| Accessibility | `.agent/skills/ux-high-level-agent/base-conhecimento/references/accessibility-and-inclusion.md` |
| UI states | `.agent/skills/ux-high-level-agent/base-conhecimento/references/ux-states-and-edge-cases.md` |
| Playwright script | `.agent/skills/ux-high-level-agent/scripts/playwright_ux_capture.mjs` |
