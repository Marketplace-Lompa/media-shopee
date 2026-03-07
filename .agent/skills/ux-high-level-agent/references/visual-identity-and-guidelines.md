# Visual Identity Analysis and Guidelines Synthesis

## Purpose

Expandir o escopo do agente para:

- analisar identidade visual de referencias
- traduzir estilo em guidelines acionaveis
- aumentar repertorio criativo com fontes externas curadas

Sem copiar codigo proprietario ou replicar layouts de forma literal.

## When to Use

Usar quando o pedido envolver:

- “quero uma direção visual”
- “analise a identidade visual”
- “crie guidelines”
- “deixe mais premium / mais alternativo / mais corporativo”
- “buscar referências”

## Inputs (Examples)

- URL de referencia (Framer/site publicado)
- screenshots
- produto/domínio (SaaS, fintech, AI agency etc.)
- objetivo de tom (clean, disruptivo, playful, editorial)
- referencias externas (ex.: [Behance UI/UX](https://www.behance.net/galleries/ui-ux))

## Output Expected (Minimum)

Entregar pelo menos:

1. **Leitura de identidade visual**
2. **Classificacao de estilo** (eixos + niveis)
3. **Guidelines sintetizadas**
4. **Guardrails responsivos**
5. **Anti-padroes / riscos**

## Identity Analysis Framework (Practical)

## 1. Brand Signal / First Impression

- Que sensacao domina? (`premium`, `experimental`, `corporativo`, `playful`, `editorial`, `utilitario`)
- Onde a marca “aparece” mais forte?
  - tipografia
  - cor
  - composicao
  - motion
  - cursor/pointer

## 2. Typography Signature

- Escala do hero (contida vs agressiva)
- Relação entre headline/subheadline
- Peso dominante (600/700/800)
- Tracking / densidade
- Ritmo de linhas (rag / line breaks)

## 3. Color and Contrast Model

- Fundo dominante (light / dark / hybrid)
- Cores de acento (1-2 principais vs paleta extensa)
- Contraste de CTA
- Uso de cor como:
  - sinal
  - superfície
  - identidade

## 4. Surface Language

- Raios (duro vs arredondado)
- Bordas (invisíveis, suaves, fortes)
- Sombras (suaves, profundas, editoriais)
- Blur/transparência (glass, frosted)
- Texturas (dots, gradients, patterns)

## 5. Composition System

- Grid rígido vs composição editorial
- Bento / split / collage / sobreposição
- Hierarquia espacial (qual bloco “puxa” o olhar)
- Ritmo vertical entre seções

## 6. Component Signature

- Nav (capsule, sticky glass, minimal)
- Hero (mockup, collage, typographic, proof-led)
- Cards (densos, clean, experimental)
- CTAs (filled/ghost/text)
- Widgets/promo/floating elements
- Cursor customizado (se existir)

## 7. Motion / Interaction Signature

- Scroll-linked motion?
- Hover states fortes ou discretos?
- Micro-motion funcional vs decorativa?
- Pointer customizado?

## Guidelines Synthesis Template (Recommended)

## A. Design Principles (3-6)

Exemplo:

- “Clareza primeiro, ornamentação depois”
- “Impacto tipográfico com CTA sempre preservado”
- “Contraste alto com superfícies controladas”

## B. Visual Tokens (starter)

- paleta base (bg, surface, text, muted, accent)
- escala tipográfica (hero, h2, body, meta)
- radius scale
- shadow scale
- spacing scale

## C. Component Guidelines

- Nav
- Hero
- Cards
- CTAs
- Forms
- Footer

Para cada componente:

- papel de UX
- regras
- variações permitidas
- o que evitar

## D. Responsive Guardrails

- o que pode mudar no mobile (stack, reorder, hide, simplify)
- o que nao pode quebrar (headline, CTA, fluxo principal)
- tratamento de overlays/floating widgets

## E. Motion and Pointer Guardrails (if applicable)

- quando usar motion expressivo
- limites de duração/easing
- cursor customizado desktop-only
- fallback para touch e `prefers-reduced-motion`

## F. Anti-Patterns

- copiar visual sem entender hierarquia
- exagerar ornamentos e perder CTA
- usar referências externas como blueprint literal

## Using Behance as Reference (Safe and Useful)

Fonte sugerida de repertorio visual:

- [Behance UI/UX Galleries](https://www.behance.net/galleries/ui-ux)

Como usar corretamente:

- coletar sinais de linguagem visual (mood, ritmo, composição, tratamento de tipografia)
- comparar múltiplas referências para evitar imitação de uma peça só
- traduzir em guidelines abstratas e tokens
- criar implementação original

Como **não** usar:

- copiar layout/blocos 1:1
- reproduzir assets/propriedade visual sem adaptação
- tratar uma referência como código de produção

## Reference Platforms (Padrao Ouro, via Cerebro Global)

Catalogo principal de fontes para repertorio e benchmark:

- `/Users/lompa-marketplace/Documents/Design/base-conhecimento-principal-ux/references/design-reference-platforms-catalog.md`

Uso operacional:

- UX funcional: priorizar `Mobbin` / `Page Flows` / `Pttrns`
- Direcao visual web: combinar `Behance` + `Lapa`/`Awwwards`/`One Page Love`
- Consistencia e acessibilidade: cruzar com `design systems oficiais`

## Evidence Tags (Always)

Ao documentar identidade/guidelines, marcar:

- `Measured`
- `Observed`
- `Inferred`

Isso evita transformar gosto pessoal em “regra” sem base.

## Behance UI/UX Deep-Dive (Operational Learnings)

Relatorio detalhado promovido no cerebro global:

- `/Users/lompa-marketplace/Documents/Design/base-conhecimento-principal-ux/references/visual-identity-behance-uiux-trend-scan.md`

Aplicacao operacional na skill:

- Use Behance para **clusterizar estilo**, nao para copiar uma peça.
- Extraia sinais por eixo:
  - tipografia
  - contraste
  - composição
  - prova de produto (mockups/dashboard)
  - intensidade de branding
- Para pedidos “mais alternativo”, combine:
  - tipografia forte
  - composição editorial
  - CTA preservado
  - overlay com guardrail mobile
- Para pedidos SaaS/AI, priorize `proof-led`:
  - hero + screenshot/mockup cedo
  - métricas/logos/prova
  - ornamentação subordinada à clareza
