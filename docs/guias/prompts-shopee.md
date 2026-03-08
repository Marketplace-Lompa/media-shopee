# Guia de Prompts — E-commerce Shopee com Nano Banana 2

> Modelo: `gemini-3.1-flash-image-preview`  
> Atualizado: Março/2026

---

## Estrutura de Prompt Ideal

O Nano Banana 2 responde melhor a prompts com estrutura clara e vocabulário específico. Use sempre o padrão:

```
[MODELO] + [ROUPA] + [COMPOSIÇÃO] + [CÂMERA] + [CENÁRIO] + [LUZ] + [ESTILO]
```

---

## Sistema de 3 Fotos (Shopee)

Toda listagem Shopee deve ter no mínimo 3 tipos de foto:

### 1. HERO (Capa Principal) — 9:16
A foto que aparece na busca. Deve ser impactante e mostrar a peça completa.

**Estrutura:**
```
Modelo feminina/masculina brasileira, [descrição modelo], usando [peça + cor + material],
[pose], [cenário], [câmera], [enquadramento], [luz], fotografia editorial de moda,
alta resolução, cores vibrantes
```

**Exemplo:**
```
Modelo feminina brasileira, 26 anos, cabelos cacheados castanhos, pele morena clara,
usando camiseta branca de algodão modal com estampa ondinha sutil na barra,
em pé com uma mão no quadril e a outra soltando os cabelos,
rua de São Paulo ao entardecer com árvores ao fundo bokeh,
câmera em ângulo médio-americano (da cintura para cima), luz dourada natural,
fotografia editorial de moda e-commerce, cores vibrantes, nitidez profissional
```

### 2. MEDIUM (Meio do Anúncio) — 3:4, 4:5 ou 9:16
Foto de cintura para cima. Destaca o produto com mais detalhe.

**Estrutura:**
```
Modelo [gênero] brasileira/o, [descrição], [peça], [pose de cintura para cima],
[cenário neutro ou complementar], câmera em close médio (cintura para cima),
[luz], fotografia de produto e-commerce
```

### 3. MACRO (Detalhe de Textura) — 1:1
Close-up extremo mostrando o tecido/material. Essencial para confiança do cliente.

**Estrutura:**
```
Close-up macro extremo do tecido [nome do tecido] [cor], mostrando textura [descrição detalhada],
fio por fio visível, [detalhe específico da peça],
fundo desfocado suave, luz de estúdio lateral revelando textura,
fotografia macro de tecido, 4K, ultra-nítido
```

---

## Vocabulário por Categoria de Roupa

### Camisetas / Blusas
| Elemento | Palavras-chave |
|---|---|
| Tecido modal | `modal macio`, `caimento fluido`, `textura sedosa`, `brilho suave` |
| Tecido algodão | `algodão penteado`, `textura natural`, `levemente estruturado` |
| Tecido dry-fit | `synthetic athletic`, `brilho técnico`, `textura comprimida` |
| Acabamento | `costura overlock visível`, `etiqueta no pescoço`, `barra bem acabada` |

### Calças / Shorts
| Elemento | Palavras-chave |
|---|---|
| Jeans | `denim azul índigo`, `lavagem clara/média/escura`, `textura de sarja` |
| Moletom | `french terry`, `textura felpuda interna`, `acabamento elástico` |
| Linho | `linho natural bege`, `textura rústica leve`, `caimento solto` |

### Vestidos / Saias
| Elemento | Palavras-chave |
|---|---|
| Fluido | `tecido fluindo suavemente`, `drapeado natural`, `movimento ao caminhar` |
| Estruturado | `forma mantida`, `silhueta definida`, `volume controlado` |

---

## Modelos Brasileiros — Referências

### Modelo Feminina
```
modelo feminina brasileira, [idade] anos, [tom de pele], cabelos [tipo + cor],
[altura aprox.], expressão [natural/sorridente/séria porém elegante]
```

**Tons de pele disponíveis:**
- `pele clara rosada` — Sul/Sudeste
- `pele morena clara` — mix brasileiro
- `pele morena` — representação média
- `pele morena escura` — representação negra
- `pele negra` — representação negra retinta

### Modelo Masculino
```
modelo masculino brasileiro, [idade] anos, [tom de pele], cabelos [tipo + cor],
[compleição: magro/atlético/forte], expressão [descontraída/séria/sorridente]
```

---

## Cenários por Plataforma

### Shopee (lifestyle permitido)
| Cenário | Quando usar |
|---|---|
| Rua de São Paulo | Peças urbanas, casuais |
| Praia / litoral | Roupas de verão, resort |
| Parque / jardim | Peças leves, primavera |
| Estúdio minimalista | Peças de qualquer estilo |
| Café / interior | Moda feminina casual |

### Mercado Livre (usar `moda-ml` skill)
- ✅ Fundo branco/cinza/creme digitalizado APENAS
- ❌ Sem cenários reais na capa
- Ver skill `moda-ml` para regras completas

---

## Configurações de Câmera Recomendadas

| Look | Enquadramento | Distância focal equiv. |
|---|---|---|
| Hero Shopee | Americano (joelhos p/ cima) | 50mm |
| Lifestyle | Inteiro (cabeça a pés) | 35mm |
| Detalhe outfit | Cintura p/ cima | 85mm |
| Macro textura | Detalhe de tecido | 100mm macro |
| Ambiente | Full body + cenário | 28mm |

---

## Parâmetros API para Cada Tipo

### Compatibilidade por modo

- `Studio Local (app/backend)`: `1:1`, `3:4`, `4:3`, `9:16`, `16:9`
- `Scripts API (api/scripts/gerar_imagem.py)`: inclui também `4:5`, `5:4` e formatos ultra-wide

Se estiver no Studio Local e quiser um enquadramento vertical tipo `4:5`, use `3:4` como substituto mais próximo.

```python
# HERO (capa Shopee)
config = ImageConfig(aspect_ratio="9:16", image_size="2K")

# MEDIUM (cintura p/ cima) - Studio Local
config = ImageConfig(aspect_ratio="3:4", image_size="2K")

# MEDIUM (cintura p/ cima) - Scripts API diretos
config = ImageConfig(aspect_ratio="4:5", image_size="2K")

# MACRO (textura)
config = ImageConfig(aspect_ratio="1:1", image_size="2K")

# BANNER (desktop)
config = ImageConfig(aspect_ratio="16:9", image_size="2K")
```

---

## Checklist antes de Gerar

- [ ] Prompt tem descrição do modelo (gênero, tom de pele, cabelo)
- [ ] Descrição da peça é específica (material, cor, detalhes)
- [ ] Cenário definido (não deixar genérico)
- [ ] Proporção correta para o tipo de foto
- [ ] Sem elementos proibidos (marcas, logotipos reais)
