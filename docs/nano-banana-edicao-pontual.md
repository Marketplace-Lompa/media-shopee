# Nano Banana — Edição Pontual de Imagens Existentes

## Contexto do Projeto

- **Modelo de geração atual**: `gemini-3.1-flash-image-preview` (Nano Banana 2 Preview)
- **Modelo do agente de prompt**: `gemini-3-flash-preview`
- **SDK**: `google-genai` (Python)
- **Fluxo atual**: Geração do zero (text-to-image ou image+text-to-image)

---

## 1. Duas Abordagens Disponíveis para Edição

### 1A. Edição Nativa via Gemini (Nano Banana) — **Recomendada**

O Nano Banana 2 (`gemini-3.1-flash-image-preview`) suporta **edição nativa** de imagens existentes usando a mesma API `generate_content`. Não precisa de máscara explícita — o modelo entende instruções em linguagem natural e modifica pontualmente a imagem.

#### Como funciona

Você envia a **imagem original** + **instrução textual de edição** como `contents`, e o modelo retorna a imagem modificada.

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=API_KEY)

# Carregar a imagem existente (resultado anterior)
with open("gen_abc123_1.png", "rb") as f:
    image_bytes = f.read()

# Prompt de edição pontual
edit_prompt = "Change the background to a warm sunset beach scene, keeping the model and clothing exactly as they are."

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        types.Content(role="user", parts=[
            types.Part(inline_data=types.Blob(
                mime_type="image/png", data=image_bytes
            )),
            types.Part(text=edit_prompt),
        ])
    ],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="1K",
        ),
        safety_settings=SAFETY_CONFIG,
    ),
)
```

#### Pontos-chave

| Aspecto | Detalhe |
|---|---|
| **Máscara** | Não necessária — o modelo infere a região a editar pelo prompt |
| **Preservação** | Alta para elementos não mencionados no prompt |
| **Limitação de refs** | Até 10 objetos com fidelidade + até 14 imagens totais de referência |
| **Multi-turn** | Suportado via `client.chats.create()` para edições iterativas |
| **Resolução** | 0.5K, 1K, 2K, 4K |
| **Aspect ratios** | 1:1, 3:4, 4:3, 9:16, 16:9, 1:4, 4:1, 1:8, 8:1 (3.1 Flash) |

#### Tipos de edição suportados

1. **Trocar fundo/cenário** — Manter modelo e roupa, mudar ambiente
2. **Modificar cor** — Alterar cor de peça, cabelo, fundo
3. **Adicionar/remover elementos** — Adicionar acessório, remover objetos
4. **Ajustar estilo/iluminação** — Warm light, studio, outdoor
5. **Alterar pose** — Re-posicionar a modelo (menor confiabilidade)
6. **Trocar enquadramento** — Converter medium para close-up (moderado)

---

### 1B. Edição com Máscara (Imagen 3 via Vertex AI) — **Alternativa Precisa**

Se precisar de edição **cirúrgica** com controle exato de região, o Imagen 3 via Vertex AI oferece inpainting com máscara explícita.

#### Modos de máscara disponíveis

| Modo | Descrição |
|---|---|
| `MASK_MODE_USER_PROVIDED` | Usuário fornece máscara preto/branco |
| `MASK_MODE_BACKGROUND` | Segmentação automática do fundo |
| `MASK_MODE_FOREGROUND` | Segmentação automática do primeiro plano |
| `MASK_MODE_SEMANTIC` | Máscara por classe semântica (ex: "sky", "person") |

#### Modos de edição

| Modo | Uso |
|---|---|
| `EDIT_MODE_INPAINT_INSERTION` | Adicionar conteúdo na área mascarada |
| `EDIT_MODE_INPAINT_REMOVAL` | Remover conteúdo da área mascarada |

> [!IMPORTANT]
> Imagen 3 (Vertex AI) requer uma conta GCP com billing ativado e usa API diferente (`vertexai` SDK). O Nano Banana (Gemini API) é gratuito/freemium e usa o `google-genai` SDK.

---

## 2. Abordagem Recomendada para o MEDIA-SHOPEE

### Usar Edição Nativa do Nano Banana 2 (Single-turn e Multi-turn)

**Razão**: Já usamos o mesmo SDK (`google-genai`), mesmo modelo, mesma API key. Não precisa de infra adicional.

### 2.1 Single-turn Edit (Edição Pontual Direta)

O fluxo mais simples — o usuário seleciona uma imagem gerada e descreve a mudança:

```
[Imagem Original] + [Prompt de Edição] → [Imagem Editada]
```

**Código-base**:
```python
def edit_image(
    original_image_bytes: bytes,
    edit_prompt: str,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
) -> dict:
    """
    Edita pontualmente uma imagem existente com instrução em linguagem natural.
    Retorna dict com filename, path, size_kb, mime_type.
    """
    content_parts = [
        types.Part(inline_data=types.Blob(
            mime_type="image/jpeg", data=original_image_bytes
        )),
        types.Part(text=edit_prompt),
    ]

    response = client.models.generate_content(
        model=MODEL_IMAGE,
        contents=[types.Content(role="user", parts=content_parts)],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution,
            ),
            safety_settings=SAFETY_CONFIG,
        ),
    )

    # Extrair imagem da resposta (mesmo pattern do generator.py)
    for part in (response.parts or []):
        if getattr(part, "inline_data", None):
            mime = getattr(part.inline_data, "mime_type", "image/png")
            if mime.startswith("image/"):
                return {
                    "data": part.inline_data.data,
                    "mime_type": mime,
                }
    raise RuntimeError("Nano retornou sem imagem na edição")
```

### 2.2 Multi-turn Edit (Edição Iterativa em Conversa)

Para refinamentos progressivos — o usuário faz várias edições na mesma imagem:

```
Turn 1: [Imagem] + "Mude o fundo para praia" → [V1]
Turn 2: "Agora mude a iluminação para golden hour" → [V2]  
Turn 3: "Adicione óculos de sol" → [V3]
```

**Código-base**:
```python
chat = client.chats.create(
    model=MODEL_IMAGE,
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="1K",
        ),
        safety_settings=SAFETY_CONFIG,
    ),
)

# Turn 1: enviar imagem + prompt
with open("original.png", "rb") as f:
    image_data = f.read()

response = chat.send_message([
    types.Part(inline_data=types.Blob(mime_type="image/png", data=image_data)),
    "Change the background to a warm sunset beach scene.",
])

# Turn 2+: apenas texto (modelo mantém contexto da imagem anterior)
response = chat.send_message("Now add warm golden hour lighting.")
response = chat.send_message("Add stylish sunglasses on the model.")
```

> [!TIP]
> **Multi-turn é a abordagem recomendada pelo Google** para edições iterativas. O chat mantém contexto entre turnos, evitando reenvio da imagem.

---

## 3. Boas Práticas de Prompting para Edição

### 3.1 Template de Preservação (Crucial para Moda)

```
"Using the provided image, [AÇÃO ESPECÍFICA]. 
Keep the model's face, body, pose, and the garment details 
(texture, color, draping, construction) exactly as they are. 
Only modify [ELEMENTO ALVO]."
```

### 3.2 Padrões de Prompt por Tipo de Edição

| Edição | Template de Prompt |
|---|---|
| **Trocar fundo** | `"Change only the background to [CENÁRIO]. Keep the model, pose, lighting on the subject, and all garment details (fabric texture, color, draping) exactly as they are."` |
| **Mudar cor da peça** | `"Change the color of the [PEÇA] from [COR_ATUAL] to [COR_NOVA]. Preserve the exact same fabric texture, draping, and construction details."` |
| **Adicionar acessório** | `"Add [ACESSÓRIO] to the model. Keep everything else — pose, expression, clothing, background — exactly the same."` |
| **Remover elemento** | `"Remove [ELEMENTO] from the image. Fill the area naturally with the surrounding context."` |
| **Ajustar iluminação** | `"Adjust the lighting to [TIPO_LUZ] while keeping everything else identical. The light should feel [DESCRIÇÃO]."` |
| **Mudar enquadramento** | `"Reframe this as a [wide/medium/close-up] shot, keeping the model, outfit, and style exactly the same."` |

### 3.3 Anti-patterns (O que NÃO fazer)

> [!WARNING]
> **Evite estes erros comuns:**

| ❌ Anti-pattern | ✅ Correto |
|---|---|
| `"Make it better"` | `"Increase the sharpness and add warm rim lighting from the right"` |
| `"Change everything except the dress"` | `"Change only the background to a minimalist white studio"` |
| Prompt longo com 5+ mudanças simultâneas | Uma mudança por turn (ou 2 no máximo) |
| Não referenciar a imagem original | `"Using the provided image..."` ou `"In this photo..."` |
| Mudar pose + fundo + cor ao mesmo tempo | Fazer em 2-3 turns separados |

### 3.4 Regras de Preservação para E-commerce

Para edições de fotos de moda/e-commerce, sempre incluir no prompt:

```
"IMPORTANT: Preserve exactly:
- The garment's fabric texture, weave pattern, and draping behavior
- The model's skin tone, facial features, and body proportions  
- The original color accuracy of the clothing
- All construction details (seams, closures, neckline shape)
Only modify: [ELEMENTO ALVO]"
```

---

## 4. Limitações e Cuidados

### 4.1 Limitações Técnicas

| Limitação | Impacto |
|---|---|
| **Drift de identidade** | Edições consecutivas podem alterar sutilmente o rosto da modelo |
| **Drift de textura** | Tecido pode perder detalhes finos após 3+ edições |
| **Aspect ratio fixo** | A edição herda o aspect ratio da imagem original |
| **Sem batch** | Edição é sempre 1 imagem por vez (diferente de geração) |
| **Sem máscara explícita** | Nano Banana 2 infere a região; sem pixel-level control |
| **SynthID** | Toda imagem gerada/editada contém watermark SynthID |

### 4.2 Mitigações

1. **Drift de identidade**: Limitar cadeia de edições a 3-4 turns. Se precisar de mais, recomeçar do original.
2. **Drift de textura**: Enviar a imagem original de referência como contexto adicional junto com a editada.
3. **Precisão de região**: Para edições cirúrgicas (ex: mudar só a manga), ser extremamente específico no prompt.

### 4.3 Comparação: Nano Banana 2 vs Imagen 3

| Feature | Nano Banana 2 (Gemini API) | Imagen 3 (Vertex AI) |
|---|---|---|
| **Tipo de edição** | Natural language, sem máscara | Mask-based inpainting |
| **SDK** | `google-genai` | `google-cloud-aiplatform` |
| **Custo** | Gratuito/Freemium | Pay-per-use (GCP billing) |
| **Multi-turn** | ✅ Nativo | ❌ Single-shot |
| **Precisão pixel** | Moderada (infere região) | Alta (máscara explícita) |
| **Resolução max** | 4K | 1024x1024 |
| **Refs simultâneas** | Até 14 | 1 ref + 1 mask |
| **Integração** | Já usamos no projeto | Requer nova infra |

---

## 5. Fluxo UX Proposto para MEDIA-SHOPEE

### 5.1 Interação do Usuário

```
1. Usuário gera imagem normalmente (pipeline atual)
2. Na galeria, vê o resultado
3. Clica em "✏️ Editar" na imagem
4. Abre composer de edição com:
   - Thumbnail da imagem original
   - Campo de texto: "O que deseja mudar?"
   - Botões rápidos: [Trocar Fundo] [Mudar Cor] [Ajustar Luz] [Adicionar Acessório]
5. Envia instrução de edição
6. Pipeline de edição:
   a. Agente otimiza o prompt de edição (preservação automática)
   b. Nano Banana 2 gera imagem editada
   c. Exibe resultado ao lado do original para comparação
7. Usuário pode:
   - Aceitar → Salva como novo resultado
   - Editar novamente → Nova instrução (multi-turn)
   - Cancelar → Volta ao original
```

### 5.2 Pipeline Backend

```
POST /edit (novo endpoint)
├── Recebe: image_url (resultado existente) + edit_instruction
├── Carrega bytes da imagem original do disco
├── [Opcional] Agente otimiza prompt de edição:
│   ├── Adiciona cláusulas de preservação automáticas
│   ├── Traduz instrução pt-BR → prompt EN otimizado
│   └── Detecta tipo de edição para template adequado
├── Chama generate_content com imagem + prompt
├── Salva resultado na mesma session_dir
└── Retorna: novo arquivo + comparação metadata
```

### 5.3 Decisão Arquitetural

| Decisão | Recomendação |
|---|---|
| **Reusar `generator.py`?** | Criar função `edit_image()` separada em `generator.py` |
| **Novo router?** | Sim, `routers/edit.py` — mantém separação de concerns |
| **Agente de prompt** | Reusar `agent.py` com flag `mode=edit` (não criar agente separado) |
| **Multi-turn** | V1 = single-turn edit. V2 = multi-turn chat com histórico |
| **Histórico** | Salvar chain de edições por session para undo/redo |

---

## 6. Referências Oficiais

| Recurso | URL |
|---|---|
| **Documentação oficial Nano Banana** | [ai.google.dev/gemini-api/docs/image-generation](https://ai.google.dev/gemini-api/docs/image-generation) |
| **Image editing (text-and-image-to-image)** | [Seção de editing na doc acima](https://ai.google.dev/gemini-api/docs/image-generation#image-editing) |
| **Multi-turn editing** | [Seção multi-turn na doc acima](https://ai.google.dev/gemini-api/docs/image-generation#multi-turn-image-editing) |
| **Prompting guide** | [Best practices na doc acima](https://ai.google.dev/gemini-api/docs/image-generation#best-practices) |
| **Imagen 3 Inpainting (Vertex AI)** | [cloud.google.com/vertex-ai/generative-ai/docs/image/edit-insert-objects](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/edit-insert-objects) |
| **Notebook de edição Imagen 3** | [GitHub GoogleCloudPlatform](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/vision/getting-started/imagen3_editing.ipynb) |
| **Model selection guide** | [Seção model selection na doc oficial](https://ai.google.dev/gemini-api/docs/image-generation#model-selection) |
