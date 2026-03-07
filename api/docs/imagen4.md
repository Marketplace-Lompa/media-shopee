# Imagen 4 — Geração de Imagem Profissional via API

> Documentação baseada em: https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images  
> Atualizada em: Março/2026

---

## O que é o Imagen 4?

**Imagen 4** é a família de modelos de geração de imagem de alta fidelidade do Google. Diferente do Nano Banana (família Gemini), o Imagen é focado exclusivamente em imagens com **fotorrealismo extremo**, suporte nativo a proporções e resoluções profissionais, e não realiza edição conversacional.

---

## Família de Modelos

| Modelo | Model ID (API) | Velocidade | Qualidade | Custo/imagem |
|---|---|---|---|---|
| **Imagen 4 Fast** | `imagen-4.0-fast-generate-001` | ⚡⚡⚡ | ★★★ | $0.02 |
| **Imagen 4 Standard** | `imagen-4.0-generate-001` | ⚡⚡ | ★★★★ | $0.04 |
| **Imagen 4 Ultra** | `imagen-4.0-ultra-generate-001` | ⚡ | ★★★★★ | $0.06 |

> **Recomendação:** Para fotos de produto com máximo fotorrealismo, use **Imagen 4 Ultra**. Para volume alto (lookbooks, variações de cor), use **Imagen 4 Fast**.

---

## Diferenças: Imagen 4 vs. Nano Banana

| Característica | Imagen 4 | Nano Banana |
|---|---|---|
| Fotorrealismo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Velocidade | Médio | Alto |
| Edição conversacional | ❌ | ✅ |
| Grounding com Search | ❌ | ✅ (3.1 Flash) |
| Proporções suportadas | 5 padrões | 14+ (inclui 4:1, 8:1) |
| Texto legível em imagem | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ (Pro) |
| Modo free tier | Limitado | ~500/dia |
| Custo (paid) | $0.02–$0.06 | $0.039–$0.24 |

---

## Proporções Suportadas

| Proporção | Dimensões (1K) | Uso ideal |
|---|---|---|
| `1:1` | 1024×1024 | Posts quadrados, thumbnails |
| `3:4` | 768×1024 | Mobile portrait |
| `4:3` | 1024×768 | Desktop, TV |
| `9:16` | 768×1352 | Stories, Shopee mobile cover |
| `16:9` | 1408×768 | Banners, YouTube, desktop |

---

## Resoluções por Modelo

| Modelo | Resoluções disponíveis |
|---|---|
| Imagen 4 Fast | `1K` |
| Imagen 4 Standard | `1K`, `2K` |
| Imagen 4 Ultra | `1K`, `2K` |

---

## Parâmetros da API (`generate_images`)

| Parâmetro | Tipo | Descrição | Padrão |
|---|---|---|---|
| `prompt` | `str` | Descrição da imagem (máx. 480 tokens) | obrigatório |
| `negative_prompt` | `str` | O que NÃO incluir na imagem | opcional |
| `number_of_images` | `int` | Quantidade de imagens (1–4) | `4` |
| `aspect_ratio` | `str` | Proporção da saída | `"1:1"` |
| `image_size` | `str` | Resolução `"1K"` ou `"2K"` | `"1K"` |
| `person_generation` | `str` | `"allow_all"`, `"allow_adult"`, `"dont_allow"` | `"allow_adult"` |
| `add_watermark` | `bool` | Adicionar SynthID watermark | `True` |
| `seed` | `int` | Seed para reprodutibilidade (aproximada) | opcional |

---

## Exemplos de Código Python

### Instalação

```bash
pip install google-genai pillow python-dotenv
```

### Geração básica

```python
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

response = client.models.generate_images(
    model="imagen-4.0-generate-001",
    prompt="Modelo feminina brasileira, 25 anos, blusa branca de linho, calca jeans, estudio fotografico profissional, fundo branco, luz natural",
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="9:16",
        person_generation="allow_adult",
    )
)

for i, image in enumerate(response.generated_images):
    image.image.save(f"output/imagen4_{i}.png")
    print(f"Salvo: output/imagen4_{i}.png")
```

### Geração com prompt negativo

```python
response = client.models.generate_images(
    model="imagen-4.0-ultra-generate-001",
    prompt="Modelo feminina brasileira elegante, blusa de renda bege, parque ao ar livre, luz dourada de fim de tarde",
    config=types.GenerateImagesConfig(
        number_of_images=2,
        aspect_ratio="9:16",
        image_size="2K",
        negative_prompt="deformado, feio, baixa qualidade, pixelado, desfocado, marca d'água, texto",
        person_generation="allow_adult",
    )
)
```

### Geração em batch (4 variações)

```python
response = client.models.generate_images(
    model="imagen-4.0-fast-generate-001",
    prompt="Camiseta branca modal feminina, fundo branco limpo, iluminacao de estudio",
    config=types.GenerateImagesConfig(
        number_of_images=4,   # Máximo permitido
        aspect_ratio="1:1",
        person_generation="dont_allow",  # Só o produto
    )
)

for i, image in enumerate(response.generated_images):
    image.image.save(f"output/variacao_{i+1}.png")
```

### REST (cURL)

```bash
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:generateImages" \
  -H "x-goog-api-key: $GOOGLE_AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Modelo feminina brasileira, blusa branca de linho, fundo branco, fotografia profissional",
    "config": {
      "numberOfImages": 1,
      "aspectRatio": "9:16",
      "personGeneration": "ALLOW_ADULT"
    }
  }'
```

---

## Limites de Uso

### Free Tier (API Key gratuita do AI Studio)
| Modelo | Req/minuto | Imagens/dia |
|---|---|---|
| Imagen 4 Fast | 2 IPM | ~50–100/dia |
| Imagen 4 Standard | 2 IPM | ~50–100/dia |
| Imagen 4 Ultra | 2 IPM | ~50/dia |

> ⚠️ O Imagen 4 tem limites gratuitos mais restritos que o Nano Banana.

### Paid Tier (billing habilitado)
| Tier | Req/minuto |
|---|---|
| Tier 1 | 10 RPM |
| Tier 2 | 100 RPM |
| Tier 3+ | Sob demanda |

---

## Custo Estimado por Cenário

| Cenário | Modelo | Qtd/mês | Custo/mês |
|---|---|---|---|
| Cover Shopee (1 produto) | Fast | 10 imagens | $0.20 |
| Lookbook completo | Standard | 50 imagens | $2.00 |
| Catálogo profissional | Ultra | 200 imagens | $12.00 |
| Volume alto | Fast | 1.000 imagens | $20.00 |

> Com os **R$ 1.759 de créditos Google Cloud**, você tem aproximadamente **29.000 imagens com Imagen 4 Fast** antes de precisar pagar.

---

## Casos de Uso — Shopee/E-commerce

| Objetivo | Modelo recomendado | Proporção | Resolução |
|---|---|---|---|
| Foto de capa Shopee | `imagen-4.0-standard` | `9:16` | `1K` |
| Foto produto flat lay | `imagen-4.0-ultra` | `1:1` | `2K` |
| Banner promocional | `imagen-4.0-fast` | `16:9` | `1K` |
| Detalhe de tecido | `imagen-4.0-ultra` | `1:1` | `2K` |
| Foto capa Mercado Livre | `imagen-4.0-standard` | `1:1` | `1K` |

---

## Links Oficiais

- 📖 [Documentação Imagen 4](https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images)
- 💰 [Pricing Vertex AI / Imagen](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- 🔑 [Google AI Studio](https://aistudio.google.com)
