# Modo Edição Pontual — /alterar

## Problema
Não existe forma de editar uma imagem gerada. O usuário precisa re-gerar do zero mesmo quando quer apenas trocar o fundo, ajustar iluminação ou pequenos detalhes.

## Objetivo
Adicionar botão "✏️ Modificar" no lightbox que ativa um **modo /alterar** no chat. Tudo que o usuário escreve nesse modo é tratado como instrução de edição pontual. O agente refina a instrução com cláusulas de preservação e envia ao Nano Banana 2 junto com a imagem original.

---

## Fluxo UX

```
1. Usuário abre lightbox de uma imagem existente
2. Clica "✏️ Modificar"
   → Lightbox fecha
   → ChatInput entra em modo /alterar com banner:
     ┌─────────────────────────────────────────┐
     │ ✏️ Editando #a3b8d1b6 · gen_a3_1.png    │
     │ [thumbnail 40px]  [× Cancelar]          │
     └─────────────────────────────────────────┘
3. Usuário digita instrução: "Troque o fundo para praia ao pôr do sol"
4. Pipeline de edição:
   a. Edit Agent otimiza prompt (preservação + tradução)
   b. Nano Banana 2 recebe [imagem original + prompt refinado]
   c. Resultado aparece na Gallery como nova geração
5. Usuário pode:
   - Aceitar → salva no histórico
   - Editar novamente → fica no modo /alterar
   - Cancelar → volta ao modo normal
```

---

## Proposta de Mudanças

### Frontend

---

#### [MODIFY] `types/index.ts` — Novo estado de edição

Adicionar tipo para o modo de edição:

```ts
export interface EditTarget {
  session_id: string;
  filename: string;
  url: string;            // URL da imagem a editar
  prompt?: string;        // prompt original (para contexto do agente)
  aspect_ratio?: string;  // herda do original
  resolution?: string;    // herda do original
}
```

Adicionar novo status ao `GenerationStatus`:

```ts
| { type: 'editing'; message: string }  // pipeline de edição ativo
```

---

#### [MODIFY] `App.tsx` — State de edição + handler

Novo state:
```ts
const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
```

Novo handler `handleEdit(instruction: string)`:
- Faz `POST /edit/stream` com `{ source_url, edit_instruction }`
- Lê SSE da mesma forma que `handleGenerate`
- Quando `done`, atualiza histórico e limpa `editTarget`

Lightbox: adicionar botão "Modificar" que seta `editTarget` e fecha o lightbox.

---

#### [MODIFY] `ChatInput.tsx` — Modo /alterar visual

Receber nova prop `editTarget: EditTarget | null` e `onCancelEdit: () => void`.

Quando `editTarget` ativo:
- Mostrar banner fixo no topo do input com thumbnail + filename + botão cancelar
- Placeholder do textarea muda para: "Descreva a alteração desejada…"
- Botão de envio muda ícone para ✏️ (Edit) ao invés de Send
- Hiding dos paineis de parâmetros (aspect_ratio, resolution → herdados do original)
- No submit: chama `onEdit(instruction)` ao invés de `onSubmit(payload)`

---

#### [MODIFY] `Gallery.tsx` — Não precisa mudar

A Gallery já exibe resultados do `status.response` normalmente. O resultado da edição entra pelo mesmo fluxo de `done` event.

---

### Backend

---

#### [NEW] `routers/edit.py` — Endpoint SSE de edição

```python
POST /edit/stream
  source_url: str      # ex: "/outputs/a3b8d1b6/gen_a3b8d1b6_1.png"
  edit_instruction: str # instrução do usuário em pt-BR
```

Pipeline simplificado (sem grounding, sem triage, sem quality contract):

```
1. Carrega bytes da imagem original do disco
2. Chama Edit Agent (otimiza prompt de edição):
   - Detecta tipo de edição (fundo, cor, acessório, iluminação, etc.)
   - Adiciona cláusulas de preservação automáticas
   - Traduz instrução pt-BR → prompt EN otimizado
3. SSE: stage "editing" → progress
4. Chama generate_images com [imagem_original + prompt_refinado]
5. Salva resultado em novo session_id
6. SSE: stage "done" → resposta com imagens
7. Salva no histórico com referência ao source_session_id
```

#### [NEW] `edit_agent.py` — Agente de refinamento de edição

Função `refine_edit_instruction(instruction, source_image_bytes, source_prompt)`:

- Usa `MODEL_AGENT` (gemini-3-flash-preview) para analisar:
  1. O que o usuário quer mudar
  2. O que deve ser preservado (inferido da imagem + prompt original)
- Retorna prompt otimizado com template de preservação:

```
"Using the provided image, [INSTRUÇÃO REFINADA].
PRESERVE exactly: the garment's fabric texture, weave pattern, color accuracy,
and draping behavior; the model's skin tone, facial features, body proportions,
and pose. Only modify: [ELEMENTO ALVO]."
```

Templates por tipo de edição:
| Tipo | Preservação extra |
|---|---|
| Fundo | `"lighting on the subject"` |
| Cor de peça | `"same fabric texture, draping, construction"` |
| Acessório | `"everything else — pose, expression, clothing, background"` |
| Iluminação | `"all physical elements"` |
| Enquadramento | `"model, outfit, style"` |

#### [MODIFY] `generator.py` — Função `edit_image()`

Nova função que reutiliza a mesma chamada `generate_content` mas monta o `contents` de forma específica para edição:

```python
def edit_image(
    source_image_bytes: bytes,
    edit_prompt: str,
    aspect_ratio: str,
    resolution: str,
    session_id: Optional[str] = None,
) -> List[dict]:
    # Monta: [imagem original] + [prompt de edição]
    # Retorna mesma estrutura de generate_images
```

#### [MODIFY] `history.py` — Campo `source_session_id`

Adicionar campo opcional `source_session_id` para rastrear a linhagem de edição:
```python
"source_session_id": source_session_id,  # de onde veio a edição
"edit_instruction": edit_instruction,     # instrução original do user
```

#### [MODIFY] `main.py` — Registrar router

```python
from routers import edit as edit_router
app.include_router(edit_router.router)
```

---

## Resumo de Arquivos

| Arquivo | Ação | Linhas estimadas |
|---|---|---|
| `types/index.ts` | MODIFY | +15 |
| `App.tsx` | MODIFY | +60, -0 |
| `ChatInput.tsx` | MODIFY | +40, -5 |
| `routers/edit.py` | **NEW** | ~150 |
| `edit_agent.py` | **NEW** | ~100 |
| `generator.py` | MODIFY | +35 |
| `history.py` | MODIFY | +5 |
| `main.py` | MODIFY | +2 |
| `lib/api.ts` | MODIFY | +5 |

---

## Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| **Drift de identidade** após edição | Edit Agent aplica cláusulas de preservação fortes + structural contract |
| **Drift de textura** em edições encadeadas | Limitar cadeia a 3 edições, após isso recomendar re-geração |
| **Imagem original deletada** do disco antes da edição | Verificar existência do arquivo antes de iniciar; fallback para URL |
| **Prompt muito longo** com muitas cláusulas | Cap de 2800 chars no prompt final |

## Verificação

1. Abrir lightbox → clicar "Modificar"
2. Banner de edição aparece no ChatInput
3. Digitar "Troque o fundo para praia"
4. Pipeline roda e resultado aparece no grid
5. Histórico mostra linhagem (source_session_id)
6. Cancelar edição volta ao modo normal
