# API Discoveries & Project Learnings

Registro persistente de erros corrigidos, comportamentos descobertos e boas práticas identificadas no uso real das APIs e ferramentas do projeto.

Atualizado via comando `/train` ao final de cada sessão relevante.

---

## Índice rápido

| Data | Categoria | Severidade | Resumo |
|---|---|---|---|
| 2026-03-07 | `api` | 🔴 | Thinking level MEDIUM não existe no modelo de imagem |
| 2026-03-07 | `api` | 🔴 | Model name errado — gemini-3.1-flash não existe |
| 2026-03-07 | `api` | 🟡 | Billing obrigatório para modelos de imagem Nano Banana 2 |
| 2026-03-07 | `api` | 🟡 | Flash retorna JSON com markdown — parser precisa de regex |
| 2026-03-07 | `api` | 🟢 | Safety BLOCK_NONE confirmado: lingerie/catálogo sem bloqueio |

---

## Aprendizados detalhados

---

### [2026-03-07] Thinking level MEDIUM não existe no Nano Banana 2 (modelo de imagem)

**Categoria:** `api`
**Modelo afetado:** `gemini-3.1-flash-image-preview` (Nano Banana 2)
**Severidade:** 🔴 Crítico (causa erro imediato)

**Contexto:** Ao testar o pipeline de geração de lingerie com `thinking_level="MEDIUM"`.

**Problema:**
```
400 INVALID_ARGUMENT: Thinking level MEDIUM is not supported for this model.
Please retry with other thinking level.
```

A documentação do Google AI Studio menciona três níveis (HIGH, MEDIUM, MINIMAL), mas o **modelo de imagem** `gemini-3.1-flash-image-preview` só aceita dois:
- `"MINIMAL"` — rápido, sem raciocínio profundo
- `"HIGH"` — raciocínio completo, para texturas complexas, texto em imagem, multi-elemento

**Solução:** Substituir `"MEDIUM"` por `"HIGH"` ou `"MINIMAL"` sempre que o modelo for de imagem.

**Regra para sessões futuras:**
> Para o Nano Banana 2 (e qualquer modelo `*-image-preview`): use apenas `MINIMAL` ou `HIGH`.  
> O Gemini Flash de **texto** aceita todos os níveis.

---

### [2026-03-07] Nome do modelo gemini-3.1-flash não existe

**Categoria:** `api`
**Modelo afetado:** `gemini-3.1-flash` (nome inexistente)
**Severidade:** 🔴 Crítico (causa erro 404)

**Contexto:** Ao chamar o Gemini Flash para texto no `test_flash.py`.

**Problema:**
```
404 NOT_FOUND: models/gemini-3.1-flash is not found for API version v1beta
```

**Solução:** Usar `"gemini-3-flash-preview"` (sem o ponto 3.1 no nome de texto).

**Mapa de nomes corretos confirmados em produção (Mar/2026):**
| Nome documentado | Nome real na API |
|---|---|
| Gemini 3.1 Flash (texto) | `gemini-3-flash-preview` |
| Nano Banana 2 (imagem) | `gemini-3.1-flash-image-preview` |
| Nano Banana Pro (imagem) | `gemini-3-pro-image-preview` ou `nano-banana-pro-preview` |

**Como verificar modelos disponíveis na key:**
```python
client = genai.Client(api_key=api_key)
for m in client.models.list():
    print(m.name)
```

---

### [2026-03-07] Billing obrigatório para gemini-3.1-flash-image-preview

**Categoria:** `api`
**Modelo afetado:** `gemini-3.1-flash-image-preview`
**Severidade:** 🟡 Importante (bloqueia uso sem billing)

**Contexto:** Primeiras chamadas ao Nano Banana 2 após configurar a chave de API.

**Problema:**
```
429 RESOURCE_EXHAUSTED: limit: 0, model: gemini-3.1-flash-image
```
O `limit: 0` é permanente no free tier — não é cota esgotada, é ausência de cota.

**Solução:** Ativar billing no Google AI Studio → aguardar ~2 min de propagação → testar novamente.

**Nota:** O modelo de texto (`gemini-3-flash-preview`) funciona no free tier. O modelo de imagem exige billing ativado.

---

### [2026-03-07] Flash retorna JSON com markdown — parser precisa ser robusto

**Categoria:** `api`
**Modelo afetado:** `gemini-3-flash-preview`
**Severidade:** 🟡 Importante (causa json.JSONDecodeError em produção)

**Contexto:** O Prompt Agent pede ao Flash que retorne JSON puro, mas ele às vezes encapsula em markdown ou trunca strings.

**Problema:**
```
json.JSONDecodeError: Unterminated string starting at: line 6 column 3 (char 747)
```

**Solução:** Parser com fallback em regex:
```python
import re, json

raw = response.text.strip()

# Caso 1: veio com ```json ... ```
if "```" in raw:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        raw = match.group(1)
    else:
        match2 = re.search(r"\{.*\}", raw, re.DOTALL)
        if match2:
            raw = match2.group(0)
# Caso 2: veio com texto antes do JSON
elif not raw.startswith("{"):
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)

resultado = json.loads(raw)
```

**Regra para sessões futuras:** Nunca usar `json.loads(response.text)` diretamente — sempre aplicar o parser robusto acima.


### [2026-03-07] Safety BLOCK_NONE confirmado para catálogo de lingerie

**Categoria:** `api`
**Modelo afetado:** `gemini-3.1-flash-image-preview`
**Severidade:** 🟢 Dica (confirma configuração correta)

**Contexto:** Teste de geração de catálogo de lingerie com modelo curvilíneo.

**Resultado:** Imagem gerada sem nenhum bloqueio com:
```python
SAFETY_CONFIG = [
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",         threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",        threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",  threshold="BLOCK_NONE"),
]
```

**Regra para sessões futuras:** Sempre incluir `SAFETY_CONFIG` com `BLOCK_NONE` nas chamadas ao Nano Banana 2. Sem isso, prompts de moda íntima, biquínis, decotes e costas expostas podem ser bloqueados por falsos positivos.

---

*Próxima entrada: adicionar via `/train` na próxima sessão.*

