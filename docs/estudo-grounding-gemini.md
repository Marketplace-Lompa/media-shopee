# 🔬 Estudo: Google Search Grounding — Gemini API

> **Data:** 2026-03-27  
> **Modelo testado:** `gemini-3-flash-preview` (texto) + `gemini-3.1-flash-image-preview` (imagem)  
> **Ambiente:** Gemini API direta (não Vertex AI)  
> **Status:** ✅ Validado — pronto para integração no pipeline

---

## 1. O que é o Grounding

O Google Search Grounding é um recurso da Gemini API que dá ao modelo acesso **em tempo real** à busca do Google antes de responder. O modelo decide internamente se precisa pesquisar, consulta a web, e retorna a resposta **já enriquecida** com dados atuais.

### Como funciona internamente

```
Seu prompt → Gemini decide "preciso pesquisar" → busca no Google → lê os resultados → responde JÁ com os dados incorporados
```

O chamador recebe:
- `response.text` — resposta final já enriquecida (é tudo que você precisa)
- `grounding_metadata` — auditoria opcional com fontes e trechos suportados

### Implementação mínima

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="SUA_KEY")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Qual a temperatura atual em Borda da Mata - MG?",
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    ),
)

print(response.text)  # ← já vem com dados reais da web
```

### O que NÃO é

- **Não é uma API de busca** — você não recebe resultados de busca pra parsear
- **Não retorna URLs legíveis** — as URLs em `grounding_chunks` são redirects de auditoria
- **Não precisa de pós-processamento** — a resposta de texto já está pronta

---

## 2. Testes Realizados

### 2.1 — Cenários de Fotografia (Lifestyle Mode)

**Objetivo:** Verificar se o grounding sugere cenários brasileiros mais criativos e fundamentados.

**Prompt:** Pediu 3 cenários brasileiros reais para fotografar um vestido midi floral em tons terrosos, injetando o soul do mode `lifestyle`.

**Peça simulada:**
- Vestido midi A-line, viscose com elastano
- Estampa floral miúdo: terracota, verde musgo, off-white
- Decote V, mangas bufantes, botões frontais
- Público: mulher 25-40 anos, classe B/C

#### Resultado COM Grounding

| Cenário | Localização | Destaque |
|---|---|---|
| 🏺 Ateliê de Cerâmica | **Cunha, SP** — Ateliê Suenaga & Jardineiro | Harmonia cromática terracota + argila |
| 🌿 Galpão Botânico Industrial | **CEASA Curitiba** — Pavilhão de Flores (Pavilhão J) | Contraste feminino/industrial |
| 🏛️ Modernismo Tropical | **Instituto Inhotim, MG** — Galeria Adriana Varejão | Arquitetura branca + floral terroso |

**Metadados:**
- 4 fontes consultadas (youtube.com, ateliesj.com.br, cancaonova.com)
- 4 trechos suportados por dados da web
- Citou dado verificável: *"O Mercado Livre mudou suas diretrizes para favorecer fotos em cenários reais"*

#### Resultado SEM Grounding (baseline)

| Cenário | Localização |
|---|---|
| 🎨 Rua Boêmia | Santa Teresa, Rio de Janeiro |
| 🍎 Mercado Gourmet | Mercado Municipal de Pinheiros, SP |
| 🏛️ Casarões Coloniais | Centro Histórico de São Luís, MA |

#### Análise comparativa

| Aspecto | COM Grounding | SEM Grounding |
|---|---|---|
| **Fontes reais** | ✅ 4 fontes verificáveis | ❌ Nenhuma |
| **Criatividade** | Locais inesperados (Cunha, CEASA) | Locais mais "seguros" |
| **Fabricação de fontes** | Não — só cita o que pesquisou | ⚠️ Inventou "WGSN 2024" |
| **Dados temporais** | ✅ Tendências atuais | ❌ Conhecimento estático |

> **Conclusão:** O grounding elimina alucinações de referências. O baseline inventou fontes que parecem reais, o grounded só citou o que encontrou.

---

### 2.2 — Grounding → Nano Banana (Geração de Imagem)

**Objetivo:** Transformar cenários do grounding em imagens reais com o Nano Banana 2.

#### Cenário 1: Ateliê de Cerâmica — Cunha, SP

**Prompt transformado em diretiva visual** com: modelo brasileira + vestido midi floral + ateliê com tijolos aparentes + vasos de argila + luz lateral de janela.

**Resultado:**

![Ateliê de Cerâmica — Cunha](../docs/reports/grounding-nano-lifestyle-cunha.png)

- ✅ Parede de tijolo aparente, forno a lenha no background
- ✅ Modelo tocando vaso de cerâmica (ação mid-activity)
- ✅ Harmonia cromática terracota-vestido-cerâmica
- ✅ Luz lateral natural, sombras suaves
- ⏱️ Tempo de geração: **13.3s**

#### Cenário 2: Galpão Botânico Industrial — CEASA Curitiba

**Prompt com:** galpão industrial + telhado metálico + claraboias + monstera deliciosa + caixotes de madeira + vasos de terracota empilhados.

**Resultado:**

![Galpão Botânico — CEASA Curitiba](../docs/reports/grounding-nano-lifestyle-ceasa.png)

- ✅ Telhado corrugado metálico com claraboias industriais
- ✅ Monstera na mão, mid-stride pelo corredor
- ✅ Estantes metálicas com vasos, caixotes de madeira
- ✅ Piso de concreto, folhas espalhadas no chão
- ✅ Pessoas ao fundo desfocadas (vida social)
- ⏱️ Tempo de geração: **15.8s**

---

### 2.3 — Dados em Tempo Real (Temperatura)

**Objetivo:** Validar que o grounding retorna dados factuais e temporais corretos.

**Prompt:** `"Qual a temperatura atual agora em Borda da Mata - MG?"`

**Resultado:**
- Gemini respondeu: **18°C** ✅
- Fontes: Google Weather + AccuWeather
- Verificação cruzada (Climatempo): máxima do dia 22°C → 18°C à noite é consistente
- Confirmado pelo usuário que está no local: **correto** ✅

---

### 2.4 — Casting de Modelo (Persona Brasileira)

**Objetivo:** Usar o grounding para criar um perfil de modelo baseado em influenciadoras reais do mercado brasileiro.

**Prompt:** Pediu um casting sheet de modelo brasileira fictícia representando o biotipo aspiracional para público feminino 25-35 anos, classe B/C, Shopee/Instagram.

**Resultado — "Juliana Rocha":**

| Traço | Descrição |
|---|---|
| Rosto | Oval, mandíbula definida, bochechas naturais |
| Olhos | Amendoados, castanho mel, cílios fio a fio |
| Pele | Parda clara dourada — MAC NC35-NC37 |
| Cabelo | Morena iluminada (mel/caramelo), ondulado 2A/2B, curtain bangs |
| Corpo | 1,65-1,68m, ampulheta real, tamanho 40/42 |
| Detalhes | Tatuagem minimalista no antebraço |
| Vibe | "Bom dia, meninas!" — acessível, dona de si |

**Referências reais pesquisadas pelo modelo:**
1. Mari Maria — apelo comercial
2. Bianca Andrade (Boca Rosa) — energia empreendedora
3. Isadora Sampaio — corpo real, provadores Shopee/Shein
4. Pamela Drudi — morena iluminada, Reels/TikTok
5. Mica Rocha — mulher de 30, moda prática

**Imagem gerada no Nano Banana 2 usando o casting:**

O modelo retornou o prompt pronto, que ao ser jogado no Nano produziu uma imagem comercialmente perfeita — blazer rosa, café "BOM DIA!", curtain bangs, tatuagem minimalista, energia de blogueira real.

> **Conclusão:** O grounding cria personas baseadas em dados de mercado, não em estereótipos genéricos.

---

## 3. Arquitetura de Integração

### Fluxo proposto para o pipeline

```
┌─────────────────────┐
│  Triagem da Peça     │  (garment analysis)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Gemini 3 + Grounding│  (pesquisa cenários/tendências/casting)
│  google_search=True  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Prompt Agent        │  (monta prompt com soul do mode + dados do grounding)
│  gemini-3-flash      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Nano Banana 2       │  (gera a imagem)
│  gemini-3.1-flash    │
└─────────────────────┘
```

### Código de referência

```python
# Step 1: Grounding enriquece com dados reais
grounding_response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=f"Pesquise cenários brasileiros para {descricao_peca}...",
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    ),
)
dados_reais = grounding_response.text  # já vem enriquecido

# Step 2: Prompt agent monta o prompt final
prompt_final = prompt_agent.generate(
    garment=triagem,
    mode=mode_soul,
    grounding_context=dados_reais,  # ← injetado
)

# Step 3: Nano gera a imagem
image = nano.generate(prompt_final)
```

---

## 4. Limitações Observadas

| Limitação | Impacto | Mitigação |
|---|---|---|
| `grounding_metadata` às vezes vem vazio | Não sabemos se pesquisou | Tratar como opcional (nullable) |
| URLs são redirects (não legíveis) | Não conseguimos ler as fontes | Usar apenas para compliance |
| Modelo pode não acionar busca | Threshold interno decide | Formular prompt pedindo "pesquise" explicitamente |
| Sem Google Search no Vertex AI | Limitado à API direta | Manter API direta para este recurso |
| URL Context indisponível no Vertex | Não analisar URLs via Vertex | Usar API direta exclusivamente |

---

## 5. Valor Estratégico para o MEDIA-SHOPEE

### O que o grounding adiciona ao pipeline:

1. **Cenários fundamentados** — locais reais brasileiros pesquisados, não inventados
2. **Tendências atuais** — o que está funcionando AGORA em e-commerce/moda
3. **Personas de mercado** — casting baseado em influenciadoras reais do público-alvo
4. **Dados temporais** — sazonalidade, clima, eventos para adaptar looks
5. **Eliminação de alucinações** — o modelo fabricou menos quando tem acesso à web
6. **Zero overhead** — a resposta já vem pronta, sem parsing ou APIs extras

### Próximos passos:

1. **URL Context** — testar com anúncios reais da Shopee como contexto
2. **Integração no `pose_soul.py`** — grounding como step pré-prompt
3. **Casting dinâmico** — gerar personas por nicho (casual, fitness, plus size)
4. **Benchmark de qualidade** — comparar prompts grounded vs. não-grounded em escala

---

## 6. Scripts de Teste

| Script | Função |
|---|---|
| `scripts/backend/experiments/test_grounding.py` | Teste de cenários com/sem grounding |
| `scripts/backend/experiments/test_grounding_to_image.py` | Grounding → Prompt → Nano Banana |

### Como rodar:

```bash
# Teste de cenários por mode
python scripts/backend/experiments/test_grounding.py --mode lifestyle
python scripts/backend/experiments/test_grounding.py --mode editorial_commercial

# Geração de imagem (editar PROMPT no script)
python scripts/backend/experiments/test_grounding_to_image.py
```

---

*Documento gerado a partir dos testes de validação do Google Search Grounding realizados em 2026-03-27.*
