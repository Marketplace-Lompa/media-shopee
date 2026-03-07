---
name: review-uiux
description: Perform deep frontend UI/UX reviews focused on design system compliance, usability heuristics, WCAG AA accessibility, performance, architecture, and UI state completeness. Use when asked to review layouts, responsiveness, UX quality, design consistency, or frontend usability/accessibility risks.
---

# UI/UX Review — Skill Consolidada

Unifica três origens:
- `review-uiux` (Codex) — 7 dimensões, Nielsen, WCAG AA, formato de output estruturado
- `ux-high-level-agent` (Claude Frontend Agent) — auditoria visual, reconstrução high-fidelity, identidade visual, evolução de base de conhecimento
- `validate-frontend` (Codex) — Playwright headless, evidência por breakpoint

**Princípio central:** Evidence First — medir antes de concluir. Separar `Measured` | `Observed` | `Inferred`.

---

## Quando usar

- Review de layout, responsividade, qualidade de UX
- Auditoria de consistência do design system
- Validação de acessibilidade WCAG AA
- Captura de screenshots e evidência visual por breakpoint
- Reconstrução high-fidelity de referência (sem copiar código proprietário)
- Análise de identidade visual e síntese de guidelines
- Loop Build → Review → Fix antes de declarar etapa concluída

---

## Comportamento padrão

- **Read-only** — não edita código a menos que explicitamente solicitado
- Findings ordenados por severidade: `CRITICAL` → `HIGH` → `MEDIUM` → `LOW`
- Referências concretas a arquivo/linha quando possível
- Checks objetivos sobre opiniões estéticas subjetivas

---

## Workflow

### 1. Discovery — Mapear antes de julgar

1. Detectar design system e tokens (prioridade):
   - `globals.css` / `index.css` / `theme.ts` / `tokens.json` / `tailwind.config.*`
2. Detectar stack:
   - Framework (React/Next/Vue/Svelte)
   - UI library (shadcn/MUI/Chakra/etc.)
   - Styling (Tailwind/CSS Modules/styled-components/Vanilla CSS)
3. Se path específico fornecido, focar nele e dependências diretas
4. Respeitar padrões existentes do projeto — não impor sistema externo
5. Preferir evidência visual/runtime para layout e responsividade. Se ausente, marcar como assunção.

### 2. Captura de Evidência (Playwright headless — não-intrusivo)

**Precondição:** dev server rodando localmente.

```bash
# Capture multi-breakpoint sem abrir janela de browser
# Usar script: .agent/skills/ux-high-level-agent/scripts/playwright_ux_capture.mjs

node .agent/skills/ux-high-level-agent/scripts/playwright_ux_capture.mjs \
  --url http://localhost:<porta> \
  --out-dir /tmp/ux-review \
  --label <slug>
```

**Breakpoints obrigatórios:**
- Desktop: 1440×900
- Tablet:  834×1112
- Mobile:  390×844

**Pontos de scroll:** hero, mid, bottom de cada página relevante.

### 3. Avaliar em 7 Dimensões

Severidades: `CRITICAL` | `HIGH` | `MEDIUM` | `LOW`

#### 3.1 Design System Compliance
- Uso de tokens vs values hardcoded ("magic numbers")
- Consistência de spacing/radius/shadow/typography
- Uso semântico de cores (feedback, surface, text, border)
- Reutilização de primitivas UI estabelecidas

#### 3.2 UX & Usabilidade — Heurísticas Nielsen
- Visibilidade do status do sistema
- Controle e reversibilidade do usuário
- Consistência e padrões
- Prevenção e recuperação de erros
- Reconhecimento em vez de memorização
- Design minimalista
- CTA principal sempre visível e com hierarquia clara

#### 3.3 Acessibilidade (WCAG 2.1 AA)
- Elementos semânticos e labels corretos
- Comportamento de teclado/foco e `:focus-visible`
- Contraste: 4.5:1 texto, 3:1 componentes UI
- Acessibilidade de formulários e clareza para screen readers
- Qualidade de alt text
- Reflow/zoom até 400% sem quebrar fluxos principais
- Keyboard trap em dialogs/modais + comportamento Esc
- `aria-live` em feedback assíncrono
- Landmarks semânticos: `header`, `main`, `nav`, `footer`

#### 3.4 Performance Percebida
- Imports pesados e peso client-side evitável
- Render churn e dependências incorretas de hooks
- Keys de lista e rendering instável
- Otimização de imagens e layout shifts
- Skeleton screens vs spinners para conteúdo previsível
- Metas: `LCP < 2.5s`, `CLS < 0.1`, `INP < 200ms`
- Botões de submit: desabilitar durante processamento + spinner inline

#### 3.5 Motion & Qualidade de Interação
- Evitar motion decorativo que compete com conclusão de tarefa
- `prefers-reduced-motion` obrigatório em animações não-essenciais
- Verificar que transições de enter/exit não quebram feedback de estado
- Touch targets ≥ 40px no mobile

#### 3.6 Arquitetura & Padrões
- Tamanho e coesão de componentes
- Separação de UI / dados / lógica de negócio
- Prop drilling e limites de estado
- Type safety e cobertura de error boundary

#### 3.7 Completude de Estados de UI
Verificar em todo componente que consome dados:
- `loading` — skeleton ou spinner contextual
- `empty` — mensagem + ação orientadora
- `error` — mensagem específica + sugestão de recuperação
- `partial/degraded` — degradação graciosa
- `success` — confirmação visual de ação concluída

### 4. Qualidade Visual — Quick Rubric

| Eixo | Check |
|---|---|
| Hierarquia | Título domina sem competir com nav/ornamentos |
| Ritmo | Spacing segue escala previsível (8/12/16/24/32) |
| Superfície | Raios, sombras e bordas coerentes entre cards/inputs/modais |
| Tipografia | Escala clara por função; comprimento de linha legível |
| Densidade | Mobile simplificado vs comprimido |
| Responsivo | Sem overflow horizontal; reflows respeitam prioridade |

**Failure modes comuns:**
- Hero forte + CTA fraco ou distante
- Overlay/collage invadindo headline/CTA no mobile
- Cards coloridos com texto sem contraste suficiente
- Motion sem sincronismo (parece bug)
- Header sticky com blur excessivo degradando legibilidade

### 5. Identidade Visual (quando solicitado)

Extrair assinatura visual dominante:
- Tipo de contraste e paleta
- Tipografia: peso, escala, ritmo
- Linguagem de superfícies: cards, bordas, sombras, blur
- Composição: grid, editorial, bento, collage
- Tom: corporativo, playful, disruptivo, minimalista
- Motion/pointer signatures

Sintetizar em guidelines acionáveis:
- Princípios
- Tokens visuais
- Padrões de componentes
- Guardrails por breakpoint
- Anti-padrões a evitar

---

## Formato de Output

```markdown
# UI/UX Review — [scope]

**Stack**: ...
**Design System**: ...
**Evidência**: Playwright headless / Observação / Inferência

## Score Geral: X/10

## Findings por Severidade

### CRITICAL
- [ID] `arquivo:linha` — problema, impacto, ação recomendada.

### HIGH
- ...

### MEDIUM
- ...

### LOW
- ...

## Nielsen's Heuristics Score
| Heurística | Score | Nota |
|---|---|---|

## UI States Coverage
| Componente | Loading | Empty | Error | Success |
|---|---|---|---|---|

## Top 3 Quick Wins
1. ...
2. ...
3. ...

## Top 3 Melhorias Estratégicas
1. ...
2. ...
3. ...
```

---

## Loop Build → Review (obrigatório para trabalho de UI)

1. Terminar etapa importante de UI
2. Rodar dev server localmente
3. Capturar screenshots Playwright por breakpoint
4. Fazer análise crítica antes de seguir
5. Corrigir problemas relevantes antes de declarar etapa concluída

---

## Design Tokens Reference (hierarquia de 3 níveis)

Base global: `.agent/skills/ux-high-level-agent/base-conhecimento/references/design-tokens-system.md`

**Princípios:**
- Semantic First — nunca usar primitivos diretamente em componentes
- Fewer is Better — subset mínimo, expandir sob demanda
- Theme-Agnostic Naming — `surface-primary` não `white-background`
- Dark mode: remapear semanticamente, não inverter; superfícies elevadas ficam mais claras

**Dark mode guardrails:**
- Não usar preto puro `#000` como background (`gray-900/950`)
- Sombras perdem eficácia em dark — usar bordas sutis
- Testar contraste AA em ambos os modos

---

## Component Patterns Reference

18 patterns documentados em: `.agent/skills/ux-high-level-agent/base-conhecimento/references/component-patterns.md`

Highlights para este projeto (Studio de geração de imagens):
- **Chat input com upload** → Form System (pattern 13)
- **Galeria de resultados** → Metric Cards / Grid (pattern 4)
- **Reference Pool panel** → Sidebar Navigation (pattern 14d) + Bento Grid (pattern 7)
- **Parâmetros de geração** → Tabs (pattern 14c) + Form System (pattern 13)
- **Feedback de geração** → Progress Indicator (pattern 15c) + Toast (pattern 15a)
- **Estados de loading** → Skeleton (pattern 16)

---

## Regras Absolutas

- Findings acionáveis, curtos e testáveis
- Preferir "o que mudar" sobre comentário abstrato
- Se não há problemas relevantes, declarar explicitamente e listar riscos residuais
- Não propor mudanças que conflitem com padrões atuais do projeto
- Não impor escolhas de arquitetura/biblioteca que o projeto não usa
- Não enforçar fórmulas estéticas (golden ratio etc.) como requisitos duros
- Cursor customizado: ativar apenas em `pointer: fine` (desktop), testar sem degradar inputs
