# AKR — catalog_clean sem fidelidade de garment (compiler.py)

## Status
`[ATIVO]`

## Válido para
Python 3.11 / Imagen 3 (Nano Banana Pro) / `compiler.py` V2 / pipeline `reference_mode`

## Problema
O modo `catalog_clean` produzia garments com padrão têxtil incorreto — o Nano gerava
interpretações livres da roupa (ex: triângulos em mosaico) em vez de reproduzir o
padrão real das imagens de referência (ex: linhas diagonais cruzadas).

## Sintoma
- Output do `catalog_clean` com padrão geométrico diferente das referências
- Outros modes (`natural`, `lifestyle`) respeitavam a fidelidade de peça corretamente
- A diferença de fidelidade entre modes sugeria que o problema estava no branching por `mode_id`

## Root Cause
Três exceções explícitas em `compiler.py` (`_compile_prompt_v2`) desligavam **todo o P1
de fidelidade de garment** exclusivamente para `catalog_clean` + `reference_mode`:

```python
# Linha ~249 — excluía P1 estrutural (geometria observável)
and not (mode_id == "catalog_clean" and pipeline_mode == "reference_mode")

# Linha ~258 — excluía âncora de garment ("sole garment truth source")
if has_images and pipeline_mode == "reference_mode" and mode_id != "catalog_clean" ...

# Linha ~270 — excluía grounding de silhueta atípica
if grounding_mode == "full" and mode_id != "catalog_clean" ...
```

Com zero cláusulas P1 no prompt do Stage 1, o Nano ficava **completamente livre** para
inventar o padrão têxtil da peça. O Stage 2 (Edit/Replace) recebia um `image_analysis_hint`
ambíguo ("diamond and triangle grid") que reforçava a interpretação errada.

A premissa original das exceções era que o Stage 2 cuidaria da fidelidade via grounding
visual — mas sem P1 no Stage 1, o placeholder base já nascia com o padrão errado,
dificultando o replace no Stage 2.

## Solução Aplicada
Removidas as 3 condições `mode_id != "catalog_clean"` do `compiler.py`.

O `catalog_clean` agora usa **exatamente o mesmo fluxo de fidelidade de garment** que
todos os outros modes. A única diferença do mode permanece no backdrop neutro (controlado
pelas souls, `modes.py`, `mode_profile.py` — inalterados).

```diff
- and not (mode_id == "catalog_clean" and pipeline_mode == "reference_mode")

- if has_images and pipeline_mode == "reference_mode" and mode_id != "catalog_clean" and not suppress_reference_mechanics:
+ if has_images and pipeline_mode == "reference_mode" and not suppress_reference_mechanics:

- if grounding_mode == "full" and mode_id != "catalog_clean" and not suppress_reference_mechanics:
+ if grounding_mode == "full" and not suppress_reference_mechanics:
```

## Dead Ends (tentativas que NÃO funcionaram)
1. **Adicionar mais texto de padrão ao `reference_item_description`** — piorou: Nano
   generalizou a textura para toda a peça sem ancoragem de zona.
2. **Injetar `pattern_lock` textual** (`"geometric diamond relief"`) — causou alucinação
   de textura em mangas lisas (texto sem âncora de zona).
3. **Instrução `"zone-by-zone exactly as shown"`** — abstrata demais; Nano ignorou e
   aplicou textura uniformemente. (`build_pattern_lock` foi desativado por isso.)
4. **Diagnosticar no `fidelity.py`** — o problema não estava no Stage 2 (`compile_edit_prompt`
   / `prepare_garment_replacement_prompt`), mas no Stage 1 via `compiler.py`.

## Regra arquitetural derivada
> **`catalog_clean` = backdrop neutro apenas.**
> Qualquer exceção de fidelidade de garment por `mode_id == "catalog_clean"` é um erro.
> O mode não deve ter tratamento especial no pipeline de substituição de peça.

## Referências
- `app/backend/agent_runtime/compiler.py` — função `_compile_prompt_v2`, linhas P1 (~243-275)
- `app/backend/agent_runtime/fidelity.py` — `prepare_garment_replacement_prompt` (Stage 2, sem alteração)
- `app/backend/agent_runtime/fidelity.py` — `build_pattern_lock` (desativado — retorna `""`)
- Sessão: `bef69852-e3f5-4f0c-970f-97a33fa31661`

## Data
2026-04-01
