---
description: Cria prompts do zero para geração de imagens no Nano Banana Pro. Analisa referência (se houver) para manter fidelidade à roupa enquanto recria modelo, pose, cenário e captura com total liberdade criativa.
---

# Create Image (/create-image)

Ao receber o comando `/create-image`, o objetivo é **criar um prompt do zero** para gerar uma imagem nova no Nano Banana Pro. Toda a criatividade é aplicada — modelo, pose, cenário, iluminação, captura — usando o stack completo de skills do projeto.

> ⚠️ A diferença de `/edit-image`: aqui tudo é **criado do zero**. Se houver referência, ela serve apenas para **extrair a roupa** — todo o resto é reinventado.

---

## Etapa 1: Classificar o Tipo de Criação

### Tipo A — Criação com Referência de Roupa
**Trigger:** O usuário envia uma foto junto com o comando, ou aponta para um diretório com fotos.

O que fazer:
- A foto é referência da **ROUPA**, não da cena
- Extrair a roupa com máxima precisão (Skill `moda`)
- Ignorar completamente: modelo, pose, cenário e iluminação da foto original
- Criar tudo novo com as skills `ecommerce` e `realismo`

### Tipo B — Criação Pura (Sem Referência)
**Trigger:** O usuário descreve o que quer apenas por texto, sem nenhuma imagem.

O que fazer:
- Construir a descrição da roupa a partir do texto do usuário (Skill `moda`)
- Criar modelo, pose, cenário, iluminação e captura com total autonomia
- Usar as skills `ecommerce` e `realismo` como base criativa

---

## Etapa 2: Analisar a Roupa

### Com referência (Tipo A)

Visualizar a imagem e aplicar a **Skill `moda`** completa:

**Material (O que reforçar):**
- Tipo exato de tecido/construção (ex: heavy knitwear, cotton chambray, fine tricot)
- Cor precisa (ex: "warm terracotta", não "laranja")

**O que NÃO reforçar (O modelo extrai da foto):**
- ❌ **NUNCA** descreva estampas, listras ou desenhos.
- ❌ **NUNCA** descreva o padrão da textura visual (ex: zigzag, ribbed, cables). O texto confunde a IA.

**Construção:**
- Tipo de peça e silhueta
- Decote, gola, mangas, punhos, barra
- Fechamentos e detalhes construtivos
- Camadas (se houver: Layer Stack Pattern da Skill `moda`)

**Comportamento:**
- Como o tecido cai e se move
- Tipo de dobras naturais
- Como interage com o corpo

**Interação com a luz:**
- Matte, sheen, transparent, napped, textured (Light Response Matrix)

### Sem referência (Tipo B)

Extrair do texto do usuário os detalhes da roupa e enriquecer com vocabulário da Skill `moda`. Se o usuário for vago (ex: "uma blusa branca"), aplicar defaults realistas — descrever como se fosse uma peça real:

```
Vago:    "blusa branca"
Preciso: "a relaxed-fit white cotton poplin blouse with a point collar, 
          concealed button placket, and slightly oversized long sleeves 
          rolled at the cuffs. The fabric falls straight with natural 
          wear creases at the elbows."
```

---

## Etapa 3: Criar o Mundo ao Redor

Aqui é onde a criatividade é total. Usar as skills para tomar **todas as decisões criativas**.

### Modelo (Skill `ecommerce` → Brazilian Model Framework)

Montar a descrição da modelo combinando os building blocks:

| Bloco | Decidir |
|-------|---------|
| **Gênero** | Baseado na peça (se ambíguo, perguntar ao usuário) |
| **Idade** | Variar — mid-20s a early 30s como default |
| **Pele** | Variar etnia brasileira a cada prompt — nunca repetir o mesmo padrão |
| **Cabelo** | Tipo e estilo coerente com a vibe da peça |
| **Tipo físico** | Variar naturalmente |
| **Expressão** | Relaxada, mid-moment — nunca sorriso perfeito |

### Pose (Skill `ecommerce` → High-Conversion Poses)

Escolher baseado na peça e contexto:

| Tipo de Peça | Pose Recomendada |
|---|---|
| Vestido / saia | Mid-stride, hair toss, turning away |
| Calça / jeans | Walking, weight on one hip, leaning |
| Blusa / top | Arms crossed loosely, hand on bag strap, adjusting sunglasses |
| Jaqueta / blazer | Coat open walking, hands in pockets, looking down at phone |
| Loungewear | Cross-legged on couch, perched on stool |
| Conjunto | Full walking, stepping off curb, interactive (café, shopping) |

### Cenário e Styling Climático (Skill `ecommerce`)

Escolher rigorosamente baseado no mood e na **estação térmica** da peça. É terminantemente proibido colocar roupas de inverno pesado com styling de verão (ex: tricot grosso com shorts e pernas à mostra) ou cenários incompatíveis. O clima, a luz e as roupas secundárias (calça/short/sapato) DEVEM fazer pleno sentido.

> **Regra de Criatividade:** Seja criativo e altamente específico nos cenários. Não repita sempre a mesma "rua de paralelepípedos" ou "café". Crie ambientes ricos brasileiros (ex: "um pátio de museu de arte contemporânea em São Paulo", "uma calçada charmosa de Ipanema na luz da manhã", "um café colonial no Sul do Brasil com folhas secas de outono").

| Estação / Mood | Styling Secundário Obrigatório (Bottoms/Shoes) | Cenários Recomendados (Invente variantes!) |
|---|---|---|
| Inverno Pesado / Cozy | Botas, calça de couro/jeans escuro, blusa de gola alta por baixo | Café colonial indoor, loft industrial, ruas frias e nubladas, livraria |
| Meia-estação / Urbano | Jeans clássico, bota de cano curto, saia midi, mocassim | Distrito de compras elegante, ruas com árvores de outono, rooftop |
| Verão / Praia / Tropical | Sandálias, rasteiras, pernas à mostra, tecidos fluidos | Calçadão, mercado orgânico ao ar livre, jardim botânico, resort |
| Elegante / Noite | Alfaiataria impecável, salto alto, joias sutis | Restaurante upscale noturno, varanda arquitetônica, interior vintage de luxo |

### Captura (Skill `ecommerce` → 3-Shot System)

Se o usuário não especificar, usar o **3-Shot System** e perguntar qual shot:

| Shot | Quando Usar |
|---|---|
| **Wide (corpo inteiro)** | Default para primeiro prompt, hero shot |
| **Medium (cintura acima)** | Detalhe de fit, segundo prompt do set |
| **Close-up (detalhe)** | Textura, construção, terceiro prompt |

Se o usuário não especificar e for prompt único, usar **Wide** como default (mostra tudo).

### Iluminação & Realismo (Skill `realismo`)

Aplicar as alavancas de realismo:

| Alavanca | Ação |
|---|---|
| **Dispositivo** | Sempre declarar (smartphone ou câmera consumer) |
| **Iluminação natural** | Mista, não-controlada, golden hour como default |
| **Composição orgânica** | Sujeito ligeiramente off-center |
| **Textura de pele** | Poros, leve oleosidade, naturalidade |
| **Momento, não pose** | Mid-action, olhar off-camera |
| **Profundidade imperfeita** | Foco levemente errado no fundo |
| **Artefatos de captura** | Film grain sutil, white balance levemente quente |

**Intensidade default:** Level 2 (Semi-Professional) para e-commerce.

---

## Etapa 4: Gerar o Prompt

### Fidelity Lock (OBRIGATÓRIO quando há referência)

Incluir no prompt para travar a roupa:

```
Keep the clothing exactly as shown in the reference image with 100% 
identical texture, pattern, fit, and proportions. The model, pose, 
and background are completely new and independent from the reference.
```

### Ordem de Montagem

```
1. [Cue de realismo]        ← "A RAW photo" / "Shot on iPhone"
2. [Modelo]                 ← Idade, pele, cabelo, expressão
3. [Roupa completa]         ← 3 dimensões da Skill moda
4. [Fidelity Lock]          ← Se houver referência
5. [Pose]                   ← Ação específica
6. [Cenário]                ← Local + detalhes visuais
7. [Iluminação]             ← Tipo + direção + temperatura
8. [Captura]                ← Câmera/device + ângulo + distância
9. [Marcadores de realismo] ← Grain, pele, foco, composição
```

---

## Etapa 5: Entregar

### Formato de Saída
- **100% em inglês**
- **Máximo 150 palavras**
- **Bloco único** ` ```text ``` ` — copiar com um clique
- **Zero placeholders** — todas as decisões já tomadas

### Proibições
- ❌ Aspect ratio, resoluções (`8K`, `4K`, `ultra HD`)
- ❌ Tags de qualidade (`masterpiece`, `best quality`)
- ❌ Termos NSFW ou descritivos do corpo
- ❌ Múltiplos estilos conflitantes
- ❌ Placeholders `[inserir aqui]`

### Comportamento de Entrega

1. **Uma frase em pt-BR** descrevendo o que foi criado
2. **O prompt em bloco código** pronto para colar
3. **Dica rápida** (opcional) — se houver algo que o usuário possa ajustar para melhorar

---

## Modo Série (Listing Set)

Se o usuário pedir **múltiplas fotos** (ex: "cria um set de 5 fotos para o anúncio"), aplicar a **Listing Set Strategy** da Skill `ecommerce`:

| Imagem | Shot | Pose | Variação |
|--------|------|------|----------|
| 1 | Wide / Hero | Movimento (mid-stride) | 3/4 esquerda |
| 2 | Medium | Casual (weight on hip) | Frontal leve |
| 3 | Wide / Back | Turning away | 3/4 direita |
| 4 | Close-up | Detalhe da textura | Macro |
| 5 | Medium / Lifestyle | Interativo (café, compras) | Perfil |

Cada prompt é entregue em seu próprio bloco, numerado. Mesma modelo, mesma roupa, compatibilidade de cor e mood em todos.

---

## Exemplos

### Tipo A — Com referência (foto de uma jaqueta jeans)

**Usuário:** `/create-image` + foto de jaqueta jeans oversized

> Analisei a jaqueta: denim médio, washed, oversized com bolsos frontais. Criando com modelo brasileira e cenário urbano.

```text
A RAW photo of a Brazilian woman in her late 20s with deep dark skin 
and short textured coils, relaxed confident expression. Wearing an 
oversized stonewashed medium-blue denim jacket with classic point 
collar, exposed brass snap buttons, two chest flap pockets, and 
slightly frayed cuffs. The denim is soft from washing, with natural 
whiskering at the elbows and lighter fading at stress points. The 
jacket falls away from the body with structured volume; sleeves 
pushed up to mid-forearm. Keep the clothing exactly as shown in the 
reference with 100% identical texture, wash, and construction. She 
leans casually against a warm-toned wall on a cobblestone side street, 
one hand in pocket, looking off-camera left. Late afternoon golden 
light from the right. Shot on iPhone, subtle film grain, natural 
skin with visible pores, slightly warm white balance, background 
gently out of focus.
```

### Tipo B — Sem referência

**Usuário:** `/create-image` "vestido preto midi elegante pra cenário noturno"

> Prompt criado: vestido midi preto em crepe, cenário noturno urbano com iluminação quente.

```text
A RAW photo of a Brazilian woman in her early 30s with golden tanned 
skin and long straight dark hair, wearing a fitted black wool crepe 
midi dress with a square neckline, sleeveless cut, and a concealed 
back zipper. The crepe fabric skims the body without clinging, 
creating soft draped folds at the waist and falling straight to 
mid-calf with a clean blind hem. The matte fabric absorbs light 
softly with no specular highlights. She walks mid-stride along a 
rooftop terrace at night, city lights blurred in the background, 
warm Edison string lights overhead creating pools of amber light 
and soft shadows. Slight breeze catches her hair. Shot on iPhone, 
organic composition slightly off-center, film grain, natural skin 
texture, the ambient mix of warm bulb light and cool night sky 
creating subtle color temperature variation.
```
