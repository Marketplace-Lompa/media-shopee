# OBSOLETO — Look Contract

Este documento descreve uma arquitetura removida do runtime em `2026-03-27`.
O `look_contract` deixou de existir porque a triagem voltou a ter escopo estrito
de leitura da peça hero, e o styling passou a ser responsabilidade do caminho
`soul-first`.

# Look Contract — Style Agent

> Garante coerência estilística nos looks gerados, inferindo peça inferior, cores e acessórios compatíveis com a peça-alvo.

---

## Problema

Sem orientação de estilo, o pipeline gerava combinações incoerentes: um poncho artesanal com saia plissada, ou uma blusa casual com calça social. O modelo de geração (Imagen/Nano Banana) escolhia a peça inferior livremente, sem considerar a estética da peça de referência.

## Solução

O **Look Contract** é um contrato de estilo inferido automaticamente pela triagem visual unificada (`_infer_unified_vision_triage`). Ele analisa a peça-alvo e retorna restrições de styling que são injetadas no contexto do agente como um bloco XML `<LOOK_CONTRACT>`.

---

## Arquitetura

```
Imagens de referência
        │
        ▼
┌─────────────────────────────┐
│  _infer_unified_vision_triage │  ← UMA única chamada Gemini
│  (triage.py)                  │
│                               │
│  Retorna 7 campos:            │
│  1. garment_hint              │
│  2. image_analysis            │
│  3. structural_contract       │
│  4. set_detection             │
│  5. garment_aesthetic         │
│  6. lighting_signature        │
│  7. look_contract  ← NOVO     │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  run_agent() (agent.py)      │
│                               │
│  Extrai _unified_look_contract│
│  Se confidence > 0.5:        │
│    Injeta <LOOK_CONTRACT>    │
│    entre STRUCTURAL_CONTRACT │
│    e grounding blocks        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Gemini Flash compila prompt │
│  respeitando as restrições   │
│  de bottom_style, cor, etc.  │
└─────────────────────────────┘
```

### Zero latência adicional

O look_contract é inferido **dentro** da chamada Gemini que já existe para `structural_contract`, `garment_hint`, etc. Não há chamada extra — o schema unificado (`UNIFIED_VISION_SCHEMA`) foi estendido com o campo 7.

---

## Schema

Definido em `constants.py` dentro de `UNIFIED_VISION_SCHEMA`:

```python
"look_contract": {
    "type": "OBJECT",
    "properties": {
        "bottom_style":      {"type": "STRING"},  # ex: "calça slim escura"
        "bottom_color":      {"type": "STRING"},  # ex: "preto", "off-white"
        "color_family":      {"type": "STRING"},  # ex: "earth tones"
        "season":            {"type": "STRING"},  # ex: "transicional"
        "occasion":          {"type": "STRING"},  # ex: "casual elegante"
        "forbidden_bottoms": {                     # ex: ["saia plissada", "shorts"]
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "accessories":       {"type": "STRING"},  # ex: "sandália minimalista"
        "style_keywords":    {                     # ex: ["artesanal", "boho"]
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "confidence":        {"type": "NUMBER"}   # 0.0 a 1.0
    }
}
```

---

## Arquivos Modificados

| Arquivo | O que mudou |
|---|---|
| `agent_runtime/constants.py` | `UNIFIED_VISION_SCHEMA` estendido com campo `look_contract` |
| `agent_runtime/triage.py` | Instrução do Gemini atualizada para inferir look_contract; normalização no retorno |
| `agent.py` | Extrai `_unified_look_contract` do triage; injeta bloco `<LOOK_CONTRACT>` no contexto |

---

## Injeção no Contexto (agent.py:295-315)

O bloco é injetado **entre** `<STRUCTURAL_CONTRACT>` e os blocos de grounding:

```xml
<LOOK_CONTRACT>
[Styling constraints — outfit must be coherent with the target garment]
- bottom_style: fitted dark trousers
- bottom_color: black / dark charcoal
- color_family: earth tones
- season: transitional
- occasion: casual elegant
- forbidden_bottoms: pleated skirt, sporty shorts, tulle skirt
- accessories: minimal leather sandals
- style_keywords: artisanal, bohemian, layered
Use bottom_style and bottom_color as the primary guide for the
model's lower garment. NEVER suggest a forbidden_bottom type.
</LOOK_CONTRACT>
```

**Condição de ativação:** `confidence > 0.5` (linha 297).

---

## Exemplo Real — Poncho/Ruana Artesanal

**Input:** 4 imagens de uma ruana listrada (rosa/verde oliva, crochê artesanal)

**Look Contract inferido:**
- `bottom_style`: fitted dark trousers
- `bottom_color`: black / dark charcoal
- `forbidden_bottoms`: pleated skirt, sporty shorts, tulle skirt
- `accessories`: minimal leather sandals
- `confidence`: 0.85

**Resultado gerado:**
- ✅ Ruana preservada (structural_contract)
- ✅ Calça slim preta (look_contract → bottom_style)
- ✅ Sandália caramelo (look_contract → accessories)
- ❌ Saia plissada bloqueada (forbidden_bottoms)

---

## Teste Integrado

```bash
cd /Users/lompa-marketplace/Documents/MEDIA-SHOPEE
python app/tests/test_look_contract.py
```

O teste:
1. Carrega 4 imagens reais de `tests/output/poncho-teste/`
2. Envia para `/generate/async` com campo multipart `images`
3. Aguarda job e salva resultado em `tests/output/look_contract_test/`
4. Compara visualmente com `resultado1.png` (baseline sem look_contract)

**Saída:** `app/tests/output/look_contract_test/resultado_com_look_contract.png`

---

## Evolução Futura

- [ ] Flag `LOOK_CONTRACT_ENABLED` em variável de ambiente para desativar em runtime
- [ ] Expor look_contract no response da API para debug no frontend
- [ ] Integrar com pipeline v2 (`pipeline_v2.py`)
- [ ] Testes automatizados com múltiplos tipos de peça (vestido, blazer, lingerie)
