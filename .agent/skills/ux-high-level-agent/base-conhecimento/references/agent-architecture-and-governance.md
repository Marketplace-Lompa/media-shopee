# Agent Architecture and Governance (UX Skill)

## Goal

Projetar um agente/skill de UX de alto nivel que seja:

- migravel entre repositorios
- orientado por evidencia visual
- evolutivo via Markdown
- pratico para entrega (nao apenas teoria)

## Knowledge Layers (Aprimorado)

### Layer 1: Trigger metadata
- `SKILL.md` frontmatter (`name`, `description`)
- Funcao: disparar a skill no contexto correto

### Layer 2: Operating workflow
- `SKILL.md` body
- Funcao: definir comportamento padrao, regras e orquestração de Artefatos Canônicos

### Layer 3: Reference knowledge (Memory Cascade)
- `references/*.md` (Global Core) + `./ux-context/*.md` (Local Domain)
- Funcao: aprofundar heuristicas, casos e padroes
- Regra: Precedência `Local > Global`. Todo achado deve citar sua `provenance`.

### Layer 4: Capability-Based Probe (Abstração)
- `scripts/*` + Adaptadores (ex: Playwright, Appium)
- Funcao: captura de evidência baseada em capacidades (`visual_capture`, `ui_tree_inspection`)
- Regra: O agente solicita *capacidades*, o adaptador as provê. Sem lock-in de ferramenta.

### Layer 5: Reusable output assets & Translators
- `assets/*` + `translators/`
- Funcao: templates base e tradutores de tokens para stacks específicas
- Regra: Saída deve incluir `unsupported_features_report` se o tradutor falhar na conversão técnica.

## Operational Modes (Conceptual)

### Mode A: Discovery
- Produz: `EvidenceBundle` (captura inicial) + Mapa de Hipóteses.
- Foco: Entender stack e intenção via `UX Profile`.

### Mode B: Reconstruction
- Produz: `ScreenIntentSpec` (Blueprint abstrato).
- Foco: Implementar estrutura e lógica visual agnóstica.

### Mode C: Review
- Produz: `UXFinding` (vinculado à evidência).
- Foco: Crítica técnica baseada em heurísticas e bias do projeto.

### Mode D: Calibration
- Ajusta: `UX Profile` e pesos de decisão.
- Foco: Refinar o bias sem alterar o Core Knowledge.

### Mode E: Learning
- Produz: Candidatos a conhecimento para promoção.
- Foco: Registrar caso e sugerir padrões para o Global Core.

## Architectural Contracts (Transversal)

Para garantir o desacoplamento, a comunicação entre camadas e modos ocorre via **Artefatos Canônicos**:
- `EvidenceBundle`: Dados brutos da prova (imagem + metadata).
- `UXFinding`: Relato estruturado de dor ou melhoria.
- `TokenSpec`: Definição de design pronta para o Tradutor (L5).

## Non-Negotiable Rules (Preservação + Evolução)

- **Validação Real:** Validar por comportamento real da UI, nao apenas por inspeção de codigo.
- **Entrega Funcional:** Entregar codigo original funcional.
- **Transparência Técnica:** Manter honestidade sobre limites da simulacao e declarar o que foi medido vs inferido.
- **Rastreabilidade:** Garantir rastreabilidade total: toda decisão deve apontar para uma evidência no `EvidenceBundle` (via ID único).
- **Capability Negotiation:** Provedores L4 devem expor capacidades antes da execução para o agente degradar com elegância se necessário.
- **Ética e Segurança:** Nao burlar protecoes nem tentar obter codigo proprietario.

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
