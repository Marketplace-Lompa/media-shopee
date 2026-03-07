---
name: moda-ml
description: >
  Skill específica para fotos de moda no Mercado Livre. Contém todas as regras
  oficiais, requisitos técnicos, proibições absolutas, e boas práticas para
  gerar imagens que passam na moderação do ML sem perder exposição. Diferente
  da skill ecommerce (genérica), esta skill aplica as restrições específicas
  do Mercado Livre: fundo branco/cinza/creme digitalizado, sem elementos extras,
  sem cenários reais na foto de capa, enquadramento 60-80%, e compliance total.
  Deve ser usada sempre que o destino da imagem for o Mercado Livre.
---

# Moda ML — Regras de Fotos de Moda no Mercado Livre

## Contexto

O Mercado Livre modera ativamente as fotos de moda desde fevereiro de 2022. Fotos que não seguem as políticas podem:
- Perder exposição nos resultados de busca
- Ter o anúncio pausado
- Gerar moderação automática

> **Estatística oficial do ML:** clientes olham de 3 a 4 vezes as fotos antes de decidir a compra.

---

## Regras Gerais (Todas as Categorias)

### Quantidade de Fotos
- **Mínimo obrigatório:** 4 fotos
- **Máximo permitido:** 8 a 10 fotos (varia por variação)
- **Até 10 fotos por variação** de cor/tamanho
- A **primeira foto (capa)** é a mais importante — aparece nos resultados de busca

### Requisitos Técnicos Obrigatórios

| Parâmetro | Valor |
|-----------|-------|
| **Formato** | Quadrado (1:1) |
| **Tamanho** | 1200 × 1200 px (recomendado) — mínimo 500 × 500 px |
| **Resolução** | 72 dpi |
| **Peso mínimo** | Acima de 600 KB |
| **Modo de cor** | RGB |
| **Peso máximo** | 2 MB (compressão necessária se exceder) |

### Fundo — Regra Fundamental

| Regra | Detalhe |
|-------|---------|
| **Cores permitidas** | Branco, cinza claro, creme/bege |
| **Tipo** | Liso, criado **digitalmente** |
| **Proibido** | Fundos texturizados, reais, degradê, cenários |
| **Contraste** | Se o produto é branco → usar fundo cinza ou creme |
| **Foto de capa** | Preferencialmente fundo branco |

> ⚠️ **DIFERENÇA CRÍTICA vs Shopee/Ecommerce genérico:** no ML, a foto de capa NÃO pode ter cenário lifestyle. Cenários são tolerados apenas em fotos complementares e mesmo assim com restrições.

### Proibições Absolutas (todas as fotos)

| ❌ Proibido | Motivo |
|-------------|--------|
| Marca d'água | Distrai e oculta produto |
| Logotipo da empresa | Elemento extra |
| Texto sobre a foto | Qualquer texto, inclusive medidas |
| Bordas / molduras | Elemento extra |
| Código QR | Elemento extra |
| Dados de contato (email, fone, redes) | Informação comercial proibida |
| Etiquetas do ML ("Mais vendido", "Full", "MercadoLíder") | Apenas o ML pode atribuir |
| Banners promocionais | Informação comercial |
| Informações sobre variações | Usar sistema de variações do ML |
| Instruções de compra/entrega | Informação comercial |
| Fotos de terceiros sem autorização | Direitos autorais → anúncio pausado |

---

## Regras por Categoria

### Partes de Cima (Blusas, Camisetas, Camisas, Jaquetas, Casacos, Cardigãs)

**Foto de Capa:**
- Fundo: branco, cinza ou creme — liso, digital
- Apresentação: modelo real OU manequim transparente (invisível)
- Enquadramento: produto centralizado, visível 100%, ocupando 60-80% da imagem
- Posição: de frente
- Rosto: se usar modelo, o rosto **não pode ser cortado**

**Fotos Complementares (2ª em diante):**
- Vista traseira
- Detalhes aproximados (textura, botões, costura, estampa)
- Como fica no corpo inteiro

**O que evitar:**
- Roupas amassadas
- Ambientes pouco iluminados
- Elementos que distraiam

### Partes de Baixo (Calças, Shorts, Saias)

**Mesmas regras de partes de cima, com destaque:**
- Modelo real ou manequim transparente
- Centralizado, de frente, 60-80% da imagem
- Complementares: costas, detalhes (zíper, bolsos, barra)

### Vestidos e Macacões

**Foto de Capa:**
- Modelo real ou manequim transparente
- Se usar modelo: mostrar **corpo inteiro** ou pelo menos da panturrilha até acima da cabeça
- Centralizado, de frente

**O que evitar:**
- Roupas amassadas, mal iluminadas
- Penduradas em cabide
- Com outras peças de roupa no enquadramento

### Roupas Íntimas e de Praia

- Modelo real ou manequim transparente
- Centralizado, virado para frente
- Rosto do modelo **não pode ser cortado**
- Evitar: roupas amassadas, cabides, outras peças visíveis

### Calçados

**Regras especiais:**
- Apenas **1 unidade** do calçado na capa
- Ângulo lateral — **virado para a direita**
- Cadarço amarrado (se tiver)
- Chinelo de dedos: mostrar o par visto de cima, centralizado, sem modelos
- **Não usar** calçados sobre caixas ou texturas

**Complementares:** perspectiva (diagonal), vista de cima/frente, parte traseira, sola

### Roupas de Bebê

**Diferencial:**
- Produto **sozinho, sem manequim**
- Ajuda a visualizar o caimento sem referência corporal
- Mesmas regras de fundo e enquadramento

### Packs (Pacotes)

- Produto sozinho ou manequim transparente
- **Alinhar produtos diagonalmente** da esquerda para a direita
- Um produto pode aparecer por inteiro, o restante em ordem
- Para íntimas: exibir o elástico da peça

### Acessórios (Bolsas, Cintos, Chapéus, etc.)

- Produto **sozinho, sem manequim** na capa
- Complementares: pode mostrar com modelo real

---

## Manequim Transparente (Ghost Mannequin)

O ML permite e incentiva o uso de **manequim transparente** — técnica onde o manequim é removido digitalmente, mostrando apenas a peça como se estivesse flutuando.

### Para IA: Como Simular Ghost Mannequin

```
The garment displayed as if worn on an invisible mannequin — the 
garment holds its natural three-dimensional shape and drape as if 
on a body, but no model or mannequin is visible. Clean white 
digital background. The garment is centered, facing forward, 
occupying 70% of the square frame.
```

### Quando Usar
- Quando quer mostrar a peça sem associar a um biotipo específico
- Quando o ML exige "sem modelo" (bebê, acessórios)
- Quando quer padronizar o catálogo inteiro

---

## Estratégia de Listing Otimizada para ML (4-8 Fotos)

### Set Mínimo (4 Fotos — Obrigatório)

| Foto # | Tipo | Descrição | Fundo |
|--------|------|-----------|-------|
| **1** | Capa — Frente | Modelo ou ghost mannequin, produto centralizado, de frente | Branco/cinza/creme digital |
| **2** | Costas | Mesmo modelo/manequim, vista traseira | Mesmo fundo |
| **3** | Detalhe | Close-up da textura, botões, costura, estampa | Peça como fundo (macro) |
| **4** | Fit / Corpo Inteiro | Modelo vestindo, corpo inteiro, mostrando caimento | Fundo liso ou soft |

### Set Completo (8 Fotos — Recomendado)

| Foto # | Tipo | Descrição | Fundo |
|--------|------|-----------|-------|
| **1** | Capa — Frente | Modelo ou ghost mannequin, centralizado, de frente | Branco digital |
| **2** | Costas | Vista traseira, mesma apresentação | Mesmo fundo |
| **3** | Lateral / 3/4 | Mostra silhueta e volume | Mesmo fundo |
| **4** | Detalhe 1 | Close-up textura / tecido | Macro na peça |
| **5** | Detalhe 2 | Close-up elemento (botão, zíper, etiqueta, costura) | Macro na peça |
| **6** | Fit — Corpo Inteiro | Modelo real, corpo completo, caimento real | Fundo liso |
| **7** | Lifestyle (sutil) | Modelo em contexto discreto (sem cenário elaborado) | Neutro / soft |
| **8** | Variação / Composição | Flat lay ou combinação com outras peças do look | Fundo liso |

---

## Instruções de Prompt para Compliance ML

### Foto de Capa (Foto 1) — Template

```
[Garment description] displayed on a [model description / invisible 
ghost mannequin]. Clean solid white digital background, no textures, 
no real environment. The garment is centered in the frame, facing 
forward, fully visible with no cropping, occupying approximately 
70% of the square image. Even, soft studio lighting with no harsh 
shadows. The image is clean, professional, with no text, logos, 
watermarks, borders, or additional elements.
```

### Foto com Modelo Real — Template

```
A [Brazilian model description] wearing [garment description]. 
She stands facing the camera in a natural relaxed pose. Clean solid 
[white/light gray/cream] digital background. Full body visible from 
slightly above the head to below the feet. The garment is the 
protagonist — no accessories or elements that distract. Even, soft 
lighting. No text, logos, or watermarks. Square format composition.
```

### Foto de Detalhe — Template

```
Extreme close-up of [specific detail: fabric texture / button / 
stitching / pattern / zipper / embroidery] on the [garment]. 
The detail occupies 80% of the frame with shallow depth of field. 
Soft even lighting revealing the texture and construction quality. 
No text or additional elements. Square format.
```

### Ghost Mannequin — Template

```
[Garment description] displayed on a completely invisible mannequin. 
The garment holds its natural three-dimensional shape as if worn, 
but no body or mannequin is visible. Clean solid white digital 
background. Centered, facing forward, occupying 70% of the square 
frame. Even soft lighting, no harsh shadows. Professional catalog 
style photography.
```

---

## Proibições no Prompt (Anti-Patterns ML)

Ao gerar imagens para o ML, **NUNCA incluir no prompt:**

| ❌ Nunca | Por quê |
|----------|---------|
| Cenários reais na foto de capa | ML exige fundo liso digital |
| Textos, números, medidas | Proibido pelo ML |
| Logotipos | Proibido pelo ML |
| Múltiplos produtos juntos | Usar sistema de variações |
| Cabides | Não pode parecer pendurado |
| Roupas amassadas, dobradas | Má apresentação |
| Embalagens | Não na foto principal |
| Caixas sob calçados | Proibido especificamente |
| Acessórios que distraiam | Produto é o protagonista |
| Bordas / molduras decorativas | Elemento extra proibido |
| Fundo com gradiente | ML exige fundo liso |

---

## Diferenças ML vs Shopee

| Aspecto | Mercado Livre | Shopee |
|---------|---------------|--------|
| **Fundo capa** | Branco/cinza/creme liso digital OBRIGATÓRIO | Mais flexível, aceita cenários |
| **Cenário** | Proibido na capa, restrito nas complementares | Aceito e incentivado (lifestyle) |
| **Elementos extras** | Proibição rigorosa | Mais tolerante |
| **Marca d'água** | Proibição absoluta | Tolerada em alguns casos |
| **Manequim** | Transparente (removido digitalmente) | Aceita manequim visível |
| **Min fotos** | 4 obrigatórias | Variável |
| **Formato** | 1:1 quadrado obrigatório | 1:1 recomendado |
| **Tamanho** | 1200×1200 recomendado, min 500px | Similar |
| **Moderação** | Ativa — pode pausar/perder exposição | Menos rigorosa |
| **Texto na foto** | Proibido | Tolerado (banners, preço) |

---

## Checklist de Compliance (Validação Final)

Antes de publicar qualquer foto no ML, verificar:

- [ ] Fundo liso digital (branco, cinza ou creme)?
- [ ] Produto centralizado e de frente?
- [ ] Produto ocupa 60-80% da imagem?
- [ ] Formato quadrado (1:1)?
- [ ] Resolução ≥ 1200×1200 px?
- [ ] Peso ≥ 600 KB e ≤ 2 MB?
- [ ] Modo de cor RGB?
- [ ] Sem marca d'água?
- [ ] Sem logotipo?
- [ ] Sem texto de qualquer tipo?
- [ ] Sem bordas ou molduras?
- [ ] Sem QR code?
- [ ] Sem dados de contato?
- [ ] Sem etiquetas/atributos do ML?
- [ ] Sem elementos extras (acessórios distractores)?
- [ ] Roupa não amassada?
- [ ] Rosto do modelo não cortado (se usar modelo)?
- [ ] Mínimo 4 fotos no listing?
- [ ] Foto original (sem violação de direitos autorais)?

---

## Integração com o Stack

```
┌──────────────┐
│   moda-ml    │ ← Compliance ML, fundo, enquadramento, proibições
├──────────────┤
│  ecommerce   │ ← Poses, modelo, composição (adaptado ao ML)
├──────────────┤
│     moda     │ ← Descrição da peça (tecido, construção, caimento)
├──────────────┤
│   realismo   │ ← Autenticidade (levers aplicados com moderação no ML)
└──────────────┘
```

**Quando `moda-ml` está ativa:**
- `ecommerce` → poses mais contidas (não movement extremo — o ML quer clareza)
- `realismo` → Level 3 (Natural Professional) — menos "casual phone" no ML
- `moda` → sem alteração, descrição de peça é universal
- **Fundo** → sempre liso digital, nunca cenário na capa
- **Composição** → quadrado 1:1, centralizado, 60-80%

**Quando NÃO usar `moda-ml`:**
- Se o destino for Shopee → usar `ecommerce` diretamente
- Se for conteúdo de redes sociais → usar `ecommerce` + `realismo`
- Se for vídeo → irrelevante (ML tem regras diferentes pra vídeo)
