# Análise Fotográfica — Modo Lifestyle

## O Que é Fotografia Lifestyle (na Moda)?

Lifestyle em fotografia de moda é o **espaço entre o paparazzi e o editorial**. Não é uma foto roubada — a modelo **sabe** que está sendo fotografada. Porém, ela não está **posando para a câmera**. Ela está **vivendo um momento**, e o fotógrafo está ali como **testemunha convidada**.

### Referências Reais do Gênero
- **Influencer stories:** A modelo anda pela rua, para num café, verifica o celular — e o fotógrafo (geralmente um amigo) captura isso mid-action
- **BTS (behind the scenes):** Parece bastidor de editorial — a modelo entre sets, ajustando o cabelo, rindo de algo off-camera
- **Street style São Paulo/Rio:** Fotógrafo posicionado na saída de evento, captura a pessoa **andando**, **chegando**, **conversando**
- **Instagram elevated:** Não é selfie, não é profissional — é aquela foto que o namorado/amiga tirou com iPhone mas que ficou **incrivelmente boa**

### DNA Visual do Lifestyle

| Eixo | Lifestyle REAL |
|---|---|
| **Relação com câmera** | A modelo sabe, mas finge que não. Ou olha brevemente, mid-moment. |
| **Pose** | Mid-action: caminhando, ajeitando bolsa, olhando para o lado, sentada casualmente |
| **Câmera** | Social, mid-distance, slight dutch angle, phone-quality ok, BTS energy |
| **Cenário** | CO-PROTAGONISTA — conta história. Bar, rua, praia, carro, varanda de apartamento |
| **Styling** | Intencional mas descontraído — como alguém que "se arrumou para sair" |
| **Maquiagem** | Natural-bonita. "No-makeup makeup" — parece pouca, mas tem. |
| **Calçado** | Parte do look — tênis statement, sandália rasteira bonita, mule |
| **Acessórios** | IMPORTANTES — bolsa, óculos de sol, pulseiras. Lifestyle vende o lifestyle. |
| **Cor/Mood** | Warm, dourado, golden hour, sombras longas, flare de luz |
| **Aspiração** | "Eu quero ser essa garota" — é desejável mas **alcançável** |

---

## Diagnóstico por Camada

### 1. `mode_identity_soul.py` — SOUL do Lifestyle (L41-47)

```
"you are an influencer's photographer capturing a moment mid-life. 
The model is DOING something — walking, arriving, pausing in conversation, 
adjusting sunglasses. The scene is a CO-PROTAGONIST alongside the garment."
```

**Diagnóstico:** ✅ **Excelente.** A soul já captura o DNA corretamente. "Influencer's photographer" é a metáfora perfeita. "Mid-life", "DOING something" — tudo certo.

**Lacunas:**
- 🟡 Falta a regra de **aspiração alcançável** — hoje pode escorregar para editorial aspiracional demais
- 🟡 Falta o conceito de **"foto que seu namorado/amiga tirou"** — a intimidade de quem está ali por afeto, não profissionalmente
- 🟡 Não tem regra anti-editorial explícita: "this is NOT an editorial shoot, it's a life moment that happens to be photographed beautifully"

---

### 2. `model_soul.py` — Casting (L19-94)

**Status:** Universal para todos os modes. Sem overlay condicional para lifestyle (existe apenas para `editorial_commercial`).

**Diagnóstico:** 🟡 **Neutro demais.** O lifestyle precisa de uma modelo que:
- Parece alguém que você **seguiria no Instagram** (não uma modelo de casting)
- Tem **personalidade visual** — cabelo com personalidade, acessório statement, atitude de quem se cuida mas não é "produzida"
- Maquiagem **intencional mas leve** — gloss, blush sutil, sobrancelha feita, rímel. NÃO é zero makeup (isso é natural), mas NÃO é editorial (smokey eye, lip bold)
- Energia de **autoconfiança casual** — sabe que está bonita, não precisa provar

**Sugestão:**
- Overlay condicional para lifestyle com: "no-makeup makeup look — visible lip color, groomed brows, healthy skin, subtle mascara", "she looks like someone with 50k followers, not a signed model", "her energy is self-assured and socially aware, not performing for the camera"

---

### 3. `scene_soul.py` — Cenário (L37-73)

**Status:** Universal. "Follow the active MODE_IDENTITY to decide how much the environment should speak."

**Diagnóstico:** ✅ **Funcional**, mas o lifestyle mereceria um overlay que reforça:
- O cenário deve **contar uma história de onde ela está e por quê** — ela está ali de propósito (num brunch, numa loja, andando no Baixo Augusta)
- O cenário não é ruído — é **contexto narrativo**
- Permitir cenários mais **aspiracionais** que no natural (mas não premium-editorial): beach club popular, bar de bairro cool, feira de design, saída de academia

---

### 4. `pose_soul.py` — Pose (L41-47)

```
"Let the body imply life, momentum, and approachable desirability.
The gesture should feel caught mid-moment rather than arranged for a catalog stand."
```

**Diagnóstico:** ✅ **Bom.** "Mid-moment" e "approachable desirability" estão corretos.

**Lacunas:**
- 🟡 Falta vocabulário de **ações concretas de lifestyle:** entrando num carro, ajustando óculos de sol na cabeça, segurando café pra viagem, verificando notificação no celular, rindo de algo que alguém disse, caminhando com sacola de compras
- 🟡 Principal diferença vs. Natural: no lifestyle a modelo pode **performar levemente** — um olhar de canto, um meio-sorriso, um gesto de cabelo que é consciente. No natural, ela é inconsciente.

---

### 5. `capture_soul.py` — Câmera (L41-47)

```
"Let the camera feel socially alive, approachable, and mid-moment.
The framing can feel closer to an elevated phone or BTS instinct 
than to a formal studio setup."
```

**Diagnóstico:** ✅ **Muito bom.** "Elevated phone" e "BTS instinct" são exatamente a referência certa.

**Lacunas:**
- 🟡 Poderia reforçar: leve **shallow depth of field** (o fundo ligeiramente blurred como num Portrait Mode de iPhone)
- 🟡 A câmera pode estar **mais perto** do que em outros modos — proximidade de quem conhece a pessoa
- 🟡 **Golden hour flare** e **sombras longas** como assinatura de mood — lifestyle é quase sempre fim de tarde

---

### 6. `styling_soul.py` — Styling (L49-55)

```
"Let the styling feel desirable, current, and lived-in.
Small finishing touches can help sell the lifestyle."
```

**Diagnóstico:** ✅ **Correto.**

**Lacuna principal:**
- 🟡 Para lifestyle, **acessórios são mais importantes** que em qualquer outro mode. Uma bolsa, um óculos, um headphone pendurado, uma sacola de loja — esses objetos **contam a história de vida**
- 🟡 O calçado também é **statement**, não utilitário (diferente do natural onde chinelo é ok)

---

### 7. `creative_brief_builder.py` — Pools do Lifestyle (L73-88)

```python
"lifestyle": {
    "scenario_pool": ("textured_city", "beach_coastal", "market_feira", 
                      "rooftop_terrace", "tropical_garden", "nature_open_air"),
    "pose_energy": ("candid", "directed"),
    "casting_profile": ("natural_commercial", "editorial_presence"),
    "framing_profile": ("environmental_wide", "three_quarter"),
    "camera_type": ("phone_social", "natural_digital"),
    "capture_geometry": ("environmental_wide_observer", "three_quarter_slight_angle"),
    "lighting_profile": ("ambient_lifestyle", "directional_daylight"),
}
```

**Diagnóstico:** 🟡 **Parcialmente alinhado.**

| Pool | Status | Observação |
|---|---|---|
| `scenario_pool` | ✅ | Bom mix — cidade, praia, feira, rooftop |
| `pose_energy` | ✅ | `candid` + `directed` é a dualidade certa |
| `casting_profile` | 🟡 | `editorial_presence` pode puxar demais para editorial |
| `framing_profile` | 🟡 | Falta `full_body` — lifestyle precisa mostrar o look completo |
| `camera_type` | ✅ | `phone_social` + `natural_digital` — perfeito |
| `capture_geometry` | 🟡 | `environmental_wide_observer` fica muito "assistindo de longe" |
| `lighting_profile` | 🟡 | Falta referência a "golden hour" — a hora dourada é a assinatura do lifestyle |

---

### 8. `scene_engine.py` — Pools de Cenário Usados no Lifestyle

Os pools `textured_city`, `beach_coastal`, `market_feira`, `rooftop_terrace`, `tropical_garden`, `nature_open_air` alimentam o lifestyle.

**Análise de afinidade com lifestyle:**

| Pool | Afinidade | Problema potencial |
|---|---|---|
| `textured_city` | ✅ Alta | Perfeito — rua com textura, muros, urban realismo |
| `beach_coastal` | ✅ Alta | Perfeito — praia/boardwalk brasileiro |
| `market_feira` | 🟡 Média | Pode funcionar, mas feira é mais "natural" que "lifestyle" |
| `rooftop_terrace` | 🟡 Média | Bom, mas "hotel terrace" (L367) é editorial demais |
| `tropical_garden` | 🟡 Média | "pousada garden" (L204) é editorial; "quintal" é natural, não lifestyle |
| `nature_open_air` | 🟡 Baixa | Genérico demais para lifestyle — falta narrativa de *onde* ela está |

**Cenários que FALTAM no lifestyle mas são essenciais:**
- 🔴 **Área de restaurante/bar ao ar livre** — a garota no rolê
- 🔴 **Interior de carro (Uber/corrida)** — ultra-lifestyle brasileiro
- 🔴 **Saída de loja/shopping** — sacola na mão, look completo
- 🔴 **Calçadão/orla** — caminhando no calçadão, vento no cabelo
- 🔴 **Porta de apartamento/elevador** — "saindo pra rua"

---

### 9. `curation_policy.py` — Guardrails do Lifestyle

O lifestyle cai no branch `lifestyle_permissive` (L454-483):
- `movement_budget`: "high" (se não spatially_sensitive)
- `frontality_bias`: "free"
- `occlusion_tolerance`: "medium"
- `gesture_range`: "open"
- `camera_language`: "natural_commercial"

**Diagnóstico:** ✅ **Bom.** `movement_budget: high`, `frontality_bias: free`, `gesture_range: open` — tudo alinhado com lifestyle.

> [!NOTE]
> Estes são engine states, já suprimidos pela guarda `_soul_driven`. Mas os valores estão coerentes se quisermos alinhá-los para consistência futura.

---

### 10. `fidelity.py` + `prompt_result.py` — Stage 1 e Footwear

Após as correções do outro agente, o `fidelity.py` já vai receber `art_direction_soul`. O fallback de footwear no `prompt_result.py` para lifestyle (L321-322) é genérico: "discreet commercially coherent footwear".

**Lacuna:** Para lifestyle, o calçado deveria ser **parte do look**, não "discreet". Sugestão: "contemporary footwear that completes the look as part of the lifestyle story — sneakers, mules, or strappy sandals."

---

## Resumo de Gaps (Lifestyle)

| Prioridade | Camada | Gap |
|---|---|---|
| 🔴 P0 | `model_soul.py` | Sem overlay lifestyle — falta diretiva de "no-makeup makeup", personalidade visual, energia Instagram |
| 🔴 P0 | `scene_soul.py` | Sem overlay lifestyle — falta reforçar cenário como narrativa de VIDA (onde ela está, por quê) |
| 🟡 P1 | `mode_identity_soul.py` | Falta regra anti-editorial e conceito de aspiração alcançável |
| 🟡 P1 | `pose_soul.py` | Falta vocabulário de ações concretas mid-moment |
| 🟡 P1 | `capture_soul.py` | Falta reforço de proximidade social e golden hour como mood |
| 🟡 P1 | `creative_brief_builder.py` | Pools de cenário incompletos — faltam cenários de "rolê urbano" |
| 🟢 P2 | `styling_soul.py` | Falta reforço de acessórios como contadores de história |
| 🟢 P2 | `prompt_result.py` | Footwear fallback genérico — precisa ser "statement contextual" |
| 🟢 P2 | `scene_engine.py` | Faltam families: bar_ao_ar_livre, interior_carro, saida_loja, calcadao_orla |

---

## Visão Final — O Que o Lifestyle DEVE Produzir

> Uma mulher brasileira bonita, arrumada-casual, num momento de vida real — saindo do Uber, chegando num brunch, andando na Oscar Freire com sacola de compras, verificando o celular na varanda do bar. O fotógrafo é alguém que ela conhece (namorado, amiga, ela mesma com timer). A foto tem warm tones, leve bokeh, golden hour. Ela sabe que a foto está sendo tirada, talvez dá um meio-sorriso, mas está VIVENDO, não posando. O look é completo — tênis branco, mini bolsa, óculos de sol na cabeça. A roupa que estamos vendendo é a peça hero, mas ela está vestida como uma pessoa de verdade que montou esse look de propósito.

**A diferença crucial:**
- **Natural** = ela NÃO sabe que estão fotografando (paparazzi)
- **Lifestyle** = ela SABE, mas está vivendo (influencer BTS)
- **Editorial** = ela está POSANDO intencionalmente (fashion shoot)
