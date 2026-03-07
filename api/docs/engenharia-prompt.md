# Engenharia de Prompt — Framework KERNEL e Direção Cinematográfica

> Documentação de estratégias avançadas de prompt para modelos de imagem e vídeo.  
> Modelos cobertos: Nano Banana 2, Veo 3.1  
> Atualizado: Março/2026

---

## Índice

1. [Princípio Fundamental](#1-princípio-fundamental)
2. [Framework KERNEL para Imagem](#2-framework-kernel-para-imagem)
3. [Direção Cinematográfica para Veo 3.1](#3-direção-cinematográfica-para-veo-31)
4. [Character Bible — Consistência de Personagem](#4-character-bible--consistência-de-personagem)
5. [Thinking Level e Estrutura de Raciocínio](#5-thinking-level-e-estrutura-de-raciocínio)
6. [Thought Signatures — CRÍTICO para Multi-turno](#6-thought-signatures--crítico-para-multi-turno)

---

## 1. Princípio Fundamental

> **"Descreva a cena. Não liste palavras-chave."**

Modelos de raciocínio como o Gemini 3 trabalham melhor com **parcerias de pesquisa e direção técnica**, não com chat casual. Um parágrafo narrativo e descritivo quase sempre produzirá resultado melhor do que uma lista de palavras-chave desconexas.

| Abordagem | Resultado |
|---|---|
| ❌ `"modelo, blusa, branca, shopee, foto, profissional"` | Genérico, sem coerência visual |
| ✅ `"Modelo feminina brasileira, 26 anos, usando blusa branca de linho com mangas curtas, em pé em posição de três quartos, iluminação de estúdio suave e difusa, câmera no nível dos olhos, enquadramento americano"` | Específico, controlado, previsível |

---

## 2. Framework KERNEL para Imagem

O **Framework KERNEL** estrutura requisições de API para evitar respostas genéricas em ambientes de produção:

### K — Keep it simple (Objetivo Claro)
Defina **um único objetivo** por prompt.

❌ Errado: `"Ajuda com uma imagem de produto moda"`  
✅ Correto: `"Foto macro do tecido tricô de algodão bege, textura fio a fio visível"`

---

### E — Easy to verify (Critérios Mensuráveis)
Estabeleça critérios de sucesso verificáveis.

✅ `"inclua três xícaras de porcelana branca sobre mesa de madeira clara"`  
✅ `"a modelo deve estar olhando diretamente para a câmera"`

---

### R — Reproducible (Sem Termos Temporais)
Evite termos como "estilo atual" ou "tendência 2026". Use descrições de estéticas atemporais ou versões específicas.

❌ `"roupa com estilo atual"`  
✅ `"estilo minimalista com paleta neutro-terrosa: creme, bege e branco off"`

---

### N — Narrow scope (Uma Tarefa por Prompt)
Não tente gerar código + imagem + descrição em uma única chamada.  
Separe a tarefa em chamadas independentes quando necessário.

---

### E — Explicit constraints (Restrições Explícitas)
Defina o que **NÃO** deve aparecer — use prompt negativo semântico (não `"sem X"`, mas a versão positiva do que você quer):

❌ `"sem pessoas ao fundo"`  
✅ `"cenário completamente isolado, sem pessoas, só a modelo no frame"`

❌ `"sem texto"`  
✅ `"imagem totalmente visual, sem elementos tipográficos"`

---

### L — Logical structure (Estrutura Tripartite)

```
[CONTEXTO no início] → [TAREFA no meio] → [FORMATO DE SAÍDA + PARÂMETROS no final]
```

**Template:**
```
Contexto: [quem é o sujeito, onde está, que situação]
Tarefa: [o que o modelo deve gerar/fazer]
Saída: [proporção, resolução, estilo fotográfico, técnica de câmera]
```

**Exemplo aplicado:**
```
Contexto: Modelo feminina brasileira, 25 anos, pele morena clara, cabelo cacheado castanho.
Tarefa: Foto editorial de moda e-commerce vestindo blusa de tricô bege de ponto aberto, 
braço levantado tocando suavemente os cabelos, expressão relaxada e confiante.
Saída: 9:16, estúdio com fundo branco limpo, iluminação de aro suave, câmera no nível dos olhos, 
enquadramento americano (cintura para cima), estilo Zara campaign 2024.
```

---

## 3. Direção Cinematográfica para Veo 3.1

Para vídeo, o prompt deve funcionar como uma **folha de direção cinematográfica**. Use os 6 ingredientes:

### Os 6 Ingredientes

```
[1. CINEMATOGRAFIA] + [2. SUJEITO E AÇÃO] + [3. ESTILO VISUAL] + 
[4. ILUMINAÇÃO E ATMOSFERA] + [5. AMBIENTE] + [6. PARÂMETROS TÉCNICOS]
```

---

#### 1. Cinematografia — trabalho de câmera

| Termo | Efeito |
|---|---|
| `Crane shot` | Câmera sobe ou desce em grua, visão aérea dramática |
| `Dolly-in` | Câmera avança lentamente em direção ao sujeito |
| `Dolly-out / Pull-back` | Câmera recua, revelando o cenário |
| `Tracking shot` | Câmera acompanha o sujeito em movimento |
| `Handheld tracking` | Câmera na mão, levemente instável, realista |
| `Static wide shot` | Câmera parada, plano aberto |
| `Pan left/right` | Câmera gira horizontalmente |
| `Tilt up/down` | Câmera inclina verticalmente |

---

#### 2. Sujeito e Ação — quem faz o quê

❌ `"alguém caminhando"`  
✅ `"Um monge idoso caminha lentamente por um jardim zen, movimentos deliberados, mãos entrelaçadas nas costas"`

---

#### 3. Estilo Visual — o "look" do vídeo

| Referência | Estética |
|---|---|
| `Film Noir` | Preto e branco, sombras duras, drama |
| `Cyberpunk` | Neon, chuva, futuro distópico |
| `Golden hour lifestyle` | Luz dourada, naturalidade, calor |
| `Hyperrealistic documentary` | Câmera na mão, realismo total |
| `Wes Anderson symmetry` | Composição centrada, paleta pastel, estilizado |
| `Commercial fashion editorial` | Luz de estúdio, modelo direto ao olhar, produto em destaque |

---

#### 4. Iluminação e Atmosfera — tom emocional

| Termo | Uso |
|---|---|
| `Golden hour` | Luz de fim de tarde, quente e suave |
| `Overcast soft light` | Dia nublado, luz difusa sem sombras |
| `Moody side lighting` | Luz lateral dramática, contraste alto |
| `Neon glow` | Reflexos coloridos, ambientes urbanos noturnos |
| `Studio rim lighting` | Luz de contorno, separa sujeito do fundo |
| `Candlelight flicker` | Luz quente e instável, intimidade |

---

#### 5. Ambiente — cenário e condições

Detalhe: **local + hora do dia + condições climáticas**

✅ `"Favela carioca ao entardecer, ruas molhadas após chuva, luzes de mercadinho ao fundo"`  
✅ `"Estúdio industrial minimalista, São Paulo, meio-dia, luz natural entrando por janelas altas"`

---

#### 6. Parâmetros Técnicos — lente e profundidade

| Parâmetro | Efeito |
|---|---|
| `35mm lens` | Campo visão natural, jornalístico |
| `50mm lens` | Padrão, mais próximo da visão humana |
| `85mm lens` | Retrato, comprime fundo, bokeh natural |
| `24mm wide-angle` | Grandes planos, arquitetura |
| `Macro lens` | Detalhes extremos, textura |
| `Shallow depth of field` | Fundo desfocado, sujeito isolado |
| `24 FPS` | Cadência cinematográfica padrão |

---

### Template completo Veo 3.1

```
[CINEMATOGRAFIA]: Tracking shot suave acompanhando a modelo
[SUJEITO]: Modelo feminina brasileira, 27 anos, cabelos soltos, 
           vestindo vestido midi floral bege, caminhando descalça na areia
[ESTILO]: Campanha comercial de moda, hyperrealistic lifestyle
[LUZ]: Golden hour, luz lateral quente e suave, reflexos dourados na pele
[AMBIENTE]: Praia de Trancoso, Bahia, fim de tarde, mar calmo ao fundo
[TÉCNICO]: 85mm lens, shallow depth of field, 24 FPS, 9:16
[ÁUDIO]: Som ambiente de ondas quebrando suavemente, brisa leve
```

---

#### Controle de diálogo e SFX no Veo

O modelo entende física de áudio — ajusta volume com base em distância e ambiente:

```python
prompt = """
Tracking shot de uma modelo caminhando por corredor de hotel de luxo.
Seus saltos ecoam no mármore.
Ela para, vira para a câmera e sussurra: 'Encontrei o que eu precisava.'
Fundo sonoro: silêncio de hotel, eco suave nos corredores, AC ao longe.
"""
```

---

## 4. Character Bible — Consistência de Personagem

Para vídeos com mais de 8 segundos (múltiplos clipes), a descrição de personagem deve ser padronizada em JSON para reduzir variabilidade em ~70%.

### Estrutura do Character Bible

```python
CHARACTER_BIBLE = {
    "character_description": {
        "name": "Sofia",
        "age": "26 anos",
        "ethnicity": "brasileira, pele morena clara",
        "hair": "cachos médios castanho-escuros, volume natural",
        "eyes": "castanhos amendoados",
        "build": "média, 1.68m, atlética",
        "distinguishing_features": "sardas levíssimas no nariz, sorriso largo"
    },
    "outfit_session": "vestido midi floral bege, sandálias nude",
    "mood": "confiante, descontraída, acessível"
}

def build_video_prompt(scene: dict, character: dict) -> str:
    return f"""
CHARACTER (manter idêntico em todos os clipes):
{character['character_description']}
Roupa: {character['outfit_session']}
Expressão: {character['mood']}

CENA:
{scene['description']}
Câmera: {scene['camera']}
Ambiente: {scene['environment']}
Luz: {scene['lighting']}
"""
```

### Uso em múltiplos clipes

```python
cenas = [
    {
        "description": "Sofia caminha por rua de São Paulo ao entardecer",
        "camera": "Tracking shot lateral, 35mm",
        "environment": "Rua Gonçalo de Carvalho, Porto Alegre",
        "lighting": "Golden hour, luz lateral"
    },
    {
        "description": "Sofia entra em café, pede no balcão, sorri para o barista",
        "camera": "Dolly-in suave, 50mm",
        "environment": "Café industrial minimalista, interior",
        "lighting": "Luz natural de janela + luz quente do balcão"
    }
]

for i, cena in enumerate(cenas):
    prompt = build_video_prompt(cena, CHARACTER_BIBLE)
    # cada clipe mantém Sofia consistente
```

---

## 5. Thinking Level e Estrutura de Raciocínio

O `thinking_level` controla a profundidade de raciocínio na geração de imagem. **Disponível no Nano Banana 2 e Pro.**

### Níveis disponíveis

| Nível | Quando usar | Impacto de custo | Latência |
|---|---|---|---|
| `"HIGH"` | Layouts complexos, texto em imagem, composição multi-elemento | Maior (mais tokens de "pensamento") | 8–18s |
| `"MEDIUM"` | Padrão equilibrado — texturas moderadas, cenas com modelo | Médio | 5–12s |
| `"MINIMAL"` | ✅ Padrão implícito — iteração rápida, catálogo, fundo simples | Menor | 1–5s |

> ⚠️ **Atenção:** O valor correto da API é `"MINIMAL"` (não `"LOW"`). Usar `"LOW"` causa erro silencioso e o modelo assume `MINIMAL` como fallback.

### Código com thinking_level

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=["Capa de revista de moda com título estilizado em serif, modelo feminina, composição assimétrica"],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(
            aspect_ratio="9:16",
            image_size="2K"
        ),
        thinking_config=types.ThinkingConfig(thinking_level="HIGH")
    )
)
```

### Quando usar HIGH obrigatoriamente

- Texto estilizado dentro da imagem (títulos, labels, infográficos)
- Layouts com posicionamento geométrico preciso
- Composições com múltiplos elementos interdependentes
- Qualquer prompt com instruções de "coloque X aqui, Y ali"

### Quando usar MINIMAL

- Geração em volume (catálogos, variações de cor)
- Composições simples (produto em fundo branco, ghost mannequin)
- Iteração rápida de conceitos
- Fase de rascunho antes do render final
- Modelos em cenário sem textura complexa de roupa

---

## 6. Thought Signatures — CRÍTICO para Multi-turno

> ⚠️ **Omitir as Thought Signatures em conversas multi-turno causa erro 400 ou degradação grave da qualidade.**

### O que são

Quando o modelo "pensa" antes de gerar, ele produz uma **assinatura de raciocínio** (`thought_signature`) que representa o estado interno do processo criativo. Para manter coerência em conversas de múltiplos turnos, essa assinatura **deve ser enviada de volta** na requisição seguinte.

### Fluxo correto com Thought Signatures

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
historico = []

# === Turno 1 ===
historico.append(types.Content(role="user", parts=[
    types.Part.from_text(
        "Modelo feminina brasileira, blusa azul marinho, estúdio branco"
    )
]))

resp1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=historico,
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K"),
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM")
    )
)

# ⚠️ IMPORTANTE: incluir a resposta COMPLETA (com thought signature) no histórico
historico.append(resp1.candidates[0].content)

# Salvar imagem
for part in resp1.parts:
    if part.inline_data:
        part.as_image().save("output/v1.png")

# === Turno 2 — a thought signature é enviada automaticamente via histórico ===
historico.append(types.Content(role="user", parts=[
    types.Part.from_text("Mantenha tudo igual, mas mude a blusa para vermelho vinho")
]))

resp2 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=historico,  # contém a thought signature do turno 1
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM")
    )
)

historico.append(resp2.candidates[0].content)
for part in resp2.parts:
    if part.inline_data:
        part.as_image().save("output/v2_vermelho.png")
```

### Erros comuns

| Erro | Causa | Solução |
|---|---|---|
| `400 Bad Request` | Thought signature omitida | Incluir `resp.candidates[0].content` no histórico |
| Degradação de qualidade | Histórico incompleto | Sempre append a resposta completa, não apenas a imagem |
| Inconsistência visual entre turnos | Assinatura corrompida | Não manipular o objeto de conteúdo, passar como retornado |
