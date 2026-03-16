# Controle de Ângulo de Câmera e Novel View Synthesis

> Pesquisa sobre como girar a câmera/gerar múltiplos ângulos de uma imagem mantendo
> fidelidade de produto, no Nano Banana e em outras APIs disponíveis.

---

## 1. Estado atual: Nano Banana (`gemini-3.1-flash-image-preview`)

**Não existe parâmetro nativo de câmera.** Todo controle de ângulo é via engenharia de prompt.

### O que funciona via prompt

```text
# Frente → Costas
"Same model, same garment, rear view / back shot, same lighting"

# Frente → Lateral 3/4
"Three-quarter view from the right side, same model and outfit"

# Multi-turn (mais confiável para consistência)
Passo 1: gerar imagem frontal
Passo 2: enviar a imagem como referência + "back view of the same model and garment"
```

### Limites do prompt engineering
- Sem garantia de identidade exata da modelo entre shots
- Sem controle de azimuth/elevation em graus
- Resultado varia por tentativa — não é determinístico
- Melhor resultado com **multi-turn** (imagem anterior como referência)

### `REFERENCE_TYPE_CONTROL` no `imagen-3.0-capability-001`
O modelo Vertex AI tem controles estruturais (`face_mesh`, `canny_edge`, `scribble`),
mas **não inclui controle de pose ou câmera** — serve para guiar composição, não viewpoint.

---

## 2. Alternativas com controle estruturado

### Kling API — `camera_control` (vídeo)

```json
{
  "camera_control": {
    "type": "simple",
    "config": {
      "horizontal": 10,   // pan esquerda/direita (-10 a 10)
      "vertical": 0,      // tilt cima/baixo (-10 a 10)
      "zoom": 0,          // zoom in/out (-10 a 10)
      "tilt": 0,          // inclinação lateral (-10 a 10)
      "roll": 0,          // rotação em torno do eixo (-10 a 10)
      "pan": 0            // pan orbital (-10 a 10)
    }
  }
}
```

**Problema:** Output é **vídeo** (MP4), não imagem estática.
Para extrair frame específico: `ffmpeg -ss 00:00:01 -i output.mp4 -frames:v 1 frame.png`

Endpoint: `POST https://api.kling.ai/v1/images/generations` ou `/v1/videos/image2video`

**Custo:** ~$0.028–$0.036 por segundo de vídeo. Para 5s = ~$0.14–$0.18.

---

### Stable Virtual Camera (SEVA) — NVS real

O único modelo open-weight com controle verdadeiro de novel view synthesis.

- **Paper:** Stability AI, 2025
- **Input:** 1–N imagens de uma cena
- **Output:** vídeo orbitando a cena com azimuth/elevation em graus
- **Controle:** trajetória de câmera customizável
- **Requer:** self-hosting (GPU A100/H100)
- **Sem SaaS:** não existe endpoint comercial — só Replicate (quando disponível) ou instância própria
- **Foco:** cenas 3D gerais, não especializado em moda/produto

```python
# Pseudo-código via Replicate (quando disponível)
import replicate
output = replicate.run(
    "stability-ai/stable-virtual-camera",
    input={
        "image": open("product.png", "rb"),
        "azimuth_start": 0,
        "azimuth_end": 180,  # girar 180 graus
        "elevation": 15,
        "num_frames": 24,
    }
)
```

---

### Veo 2/3 — Vídeo orbital via prompt

```text
"Slowly orbit around the product 360 degrees, maintaining the same lighting"
```

Output é vídeo. Mesma limitação do Kling para extração de frame estático.
Sem parâmetro de câmera estruturado na API pública.

---

## 3. Estratégia atual do projeto: multi-turn prompt

O pipeline atual (`hero_front → back_or_side → functional_detail`) já usa a abordagem
mais confiável para Nano Banana: **enviar a imagem anterior como referência visual**.

```python
# Pipeline v2 — lógica de multi-angle via referência
# Imagem 1 (hero_front): gerada a partir das fotos brutas do produto
# Imagem 2 (back_or_side): gerada com imagem 1 como referência adicional
# Imagem 3 (functional_detail): close-up do detalhe mais importante da peça
```

### Prompts por slot

```text
# hero_front
"Full body front view, Brazilian fashion model, studio white background, soft directional light"

# back_or_side (+ imagem front como referência)
"Same model and garment from the previous image — rear view / back shot.
 Keep identical lighting, background, and garment fidelity."

# functional_detail
"Close-up crop of the [garment detail] — texture visible, soft focus background"
```

---

## 4. Decisão de implementação

| Abordagem | Controle | Custo | Viável agora? |
|-----------|---------|-------|--------------|
| Prompt engineering Nano Banana | Baixo | Grátis | ✅ Já em uso |
| Multi-turn (imagem anterior como ref) | Médio | Grátis | ✅ Já em uso |
| Kling `camera_control` | Alto | ~$0.14/set | ⚠️ Vídeo, requer extração |
| SEVA (Stability AI) | Muito alto | Self-host GPU | ❌ Inviável (infra) |
| Imagen 3 `REFERENCE_TYPE_CONTROL` | Médio | $0.02/img | ⚠️ Sem controle de câmera |

**Conclusão:** Para o pipeline atual, o multi-turn via Nano Banana é a abordagem certa.
Não vale introduzir dependência de Kling ou SEVA para extração de frames estáticos.

Se no futuro houver necessidade de **360° view determinístico em produção**,
o path seria: Kling image2video → `ffmpeg` frame extraction → pipeline existente.

---

## 5. Melhoria incremental recomendada

Adicionar `grounded_images` do slot anterior como referência nos slots seguintes,
que o pipeline v2 já suporta via `grounded_images` param em `generate_images()`.

Isso garante que `back_or_side` e `functional_detail` tenham acesso visual ao
`hero_front` gerado, aumentando consistência de garment sem custo extra.

---

*Pesquisa realizada em 2026-03-15. Fontes: Kling API docs, Stability AI SEVA paper, Vertex AI docs, Gemini API docs.*
