# Auditoria: `curation_policy.py` — Policy vs Creative Direction

> Classificação de cada componente do arquivo para informar a próxima fase da consolidação Soul-First.

---

## Classificação por Função

| Função | Tipo | Justificativa |
|--------|------|---------------|
| `dedupe_preserve_order()` | 🔧 Utility | Helper puro, sem lógica de negócio |
| `apply_selection_policy()` | 🛡️ Policy | Filtra IDs baseado em preferred/avoid — **guardrail legítimo** |
| `_mode_guardrail_profile()` | 🛡️ Policy | Resolve guardrail_profile do mode — **guardrail legítimo** |
| `_movement_budget_from_guardrail()` | 🛡️ Policy | Traduz guardrail_profile → budget — **guardrail legítimo** |
| `_frontality_bias_from_guardrail()` | 🛡️ Policy | Traduz guardrail_profile → bias — **guardrail legítimo** |
| `_occlusion_tolerance_from_guardrail()` | 🛡️ Policy | Traduz guardrail_profile → tolerance — **guardrail legítimo** |
| `_ugc_intent()` | ⚠️ Hybrid | Detecta intenção UGC no texto — **policy de roteamento**, mas influencia casting e cena |
| `build_affinity_prompt()` | 🔧 Utility | Extrai prompt limpo — trivial |
| `derive_reference_budget()` | 🛡️ Policy | Define budget de referências por stage — **guardrail de custo/qualidade** |
| `derive_reference_guard_bundle()` | 🛡️ Policy | Define regras de identity guard — **guardrail anti-cópia** |
| `derive_reference_guard_config()` | 🛡️ Policy | Wrapper de `derive_reference_guard_bundle` |
| `stage1_candidate_count()` | 🛡️ Policy | Quantas candidatas gerar no Stage 1 — **guardrail de custo** |
| `derive_art_direction_selection_policy()` | ⚠️ **Hybrid** | **Maior função do arquivo** — mistura guardrails e seleção criativa |

---

## Análise Detalhada: `derive_art_direction_selection_policy()`

Esta função (L332-548) é a mais longa e a mais problemática. Ela decide:

### O que é **Policy** (legítimo):
- `identity_guard` — regras anti-cópia de identidade
- `movement_budget` — limite de movimento por guardrail_profile
- `frontality_bias` — orientação corporal por guardrail
- `occlusion_tolerance` — tolerância a oclusão da peça
- `scene_constraints.context_rigidity` — rigidez do cenário
- `pose_constraints.silhouette_priority` — prioridade de silhueta

### O que é **Creative Direction** (deveria estar no agent/briefing):
- `preferred_scene_ids` — **SELECIONA cenários** (ex: showroom vs outdoor vs boutique)
- `preferred_camera_ids` — **SELECIONA câmeras** (ex: canon vs phone)
- `preferred_lighting_ids` — **SELECIONA iluminação** (ex: showroom vs golden hour)
- `preferred_casting_family_ids` — **SELECIONA casting** (ex: premium vs natural vs UGC)
- `preferred_pose_ids` — **SELECIONA poses** (ex: stable vs movement)
- `scene_constraints.backdrop_mode` — **ESCOLHE tipo de backdrop**
- `capture_constraints.camera_language` — **DEFINE linguagem de câmera**
- `capture_constraints.depth_context` — **DEFINE profundidade de cena**

### O que é **Constraint que parece Creative** (zona cinzenta):
- `avoid_scene_ids` — bloqueia cenários incompatíveis → guardrail negativo ✅
- `avoid_camera_ids` — bloqueia câmeras inadequadas → guardrail negativo ✅
- `avoid_lighting_ids` — bloqueia iluminação incoerente → guardrail negativo ✅
- `avoid_casting_family_ids` — bloqueia casting incompatível → guardrail negativo ✅
- `avoid_pose_ids` — bloqueia poses perigosas → guardrail negativo ✅

---

## Classificação das Constantes

| Constante | Tipo | Nota |
|-----------|------|------|
| `_SCENE_AFFINITY` | 🗺️ Routing | Mapeia preferência → ID de cena |
| `_STABLE_POSE_IDS` | 🎨 Creative pool | Pool curado de poses estáveis |
| `_BALANCED_POSE_IDS` | 🎨 Creative pool | Pool curado de poses balanceadas |
| `_MOVEMENT_POSE_IDS` | 🎨 Creative pool | Pool curado de poses com movimento |
| `_CATALOG_SCENES` | 🎨 Creative pool | Pool curado de cenários catalog |
| `_INDOOR_COMMERCIAL_SCENES` | 🎨 Creative pool | Pool curado de cenários indoor |
| `_OUTDOOR_COMMERCIAL_SCENES` | 🎨 Creative pool | Pool curado de cenários outdoor |
| `_UGC_INDOOR/OUTDOOR_SCENES` | 🎨 Creative pool | Pool curado de cenários UGC |
| `_PREMIUM/NATURAL/UGC_CASTING` | 🎨 Creative pool | Pools curados de casting |
| `_COMMERCIAL/NATURAL/PHONE_CAMERAS` | 🎨 Creative pool | Pools curados de câmera |
| `_CATALOG/NATURAL/EDITORIAL/UGC_LIGHTING` | 🎨 Creative pool | Pools curados de iluminação |

---

## Quem consome `curation_policy`?

```
generation_flow.py (L511+)
  └─ derive_art_direction_selection_policy()
      ├─ art_direction_config → passado a generation_flow internamente
      ├─ scene_engine.py → usa preferred_scene_ids para filtrar cenários
      ├─ pose_engine.py → usa preferred_pose_ids para filtrar poses
      ├─ capture_engine.py → usa preferred_camera_ids para filtrar câmeras
      └─ fidelity.py → usa identity_guard para shell de proteção
```

---

## Recomendação para o Plano

> [!IMPORTANT]
> **Não mexer neste arquivo no piloto do catalog_clean.** Mas a separação futura é clara:

1. **Manter como Policy:** `derive_reference_budget`, `derive_reference_guard_*`, `stage1_candidate_count`, e os campos `avoid_*` e `*_constraints` de `derive_art_direction_selection_policy`.

2. **Migrar para briefings:** Os campos `preferred_*_ids` e os creative pools (`_CATALOG_SCENES`, `_PREMIUM_CASTING`, etc.) deveriam ser absorvidos pelas engine de briefing de cada mode — o mode define quais cenários, poses, câmeras e casting são compatíveis com sua identidade.

3. **O campo `ugc_intent`** é um detector de intenção — deveria possivelmente migrar para um módulo de classificação de intenção separado.

4. **Os `*_constraints`** (scene_constraints, pose_constraints, capture_constraints) são guardrails legítimos e devem permanecer — mas os nomes `camera_language`, `depth_context`, e `backdrop_mode` parecem creative choices e talvez devessem ser renomeados para `max_camera_formality`, `max_backdrop_complexity`, etc.
