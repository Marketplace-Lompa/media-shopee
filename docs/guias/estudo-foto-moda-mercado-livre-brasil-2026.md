# Estudo Consolidado — Melhores Práticas de Foto de Moda para Mercado Livre Brasil (2026)

Data: 2026-03-15  
Escopo: consolidar requisitos oficiais recentes do Mercado Livre para fotos de moda, mapear particularidades por subcategoria e traduzir em regras de negócio aplicáveis ao MEDIA-SHOPEE.

## 1. Resumo executivo

O Mercado Livre Brasil está mais granular que a Shopee em regras de imagem para moda:

1. A política muda por subcategoria (ex.: calçados, packs, acessórios, roupa íntima/praia).
2. A capa é avaliada por variação e continua crítica para posicionamento.
3. Em moda, parte das subcategorias já aceita ou incentiva contexto visual (fundos com textura/lisos reais), enquanto outras ainda mantêm orientação de fundo neutro digital.

Implicação direta: não existe uma única regra visual de moda para todo o ML. A operação precisa de validação por subcategoria.

## 2. O que já existe no projeto e entra neste estudo

1. [docs/guias/estudo-foto-moda-shopee-brasil-2026.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/estudo-foto-moda-shopee-brasil-2026.md)
2. [docs/guias/prompts-shopee.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/prompts-shopee.md)
3. [docs/learnings/validacao-prompt-only-marketplace.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/learnings/validacao-prompt-only-marketplace.md)
4. [docs/pipeline-v2-prod-readiness.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/pipeline-v2-prod-readiness.md)

Observação: o repositório tem muito material técnico de fidelidade visual e pouco conteúdo formal de regra de imagem do ML, então este documento fecha essa lacuna.

## 3. Regras oficiais do Mercado Livre com maior impacto em moda

## 3.1 Regras transversais (aplicam amplamente)

- Use somente fotos do produto anunciado.
- Evite inserir logo, marca d'água, borda, QR code, contato, instruções de envio ou textos promocionais.
- Não usar fotos de terceiros sem autorização (risco de denúncia por direitos autorais e pausa do anúncio).
- Produto precisa ser protagonista e estar totalmente visível.

## 3.2 Regras de composição e resolução (diretrizes recorrentes)

- Centralização forte do produto (guides mencionam ocupação alta do frame, com referência de ~95%).
- Imagens com lados equivalentes (quadradas ou proporção semelhante) em diretrizes gerais.
- Mínimo técnico recorrente de 500x500 e recomendação de 1200x1200 para zoom em guias gerais.

## 3.3 Particularidades de moda por subcategoria (ponto-chave)

Com base nos guias recentes da Central de Vendedores:

1. `Calçados`: tende a pedir fundo neutro (branco/creme/cinza claro) e planos específicos (superior/frontal, sola/traseira).
2. `Packs`: orienta fundo digitalizado neutro e traz especificação própria (ex.: vertical 1200x1540 em orientação do guia de packs).
3. `Acessórios` e `Roupa íntima/praia`: aceita contexto com textura ou fundo liso real em tons neutros; alguns guias desaconselham fundo branco digitalizado nessas peças.
4. `Vestidos/macacões` e outras peças: reforça uso de modelo real ou manequim invisível, mantendo foco integral na peça e sem distrações.
5. Fotos complementares: em moda, há recomendação de múltiplos ângulos e detalhe; em alguns guias aparece limite de até 10 fotos por variação.

## 3.4 Mudança estrutural relevante do ML

Guia oficial recente do ML indica transição para fotos em contexto em várias categorias, mantendo fundo branco obrigatório ainda em algumas verticais (citadas explicitamente: Tecnologia, Beleza, Saúde e Supermercado).

Implicação: moda fica em regime híbrido, com maior liberdade visual que marketplaces mais rígidos na capa.

## 4. Playbook recomendado para Moda no Mercado Livre BR

## 4.1 Sequência de fotos por variação

1. Capa da variação: protagonista absoluto, sem ruído, conforme regra específica da subcategoria.
2. Frente com leitura completa da peça.
3. Costas/lateral para modelagem.
4. Detalhe de tecido/costura.
5. Detalhe funcional (gola, barra, fechamento, forro, elástico).
6. Contexto de uso controlado (quando a subcategoria permitir).

## 4.2 Estratégia de fundo (decisão crítica)

- Não aplicar regra única para toda moda.
- Decidir por `background_policy` via subcategoria:
  - `neutral_digital` (quando a subcategoria pede fundo digitalizado claro).
  - `neutral_real_or_textured_light` (quando a subcategoria permite contexto e fundo real/texturizado leve).

## 4.3 Padrão de qualidade visual

- Não cortar produto, não encostar em bordas.
- Não esconder peça com cabelo/braços/acessórios não vendidos.
- Evitar edição que distorça cor/material real.
- Preservar coerência entre variações do mesmo anúncio.

## 5. Tradução para regra de negócio do MEDIA-SHOPEE (ML)

## 5.1 Hard rules (bloqueio)

1. `contains_logo_or_watermark_or_qr_or_contact == true` -> bloquear.
2. `product_not_fully_visible == true` -> bloquear.
3. `product_not_protagonist == true` -> bloquear.
4. `copyright_risk == high` -> bloquear para revisão manual.
5. `subcategory_background_policy_violation == true` -> bloquear.

## 5.2 Soft rules (score)

1. Foto de costas/lateral presente.
2. Foto macro de material presente.
3. Foto de detalhe funcional presente.
4. Coerência de cor entre variações.
5. Sequência completa por variação.

Sugestão de score:
- `>= 85`: pronto para publicação.
- `70-84`: publicar com alerta.
- `< 70`: retornar para ajuste.

## 6. Pontos de atenção para arquitetura

1. O validador de ML precisa ser orientado por subcategoria, não por marketplace apenas.
2. O pipeline de geração deve aceitar `photo_policy_profile` dinâmico por categoria da variação.
3. O fallback para fundo branco universal em moda pode gerar não conformidade em subcategorias que pedem contexto realista.

## 7. Limitações e nível de confiança

- Alto: diretrizes de higiene visual e proibição de elementos extras (logo, watermark, QR, contato etc.).
- Médio-alto: variação de fundo e formato por subcategoria de moda (confirmada em guias recentes, mas com mudanças contínuas).
- Médio: detalhes finos de tamanho/formato podem ser atualizados com frequência por módulo/categoria.

Nota técnica: várias páginas oficiais do ML bloqueiam scraping direto (403), então a coleta usou snippets recentes indexados das URLs oficiais da Central de Vendedores.

## 8. Fontes externas (Mercado Livre e apoio)

### Mercado Livre — oficiais

1. Fotos de qualidade (Central de Vendedores):  
   https://vendedores.mercadolivre.com.br/nota/fotos-de-qualidade-o-segredo-para-se-destacar-e-vender-mais
2. Fotos são o cartão de visita (Central de Vendedores):  
   https://vendedores.mercadolivre.com.br/nota/fotos-sao-o-cartao-de-visita-dos-seus-negocios-destaque-se
3. Requisitos de fotos para vender Packs:  
   https://vendedores.mercadolivre.com.br/nota/requisitos-de-fotos-para-vender-packs
4. Requisitos de fotos para Calçados:  
   https://vendedores.mercadolivre.com.br/nota/requisitos-de-fotos-para-calcados
5. Requisitos de fotos para Acessórios:  
   https://vendedores.mercadolivre.com.br/nota/requisitos-de-fotos-para-vender-acessorios
6. Requisitos de fotos para Roupa íntima e de praia:  
   https://vendedores.mercadolivre.com.br/nota/requisitos-de-fotos-para-roupa-intima-e-de-praia
7. Requisitos de fotos para Vestidos e macacões:  
   https://vendedores.mercadolivre.com.br/nota/requisitos-de-fotos-para-vestidos-e-macacoes
8. Hub moda e requisitos por peça:  
   https://vendedores.mercadolivre.com.br/nota/fotos-de-moda-melhore-suas-fotos-e-venda-mais
9. Diretriz geral de infrações em fotos (Ajuda):  
   https://www.mercadolivre.com.br/ajuda/fotos-na-pagina-principal_1024

### UX / conversão (apoio de mercado)

10. Baymard — zoom/resolução em PDP:  
    https://baymard.com/blog/ensure-sufficient-image-resolution-and-zoom
11. Baymard — imagem em escala real:  
    https://baymard.com/blog/in-scale-product-images

## 9. Próximos passos sugeridos

1. Criar `ml_photo_policy_by_subcategory.json` com perfis de fundo/composição por categoria.
2. Implementar `pre_publish_validator_ml` com bloqueios e score.
3. Adicionar testes de regressão visual por subcategoria (calçados, packs, acessórios, íntima/praia).
