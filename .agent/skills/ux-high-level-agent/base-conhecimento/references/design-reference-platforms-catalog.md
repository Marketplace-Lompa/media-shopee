# Design Reference Platforms Catalog (Global Brain)

## Purpose

Catalogar plataformas de referencia para alimentar o agente modular de UX/Design com mais repertorio, sem depender de uma unica fonte.

Este catalogo serve para:

- ampliar repertorio visual
- melhorar analise de identidade visual
- fortalecer benchmark de UX real
- separar referencia de producao real vs portfolio conceitual

## Usage Rule (Important)

Usar plataformas como **insumo de sinais** e **padroes**, nao como blueprint literal.

Sempre registrar:

- `Measured` (captura, metadados, tags, filtros)
- `Observed` (leitura visual)
- `Inferred` (guidelines sintetizadas)

## Source Categories (Recommended for the Agent)

## A. Real Product UI / UX Flows (Alta prioridade)

Melhor para:

- fluxos reais
- benchmark de UX
- padrões de onboarding/login/checkout/settings
- comportamento multi-step

Plataformas:

- `Mobbin` - [mobbin.com](https://mobbin.com)
- `Page Flows` - [pageflows.com](https://pageflows.com)
- `Pttrns` - [pttrns.com](https://www.pttrns.com/)
- `Refero` - [refero.design](https://refero.design/)
- `Screenlane` (atualmente redireciona para Page Flows) - [screenlane.com](https://screenlane.com/)
- `PageCollective` (historico / pode variar disponibilidade) - [pagecollective.com](https://pagecollective.com/)

Heuristica de uso:

- preferir essas fontes quando a pergunta for de UX funcional ("como apps reais resolvem X?")

## B. Website / Landing Inspiration (Alta prioridade)

Melhor para:

- direcao visual de marketing site
- layout, hero, grids, sections
- combinacoes tipografia + CTA + mockup

Plataformas:

- `Behance UI/UX Gallery` - [behance.net/galleries/ui-ux](https://www.behance.net/galleries/ui-ux)
- `Awwwards` - [awwwards.com](https://www.awwwards.com/)
- `Land-book` - [land-book.com](https://land-book.com/)
- `Lapa Ninja` - [lapa.ninja](https://www.lapa.ninja/)
- `One Page Love` - [onepagelove.com](https://onepagelove.com/)
- `Godly` - [godly.website](https://godly.website/)
- `SiteInspire` - [siteinspire.com](https://www.siteinspire.com/)

Heuristica de uso:

- preferir multiplas referencias por cluster (3-5+)
- converter em guidelines antes de construir

## C. Visual Identity / Branding (Media-Alta prioridade)

Melhor para:

- linguagem de marca
- direcao tipografica
- sistemas visuais
- identidade aplicada em digital

Plataformas:

- `Behance` (branding + digital hybrid) - [behance.net](https://www.behance.net/)
- `Dribbble` (bom para sinais e acabamento visual; menor confianca para UX completo) - [dribbble.com](https://dribbble.com/)
- `Brand New (UnderConsideration)` - [underconsideration.com/brandnew](https://www.underconsideration.com/brandnew/)
- `BP&O` - [bpando.org](https://bpando.org/)
- `Fonts In Use` - [fontsinuse.com](https://fontsinuse.com/)

Heuristica de uso:

- usar para assinatura visual e tom de marca
- validar UX estrutural em fontes de produto/website reais

## D. Design Systems / Guidelines Oficiais (Alta prioridade para consistencia)

Melhor para:

- acessibilidade
- fundamentos
- tokens
- componentes com rigor
- padroes de plataforma

Plataformas:

- `Material Design 3` - [m3.material.io](https://m3.material.io/)
- `Apple Human Interface Guidelines` - [developer.apple.com/design/human-interface-guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- `Atlassian Design System` - [atlassian.design/design-system](https://atlassian.design/design-system/)
- `Shopify Polaris` - [shopify.dev/docs/api/polaris](https://shopify.dev/docs/api/polaris)
- `IBM Carbon` - [carbondesignsystem.com](https://carbondesignsystem.com/)
- `Microsoft Fluent 2` - [fluent2.microsoft.design](https://fluent2.microsoft.design/)

Heuristica de uso:

- usar como "ancora de qualidade" quando o projeto estiver muito experimental

## E. Motion / Interactive Web Inspiration (Media prioridade)

Melhor para:

- narrativa interativa
- scroll motion
- microinteracoes
- referencias de front-end expressivo

Plataformas:

- `Awwwards` - [awwwards.com](https://www.awwwards.com/)
- `Godly` - [godly.website](https://godly.website/)
- `Lapa Ninja` (filtros 3D / categorias visuais) - [lapa.ninja](https://www.lapa.ninja/)
- `The FWA` - [thefwa.com](https://thefwa.com/)
- `CSS Design Awards` - [cssdesignawards.com](https://www.cssdesignawards.com/)

Heuristica de uso:

- aplicar motion como reforco de hierarquia, nao efeito por efeito

## F. Email / Lifecycle UX (Media prioridade, alto valor para growth)

Melhor para:

- emails transacionais
- onboarding lifecycle
- retention / CRM touchpoints

Plataformas:

- `Really Good Emails` - [reallygoodemails.com](https://www.reallygoodemails.com/)
- `Email Love` - [emaillove.com](https://emaillove.com/)
- `Page Flows` (emails tambem aparecem na plataforma) - [pageflows.com](https://pageflows.com/)

## G. Implementation-Adjacent UI Refs (Media prioridade)

Melhor para:

- transformar direcao visual em base implementavel
- aprender padroes de componente com codigo

Plataformas:

- `shadcn/ui` - [ui.shadcn.com](https://ui.shadcn.com/)
- `Radix UI` - [radix-ui.com](https://www.radix-ui.com/)
- `MUI` - [mui.com](https://mui.com/)
- `Mantine` - [mantine.dev](https://mantine.dev/)
- `Chakra UI` - [chakra-ui.com](https://chakra-ui.com/)

Regra:

- nao confundir biblioteca de componentes com referencia de identidade visual

## Priority Matrix for Ingestion

## Tier 1 (Sempre no loop)

- Behance UI/UX
- Mobbin
- Page Flows
- Lapa Ninja
- Awwwards
- 1 design system oficial relevante ao dominio (ex.: Polaris para admin, Material para mobile, HIG para Apple-first)

## Tier 2 (Conforme objetivo)

- Land-book
- One Page Love
- Godly
- Pttrns
- Refero
- Atlassian / Carbon / Fluent / outros sistemas

## Tier 3 (Especializado / ocasional)

- Email refs
- Branding refs (Brand New/BP&O/Fonts In Use)
- implementation-adjacent libs

## Confidence Model by Source Type

## High confidence for UX behavior

- Mobbin
- Page Flows
- Pttrns
- Refero

## High confidence for visual direction / trend scan

- Behance
- Awwwards
- Land-book
- Lapa Ninja
- One Page Love
- Godly

## High confidence for consistency / standards

- Material
- HIG
- Atlassian
- Polaris
- Carbon
- Fluent

## Lower confidence (use with caution)

- Dribbble-only decisions (visual polish alto, UX real menor evidencia)
- isolating a single portfolio shot and treating it as pattern evidence

## Ingestion Strategy (Agent-Ready)

## 1. Weekly scan (lightweight)

- 1 source de produto real (`Mobbin` ou `Page Flows`)
- 1 source de websites (`Lapa`, `Land-book`, `One Page Love`, `Awwwards`)
- 1 source de repertorio amplo (`Behance`)

Saida:

- `weekly-trend-scan-YYYY-MM-DD.md`
- 5-10 sinais visuais/UX
- 2-3 clusters emergentes

## 2. Case-driven scan (deep)

Quando surgir um caso novo (ex.: fintech AI, agency editorial):

- escolher `3-5` fontes relevantes
- capturar / extrair / classificar
- gerar guidelines especificas do caso

## 3. Pattern promotion

Se um sinal aparecer em varios casos:

- promover para `design-rules-and-heuristics.md`
- promover para `component-patterns.md`
- atualizar `taxonomias/style-levels.md` se necessario

## Legal / Ethical / Operational Guardrails

- Respeitar ToS e robots quando aplicavel
- Preferir captura visual e metadados a scraping agressivo
- Nao redistribuir assets proprietarios
- Nao copiar layout/codigo 1:1
- Usar referencias para direcao original

## Notes on Source Reliability

- `Screenlane` atualmente aparece redirecionando para `Page Flows` em consultas recentes; tratar como legado/alias operacional.
- `SiteInspire` pode bloquear alguns crawlers (403), mas continua util como fonte manual.
- Plataformas mudam filtros, paywalls e disponibilidade; validar antes de depender no pipeline.

