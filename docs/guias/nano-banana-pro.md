# Nano Banana Pro — Guia Completo de Boas Práticas, Técnicas e Truques

> **Última atualização:** Fevereiro 2026
> **Fontes:** [Google Blog (oficial)](https://blog.google/products/gemini/prompting-tips-nano-banana-pro/), [DEV Community / Google AI](https://dev.to/googleai/nano-banana-pro-prompting-guide-strategies-1h9n), [awesome-nanobanana-pro (GitHub)](https://github.com/ZeroLu/awesome-nanobanana-pro), [glbgpt.com](https://www.glbgpt.com/hub/the-ultimate-guide-of-nano-banana-pro-prompt/)

---

## Sumário

1. [O que é o Nano Banana Pro](#1-o-que-é-o-nano-banana-pro)
2. [As 4 Regras de Ouro](#2-as-4-regras-de-ouro)
3. [Fórmula Core do Prompt](#3-fórmula-core-do-prompt)
4. [Boas Práticas Gerais](#4-boas-práticas-gerais)
5. [Técnicas Avançadas](#5-técnicas-avançadas)
6. [Iluminação — O Fator Mais Poderoso](#6-iluminação--o-fator-mais-poderoso)
7. [Câmera e Linguagem Cinematográfica](#7-câmera-e-linguagem-cinematográfica)
8. [Consistência de Personagem (Identity Locking)](#8-consistência-de-personagem-identity-locking)
9. [Texto em Imagens (Text Rendering)](#9-texto-em-imagens-text-rendering)
10. [Edição e Restauração](#10-edição-e-restauração)
11. [Alta Resolução e Texturas (4K)](#11-alta-resolução-e-texturas-4k)
12. [Controle Estrutural e Layout](#12-controle-estrutural-e-layout)
13. [Modo Thinking & Reasoning](#13-modo-thinking--reasoning)
14. [🛍️ E-commerce & Moda (Foco Shopee)](#14-️-e-commerce--moda-foco-shopee)
15. [Templates Prontos por Estilo](#15-templates-prontos-por-estilo)
16. [Prompts Negativos (O que Evitar)](#16-prompts-negativos-o-que-evitar)
17. [Erros Comuns de Iniciantes](#17-erros-comuns-de-iniciantes)
18. [Limitações Conhecidas](#18-limitações-conhecidas)
19. [Referências e Recursos](#19-referências-e-recursos)

---

## 1. O que é o Nano Banana Pro

O **Nano Banana Pro** é o modelo de geração de imagens mais avançado do Google, construído sobre o **Gemini 3**. Ele marca a transição de geração de imagens "divertida" para **produção profissional de assets visuais**.

### Capacidades-chave:
- **Text rendering** SOTA (estado da arte) em múltiplos idiomas
- **Consistência de personagem** com até 14 imagens de referência
- **Alta resolução nativa** (1K, 2K, 4K)
- **Edição conversacional** — edite partes da imagem via texto natural
- **Grounding com Google Search** — conhecimento do mundo real
- **Modo "Thinking"** — raciocina antes de renderizar

### Onde usar:
- Gemini App
- Google AI Studio
- Vertex AI
- API direta

---

## 2. As 4 Regras de Ouro

> ⚠️ **O Nano Banana Pro é um modelo "Thinking".** Ele não faz matching de keywords — ele **entende intenção, física e composição**. Pare de usar "tag soups" e comece a agir como um **Diretor Criativo**.

### Regra 1: Edite, Não Regere

Se a imagem está 80% correta, **NÃO gere do zero**. Peça a mudança específica:

```
❌ Gerar prompt inteiro de novo
✅ "Ótimo, mas mude a iluminação para sunset e o texto para neon blue."
```

### Regra 2: Use Linguagem Natural e Frases Completas

Fale com o modelo como se estivesse **briefando um artista humano**:

```
❌ "Cool car, neon, city, night, 8k."
✅ "A cinematic wide shot of a futuristic sports car speeding through 
   a rainy Tokyo street at night. The neon signs reflect off the wet 
   pavement and the car's metallic chassis."
```

### Regra 3: Seja Específico e Descritivo

Prompts vagos geram resultados genéricos:

| Elemento | ❌ Vago | ✅ Específico |
|----------|---------|--------------|
| **Sujeito** | "a woman" | "a sophisticated elderly woman wearing a vintage chanel-style suit" |
| **Material** | "shiny" | "brushed steel with matte finish" |
| **Textura** | "soft" | "crumpled linen paper texture" |

### Regra 4: Dê Contexto (O "Para quem")

O modelo "pensa" — dar contexto ajuda nas decisões artísticas:

```
✅ "Create an image of a sandwich for a Brazilian high-end gourmet cookbook."
```
→ O modelo infere: pratos profissionais, depth of field raso, iluminação perfeita.

---

## 3. Fórmula Core do Prompt

A estrutura ideal segue **7 camadas**, da mais geral à mais específica:

```
[1. Estilo & Direção de Arte]
+ [2. Descrição da Cena / Ambiente]
+ [3. Sujeito Principal (Hero Element)]
+ [4. Câmera, Lente & Controles Cinematográficos]
+ [5. Iluminação]
+ [6. Textura, Cor & Material]
+ [7. (Opcional) Prompts Negativos]
```

### Exemplo completo aplicando a fórmula:

```text
A photorealistic editorial photo [1] of a sun-drenched Brazilian 
coastal café [2] with a young woman in a hand-embroidered linen 
blouse sitting at a marble table [3]. Shot on 85mm f/1.4 at 
eye-level, medium close-up [4]. Golden hour backlighting creating 
warm rim light and long shadows [5]. Visible fabric weave on the 
blouse, glossy marble surface, matte ceramic cup [6]. No blur, no 
distorted hands [7].
```

---

## 4. Boas Práticas Gerais

### ✅ Seja específico, não vago
```
❌ "a cat"
✅ "a fluffy orange British shorthair kitten sitting on a marble 
   countertop, soft morning light"
```

### ✅ Use descrições em camadas
Detalhar **atmosfera + materiais + mood** gera mais profundidade.

### ✅ Use linguagem cinematográfica
O modelo responde **extremamente bem** a terminologia de cinema e fotografia.

### ✅ Descreva a iluminação com cuidado
Iluminação é o **fator de influência mais forte** no Nano Banana Pro.

### ❌ Não sobrecarregue o prompt
Instruções demais podem confundir o modelo. Foque nos elementos essenciais.

### ✅ Especifique composição e aspect ratio
```
"A 9:16 vertical poster"
"A cinematic 21:9 wide shot"
```

### ✅ Defina o papel de cada imagem de referência
```
"Use Image A for the character's pose, Image B for the art style, 
and Image C for the background environment."
```

---

## 5. Técnicas Avançadas

### 5.1. Multi-Prompt Weighting (Pesos)
Enfatize detalhes específicos:
```
(sharp focus:1.3)
(glowing eyes:1.5)
(background blur:0.8)
```

### 5.2. Layering de Cenas Complexas
Ideal para storytelling ou sequências cinematográficas — descreva cada elemento separadamente.

### 5.3. Controle de Perspectiva
| Tipo | Uso |
|------|-----|
| `aerial` | Vista aérea, paisagens |
| `worm's-eye` | Ângulo de baixo, monumentalidade |
| `over-the-shoulder` | Intimidade, narrativa |
| `extreme close-up` | Detalhes, texturas |
| `low-angle shot` | Poder, autoridade |

### 5.4. Color Science (Ciência de Cor)
O modelo reage fortemente a termos de color grading de cinema:
- `teal & orange` — cinemático moderno
- `noir palette` — monocromático dramático
- `pastel diffusion` — suave, editorial
- `muted earth tones` — orgânico, natural
- `high saturation pop art` — vibrante, impacto

### 5.5. Engenharia de Texturas e Materiais
Útil para prompts de render 3D:
```
"glossy finish", "matte ceramic", "brushed aluminum", 
"raw silk texture", "crumpled paper", "wet asphalt reflection"
```

---

## 6. Iluminação — O Fator Mais Poderoso

A iluminação é o **parâmetro que mais afeta o resultado** no Nano Banana Pro.

### Tipos de Iluminação e Quando Usar

| Iluminação | Efeito | Uso Ideal |
|-----------|--------|-----------|
| `soft lighting` | Suave, sem sombras duras | Retratos, moda |
| `golden hour backlighting` | Rim light dourado, sombras longas | Editorial, lifestyle |
| `volumetric rays` | Raios de luz visíveis | Atmosfera, drama |
| `neon glow` | Brilho colorido artificial | Urbano, cyberpunk |
| `studio softbox` | Iluminação profissional controlada | E-commerce, produto |
| `overcast diffused` | Luz difusa sem direção forte | Natural, casual |
| `dramatic side lighting` | Alto contraste lateral | Fashion, retrato artístico |
| `backlight with lens flare` | Contraluz com reflexo | Cinematográfico |
| `cold overcast afternoon` | Luz fria, inverno | Moody, melancólico |
| `flash from camera` | Flash direto, brilho em superfícies | Backstage, evento |

### Exemplo prático para moda:
```
"Soft directional light from the left, creating gentle shadows 
that define the fabric folds. Warm color temperature (5500K). 
No harsh highlights on the model's skin."
```

---

## 7. Câmera e Linguagem Cinematográfica

### Lentes e Distância Focal

| Lente | Uso |
|-------|-----|
| `24mm wide-angle` | Ambientes, arquitetura |
| `35mm` | Street style, lifestyle |
| `50mm f/1.8` | Look natural, e-commerce clean |
| `85mm f/1.4` | Retratos, bokeh cremoso |
| `135mm` | Compressão, beleza de moda |
| `200mm telephoto` | Separação sujeito/fundo extrema |

### Abertura (Depth of Field)
```
"shallow depth of field (f/1.8)" → fundo muito borrado
"deep focus (f/11)" → tudo nítido
```

### Exemplos de linguagem cinematográfica:
```
"Shot on Canon EOS R5 with 50mm f/1.8 lens"
"Cinematic color grading with muted teal tones"
"Film grain, slightly desaturated, Kodak Portra 400 look"
"Low-angle shot with shallow depth of field"
```

---

## 8. Consistência de Personagem (Identity Locking)

O Nano Banana Pro suporta **até 14 imagens de referência** (6 com alta fidelidade).

### Best Practices:

1. **Declare explicitamente:**
   ```
   "Keep the person's facial features exactly the same as Image 1."
   ```

2. **Separe identidade de expressão:**
   ```
   "Same face as Image 1, but change expression to excited and surprised."
   ```

3. **Para múltiplos personagens:**
   ```
   "Keep the attire and identity consistent for all 3 characters, 
   but their expressions and angles should vary."
   ```

### Exemplo — Thumbnail Viral:
```text
Design a viral video thumbnail using the person from Image 1. 
Face Consistency: Keep the person's facial features exactly the same 
as Image 1, but change their expression to look excited and surprised. 
Action: Pose the person on the left side, pointing towards the right. 
Subject: On the right, place a high-quality image of the product. 
Graphics: Add a bold yellow arrow connecting the finger to the product. 
Background: A blurred, bright kitchen background. High saturation.
```

### Exemplo — Storyboard Consistente:
```text
Create a 9-part story with 9 images featuring a woman in an 
award-winning luggage commercial. Emotional highs and lows. 
The identity of the woman and her attire must stay consistent 
throughout but seen from different angles and distances. 
Generate images one at a time. 16:9 landscape format.
```

---

## 9. Texto em Imagens (Text Rendering)

O Nano Banana Pro tem capacidade **SOTA** para renderizar texto legível e estilizado.

### Best Practices:
- Coloque o texto desejado **entre aspas** no prompt
- Especifique a **fonte** (sans-serif, serif, handwritten)
- Especifique **posição** (top, centered, bottom)
- Especifique **cor e estilo** (bold, outline, drop shadow)
- **Limite a 3 palavras** para melhor taxa de sucesso (75% de acerto)
- Para 4-8 palavras: ~40% de acerto
- Para 9+ palavras: ~15% de acerto

> 💡 **Dica profissional:** Para controle 100% do texto, gere a imagem sem texto e adicione o texto no Photoshop/Figma depois.

### Exemplo:
```text
The headline 'URBAN EXPLORER' rendered in bold, white, sans-serif font 
at the top. Use a thick white outline and drop shadow.
```

---

## 10. Edição e Restauração

### O modelo não precisa de máscara manual — basta descrever a mudança:

| Técnica | Prompt |
|---------|--------|
| **Remoção de objeto** | "Remove the tourists from the background and fill with matching cobblestones" |
| **Mudança de estação** | "Turn this scene into winter. Keep the architecture, add snow and cold lighting" |
| **Colorização** | "Colorize this B&W photo with warm vintage tones" |
| **Mudança de horário** | "Turn this scene into nighttime" |
| **Foco seletivo** | "Focus on the flowers" |
| **Mudança de iluminação** | "Change to sunset golden hour backlighting" |
| **Adaptação de aspect ratio** | "Adapt this vertical image to 16:9 landscape, extending the scene naturally" |

### Exemplo de edição conversacional:
```
Geração 1: "A woman in a red dress walking through a garden"
Edição 2:  "Great, but change the dress to emerald green"
Edição 3:  "Now make it nighttime with string lights"
```

---

## 11. Alta Resolução e Texturas (4K)

O Nano Banana Pro suporta geração nativa de **1K a 4K**.

### Best Practices:
- Solicite explicitamente a resolução: `"4K resolution"`, `"suitable for large-format print"`
- Descreva detalhes de alta fidelidade: imperfeições, texturas de superfície
- Use para wallpapers, prints de grande formato, assets de produção

### Exemplo:
```text
A breathtaking atmospheric environment of a mossy forest floor. 
Complex lighting effects and delicate textures, every strand of moss 
and beam of light rendered in pixel-perfect resolution suitable for 
a 4K wallpaper.
```

---

## 12. Controle Estrutural e Layout

Imagens de input podem controlar **composição e layout** (não apenas referência de personagem).

### Usos:
| Input | Output |
|-------|--------|
| Sketch a mão | Anúncio finalizado |
| Wireframe UI | Mockup high-fidelity |
| Grid 64x64 | Pixel art / Sprite sheet |
| Rascunho de layout | Poster profissional |

### Exemplo:
```text
Create a high-end magazine advertisement for a luxury brand based 
on this hand-drawn sketch. Keep the exact layout of the bottle 
and text placement, but render in photorealistic style.
```

---

## 13. Modo Thinking & Reasoning

O Nano Banana Pro usa um processo de **"Thinking"** onde gera imagens intermediárias (não cobradas) para refinar a composição antes do output final.

### Funcionalidades:
- Resolver equações visualmente
- Analisar dados e gerar infográficos
- Deduzir estados "antes/depois"
- Resolver problemas espaciais e lógicos

---

## 14. 🛍️ E-commerce & Moda (Foco Shopee)

> **Esta é a seção mais relevante para o projeto MEDIA-SHOPEE.**

### 14.1. Virtual Model Try-On

Veste uma modelo em uma peça específica preservando textura e integração de iluminação.

```text
Using Image 1 (the garment) and Image 2 (the model), create a 
hyper-realistic full-body fashion photo where the model is wearing 
the garment. 

Crucial Fit Details: The [T-shirt/Jacket] must drape naturally on 
the model's body, conforming to their posture and creating realistic 
folds and wrinkles.

High-Fidelity Preservation: Preserve the original fabric texture, 
color, and any logos from Image 1 with extreme accuracy.

Seamless Integration: Blend the garment into Image 2 by perfectly 
matching the ambient lighting, color temperature, and shadow direction.

Photography Style: Clean e-commerce lookbook, shot on a Canon EOS R5 
with a 50mm f/1.8 lens for a natural, professional look.
```

### 14.2. Foto de Produto Profissional (Studio Shot)

Isola o produto de fundos bagunçados e coloca em studio profissional.

```text
Identify the main product in the uploaded photo (automatically 
removing any hands holding it or messy background details). 
Recreate it as a premium e-commerce product shot.

Subject Isolation: Cleanly extract the product, completely removing 
any fingers, hands, or clutter.

Background: Place the product on a pure white studio background 
(RGB 255, 255, 255) with a subtle, natural contact shadow at the 
base to ground it.

Lighting: Use soft, commercial studio lighting to highlight the 
product's texture and material. Ensure even illumination with no 
harsh glare.

Retouching: Automatically fix any lens distortion, improve sharpness, 
and color-correct to make the product look brand new and professional.
```

### 14.3. Lookbook Editorial para Shopee

```text
A RAW photo, editorial fashion shoot of a [descrever modelo: idade, 
etnia, cabelo], wearing [DESCRIÇÃO DETALHADA DA ROUPA]. 

Keep the clothing exactly as shown in the reference image with 100% 
identical texture, pattern, fit, and proportions. The model, pose, 
and background are completely new and independent from the reference.

[POSE: standing casually / walking confidently / seated elegantly].
[CENÁRIO: Brazilian urban street / modern café / beach boardwalk].

Shot on iPhone, film grain, natural skin texture, hyperrealistic, 
natural lighting, anatomically correct hands, exactly 5 fingers, 
indistinguishable from reality.
```

### 14.4. Produto Flutuante (Flatlay Criativo)

```text
Create an e-commerce-ready image of [clothing item] floating 
horizontally in the air, descending, looking weightless, without 
human presence, surreal and not subject to gravity, with soft 
lighting and a minimalist, elegant style. White background. 
Ultra-HD quality, 4:5 aspect ratio.
```

### 14.5. Cenários Lifestyle para Moda

```text
Show this [clothing item] on a street-style fashion background with 
blurred pedestrians and warm sunlight. Emphasize clean composition 
and clear focus on the outfit. Muted colors, soft urban lighting, 
casual, modern vibe.
```

### 14.6. Foto de Produto Premium com Sombra

```text
A full-body, centered portrait of a model wearing [clothing item]. 
The subject is lit with volumetric studio lighting that creates 
deep definitions, realistic shadows, and a strong 3D quality on 
the folds of the outfit. Seamless, pure high-key white studio 
backdrop. High contrast. Focused ONLY on the subject. Standard 
portrait lens (approx. 50mm equivalent).
```

### 14.7. Brand Asset Generation (Série de 9 fotos)

```text
Create 9 stunning fashion shots as if they're from an award-winning 
fashion editorial. Use this reference as the brand style but add 
nuance and variety to the range so they convey a professional 
design touch. Please generate nine images, one at a time.
```

### 14.8. Diretivas de Fidelidade de Roupa (OBRIGATÓRIO)

Sempre inclua uma destas para travar a roupa e liberar o resto:

| Variação | Texto |
|----------|-------|
| **Padrão** | `"Keep the clothing exactly as shown in the reference image with 100% identical texture, pattern, fit, and proportions. The model, pose, and background are completely new."` |
| **Alternativa 1** | `"Preserve every garment detail from the reference — fabric, color, pattern, silhouette. Everything else is new."` |
| **Alternativa 2** | `"The outfit must be a 1:1 exact match to the reference. The person and setting are entirely different."` |

---

## 15. Templates Prontos por Estilo

### 📸 Realismo Cinematográfico
```
[Realistic Style] + [Hero Subject] + [Environment Mood] 
+ [Camera & Lens] + [Lighting] + [Textures]

Exemplo: A photorealistic woman explorer standing at the entrance 
of an ancient temple, shot on 35mm film, golden-hour rim lighting, 
dusty warm tones, dramatic shadows.
```

### 🎨 Anime & Estilizado
```
[Anime Type] + [Character Description] + [Pose] 
+ [Scene] + [Color Palette] + [Effects]

Exemplo: Vibrant anime girl with silver hair and blue eyes, 
dynamic running pose, futuristic Tokyo street, neon reflections, 
pastel glow.
```

### 🧴 Product Rendering
```
[Product Type] + [Angle] + [Lighting Setup] 
+ [Material] + [Surface] + [Brand Aesthetic]

Exemplo: Minimalist skincare bottle, shot in 45° angle, soft 
diffused light, matte ceramic texture, floating on glossy water.
```

### 💎 Luxury Product Photography
```
Product: [BRAND] [PRODUCT NAME] - [bottle shape], [label description]
Scene: Luxury product shot floating on dark water with [flower type] 
in [colors] arranged around it. [Lighting style] creates reflections 
and ripples across the water.
Mood & Style: [Adjectives], high-end commercial photography, 
[camera angle], shallow depth of field with soft bokeh background.
```

### 👕 E-commerce Fashion (Template do Projeto)
```text
A RAW photo, [ESTILO] of a [MODELO: rosto + cabelo], wearing 
[ROUPA: descrição fiel à referência]. Keep the clothing exactly 
as shown in the reference image with 100% identical texture, 
pattern, fit, and proportions. The model, pose, and background 
are completely new and independent from the reference. [POSE]. 
[CENÁRIO]. Shot on iPhone, film grain, natural skin texture, 
hyperrealistic, natural lighting, anatomically correct hands, 
exactly 5 fingers, indistinguishable from reality.
```

---

## 16. Prompts Negativos (O que Evitar)

Adicione ao prompt para reduzir erros:

### Negativos Técnicos (sempre incluir):
```
No blur, no extra limbs, no distorted hands, no artifacts, 
no incorrect anatomy, no low detail, no washed-out backgrounds.
```

### Negativos Anti-NSFW (para moda):
| ✅ PERMITIDO | ❌ PROIBIDO |
|-------------|------------|
| "skin texture", "natural pores" | "tight-fitting", "body-hugging" |
| "RAW photo", "film grain" | "curves", "voluptuous", "busty" |
| "anatomically correct hands" | "sensual", "seductive", "alluring" |
| "hyperrealistic", "natural lighting" | "provocative", "sultry" |

> **Regra:** Descreva a **ROUPA** e como ela cai — nunca o **corpo**.

---

## 17. Erros Comuns de Iniciantes

| # | Erro | Solução |
|---|------|---------|
| 1 | **Tag soup** (`"dog, park, 4k, realistic"`) | Use frases completas e narrativas |
| 2 | **Estilos conflitantes** ("photorealistic anime watercolor") | Escolha UM estilo dominante |
| 3 | **Esquecer a iluminação** | SEMPRE defina tipo e direção da luz |
| 4 | **Não especificar distância focal** | Inclua a lente (`85mm f/1.4`) |
| 5 | **Excesso de adjetivos** | Foque nos que causam mais impacto visual |
| 6 | **Ignorar composição** | Defina enquadramento (`medium close-up`, `wide shot`) |
| 7 | **Regerar do zero** quando a imagem está 80% boa | Use edição conversacional |
| 8 | **Não dar contexto** ("for a cookbook") | Explique o "para quê" |
| 9 | **Prompt muito longo** (200+ palavras) | Limite a ~150 palavras focadas |
| 10 | **Descrever o corpo** ao invés da roupa | Foque na peça, tecido e caimento |

---

## 18. Limitações Conhecidas

O Google reconhece oficialmente estas limitações (em constante melhoria):

| Área | Limitação |
|------|-----------|
| **Texto pequeno** | Renderizar texto muito pequeno ou longas frases pode falhar |
| **Ortografia** | Erros de spelling podem ocorrer (especialmente em idiomas não-inglês) |
| **Dados e fatos** | Infográficos podem conter dados incorretos — sempre verificar |
| **Tradução** | Texto multilíngue pode ter erros gramaticais ou culturais |
| **Edições complexas** | Blending e mudanças de iluminação podem gerar artefatos |
| **Consistência facial** | Geralmente confiável, mas pode variar entre edições |
| **Mãos** | Mesmo com `"anatomically correct hands"`, pode falhar |

---

## 19. Referências e Recursos

### 📚 Fontes Oficiais
- [Google Blog — 7 Tips for Nano Banana Pro](https://blog.google/products/gemini/prompting-tips-nano-banana-pro/)
- [DEV Community — Nano Banana Pro: Prompting Guide & Strategies (Google AI)](https://dev.to/googleai/nano-banana-pro-prompting-guide-strategies-1h9n)
- [Nano Banana Pro Developer Tutorial](https://dev.to/googleai/introducing-nano-banana-pro-complete-developer-tutorial-5fc8)

### 🧪 Repositórios e Guias da Comunidade
- [awesome-nanobanana-pro (GitHub)](https://github.com/ZeroLu/awesome-nanobanana-pro) — Prompts curados por categoria
- [The Ultimate Guide of Nano Banana Pro Prompt](https://www.glbgpt.com/hub/the-ultimate-guide-of-nano-banana-pro-prompt/) — Fórmulas e templates
- [r/PromptEngineering — Nano Banana Pro Guide](https://www.reddit.com/r/PromptEngineering/comments/1pid4cs/nano_banana_pro_ultimate_prompting_guide/)

### 🛠️ Ferramentas
- [Google AI Studio](https://aistudio.google.com/) — Interface para testar prompts
- [Nano Banana Pro no Vertex AI](https://cloud.google.com/vertex-ai) — Uso em produção via API

---

> 💡 **Dica final:** Este documento é um **guia vivo**. À medida que novas técnicas surgirem ou o modelo for atualizado, atualize as seções relevantes. O Nano Banana Pro evolui rapidamente.
