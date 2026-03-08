# Decisão de Modelo: Nano Banana 2 como padrão

> ADR (Architecture Decision Record)
>
> Status: aprovado
>
> Última revisão: 2026-03-07
>
> Referências oficiais:
> - [Image generation docs](https://ai.google.dev/gemini-api/docs/image-generation)
> - [Pricing](https://ai.google.dev/gemini-api/docs/pricing)
> - [Deprecations](https://ai.google.dev/gemini-api/docs/deprecations)

---

## Contexto

Precisávamos definir um modelo padrão para geração de imagem de e-commerce com foco em:
- velocidade de iteração
- custo previsível
- qualidade suficiente para catálogo Shopee

Modelos considerados:
- `gemini-2.5-flash-image`
- `gemini-3-pro-image-preview`
- `gemini-3.1-flash-image-preview`

---

## Decisão

**Modelo padrão do projeto:** `gemini-3.1-flash-image-preview`.

---

## Justificativas

1. Melhor equilíbrio entre qualidade, velocidade e custo para uso diário.
2. Suporte amplo a fluxos de edição/geração por texto + imagem.
3. Bom encaixe com o pipeline atual (`agent -> generator -> frontend`).
4. Mantém fallback simples para outros modelos sem alterar arquitetura.

---

## Notas importantes de status

- `gemini-3.1-flash-image-preview` é modelo **preview**.
- `gemini-3-pro-image-preview` também é **preview**.
- Status de preview/depreciação pode mudar; validar periodicamente em `Deprecations`.

Este ADR **não** assume permanência de roadmap de preview.

---

## Consequências para o projeto

- Defaults do backend e scripts ficam alinhados ao `gemini-3.1-flash-image-preview`.
- Custos e cotas devem ser tratados como variáveis operacionais (não hardcoded em decisão).
- A decisão será revisada quando houver:
  - mudança de status no deprecations
  - vantagem clara de custo/latência em outro modelo
  - necessidade técnica não atendida pelo modelo atual

