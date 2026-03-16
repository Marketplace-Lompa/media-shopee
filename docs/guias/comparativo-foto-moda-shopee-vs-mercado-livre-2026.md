# Comparativo — Regras de Foto de Moda: Shopee vs Mercado Livre (Brasil, 2026)

Data: 2026-03-15  
Base: consolidação dos estudos internos e pesquisa web oficial recente.

Documentos-base:
1. [Shopee](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/estudo-foto-moda-shopee-brasil-2026.md)
2. [Mercado Livre](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/estudo-foto-moda-mercado-livre-brasil-2026.md)

## 1. Diferenças principais (executivo)

1. Shopee tende a ser mais rígida em capa “limpa” com fundo branco e leitura objetiva do produto.
2. Mercado Livre está mais segmentado por subcategoria: em parte da moda aceita/estimula contexto real; em outras mantém fundo neutro/digitalizado.
3. No ML, regra de foto em moda é mais dependente da categoria da variação; na Shopee a regra tende a ser mais uniforme por marketplace.

## 2. Tabela objetiva de diferenças

| Tema | Shopee (Moda) | Mercado Livre (Moda) | Impacto de implementação |
|---|---|---|---|
| Política de fundo na capa | Predominância de fundo branco e capa limpa | Híbrida por subcategoria (algumas aceitam contexto/textura, outras pedem neutro) | ML precisa resolver política por subcategoria |
| Nível de padronização | Mais homogêneo no marketplace | Mais granular por categoria | Necessário `policy resolver` por canal+categoria |
| Protagonismo do produto | Alto, com ocupação elevada do frame | Alto, com orientação explícita de protagonista e ocupação alta | Comum aos dois |
| Elementos proibidos (logo, QR, contato, promo) | Proibidos/fortemente desaconselhados | Proibidos/fortemente desaconselhados | Regra shared cross-channel |
| Regras por variação | Importante | Crítico (capa por variação e qualidade da variação) | Validador por variação nos dois, mais rígido no ML |
| Contexto/lifestyle | Permitido, mas sem perder leitura comercial | Permitido em várias subcategorias de moda (não universal) | No ML, contexto depende da categoria |
| Risco operacional | Drift de fidelidade visual da peça | Não conformidade por aplicar “fundo único” em categoria errada | Estratégias de mitigação diferentes |

## 3. O que é igual nos dois canais

1. Produto precisa ser claramente o foco da imagem.
2. Imagem precisa ser nítida, sem pixelização e sem distorção grosseira.
3. Não usar elementos visuais que pareçam spam (texto promocional, contato, QR, bordas agressivas).
4. Não usar foto sem direito de uso.
5. Galeria com múltiplos ângulos/detalhes tende a melhorar confiança e reduzir devolução.

## 4. Onde cada canal exige cuidado específico

## 4.1 Shopee

- Evitar qualquer desvio de capa limpa e leitura rápida mobile.
- Foco em consistência de catálogo com forte governança visual.

## 4.2 Mercado Livre

- Não aplicar regra universal de fundo para toda moda.
- Decisão de fundo/composição deve ser derivada da subcategoria.
- Em categorias com requisito específico (ex.: packs, calçados, íntima/praia, acessórios), validar perfil antes de gerar/publicar.

## 5. Recomendação de arquitetura única (multi-canal)

## 5.1 Camada de políticas

Criar um resolvedor:
- `policy = resolve_photo_policy(channel, category_id, variation_context)`

Saída mínima:
- `background_policy`
- `cover_layout_policy`
- `forbidden_overlays`
- `required_shots`
- `min_quality_threshold`

## 5.2 Camada de validação

Executar antes da publicação:
1. `hard_fail_rules` (bloqueio).
2. `soft_score_rules` (qualidade/completude da galeria).
3. `channel_specific_exceptions`.

## 5.3 Camada de prompting

- Prompt base compartilhado de fidelidade de peça.
- Prompt de composição separado por canal/categoria.
- Nunca misturar “fundo obrigatório branco” em categorias ML que explicitamente aceitam contexto.

## 6. Matriz de regra de negócio sugerida

## 6.1 Shared hard rules

1. `contains_logo_or_watermark_or_qr_or_contact == true` -> bloquear.
2. `product_not_fully_visible == true` -> bloquear.
3. `image_blur_or_low_resolution == true` -> bloquear.
4. `copyright_risk == high` -> revisão manual obrigatória.

## 6.2 Shopee hard additions

1. `cover_background != white` -> bloquear (quando regra da conta/categoria exigir capa branca).
2. `cover_product_occupancy < threshold_shopee` -> bloquear.

## 6.3 Mercado Livre hard additions

1. `subcategory_background_policy_violation == true` -> bloquear.
2. `variation_cover_missing_or_invalid == true` -> bloquear.

## 7. Risco de erro mais comum

1. Aplicar template Shopee no ML sem ajuste por subcategoria.
2. Aplicar template ML contextual em fluxo Shopee que pede capa mais clean/white.
3. Reutilizar os mesmos assets sem validação de regra por canal.

## 8. Prioridade de implementação

1. Implementar `photo_policy_resolver` por canal/categoria.
2. Implementar `validator` com bloqueios + score.
3. Versionar templates de prompt por canal (`shopee`, `ml`) e por família de categoria.

## 9. Referências

- Shopee study: [estudo-foto-moda-shopee-brasil-2026.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/estudo-foto-moda-shopee-brasil-2026.md)
- Mercado Livre study: [estudo-foto-moda-mercado-livre-brasil-2026.md](/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/guias/estudo-foto-moda-mercado-livre-brasil-2026.md)
