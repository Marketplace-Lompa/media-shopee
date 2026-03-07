# Guia de Acoplamento em Qualquer Projeto

## Objetivo

Acoplar este agente/skill de UX em um novo repositorio sem reescrever a arquitetura.

## Minimo necessario para operar

### 1. Skill operacional

Copiar:

- `/Users/lompa-marketplace/Documents/Design/skills/ux-high-level-agent`

### 2. Base global (cerebro)

Copiar:

- `/Users/lompa-marketplace/Documents/Design/base-conhecimento-principal-ux`

### 3. Pasta de casos/artefatos

Criar:

- `case-runs/`

### 4. Um projeto executavel local (quando rebuild)

Pode ser qualquer stack:

- Vite
- Next.js
- Nuxt
- Astro
- outro frontend compatível com browser

## Variaveis de adaptacao (por repo)

Estas variaveis podem mudar sem quebrar o modelo:

- stack de frontend
- estrategia de componentes
- porta local (3005/3006/3007/...)
- naming dos projetos locais
- local dos artefatos (desde que indexado)

## O que NAO deve mudar (contratos)

- loop por etapas (capturar -> implementar -> validar -> aprender)
- uso de screenshots por breakpoint nas etapas de UI
- separacao `Measured/Observed/Inferred`
- atualizacao de caso + indices + classificacao de estilo
- snapshots em `exemplos/` quando houver implementacao local

## Fluxo de bootstrap (novo repo)

1. Copiar skill + base global
2. Ajustar caminhos no `SKILL.md` se necessario
3. Garantir Playwright instalado em pelo menos um projeto executavel
4. Criar `case-runs/`
5. Executar primeiro caso e registrar como `case-01`
6. Atualizar indices/taxonomia

## Estrategia de modularizacao recomendada

## Modulo A: Auditoria visual

Entradas:

- URL
- screenshots de referencia (opcional)

Saidas:

- capturas
- metricas
- notas de UX

## Modulo B: Reconstrucao

Entradas:

- evidencia coletada
- objetivo de fidelidade

Saidas:

- projeto local rodando
- componentes e motion

## Modulo C: Review de UX

Entradas:

- screenshots locais
- metadados de overflow/breakpoints

Saidas:

- findings criticos
- correcoes priorizadas

## Modulo D: Aprendizado

Entradas:

- resultados do caso
- problemas encontrados
- melhorias de pipeline

Saidas:

- caso em Markdown
- regras promovidas
- indices atualizados

## Checklist de “acoplavel o suficiente”

Se responder “sim” para tudo abaixo, a arquitetura esta boa:

- A base global funciona sem depender de React/Vite?
- A skill continua curta e operacional?
- O pipeline tem script reutilizavel e parametros explicitos?
- Um novo caso pode ser criado sem copiar conhecimento manualmente?
- Os estilos podem ser buscados por taxonomia, nao por nome de template?
- O historico de aprendizados e navegavel por indices?
