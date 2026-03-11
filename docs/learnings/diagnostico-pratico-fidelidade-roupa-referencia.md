# Diagnostico Pratico de Fidelidade

Data: 2026-03-11

## Objetivo

Validar, na pratica, como o pipeline atual se comporta em um caso real de fidelidade de roupa usando as referencias de:

- `docs/roupa-referencia-teste/`

Foco desta rodada:

- fidelidade estrutural da peca
- fidelidade de textura e padrao
- naturalidade da modelo
- qualidade comercial da imagem
- diferenca entre baseline controlado e pipeline completo

Nao foi objetivo desta rodada:

- testar Virtual Try-On
- testar Product Recontext
- otimizar o agente
- otimizar frontend

---

## Conjunto analisado

A pasta de referencia contem 20 arquivos, incluindo:

- 10 fotos de alta resolucao da modelo vestindo a peca
- 8 imagens menores/recortadas em formato WhatsApp
- 2 imagens de detalhe/plano da peca (`referencia.jpeg` e `referencia2.jpeg`)

Folhas-contato geradas nesta rodada:

- `app/outputs/reference_test_contact_sheet.jpg`
- `app/outputs/reference_test_candidate_subset.jpg`
- `app/outputs/reference_vs_outputs_comparison.jpg`
- `app/outputs/reference_vs_baselines_vs_pipeline.jpg`
- `app/outputs/reference_test_findings_sheet.jpg`

Achado inicial importante:

- o conjunto mistura referencias "modelo vestindo" e referencias "detalhe da peca"
- isso interfere diretamente no benchmark se o pipeline tratar tudo como um unico grupo homogeneo

---

## Como o pipeline atual curou essas referencias

Foi reproduzida a curadoria real do projeto via `build_reference_pack()`.

Resultado:

- `raw_count`: 20
- `unique_count`: 10
- `pre_outlier_unique_count`: 19
- `analysis_count`: 6
- `generation_count`: 10
- `duplicate_count`: 1
- `dropped_low_quality_count`: 0
- `dropped_outliers_count`: 9

Leitura:

- metade relevante do conjunto foi descartada como outlier
- as imagens de detalhe da peca nao entraram no subconjunto principal usado no benchmark padrao
- isso e um candidato forte a causa de perda de fidelidade estrutural

---

## Setup dos testes

## Teste A - Baseline controlado

Configuracao:

- sem `run_agent`
- sem grounding
- sem repair
- sem diversidade
- sem persistencia de estado como variavel experimental
- geracao direta via `generator.generate_images()`

Prompt base usado:

```text
Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment. Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible, clean premium indoor composition, soft natural daylight, no redesign, no extra outerwear, no distracting accessories.
```

Objetivo:

- medir o comportamento do motor de imagem quase "puro"
- isolar fidelidade da peca antes da interferencia do agente

## Teste B - Pipeline completo atual

Configuracao:

- `_run_generate_pipeline()`
- sem grounding
- com triagem visual
- com prompt compiler
- com diversidade/casting
- com camada de qualidade/reparo habilitada

Objetivo:

- comparar o comportamento real de producao contra o baseline controlado

---

## Matriz resumida

| ID | Setup | Refs | Output | Score | Leitura |
| --- | --- | --- | --- | --- | --- |
| A0 | `gemini-3.1-flash-image-preview`, `2K` | 6 fotos hi-res vestindo | falhou | n/a | instavel operacionalmente, `500 INTERNAL` |
| A1 | baseline, `MINIMAL`, `1K`, `4:5` | 3 fotos vestindo | `app/outputs/ref_test_minimal_1k/gen_ref_test_minimal_1k_1.png` | `0.91` | melhor baseline puro, forte em textura |
| A2 | baseline, `HIGH`, `1K`, `4:5` | 3 fotos vestindo | `app/outputs/ref_test_high_1k/gen_ref_test_high_1k_1.png` | `0.89` | mais polish, menos fidelidade material |
| B1 | pipeline completo, `1K`, `3:4` | 3 fotos vestindo | `app/outputs/3c1439d0/gen_3c1439d0_1.png` | `0.88` | mais complexo e inferior ao baseline simples |
| A3 | baseline, `MINIMAL`, `1K`, `4:5` | 2 fotos vestindo + 1 detalhe plano | `app/outputs/ref_test_detailmix_minimal_1k/gen_ref_test_detailmix_minimal_1k_1.png` | `0.94` | melhor resultado da rodada |

---

## Subconjuntos usados

## Subconjunto 1 - Somente fotos vestindo

Usado nos baselines iniciais:

- `IMG_3324.jpg`
- `IMG_3326.jpg`
- `IMG_3327.jpg`

Motivo:

- as tres imagens foram fortes no ranking do `build_reference_pack()`
- sao referencias coerentes entre si

## Subconjunto 2 - Fotos vestindo + detalhe plano da peca

Usado no melhor teste desta rodada:

- `IMG_3324.jpg`
- `IMG_3326.jpg`
- `referencia2.jpeg`

Motivo:

- manter contexto de uso real no corpo
- adicionar construcao e leitura limpa da geometria da peca

---

## Resultados

## 1. Falha operacional com 6 referencias grandes em 2K

Teste:

- `gemini-3.1-flash-image-preview`
- 6 referencias de alta resolucao
- `2K`

Resultado:

- erro `500 INTERNAL`

Leitura:

- o setup atual com muitas referencias grandes e resolucao alta nao esta estavel para benchmark
- antes de discutir fidelidade, o ambiente de inferencia ja mostrou fragilidade operacional

Conclusao:

- para benchmark inicial, `1K` e poucas referencias fortes sao mais confiaveis

---

## 2. Baseline controlado com 3 fotos vestindo

### 2.1 `MINIMAL`, `1K`, `4:5`

Arquivo gerado:

- `app/outputs/ref_test_minimal_1k/gen_ref_test_minimal_1k_1.png`

Scores da avaliacao automatica:

- `garment_fidelity`: `0.90`
- `silhouette_fidelity`: `0.85`
- `texture_fidelity`: `0.95`
- `construction_fidelity`: `0.80`
- `natural_model_score`: `0.95`
- `photorealism_score`: `0.98`
- `commercial_quality_score`: `0.92`
- `overall_score`: `0.91`

Resumo:

- otima textura
- excelente realismo
- boa fidelidade geral
- vazamento de styling do look original

Problemas observados:

- manteve bermuda/faixa visual do look original
- transicao ombro/manga nao reproduziu perfeitamente a mesma logica da referencia

### 2.2 `HIGH`, `1K`, `4:5`

Arquivo gerado:

- `app/outputs/ref_test_high_1k/gen_ref_test_high_1k_1.png`

Scores da avaliacao automatica:

- `garment_fidelity`: `0.85`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.80`
- `construction_fidelity`: `0.85`
- `natural_model_score`: `0.95`
- `photorealism_score`: `0.98`
- `commercial_quality_score`: `0.92`
- `overall_score`: `0.89`

Resumo:

- mais "bonita" editorialmente
- pior em textura real da peca

Problema principal:

- simplificacao da malha/croche
- visual mais uniformizado e menos aderente a textura real

### Leitura comparativa `MINIMAL` vs `HIGH`

Para este caso:

- `MINIMAL` venceu em fidelidade
- `HIGH` melhorou polish visual, mas piorou a aderencia material da peca

Conclusao:

- para benchmark de fidelidade, `MINIMAL` deve ser o default inicial

---

## 3. Pipeline completo atual com 3 referencias

Parametros:

- pipeline real
- `3:4`
- `1K`
- sem grounding

Observacao operacional:

- o backend atual nao aceitou `4:5` no fluxo de producao desta rodada
- para o comparativo justo com o pipeline real foi necessario usar `3:4`
- isso significa que o harness isolado hoje consegue testar um envelope melhor que o endpoint de producao

Arquivo gerado:

- `app/outputs/3c1439d0/gen_3c1439d0_1.png`

Prompt final persistido em historico:

```text
RAW photo, A striking Northeastern Brazilian model. Wearing Textured knit ruana wrap with horizontal stripes in olive green and dusty rose. Open-front design with draped dolman-style coverage and a rounded cocoon hem falling to the upper thighs editorial catalog shot, garment fully visible, 3/4 stance with relaxed shoulders and near-camera gaze exact texture, stitch, and fiber relief serene home studio with large diffused window light and simple backdrop polished model, natural expression warm near-camera look with relaxed expression native edge-to-edge composition with background continuity across the full frame dappled natural light revealing fabric texture and depth high-waist dark leggings, ankle boots even soft light, gentle bokeh background, centered composition. Sony A7R IV, 85mm f/1.8. Diffused natural light. Sharp focus on knit texture, visible fiber detail, natural skin realism with pores and subtle imperfections.
```

Scores da avaliacao automatica:

- `garment_fidelity`: `0.85`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.80`
- `construction_fidelity`: `0.85`
- `natural_model_score`: `0.95`
- `photorealism_score`: `0.92`
- `commercial_quality_score`: `0.90`
- `overall_score`: `0.88`

Leitura:

- o pipeline completo nao venceu o baseline simples
- ficou mais lento
- continuou vazando styling do look base

Problemas observados:

- shorts/sandalia ainda apareceram como heranca do visual original
- o agente adicionou varias camadas sem melhorar a fidelidade final da peca

Conclusao:

- a complexidade do pipeline nao trouxe ganho mensuravel nesta rodada

---

## 4. Melhor resultado da rodada: fotos vestindo + detalhe plano

Parametros:

- `gemini-3.1-flash-image-preview`
- `MINIMAL`
- `1K`
- `4:5`
- refs:
  - `IMG_3324.jpg`
  - `IMG_3326.jpg`
  - `referencia2.jpeg`

Arquivo gerado:

- `app/outputs/ref_test_detailmix_minimal_1k/gen_ref_test_detailmix_minimal_1k_1.png`

Scores da avaliacao automatica:

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.92`
- `construction_fidelity`: `0.95`
- `natural_model_score`: `0.98`
- `photorealism_score`: `0.98`
- `commercial_quality_score`: `0.95`
- `overall_score`: `0.94`

Resumo:

- melhor fidelidade estrutural desta rodada
- melhor equilibrio entre realismo e preservacao da peca
- reduziu vazamento do styling original

Interpretacao:

- a referencia de detalhe plano ajudou mais do que adicionar muitas fotos da modelo vestindo
- a peca foi compreendida como objeto/construcao, nao so como aparencia sobre um corpo

Este foi o achado mais importante da rodada.

---

## 5. Rodada 2 - pipeline refinado com `reference_mode_strict`

Depois do diagnostico inicial, o pipeline foi ajustado para testar um caminho mais proximo do benchmark vencedor sem abandonar o stack atual.

Mudancas aplicadas no codigo:

- `VALID_ASPECT_RATIOS` passou a aceitar `4:5`
- o curador de referencias passou a preservar 1-2 outliers estruturais em vez de descartar tudo que foge do cluster principal
- foi criado um fast-path `reference_mode_strict` para uploads com `fidelity_mode=estrita`
- esse fast-path:
  - desliga grounding
  - desliga diversidade
  - nao passa pelo prompt agent completo
  - usa `MINIMAL`
  - monta um prompt curto, comercial e orientado a fidelidade
  - reutiliza `structural_hint` real da triagem visual para ancorar subtype/silhueta

Configuracao usada:

- `guided_brief.fidelity_mode`: `estrita`
- prompt do usuario: vazio
- `aspect_ratio`: `4:5`
- `resolution`: `1K`
- `n_images`: `1`
- grounding: `off`

Pack estrito selecionado:

- `IMG_3324.jpg`
- `IMG_3326.jpg`
- `referencia.jpeg`
- `referencia2.jpeg`

Arquivo gerado:

- `app/outputs/050d2787/gen_050d2787_1.png`

Prompt final:

```text
Ultra-realistic premium fashion catalog photo of a natural adult woman wearing the garment. Direct eye contact, realistic skin texture, natural body proportions, standing pose, full garment clearly visible, clean premium indoor composition, soft natural daylight. Preserve exact garment geometry, texture continuity, and construction details. Garment identity anchor: ruana_wrap, draped silhouette, open front opening, cocoon hem behavior, cape_like sleeve architecture. Catalog-ready minimal styling with the garment as the hero piece. Keep accessories subtle and secondary to the garment. Build new styling independent from the reference person's lower-body look, footwear, and props unless explicitly requested.
```

Scores da avaliacao automatica:

- `garment_fidelity`: `0.95`
- `silhouette_fidelity`: `0.90`
- `texture_fidelity`: `0.95`
- `construction_fidelity`: `0.92`
- `natural_model_score`: `0.98`
- `photorealism_score`: `0.98`
- `commercial_quality_score`: `0.96`
- `overall_score`: `0.95`

Resumo:

- superou o melhor baseline anterior (`0.94`)
- superou com folga o pipeline completo anterior (`0.88`)
- preservou a roupa com mais fidelidade sem sacrificar qualidade comercial
- validou que o problema principal estava na orquestracao, nao no Nano 2 isolado

Leitura:

- a combinacao vencedora deixou de ser "mais inteligencia"
- passou a ser "melhor curadoria + prompt curto + ancora estrutural + menos interferencia"
- o caminho mais promissor para o produto agora e evoluir esse `reference_mode_strict`

---

## 6. Rodada 3 - bateria curta para extrair a heuristica do agente

Objetivo:

- validar se o agente precisa sempre de refs de detalhe
- validar se mais imagens ajudam ou atrapalham
- validar se prompt mais longo melhora ou so adiciona ruído
- validar se ha variancia suficiente para justificar rerank

Todos os testes abaixo usaram:

- `gemini-3.1-flash-image-preview`
- `MINIMAL`
- `1K`
- `4:5`
- `structural_hint`: `ruana_wrap, draped silhouette, cape_like sleeve architecture, cocoon hem`

### Matriz

| Caso | Refs | Prompt/Cenario | Score | Leitura |
| --- | --- | --- | --- | --- |
| `c3_4worn_short_indoor` | 4 vestindo | curto, indoor | `0.95` | melhor score da bateria |
| `c5_4mix_short_outdoor` | 2 vestindo + 2 detalhe | curto, outdoor | `0.95` | melhor score em cenario externo |
| `c1_3mix_short_indoor` | 2 vestindo + 1 detalhe | curto, indoor | `0.94` | excelente e mais barato em refs |
| `c6_4mix_long_indoor` | 2 vestindo + 2 detalhe | longo, indoor | `0.94` | prompt longo nao trouxe ganho real |
| `c4_6worn_short_indoor` | 6 vestindo | curto, indoor | `0.93` | mais imagens nao melhoraram |
| `c2_4mix_short_indoor` | 2 vestindo + 2 detalhe | curto, indoor | `0.91` | caso abaixo do esperado; investigar variancia |

### Repeticao do caso `c2_4mix_short_indoor`

Mesma configuracao, 2 novas geracoes:

- repeticao 1: `0.93`
- repeticao 2: `0.94`

Leitura:

- existe variancia estocastica real no Nano 2 mesmo com a mesma configuracao
- a oscilacao observada nesta peca ficou em torno de `0.02` a `0.04`
- isso justifica considerar `top-2 candidate rerank` em vez de confiar 100% em single-shot

### Conclusoes praticas para o agente

#### 1. Mais imagens nao significam mais fidelidade

O caso com 6 fotos vestindo perdeu para 4 fotos vestindo e tambem nao superou o mix curto com detalhe.

Regra:

- evitar pack grande por default
- comecar com `3` ou `4` refs fortes

#### 2. Prompt curto e ancorado vence prompt longo na maior parte do tempo

O prompt longo nao superou o curto de forma relevante.

Regra:

- usar prompt curto
- incluir ancora estrutural objetiva
- evitar excesso de camera jargon e floreio editorial

#### 3. Refs de detalhe ajudam, mas nao sao obrigatorias em todo caso

Nesta peca especifica:

- `2 vestindo + 1 detalhe` foi muito forte
- `2 vestindo + 2 detalhe` tambem foi forte
- mas `4 vestindo` tambem atingiu o topo quando as fotos vestindo eram coerentes e boas

Regra:

- se houver detalhes planos bons, usar pelo menos `1`
- se as fotos vestindo forem muito consistentes, o agente pode operar bem sem detalhe
- se o garment for estruturalmente ambiguo, detalhe volta a ser prioritario

#### 4. O agente precisa escolher subset, nao despejar tudo

O ganho veio de selecao, nao de volume.

Regra sugerida:

- priorizar 2 fotos vestindo com boa leitura frontal/3-4
- adicionar 1 ou 2 refs estruturais diversas
- descartar o resto para a chamada principal

#### 5. Outdoor e indoor podem funcionar

O cenario externo nao degradou fidelidade quando o prompt continuou curto e o lock estrutural permaneceu forte.

Regra:

- cenario pode variar
- fidelidade nao pode depender do cenario
- o lock estrutural deve vir antes do styling

### Heuristica provisoria do agente

Para casos de fotos reais/amadoras/anuncio:

1. Curar e deduplicar todas as imagens.
2. Selecionar `3` ou `4` refs maximas para geracao.
3. Prioridade de selecao:
   `2` fotos vestindo coerentes + `1` detalhe bom.
   Se houver outro detalhe estrutural forte, subir para `4` refs.
4. Gerar prompt curto com:
   - foto de catalogo ultra realista
   - garment as hero piece
   - ancora estrutural objetiva
   - styling comercial limpo
5. Rodar `MINIMAL`, `1K`, `4:5`.
6. Quando a peca for importante ou ambigua, gerar `2` candidatas e reranquear por fidelidade.

Este conjunto de regras ficou muito mais proximo do raciocinio manual que produziu os melhores resultados.

---

## 7. Rodada 4 - tentar unir fidelidade da roupa com troca real de modelo/ambiente

Problema observado manualmente:

- os melhores resultados de fidelidade ainda herdavam demais a identidade da foto original
- o melhor resultado em troca de modelo/ambiente (`050d2787`) ainda perdia parte da verdade estrutural da peca

Foram testadas duas intervencoes adicionais.

### Teste A - `anonmix01`

Estrategia:

- manter geracao em um unico passo
- aplicar desidentificacao leve nas duas fotos vestindo
- combinar com `referencia.jpeg` e `referencia2.jpeg`
- manter prompt curto e `structural_hint`

Arquivo:

- `app/outputs/anonmix01/gen_anonmix01_1.png`

Leitura manual:

- melhorou um pouco a independencia visual
- mas ainda manteve demais a mesma “linguagem” da referencia
- ainda nao trocou o look interno do jeito desejado
- portanto, sozinho, nao resolve o problema do produto

### Teste B - `editmix01`

Estrategia:

- usar como base uma imagem muito fiel de roupa
- rodar uma segunda etapa de edicao pedindo:
  - modelo claramente diferente
  - innerwear novo
  - ambiente novo
  - preservacao total do cardigan/ruana
- passar `referencia.jpeg` e `referencia2.jpeg` como ancora da roupa na edicao

Arquivo:

- `app/outputs/editmix01/edit_editmix01_1.png`

Leitura manual:

- foi a intervencao mais promissora desta rodada
- trocou modelo, innerwear e ambiente de forma muito mais clara
- preservou a roupa melhor do que `050d2787`
- ainda pode haver leve simplificacao no caimento em relacao ao melhor caso de fidelidade pura
- mesmo assim, ficou mais perto do objetivo comercial final

### Conclusao desta rodada

Para unir “roupa muito fiel” com “modelo e ambiente realmente novos”, a direcao mais forte ate agora nao e um unico prompt mais esperto.

E:

1. gerar primeiro a melhor versao possivel da roupa
2. depois editar apenas identidade/innerwear/cenario
3. manter a roupa travada por prompt e referencias de detalhe

Em outras palavras:

- `single-pass` ainda parece bom para benchmark e para alguns casos
- `two-pass` parece mais promissor para o produto real

---

## Diagnostico tecnico

## 1. O benchmark atual esta contaminado por complexidade

Hoje o pipeline real mistura:

- triagem visual
- diversidade de modelo/cenario/pose
- prompt compiler
- camada comercial
- repair prompt
- scoring tecnico

Isso dificulta responder a pergunta mais basica:

- "o modelo preservou a roupa ou nao?"

## 2. O estado do sistema interfere no experimento

O pipeline de diversidade persiste estado e muda casting/cenario com o tempo.

Para benchmark isso e ruim porque:

- duas execucoes teoricamente equivalentes deixam de ser equivalentes

## 3. O curador de referencia provavelmente esta descartando sinal importante

As imagens de detalhe da peca ajudam a preservar:

- construcao
- geometria
- leitura do padrao
- continuidade das listras

Hoje essas imagens parecem ser tratadas como outlier e nao como ancora estrutural.

## 4. `HIGH` nao deve ser assumido como melhor para fidelidade

Nesta peca:

- `HIGH` melhorou polish
- `MINIMAL` preservou melhor a textura real

Logo:

- `HIGH` nao deve ser default cego

## 5. O modelo ainda puxa styling do look de referencia

Mesmo com prompt pedindo foto de catalogo limpa, o modelo ainda herda:

- parte inferior
- acessorios
- styling do corpo base

Isso indica que:

- fotos da modelo vestindo sao referencias ambivalentes
- ajudam a mostrar drapeado
- mas tambem vazam informacao de look

---

## O que funcionou

- reduzir o teste para um setup simples
- usar `1K`
- usar poucas referencias fortes
- usar `MINIMAL`
- adicionar uma referencia de detalhe plano da peca
- avaliar a saida com score estruturado

---

## O que nao funcionou bem

- 6 referencias grandes em `2K`
- assumir que mais referencia sempre melhora
- assumir que `HIGH` melhora fidelidade
- assumir que o pipeline completo atual melhora o benchmark
- depender so de fotos da modelo vestindo para representar a peca

---

## Recomendacoes imediatas

## 1. Criar `benchmark mode`

Esse modo deve rodar:

- sem agente
- sem grounding
- sem repair
- sem diversidade
- sem estado persistente
- sem prompt rewriting automatico do pipeline

Objetivo:

- medir o motor de imagem antes das camadas de orquestracao

## 2. Mudar a curadoria de referencia

Regra sugerida:

- manter 2 refs "vestindo"
- manter 1 ou 2 refs "detalhe/plano da peca"
- nao tratar detalhe de construcao como outlier visual

## 3. Fixar defaults de benchmark

Defaults sugeridos para primeira fase:

- modelo: `gemini-3.1-flash-image-preview`
- thinking: `MINIMAL`
- resolucao: `1K`
- refs: 3 ou 4 no maximo
- aspect ratio de benchmark: `4:5` no harness isolado

## 4. So depois comparar outros motores

Quando o benchmark simples estiver estabilizado, comparar:

- `virtual-try-on-001`
- `imagen-product-recontext-preview-06-30`
- pipeline Gemini atual

## 5. Prioridade imediata mudou

Com o resultado da Rodada 2, a prioridade tecnica deixa de ser integrar outro motor agora.

Passa a ser:

- endurecer o `reference_mode_strict`
- transformar esse caminho em padrao para casos com fotos reais/amadoras da roupa
- so depois reintroduzir sofisticacoes que provarem ganho real

---

## Artefatos principais desta rodada

Referencias visuais e comparativos gerados:

- `app/outputs/reference_test_contact_sheet.jpg`
- `app/outputs/reference_test_candidate_subset.jpg`
- `app/outputs/reference_vs_outputs_comparison.jpg`
- `app/outputs/reference_vs_baselines_vs_pipeline.jpg`
- `app/outputs/reference_test_findings_sheet.jpg`

Saidas principais:

- `app/outputs/ref_test_minimal_1k/gen_ref_test_minimal_1k_1.png`
- `app/outputs/ref_test_high_1k/gen_ref_test_high_1k_1.png`
- `app/outputs/ref_test_detailmix_minimal_1k/gen_ref_test_detailmix_minimal_1k_1.png`
- `app/outputs/3c1439d0/gen_3c1439d0_1.png`

---

## Conclusao

A hipotese inicial foi confirmada.

O projeto provavelmente comecou com uma estrutura mais proxima do problema central e, ao adicionar muitas camadas de inteligencia e automacao, perdeu capacidade de medir com clareza o que realmente melhora a fidelidade da roupa.

Nesta rodada, o melhor resultado nao veio do pipeline mais complexo.

Veio de:

- menos referencias
- referencias mais certas
- `MINIMAL`
- uma mistura melhor entre referencia no corpo e detalhe plano da peca

Em outras palavras:

- o problema atual parece menos "falta de prompt bom"
- e mais "falta de desenho experimental limpo + curadoria correta de referencia"
