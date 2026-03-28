# Walkthrough — Consolidação Lifestyle Soul-First

## Contexto
O modo `lifestyle` precisava de overlays condicionais em todos os 6 módulos de Soul para garantir que o Gemini gere prompts com a identidade correta: modelo **mid-activity**, cenário como **co-protagonista narrativo**, e estética **influencer/BTS** — distinto tanto do natural (paparazzi/candid) quanto do editorial (composição autoral).

## Alterações Realizadas

### P0 — Overlays Estruturais

#### `model_soul.py`
- **Novo overlay** `LIFESTYLE MODE HUMAN LOGIC`
- Maquiagem intencional mas não editorial ("preparou para o dia, não para a sessão")
- Cabelo com identidade pessoal, não de salão
- Personalidade visual individual, não placeholder de casting

#### `scene_soul.py`
- **Novo overlay** cenário co-protagonista
- O lugar deve explicar **por que** ela está ali
- Evita tanto a domesticidade silenciosa do natural quanto o curado premium do editorial
- Diferenciação clara: "socially alive and narratively coherent"

#### `pose_soul.py`
- **Overlay reforçado** com contrato de ação estrutural
- `"A static, idle pose breaks the lifestyle contract"`
- Diferenciação: pode ter camera-awareness (vs natural), mas corpo moldado pela atividade (vs editorial)

### P1 — Reforços Filosóficos

#### `mode_identity_soul.py`
- Contrato estrutural explícito: `"A static, idle, or purely presentational pose is a contract violation"`
- Nova regra de footwear narrativo: calçado conta o que ela estava fazendo
- Alma expandida de 7 para 9 diretrizes

#### `capture_soul.py`
- Câmera **participativa**: acompanha a ação, não observa passivamente
- Proximidade social: viewer sente-se parte da cena
- Diferenciação explícita: "(natural) not passive observation, (editorial) not authored spatial composition"

#### `creative_brief_builder.py`
- **Sem alterações** — pools são world families (textured_city, beach_coastal, etc.), não hardcodes literais

### P2 — Finishing Touches

#### `styling_soul.py`
- Acessórios como **ferramentas narrativas**: bolsa = chegou, óculos = sol, copo = mid-activity
- Objeto emerge da cena, não de um menu de styling

#### `prompt_result.py`
- Footwear fallback `lifestyle`: calçado da atividade, não comercialmente discreto
- `"tells you where she was going and what she was doing"`

## Verificação de Integridade

### Separação de Souls por Mode
Todos os 6 módulos usam `if/elif normalized == "..."` com overlay condicional. **Nenhum mode contamina outro** — a pattern é consistente.

### Guard `_soul_driven`
Confirmado em `prompt_context.py` L206: `_soul_driven = active_mode in {"natural", "lifestyle", "editorial_commercial"}`. Engine states **não vazam** para o prompt final.

### Teste E2E
Smoke test com imagem de referência (poncho crochet) + `mode="lifestyle"`:
- ✅ **Mid-activity**: "She is captured mid-activity, leaning slightly forward as she browses an outdoor artisanal market"
- ✅ **Cenário brasileiro co-protagonista**: mercado artesanal + flamboyant tree
- ✅ **Zero leaks editoriais**: nenhum "catalog-worthy", "standing pose", "direct eye contact"
- ✅ **Câmera participativa**: "observer viewpoint with spatial breathing room"
- ✅ **Contrato de retorno**: 1116 chars, thinking HIGH, realism 3

## Arquivos Modificados
| Arquivo | Tipo de Mudança |
|---|---|
| `model_soul.py` | +19 linhas (novo overlay) |
| `scene_soul.py` | +10 linhas (novo overlay) |
| `pose_soul.py` | +6 linhas (overlay expandido) |
| `mode_identity_soul.py` | +2 linhas (contrato + footwear) |
| `capture_soul.py` | +6 linhas (overlay expandido) |
| `styling_soul.py` | +6 linhas (overlay expandido) |
| `prompt_result.py` | +2 linhas (footwear elif) |
