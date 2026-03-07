# Nano Banana 2 — Referência Técnica Completa da API

> **Modelo oficial do projeto:** `gemini-3.1-flash-image-preview`  
> **Codinome:** Nano Banana 2  
> **Status:** ✅ Ativo (lançado: Fev/2026)  
> **Fonte primária:** https://ai.google.dev/gemini-api/docs/image-generation  
> **Última atualização:** Março/2026

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Endpoints e Autenticação](#2-endpoints-e-autenticação)
3. [Modos de Geração](#3-modos-de-geração)
4. [Parâmetros Completos da API](#4-parâmetros-completos-da-api)
5. [Proporções e Resoluções](#5-proporções-e-resoluções)
6. [Grounding com Google Search](#6-grounding-com-google-search)
7. [Grounding com Google Image Search](#7-grounding-com-google-image-search)
8. [Thinking Mode](#8-thinking-mode)
9. [Múltiplas Imagens de Referência (até 14)](#9-múltiplas-imagens-de-referência-até-14)
10. [Edição Conversacional (Multi-turno)](#10-edição-conversacional-multi-turno)
11. [Geração em Batch](#11-geração-em-batch)
12. [Rate Limits e Cotas](#12-rate-limits-e-cotas)
13. [Pricing Detalhado](#13-pricing-detalhado)
14. [Limitações Conhecidas](#14-limitações-conhecidas)
15. [Boas Práticas de Prompt](#15-boas-práticas-de-prompt)
16. [Exemplos Completos](#16-exemplos-completos)

---

## 1. Visão Geral

O Nano Banana 2 é o modelo recomendado pelo próprio Google para geração de imagens via API:

> *"Gemini 3.1 Flash Image Preview (Nano Banana 2) should be your go-to image generation model, as the best all-around performance and intelligence to cost and latency balance."*
> — Google AI for Developers

### Por que Nano Banana 2?

| Aspecto | Detalhe |
|---|---|
| **Qualidade** | ~95% do Nano Banana Pro a metade do custo |
| **Velocidade** | 4–6s por imagem (3–5x mais rápido que o Pro) |
| **Custo** | $0.067/img (1K) — 50% mais barato que o Pro |
| **Recursos exclusivos** | Grounding Image Search + Thinking Mode |
| **Status** | Ativo e recomendado pelo Google |

---

## 2. Endpoints e Autenticação

### Endpoint principal

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent
```

### Autenticação

```python
from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
```

### Header (REST)

```
x-goog-api-key: $GOOGLE_AI_API_KEY
Content-Type: application/json
```

---

## 3. Modos de Geração

O modelo suporta os seguintes modos, controlados pela estrutura do `contents`:

### 3.1 Texto → Imagem

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=["Descrição detalhada da imagem desejada"],
    config=types.GenerateContentConfig(
        response_modalities=["Image"]
    )
)
```

### 3.2 Texto → Imagem + Texto (Intercalado)

O modelo pode retornar texto e imagem na mesma resposta. Útil para receitas ilustradas, tutoriais, etc.

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=["Generate an illustrated recipe for a Brazilian feijoada"],
    config=types.GenerateContentConfig(
        response_modalities=["Text", "Image"]  # ordem importa
    )
)

for part in response.parts:
    if part.text:
        print(part.text)
    elif part.inline_data:
        part.as_image().save("saida.png")
```

### 3.3 Imagem + Texto → Imagem (Edição)

Fornece uma imagem existente e instrução textual para modificar.

```python
from PIL import Image

img_existente = Image.open("input/produto.jpg")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        img_existente,
        "Mude o fundo para um jardim ensolarado ao entardecer"
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16")
    )
)
```

### 3.4 Múltiplas Imagens + Texto → Imagem

Fornece até 14 imagens de referência combinadas com instrução.

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        "Combine o estilo desta blusa com esta calça, em um ambiente urbano",
        Image.open("input/blusa.jpg"),
        Image.open("input/calca.jpg"),
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K")
    )
)
```

### 3.5 Edição Multi-turno (Conversacional)

Iteração contínua sobre a mesma imagem, mantendo contexto entre turnos.

```python
from google.genai import types

historico = []

# Turno 1: gerar imagem inicial
historico.append(types.Content(role="user", parts=[
    types.Part.from_text("Modelo feminina com blusa branca, estúdio, fundo branco")
]))

resp1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=historico,
    config=types.GenerateContentConfig(response_modalities=["Image"])
)

# Adicionar resposta ao histórico
historico.append(resp1.candidates[0].content)

# Turno 2: modificar
historico.append(types.Content(role="user", parts=[
    types.Part.from_text("Mantenha tudo igual, mas mude o fundo para azul marinho")
]))

resp2 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=historico,
    config=types.GenerateContentConfig(response_modalities=["Image"])
)
```

---

## 4. Parâmetros Completos da API

### `GenerateContentConfig`

| Parâmetro | Tipo | Valores | Descrição |
|---|---|---|---|
| `response_modalities` | `list[str]` | `["Image"]`, `["Text", "Image"]` | Tipos de saída. Padrão: `["Text", "Image"]` |
| `image_config` | `ImageConfig` | objeto | Configurações visuais (ver abaixo) |
| `tools` | `list[Tool]` | `[{"google_search": {}}]` | Habilitar Grounding |
| `temperature` | `float` | `0.0`–`2.0` | Criatividade. Padrão: `1.0` |
| `top_p` | `float` | `0.0`–`1.0` | Distribuição de tokens. Padrão: `0.95` |
| `candidate_count` | `int` | `1` | Número de candidatos (fixo em 1) |

### `ImageConfig`

| Parâmetro | Tipo | Valores | Descrição |
|---|---|---|---|
| `aspect_ratio` | `str` | Ver Seção 5 | Proporção da imagem. Padrão: `"1:1"` |
| `image_size` | `str` | `"512px"`, `"1K"`, `"2K"`, `"4K"` | Resolução. Padrão: `"1K"` |

> ⚠️ **IMPORTANTE:** Use sempre `K` maiúsculo. `"1k"` (minúsculo) será rejeitado com erro.

---

## 5. Proporções e Resoluções

### Proporções suportadas pelo Nano Banana 2

| Proporção | Dimensões (1K) | Dimensões (2K) | Caso de uso ideal |
|---|---|---|---|
| `"1:1"` | 1024×1024 | 2048×2048 | Posts quadrados, thumbnails, ML cover |
| `"3:4"` | 768×1024 | 1536×2048 | Retrato padrão |
| `"4:3"` | 1024×768 | 2048×1536 | Desktop, apresentações |
| `"9:16"` | 576×1024 | 1152×2048 | **Cover Shopee mobile ← padrão do projeto** |
| `"16:9"` | 1024×576 | 2048×1152 | Banners, YouTube, desktop |
| `"21:9"` | 1024×439 | 2048×878 | Ultra-wide, cinema |
| `"3:2"` | 1024×683 | 2048×1366 | Fotografia landscape |
| `"2:3"` | 683×1024 | 1366×2048 | Fotografia portrait |
| `"5:4"` | 1024×819 | 2048×1638 | Médio formato |
| `"4:5"` | 819×1024 | 1638×2048 | Instagram portrait |
| `"4:1"` | 1024×256 | — | Banner ultra-horizontal |
| `"1:4"` | 256×1024 | — | Banner ultra-vertical |
| `"8:1"` | 1024×128 | — | Rodapé/header skinny |
| `"1:8"` | 128×1024 | — | Rodapé/header skinny vertical |

> As proporções `4:1`, `1:4`, `8:1`, `1:8` são **exclusivas do Nano Banana 2** — não existem nos outros modelos.

### Resoluções e tokens consumidos

| Resolução | Dimensão (1:1) | Tokens output | Custo |
|---|---|---|---|
| `"512px"` | 512×512 | ~560 tokens | ~$0.034 |
| `"1K"` | 1024×1024 | ~1.120 tokens | **$0.067** |
| `"2K"` | 2048×2048 | ~1.680 tokens | $0.101 |
| `"4K"` | 4096×4096 | ~2.520 tokens | $0.151 |

---

## 6. Grounding com Google Search

Permite que o modelo busque informações em tempo real antes de gerar a imagem. Útil para tendências de moda, eventos atuais, dados climáticos, etc.

### Como funciona

1. O modelo analisa o prompt
2. Executa busca no Google Search
3. Usa os resultados textuais como contexto
4. Gera a imagem baseada nos dados reais encontrados

> ⚠️ A busca por imagens via Web Search **não** passa as imagens encontradas para o modelo — apenas texto. Use Image Search (Seção 7) para referências visuais da web.

### Código Python

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="Quais são as tendências de moda feminina brasileira no verão 2026? Crie um look editorial moderno.",
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K"),
        tools=[{"google_search": {}}]
    )
)
```

### Custo do Grounding

- **$14 por 1.000 consultas de search** (paid tier)
- O conteúdo retornado pelo Search **não é cobrado como tokens de input**

---

## 7. Grounding com Google Image Search

**Exclusivo do Nano Banana 2.** Permite usar imagens reais da web como referência visual para geração.

### Como funciona

1. A model busca imagens no Google Image Search baseado no prompt
2. Usa essas imagens reais como contexto visual
3. Gera uma nova imagem inspirada nas referências encontradas

### Código Python

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="Uma modelo usando o estilo de moda da semana de moda de São Paulo 2026",
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
        tools=[
            types.Tool(google_search=types.GoogleSearch(
                search_types=types.SearchTypes(
                    web_search=types.WebSearch(),    # busca textual + imagens web
                    image_search=types.ImageSearch() # busca visual específica
                )
            ))
        ]
    )
)

# Verificar fontes usadas
if response.candidates[0].grounding_metadata:
    meta = response.candidates[0].grounding_metadata
    print("Queries de imagem usadas:", meta.image_search_queries)
    for chunk in meta.grounding_chunks:
        print(f"  Fonte: {chunk.uri}")
        print(f"  Imagem: {chunk.image_uri}")
```

### Campos de resposta do Grounding

| Campo | Descrição |
|---|---|
| `grounding_metadata.image_search_queries` | Queries usadas para busca de imagens |
| `grounding_metadata.grounding_chunks[].uri` | URL da página contendo a imagem |
| `grounding_metadata.grounding_chunks[].image_uri` | URL direta da imagem |
| `grounding_metadata.grounding_supports` | Mapeamento de citações com o conteúdo gerado |
| `grounding_metadata.search_entry_point.rendered_content` | HTML do chip "Google Search" (obrigatório exibir) |

### Requisitos de exibição (obrigatório)

Quando usar Image Search, você **deve**:
1. Exibir um link para a página contendo a imagem fonte
2. Se mostrar a imagem fonte, fornecer clique direto (single-click) para a página original
3. Renderizar o chip "Google Search" retornado em `search_entry_point.rendered_content`

---

## 8. Thinking Mode

O Nano Banana 2 usa um processo interno de "thinking" que:

1. Analisa o prompt com raciocínio avançado
2. Gera "thought images" intermediárias internamente (não cobradas, não visíveis)
3. Refina composição, iluminação e layout
4. Produz a imagem final de alta qualidade

### Comportamento padrão

O Thinking Mode é **ativado por padrão** no Nano Banana 2. Não é necessário configurar nada para usufruí-lo.

### Para prompts complexos, use instructions passo a passo

```python
prompt = """
Passo 1: Crie um fundo de estúdio minimalista com iluminação suave e difusa.
Passo 2: Adicione uma modelo feminina brasileira, 25 anos, cabelos cacheados, pele morena clara.
Passo 3: Vista ela com uma blusa de tricô bege de textura aberta.
Passo 4: Posicione a câmera em ângulo médio-americano (da cintura para cima).
Resultado final: Fotografia editorial de moda e-commerce, 9:16, 2K.
"""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K")
    )
)
```

---

## 9. Múltiplas Imagens de Referência (até 14)

O Nano Banana 2 suporta até **14 imagens de referência** combinadas em um único request.

### Tipos de referência aceitos

- Fotos de pessoas/modelos (consistência facial)
- Roupas/produtos (manter detalhes da peça)
- Estilos/referências visuais (transferência de estilo)
- Cenários/fundos
- Combinação de qualquer um dos acima

### Capacidades de consistência

| Tipo | Máximo suportado |
|---|---|
| Personagens (consistência facial) | 4 personagens |
| Objetos (fidelidade) | 10 objetos |
| Imagens de referência total | 14 imagens |

### Código Python — Múltiplas referências

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

# Juntar referências: modelo + produto + estilo
referencias = [
    "Crie uma foto de moda da modelo vestindo esta blusa, no estilo desta referência editorial",
    Image.open("input/modelo_referencia.jpg"),   # referência de modelo
    Image.open("input/blusa_produto.jpg"),        # produto a vestir
    Image.open("input/estilo_editorial.jpg"),     # estilo visual desejado
]

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=referencias,
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(
            aspect_ratio="9:16",
            image_size="2K"
        )
    )
)

for part in response.parts:
    if part.inline_data:
        part.as_image().save("output/resultado.png")
```

### MIME types aceitos para imagens de input

| Formato | MIME type |
|---|---|
| JPEG/JPG | `image/jpeg` |
| PNG | `image/png` |
| WebP | `image/webp` |
| GIF | `image/gif` |
| HEIC | `image/heic` |
| HEIF | `image/heif` |

---

## 10. Edição Conversacional (Multi-turno)

O Nano Banana 2 mantém contexto entre turnos, permitindo edição iterativa sem reenviar a imagem original a cada vez.

### Fluxo típico de e-commerce

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
historico = []

# === Turno 1: Gerar imagem base ===
historico.append(types.Content(role="user", parts=[
    types.Part.from_text(
        "Modelo feminina brasileira, blusa branca de linho, calça bege, "
        "fundo branco de estúdio, iluminação natural suave, 9:16"
    )
]))

resp1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=historico,
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K")
    )
)
historico.append(resp1.candidates[0].content)
resp1.parts[0].as_image().save("output/v1_original.png")

# === Turno 2: Trocar cor da blusa ===
historico.append(types.Content(role="user", parts=[
    types.Part.from_text("Mantenha tudo idêntico, mas mude a blusa para azul marinho")
]))

resp2 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=historico,
    config=types.GenerateContentConfig(response_modalities=["Image"])
)
historico.append(resp2.candidates[0].content)
resp2.parts[0].as_image().save("output/v2_azul.png")

# === Turno 3: Mudar cenário ===
historico.append(types.Content(role="user", parts=[
    types.Part.from_text("Agora mude o fundo para uma rua de São Paulo ao entardecer, bokeh")
]))

resp3 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=historico,
    config=types.GenerateContentConfig(response_modalities=["Image"])
)
resp3.parts[0].as_image().save("output/v3_rua.png")
```

---

## 11. Geração em Batch

Para geração de grande volume com tolerância de latência (até 24h), a Batch API oferece **50% de desconto**.

### Quando usar Batch

- Geração de +100 variações de produto
- Processamento noturno de catálogos
- Pré-geração de lookbooks completos

### Limites do Batch

| Métrica | Limite |
|---|---|
| Requests concorrentes | 100 |
| Tamanho máximo do arquivo de input | 2 GB |
| Armazenamento máximo | 20 GB |
| Tokens enfileirados (Nano Banana 2) | 1.000.000 tokens |
| Prazo de processamento | Até 24 horas |
| Desconto | 50% sobre o preço padrão |

### Documentação oficial do Batch

👉 https://ai.google.dev/gemini-api/docs/batch-api#image-generation

---

## 12. Rate Limits e Cotas

### Free Tier (API Key gratuita)

| Métrica | Limite |
|---|---|
| Requests por minuto (RPM) | 15 |
| Requests por dia (RPD) | ~500–1.000 |
| Tokens por minuto (TPM) | Variável |

### Paid Tier

| Tier | RPM | Custo |
|---|---|---|
| Tier 1 | Maior RPM | Pay-per-use |
| Tier 2+ | Sob demanda | Pay-per-use |

> Rate limits se aplicam *por projeto*, não por API key. Projetos com maior gasto histórico recebem limites maiores automaticamente.

---

## 13. Pricing Detalhado

### Tokens de output (imagens geradas)

**Preço base: $60 por 1.000.000 tokens de output**

| Resolução | Tokens consumidos | Custo por imagem |
|---|---|---|
| `512px` (0.5K) | ~560 tokens | **~$0.034** |
| `1K` (1024px) | ~1.120 tokens | **$0.067** |
| `2K` (2048px) | ~1.680 tokens | **$0.101** |
| `4K` (4096px) | ~2.520 tokens | **$0.151** |

### Tokens de input (texto do prompt)

**Preço: $0.25 por 1.000.000 tokens de input**

> Para prompts típicos de 200 tokens: custo de input ≈ $0.00005 (negligível)

### Grounding com Google Search

| Tipo | Custo |
|---|---|
| Web Search + Image Search | $14 por 1.000 queries |
| Conteúdo retornado pelo Search | **Não cobrado como tokens** |

### Batch API

| Modo | Preço vs. Padrão |
|---|---|
| Batch | 50% de desconto |

### Estimativa mensal — uso típico Shopee

| Cenário | Imagens/mês | Resolução | Custo |
|---|---|---|---|
| Free tier máximo | 500/dia × 30 = 15.000 | 1K | **$0** |
| 100 produtos, 5 fotos cada | 500 | 2K | $50.50 |
| 500 produtos, 3 fotos cada | 1.500 | 1K | $100.50 |
| Alto volume (batch) | 5.000 | 1K | **$167.50** (c/ 50% desc.) |

---

## 14. Limitações Conhecidas

| Limitação | Detalhe |
|---|---|
| **Sem input de áudio/vídeo** | Aceita apenas texto e imagens como input |
| **Consistência de personagens** | Máximo 4 personagens com consistência facial |
| **Fidelidade de objetos** | Máximo 10 objetos com fidelidade garantida |
| **Imagens de referência** | Máximo 14 imagens em um único request |
| **Texto em imagens** | Melhor resultado: gerar texto primeiro, depois pedir imagem com o texto |
| **Contagem de imagens** | O modelo pode não seguir exatamente o número solicitado de imagens |
| **Idiomas** | Melhor performance em: EN, pt-BR, es, fr, de, ja, ko, zh, ar, hi, id, it, ru, uk, vi |
| **SynthID watermark** | **Todas** as imagens geradas incluem marca d'água digital invisível (SynthID) |

### SynthID Watermark

Todas as imagens do Nano Banana 2 contêm uma marca d'água digital **invisível** (não afeta a qualidade visual), criada pelo Google para identificar conteúdo gerado por IA. Não é possível desativar.

---

## 15. Boas Práticas de Prompt

Extraídas da documentação oficial do Google:

### Regra de ouro: descreva a cena, não liste palavras-chave

❌ **Evite:** `"modelo, blusa, branca, foto, shopee, profissional"`

✅ **Prefira:** `"Modelo feminina brasileira, 25 anos, usando blusa branca de linho de manga curta, em pé em posição de três quartos, estúdio fotográfico com fundo branco limpo e iluminação de aro suave, câmera posicionada na altura dos olhos, enquadramento americano"`

### Estratégias avançadas

| Estratégia | Como aplicar |
|---|---|
| **Seja hiper-específico** | Em vez de "armadura fantasia", diga "armadura élfica com gravuras de prata, gola alta e ombreiras em formato de asa de falcão" |
| **Forneça contexto e intenção** | "Para um anúncio premium de skincare minimalista" → melhor que "crie um anúncio" |
| **Itere e refine** | Use edição multi-turno: "Mantenha tudo, mas deixe a iluminação mais quente" |
| **Use step-by-step** | "Primeiro: fundo. Segundo: modelo. Terceiro: roupa." |
| **Prompt negativo semântico** | Em vez de "sem carros", diga "rua vazia, tranquila, sem tráfego" |
| **Controle a câmera** | Use termos fotográficos: `wide-angle`, `macro shot`, `low-angle perspective`, `bokeh`, `depth of field` |

### Termos de câmera que funcionam

```
wide-angle shot          → plano aberto, cena ampla
macro shot               → detalhe extremo, textura
low-angle perspective    → câmera de baixo para cima, imponente
high-angle shot          → câmera de cima, bird's eye
eye-level                → câmera na altura dos olhos
shallow depth of field   → fundo desfocado (bokeh)
bokeh                    → fundo com círculos de luz desfocados
golden hour lighting     → luz dourada de fim de tarde
studio lighting          → iluminação de estúdio controlada
rim lighting             → luz de contorno
```

---

## 16. Exemplos Completos

### Exemplo 1: Cover Shopee 9:16 básico

```python
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        "Modelo feminina brasileira, 26 anos, cabelos cacheados castanhos, pele morena clara. "
        "Usando camiseta branca de algodão modal com textura suave. "
        "Em pé, posição de três quartos, mão no quadril. "
        "Rua de São Paulo ao entardecer, bokeh suave ao fundo. "
        "Câmera em ângulo médio-americano (cintura para cima). "
        "Luz dourada natural. Fotografia editorial de moda e-commerce. Alta resolução."
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(
            aspect_ratio="9:16",
            image_size="2K"
        )
    )
)

for part in response.parts:
    if part.inline_data:
        img = part.as_image()
        img.save("output/cover_shopee.png")
        print(f"✅ Imagem salva | Tamanho: {img.size}")
```

### Exemplo 2: Com Grounding (tendências reais)

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        "Baseado nas tendências de moda feminina casual brasileira do verão 2026, "
        "crie uma foto editorial de uma modelo usando um look completo tendência, "
        "em cenário urbano brasileiro."
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K"),
        tools=[{"google_search": {}}]
    )
)
```

### Exemplo 3: Replicar produto com múltiplas referências

```python
from PIL import Image

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        "Recrie esta peça de roupa em uma modelo brasileira similar a esta referência, "
        "mantendo todos os detalhes da peça (cor, textura, costuras, estilo). "
        "Use o mesmo tipo de cenário e iluminação da referência editorial.",
        Image.open("input/produto.jpg"),          # a peça
        Image.open("input/modelo_ref.jpg"),        # referência de modelo
        Image.open("input/editorial_ref.jpg"),     # estilo editorial
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K")
    )
)
```

### Exemplo 4: Macro textura de tecido

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        "Close-up macro extremo do tecido tricô bege de ponto rendado. "
        "Mostrar claramente a estrutura dos fios, as lacunas do ponto rendado, "
        "a textura volumosa característica do tricô de agulha grossa. "
        "Fundo levemente desfocado, profundidade de campo rasa. "
        "Luz lateral de estúdio revelando tridimensionalidade da textura. "
        "Ultra-nítido, 4K, fotografia macro."
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="4K"  # máxima qualidade para textura
        )
    )
)
```

### Exemplo 5: REST (cURL completo)

```bash
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent" \
  -H "x-goog-api-key: $GOOGLE_AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Modelo feminina brasileira, blusa branca de algodão, fundo branco estúdio, 9:16, fotografia e-commerce"
      }]
    }],
    "generationConfig": {
      "responseModalities": ["IMAGE"],
      "imageConfig": {
        "aspectRatio": "9:16",
        "imageSize": "2K"
      }
    }
  }' | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
img_data = data['candidates'][0]['content']['parts'][0]['inlineData']['data']
with open('output/resultado.png', 'wb') as f:
    f.write(base64.b64decode(img_data))
print('Salvo em output/resultado.png')
"
```

---

## Links Oficiais

| Recurso | URL |
|---|---|
| 📖 Documentação principal | https://ai.google.dev/gemini-api/docs/image-generation |
| 💰 Pricing | https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-image-preview |
| 📋 Capabilities | https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview |
| 🔁 Batch API | https://ai.google.dev/gemini-api/docs/batch-api#image-generation |
| 🔍 Rate Limits | https://ai.google.dev/gemini-api/docs/rate-limits |
| 🔑 API Keys | https://aistudio.google.com/apikey |
| 🛡️ SynthID | https://ai.google.dev/responsible/docs/safeguards/synthid |
