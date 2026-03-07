# Agent Architecture and Governance (UX Skill)

## Goal

Projetar um agente/skill de UX de alto nivel que seja:

- migravel entre repositorios
- orientado por evidencia visual
- evolutivo via Markdown
- pratico para entrega (nao apenas teoria)

## Knowledge Layers (Recommended)

## Layer 1: Trigger metadata

- `SKILL.md` frontmatter (`name`, `description`)
- Funcao: disparar a skill no contexto correto

## Layer 2: Operating workflow

- `SKILL.md` body
- Funcao: definir comportamento padrao, regras e ordem de execucao

## Layer 3: Reference knowledge (Markdown)

- `references/*.md`
- Funcao: aprofundar heuristicas, casos, padroes, governanca, checklists
- Regra: manter modular e navegavel

## Layer 4: Automation (future scripts)

- `scripts/*`
- Funcao: captura Playwright, probes, diffs, relatorios
- Regra: adicionar somente quando o workflow estiver repetitivo

## Layer 5: Reusable output assets (future)

- `assets/*`
- Funcao: templates base, componentes starter, tokens, boilerplates

## Operational Modes (Conceptual)

## Mode A: Discovery

- Entender objetivo, referencia, stack e criterio de sucesso.
- Coletar evidencia visual/DOM.

## Mode B: Reconstruction

- Implementar estrutura de UI e comportamento principal.
- Priorizar componentes e sistema visual.

## Mode C: Review

- Rodar local + Playwright + screenshots por etapa.
- Fazer critica de UX com findings concretos.

## Mode D: Calibration

- Medir motion/transform quando necessario para fidelidade.
- Ajustar curvas, timings, hierarquia, densidade.

## Mode E: Learning

- Registrar caso e promover padroes.

## Non-Negotiable Rules

- Declarar o que foi medido vs inferido.
- Nao burlar protecoes nem tentar obter codigo proprietario.
- Entregar codigo original funcional.
- Validar por comportamento real da UI, nao apenas por inspeção de codigo.
- Manter honestidade sobre limites da simulacao.

## Case Ingestion Protocol

Ao finalizar um caso:

1. Atualizar `case-XX-*.md`
2. Anotar descobertas tecnicas raras (ex.: wrapper real do transform)
3. Promover heuristicas para guias gerais se forem reutilizaveis
4. Revisar `SKILL.md` se o workflow padrao mudou

## Skill Evolution Triggers

Atualizar o skill quando ocorrer:

- novo tipo de layout recorrente
- novo padrao de motion recorrente
- falha repetida em revisoes de UX
- novo script de automacao comprovadamente util
- novo requisito de acessibilidade/responsividade

## Definition of a Good Iteration

Uma iteracao e considerada boa quando:

- aumenta a taxa de acerto de UX (menos retrabalho visual)
- reduz ambiguidade do processo
- melhora reproducao de componentes/animacoes
- adiciona conhecimento reutilizavel sem inflar demais o `SKILL.md`
