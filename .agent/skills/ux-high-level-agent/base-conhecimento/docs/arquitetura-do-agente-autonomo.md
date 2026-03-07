# Arquitetura do Agente Autonomo de UX (Modular e Acoplavel)

## Objetivo de arquitetura

Projetar um agente de UX/UI que:

- seja **modular**
- seja **abstrato o suficiente** para qualquer dominio (SaaS, fintech, AI, e-commerce, dashboard)
- seja **migravel entre repositorios**
- mantenha **aprendizado acumulado**
- produza **evidencia visual + implementacao original**

## Modelo de camadas (visao macro)

## Camada 1: Orquestracao (runtime da conversa)

Responsabilidade:

- entender objetivo do usuario
- decidir etapa atual (auditoria, rebuild, review, aprendizado)
- manter fluxo por etapas

Entrada:

- URL de referencia / screenshot / repo local / objetivo

Saida:

- plano por etapas + entregaveis

## Camada 2: Skill Operacional (procedimentos)

Responsabilidade:

- definir workflow padrao
- impor regras de qualidade
- orientar uso de scripts e referencias

Implementacao atual:

- `/Users/lompa-marketplace/Documents/Design/skills/ux-high-level-agent/SKILL.md`

## Camada 3: Base Global (cerebro)

Responsabilidade:

- guardar conhecimento reutilizavel
- classificar estilos
- registrar casos e promocoes de padroes

Implementacao atual:

- `/Users/lompa-marketplace/Documents/Design/base-conhecimento-principal-ux`

## Camada 4: Scripts/Pipeline (automacao)

Responsabilidade:

- capturas Playwright
- sanitizacao de overlays
- metricas por viewport
- probes de motion/transform

Exemplo:

- `/Users/lompa-marketplace/Documents/Design/skills/ux-high-level-agent/scripts/playwright_ux_capture.mjs`

## Camada 5: Projetos de execucao (casos)

Responsabilidade:

- conter implementacao local de cada caso
- rodar site local
- armazenar `analysis/` e screenshots de validacao

Exemplos:

- `/Users/lompa-marketplace/Documents/Design/payble-ux-sim`
- `/Users/lompa-marketplace/Documents/Design/taaskhub-ux-sim`
- `/Users/lompa-marketplace/Documents/Design/opscale-ux-sim`

## Camada 6: Biblioteca de exemplos (snapshots)

Responsabilidade:

- preservar bases reutilizaveis sem `node_modules/dist`
- acelerar novos casos

Local:

- `/Users/lompa-marketplace/Documents/Design/skills/ux-high-level-agent/exemplos`

## Contratos entre modulos (importante)

Para ser acoplavel em qualquer projeto, cada modulo precisa falar por contratos simples:

### Contrato A: Entrada de caso

Campos minimos:

- `case_id` (ex.: `case-03`)
- `reference_url`
- `goal` (`audit`, `rebuild`, `refine`)
- `local_port` (quando houver app local)
- `output_dirs` (`analysis`, `ux-review`)

### Contrato B: Evidencia visual

Entregaveis minimos:

- screenshots desktop/tablet/mobile
- metadados JSON por captura
- resumo (`summary.json`)
- observacoes UX por etapa

### Contrato C: Conhecimento promovido

Entregaveis minimos:

- `references/case-XX-*.md`
- classificacao de estilo
- atualizacao de indices

## Principios de abstracao (para qualquer repo)

### 1. Separar conhecimento de implementacao

- Conhecimento fica em Markdown (global)
- Implementacao fica no projeto do caso

Beneficio:

- voce troca stack sem perder o cerebro

### 2. Separar workflow de ferramentas

Workflow (descobrir -> reconstruir -> validar -> aprender) e estavel.
Ferramentas (React/Vite/Next/Playwright/etc.) podem variar.

### 3. Separar heuristicas de estilo por taxonomia

Nao depender de nomes de templates.
Classificar por eixos (`minimalista`, `profissional_clean`, etc.).

### 4. Separar script generico de script de caso

- script generico = reutilizavel (`playwright_ux_capture.mjs`)
- script de caso = medicao puntual (ex.: probe de tilt)

## Padrao de organizacao (recomendado para qualquer repo)

```text
<repo>/
├── skills/
│   └── ux-high-level-agent/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── exemplos/
├── base-conhecimento-principal-ux/
│   ├── README.md
│   ├── INDEX.md
│   ├── docs/
│   ├── indices/
│   ├── taxonomias/
│   └── references/
├── case-runs/
│   └── case-XX-<slug>-analysis/
└── <projetos-locais>/
    └── <case>-ux-sim
```

## Regra de autonomia (sem perder controle)

O agente pode executar etapas sozinho, mas deve:

- declarar etapa atual
- validar UI por screenshots Playwright em marcos importantes
- registrar criticamente o que esta bom e o que precisa ajuste
- atualizar conhecimento ao final do caso

Isso evita autonomia “cega” e transforma o processo em sistema auditavel.
