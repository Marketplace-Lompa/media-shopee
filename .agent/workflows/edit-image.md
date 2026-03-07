---
description: Edita uma foto existente gerando um prompt otimizado para o Nano Banana Pro. Analisa a imagem de referência e aplica modificações de modelo, pose, cenário ou captura conforme solicitado.
---

# Edit Image (/edit-image)

Ao receber o comando `/edit-image`, o objetivo é **editar uma foto existente** — nunca criar do zero. O workflow analisa a foto de referência, preserva a roupa com fidelidade máxima, e gera um prompt para recriar a imagem com as modificações solicitadas.

> ⚠️ Este workflow é para **EDIÇÃO**. Para criação do zero (sem referência), use o agente `criador-media` diretamente no Mode 2 (Pure Creation).

---

## 🚨 REGRA DE OURO: A IMAGEM É A AUTORIDADE

> **Quando uma imagem de referência está disponível, ela é a fonte primária da roupa — NÃO o texto.**

Este é o erro mais comum e crítico em prompts de edição:
- Descrição textual muito detalhada da roupa **substitui** a referência visual pelo olhar do modelo de IA
- O modelo passa a seguir o texto e **ignora** a imagem
- Resultado: roupa "inventada" baseada nas palavras, não na foto

**A regra:**: texto descreve apenas o que a imagem NÃO pode comunicar sozinha (cor precisa se ambígua, comportamento do tecido). Todo o resto é delegado à imagem.

**Antídoto:** O Fidelity Lock vai PRIMEIRO no prompt, antes de qualquer descrição de roupa.

---

## Etapa 1: Localizar a Imagem

A imagem de referência pode vir de:
- **Anexo direto** — o usuário envia junto com o comando
- **Diretório do projeto** — o usuário menciona um arquivo ou pasta (ex: `input/`, `shopee_downloads/`)
- **Contexto anterior** — imagem baixada por outro workflow (ex: `/puxar-foto-shopee`)

Se nenhuma imagem for encontrada, **pergunte ao usuário** de onde está a referência antes de prosseguir.

---

## Etapa 2: Analisar a Foto

Visualize a imagem e extraia informações usando a **Skill `moda`** (3 Dimensões):

### Dimensão 1 — Material
- Tipo de tecido (ex: cotton poplin, ribbed knit, floral lace over jersey lining)
- Cor precisa (ex: "dusty sage", não "verde")
- Estampa/padrão (tipo, escala, direção, cores)
- Acabamento de superfície (stonewashed, brushed, coated, etc.)

### Dimensão 2 — Construção
- Tipo de peça (blusa, vestido, jaqueta, conjunto)
- Decote, gola, mangas, punhos, barra
- Fechamentos visíveis (botões, zíper, amarração)
- Camadas (se houver: descrever cada camada e relação entre elas)

### Dimensão 3 — Comportamento
- Caimento (drapes loosely, holds structure, clings, skims)
- Tipo de dobras (soft folds, sharp creases, natural wear creases)
- Interação com o corpo (tension, bunching, falling naturally)

---

## Etapa 3: Identificar o que o Usuário Quer Mudar

O usuário pode solicitar mudanças em **um ou mais** destes eixos:

| Eixo | Exemplo de Pedido |
|------|-------------------|
| **Modelo** | "morena", "homem", "mais velha", "cabelo cacheado" |
| **Pose** | "andando", "sentada", "braços cruzados" |
| **Cenário** | "praia", "rua urbana", "café" |
| **Captura** | "mais perto", "corpo inteiro", "de costas" |
| **Iluminação** | "golden hour", "dia nublado", "noturna" |
| **Edição direta** | "troque o fundo", "remova o objeto", "mude a cor" |

### 🔒 Regra de Preservação (OBRIGATÓRIA)

> **O que NÃO foi pedido para mudar, DEVE ser preservado.**

Este é o princípio fundamental do `/edit-image`. Editar significa alterar APENAS os eixos que o usuário mencionou explicitamente. Todos os outros eixos são mantidos idênticos — seja da imagem de referência original, seja do prompt anterior na conversa.

| Situação | Comportamento Correto |
|---|---|
| Usuário pede "outra pose" | Muda APENAS a pose. Modelo, cenário, iluminação e captura ficam iguais |
| Usuário pede "muda o cenário" | Muda APENAS o cenário. Pose, modelo, iluminação e captura ficam iguais |
| Usuário pede "modelo morena, cenário praia" | Muda modelo E cenário. Pose, iluminação e captura ficam iguais |
| Usuário pede "mais realismo" | Intensifica levers do `realismo`. Todo o resto fica igual |

**Em iterações (quando já houve um prompt anterior na conversa):**
- O prompt anterior É a referência. Preservar tudo que não foi pedido para mudar.
- Modelo, cenário, iluminação, captura do prompt anterior são mantidos.
- Apenas substituir o eixo específico mencionado pelo usuário.

### Regra de Delegação ao Agente

**Se o usuário NÃO especificar o DETALHE de um eixo que pediu para mudar** (ex: diz "muda a pose" mas não diz QUAL pose), use os defaults das skills:

| Eixo pedido sem detalhe | Default aplicado (via Skills) |
|---|---|
| "Muda a pose" (sem dizer qual) | `ecommerce` → Movement poses (mid-stride, weight shift) |
| "Troca o modelo" (sem dizer qual) | `ecommerce` → Brazilian model framework: variar etnia, mid-20s |
| "Muda o cenário" (sem dizer qual) | `ecommerce` → Brazilian urban scenario, golden hour |
| "Outra captura" (sem dizer qual) | `ecommerce` → Variar distância/ângulo vs. prompt anterior |
| "Mais realismo" | `realismo` → Aumentar intensidade das levers em +1 nível |

> ⚠️ **Estes defaults SÓ se aplicam aos eixos que o usuário PEDIU para mudar.** Eixos não mencionados = preservados.

---

## Etapa 4: Determinar o Tipo de Prompt

### Tipo A — Recriação com Fidelidade (mais comum)

Quando o usuário quer **manter a roupa** mas recriar a cena base (nova modelo, nova iluminação, etc) do zero. É uma recriação baseada na foto original.

**Usar quando:** "cria uma foto com modelo morena", "muda o cenário inteiro", "gera de novo num estúdio"

**Regra de Preservação no Tipo A:**
- Na **primeira execução**: todos os eixos não mencionados usam defaults das skills
- Em **iterações** (já houve prompt anterior): eixos não mencionados são copiados do prompt anterior
- A **roupa** é SEMPRE preservada (Fidelity Lock)

**Fidelity Lock OBRIGATÓRIO — e SEMPRE PRIMEIRO no prompt:**
```
REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. Reproduce the clothing 
exactly as shown in the attached reference photo. Follow the texture and 
stitch pattern exactly as shown — do not invent or describe the pattern, 
copy it from the reference image. Only the model, pose, and background are new.
```

> ⚠️ **PROIBIÇÃO ABSOLUTA NO REFORÇO TEXTUAL:**
> - ❌ **NUNCA mencione desenhos ou estampas** (listras, floral, xadrez, logos). O modelo nano extrai isso perfeitamente da foto. Descrever o desenho destrói a fidelidade da peça.
> - ❌ **NUNCA descreva padrões de textura ou relevos** (zigzag, tranças, furos, diamond). 
> - ✅ **Descreva APENAS a "vibe" do material:** **fibra/material** (modal, lã, algodão) + **espessura/tipo de construção** (tricot, ponto grosso, malha leve) + **cor precisa**.

### Tipo B — Edição Cirúrgica

Quando o usuário quer **modificar algo específico** na imagem existente que já está **quase pronta**, sem recriar o prompt base.

**Usar quando:** "prompt de ajuste", "apenas alterar [X]", "troca o fundo", "muda a pose"

> 🚨 **REGRA DE GATILHO POSITIVO:** Se o usuário disser EXPLICITAMENTE as palavras **"ajuste"**, **"apenas alterar"** ou **"só muda"**, é OBRIGATÓRIO usar o fluxo Tipo B.

> ❌ **REGRA DE GATILHO NEGATIVO — ANTI-PADRÃO CRÍTICO:**
> **Feedback ou reclamação sobre o resultado NÃO é gatilho para Tipo B.** Se o usuário apontar um problema ("ficou artificial", "manga errada", "pose estranha", "modelo errada"), isso é **Tipo A com a correção incorporada ao prompt completo**.
>
> | Situação | Tipo correto |
> |---|---|
> | "ajuste a manga" | ✅ Tipo B |
> | "só muda o cenário" | ✅ Tipo B |
> | "ta criando manga comprida, o modelo não é assim" | ✅ Tipo A com correção |
> | "ficou artificial demais" | ✅ Tipo A com realismo intensificado |
> | "pose não faz sentido nenhum" | ✅ Tipo A com nova pose |
> | "modelo precisa mudar" | ✅ Tipo A com novo modelo |
>
> **Regra de ouro:** Na dúvida, **Tipo A sempre**. Nunca use Tipo B por padrão ou por preguiça. Tipo B é exceção, não default.

**Prompts de edição são CURTOS** — 1-3 frases diretas:
```
Change the background to a warm-toned cobblestone street at golden hour. 
Keep the model, clothing, pose, and lighting on the subject identical.
```

---

## Etapa 5: Gerar o Prompt

### Para Tipo A (Recriação com Fidelidade):

Montar o prompt na seguinte **ordem obrigatória**:

```
1. FIDELITY LOCK   → PRIMEIRO. Declara a imagem como autoridade da roupa.
2. ecommerce       → Modelo, pose, cenário, captura, composição
3. realismo        → Dispositivo, iluminação natural, imperfeições orgânicas
4. moda (reforço)  → MÁXIMO 2 frases: fibra/material + tipo de construção + cor
                     ❌ NUNCA descreva listras, desenhos, estampas ou texturas visuais
                     ✅ O modelo nano cuida do desenho baseando-se na referência.
                     Ex: "heavy winter knitwear", "fine modal tricot", "cotton poplin".
```

> 🔑 **Lógica:** O Fidelity Lock declara a imagem como lei. O texto depois não precisa repetir o que a imagem já mostra — ele apenas guia o que a imagem não consegue comunicar sozinha (intenção de pose, cenário, clima).

### Para Tipo B (Edição Cirúrgica):

Prompt direto sem descrever a cena inteira — apenas a instrução de mudança.

---

## Regras de Saída

### Formato
- **100% em inglês**
- **Máximo 150 palavras** (Tipo A) ou **50 palavras** (Tipo B)
- Retornar dentro de **bloco único** ` ```text ``` ` para copiar com um clique
- **Zero placeholders** — todas as decisões tomadas antes de entregar

### Proibições
- ❌ Aspect ratio, resoluções (`8K`, `4K`, `ultra HD`)
- ❌ Tags de qualidade forçadas (`masterpiece`, `best quality`)
- ❌ Termos NSFW ou descritivos do corpo (descreva a ROUPA, nunca o corpo)
- ❌ `"tight-fitting"`, `"body-hugging"`, `"form-fitting"`, `"skin-tight"`
- ❌ `"curves"`, `"voluptuous"`, `"busty"`, `"cleavage"`, `"bare skin"`
- ❌ `"sensual"`, `"seductive"`, `"alluring"`, `"sultry"`, `"provocative"`

### Permitido (e encorajado)
- ✅ `"skin texture"`, `"natural pores"`, `"realistic skin"`
- ✅ `"RAW photo"`, `"film grain"`, `"natural lighting"`
- ✅ `"anatomically correct hands"`, `"exactly 5 fingers"`
- ✅ Termos da Skill `realismo` (device cue, organic composition, imperfect depth)

---

## Exemplo Completo

**Usuário:** `/edit-image` + foto de uma blusa de renda areia + "coloca em modelo morena num cenário urbano"

**Resposta:**

> Imagem de referência identificada: blusa de renda floral sobre forro jersey, cor areia. Fidelity Lock primeiro. Descrição textual: apenas reforço mínimo de cor e padrão.

```text
REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. Reproduce the clothing exactly as shown in the attached reference photo. Follow the texture and stitch pattern exactly as shown — do not invent or describe the pattern, copy it from the reference image. Only the model, pose, and background are new. Reinforcement only: warm sand-tone lace blouse, modal fabric, over opaque nude lining. A RAW photo of a Brazilian woman in her mid-20s with warm brown skin and natural wavy dark hair. She walks mid-stride on a cobblestone street lined with warm-toned colonial architecture, looking slightly off-camera with a relaxed expression. Golden hour side lighting. Shot on iPhone, subtle film grain, natural skin with visible pores, slightly warm white balance, focus soft on background.
```
