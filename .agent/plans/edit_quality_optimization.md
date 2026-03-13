# Otimização do Fluxo de Edição de Imagem — v2

> **Revisão v2:** `temperature=0.4` removida como correção estrutural → experimento com flag. `config.py` movido para plano separado. Verificação reescrita com benchmark real via `/edit/stream`.

---

## Mudanças Aprovadas (baixo risco, sem ambiguidade)

### Componente 1 — `image_utils.py` (novo módulo)

#### [NEW] [image_utils.py](file:///Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/image_utils.py)

Extrai `_detect_image_mime` de `generator.py` para módulo compartilhado:

```python
def detect_image_mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"
```

---

### Componente 2 — `edit_agent.py`

#### [MODIFY] [edit_agent.py](file:///Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/edit_agent.py)

**Mudança A — MIME real na imagem original (linha 187):**
Hardcoded como `"image/jpeg"`. Imagem PNG gerada pelo Nano é decodificada sobre bitstream errado → artefatos de textura.

```python
# ANTES
types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=source_image_bytes))

# DEPOIS
from image_utils import detect_image_mime

types.Part(
    inline_data=types.Blob(
        mime_type=detect_image_mime(source_image_bytes),
        data=source_image_bytes,
    ),
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
)
```

**Mudança B — `media_resolution=HIGH` nas imagens de referência (linha 191):**
O `generator.py` já faz `MEDIA_RESOLUTION_HIGH` desde a linha 350. O `edit_agent` não fazia, gerando diagnóstico em baixa resolução → `preserve_clause` genérico.

```python
# ANTES
parts.append(types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=ref_bytes)))

# DEPOIS
parts.append(types.Part(
    inline_data=types.Blob(mime_type=detect_image_mime(ref_bytes), data=ref_bytes),
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
))
```

---

### Componente 3 — `generator.py`

#### [MODIFY] [generator.py](file:///Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend/generator.py)

**Mudança C — alias para `image_utils` (sem mudança de comportamento):**

```python
# ANTES (linha ~67) — remover a definição local
def _detect_image_mime(image_bytes: bytes) -> str: ...

# DEPOIS — adicionar no topo:
from image_utils import detect_image_mime as _detect_image_mime
```

---

## Mudança Experimental (flag de feature)

### `generator.py` + `config.py` — `response_modalities=['IMAGE']` na edição

> [!NOTE]
> A skill nano-banana recomenda `['IMAGE']` para pipelines de produção. Não entra como correção estrutural — entra como experimento ativável via env var para evitar risco de regressão no parser.

**Flag em `config.py` (nova linha, sem remover nada):**
```python
EDIT_IMAGE_ONLY_MODALITY = os.getenv("EDIT_IMAGE_ONLY_MODALITY", "false").strip().lower() == "true"
```

**Em `generator.py` → função `edit_image`:**
```python
from config import EDIT_IMAGE_ONLY_MODALITY
...
modalities = ["IMAGE"] if EDIT_IMAGE_ONLY_MODALITY else ["TEXT", "IMAGE"]
config = types.GenerateContentConfig(
    response_modalities=modalities,
    ...
)
```

Ativação: `.env` com `EDIT_IMAGE_ONLY_MODALITY=true`. Default `false` = comportamento atual intacto.

> [!IMPORTANT]
> `temperature` **não é alterada**. O default do Gemini 3 para imagem é o correto. Qualquer ajuste requer A/B controlado como experimento separado e independente.

---

## Fora do Escopo deste Plano

| Item removido | Motivo |
|---|---|
| `VALID_ASPECT_RATIOS` / `VALID_RESOLUTIONS` em `config.py` | Contrato global de `/generate`, não de `/edit/stream`. Altera backend sem fechar o circuito UI. Plano separado. |
| `temperature=0.4` | Não validado. Orientação atual do Gemini 3 é manter `1.0` para imagem. Experimento separado. |

---

## Arquivos Modificados

| Arquivo | Ação | Mudança |
|---|---|---|
| `backend/image_utils.py` | **[NEW]** | `detect_image_mime` compartilhado |
| `backend/edit_agent.py` | **[MODIFY]** | A + B: MIME real + `media_resolution=HIGH` |
| `backend/generator.py` | **[MODIFY]** | C: alias para `image_utils` + flag experimental D |
| `backend/config.py` | **[MODIFY]** | Flag `EDIT_IMAGE_ONLY_MODALITY` somente |

---

## Verificação

### 1. Testes estruturais

```bash
cd /Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/backend

python -c "
from image_utils import detect_image_mime
assert detect_image_mime(b'\x89PNG\r\n\x1a\n' + b'\x00'*20) == 'image/png'
assert detect_image_mime(b'\xff\xd8\xff' + b'\x00'*20) == 'image/jpeg'
assert detect_image_mime(b'\x00'*20) == 'image/jpeg'
print('image_utils OK')
"

python -c "import edit_agent, generator, config; print('imports OK')"
```

### 2. Benchmark real — protocolo antes/depois

> [!IMPORTANT]
> Critério mínimo de aprovação: executar com imagens PNG reais geradas pelo pipeline, comparar lado a lado.

**Critérios de aprovação:**

| Critério | Baseline | Meta |
|---|---|---|
| Tessuto + cor da peça preservados (visual) | referência | ≥ igual |
| `preserve_clause` no log nomeia elementos específicos | genérico | cor + material nomeados |
| Erro de parse em PNG | possível | zero |
| Sem nova exceção no `/edit/stream` | — | zero regressões |

**Protocolo:**
1. Gerar 1 imagem PNG via `/generate/stream` → registrar URL + session_id
2. Aplicar edição leve (`"mudar fundo para branco"`) → salvar resultado **before**
3. Aplicar mudanças A+B+C
4. Repetir mesma edição com mesma imagem fonte → salvar resultado **after**
5. Comparar visual: peça, cor, textura; comparar `preserve_clause` nos logs

**Para experimento D (IMAGE-only):**
1. Ativar `EDIT_IMAGE_ONLY_MODALITY=true` no `.env`
2. Repetir protocolo acima
3. Confirmar que o parser não lança `RuntimeError: Nano retornou sem imagem`
4. Comparar resultado visual com baseline
