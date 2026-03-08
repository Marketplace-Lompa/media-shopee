# Modos do Projeto MEDIA-SHOPEE

> Última revisão: 2026-03-07

Este projeto opera em **dois modos complementares**.

---

## 1) Modo Ferramenta de Prompt (manual)

Use este modo quando você quer:
- iterar criativos manualmente no AI Studio, Flow, Nano, Veo ou outras plataformas
- gerar prompts e validar estética com controle manual
- trabalhar sem depender do app local

### Componentes principais
- `.agent/skills/*` (vocabulário, realismo, e-commerce, etc.)
- `.agent/workflows/*` (atalhos e fluxo no Antigravity)
- `prompts/*.md` (prompts salvos por produto)

### Saída esperada
- prompt final pronto para colar na plataforma de geração
- variações HERO / MEDIUM / MACRO por produto

---

## 2) Modo Plataforma via API (automatizado)

Use este modo quando você quer:
- gerar mídia em fluxo repetível (script/API)
- integrar com automação de catálogo/publicação
- reduzir trabalho manual de operação

### Componentes principais
- `api/scripts/*` (CLI direta de imagem, vídeo, compressão e publicação)
- `api/docs/*` (referência técnica da API)
- `app/backend/*` + `app/frontend/*` (Studio Local)

### Saída esperada
- imagens/vídeos gerados por script
- pipeline agent -> generation -> galeria/pool

---

## Como escolher rápido

| Cenário | Modo recomendado |
|---|---|
| Explorar ideias e direção visual | Ferramenta de Prompt (manual) |
| Produção repetitiva de catálogo | Plataforma via API |
| Teste de linguagem/descrição de produto | Ferramenta de Prompt (manual) |
| Lote e integração com fluxo operacional | Plataforma via API |

---

## Fluxo recomendado (híbrido)

1. Itere linguagem e direção no modo manual.
2. Congele prompts vencedores em `prompts/*.md`.
3. Migre os prompts aprovados para scripts/API.
4. Rode geração em lote e pós-processamento (compressão/publicação).

Esse fluxo reduz custo de tentativa e erro em produção.

---

## Referências relacionadas

- [README raiz](../../README.md)
- [Guia de prompts Shopee](./prompts-shopee.md)
- [README do módulo API](../../api/README.md)
- [Comparativo de preços](../../api/docs/precos.md)
