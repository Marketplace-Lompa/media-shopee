# Comparativo de Preços — Google AI Image & Video API

> Atualizada em: Março/2026  
> Fonte: https://ai.google.dev/pricing

---

## Geração de Imagem

### Familia Nano Banana (Gemini Image)

| Modelo | Resolução | Custo por imagem | Free tier/dia |
|---|---|---|---|
| `gemini-2.5-flash-image` | 1K (1024×1024) | ~$0.039 | ~500 |
| `gemini-3-pro-image-preview` | 1K–2K | ~$0.134 | Limitado |
| `gemini-3-pro-image-preview` | 4K | ~$0.240 | Limitado |
| `gemini-3.1-flash-image-preview` | 1K | ~$0.039 | ~500 |
| `gemini-3.1-flash-image-preview` | 4K | ~$0.180 | Limitado |

### Família Imagen 4

| Modelo | Custo por imagem | Free tier/dia | Melhor para |
|---|---|---|---|
| `imagen-4.0-fast-generate-001` | **$0.02** | ~50–100 | Volume alto, lookbooks |
| `imagen-4.0-generate-001` | **$0.04** | ~50 | Qualidade/custo balanceados |
| `imagen-4.0-ultra-generate-001` | **$0.06** | ~50 | Máximo fotorrealismo |

---

## Geração de Vídeo (Veo)

| Modelo | Custo por segundo | 4s | 6s | 8s |
|---|---|---|---|---|
| `veo-3.1-generate-preview` | $0.75/s | $3.00 | $4.50 | $6.00 |
| `veo-3.1-fast-generate-preview` | ~$0.40/s | ~$1.60 | ~$2.40 | ~$3.20 |
| `veo-2.0-generate-001` | $0.35/s | $1.40 | $2.10 | $2.80 |

> ⚠️ Veo não tem free tier via API — requer billing habilitado.

---

## Estimativa de Custo Mensal por Cenário

### Cenário 1: Pequena loja Shopee (10 produtos/mês)
| Tarefa | Qtd | Modelo | Custo |
|---|---|---|---|
| Cover 9:16 por cor | 30 imagens | Imagen 4 Fast | $0.60 |
| Detalhes textura | 10 imagens | Imagen 4 Ultra | $0.60 |
| **Total** | | | **$1.20/mês** |

### Cenário 2: Loja média (50 produtos/mês)
| Tarefa | Qtd | Modelo | Custo |
|---|---|---|---|
| Covers 9:16 (3 por produto) | 150 | Imagen 4 Fast | $3.00 |
| Fotos lifestyle | 50 | Nano Banana 2 | $1.95 |
| Vídeos produto (6s) | 10 | Veo 2 | $21.00 |
| **Total** | | | **~$26/mês** |

### Cenário 3: Uso free tier máximo (sem custo)
| Canal | Modelo | Limite diário |
|---|---|---|
| Gemini API | Nano Banana 2 | ~500 imagens |
| AI Studio web | Nano Banana Pro | ~100 imagens |
| Gemini App (Ultra) | Nano Banana Pro | ~1.000 imagens |
| **Total combinado** | | **~1.600 imagens/dia grátis** |

---

## Créditos Google Cloud Disponíveis

| Fonte | Valor | Validade | Equivalência (Imagen 4 Fast) |
|---|---|---|---|
| Google Cloud Trial | R$ 1.759 (~$300) | Jun/2026 | ~15.000 imagens |
| Developer Program Ultra* | $100/mês | Mensal | ~5.000 imagens/mês |

> *Disponível apenas para assinantes Google AI Ultra com conta pessoal @gmail.com

---

## Links

- 💰 [Pricing oficial Gemini API](https://ai.google.dev/pricing)
- 💰 [Pricing Vertex AI (Imagen)](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- 📊 [Billing Dashboard](https://console.cloud.google.com/billing)
