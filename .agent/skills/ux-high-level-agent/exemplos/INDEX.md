# Exemplos (Project Library)

## Purpose

Guardar projetos completos criados durante casos reais como base de referencia pratica.
Usar estes exemplos para acelerar novas reconstrucoes, validar padroes de componentes e reaproveitar scripts de analise.

## Rules

- Salvar snapshots de projetos sem dependencias de runtime/build (`node_modules`, `dist`).
- Preservar `src/`, `scripts/`, `analysis/` e configs principais.
- Nomear por caso para manter rastreabilidade.
- Atualizar este indice sempre que um novo exemplo for adicionado.

## Current Examples

### case-01-payble-ux-sim

- Origem: reconstrução high-fidelity inspirada em landing Framer fintech (Payble-like).
- Inclui:
  - UI React/Vite com motion e mockup scroll-linked
  - scripts Playwright de captura/analise/probe de transform
  - screenshots e artefatos de review UX
- Porta padrao no projeto: `3005`

### case-02-taaskhub-ux-sim

- Origem: reconstrução local inspirada em `taaskhub.framer.website` com foco em hero SaaS, grids de páginas e linguagem visual clean/playful.
- Inclui:
  - UI React/Vite com seções de showcases, homepages e inner pages simuladas
  - screenshots Playwright de revisão UX (desktop/tablet/mobile)
- ajustes de breakpoint guiados por review (ex.: remoção de ornamentos do hero no mobile)
- Porta padrao no projeto: `3006`

### case-03-opscale-ux-sim

- Origem: reconstrução local inspirada em `opscale.framer.website`, com linguagem SaaS/AI mais enterprise, dashboard mockup e bandas de contraste (hero claro + trust band escura).
- Inclui:
  - UI React/Vite com dashboard mockup, nav flutuante escura, integrações/orbit e seções modulares
  - capturas Playwright de revisão UX (desktop/tablet/mobile)
  - validação de overflow e ajustes responsivos da composição
- Porta padrao no projeto: `3007`

### case-04-sanny-ux-sim

- Origem: reconstrução local inspirada em `sanny-template.framer.website`, com direção dark/editorial, tipografia oversized e layout mais alternativo.
- Inclui:
  - UI React/Vite com hero editorial, card promocional estilo collage e seções em painéis escuros/claro
  - revisões UX Playwright em múltiplas passadas (mobile hero/promo ajustado)
  - validação desktop/tablet/mobile sem overflow horizontal
- Porta padrao no projeto: `3008`

## Naming Convention

- `case-01-<slug>`
- `case-02-<slug>`
- `case-03-<slug>`
- `case-04-<slug>`

## Suggested Future Examples

- Dashboard analytics com densidade alta (desktop/mobile)
- E-commerce product page com motion orientado a conversao
- Design system playground com tokens + componentes base
