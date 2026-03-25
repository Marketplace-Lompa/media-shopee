# Pipeline com Grounding — Peças Atípicas

## O Problema

Peças com silhueta atípica (cardigan kimono manga morcego, poncho aberto, capa assimétrica)
confundem o Nano porque ele não conhece a construção. Exemplo real:

- **Peça real**: Cardigan kimono de crochê, manga morcego, frente aberta, com cachecol combinando
- **O que o Nano gerou**: Poncho fechado tipo cobertor enrolado — sem frente aberta, sem mangas dolman

**Causa raiz**: O Agent descreve "striped knit poncho" (genérico), e o Nano interpreta
com a silhueta mais comum que conhece (poncho fechado). Falta vocabulário técnico
e referência visual de como a peça é vestida no mundo real.

---

## Pipeline Proposto (3 Fases)

```
┌─────────────────────────────────────────────────────────┐
│                  FASE 1 — VISUAL ANALYSIS               │
│  Agent (Gemini Flash) recebe as imagens do produto      │
│  → Identifica: silhueta, construção, tipo de tecido     │
│  → Output: descrição estrutural básica                  │
│  → Ex: "peça aberta na frente, sem botões,              │
│    mangas integradas ao corpo (dolman/morcego),          │
│    cachecol combinando, crochê listrado bicolor"         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│          FASE 2A — GROUNDING (Google Search)            │
│  Agent pesquisa usando a descrição da Fase 1:           │
│                                                         │
│  Query 1 (terminologia):                                │
│    "cardigan kimono crochê manga morcego e-commerce"    │
│  → Retorna: nome correto, variações de nomenclatura     │
│                                                         │
│  Query 2 (referência visual/styling):                   │
│    "como fotografar cardigan kimono poncho para loja"    │
│  → Retorna: poses, styling, composições reais           │
│                                                         │
│  Output: vocabulário correto + URLs de referência       │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│       FASE 2B — DOWNLOAD DE IMAGENS DE REFERÊNCIA       │
│  (Fase opcional mas CRÍTICA para peças atípicas)        │
│                                                         │
│  O Grounding retorna URLs de sites de e-commerce        │
│  → Backend baixa 2-3 fotos de lookbook/catálogo de      │
│    peças similares sendo VESTIDAS por modelos reais      │
│                                                         │
│  Essas imagens servem como "visual examples" para       │
│  o Nano entender COMO a peça drape no corpo:            │
│    • Como as mangas morcego caem                        │
│    • Como a frente aberta se comporta                   │
│    • Como o cachecol é usado junto                      │
│                                                         │
│  Tecnicamente: o Nano já aceita múltiplas imagens       │
│  via inline_data (pool_images). As referências           │
│  baixadas entram como "style reference" adicional.      │
│                                                         │
│  ⚠️ Limitação: Grounding retorna URLs de páginas,      │
│  não diretamente imagens. Opções para resolver:         │
│    a) Extrair <img> tags das URLs retornadas            │
│    b) Usar Google Custom Search Image API (separada)    │
│    c) Usar google_search com query "site:shopee.com.br  │
│       cardigan kimono" + scraping de thumbnails         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│         FASE 3 — PROMPT ENRIQUECIDO + GERAÇÃO           │
│  Agent combina:                                         │
│    • Análise visual (Fase 1)                            │
│    • Vocabulário correto + referências reais (Fase 2A)  │
│    • Skills de moda, realismo, e-commerce               │
│                                                         │
│  Nano recebe:                                           │
│    1. Foto do produto (uploaded_images) → fidelidade    │
│    2. Fotos de referência (Fase 2B) → silhueta correta  │
│    3. Prompt enriquecido (Fase 3) → direção precisa     │
│                                                         │
│  → Prompt usa termos CORRETOS:                          │
│    "open-front batwing/dolman cardigan" em vez de        │
│    "poncho" → Nano entende a silhueta                   │
│                                                         │
│  → Pose INFORMADA por fotos reais:                      │
│    "arms slightly spread to show the draping batwing    │
│    silhouette, front panels falling open naturally"      │
│                                                         │
│  → Nano viu fotos reais da silhueta → não alucina       │
└─────────────────────────────────────────────────────────┘
```

---

## Implementação Técnica

### Mudança no `agent.py`

O Agent já faz a Fase 1 (análise visual). Para adicionar a Fase 2 (Grounding),
basta ativar o Google Search como tool na chamada `generate_content`:

```python
config=types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    temperature=0.8,
    max_output_tokens=2048,
    safety_settings=SAFETY_CONFIG,
    tools=[
        types.Tool(google_search=types.GoogleSearch())
    ],
)
```

### Mudança na System Instruction

Adicionar uma nova seção que instrui o Agent a usar o Google Search quando detectar
uma peça com silhueta incomum:

```
SECTION 7 — GROUNDING RESEARCH (quando disponível)

Quando detectar peça com silhueta ATÍPICA (não é camiseta, calça, saia, vestido padrão):
  1. BUSQUE o nome correto do tipo de peça usando Google Search
     Ex: "cardigan manga morcego dolman crochê"
  2. BUSQUE referências de como a peça é fotografada profissionalmente
     Ex: "fashion photography dolman cardigan e-commerce"
  3. USE os resultados para:
     - Nomear a peça corretamente no prompt (kimono cardigan, não "poncho")
     - Descrever a silhueta com vocabulário técnico preciso
     - Escolher pose que MOSTRA a silhueta (braços abertos para dolman)
     - Evitar confusão com peças similares (poncho ≠ cardigan ≠ capa)

PEÇAS QUE REQUEREM PESQUISA:
  - Manga morcego / dolman / asa → NÃO é poncho nem casaco normal
  - Cardigan assimétrico / mullet → frente mais curta que costas
  - Kaftan → NÃO é vestido nem túnica
  - Ruana / xale → NÃO é poncho fechado
  - Pelerine → cape shoulders, não capa inteira
```

### Mudança no `stream.py` (SSE)

Novo evento SSE para a Fase 2:

```python
yield _sse_event("researching", {
    "message": "Pesquisando referências reais na web…",
    "search_queries": ["cardigan kimono crochet", "dolman sleeve photography"]
})
```

### Impacto no Tempo

| Fase | Tempo Estimado | Observação |
|------|---------------|------------|
| Fase 1 (análise visual) | ~3s | Já existe |
| Fase 2 (grounding) | +2-5s | Novo — pesquisa web |
| Fase 3 (prompt + geração) | ~15-30s | Já existe |
| **Total** | **~20-38s** | +2-5s vs pipeline atual |

---

## Quando Ativar o Grounding

Não faz sentido pesquisar no Google para uma camiseta básica. O Agent deve decidir:

| Cenário | Grounding? |
|---------|-----------|
| Camiseta, calça, saia, vestido reto | ❌ Desnecessário |
| Manga morcego, dolman, kimono | ✅ Pesquisar silhueta |
| Peça com nome incerto | ✅ Pesquisar nomenclatura |
| Peça artesanal/crochê complexo | ✅ Pesquisar referências |
| Lingerie básica | ❌ Desnecessário |
| Body/macacão assimétrico | ✅ Pesquisar construção |

---

## Custo

- **Free tier**: ~1.500 prompts grounded/dia
- Se 30% dos prompts ativam grounding → ~5.000 gerações/dia no free tier
- Custo excedente: $35/1.000 prompts grounded

---

## Próximos Passos

1. [ ] Ativar `types.Tool(google_search=types.GoogleSearch())` no agent
2. [ ] Adicionar SECTION 7 na system instruction com regras de quando pesquisar
3. [ ] Adicionar evento SSE "researching" no pipeline
4. [ ] Testar com peças atípicas: kimono, kaftan, ruana, pelerine
5. [ ] Ajustar threshold — decidir se grounding é sempre-on ou condicional
