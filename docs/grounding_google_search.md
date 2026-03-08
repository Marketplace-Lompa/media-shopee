# Grounding with Google Search — Gemini API

## O que é

Grounding conecta o Gemini a dados em tempo real via Google Search, permitindo respostas mais precisas, atualizadas e com menos alucinações. O modelo decide automaticamente se precisa buscar na web e retorna citações inline das fontes.

---

## Implementação com `google-genai` SDK

### Uso básico

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_KEY")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Qual a cotação atual do dólar em reais?",
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ]
    ),
)

print(response.text)
```

### Com Dynamic Retrieval (controle de quando ativar)

> [!IMPORTANT]
> `DynamicRetrievalConfig` funciona apenas com **Gemini 1.5 Flash**. Para Gemini 2.0+, use "Search as a tool" (exemplo acima).

```python
response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="Qual a previsão do tempo em Curitiba?",
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                google_search_retrieval=types.GoogleSearchRetrieval(
                    dynamic_retrieval_config=types.DynamicRetrievalConfig(
                        mode="MODE_DYNAMIC",
                        dynamic_threshold=0.3,  # 0 = sempre grounding, 1 = nunca
                    )
                )
            )
        ]
    ),
)
```

### Acessando Grounding Metadata

```python
candidate = response.candidates[0]
metadata = candidate.grounding_metadata

# Queries executadas no Google
print(f"Search queries: {metadata.web_search_queries}")

# Widget de busca (HTML renderizado)
print(metadata.search_entry_point.rendered_content)

# URLs usadas como fonte
for chunk in metadata.grounding_chunks:
    print(f"  - {chunk.web.title}: {chunk.web.uri}")
```

---

## Classes e Tipos

| Tipo | Descrição |
|------|-----------|
| `types.GoogleSearch()` | Ativa Google Search como tool (Gemini 2.0+) |
| `types.GoogleSearchRetrieval()` | Ativa com config dinâmica (Gemini 1.5) |
| `types.DynamicRetrievalConfig` | Controla quando o grounding é ativado |
| `types.DynamicRetrievalConfigMode` | `MODE_UNSPECIFIED` ou `MODE_DYNAMIC` |
| `grounding_metadata.web_search_queries` | Lista de queries executadas |
| `grounding_metadata.grounding_chunks` | Lista de fontes (web/imagem) usadas |
| `grounding_metadata.search_entry_point` | Widget de busca com HTML |

---

## `dynamic_threshold` Explicado

O sistema atribui um **prediction score** (0 a 1) ao prompt indicando se ele se beneficiaria de grounding:

| Threshold | Comportamento |
|-----------|---------------|
| `0.0` | **Sempre** aplica grounding — toda query vai ao Google |
| `0.3` | **Default** — grounding quando score > 0.3 (recomendado) |
| `0.7` | Conservador — só grounding para queries muito informacionais |
| `1.0` | **Nunca** aplica grounding |

---

## Preço e Limites

| Item | Valor |
|------|-------|
| **Free tier** | ~1.500 prompts grounded/dia (Gemini 2.5 Flash) |
| **Pago** | ~$35 por 1.000 prompts grounded |
| **Tokens de contexto** | O texto/imagens recuperados **NÃO** são cobrados como input tokens |
| **Fontes por request** | Até 10 fontes de grounding por geração |
| **Google Maps** | $25/1.000 prompts, free tier 500/dia |

> [!WARNING]
> Cada search query individual dentro de um request é contada — se o modelo fizer 3 queries para responder 1 prompt, conta como 3.

---

## Casos de Uso no Projeto

### Potencial para o Studio

1. **Pesquisar tendências de moda**: o agente poderia buscar "tendências moda verão 2025 Brasil" antes de criar cenários
2. **Verificar cores da temporada**: "cores pantone 2025 moda feminina" para escolher paletas atuais
3. **Pesquisar referências de pose**: "fashion photography poses e-commerce 2025"

### Como integrar no `agent.py`

```python
# Em agent.py, adicionar ao generate_content:
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

> [!CAUTION]
> Ao ativar grounding no Agent, o modelo pode demorar mais (2-5s extras por query). Avaliar impacto no tempo total do pipeline antes de ativar em produção.

---

## Modelos Compatíveis

| Modelo | Método | Suporte |
|--------|--------|---------|
| Gemini 2.5 Flash/Pro | `types.Tool(google_search=...)` | ✅ Recomendado |
| Gemini 2.0 Flash | `types.Tool(google_search=...)` | ✅ |
| Gemini 1.5 Flash | `GoogleSearchRetrieval` + `DynamicRetrievalConfig` | ✅ Legacy |
| Gemini 1.5 Pro | `GoogleSearchRetrieval` | ✅ Legacy |
| Nano Banana 2 (image gen) | N/A | ❌ Não suportado |

---

## Referências

- [Gemini API Grounding Docs](https://ai.google.dev/gemini-api/docs/grounding)
- [python-genai SDK](https://github.com/googleapis/python-genai)
- [Gemini API Pricing](https://ai.google.dev/pricing)
