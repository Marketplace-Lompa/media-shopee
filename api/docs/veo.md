# Veo 3.1 — Geração de Vídeo com Áudio via API Gemini

> Documentação baseada em: https://ai.google.dev/gemini-api/docs/video  
> Atualizada em: Março/2026

---

## O que é o Veo?

**Veo** é o modelo de geração de vídeo de alta fidelidade do Google DeepMind. Disponível via Gemini API, permite criar vídeos cinematográficos a partir de texto, imagem (primeiro frame), ou pares de frames (primeiro + último). O Veo 3.1 é o mais avançado, com **geração nativa de áudio sincronizado**.

---

## Família de Modelos

| Modelo | Model ID (API) | Áudio nativo | Resolução máx. | Custo/segundo |
|---|---|---|---|---|
| **Veo 3.1 Preview** | `veo-3.1-generate-preview` | ✅ | 4K | $0.75 |
| **Veo 3.1 Fast Preview** | `veo-3.1-fast-generate-preview` | ✅ | 1080p | Menor |
| **Veo 2** | `veo-2.0-generate-001` | ❌ | 1080p | $0.35 |

---

## Parâmetros da API

| Parâmetro | Tipo | Valores | Descrição |
|---|---|---|---|
| `prompt` | `str` | texto livre | Descrição do vídeo e áudio |
| `image` | `Image` | objeto imagem | Frame inicial (image-to-video) |
| `lastFrame` | `Image` | objeto imagem | Frame final (interpolar) |
| `referenceImages` | `list[Image]` | até 3 | Imagens de referência de estilo/personagem |
| `video` | `Video` | objeto vídeo | Vídeo base para extensão |
| `aspectRatio` | `str` | `"16:9"`, `"9:16"` | Proporção do vídeo |
| `durationSeconds` | `str` | `"4"`, `"6"`, `"8"` (Veo 3.1) / `"5"`, `"6"`, `"8"` (Veo 2) | Duração do clipe |
| `resolution` | `str` | `"720p"`, `"1080p"`, `"4k"` | Resolução de saída |
| `personGeneration` | `str` | `"allow_all"`, `"allow_adult"`, `"dont_allow"` | Controle de pessoas |
| `seed` | `int` | qualquer int | Seed para reprodutibilidade aproximada |
| `negativePrompt` | `str` | texto livre | O que evitar no vídeo |

---

## Importância do Áudio (Veo 3.1)

O Veo 3.1 gera **áudio sincronizado nativamente** — dialogos, efeitos sonoros e ambientes. Controle pelo prompt:

- Diálogos: use aspas — `"A mulher diz: 'Esta blusa é incrível!'"`
- Efeitos sonoros: descreva claramente — `"som de pássaros e brisa suave"`
- Música de fundo: `"música lo-fi tranquila ao fundo"`
- Silêncio: `"sem áudio, silêncio total"`

---

## Exemplos de Código Python

### Instalação

```bash
pip install google-genai python-dotenv
```

### Texto → Vídeo (básico)

```python
import time
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

prompt = """
Modelo feminina brasileira, 25 anos, cabelos escuros, usando blusa branca de linho.
Ela caminha lentamente em direção à câmera em uma rua de São Paulo ao entardecer,
luz dourada, sorriso sutil. Som de cidade ao fundo, passos suaves.
"""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config={
        "aspectRatio": "9:16",
        "durationSeconds": "6",
        "resolution": "1080p",
        "personGeneration": "allow_adult",
    }
)

# Polling — aguardar conclusão
while not operation.done:
    print("Gerando vídeo... aguardando...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Salvar
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("output/video_shopee.mp4")
print("Vídeo salvo em output/video_shopee.mp4")
```

### Imagem → Vídeo (primeiro frame)

```python
from google import genai
from google.genai import types
import time, os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

# Carregar imagem de produto/modelo
with open("input/modelo_blusa.jpg", "rb") as f:
    image_bytes = f.read()

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="A modelo vira levemente para mostrar os detalhes da blusa, brisa suave movendo o tecido",
    image=types.Image(image_bytes=image_bytes, mime_type="image/jpeg"),
    config={
        "aspectRatio": "9:16",
        "durationSeconds": "4",
        "resolution": "1080p",
    }
)

while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)

operation.response.generated_videos[0].video.save("output/produto_animado.mp4")
```

### Primeiro + Último Frame (interpolação)

```python
# Ideal para a skill de FRAMES — criar início e fim e interpolar
with open("input/frame_inicio.jpg", "rb") as f:
    frame_inicio = f.read()
with open("input/frame_fim.jpg", "rb") as f:
    frame_fim = f.read()

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Transição suave entre as duas poses, movimento natural e fluido",
    image=types.Image(image_bytes=frame_inicio, mime_type="image/jpeg"),
    config={
        "lastFrame": types.Image(image_bytes=frame_fim, mime_type="image/jpeg"),
        "aspectRatio": "9:16",
        "durationSeconds": "4",
    }
)
```

### Extensão de Vídeo Existente

```python
with open("output/video_curto.mp4", "rb") as f:
    video_bytes = f.read()

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Continue a cena de forma natural",
    config={
        "video": types.Video(video_bytes=video_bytes, mime_type="video/mp4"),
        "durationSeconds": "4",
    }
)
```

---

## Custo Estimado

| Duração | Modelo | Custo |
|---|---|---|
| 4 segundos | Veo 3.1 | $3.00 |
| 6 segundos | Veo 3.1 | $4.50 |
| 8 segundos | Veo 3.1 | $6.00 |
| 4 segundos | Veo 2 | $1.40 |
| 8 segundos | Veo 2 | $2.80 |

> ⚠️ Vídeo é significativamente mais caro que imagem. Planeje bem antes de gerar em escala.

---

## Boas Práticas de Prompt para Vídeo

### Estrutura ideal

```
[SUJEITO] [APARÊNCIA] [AÇÃO/MOVIMENTO] [AMBIENTE] [CÂMERA] [ÁUDIO]
```

### Exemplo completo (Shopee fashion)

```
Modelo feminina brasileira, 25 anos, cabelos cacheados, usando blusa 
de tricô bege com textura visível. Ela gira lentamente para mostrar 
o tecido, parque ao fundo com árvores e luz de dia. Câmera lenta 
(slow motion) focada na textura do tecido. Som ambiente suave de parque.
```

### Elementos para Moda

- **Movimento do tecido:** `"brisa suave movendo o tecido"`, `"tecido fluindo ao caminhar"`
- **Câmera:** `"close-up na textura"`, `"câmera orbita ao redor"`, `"travelling lateral"`
- **Ação modelo:** `"vira 360 graus"`, `"caminha em direção à câmera"`, `"ajusta o cabelo"`

---

## Limites e Disponibilidade

- ⚠️ Veo **não tem free tier** na API — requer billing habilitado
- ⚠️ Operação **assíncrona** — aguardar conclusão via polling (~2–5 minutos)
- ✅ Disponível no AI Studio (web) para testar antes de usar via API

---

## Links Oficiais

- 📖 [Documentação Veo API](https://ai.google.dev/gemini-api/docs/video)
- 🎬 [Flow — Interface visual para Veo](https://flow.google)
- 💰 [Pricing Gemini API](https://ai.google.dev/pricing)
