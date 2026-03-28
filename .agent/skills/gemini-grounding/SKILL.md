---
name: gemini-grounding
description: Use when implementing or debugging Gemini API grounding features — Google Search, URL Context, Code Execution, Tool Combination, or agentic tool orchestration. Covers real-time web data access, URL content extraction, multi-tool pipelines, dynamic retrieval thresholds, grounding metadata handling, and integration patterns for the MEDIA-SHOPEE agent runtime.
---

# Gemini Grounding Tools

Use this skill when the task involves connecting Gemini models to external data sources in real time — web search, specific URLs, code execution, or combining multiple tools in an agentic loop. This skill is the authoritative reference for implementing grounding capabilities in the MEDIA-SHOPEE backend (`pose_soul.py` and related agent runtime files).

## Quick Start

If the user asks about grounding, answer in this order:
1. identify which grounding tool is needed (Google Search, URL Context, Code Execution, or a combination)
2. determine if the use case requires integrated tools only, custom functions only, or a hybrid
3. select the correct configuration pattern
4. implement with proper error handling and metadata extraction
5. call out compatibility restrictions (e.g., URL Context is NOT available on Vertex AI)

## Scope

Run this skill for:
- adding Google Search grounding to any Gemini API call
- using URL Context to extract and process content from specific web pages
- combining integrated tools (Google Search, URL Context) with custom `function_declarations`
- implementing agentic tool orchestration loops (model calls tool → code executes → returns result → model continues)
- configuring dynamic retrieval thresholds for Google Search
- extracting and using `grounding_metadata` (sources, search snippets, support chunks)
- debugging grounding failures (robots.txt blocks, unsupported content, Vertex AI incompatibility)
- Code Execution sandbox for data processing within Gemini

Default stance:
- always use the official Google AI Python SDK (`google-genai`) patterns
- prefer `google.genai.types` for all type definitions
- separate "integrated tools" (server-side, Google-managed) from "custom functions" (client-side, your code)
- never assume URL Context works on Vertex AI — it does NOT

## Core Concepts

### Grounding vs. RAG vs. Context Window

| Approach | When to Use | Latency | Data Freshness |
|---|---|---|---|
| **Context Window** | Small, known documents passed directly in the prompt | Lowest | Static (you control) |
| **RAG (Retrieval)** | Large internal knowledge bases, vector search | Medium | Semi-fresh (index updates) |
| **Google Search Grounding** | Real-time web information, trending topics, current prices | Higher | Real-time |
| **URL Context** | Specific known URLs whose content you need analyzed | Higher | Real-time (fetched at request time) |

### Integrated Tools vs. Custom Functions

This is the most critical distinction:

**Integrated Tools** (server-side, Google executes):
- `GoogleSearch` — model searches the web autonomously
- `UrlContext` — model fetches and processes URL content
- `CodeExecution` — model writes and runs Python in a sandbox

**Custom Functions** (`function_declarations`, client-side, YOUR code executes):
- You define the function schema
- Model returns a `function_call` with arguments
- Your code executes the function
- You return a `function_response` to the model
- Model uses the result to continue

**Key rule**: when combining both types, do NOT use `automatic_function_calling`. You must handle the loop manually.

## Tool Reference

### 1. Google Search Grounding

#### Purpose
Lets the model search the web in real time to ground its responses in current information.

#### Configuration

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# Básico — modelo decide quando buscar
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Qual o preço médio de vestidos na Shopee Brasil hoje?",
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    ),
)
```

#### Dynamic Retrieval (Controle de Threshold)

O modelo pode decidir usar ou não a busca com base em um threshold de confiança:

```python
config = types.GenerateContentConfig(
    tools=[
        types.Tool(
            google_search=types.GoogleSearch(
                dynamic_retrieval_config=types.DynamicRetrievalConfig(
                    mode="MODE_DYNAMIC",
                    dynamic_threshold=0.6,  # 0.0 = sempre busca, 1.0 = nunca busca
                )
            )
        )
    ]
)
```

**Heurística para threshold:**
- `0.0–0.3` → busca quase sempre (dados em tempo real, preços, tendências)
- `0.3–0.6` → busca quando o modelo não tem confiança (padrão recomendado)
- `0.6–1.0` → busca raramente (dados que o modelo provavelmente já sabe)

#### Grounding Metadata

Toda resposta com grounding retorna metadados ricos:

```python
response = client.models.generate_content(...)

# Acessar metadados de grounding
metadata = response.candidates[0].grounding_metadata

# Fontes usadas
for chunk in metadata.grounding_chunks:
    print(f"Fonte: {chunk.web.title} — {chunk.web.uri}")

# Suporte por trecho da resposta
for support in metadata.grounding_supports:
    print(f"Trecho: {support.segment.text}")
    print(f"Fontes: {[metadata.grounding_chunks[i] for i in support.grounding_chunk_indices]}")
    print(f"Confiança: {support.confidence_scores}")

# Snippet de busca renderizável (HTML)
if metadata.search_entry_point:
    print(f"Search widget: {metadata.search_entry_point.rendered_content}")
```

**Importante sobre `search_entry_point`:**
- Contém HTML/CSS para renderizar um widget de busca
- **Obrigatório exibir** se você mostrar os resultados ao usuário (termos de uso do Google)
- Em APIs internas/backend, pode ser ignorado

#### Modelos Compatíveis
- `gemini-2.5-flash` ✅
- `gemini-2.5-pro` ✅
- `gemini-2.0-flash` ✅
- `gemini-2.0-flash-lite` ✅

---

### 2. URL Context

#### Purpose
Permite que o modelo busque e processe o conteúdo de URLs específicas em tempo real, como anúncios da Shopee, páginas de produto, artigos, ou documentação.

#### Configuration

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Analise este anúncio da Shopee e extraia título, preço e descrição: https://shopee.com.br/product/123/456",
    config=types.GenerateContentConfig(
        tools=[types.Tool(url_context=types.UrlContext())]
    ),
)
```

#### Combinando URL Context com Google Search

```python
config = types.GenerateContentConfig(
    tools=[
        types.Tool(
            url_context=types.UrlContext(),
            google_search=types.GoogleSearch(),
        )
    ]
)
```

#### URL Context Metadata

```python
response = client.models.generate_content(...)

# Acessar metadados de URL Context
metadata = response.candidates[0].grounding_metadata

for chunk in metadata.grounding_chunks:
    if chunk.web:
        print(f"URL processada: {chunk.web.uri}")
        print(f"Título: {chunk.web.title}")
```

#### Limitações Críticas

| Limitação | Detalhe |
|---|---|
| **Vertex AI** | ❌ NÃO suportado — apenas Gemini API direta |
| **robots.txt** | Respeita bloqueios — algumas páginas retornam vazio |
| **JavaScript** | Não renderiza JS — conteúdo dinâmico (SPAs) pode falhar |
| **Máximo de URLs** | ~20 URLs por request |
| **Conteúdo privado** | Não acessa páginas que requerem login/autenticação |
| **Rate limiting** | Cada URL é um fetch real — rate limits se aplicam |
| **Formato** | Funciona melhor com HTML estático, artigos, docs, blogs |

#### Quando NÃO usar URL Context
- Páginas protegidas por login (Shopee Seller Center logado)
- SPAs pesadas em JavaScript (React/Angular sem SSR)
- Conteúdo atrás de paywall
- APIs REST (use `function_declarations` para isso)

#### Quando USAR URL Context
- Anúncios públicos da Shopee (página de produto)
- Artigos de blog sobre tendências
- Documentação técnica
- Páginas de concorrentes
- Resultados de busca pública

---

### 3. Code Execution

#### Purpose
Modelo escreve e executa Python em um sandbox seguro do Google. Útil para cálculos, processamento de dados, e geração de visualizações.

#### Configuration

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Calcule o markup ideal para um vestido com custo de R$45 e preço de venda de R$129",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.CodeExecution())]
    ),
)
```

#### Limitações do Sandbox
- Sem acesso à internet
- Sem acesso ao filesystem
- Bibliotecas limitadas (numpy, pandas, matplotlib disponíveis)
- Timeout de execução
- Sem persistência entre chamadas

---

### 4. Tool Combination (Orquestração Multi-Ferramenta)

Este é o padrão mais poderoso e mais complexo. Permite combinar ferramentas integradas do Google com funções customizadas do seu código.

#### Arquitetura do Loop Agentic

```
┌─────────────────────────────────────────────────┐
│                  SEU CÓDIGO                       │
│                                                   │
│  1. Envia prompt + tools config                  │
│  2. Recebe response                              │
│  3. Verifica se tem function_call pendente       │
│  4. Se sim: executa a função, retorna resultado  │
│  5. Se não: resposta final, encerra              │
│  6. Volta ao passo 2 (loop)                      │
└─────────────────────────────────────────────────┘
         │                    ▲
         ▼                    │
┌─────────────────────────────────────────────────┐
│              GEMINI API (SERVER)                  │
│                                                   │
│  - Executa Google Search (se acionado)           │
│  - Executa URL Context (se acionado)             │
│  - Executa Code Execution (se acionado)          │
│  - Retorna function_call para funções custom     │
│  - Combina resultados de todas as fontes         │
└─────────────────────────────────────────────────┘
```

#### Implementação Completa

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# 1. Defina suas funções customizadas
def get_product_data(product_id: str) -> dict:
    """Busca dados internos de um produto no banco."""
    # Sua lógica de banco de dados aqui
    return {"name": "Vestido Floral", "cost": 45.00, "price": 129.90}

def calculate_margin(cost: float, price: float) -> dict:
    """Calcula margem de lucro."""
    margin = ((price - cost) / price) * 100
    return {"margin_percent": round(margin, 2)}

# 2. Declare as funções para o modelo
custom_functions = [
    types.FunctionDeclaration(
        name="get_product_data",
        description="Busca dados internos de um produto pelo ID",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "product_id": types.Schema(type="STRING", description="ID do produto")
            },
            required=["product_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="calculate_margin",
        description="Calcula a margem de lucro de um produto",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "cost": types.Schema(type="NUMBER", description="Custo do produto"),
                "price": types.Schema(type="NUMBER", description="Preço de venda"),
            },
            required=["cost", "price"],
        ),
    ),
]

# 3. Configure ferramentas integradas + custom
tools = [
    # Ferramentas integradas (Google executa no server)
    types.Tool(
        google_search=types.GoogleSearch(),
        url_context=types.UrlContext(),
    ),
    # Funções customizadas (VOCÊ executa no client)
    types.Tool(function_declarations=custom_functions),
]

# 4. Mapeie os nomes para as funções reais
function_map = {
    "get_product_data": get_product_data,
    "calculate_margin": calculate_margin,
}

# 5. Loop agentic
contents = [
    types.Content(
        role="user",
        parts=[types.Part(text="Analise o produto ID 'SKU-1234' e compare o preço com concorrentes na Shopee")],
    )
]

config = types.GenerateContentConfig(
    tools=tools,
    # IMPORTANTE: desabilitar auto-calling quando mistura integradas + custom
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)

MAX_ITERATIONS = 10

for i in range(MAX_ITERATIONS):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    )

    # Verificar se há function_calls pendentes
    function_calls = [
        part.function_call
        for part in response.candidates[0].content.parts
        if part.function_call
    ]

    if not function_calls:
        # Sem function calls = resposta final
        break

    # Adicionar a resposta do modelo ao histórico
    contents.append(response.candidates[0].content)

    # Executar cada function call
    function_responses = []
    for fc in function_calls:
        if fc.name in function_map:
            # Função customizada — executar localmente
            result = function_map[fc.name](**fc.args)
            function_responses.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response=result,
                    )
                )
            )
        # Nota: funções integradas (google_search, url_context)
        # são executadas pelo servidor automaticamente.
        # Seus resultados já estão na response.

    # Retornar resultados ao modelo
    if function_responses:
        contents.append(
            types.Content(role="user", parts=function_responses)
        )

# Resposta final
final_text = response.candidates[0].content.parts[0].text
print(final_text)

# Metadados de grounding (se usou Google Search ou URL Context)
if response.candidates[0].grounding_metadata:
    metadata = response.candidates[0].grounding_metadata
    for chunk in metadata.grounding_chunks:
        print(f"Fonte: {chunk.web.uri}")
```

#### Regras Críticas da Combinação

1. **SEMPRE desabilite `automatic_function_calling`** quando misturar ferramentas integradas com custom
2. **Ferramentas integradas e custom devem estar em objetos `Tool` SEPARADOS** na lista `tools`
3. **O servidor executa ferramentas integradas automaticamente** — você NÃO recebe `function_call` para elas
4. **Você SÓ recebe `function_call` para funções custom** — execute e retorne o resultado
5. **Mantenha o histórico completo** (`contents`) para preservar o contexto multi-turn
6. **Limite o loop** (`MAX_ITERATIONS`) para evitar loops infinitos
7. **Trate erros nas funções custom** — retorne mensagem de erro clara, não crashe o loop

---

## Padrões de Implementação para MEDIA-SHOPEE

### Padrão 1: Pesquisa de Mercado com Google Search

Caso de uso: antes de gerar um prompt de foto, consultar tendências atuais.

```python
def generate_with_market_context(product_description: str, category: str) -> str:
    """Gera prompt de foto com contexto de mercado atual."""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
        Você é especialista em fotografia de moda para e-commerce brasileiro.
        
        Primeiro, pesquise no Google as tendências atuais de {category} 
        na Shopee Brasil e identifique:
        - Estilos de foto que estão vendendo mais
        - Poses mais usadas
        - Cenários populares
        
        Depois, gere um prompt de foto otimizado para este produto:
        {product_description}
        
        O prompt deve seguir as tendências encontradas.
        """,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    
    return response.text
```

### Padrão 2: Análise de Concorrência com URL Context

Caso de uso: analisar um anúncio concorrente da Shopee para gerar fotos melhores.

```python
def analyze_competitor(competitor_url: str, our_product: str) -> str:
    """Analisa anúncio concorrente e sugere melhorias."""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
        Analise este anúncio concorrente da Shopee:
        {competitor_url}
        
        Extraia:
        1. Estilo das fotos (fundo, iluminação, modelo)
        2. Pontos fortes do anúncio
        3. Pontos fracos
        
        Depois, gere 3 prompts de foto para o nosso produto que sejam 
        MELHORES que o concorrente:
        Nosso produto: {our_product}
        """,
        config=types.GenerateContentConfig(
            tools=[types.Tool(url_context=types.UrlContext())],
        ),
    )
    
    return response.text
```

### Padrão 3: Pipeline Completo (Search + URL + Custom Functions)

Caso de uso: fluxo completo de pesquisa, análise e geração.

```python
async def full_research_pipeline(product_id: str):
    """Pipeline completo: dados internos + web + análise."""
    
    # System instruction que orienta o modelo sobre quando usar cada ferramenta
    system_instruction = """
    Você é um agente de inteligência de mercado para e-commerce de moda.
    
    Ferramentas disponíveis:
    - Google Search: use para pesquisar tendências, preços de mercado, e novidades
    - URL Context: use quando receber uma URL específica para analisar
    - get_product_data: use para buscar dados internos de produtos
    - calculate_margin: use para calcular margens de lucro
    
    Processo:
    1. Busque os dados internos do produto
    2. Pesquise no Google os preços de produtos similares na Shopee
    3. Calcule se nossa margem está competitiva
    4. Sugira ajustes de preço e estratégia de fotos
    """
    
    # ... implementação do loop agentic conforme seção 4
```

---

## Troubleshooting

### URL Context retorna vazio
- **Causa 1**: `robots.txt` bloqueia o crawler do Google → tente outra URL
- **Causa 2**: Página é SPA (JavaScript-rendered) → use `function_declarations` + seu próprio scraper
- **Causa 3**: Página requer autenticação → não é possível com URL Context

### Google Search não é acionado
- **Causa 1**: Threshold muito alto → diminua `dynamic_threshold`
- **Causa 2**: O modelo considera que já sabe a resposta → force com instrução explícita no prompt: *"Pesquise no Google antes de responder"*
- **Causa 3**: Modelo incompatível → verifique se está usando `gemini-2.0-flash` ou superior

### Function calls em loop infinito
- **Causa**: Modelo não tem informação suficiente para parar → adicione `MAX_ITERATIONS` e retorne resposta parcial
- **Prevenção**: System instruction deve dizer explicitamente quando parar de chamar ferramentas

### Erro ao combinar ferramentas
- **Causa**: Ferramentas integradas e custom no MESMO objeto `Tool` → separe em objetos diferentes
- **Causa**: `automatic_function_calling` habilitado com ferramentas integradas → desabilite

### grounding_metadata ausente
- **Causa**: O modelo decidiu não usar grounding (threshold alto ou não necessário)
- **Verificação**: `response.candidates[0].grounding_metadata` pode ser `None` — sempre verifique antes de acessar

---

## Compatibilidade

| Ferramenta | Gemini API | Vertex AI | AI Studio |
|---|---|---|---|
| Google Search | ✅ | ✅ | ✅ |
| URL Context | ✅ | ❌ | ✅ |
| Code Execution | ✅ | ✅ | ✅ |
| Tool Combination | ✅ | Parcial | ✅ |

---

## Checklist de Implementação

Antes de deployar qualquer feature de grounding:

- [ ] Está usando `google-genai` SDK (não `google-generativeai` legado)?
- [ ] API key está em variável de ambiente, NÃO hardcoded?
- [ ] Definiu `MAX_ITERATIONS` para loops agentic?
- [ ] Desabilitou `automatic_function_calling` ao combinar ferramentas?
- [ ] Ferramentas integradas e custom estão em objetos `Tool` separados?
- [ ] Tratou `grounding_metadata` como nullable?
- [ ] Tratou erros de network/timeout nas funções custom?
- [ ] URL Context NÃO está sendo usado via Vertex AI?
- [ ] Verificou se as URLs alvo não bloqueiam via `robots.txt`?
- [ ] System instruction explica quando cada ferramenta deve ser usada?

---

## Referências Oficiais

- [Google Search Grounding](https://ai.google.dev/gemini-api/docs/google-search)
- [URL Context](https://ai.google.dev/gemini-api/docs/url-context)
- [Code Execution](https://ai.google.dev/gemini-api/docs/code-execution)
- [Tool Use Overview](https://ai.google.dev/gemini-api/docs/function-calling)
- [Agentic Tools](https://ai.google.dev/gemini-api/docs/agentic)
