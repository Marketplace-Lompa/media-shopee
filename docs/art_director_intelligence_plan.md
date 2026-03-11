# Art Director Intelligence — Plano de Implementação

**Data:** 2026-03-11
**Revisado:** 2026-03-11 (v2 — incorpora 5 refinamentos de engenharia da senior review)
**Escopo:** Transformar o pipeline MODE 2 (referência sem prompt) de "compilador de templates aleatório" para "diretor de arte inteligente" que analisa a peça e faz casting consciente de modelo brasileira + cenário brasileiro.

---

## 1. Princípio Fundamental

> Toda geração DEVE produzir uma **modelo humana brasileira real** em um **cenário brasileiro autêntico** que **complementem esteticamente a peça-alvo**.
>
> O agente funciona como **diretor de arte**: analisa a peça (cores, textura, mood, estação, formalidade), escolhe o casting ideal (modelo + cenário + pose), e entrega output "nível ouro" mesmo com **zero input do usuário**. Depois, o usuário refina via chat.

---

## 2. Diagnóstico Atual (Gaps)

### Fluxo MODE 2 (referência sem texto):

```
ROUTER
  ├── select_diversity_target(seed="")        ← 100% ALEATÓRIO (sem info da peça)
  ├── _infer_unified_vision_triage(images)    ← extrai geometria + hint + 1 frase
  └── run_agent(diversity=RANDOM, triage=GARMENT_INFO)
        ├── Gemini Flash: escreve base_prompt com narrativa da peça
        ├── Compilador: SUBSTITUI base por "RAW photo, {profile}"  ← PERDE narrativa
        └── Prompt final: profile aleatório + fatos geométricos secos
```

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G1 | **Diversidade cega** | 🔴 Alta | Profile/cenário/pose selecionados sem conhecer a peça |
| G2 | **Compilador apaga narrativa** | 🔴 Alta | `force_cover_defaults` substitui base inteiro, perdendo cores/textura/mood |
| G3 | **Gemini sem agência** | 🟡 Média | Recebe DIVERSITY_TARGET pré-decidido, não pode recomendar casting ideal |
| G4 | **Sem role assignment pro Nano** | 🟡 Média | Referências enviadas sem instrução "garment ONLY" + sem `media_resolution` |
| G5 | **image_analysis rasa** | 🟡 Média | Triagem pede "one sentence" — insuficiente para casting inteligente |

### O que funciona bem (não mexer):

- Structural contract (conf ~0.95): geometria fielmente extraída
- Anti-repeat scheduling: window de 8 jobs + max_share control
- Garment-Only Reference Mode: 8 regras separando peça de pessoa
- Catalog stance rotation: 5 poses com anti-repeat
- Scene alternation: interno/externo alterna entre gerações

---

## 3. Solução: 5 Mudanças

### M1 — Enriquecer triagem com `garment_aesthetic` (Enum-safe)

**Arquivo:** `agent_runtime/triage.py` + `agent_runtime/constants.py`

Adicionar ao `UNIFIED_VISION_SCHEMA` o campo `garment_aesthetic` que o Gemini extrai junto com structural_contract (mesma chamada, custo zero).

**REFINAMENTO (senior review):** O campo `vibe` usa **Enum fechado** em vez de free-text.
Motivo: com string livre o Gemini pode responder "relaxed weekend" e o match no Python
esperar "boho_artisanal". Enum garante previsibilidade no pipeline de afinidade (M2).

```python
"garment_aesthetic": {
    "type": "object",
    "required": ["color_temperature", "formality", "season", "vibe"],
    "properties": {
        "color_temperature": {
            "type": "string",
            "enum": ["warm", "cool", "neutral"],
            "description": "Dominant color temperature of the garment"
        },
        "formality": {
            "type": "string",
            "enum": ["casual", "smart_casual", "formal"],
            "description": "Formality level of the garment"
        },
        "season": {
            "type": "string",
            "enum": ["summer", "mid_season", "winter"],
            "description": "Most natural season/occasion for this garment"
        },
        "vibe": {
            "type": "string",
            "enum": [
                "boho_artisanal",
                "urban_chic",
                "romantic",
                "bold_edgy",
                "minimalist",
                "beachwear_resort",
                "sport_casual"
            ],
            "description": "Primary aesthetic mood of the garment for casting/scenario matching"
        }
    }
}
```

Atualizar instrução da triagem unificada para pedir esses campos com os Enums.

**Custo:** 0 chamadas extras (piggyback na chamada existente).

---

### M2 — Tornar `select_diversity_target()` garment-aware + lighting intelligence

**Arquivo:** `pipeline_effectiveness.py`

Receber `garment_aesthetic` e `structural_contract` como input e usar para filtrar/pesar
os pools de cenário, perfil e — novo — iluminação.

```python
def select_diversity_target(
    seed_hint: str = "",
    guided_brief: Optional[dict] = None,
    garment_aesthetic: Optional[dict] = None,       # NOVO (M1)
    structural_contract: Optional[dict] = None,     # NOVO (para lighting)
) -> dict:
```

#### Regras de afinidade cenário:

| garment_aesthetic | Cenários preferidos | Cenários evitados |
|---|---|---|
| `season=winter` | indoor (café, showroom, loft) | outdoor bright/botanical |
| `season=summer` | outdoor (garden, courtyard, downtown) | indoor cozy/dark |
| `formality=formal` | showroom, downtown, loft | café terrace, botanical |
| `formality=casual` | café, garden, botanical, courtyard | showroom formal |
| `color_temperature=warm` | cenários com fundo neutro/cool (contraste) | — |
| `color_temperature=cool` | cenários com tons quentes, madeira, golden hour | — |

#### Regras de afinidade perfil:

| garment_aesthetic.vibe | Perfis com mais afinidade |
|---|---|
| `boho_artisanal` | Baiana, Nordestina, Mineira |
| `urban_chic`, `minimalist` | Paulistana, Carioca, Brasília native |
| `romantic` | Sulista, Mineira |
| `bold_edgy` | Carioca, Nordestina, Paulistana |
| `beachwear_resort` | Carioca, Nordestina, Baiana |
| `sport_casual` | qualquer (sem preferência regional) |

#### Regras de afinidade iluminação (NOVO — senior review):

**REFINAMENTO:** Vincular cenário à textura/peso da roupa via `structural_contract`.
Garments com muita textura ficam melhores com luz direcional que revela relevo;
peças lisas/alfaiataria fluem com luz suave e difusa.

| structural_contract | Lighting preferido | Cenários favorecidos |
|---|---|---|
| subtype in {ruana_wrap, poncho, cape} + volume=draped | dappled light, side light, golden hour rim | courtyard, botanical garden, café terrace |
| subtype in {pullover} + material texturizado (crochê, tricô pesado) | directional sunlight, window light | open-air courtyard, loft com janela grande |
| subtype in {blazer, jacket, vest} + volume=structured/fitted | soft studio light, overcast, diffused | showroom, studio, downtown overcast |
| subtype in {dress, blouse} + volume=regular/fitted | even soft light, gentle bokeh | minimalist apartment, café, downtown |

Implementação: adicionar campo `lighting_hint` ao retorno de `select_diversity_target()` que o compilador pode injetar como P4 clause.

A afinidade funciona como **peso** (não hard filter) — o anti-repeat scheduling continua
funcionando normalmente, apenas reordena os candidatos.

**Custo:** 0 latência extra (lógica local de filtragem).

---

### M3 — Compilador usa campo estruturado (sem regex/filtros de string)

**Arquivo:** `agent_runtime/compiler.py` + `agent_runtime/constants.py` + `agent.py`

**REFINAMENTO CRÍTICO (senior review):** O plano original propunha `_extract_garment_narrative(base)` —
uma função que filtraria o texto livre do Gemini via regex para separar peça de modelo/cenário.
**Isso é frágil** — parsing de texto livre via regex quebra com variações de formato.

**Solução robusta:** Fazer o Gemini separar a descrição da peça em um campo JSON dedicado
no `AGENT_RESPONSE_SCHEMA`:

```python
# Novo campo no AGENT_RESPONSE_SCHEMA:
"garment_narrative": {
    "type": "string",
    "description": (
        "GARMENT-ONLY description: color, pattern, texture, construction, drape. "
        "Do NOT include any model/person description or scenario/background. "
        "Max 30 words. Required when reference images are present."
    )
}
```

O compilador então monta o base de forma limpa a partir de dados estruturados:

```python
# ANTES (regex frágil):
if force_cover_defaults and profile_hint:
    garment_narrative = _extract_garment_narrative(base)  # FRÁGIL
    base = f"RAW photo, {profile_hint}. Wearing {garment_narrative}"

# DEPOIS (campo estruturado — 100% seguro):
if force_cover_defaults and profile_hint:
    garment_narrative = result.get("garment_narrative", "").strip()
    if garment_narrative:
        base = f"RAW photo, {profile_hint}. Wearing {garment_narrative}"
    else:
        base = f"RAW photo, {profile_hint}"
    profile_seeded_in_base = True
```

**Vantagens:**
- Zero risco de vazamento da modelo da referência no prompt (Gemini separa na geração)
- Zero regex/parsing frágil
- O Gemini é muito mais competente em separar conteúdo do que qualquer regex
- Se o campo vier vazio, fallback seguro para comportamento atual

**Mudanças em `agent.py`:**
- Extrair `garment_narrative` do result do Gemini
- Passar como parâmetro para `_compile_prompt_v2()` (novo kwarg `garment_narrative`)

Aumentar `_base_cap` de 28 para ~50 para acomodar profile (~14w) + garment_narrative (~30w).

**Impacto:** O prompt final terá "RAW photo, [modelo brasileira]. Wearing [descrição rica
com cores e textura]" em vez de apenas fatos geométricos secos.

---

### M4 — Role assignment explícito para Nano Banana (com guard de Guided Mode)

**Arquivo:** `generator.py`

Adicionar instrução de papel no prompt enviado ao Nano:

```python
if uploaded_images:
    role_prefix = (
        "The reference image(s) show the TARGET GARMENT only — "
        "copy EXACTLY the clothing design, color, pattern, and texture. "
        "Generate a NEW Brazilian model (do NOT copy the person from the reference). "
    )
    prompt = role_prefix + prompt
```

**REFINAMENTO (senior review):** Adicionar guard para Guided Mode.

Se no futuro o guided_brief incluir uma opção de "manter modelo original" ou se o
usuário mandar texto explícito ("mantenha a modelo usando um boné"), o role prefix
"Generate a NEW Brazilian model" conflitaria. Guard defensivo:

```python
# Guard: role prefix SÓ aplica quando não há instrução explícita de manter modelo
_force_new_model = not has_prompt  # sem texto = sem intenção de preservar modelo
if uploaded_images and _force_new_model:
    role_prefix = (
        "The reference image(s) show the TARGET GARMENT only — "
        "copy EXACTLY the clothing design, color, pattern, and texture. "
        "Generate a NEW Brazilian model (do NOT copy the person from the reference). "
    )
    prompt = role_prefix + prompt
```

**Nota:** Atualmente o `guided_brief` não tem flag "keep original model" (campos são:
age_range, set_mode, scene type, pose style, capture distance, fidelity_mode).
O guard protege contra futura extensão sem que o M4 precise ser revisitado.

Quando o usuário manda texto (`has_prompt=True`), o controle da narrativa é dele —
o role prefix não se aplica.

Ativar `media_resolution="high"` para referências de garment (mais tokens = mais detalhe):

```python
config=types.GenerateContentConfig(
    response_modalities=["TEXT", "IMAGE"],
    temperature=1.0,
    media_resolution="high" if uploaded_images else None,
    image_config=types.ImageConfig(
        aspect_ratio=aspect_ratio,
        image_size=resolution,
    ),
    ...
)
```

**Custo:** marginal (mais tokens de input, mas melhora fidelidade de garment).

---

### M5 — Enriquecer `image_analysis` na triagem

**Arquivo:** `agent_runtime/triage.py`

Mudar a instrução de "one sentence high-level" para análise mais útil:

```
ANTES:
  "2. image_analysis: one sentence high-level description of what is visible."

DEPOIS:
  "2. image_analysis: 2-3 sentences describing the garment visible in the reference.
      Include: dominant colors and color temperature (warm/cool/neutral),
      fabric texture appearance, overall aesthetic mood, and suggested styling context.
      Focus on visual qualities that inform casting and scenario decisions.
      Do NOT describe the person wearing the garment — focus 100% on the clothing."
```

**Impacto:** O `image_analysis` passa de:
> "A woman wearing an open-front crochet wrap"

Para:
> "Open-front crochet wrap in warm earth tones (caramel, terracotta, cream). Handmade artisanal texture with visible open-stitch pattern. Boho relaxed aesthetic, ideal for mid-season outdoor styling."

---

## 4. Ajuste Crítico de Pipeline: Ordem de Execução no Router

**REFINAMENTO CRÍTICO (senior review):** Os routers DEVEM inverter a ordem de execução.

### Estado atual (INCORRETO para Art Director):

```python
# routers/generate.py (linha 72) e routers/stream.py (linha 89):
diversity_target = select_diversity_target(seed_hint=prompt, guided_brief=normalized_guided)
# ... mais tarde ...
unified_triage_result = _infer_unified_vision_triage(analysis_images, prompt)  # linha 103-110
```

`select_diversity_target()` roda **ANTES** da triagem → não tem acesso ao `garment_aesthetic`.

### Estado necessário (CORRETO):

```python
# 1. PRIMEIRO: triagem visual (extrai garment_aesthetic + structural_contract)
unified_triage_result = _infer_unified_vision_triage(analysis_images, prompt)
garment_aesthetic = None
structural_contract_for_diversity = None
if unified_triage_result:
    garment_aesthetic = unified_triage_result.get("garment_aesthetic")
    structural_contract_for_diversity = unified_triage_result.get("structural_contract")

# 2. DEPOIS: diversidade garment-aware (usa estética da peça para casting)
diversity_target = select_diversity_target(
    seed_hint=prompt or "",
    guided_brief=normalized_guided,
    garment_aesthetic=garment_aesthetic,
    structural_contract=structural_contract_for_diversity,
)
```

**Sem essa inversão, a M2 é impossível** — o `select_diversity_target()` não teria acesso
ao `garment_aesthetic` que vem da triagem.

**Ambos os routers** (`generate.py` e `stream.py`) precisam dessa inversão.

**Impacto na latência:** Nenhum — a triagem já roda antes do `run_agent()` em ambos os
routers. A única mudança é mover o `select_diversity_target()` para DEPOIS da triagem
(que já estava logo acima).

---

## 5. Regra de Ouro: Modelo Brasileira + Cenário Brasileiro

Independente de qualquer configuração, TODA geração DEVE:

1. **Modelo humana brasileira real** — nunca manequim, nunca flatlay, nunca modelo genérica internacional. O Name Blending usa exclusivamente nomes brasileiros + vibes regionais brasileiras + agências/marcas brasileiras.

2. **Cenário brasileiro autêntico** — todos os cenários do pool refletem ambientes comuns no Brasil (café premium, shopping district, botanical garden, downtown moderno, apartamento minimalista, loft, showroom). Nenhum cenário deve sugerir contexto estrangeiro (neve, autumn leaves, European architecture).

3. **Complementaridade estética** — o cenário e a modelo devem COMPLEMENTAR a peça, não apenas coexistir. Cores complementares, mood coerente, estação alinhada, iluminação que valorize a textura.

4. **Diversidade real** — o Name Blending garante representação de todas as regiões brasileiras (Nordeste, Sudeste, Sul, Centro-Oeste) com fenótipos autênticos ancorados por nomes reais. A rotação anti-repeat impede monotonia.

5. **Skin realism obrigatório** — toda geração inclui âncoras de realismo de pele ("visible natural pores, subtle peach fuzz") para evitar AI Face (pele plástica, simetria artificial).

---

## 6. Exemplos de Resultado Esperado

### Antes (aleatório):

| Peça | Modelo | Cenário | Resultado |
|------|--------|---------|-----------|
| Ruana crochê tons terrosos | Paulistana chic (aleatório) | Minimalist studio (aleatório) | Desconexo — peça boho em cenário clean |
| Blazer formal preto | Baiana radiant (aleatório) | Botanical garden (aleatório) | Desconexo — peça formal em cenário natureza |
| Biquíni colorido verão | Sulista elegant (aleatório) | Indoor loft (aleatório) | Desconexo — peça praia em cenário fechado |

### Depois (Art Director Intelligence):

| Peça | Estética Detectada | Modelo | Cenário + Lighting | Resultado |
|------|-------------------|--------|---------------------|-----------|
| Ruana crochê tons terrosos | warm, casual, mid_season, boho_artisanal | Nordestina litorânea | Courtyard com dappled light lateral | Harmônico — tons quentes, textura revelada, mood relaxed |
| Blazer formal preto | cool, formal, mid_season, urban_chic | Paulistana editorial | Downtown architecture, soft overcast light | Harmônico — elegância urbana, luz suave para tecido liso |
| Biquíni colorido verão | warm, casual, summer, beachwear_resort | Carioca fresh-faced | Outdoor bright natural light | Harmônico — verão brasileiro, cores vibrantes |
| Vestido renda delicado | neutral, smart_casual, mid_season, romantic | Sulista elegante | Café terrace, gentle warm backlight | Harmônico — romantismo, luz suave revelando textura |

---

## 7. Fluxo Final (pós-implementação)

```
ROUTER
  │
  ├── 1. _infer_unified_vision_triage(images)
  │     └── Retorna: garment_hint, image_analysis (2-3 frases ricas),
  │                  structural_contract, set_detection,
  │                  garment_aesthetic {color_temperature, formality, season, vibe},
  │                  garment_narrative (campo JSON dedicado, 30w max)
  │
  ├── 2. select_diversity_target(
  │       seed_hint, guided_brief,
  │       garment_aesthetic,          ← NOVO (afinidade estética)
  │       structural_contract         ← NOVO (lighting intelligence)
  │     )
  │     └── Retorna: profile, scenario, pose, lighting_hint
  │                  (casting inteligente, não aleatório)
  │
  └── 3. run_agent(diversity_target=INFORMED, unified_triage=GARMENT_INFO)
        │
        ├── Gemini Flash: escreve base_prompt + garment_narrative (campo dedicado)
        │
        ├── _compile_prompt_v2():
        │     base = "RAW photo, {profile}. Wearing {garment_narrative}"
        │     + P1: structural clauses
        │     + P2-P4: textura, composição, lighting_hint, cenário
        │
        └── generator.py:
              role_prefix = "Reference = GARMENT ONLY. Generate NEW Brazilian model."
              media_resolution = "high"
              → Nano Banana
```

---

## 8. Arquivos Modificados

| Arquivo | Mudança | Linhas estimadas |
|---------|---------|-----------------|
| `agent_runtime/constants.py` | Schema `garment_aesthetic` (Enum-safe) + `garment_narrative` no AGENT_RESPONSE_SCHEMA | +25 |
| `agent_runtime/triage.py` | Instrução enriquecida + parsing `garment_aesthetic` + `garment_narrative` | +25 |
| `pipeline_effectiveness.py` | `select_diversity_target()` garment-aware + lighting afinidade | +60 |
| `agent_runtime/compiler.py` | Usar `garment_narrative` estruturado (sem regex) + `lighting_hint` | +25 |
| `agent.py` | Extrair `garment_narrative` do response e passar ao compilador | +10 |
| `generator.py` | Role prefix (com guard) + `media_resolution` | +12 |
| `routers/generate.py` | Inverter ordem: triagem antes de diversity + passar aesthetic | +10 |
| `routers/stream.py` | Mesmo que generate.py | +10 |
| **Total** | | **~177 linhas** |

---

## 9. O que NÃO muda

- `run_agent()` signature — preservada (garment_narrative vem do response JSON, não de parâmetro)
- Anti-repeat scheduling — preservado (window, max_share, cursor)
- Structural contract — preservado (geometria)
- Guided mode — preservado (constraints do usuário)
- SYSTEM_INSTRUCTION — preservada (regras comportamentais)
- Return contract — preservado (todos os campos de saída existentes)
- `_sample_diversity_target()` em diversity.py — preservado como fallback interno do agent

---

## 10. Custo de Implementação

- **0 chamadas API extras** (garment_aesthetic vem da triagem unificada existente)
- **0 latência extra** (afinidade + lighting são lógica local de filtragem)
- **~177 linhas de código** em 8 arquivos
- **Risco:** Baixo — todas as mudanças são aditivas, sem quebra de contrato existente

---

## 11. Validação

1. Rodar job MODE 2 com ruana crochê → verificar se cenário/modelo/lighting harmonizam
2. Rodar job MODE 2 com blazer formal → verificar se cenário muda para urbano, luz suave
3. Rodar job MODE 2 com biquíni → verificar se cenário outdoor/bright é selecionado
4. Verificar anti-repeat: 3 gerações consecutivas devem ter perfis e cenários diferentes
5. Verificar `garment_aesthetic` no log: color_temperature, formality, season, vibe (Enum)
6. Verificar `garment_narrative` no log: descrição rica da peça sem menção a pessoa
7. Verificar prompt final contém cores/textura (não apenas geometria seca)
8. Confirmar que modelo é SEMPRE brasileira e cenário é SEMPRE brasileiro
9. Verificar lighting_hint presente em prompts de peças texturizadas (crochê, tricô)
10. Testar com `has_prompt=True`: role prefix do M4 NÃO deve ser injetado

---

## 12. Refinamentos Incorporados (Senior Review Log)

| # | Refinamento | Origem | Impacto |
|---|-------------|--------|---------|
| R1 | `vibe` como Enum fechado (7 valores) em vez de free-text | Senior Review | Garante match determinístico em pipeline_effectiveness.py |
| R2 | `garment_narrative` como campo JSON dedicado em vez de regex/filtro de string | Senior Review | Elimina risco de vazamento de modelo da referência, zero parsing frágil |
| R3 | Inversão de ordem no router: triagem ANTES de `select_diversity_target()` | Senior Review | Pré-requisito crítico — sem isso M2 é impossível |
| R4 | Guard no M4 role prefix: só aplica quando `not has_prompt` | Senior Review | Previne conflito quando usuário manda texto explícito ou futuro guided "keep model" |
| R5 | Lighting intelligence baseada em textura/peso do structural_contract | Senior Review | Eleva sistema de "diretor de arte" para "diretor de fotografia" |
