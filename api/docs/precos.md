# Comparativo de Preços — Gemini API (Snapshot)

> Data de verificação: **2026-03-07**
>
> Fonte oficial: [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)
>
> Observação: preços e disponibilidade podem mudar. Sempre valide no link oficial antes de orçamento final.

---

## 1) Imagem — Gemini

### `gemini-3.1-flash-image-preview` (Nano Banana 2, Preview)

**Tier:** apenas pago (free tier indisponível para este modelo na tabela oficial).

| Modalidade | Preço oficial |
|---|---|
| Output de imagem (standard) | `$60.00 / 1.000.000 tokens` |
| Equivalente 0.5K | `~$0.045 / imagem` |
| Equivalente 1K | `~$0.067 / imagem` |
| Equivalente 2K | `~$0.101 / imagem` |
| Equivalente 4K | `~$0.151 / imagem` |
| Batch output de imagem | `$30.00 / 1.000.000 tokens` |
| Batch equivalente 1K | `~$0.034 / imagem` |
| Batch equivalente 2K | `~$0.050 / imagem` |
| Batch equivalente 4K | `~$0.076 / imagem` |

### `gemini-2.5-flash-image`

| Modalidade | Preço oficial |
|---|---|
| Geração de imagem (paid) | `~$0.039 / imagem` |
| Free tier | disponível na tabela oficial |

---

## 2) Imagem — Imagen 4

| Modelo | Preço por imagem (paid) |
|---|---|
| `imagen-4.0-fast-generate-001` | `$0.02` |
| `imagen-4.0-generate-001` | `$0.04` |
| `imagen-4.0-ultra-generate-001` | `$0.06` |

Na tabela oficial de pricing do Gemini API, os modelos Imagen 4 aparecem sem free tier.

---

## 3) Vídeo — Veo

| Modelo | Preço por segundo (paid) |
|---|---|
| `veo-3.1-generate-preview` (720p/1080p) | `$0.40/s` |
| `veo-3.1-generate-preview` (4k) | `$0.60/s` |
| `veo-3.1-fast-generate-preview` (720p/1080p) | `$0.15/s` |
| `veo-3.1-fast-generate-preview` (4k) | `$0.35/s` |
| `veo-2.0-generate-001` | `$0.35/s` |

Exemplos rápidos:
- Veo 3.1 standard 6s (1080p): `~$2.40`
- Veo 3.1 fast 6s (1080p): `~$0.90`
- Veo 2 6s: `~$2.10`

---

## 4) Grounding (Google Search)

Para modelos que suportam grounding por busca, a tabela oficial indica franquia mensal e depois cobrança por query de busca. Verifique o bloco do modelo específico no pricing.

---

## 5) Regras práticas de orçamento

1. Use preview/rascunho em resolução baixa antes do render final.
2. Use batch para jobs não urgentes (desconto significativo).
3. Para vídeo, diferencie claramente custo de `standard` vs `fast`.
4. Trate este documento como snapshot; o link oficial é a verdade final.
