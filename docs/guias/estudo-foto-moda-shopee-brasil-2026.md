# Estudo Consolidado — Melhores Práticas de Foto de Moda para Shopee Brasil (2026)

Data: 2026-03-15  
Escopo: consolidar regras oficiais da Shopee, sinais recentes de mercado e aprendizados práticos já validados neste repositório.

## 1. Resumo executivo

Este estudo confirma que, para Shopee (moda), performance visual depende de duas camadas:

1. Compliance de anúncio (capa, clareza de produto, anti-spam/anti-duplicidade, direitos de imagem).
2. Qualidade comercial da galeria (sequência visual que reduz dúvida de tamanho/tecido/caimento no mobile).

No contexto do projeto MEDIA-SHOPEE, os testes internos já convergem com esse padrão: 
- linguagem “Shopee” performou melhor no teste prompt-only,
- fidelidade de tecido/peça tende a ficar melhor com `thinking MINIMAL` em baseline,
- prompts com “catalog cover, standing pose, garment fully visible” aumentam legibilidade comercial.

## 2. Documentos já existentes no projeto (consolidados neste estudo)

1. [docs/guias/prompts-shopee.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/prompts-shopee.md)
2. [docs/learnings/validacao-prompt-only-marketplace.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/learnings/validacao-prompt-only-marketplace.md)
3. [docs/learnings/diagnostico-pratico-fidelidade-roupa-referencia.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/learnings/diagnostico-pratico-fidelidade-roupa-referencia.md)
4. [docs/reports/pipeline-v2-prod-readiness.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/reports/pipeline-v2-prod-readiness.md)
5. [prompts/blusa-tricot-gola-alta.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/prompts/blusa-tricot-gola-alta.md)

## 3. Regras oficiais Shopee mais relevantes para fotos (base para regra de negócio)

Observação: parte dos materiais oficiais públicos ainda está em docs históricos globais/região, mas continuam coerentes com validações atuais de moderação/listing.

### 3.1 Regras de capa e imagens (alto nível de confiança)

- Capa com fundo branco.
- Capa com produto único (evitar múltiplos produtos empilhados/composição confusa).
- Produto ocupando boa parte do quadro (regra de 70%+ aparece explicitamente em material oficial).
- Imagem nítida, sem pixelação, com cor realista do produto.
- Evitar texto promocional agressivo na capa.
- Usar múltiplas imagens com ângulos diferentes para representar o produto de forma fiel.

### 3.2 Regras de violação que impactam foto/listagem (alto nível de confiança)

- Duplicidade de anúncio com pequenas mudanças de foto/título/descrição é passível de remoção/punição.
- Uso indevido de imagem de terceiros (copyright/IP) é passível de banimento/remoção.
- “Switched listing” (trocar o item vendido reaproveitando anúncio) é considerado violação.

### 3.3 Produtos adultos/moda íntima sensível (alto nível de confiança)

- Para produtos adultos em geral: capa focada no produto, sem sugestão sexual.
- Para moda relacionada a bem-estar sexual: modelo na capa pode ser permitido, desde que postura neutra e sem sugestão sexual.

## 4. Achados recentes de mercado e UX aplicáveis à Shopee BR

### 4.1 Contexto Brasil (médio-alto)

- Moda segue entre as verticais mais relevantes de e-commerce no Brasil.
- Troca/devolução por tamanho e percepção de material continua sendo uma dor importante.

Implicação prática: galeria de imagens deve ser desenhada para reduzir incerteza de medida e textura, não só para “ficar bonita”.

### 4.2 UX de produto (alto)

Pesquisas de UX e-commerce mostram que usuários exploram imagem logo no início da PDP e dependem de zoom/escala/contexto para decidir. Em moda isso se traduz em:

- ao menos 1 imagem “em escala” (on-model ou comparação de proporção),
- detalhe de tecido/costura que comprove qualidade real,
- consistência de cor entre fotos.

## 5. Playbook recomendado para Shopee Moda Brasil

### 5.1 Sequência ideal de galeria (9 imagens)

1. Capa: fundo branco, peça principal clara, sem ruído, foco comercial.
2. Frente completa da peça (ou on-model frontal neutra).
3. Costas/lateral para modelagem.
4. Close de tecido/trama/costura.
5. On-model com caimento estático (postura neutra).
6. On-model com leve movimento (drape/fluidez).
7. Detalhes funcionais (gola, punho, zíper, forro, transparência).
8. Variações de cor reais e consistentes.
9. Tabela de medidas legível (cm), com instrução simples de medição.

### 5.2 Regras práticas de produção

- Capa deve priorizar leitura instantânea no mobile.
- Não esconder parte crítica da peça por pose, cabelo, bolsa, braço ou cenário.
- Evitar pós-processamento que altere cor real do produto.
- Manter padrão de iluminação e WB entre variações da mesma SKU.
- Texto na imagem apenas quando realmente necessário e sem poluir capa.

## 6. Tradução para regras de negócio do MEDIA-SHOPEE

### 6.1 Hard rules (bloqueio)

1. `cover_background != white` -> bloquear publicação.
2. `cover_has_multiple_primary_products == true` -> bloquear.
3. `cover_product_occupancy < 0.70` -> bloquear.
4. `image_sharpness < limiar_min` -> bloquear.
5. `suspected_third_party_image_misuse == true` -> bloquear para revisão manual.

### 6.2 Soft rules (score de qualidade)

1. Possui foto de textura macro.
2. Possui foto de costas/lateral.
3. Possui foto on-model neutra.
4. Possui foto de detalhe funcional.
5. Possui tabela de medidas.
6. Consistência de cor entre imagens da variação.

Score sugerido:
- `>= 85`: pronto para publicação,
- `70-84`: publicar com alerta,
- `< 70`: retornar para nova geração/edição.

## 7. Convergência com evidências internas do projeto

- [docs/learnings/validacao-prompt-only-marketplace.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/learnings/validacao-prompt-only-marketplace.md): variante “Shopee” teve melhor equilíbrio impacto + legibilidade.
- [docs/learnings/diagnostico-pratico-fidelidade-roupa-referencia.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/learnings/diagnostico-pratico-fidelidade-roupa-referencia.md): `MINIMAL` ganhou em fidelidade de textura em benchmark controlado.
- [docs/reports/pipeline-v2-prod-readiness.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/reports/pipeline-v2-prod-readiness.md): `fidelity_mode=estrita` + pose legível + gate visual reduzem drift estrutural.
- [docs/guias/prompts-shopee.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/prompts-shopee.md): framework de HERO/MEDIUM/MACRO já alinhado ao comportamento de conversão em moda.

## 8. Limitações e nível de confiança

- Alto: regras de imagem/violação validadas em materiais oficiais Shopee (Seller CMS / guides).
- Médio: detalhes de rollout por país/categoria (ex.: exigências operacionais específicas de tabela de medidas) podem variar por mercado e data.
- Recomendação operacional: validar mensalmente no Seller Center da conta BR ativa antes de alterar automações de bloqueio.

## 9. Fontes externas usadas

### Shopee (oficial / documentação)

1. Listing Requirements (Seller CMS PDF):  
   https://cdngarenanow-a.akamaihd.net/shopee/seller/seller_cms/d38d33a37423e15adf187c2b33b81813/OS%20Listing%20Requirements_07182019%20%281%29.pdf
2. Listing Violations Guide (Seller CMS PDF):  
   https://cdngarenanow-a.akamaihd.net/shopee/seller/seller_cms/36dc0889da6953d419c5e63c65b16853/Listing%20violations%20guide.pdf
3. Common Listing Violations (Seller CMS PDF):  
   https://cdngarenanow-a.akamaihd.net/shopee/seller/seller_cms/f0d8d82ba8367d826b5c294eb5d0c991/Common%20listing%20violations.pdf
4. Diretrizes para anúncios de produtos adultos na Shopee (PT-BR, Seller CMS PDF):  
   https://cdngarenanow-a.akamaihd.net/shopee/seller/seller_cms/95af77b7d697edb5b07a0e65493f05a5/Diretrizes%20para%20An%C3%BAncios%20de%20Produtos%20Adultos%20na%20Shopee.pdf

### UX / e-commerce research

5. Baymard — image resolution and zoom behavior:  
   https://baymard.com/blog/ensure-sufficient-image-resolution-and-zoom
6. Baymard — in-scale image necessity:  
   https://baymard.com/blog/in-scale-product-images
7. Shopify Help — product photography fundamentals:  
   https://help.shopify.com/en/manual/products/product-media/product-photography

### Contexto Brasil (mercado)

8. E-Commerce Brasil — trocas/devoluções 2024:  
   https://www.ecommercebrasil.com.br/noticias/em-2024-60-das-trocas-e-devolucoes-no-e-commerce-foram-realizadas-em-ate-sete-dias
9. E-Commerce Brasil — crescimento moda 2025 (pub. 2026):  
   https://www.ecommercebrasil.com.br/noticias/setor-de-moda-cresce-35-no-e-commerce-brasileiro-em-2025

---

## 10. Próxima ação sugerida

Transformar este estudo em três artefatos de produto:

1. `policy_schema` versionado (hard rules + soft rules).
2. `validator` automático para bloqueio/score em lote.
3. `template pack` de prompts por categoria (malha, jeans, fitness, íntima), já aderente às regras acima.
