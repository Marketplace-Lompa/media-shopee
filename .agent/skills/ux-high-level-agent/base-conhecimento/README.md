# Base Global UX/Design (Cerebro do Agente)

## O que e isto

Esta pasta e a base global de conhecimento de UX/Design do agente autonomo.
Ela e independente da skill e serve como memoria evolutiva, classificacao de estilos e protocolo de aprendizado.

- **Skill** = camada operacional (como executar)
- **Base global** = cerebro (o que aprendemos, como organizamos, como reaproveitamos)

## Objetivo

Ser modular e abstrata o suficiente para acoplar em qualquer projeto/repositorio sem depender de uma stack especifica.

## Leitura recomendada (ordem)

1. `INDEX.md` (mapa geral)
2. `docs/arquitetura-do-agente-autonomo.md` (estrutura e modulos)
3. `docs/fluxo-de-aprendizado-e-evolucao.md` (como o agente aprende)
4. `docs/guia-de-acoplamento-em-projetos.md` (como plugar em qualquer repo)
5. `docs/integracao-mcp-codex-review.md` (como se integra ao Codex via MCP)
6. `taxonomias/style-levels.md` (classificacao de estilo)
7. `indices/cases-index.md` e `indices/cases-by-style.md` (discoverability)

## Estrutura

- `references/` = casos e guias tecnicos
- `indices/` = catalogos navegaveis
- `taxonomias/` = classificacoes padronizadas
- `docs/` = documentacao de arquitetura, operacao e acoplamento

## Regra principal

Todo novo caso deve atualizar:

- arquivo de caso em `references/`
- classificacao de estilo
- indices de casos
- snapshot em `exemplos/` (quando houver projeto local)

## Relacao com a skill

A skill (`/Users/lompa-marketplace/Documents/Design/skills/ux-high-level-agent/SKILL.md`) deve permanecer enxuta.
Detalhes estruturais e de governanca vivem aqui para nao inflar a skill e facilitar migracao entre repositorios.
