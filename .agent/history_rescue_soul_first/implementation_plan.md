# Integração do Grounding Casting no Pipeline model_soul

## Objetivo

Integrar o fluxo de **casting com grounding** (pesquisa de influenciadoras/mercado reais) dentro do pipeline existente de `model_soul.py`, para que o agente gere descrições de modelo baseadas em dados reais de mercado — sem alterar a arquitetura core do prompt assembly.

## Contexto

### O que temos hoje
O `model_soul.py` entrega diretivas textuais **instrucionais** ao agente — ele DIZ ao agente "invente uma mulher brasileira com rosto X, cabelo Y, corpo Z". O agente então interpreta essas instruções e gera a descrição da modelo no prompt final.

### O que queremos
Adicionar uma **camada de enriquecimento via grounding** que pesquisa influenciadoras/blogueiras brasileiras reais do público-alvo antes do agente gerar a modelo. O grounding informa ao agente sobre tendências de biotipo, estilo, vibe e energia que performam melhor no mercado — fazendo o casting ser **strategy-driven**, não apenas aleatório.

### Decisão de design: Enrichment Layer, não Replacement

> [!IMPORTANT]
> O grounding atua como **contexto adicional** injetado ANTES do model_soul, não como substituto dele. O model_soul continua sendo a diretiva principal, mas agora recebe um "briefing de mercado" que orienta as decisões do agente.

## Fluxo Proposto

```
┌─────────────────────┐
│  Triagem da Peça     │  garment_hint = "vestido midi floral terracota"
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Grounding Casting    │  Gemini 3 + Google Search
│  (NOVA CAMADA)       │  → pesquisa influenciadoras, biotipos, tendências
│                      │  → retorna casting_context enrichment text
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  model_soul.py       │  Recebe casting_context como novo parâmetro
│  (ALTERADO)          │  → injeta bloco <GROUNDING_CASTING> no soul
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  prompt_context.py   │  Monta o contexto completo (sem mudanças no assembly)
│  (MÍNIMA ALTERAÇÃO)  │
└─────────────────────┘
```

## Propostas de Alteração

---

### 1. Novo módulo: `grounding_casting.py`

> [!IMPORTANT]
> **Módulo separado** para não contaminar o `grounding.py` atual (focado em garment classification). Este é especificamente para **casting de modelo**.

#### [NEW] [grounding_casting.py](file:///Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/grounding_casting.py)

Função principal: `run_casting_grounding(garment_hint, mode_id) -> str`

- Monta um prompt de casting director adaptado ao `mode_id`
- Usa `gemini-3-flash-preview` com `GoogleSearch()` tool
- Retorna texto enriquecido com casting context (biotipo, referências, energia)
- Tem timeout + fallback (se grounding falhar, retorna string vazia e o model_soul funciona como antes)

**Prompts por mode:**

| Mode | Foco do Grounding |
|---|---|
| `natural` | Mulheres reais, corpo cotidiano, energia approachable, sem produção |
| `lifestyle` | Influenciadoras Shopee/Instagram, morena iluminada, energia "bom dia meninas" |
| `editorial_commercial` | Modelos editoriais brasileiras, presença forte, jawline, commanding energy |
| `catalog_clean` | Skip grounding — catalog não precisa de persona, foco na peça |

---

### 2. Alteração: `model_soul.py`

#### [MODIFY] [model_soul.py](file:///Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/model_soul.py)

- Adicionar parâmetro `casting_context: str = ""` em `get_model_soul()`
- Quando `casting_context` não está vazio, injetar bloco `MARKET-INFORMED CASTING` entre o `garment_casting_block` e as regras de `MANDATORY PHYSICAL DETAIL`
- O bloco orienta o agente a usar os dados de mercado para guiar decisões de rosto, cabelo, corpo e vibe — sem ser prescritivo

```python
# Bloco novo injetado quando casting_context está disponível
grounding_casting_block = ""
if casting_context:
    grounding_casting_block = (
        "\n"
        "📊 MARKET-INFORMED CASTING (grounding data from real market research):\n"
        f"  {casting_context}\n"
        "  Use this market intelligence to INFORM your casting decisions — let the real-world data\n"
        "  guide which physical traits, hair style, body type, and energy will resonate most with\n"
        "  the target audience. But still INVENT a unique individual, do not copy any real person.\n"
        "\n"
    )
```

---

### 3. Alteração: `prompt_context.py`

#### [MODIFY] [prompt_context.py](file:///Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/prompt_context.py)

- Na função `_build_model_soul_block()`, chamar `run_casting_grounding()` e passar o resultado como `casting_context` para `get_model_soul()`
- Adicionar parâmetro `mode_id` que já existe no call site

---

### 4. Alteração: `generation_flow.py`

#### [MODIFY] [generation_flow.py](file:///Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/agent_runtime/generation_flow.py)

- Nenhuma alteração de interface — o `casting_context` é resolvido internamente no `_build_model_soul_block`. O `generation_flow` já passa `garment_hint` e `mode_id` que são suficientes.

---

## User Review Required

> [!WARNING]
> **Performance:** O grounding adiciona **~3-8s de latência** por geração (chamada extra ao Gemini 3 com Google Search). Isso é aceitável?

> [!IMPORTANT]
> **Custo:** Cada geração fará uma chamada extra ao Gemini 3 Flash Preview. Em volume, isso pode impactar o custo da API. O grounding deve rodar **sempre** ou apenas quando habilitado por flag?

> [!NOTE]
> **Catalog mode:** Proponho **skip do grounding** para `catalog_clean` pois o foco é a peça, não a modelo. Concordas?

## Open Questions

1. **Flag de controle:** O grounding casting deve ser `always-on` para natural/lifestyle/editorial, ou controlado por uma env var tipo `ENABLE_GROUNDING_CASTING=true`?
2. **Cache:** Devemos cachear o resultado do grounding por `garment_hint` para evitar chamadas repetidas quando geramos múltiplas imagens da mesma peça?
3. **Latência aceitável:** Os 3-8s extras são OK para o UX do Studio?

## Verificação

### Testes automatizados
```bash
# Teste unitário do grounding_casting
python -c "from agent_runtime.grounding_casting import run_casting_grounding; print(run_casting_grounding('vestido midi floral terracota', 'lifestyle'))"

# Teste do model_soul com casting_context
python -c "from agent_runtime.model_soul import get_model_soul; print(get_model_soul(garment_context='vestido midi', mode_id='lifestyle', casting_context='morena iluminada, corpo ampulheta...'))"
```

### Validação visual
- Gerar 3 imagens com grounding ON vs 3 com OFF para o mesmo garment/mode
- Comparar qualidade do casting (diversidade, adequação ao público, realismo)
