# Decisão de Modelo: Nano Banana 2 como Padrão do Projeto

> Documento de decisão técnica (ADR — Architecture Decision Record)  
> Data: Março/2026  
> Status: ✅ Aprovado

---

## Contexto

O projeto MEDIA-SHOPEE utiliza a API do Google AI Studio para geração de imagens de produtos para Shopee e outros marketplaces. Era necessário decidir qual modelo da família Nano Banana (Gemini Image) seria o padrão do projeto.

Modelos avaliados:
- `gemini-2.5-flash-image` (Nano Banana original)
- `gemini-3-pro-image-preview` (Nano Banana Pro)
- `gemini-3.1-flash-image-preview` (Nano Banana 2) ← **escolhido**

---

## Comparativo Final

| Critério | Nano Banana (2.5) | Nano Banana Pro (3 Pro) | **Nano Banana 2 (3.1 Flash)** |
|---|---|---|---|
| **Model ID** | `gemini-2.5-flash-image` | ~~gemini-3-pro-image-preview~~ | **`gemini-3.1-flash-image-preview`** |
| **Status** | ✅ Produção | ⚠️ **DEPRECATED (Mar/2026)** | ✅ Ativo (Fev/2026) |
| **Qualidade** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (~95% do Pro) |
| **Velocidade** | Rápido | 8–12s por imagem | **4–6s (3–5x mais rápido)** |
| **Custo 1K** | ~$0.039 | ~$0.134 | **~$0.067** |
| **Custo 4K** | N/A | ~$0.240 | **~$0.180** |
| **Custo 0.5K** | ❌ | ❌ | **✅ (ultra econômico)** |
| **Free tier/dia** | ~500 img | ~100 img | **~500 img** |
| **Grounding Search** | ❌ | ❌ | **✅** |
| **Grounding Image Search** | ❌ | ❌ | **✅** |
| **Thinking Mode** | ❌ | ❌ | **✅** |
| **Acurácia texto** | 88% | 94% | **92%** |
| **Referências** | 6 imagens | 14 objetos/5 pessoas | **14 objetos/5 pessoas** |
| **Proporções extras** | ❌ | ❌ | **✅ (4:1, 1:4, 8:1, 1:8)** |

---

## Decisão

**Modelo padrão: `gemini-3.1-flash-image-preview` (Nano Banana 2)**

---

## Justificativas

### 1. Nano Banana Pro está deprecated
O `gemini-3-pro-image-preview` foi marcado como deprecated em março/2026 pelo Google. Usar um modelo deprecated é tecnicamente inviável para produção — risco de descontinuação a qualquer momento.

### 2. Nano Banana 2 entrega 95% da qualidade do Pro
A diferença de qualidade entre Nano Banana Pro e Nano Banana 2 é imperceptível para uso em e-commerce (fotos de produto, lookbooks). Benchmarks independentes confirmam 95% de equivalência visual.

### 3. Custo 50% menor
- Pro: $0.134/imagem (1K-2K)
- Nano Banana 2: $0.067/imagem — metade do preço para a mesma entrega

### 4. 3–5x mais rápido
Geração em 4–6 segundos vs 8–12 segundos do Pro. Em um workflow de iteração rápida (múltiplas variações de cor, pose, cenário), isso representa economia real de tempo.

### 5. Funcionalidades exclusivas
O Nano Banana 2 oferece recursos que o Pro **não tem**:
- **Grounding com Google Search** — modela referências reais do mundo (tendências de moda, estilos recentes)
- **Grounding com Google Image Search** — ancora elementos visuais em imagens reais
- **Thinking Mode** — raciocínio avançado para prompts complexos

### 6. Free tier generoso
~500 imagens/dia gratuitas — suficiente para iteração e desenvolvimento sem custo.

---

## Consequências

- Todos os scripts e workflows do projeto usam `gemini-3.1-flash-image-preview` como padrão
- O `gemini-3-pro-image-preview` foi removido dos scripts ativos (deprecated)
- O `gemini-2.5-flash-image` permanece disponível como fallback para produção de alto volume (mais barato, produção-estável)
- Modelo de backup para volume extremo: `imagen-4.0-fast-generate-001` ($0.02/img)

---

## Revisão

Esta decisão deve ser revisada se:
- O Nano Banana 2 for deprecated ou substituído
- Surgir um novo modelo com vantagem clara de custo/qualidade
- O Imagen 4 reduzir preços significativamente
