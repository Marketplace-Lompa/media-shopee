# Agent & Pipeline Learnings

Bugs, correções e padrões do pipeline de geração: agent.py → generator.py → routers/generate.py → frontend.

---

## Índice rápido

| Data | Severidade | Resumo |
|---|---|---|
| 2026-03-07 | 🔴 | GeneratedImage sem campo url → imagens pretas no frontend |
| 2026-03-07 | 🔴 | Ternário Python engole MODE 2 → Fidelity Lock não dispara |
| 2026-03-07 | 🟡 | Uploaded images não chegavam ao Nano → envio casado necessário |

---

## Aprendizados detalhados

---

### [2026-03-07] GeneratedImage sem campo url → imagens pretas no frontend

**Severidade:** 🔴 Crítico (imagens ficam totalmente pretas na gallery)

**Contexto:** Frontend usa `img.url` para renderizar imagens geradas na gallery.

**Problema:** O `generator.py` retornava `filename`, `path`, `size_kb`, `mime_type` mas **não** gerava o campo `url`. O `GeneratedImage` em `models.py` também não declarava `url`. O frontend renderizava `<img src="undefined">` → tela preta.

**Solução:**
1. `generator.py`: adicionar `"url": f"/outputs/{session_id}/{filename}"` no dict de resultado
2. `models.py`: adicionar `url: str` no `GeneratedImage`

**Regra:**
> Todo campo consumido pelo frontend deve existir explicitamente no model Pydantic E ser populado pelo backend. Nunca assumir que o frontend "calcula" a URL.

---

### [2026-03-07] Ternário Python engole MODE 2 → Fidelity Lock não dispara

**Severidade:** 🔴 Crítico (agente ignora imagens de referência e inventa prompt genérico)

**Contexto:** Usuário envia imagens sem digitar texto. O agente deveria entrar em MODE 2 (Fidelity Lock), mas inventava uma roupa completamente diferente.

**Problema:** Precedência do ternário Python:
```python
# BUGADO — o ternário é pai de toda a expressão
mode_info = (
    f"MODE 2 — ..." 
    "Apply Fidelity Lock..." 
    f'"{user_prompt}"' if has_prompt else "No additional text."
)
# Quando has_prompt=False: mode_info = "No additional text." (perdeu MODE 2 inteiro!)
```

**Solução:** Separar o ternário em variável:
```python
extra_text = f'User text: "{user_prompt}".' if has_prompt else "No additional text from user."
mode_info = (
    f"MODE 2 — User sent {len(uploaded_images)} reference image(s). "
    f"MANDATORY: Apply Fidelity Lock as the FIRST paragraph of the prompt. "
    f"{extra_text}"
)
```

**Regra:**
> NUNCA usar ternário inline em f-strings multi-linha concatenadas. A precedência do `if/else` em Python é mais baixa que a concatenação implícita de strings. Sempre extrair para variável separada.

---

### [2026-03-07] Uploaded images não chegavam ao Nano → envio casado necessário

**Severidade:** 🟡 Importante (Nano gera sem referência visual do produto)

**Contexto:** Usuário sobe imagens de referência da roupa. O agente (Gemini Flash texto) recebia as imagens para análise, mas o Nano (gerador de imagem) não.

**Problema:** `generate_images()` só aceitava `pool_images`. As `uploaded_bytes` ficavam no router e nunca eram passadas ao gerador.

**Solução:**
1. `generator.py`: adicionar parâmetro `uploaded_images: Optional[List[bytes]]`
2. Ordem de envio casado: **pool refs → uploaded refs → prompt textual** (imagens primeiro, texto por último = peso máximo no prompt)
3. `routers/generate.py`: passar `uploaded_bytes` no call a `generate_images()`

**Regra:**
> Qualquer input que o agente analisa também deve chegar ao gerador. Pipeline simétrico: agente vê = gerador vê.

---

*Próxima entrada: adicionar via `/train` na próxima sessão.*
