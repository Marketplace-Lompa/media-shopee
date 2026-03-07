---
description: Gera 3 prompts completos de e-commerce para Shopee (hero wide, medium waist-up, macro textura) a partir de uma imagem de referência de produto, com escolhas criativas autônomas de pose, cenário e captura.
---

# Shopee (/shopee)

Ao receber o comando `/shopee`, o agente analisa a imagem de referência e entrega **3 prompts prontos** para a sessão completa de fotos de capa Shopee — sem que o usuário precise pedir cada shot individualmente.

> ⚠️ Este workflow é **autônomo e criativo**: decide poses, cenário e enquadramento sem perguntar. Para edições iterativas (mudar um eixo específico), use `/edit-image`.

---

## 🚨 REGRA DE OURO HERDADA: A IMAGEM É A AUTORIDADE

> **A imagem de referência é a fonte primária da roupa — NÃO o texto.**

- O Fidelity Lock vai **PRIMEIRO** em cada um dos 3 prompts
- Descrição textual da roupa: máximo 2 frases de reforço por prompt
- Quanto mais texto descreve roupa, mais o AI ignora a imagem de referência

---

## Etapa 1: Localizar a Imagem

A imagem de referência pode vir de:
- **Anexo direto** — enviada junto com o comando
- **Diretório do projeto** — usuário menciona pasta (`input/`, `shopee_downloads/`)
- **Contexto anterior** — imagem baixada por `/puxar-foto-shopee`

Se nenhuma imagem for encontrada, **peça ao usuário** antes de prosseguir.

---

## Etapa 2: Coletar Informações Extras (opcional)

Verificar se o usuário forneceu detalhes que a **imagem não pode comunicar sozinha**:
- Composição do fio (ex: "fio modal", "100% algodão", "viscose")
- Nome da cor (ex: "marsala", "verde sage") se ambígua na referência
- Detalhe construtivo específico que o usuário queira destacar

Se não foram fornecidos, prosseguir sem perguntar — o Fidelity Lock e a imagem cuidam do resto.

---

## Etapa 3: Análise Rápida (exibir ao usuário)

Antes de entregar os prompts, mostrar em pt-BR em 2-3 linhas:
- Peça identificada (tipo + cor)
- Reforço de fibra (se fornecido pelo usuário)
- Confirmação dos 3 shots que serão gerados

---

## Etapa 4: Gerar os 3 Prompts

> 🧠 **Inteligência Sazonal:** Antes de gerar, defina mentalmente a **estação do ano** da peça principal. O cenário, as roupas secundárias (calça/short/bota) e o clima DEVEM respeitar o contexto térmico da roupa (referência: seção *Seasonal & Contextual Styling Intelligence* da skill `ecommerce`). É terminantemente proibido colocar roupas de inverno pesado com styling de verão (ex: tricot grosso com shorts e pernas de fora) ou cenários incompatíveis.

> 🎨 **Variação Criativa:** Não use sempre "cobblestone street". Invente cenários brasileiros ricos e variados (ex: varanda de um loft em Pinheiros, um café colonial no Sul, um jardim botânico, uma livraria moderna, etc).

Cada prompt segue esta **ordem obrigatória**:
```
1. FIDELITY LOCK   → PRIMEIRO. Declara a imagem como autoridade da roupa.
2. Shot config     → Tipo de enquadramento e ângulo do shot específico
3. ecommerce       → Modelo brasileiro, pose escolhida pelo agente, cenário
4. realismo        → Dispositivo, iluminação natural, imperfeições orgânicas
5. moda (reforço)  → MÁXIMO 2 frases — apenas fibra/material + tipo de ponto + cor
```

**Regra do reforço textual (obrigatória nos 3 shots):**
| ✅ Colocar em texto | ❌ NUNCA colocar em texto (destrói a fidelidade) |
|---|---|
| Fibras/material: modal, poliéster, lã, algodão | **Desenhos/Estampas:** listras, floral, xadrez, logos |
| Tipo de construção: tricot, malha leve/pesada, ponto grosso | **Padrões de textura:** zigzag, diamond, openwork, tranças |
| Cor base exata: camel, marsala, sage, off-white | **Relevos ou visual:** como o tecido se parece visualmente |

> 🚨 **DICA DE OURO:** O modelo nano captura o *desenho* e a *textura* perfeitamente da imagem. Se você escrever "striped" ou "zigzag", ele vai ignorar a foto e gerar listras genéricas por cima. Descreva apenas a "vibe/natureza" do material (ex: "heavy winter knit", "fine modal tricot").

### Shot 1 — Hero Wide (scroll-stopper)

**Propósito:** Primeira imagem do listing. Para o scroll. Mostra a peça completa com energia e contexto de vida.

**Especificações fixas:**
- Enquadramento: full-body ou joelho até acima da cabeça
- Pose: **mid-stride walking** — corpo ao ângulo 3/4, um braço em movimento, torso levemente rotacionado
- Ângulo de câmera: ligeiramente abaixo do nível dos olhos (elongating, aspirational)
- Cenário e Luz: Escolha um cenário brasileiro **criativo e específico** e uma iluminação que combinem 100% com o clima/estação da roupa (fuja de clichês repetitivos).
- Modelo e Styling: brasileira, 20s, pele/cabelo (variar a cada sessão) + **roupas secundárias (bottom/sapatos) adequadas ao clima da peça principal**.

### Shot 2 — Medium Waist-Up (fit + qualidade)

**Propósito:** Mostra o fit no busto, o decote, a manga e a textura de perto. Constrói confiança na qualidade.

**Especificações fixas:**
- Enquadramento: da cintura até ligeiramente acima da cabeça
- Pose: **weight shift casual** — peso em um quadril, mão tocando levemente o cabelo ou repousando na lateral, olhar direto para a câmera com expressão relaxada e confiante
- Ângulo de câmera: eye level, 3/4
- Mesmo cenário, modelo e **styling secundário apropriado ao clima** do Shot 1 (consistência do listing)
- Lente equivalente: 50mm (sem distorção)
- Realismo: foco ligeiramente mais suave no fundo que no Shot 1

### Shot 3 — Macro Textura (prova de qualidade)

**Propósito:** Elimina a dúvida "é barato?". Mostra o fio, o relevo e a construção com tangibilidade.

**Especificações fixas:**
- Enquadramento: tecido preenche 90% do frame, sem modelo visível
- Foco: sharp no centro do tecido, profundidade de campo muito rasa
- Luz: rasante lateral golden hour — cria micro-sombras nos vales entre pontos e relevos
- Fundo: completamente desfocado (bokeh quente)
- Sem cenário, sem modelo — apenas o tecido vestido no corpo como suporte
- Reforço de fibra obrigatório neste prompt (o AI não deduz fibra da imagem)

---

## Boas Práticas Shopee

| Aspecto | Shopee (este workflow) |
|---------|------------------------|
| **Cenário na capa** | ✅ Aceito e incentivado — lifestyle converte |
| **Fundo** | Livre — cenário real, urbano, indoor |
| **Poses** | Dinâmicas — movimento gera maior conversão |
| **Realismo** | Level 2 (Semi-Professional) como default |
| **Elementos extras** | Tolerado — mas não incluir no prompt para não poluir |
| **Marca d'água** | Tolerada pelo Shopee, mas não gerar no prompt |

> **Diferença crítica vs ML:** no Shopee, a foto de capa **pode e deve** ter cenário lifestyle. A restriction de fundo branco liso é exclusiva do Mercado Livre.

---

## Regras de Saída

### Formato
- **3 prompts numerados** — cada um em seu próprio bloco ` ```text ``` `
- **100% em inglês** dentro dos blocos
- **Parágrafo único contínuo** — sem quebras de linha internas no bloco
- **Máximo 150 palavras por prompt**
- **Zero placeholders** — todas as decisões tomadas antes de entregar

### Proibições (herdadas do `/edit-image`)
- ❌ Aspect ratio, resoluções (`8K`, `4K`, `ultra HD`)
- ❌ Tags de qualidade forçadas (`masterpiece`, `best quality`)
- ❌ Termos NSFW ou descritivos do corpo
- ❌ `"tight-fitting"`, `"body-hugging"`, `"form-fitting"`, `"skin-tight"`
- ❌ `"curves"`, `"voluptuous"`, `"busty"`, `"cleavage"`
- ❌ `"sensual"`, `"seductive"`, `"sultry"`, `"provocative"`

### Permitido (e encorajado)
- ✅ `"skin texture"`, `"natural pores"`, `"realistic skin"`
- ✅ `"RAW photo"`, `"film grain"`, `"natural lighting"`
- ✅ `"anatomically correct hands"`, `"exactly 5 fingers"`

---

## Exemplo Completo

**Usuário:** `/shopee` + foto da blusa de tricot camel com padrão zigzag + "fio modal"

**Resposta:**

> Blusa de tricot camel identificada — padrão zigzag + losango aberto, crop com barra ribbed. Fio modal fornecido. Gerando 3 prompts para sessão Shopee.

**Shot 1 — Hero Wide**
```text
REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. Reproduce the clothing exactly as shown in the attached reference photo. Follow the texture and stitch pattern exactly as shown — do not invent or describe the pattern, copy it from the reference image. Only the model, pose, and background are new. Full-body shot of a young Brazilian woman in her mid-20s with light warm brown skin and wavy dark shoulder-length hair, relaxed confident expression. She walks mid-stride on a cobblestone street with warm colonial architecture, body at 3/4 angle, one arm swinging naturally, looking slightly off-camera with a soft smile. Paired with dark indigo high-waist straight jeans. Golden hour side lighting. Shot on iPhone, natural film grain, visible skin pores, slightly warm white balance, background softly out of focus. Reinforcement only: warm camel-toffee modal tricot crop top.
```

**Shot 2 — Medium Waist-Up**
```text
REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. Reproduce the clothing exactly as shown in the attached reference photo. Follow the texture and stitch pattern exactly as shown — do not invent or describe the pattern, copy it from the reference image. Only the pose and framing are new. Medium shot framed from waist to just above head, same young Brazilian woman with light warm brown skin and wavy dark shoulder-length hair. Weight shifted to her right hip, left hand loosely touching her hair at the shoulder, torso at 3/4 angle facing the camera, looking directly at the lens with a relaxed confident expression and a subtle closed-lip smile. Same cobblestone street, golden hour side lighting. Shot on iPhone, natural film grain, visible skin pores, slightly warm white balance, background softly out of focus at 50mm equivalent. Reinforcement only: warm camel-toffee modal tricot crop top.
```

**Shot 3 — Macro Textura**
```text
REFERENCE IMAGE IS THE AUTHORITY FOR THE GARMENT. Reproduce the exact knit fabric from the reference photo. Follow the texture and stitch pattern exactly as shown — do not invent or describe the pattern, copy it from the reference image. Extreme macro close-up of the knit surface worn on the torso, fabric filling 90% of the frame. Sharp focus on fabric at center, very shallow depth of field, surrounding area in soft warm bokeh. Warm golden side light raking across the surface to reveal the fabric dimensional texture. Reinforcement only: warm camel-toffee modal tricot knit, crop length with ribbed hem band. Shot on iPhone macro mode, natural side lighting, slight film grain.
```
