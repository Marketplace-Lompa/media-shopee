# Auditoria de Determinismo no Pipeline (Atualizado)

## 1. Resumo Executivo
O comportamento rígido não vem só do texto do prompt. Hoje o pipeline está com **fidelidade da peça em primeiro lugar** e, por design, isso reduz liberdade de modelo humana, cenário e pose quando `has_images=true` e `has_prompt=false`.

Principais fatores determinísticos ativos:
- Condicionamento visual forte no Nano via imagens de referência.
- Compilador com prioridade P1 (estrutura da peça) e truncamento agressivo da base.
- Gating de capa catálogo no modo sem texto.
- Cláusulas fixas de styling complementar e composição.
- Scheduler de diversidade com estado persistido.

---

## 2. Diagnóstico Técnico no Código

### A. Condicionamento visual direto no gerador (não é só prompt)
As imagens curadas são sempre enviadas ao modelo de imagem, antes do texto, como referência visual forte:
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/generator.py` (linhas ~63-80)

Impacto:
- Ajuda fidelidade de roupa.
- Pode “puxar” rosto/pose/cenário da referência, mesmo com instrução textual para trocar.

### B. Gating de capa no modo sem texto
No `reference_mode` sem prompt do usuário, o compilador ativa defaults de capa e poda termos de lifestyle/movimento:
- `force_cover_defaults`: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent.py` (linha ~1432)
- prune de pose/lifestyle: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent.py` (linhas ~1258-1298)

Impacto:
- Reduz saídas sentadas/café (bom para catálogo).
- Também achata variação criativa quando usuário quer alternativa sem escrever prompt.

### C. Prioridade estrutural P1 + reserva de budget
As cláusulas estruturais entram primeiro e têm prioridade máxima:
- P1 e `struct_priority`: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent.py` (linhas ~1442-1453 e ~1387 no bloco de compressão)
- reserva para P1/P2-P4 + descarte por budget: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent.py` (linhas ~1584-1665)

Impacto:
- Estabiliza geometria da peça.
- “Esmaga” parte da criatividade de composição quando orçamento textual fica apertado.

### D. Truncamento agressivo da narrativa base com imagem
Quando há referência, a base narrativa é capada para 12 palavras:
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent.py` (linhas ~1628-1634)

Impacto:
- Remove boa parte de cenário/pose/modelo que o LLM propõe.
- Mantém quase só framing curto + cláusulas rígidas.

### E. Cláusula de cenário orientada a fundo desfocado
`_scene_composition_clause` privilegia “subject sharp + background softly defocused”:
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent.py` (linhas ~935-967)

Impacto:
- Consistência comercial.
- Menor variedade de leitura de ambiente (urbano/lifestyle/editorial).

### F. Styling complementar fixo
Quando peça é upper-body e o base não menciona parte inferior, injeta:
`"fitted dark trousers, minimal footwear"`
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent.py` (linhas ~1494-1515)

Impacto:
- Evita vazamento da peça inferior da referência.
- Repetição visual e sensação de “mesmo look” entre jobs.

### G. Diversidade parcialmente determinística por estado
Seleção de perfil/cenário/pose usa estado persistido + cursor:
- `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/pipeline_effectiveness.py` (linhas ~459-525)

Impacto:
- Boa distribuição de repetição.
- Sem prompt (`seed_hint=""`), padrão pode parecer previsível.

---

## 3. Conclusão da Auditoria
O documento anterior estava parcialmente correto, mas incompleto.  
**O núcleo do determinismo atual é híbrido:**
1. Prompt compiler rígido (P1 e truncamento).
2. Condicionamento visual das referências no gerador.
3. Gating de capa e defaults comerciais.

Portanto, a solução não é “soltar o prompt” isoladamente; precisa rebalancear gates e budget sem perder fidelidade.

---

## 4. Plano de Ajuste (Lean, sem overengineering)

### MT-A — Rebalancear budget de base em modo com referência
- Trocar limite fixo de 12 palavras por faixa dinâmica (ex.: 24-40) quando confiança estrutural já estiver alta.
- Preserva fidelidade, devolvendo espaço para variação de modelo/pose/cenário.

### MT-B — Cover-first em vez de cover-hard
- Manter restrição dura só para: peça legível, modelo em pé, sem sentado/mesa/café.
- Tornar gaze/cenário mais flexíveis no modo sem texto.

### MT-C — Variar styling complementar de forma controlada
- Substituir frase fixa de trousers por pool pequeno contextual (ex.: trousers/skirt/jeans clean), sem quebrar leitura da peça.
- Aplicar apenas quando não houver escolha explícita do usuário.

### MT-D — Suavizar composição de cenário
- Em vez de sempre “softly defocused”, alternar intensidade de DOF por cenário e intenção.
- Manter padrão catálogo, mas com mais leitura do ambiente.

### MT-E — Telemetria de rigidez (debug)
- Expor no debug final quais cláusulas criativas foram descartadas por budget.
- Facilita ajuste sem tentativa e erro cego.

---

## 5. Critério de Aceite
- Fidelidade da peça permanece estável.
- Sem prompt, primeira imagem continua capa catálogo.
- Sem prompt, modelo/cenário/pose variam perceptivelmente entre jobs.
- Não retorna comportamento “sentada/café” no automático.
- Prompt final sem contradições estruturais.
