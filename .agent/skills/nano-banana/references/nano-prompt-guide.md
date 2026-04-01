# Nano Banana — Guia de Prompting para Agentes

> **Documento operacional.** Este guia é a referência única para agentes que montam prompts de geração e edição de imagens no stack Gemini/Imagen (Nano Banana). Consolida as skills `nano-banana`, `ecommerce`, `moda` e `realismo` + mode identities num formato de execução sequencial.

---

## 0. Princípio Fundacional

O Gemini é **literalista e narrativo**. Ele lê o prompt como uma cena descrita por um diretor de fotografia, não como uma lista de tags. Toda decisão de prompt deve seguir esta regra:

> **Descreva o que a câmera VERIA, não o que você QUER que aconteça.**

---

## 1. Seleção de Modelo

Antes de escrever qualquer prompt, selecione o modelo correto:

| Modelo | ID | Quando Usar | Resoluções |
|---|---|---|---|
| **Nano Banana** | `gemini-2.5-flash-image` | Iteração rápida, muitas variantes, budget alto volume | `1K` |
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | **Padrão de produção.** Melhor equilíbrio velocidade/qualidade, grounding, multi-ref | `512`, `1K`, `2K`, `4K` |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | Alta fidelidade, tipografia, composição complexa, polimento premium | `1K`, `2K`, `4K` |

**Atalho de decisão:**
- Foto de moda para e-commerce → **Nano Banana 2** (`thinkingLevel: high` para texturas complexas)
- Logo, poster com texto → **Nano Banana Pro**
- 20 variações rápidas de cor → **Nano Banana**

---

## 2. Anatomia do Prompt — Sequência Obrigatória

Monte o prompt nesta ordem exata. **Cada camada é uma frase ou bloco separado.** Não misture camadas.

```
┌─────────────────────────────────────────────────┐
│ CAMADA 1 — Sujeito + Ação                       │
│ CAMADA 2 — Vestuário (com regras da skill moda) │
│ CAMADA 3 — Ambiente + Contexto                  │
│ CAMADA 4 — Câmera + Composição                  │
│ CAMADA 5 — Luz + Mood                           │
│ CAMADA 6 — Travas de Fidelidade                 │
│ CAMADA 7 — Specs de Output                      │
└─────────────────────────────────────────────────┘
```

### Camada 1 — Sujeito + Ação
**O que a câmera vê no centro do frame.**

```text
A [idade] Brazilian [gênero] with [tom de pele], [tipo de cabelo], [tipo corporal], [expressão].
Ela está [AÇÃO em andamento — nunca estática].
```

**Regra:** A ação deve ser um **gerúndio observável** (walking, reaching, adjusting), não um estado ("looking confident").

### Camada 2 — Vestuário
**Regra crítica: separe o modo de operação.**

| Situação | Modo | Regra |
|---|---|---|
| Imagem de referência disponível | **EDIT** | Fidelity Lock PRIMEIRO + máximo 2 frases de reforço (fibra + construção + cor) |
| Sem referência | **CREATE** | Framework completo de 3 dimensões (Material + Construção + Comportamento) |

**Fidelity Lock (modo EDIT):**
```text
REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. Reproduce the clothing
exactly as shown in the attached reference photo. Follow the texture and
stitch pattern exactly as shown — do not invent or describe the pattern,
copy it from the reference image. Only the model, pose, and background are new.
```

**Reforço permitido (máximo 2 frases):**
- ✅ Fibra/material: "heavy winter knitwear in wool blend"
- ✅ Construção: "chunky cable-knit construction"
- ✅ Cor precisa: "deep burgundy"
- ❌ NUNCA descreva padrão visual (listras, xadrez, zigzag) — o modelo sobrescreve a referência

**Modo CREATE — as 3 Dimensões:**
1. **Material:** fibra + trama + acabamento + comportamento de luz
2. **Construção:** costuras + fechamentos + gola + manga + punho
3. **Comportamento:** caimento + cling + volume + reação da gravidade

### Camada 3 — Ambiente + Contexto
**O cenário conta uma história. Deve ser coerente com a estação da peça.**

| Estação da Peça | Cenário | Anti-Pattern |
|---|---|---|
| Inverno pesado | Cafés, ruas urbanas frias, interiores aconchegantes | ❌ Praia, sol forte, pernas nuas |
| Meia-estação | Golden hour, parques, tardinha urbana | ❌ Neve, calor tropical |
| Alto verão | Praia, mercados a céu aberto, parques tropicais | ❌ Casacos, botas, cenários internos escuros |

**Regra de diversidade:** NUNCA repita o mesmo cenário entre gerações. Rotacione entre ambientes distintos.

### Camada 4 — Câmera + Composição
**Use linguagem fotográfica precisa — nunca adjetivos vagos.**

| Objetivo | Instrução |
|---|---|
| Fashion body shot | `85mm f/1.8, 3/4 body angle, slightly below eye level` |
| Detalhe de textura | `macro lens, close focus, shallow depth of field` |
| Contexto ambiental | `35mm f/2.0, wide environmental portrait` |
| Meio corpo neutro | `50mm f/2.8, eye-level, medium shot from waist up` |

**Regras de ângulo:**
- Default: **15-30° de rotação** (3/4 angle) — NUNCA 0° frontal puro
- Hero shot: ângulo levemente abaixo do olho (empodera)
- Detail shot: eye level (honesto, sem distorção)

### Camada 5 — Luz + Mood
**Descreva luz que ACONTECE, não luz que foi PROJETADA.**

```text
✅ "Late afternoon sunlight entering through a window, creating warm patches
   and long shadows across the scene"
❌ "Perfect studio lighting with softbox setup"
```

| Contexto | Luz |
|---|---|
| Hero / Wide | Golden hour, rim lighting, sombras longas |
| Medium / Fit | Luz difusa de janela, sem sombras duras, cores fiéis |
| Close-up / Texture | Luz lateral controlada, máximo contraste de textura |
| Lifestyle / Action | Luz mista (natural + artificial), inconsistências reais |

### Camada 6 — Travas de Fidelidade
**O que NÃO pode mudar. Essencial em edições e multi-turn.**

```text
Keep [identidade/produto/logo/background/framing/lighting] exactly the same.
Do not modify any other part of the image.
Do not add props, redesign the packaging, or shift the framing.
```

### Camada 7 — Specs de Output

```text
Output: [aspect ratio] format, [resolution].
```

- E-commerce Shopee: retrato 3:4 ou 1:1
- Banner/hero: paisagem 16:9
- Instagram: 1:1 ou 4:5

---

## 3. Regras Absolutas (Nunca Viole)

### 3.1 — Negative Prompts: PROIBIDO

> **Fonte oficial:** [Google Developers Blog](https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/)

O Gemini processa tokens literalmente. Ao escrever "no cars", o modelo **ativa** o conceito "cars" e frequentemente o inclui. Em vez disso, use **negativas semânticas** — descreva positivamente o estado desejado.

| ❌ Negativa Direta (FALHA) | ✅ Negativa Semântica (FUNCIONA) |
|---|---|
| "no background clutter" | "clean, minimal studio backdrop" |
| "no bad anatomy" | "anatomically precise, natural hand posture" |
| "no clouds" | "perfectly clear, solid blue sky" |
| "sem cenário artificial" | "authentic domestic interior with lived-in texture" |
| "no mannequin pose" | "dynamic mid-stride movement, body in natural motion" |
| "avoid AI look" | "subtle film grain, micro-focus variation, slightly off-center composition" |

### 3.2 — Palavras Proibidas

Estas palavras forçam o modelo para "modo AI" e destroem realismo:

```
❌ "ultra realistic"    ❌ "best quality"      ❌ "masterpiece"
❌ "8K" (a menos que suportado)  ❌ "perfect lighting"
❌ "flawless skin"      ❌ "professional photography"
❌ "cinematic" (sem contexto)    ❌ "premium" (sem evidência)
❌ "beautiful"          ❌ "stunning"          ❌ "amazing"
```

**Substitua por instruções observáveis:**
- "cinematic" → `anamorphic lens flare, 2.39:1 frame, shallow depth`
- "premium" → `brushed metal surface, controlled reflections, high-key studio`
- "realistic" → `visible skin pores, natural lens grain, mixed color temperature`

### 3.3 — Descrição de Cena, Não Lista de Tags

```
❌ "woman, street, golden hour, bokeh, 85mm, f/1.4, realistic, premium"
✅ "A young Brazilian woman walking down a cobblestone street in late
   afternoon. Golden sunlight catches her hair from behind, creating
   warm rim lighting. Shot at 85mm f/1.8, natural background blur."
```

### 3.4 — Uma Mudança Por Vez (Multi-Turn)

Ao iterar em edições:
1. Estabeleça a baseline com locks
2. Mude **UMA** variável
3. Restate os locks antes da próxima edição
4. Se a fidelidade derivar, re-ancore com a referência original

---

## 4. Sistema de 3 Shots para E-commerce

Cada listing precisa de **3 shots complementares** em distâncias diferentes.

### Shot 1 — Hero / Wide (Full-Body)
**Propósito:** Scroll-stopper. Primeira impressão.

```text
Full-body wide shot, head to shoes, breathing room above and below.
Model occupies 60-70% of frame height. Dynamic movement pose.
Contextual background that tells a story. 3/4 angle, slightly below eye level.
```

### Shot 2 — Medium / Waist-Up
**Propósito:** Fit, caimento, qualidade do tecido.

```text
Medium shot from waist up. Focus on neckline, sleeve detail, fabric texture.
Relaxed natural expression. Soft background bokeh. ~50mm lens feel.
```

### Shot 3 — Close-Up / Macro
**Propósito:** Elimina dúvida "é barato?".

```text
Extreme close-up of [textura/trama/costura/botão]. Shallow depth of field,
macro-style focus showing individual fibers. The texture must feel tangible.
```

### Extensão (5-7 imagens):

| Shot | Tipo | Propósito |
|---|---|---|
| 4 | **Back View** | Costas, fechamento, caimento traseiro |
| 5 | **Lifestyle / Action** | Modelo usando no contexto real |
| 6 | **Flat Lay** | Produto deitado, visão geral |
| 7 | **Color Variant** | Mesma pose, cor diferente |

---

## 5. Alavancas de Realismo

Para que a imagem pareça **foto real** e não AI, injete **3-5 alavancas** (nunca todas de uma vez).

| # | Alavanca | O que faz | Exemplo no prompt |
|---|---|---|---|
| 1 | **Dispositivo real** | Simula óptica do equipamento | `shot on iPhone 14, natural barrel distortion` |
| 2 | **Luz descontrolada** | Quebra perfeição de estúdio | `mixed warm tungsten and cool daylight, uneven patches` |
| 3 | **Composição orgânica** | Enquadramento humano | `subject slightly off-center, horizon tilted ~1°` |
| 4 | **Textura com defeitos** | Superfícies reais | `visible skin pores, fabric micro-wrinkles from use` |
| 5 | **Momento, não pose** | Captura entre instantes | `mid-gesture, gaze hasn't found the camera yet` |
| 6 | **Foco imperfeito** | Autofoco quase certo | `focus on shoulder instead of eyes, slight depth mismatch` |
| 7 | **Artefatos de captura** | Marca do processo | `subtle film grain in shadows, natural lens vignetting` |
| 8 | **Grain injection** | Corrige AI Softness | `monochromatic grain 1-3%, yarn filaments individually distinct` |

### Calibração por contexto:

| Contexto | Nível | Alavancas | ThinkingLevel |
|---|---|---|---|
| Lifestyle / Social | Nível 1 (casual authentic) | 5-7, alta intensidade | MINIMAL |
| E-commerce / Catálogo | Nível 2 (semi-pro) | 3-4, moderada | MEDIUM |
| Editorial / Lookbook | Nível 3 (natural professional) | 2-3, sutil | MEDIUM |
| Macro / Textura | Nível 3 | Textura + grain + foco | HIGH |

---

## 6. Mode Identities (DNA Visual)

Cada mode tem uma **soul** — a identidade filosófica que guia o agente. Injete a soul relevante no contexto de pensamento, não no prompt visual.

### catalog_clean
> Você é um fotógrafo de produto para catálogo e-commerce premium. A peça é a protagonista absoluta. Tudo — modelo, luz, backdrop — existe apenas para servir a legibilidade da roupa.
- Backdrop deve ser esquecível de propósito
- **Olhar direto para câmera**, sorriso acolhedor, contato visual quente (obrigatório)

### natural
> Você captura uma pessoa real vestindo roupas reais em um lugar real. A câmera é presente mas nunca performática. A cena é QUIETA e o modelo parece alguém que você conheceria. A imagem deve parecer encontrada, não art-directed.
- Cenário = ator coadjuvante, nunca protagonista
- Anti-portrait: NÃO colapsar em retrato estático limpo
- Anti-tableau: evitar lógica de cena contemplativa ou esteticamente pausada
- Anti-repetição: se parece polido ou visualmente auto-consciente demais, está errado

### lifestyle
> Você é o fotógrafo de uma influencer capturando um momento no meio da vida. A modelo ESTÁ FAZENDO algo — a linguagem corporal origina de uma atividade em progresso. Sem atividade, a imagem colapsa em outro mode. O cenário é CO-PROTAGONISTA.
- **Contrato estrutural:** modelo DEVE estar mid-activity (violação se estática)
- Cenário como co-star: o local IMPORTA e conta história
- Aspiration autêntica: "quero estar lá, usando aquilo" — aspiracional mas alcançável
- Anti-repetição: na dúvida, escolha o local INESPERADO

### editorial_commercial
> Você é um diretor de arte de moda fotografando para editorial comercial brasileiro. Cada frame é INTENCIONAL. A composição comunica escolhas deliberadas.
- Sofisticação CONQUISTADA pela composição, não mostrando objetos caros
- Um muro de concreto desgastado com luz perfeita é mais editorial que interior generic de luxo
- Cenário deve ser inconfundivelmente brasileiro mas elevado pela direção de arte

---

## 7. Template Rápido — Prompt Completo

```text
[SHOT TYPE] of a [AGE] Brazilian [GENDER] with [SKIN TONE], [HAIR], [BODY TYPE].
She is [ACTION — gerúndio observável].

[GARMENT — Fidelity Lock OU 3 Dimensões conforme modo EDIT/CREATE]

Setting: [CENÁRIO BRASILEIRO ESPECÍFICO]. [DETALHES AMBIENTAIS].
[COERÊNCIA SAZONAL — peça quente = cenário frio].

Camera: [LENTE] [ÂNGULO] [DISTÂNCIA]. [COMPOSIÇÃO ORGÂNICA — slightly off-center].
Lighting: [LUZ NATURAL DESCRITA COMO ACONTECIMENTO, não design].

[ALAVANCAS DE REALISMO — 3-5 selecionadas por contexto].

[TRAVAS DE FIDELIDADE — o que NÃO pode mudar].

Output: [ASPECT RATIO], [RESOLUTION].
```

---

## 8. Checklist de Validação (Pré-Envio)

Antes de enviar qualquer prompt ao modelo, verifique:

- [ ] Sequência de camadas respeitada (1→7)?
- [ ] Zero negative prompts diretos ("no X", "sem Y")?
- [ ] Zero palavras proibidas ("masterpiece", "8K", "cinematic" vago)?
- [ ] Vestuário: modo correto (EDIT com lock / CREATE com 3D)?
- [ ] Cenário coerente com a estação da peça?
- [ ] Linguagem fotográfica (lentes, f-stop) no lugar de adjetivos vagos?
- [ ] Pelo menos 3 alavancas de realismo ativas?
- [ ] Ação em gerúndio (não pose estática)?
- [ ] ThinkingLevel adequado ao tipo de shot?
- [ ] Modelo brasileiro(a) com diversidade étnica?

---

## 9. Referência Rápida — Edição de Imagem

### Edit Simples (mudar 1 elemento)
```text
Using the provided image, change only [TARGET] to [NEW RESULT].
Keep [identity/product/background/framing/lighting] exactly the same.
Do not modify any other part of the image.
```

### Composição Multi-Referência
```text
Use Image 1 for the model identity and pose.
Use Image 2 for the outfit and fabric behavior.
Use Image 3 for the color palette and set dressing.
Blend into one physically coherent photograph. Not a collage.
```

### Tipografia em Imagem
```text
Create [TYPE] with the exact text "[TEXT]".
Set in [FONT STYLE] at [POSITION].
Ensure fully legible, intentionally designed — not incidental scene detail.
```

**Dica:** Para tipografia complexa, gere o texto em etapa separada, depois solicite a imagem com o texto. Resultados significativamente melhores.

---

## 10. Anti-Patterns Consolidados

| Anti-Pattern | Efeito | Correção |
|---|---|---|
| Lista de tags em vez de cena | Output genérico e inconsistente | Descrever cena narrativa |
| Negative prompts diretos | Modelo ativa o conceito indesejado | Negativa semântica (descrever o desejado) |
| Adjetivos vagos (premium, cinematic) | Modelo não sabe o que renderizar | Instruções fotográficas concretas |
| Descrever padrão visual com referência | Sobrescreve a imagem de referência | Fidelity Lock + só fibra/construção/cor |
| Várias mudanças simultâneas (multi-turn) | Fidelidade desliza entre iterações | Uma variável por vez + restate locks |
| Cenário genérico repetido | Todos os outputs parecem iguais | Inventar local específico a cada geração |
| Estação incoerente (tricô + praia) | Destrói credibilidade | Matrix estação→cenário |
| Quality tags (8K, masterpiece) | Força "modo AI" | Remover completamente |
| Pose 100% frontal 0° | Achata peça e modelo | Default 15-30° de rotação |
| Focus perfeito em tudo | Marca digital de AI | Micro-variação de foco |

---

## 11. Fatos Técnicos do Gemini (Referência)

- Imagens geradas incluem watermark SynthID
- Modelos Gemini 3 sempre usam thinking (não pode desabilitar)
- `gemini-3.1-flash-image-preview` suporta `thinkingLevel`: `minimal` e `high`
- Suporta até **14 referências** total (split entre objeto e personagem)
- Google Search grounding disponível; Image Search grounding apenas no Nano Banana 2
- Output default = texto + imagem; image-only deve ser requisitado explicitamente
- Aspect ratio segue input em edição; default quadrado se não especificado
- `imageSize` usa K maiúsculo: `512`, `1K`, `2K`, `4K` — lowercase é rejeitado
- Thinking gera até **2 thought images** internas (não cobradas, adicionam latência)
- Para texto em imagem: gere conteúdo textual primeiro, depois peça a imagem (resultados muito melhores)

---

## 12. Fluxo de Trabalho para Agentes

```
1. Receber pedido do usuário
2. Identificar mode (catalog_clean / natural / lifestyle / editorial)
3. Carregar soul do mode
4. Determinar: EDIT (com referência) ou CREATE (sem referência)?
5. Selecionar modelo (Nano Banana / 2 / Pro)
6. Montar prompt na sequência de 7 camadas
7. Selecionar 3-5 alavancas de realismo por contexto
8. Rodar checklist de validação
9. Executar geração
10. Se multi-turn: restate locks + alterar UMA variável por vez
```

---

**Fonte das regras:** Skills `nano-banana`, `ecommerce`, `moda`, `realismo` + `mode_identity_soul.py` + [Google Developers Blog — Best Practices](https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/) + [Official Gemini Image Generation Docs](https://ai.google.dev/gemini-api/docs/image-generation).
