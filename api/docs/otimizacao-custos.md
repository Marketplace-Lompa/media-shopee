# Otimização de Custos — Estratégias Avançadas

> Guia de táticas para maximizar ROI em projetos de geração de mídia com Google AI API.  
> Atualizado: Março/2026

---

## Índice

1. [Estrutura de Custos por Modalidade](#1-estrutura-de-custos-por-modalidade)
2. [Estratégia de Tiering — Flash → Pro](#2-estratégia-de-tiering--flash--pro)
3. [Context Caching — 90% de Redução](#3-context-caching--90-de-redução)
4. [Batch API — 50% de Desconto](#4-batch-api--50-de-desconto)
5. [Áudio no Veo — Desabilitar para Reduzir Custos](#5-áudio-no-veo--desabilitar-para-reduzir-custos)
6. [Thinking Level para Otimização](#6-thinking-level-para-otimização)
7. [Estimativa de Custo por Projeto](#7-estimativa-de-custo-por-projeto)

---

## 1. Estrutura de Custos por Modalidade

### Imagem — Nano Banana 2 (gemini-3.1-flash-image-preview)

| Resolução | Tokens consumidos | Custo por imagem | Batch (50% desc.) |
|---|---|---|---|
| `512px` | ~747 tokens | $0.045 | **$0.023** |
| `1K` | ~1.120 tokens | $0.067 | **$0.034** |
| `2K` | ~1.680 tokens | $0.101 | **$0.051** |
| `4K` | ~2.520 tokens | $0.151 | **$0.076** |

> Base: $60 por 1M tokens de output de imagem

### Imagem — Imagen 4

| Modelo | Custo por imagem |
|---|---|
| Imagen 3 Standard | $0.03 |
| Imagen 4 Standard | $0.04 – $0.06 |
| Imagen 4 Fast | $0.02 (mais barato de todos) |
| Imagen 4 Ultra | $0.08 |

### Vídeo — Veo 3.1

| Modo | Custo por segundo | Custo por clipe 8s |
|---|---|---|
| Veo 3.1 Standard (720p/1080p) | $0.40 | $3.20 |
| Veo 3.1 Standard (4k) | $0.60 | $4.80 |
| Veo 3.1 Fast (720p/1080p) | $0.15 | **$1.20** |
| Veo 3.1 Fast (4k) | $0.35 | $2.80 |

> ⚠️ **Regra:** Use `Fast` durante desenvolvimento. Reserve `Standard` para render final.

### Grounding com Google Search

| Tipo | Franquia gratuita | Custo após franquia |
|---|---|---|
| Web Search | 5.000 prompts/mês | $14 por 1.000 queries |
| Image Search | Incluído | $14 por 1.000 queries |
| Conteúdo retornado | — | **Não cobrado como tokens** |

---

## 2. Estratégia de Tiering — Flash → Pro

O modelo de desenvolvimento deve seguir um pipeline progressivo:

```
Rascunho → Conceito → Aprovação → Render Final
  Flash       Flash      Flash         Standard
  ($0.034)   ($0.067)   ($0.034)      ($0.101–0.151)
```

### Implementação prática

```python
MODELOS = {
    "rascunho": {
        "model": "gemini-3.1-flash-image-preview",
        "image_size": "512px",    # mais barato, só para verificar composição
        "thinking_level": "MINIMAL"
    },
    "conceito": {
        "model": "gemini-3.1-flash-image-preview",
        "image_size": "1K",       # qualidade suficiente para aprovação
        "thinking_level": "MINIMAL"
    },
    "producao": {
        "model": "gemini-3.1-flash-image-preview",
        "image_size": "2K",       # qualidade final Shopee
        "thinking_level": "HIGH"
    },
    "hero_4k": {
        "model": "gemini-3.1-flash-image-preview",
        "image_size": "4K",       # somente para assets de alta resolução
        "thinking_level": "HIGH"
    }
}

fase = "rascunho"  # começa no mais barato
config_atual = MODELOS[fase]
```

---

## 3. Context Caching — 90% de Redução

Quando o mesmo conjunto de imagens de referência é usado repetidamente (identity bible, manual de marca, referência de produto), o **Context Caching** evita reprocessar os mesmos tokens a cada request.

### Quando usar

- Mesmo produto em múltiplas variações (cor, pose, cenário)
- Sessão de fotos com a mesma modelo
- Lookbook de coleção completa
- Qualquer workflow com +10 requests usando as mesmas referências

### Redução de custo

| Situação | Sem cache | Com cache |
|---|---|---|
| 100 imagens com mesma referência de produto | $X de input | **$X × 0.10** (90% menos) |
| Session de fotos: 50 variações com mesma modelo | $X de input | **$X × 0.10** |

### Código com Caching (Cloud-hosted)

```python
# Método 1: Upload para Files API (evita base64 grande a cada requisição)
uploaded_file = client.files.upload(
    path="input/produto_referencia.jpg",
    config={"mime_type": "image/jpeg", "display_name": "produto-ref"}
)

# Usar URI em vez de reenviar a imagem toda vez
file_uri = uploaded_file.uri

# Nas requisições seguintes, reference pela URI
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        {"file_data": {"file_uri": file_uri, "mime_type": "image/jpeg"}},
        "Recrie esta peça em modelo feminina brasileira, cenário urbano"
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K")
    )
)
```

### Limites do Files API

| Parâmetro | Limite |
|---|---|
| Tamanho máximo por arquivo | 2 GB |
| Armazenamento máximo total | 20 GB |
| TTL padrão | 48 horas |
| Formatos suportados | PNG, JPEG, WebP, GIF, HEIC, MP4 |

---

## 4. Batch API — 50% de Desconto

Para geração em volume sem urgência de tempo (catálogos, pré-geração noturna).

### Parâmetros

| Métrica | Limite |
|---|---|
| Prazo de processamento | Até 24 horas |
| Desconto | **50% sobre preço padrão** |
| Requests concorrentes | 100 |
| Tokens enfileirados (Nano Banana 2) | 1.000.000 |

### Quando usar Batch

✅ Geração de catálogo completo (100+ produtos)  
✅ Processamento noturno de lookbooks  
✅ Pré-geração de variações sazonais  
✅ Qualquer tarefa não time-sensitive  

### Quando NÃO usar Batch

❌ Edição conversacional (multi-turno)  
❌ Preview em tempo real para aprovação  
❌ Testes e iteração de prompt  

### Custo comparado

| Modalidade | 1.000 imagens 1K | 1.000 imagens 2K |
|---|---|---|
| Padrão (sync) | $67.00 | $101.00 |
| **Batch** | **$33.50** | **$50.50** |

> Documentação oficial: https://ai.google.dev/gemini-api/docs/batch-api#image-generation

---

## 5. Áudio no Veo — Desabilitar para Reduzir Custos

Se o projeto final usará trilha sonora externa, locução profissional ou música licenciada, **desabilitar a geração de áudio reduz o custo em até 33%** em alguns provedores.

### Código para desabilitar áudio

```python
operation = await ai.models.generateVideos(
    model="veo-3.1-generate-preview",
    prompt="Modelo caminhando por rua de São Paulo ao entardecer",
    config={
        "aspectRatio": "9:16",
        "resolution": "1080p",
        "durationSeconds": 8,
        "generateAudio": False  # ← desabilitar para economizar
    }
)
```

### Quando manter o áudio

✅ Vídeos para redes sociais (Reels, TikTok) — o som gerado é surpreendentemente bom  
✅ Demonstrações rápidas de produto  
✅ Quando não há orçamento para pós-produção de áudio  

### Quando desabilitar o áudio

✅ Produção profissional com sonoplastia dedicada  
✅ Vídeos com locução gravada  
✅ Conteúdo musical (trilha licenciada substituirá o áudio)  
✅ Etapa de desenvolvimento/protótipo  

---

## 6. Thinking Level para Otimização

O `thinking_level` impacta diretamente o custo (tokens de "pensamento" são cobrados):

| Nível (imagem) | Uso recomendado | Tokens extras | Impacto no custo |
|---|---|---|---|
| `"MINIMAL"` | Volume alto, composições simples | Menor | menor custo |
| `"HIGH"` | Texto em imagem, layouts complexos | Maior | maior custo |

### Regra prática

```
Rascunho → MINIMAL
Conceito para aprovação → MINIMAL  
Render final com texto/layout complexo → HIGH
```

---

## 7. Estimativa de Custo por Projeto

### Projeto: Lançamento de coleção (20 produtos, 5 fotos cada)

| Fase | Modelo | Resolução | Imagens | Custo unitário | Total |
|---|---|---|---|---|---|
| Rascunho | Nano Banana 2 | 512px | 100 | $0.034 | $3.40 |
| Conceito | Nano Banana 2 | 1K | 100 | $0.067 | $6.70 |
| **Produção final** | Nano Banana 2 | 2K (batch) | 100 | $0.051 | **$5.10** |
| **Total** | | | **300** | | **$15.20** |

### Projeto: Vídeo de lookbook (5 produtos, 1 vídeo de 8s cada)

| Fase | Modo | Clipes | Custo/clipe | Total |
|---|---|---|---|---|
| Teste de conceito | Fast ($1.20/clipe) | 10 variações | $1.20 | $12.00 |
| **Render final** | Standard ($3.20/clipe) | 5 | $3.20 | **$16.00** |
| **Total** | | **15** | | **$28.00** |

### Regra de ouro

> **75% dos custos vêm dos 25% finais (render de produção).**  
> Invista em iteração barata para chegar com certeza na etapa final.
