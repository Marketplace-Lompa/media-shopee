# Imagen 3 Subject Customization — Vertex AI para E-commerce de Moda

> Pesquisa sobre upgrade do gerador de imagens: do Nano Banana (Gemini API pública)
> para o Imagen 3 Subject Customization (Vertex AI), com foco em fidelidade de produto.

---

## 1. Modelo a usar

| Modelo | Finalidade | Subject Customization |
|--------|-----------|----------------------|
| `imagen-3.0-generate-001` | Geração text-to-image pura | ❌ |
| `imagen-3.0-fast-generate-001` | Geração rápida / baixo custo | ❌ |
| `imagen-3.0-capability-001` | Edição, customização, referências | ✅ **único que suporta** |
| `imagen-4.0-generate-001` | Geração nova geração | ❌ |
| `virtual-try-on-001` | Try-on de roupas em pessoa fornecida | caso específico |

**`imagen-3.0-capability-001` é o único modelo com Subject Customization.**

---

## 2. Como funciona: múltiplas fotos da mesma peça

### Regra crítica: mesmo `referenceId` para fotos da mesma peça

Quando você fornece frente + costas + detalhe de textura da mesma peça, todas usam **`referenceId: 1`**. O modelo constrói uma representação multiview interna da peça, melhorando fidelidade na saída. Até 4 slots de referência por request, mas cada slot aceita N fotos.

### Endpoint REST

```
POST https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/us-central1/publishers/google/models/imagen-3.0-capability-001:predict
```

### Payload completo

```json
{
  "instances": [
    {
      "prompt": "Professional catalog photo of the garment [1] worn by a Brazilian fashion model, white studio background, soft directional lighting, full-body shot",
      "referenceImages": [
        {
          "referenceType": "REFERENCE_TYPE_SUBJECT",
          "referenceId": 1,
          "referenceImage": { "bytesBase64Encoded": "BASE64_FRENTE" },
          "subjectImageConfig": {
            "subjectType": "SUBJECT_TYPE_PRODUCT",
            "subjectDescription": "knit wrap cardigan, olive green and dusty rose vertical stripes, open front, cocoon silhouette"
          }
        },
        {
          "referenceType": "REFERENCE_TYPE_SUBJECT",
          "referenceId": 1,
          "referenceImage": { "bytesBase64Encoded": "BASE64_COSTAS" },
          "subjectImageConfig": {
            "subjectType": "SUBJECT_TYPE_PRODUCT",
            "subjectDescription": "knit wrap cardigan, olive green and dusty rose vertical stripes, open front, cocoon silhouette"
          }
        },
        {
          "referenceType": "REFERENCE_TYPE_SUBJECT",
          "referenceId": 1,
          "referenceImage": { "bytesBase64Encoded": "BASE64_DETALHE_TEXTURA" },
          "subjectImageConfig": {
            "subjectType": "SUBJECT_TYPE_PRODUCT",
            "subjectDescription": "knit wrap cardigan, olive green and dusty rose vertical stripes, open front, cocoon silhouette"
          }
        }
      ]
    }
  ],
  "parameters": {
    "sampleCount": 4,
    "negativePrompt": "blurry, distorted fabric, wrong color, watermark",
    "seed": 42
  }
}
```

### Tipos de referência disponíveis

| `referenceType` | Uso |
|----------------|-----|
| `REFERENCE_TYPE_SUBJECT` | Preservar identidade do produto/pessoa |
| `REFERENCE_TYPE_STYLE` | Guiar estilo visual |
| `REFERENCE_TYPE_CONTROL` | Guiar composição (canny, face mesh) |
| `REFERENCE_TYPE_RAW` | Imagem base para edição direta |
| `REFERENCE_TYPE_MASK` | Máscara para inpainting |

### Tipos de sujeito

| `subjectType` | Uso |
|--------------|-----|
| `SUBJECT_TYPE_PRODUCT` | ✅ Produtos, objetos, peças de roupa |
| `SUBJECT_TYPE_PERSON` | Pessoas, rostos |
| `SUBJECT_TYPE_ANIMAL` | Animais |
| `SUBJECT_TYPE_DEFAULT` | Genérico |

---

## 3. Autenticação: migrar de API Key para Vertex AI

O SDK `google-genai` é o mesmo — só muda como o `Client()` é inicializado.

### Desenvolvimento local (ADC)

```bash
gcloud auth application-default login
gcloud config set project SEU_PROJECT_ID
```

```python
from google import genai

client = genai.Client(
    vertexai=True,
    project="seu-project-id",
    location="us-central1"
)
```

### Via variáveis de ambiente (zero alteração de código)

```bash
# .env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=seu-project-id
GOOGLE_CLOUD_LOCATION=us-central1
# GOOGLE_AI_API_KEY continua para Nano Banana (Gemini API pública)
```

```python
# Sem mudança de código — SDK detecta a env var
client = genai.Client()
```

### Produção (Service Account)

```python
from google import genai
from google.oauth2.service_account import Credentials

credentials = Credentials.from_service_account_file(
    "/path/to/sa.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
client = genai.Client(
    vertexai=True,
    project="seu-project-id",
    location="us-central1",
    credentials=credentials
)
```

---

## 4. Custos

| Modelo | Preço por imagem |
|--------|-----------------|
| `imagen-3.0-capability-001` | **$0.02/imagem** |
| `imagen-3.0-generate-001` | $0.04/imagem |
| `imagen-3.0-fast-generate-001` | $0.02/imagem |
| Gemini API (`gemini-3.1-flash-image-preview`) | **Gratuito** (com limites de RPM) |

**Com 100 imagens/dia → ~$2/dia (~$60/mês) no capability-001.**

---

## 5. Limitações confirmadas

- **Máximo 4 slots de referência por request** (cada slot = 1 referenceId; mas aceita N fotos por slot com mesmo ID)
- **Rate limit:** 20 requests/minuto por modelo
- **Regiões:** `us-central1`, `europe-west2`, `asia-northeast3`
- **Sem free tier:** pago desde a primeira imagem no Vertex AI
- **Aspect ratio:** não controlado diretamente nos params — segue resoluções fixas do modelo (1024×1024, 896×1280, etc.)

### Casos que NÃO funcionam bem (documentação oficial)
- Preservar identidade de duas ou mais pessoas simultaneamente
- Combinar múltiplos produtos com preservação simultânea de estilo
- Constraints composicionais muito específicos com control images

### Casos que funcionam bem para moda
- ✅ Produto em fundo branco → produto em nova cena
- ✅ Produto flat lay → produto sendo vestido
- ✅ Variação de cena/fundo mantendo a peça fiel
- ✅ Múltiplas perspectivas da peça → melhor fidelidade

---

## 6. Módulo Python pronto para uso

```python
"""
Imagen 3 Subject Customization — gerador de fotos de produto
Arquivo: app/backend/imagen3_generator.py
"""
import base64
import os
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import requests
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request as GoogleAuthRequest
from PIL import Image as PILImage

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION   = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL      = "imagen-3.0-capability-001"
ENDPOINT   = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
    f"/locations/{LOCATION}/publishers/google/models/{MODEL}:predict"
)


def _get_access_token() -> str:
    creds, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(GoogleAuthRequest())
    return creds.token


def _to_base64(img: bytes | str | Path, max_px: int = 1024) -> str:
    if isinstance(img, (str, Path)):
        img = Path(img).read_bytes()
    with PILImage.open(BytesIO(bytes(img))) as pil:
        pil = pil.convert("RGB")
        w, h = pil.size
        scale = min(1.0, max_px / max(w, h))
        if scale < 1.0:
            pil = pil.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
        buf = BytesIO()
        pil.save(buf, "JPEG", quality=88, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()


def generate_product_shots(
    product_images: List[bytes | str | Path],
    prompt: str,
    product_description: str,
    n_images: int = 4,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
) -> List[bytes]:
    """
    Gera fotos de produto em novas cenas usando Subject Customization.

    - product_images: lista de fotos da peça (frente, costas, detalhe...)
                      todas usam referenceId=1 para fidelidade máxima
    - prompt: descreva a cena; use [1] para referenciar o produto
    - product_description: descrição textual da peça (ancora identidade)
    """
    refs = [
        {
            "referenceType": "REFERENCE_TYPE_SUBJECT",
            "referenceId": 1,
            "referenceImage": {"bytesBase64Encoded": _to_base64(img)},
            "subjectImageConfig": {
                "subjectType": "SUBJECT_TYPE_PRODUCT",
                "subjectDescription": product_description,
            },
        }
        for img in product_images
    ]

    if "[1]" not in prompt:
        prompt = prompt.rstrip(".") + " featuring the product [1]."

    params: dict = {"sampleCount": max(1, min(4, n_images))}
    if negative_prompt:
        params["negativePrompt"] = negative_prompt
    if seed is not None:
        params["seed"] = seed

    payload = {
        "instances": [{"prompt": prompt, "referenceImages": refs}],
        "parameters": params,
    }

    resp = requests.post(
        ENDPOINT,
        headers={
            "Authorization": f"Bearer {_get_access_token()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()

    return [
        base64.b64decode(p["bytesBase64Encoded"])
        for p in resp.json().get("predictions", [])
        if "bytesBase64Encoded" in p
    ]


def virtual_try_on(
    person_image: bytes | str | Path,
    garment_image: bytes | str | Path,
    n_images: int = 4,
) -> List[bytes]:
    """
    Coloca uma peça específica em uma pessoa específica.
    Mais especializado que Subject Customization para esse caso.
    """
    endpoint = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/publishers/google/models/virtual-try-on-001:predict"
    )
    payload = {
        "instances": [{
            "personImage":   {"image": {"bytesBase64Encoded": _to_base64(person_image)}},
            "productImages": [{"image": {"bytesBase64Encoded": _to_base64(garment_image)}}],
        }],
        "parameters": {
            "sampleCount": max(1, min(4, n_images)),
            "personGeneration": "allow_adult",
            "safetySetting": "block_none",
            "addWatermark": False,
        },
    }
    resp = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {_get_access_token()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return [
        base64.b64decode(p["bytesBase64Encoded"])
        for p in resp.json().get("predictions", [])
        if "bytesBase64Encoded" in p
    ]
```

---

## 7. Quando usar cada abordagem

| Cenário | Melhor abordagem |
|---------|-----------------|
| Gerar foto de catálogo a partir de várias fotos da peça | **Subject Customization** (`capability-001`) |
| Colocar roupa específica em modelo humano específico | **Virtual Try-On** (`virtual-try-on-001`) |
| Prompt editorial complexo + cena detalhada | **Nano Banana atual** (mais flexível) |
| Testes, volume moderado, sem billing GCP | **Nano Banana atual** (gratuito) |
| Fidelidade máxima de produto em produção | **capability-001** ($0.02/img) |
| Edição pontual de imagem existente | **Nano Banana atual** (`edit_image`) |

---

## 8. Próximos passos para testar

1. **Criar projeto GCP** com billing habilitado
2. **Habilitar a API:** `Vertex AI API` no console
3. **Autenticar:** `gcloud auth application-default login`
4. **Adicionar ao `.env`:**
   ```
   GOOGLE_CLOUD_PROJECT=lompa-media-shopee
   GOOGLE_CLOUD_LOCATION=us-central1
   ```
5. **Copiar `imagen3_generator.py`** para `app/backend/`
6. **Testar com o poncho:**
   ```python
   imgs = [Path("app/tests/samples/poncho-ruana-listras/IMG_3321.jpg"),
           Path("app/tests/samples/poncho-ruana-listras/IMG_3325.jpg"),
           Path("app/tests/samples/poncho-ruana-listras/IMG_3328.jpg")]

   results = generate_product_shots(
       product_images=imgs,
       prompt="Catalog photo of knit cardigan [1] on a Brazilian female model, white studio, full body",
       product_description="knit wrap cardigan, olive green and dusty rose vertical stripes, open front, cocoon silhouette, crochet texture",
       n_images=4,
   )
   ```

---

*Pesquisa realizada em 2026-03-15. Fontes: Vertex AI docs, google-genai SDK, pgaleone.eu.*
