# Veo — Geração de Vídeo via Gemini API

> Verificado em: **2026-03-07**
>
> Fontes oficiais:
> - [Video generation docs](https://ai.google.dev/gemini-api/docs/video)
> - [Pricing](https://ai.google.dev/gemini-api/docs/pricing)

---

## Modelos recomendados

| Modelo | ID | Observações |
|---|---|---|
| Veo 3.1 Standard | `veo-3.1-generate-preview` | melhor qualidade geral |
| Veo 3.1 Fast | `veo-3.1-fast-generate-preview` | custo menor, iteração rápida |
| Veo 2 | `veo-2.0-generate-001` | fallback estável |

---

## Parâmetros principais (`GenerateVideosConfig`)

| Campo | Valores aceitos |
|---|---|
| `durationSeconds` | `5`, `6`, `7`, `8` |
| `aspectRatio` | `16:9` ou `9:16` |
| `resolution` (Veo 3.1/Fast) | `720p`, `1080p`, `4k` |
| `resolution` (Veo 2) | `720p`, `1080p` |
| `numberOfVideos` | geralmente `1` |

Referências visuais:
- `image`: primeiro frame (image-to-video)
- `lastFrame`: frame final (interpolação)
- `referenceImages`: até **3** imagens de referência

---

## Custos (paid tier)

| Modelo | Preço oficial |
|---|---|
| `veo-3.1-generate-preview` (720p/1080p) | `$0.40/s` |
| `veo-3.1-generate-preview` (4k) | `$0.60/s` |
| `veo-3.1-fast-generate-preview` (720p/1080p) | `$0.15/s` |
| `veo-3.1-fast-generate-preview` (4k) | `$0.35/s` |
| `veo-2.0-generate-001` | `$0.35/s` |

Exemplo de conta rápida:
- Veo 3.1 Fast, 6s, 1080p: `6 x 0.15 = $0.90`
- Veo 3.1 Standard, 8s, 1080p: `8 x 0.40 = $3.20`

---

## Exemplo Python (texto -> vídeo)

```python
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

operation = client.models.generate_videos(
    model="veo-3.1-fast-generate-preview",
    prompt="Modelo feminina caminhando em rua de Sao Paulo ao entardecer, camera acompanhando lateralmente, atmosfera realista",
    config={
        "aspectRatio": "9:16",
        "durationSeconds": "6",
        "resolution": "1080p",
    },
)

while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)

video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("output/video.mp4")
```

---

## Estratégia recomendada de uso

1. Prototipe em `veo-3.1-fast-generate-preview` (custo baixo).
2. Congele prompt/câmera/movimento.
3. Render final em `veo-3.1-generate-preview` quando necessário.
4. Para lotes grandes, estime custo total antes de disparar.

