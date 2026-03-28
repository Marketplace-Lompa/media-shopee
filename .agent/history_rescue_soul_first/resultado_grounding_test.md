# 🧪 Resultado — Teste de Google Search Grounding

## Configuração do Teste
| Parâmetro | Valor |
|---|---|
| **Mode** | `lifestyle` |
| **Model** | `gemini-2.5-flash` |
| **Peça** | Vestido midi floral (viscose, tons terrosos, decote V) |
| **Prompt** | Pediu 3 cenários brasileiros reais para fotografar a peça |

---

## Resultados

### ✅ Resposta COM Grounding (Google Search)
- **8.761 caracteres** de resposta
- **9 trechos suportados** por fontes da web
- Cenários sugeridos:
  1. 🏪 **Feira de Antiguidades — Largo da Ordem (Curitiba)** ou Bixiga (SP)
  2. 🌿 **Estufa/Viveiro — Jardim Botânico de Curitiba** ou Holambra (SP)
  3. 🏛️ **Rua de Pedra — Ouro Preto (MG)** ou Paraty (RJ)

#### Metadata de Grounding
O modelo acionou a busca e retornou **grounding_supports** com trechos como:
- *"As modelos parecem estar vivendo um momento, não apenas posando..."*
- *"Cafés charmosos, parques urbanos, feiras, ruas pitorescas..."*
- *"Cores e Texturas Complementares: Escolha de cenários que harmonizem..."*

> [!NOTE]
> O campo `grounding_chunks` (fontes com URLs) veio vazio neste teste, mas os `grounding_supports` confirmam que o modelo pesquisou e usou informação da web para fundamentar as sugestões.

---

### 📋 Resposta SEM Grounding (Baseline)
- **8.173 caracteres** de resposta
- Cenários sugeridos:
  1. 🎨 **Santa Teresa, Rio de Janeiro** — ruas de paralelepípodos, grafites
  2. 🍎 **Mercado Municipal de Pinheiros, São Paulo** — feira gourmet
  3. 🏛️ **Centro Histórico de São Luís, Maranhão** — azulejos coloniais

---

## 📊 Análise Comparativa

| Aspecto | COM Grounding | SEM Grounding |
|---|---|---|
| **Tamanho** | 8.761 chars | 8.173 chars |
| **Fontes da web** | 9 trechos suportados | Nenhuma |
| **Especificidade** | Alta — cita locais precisos | Alta — também bom |
| **Referências visuais** | Menciona Farm Rio, campanhas reais | Menciona Farm, Amaro, influenciadoras |
| **Fidelidade ao mode** | ✅ Ação mid-life presente | ✅ Ação mid-life presente |
| **Variação** | Locais menos óbvios | Locais mais "esperados" |

---

## 🎯 Conclusão

### O que o Grounding adiciona de valor real:

1. **Fundamentação em tendências atuais** — O modelo pesquisou o que está funcionando AGORA em fotografia de e-commerce brasileira, não apenas usou conhecimento estático
2. **Suporte com confiança** — Os `grounding_supports` provam que trechos específicos da resposta foram baseados em dados da web
3. **Cenários mais inesperados** — O grounding sugeriu Largo da Ordem (Curitiba) e viveiros de Holambra, que são menos óbvios que Santa Teresa ou São Luís
4. **Alinhamento com soul do mode** — Ambas as respostas respeitaram o contrato do lifestyle (ação mid-activity, cenário co-protagonista)

### Limitações observadas:
- As URLs das fontes (`grounding_chunks.web`) vieram vazias neste teste — pode ser um comportamento intermitente da API
- A diferença qualitativa entre grounded e baseline não é drástica para este tipo de prompt genérico
- O valor real do grounding será maior quando pedirmos informações **temporais** (tendências da semana, sazonalidade)

### Próximos passos recomendados:
1. Testar com prompts que exijam dados temporais ("trending locations for fashion in Brazil March 2026")
2. Testar URL Context com um anúncio real da Shopee como contexto
3. Integrar o grounding como step pré-prompt no pipeline do `pose_soul.py`

---

> [!TIP]
> O grounding funciona melhor como **enrichment layer** — não como substituto do raciocínio criativo do modelo. Use-o para injetar dados reais do mercado ANTES de gerar o prompt de fotografia.
