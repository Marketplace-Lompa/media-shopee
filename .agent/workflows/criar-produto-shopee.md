---
description: Cria um anúncio completo na Shopee Seller Center a partir de uma pasta de fotos — analisa cores, organiza imagens e publica automaticamente.
---

# /criar-produto-shopee

Ao receber o comando `/criar-produto-shopee`, execute o fluxo abaixo para criar um anúncio na Shopee usando o Chrome já logado.

---

## Pré-requisitos

- Python 3 com `playwright`, `Pillow`, `scikit-learn` e `numpy` instalados
- Chrome já aberto com debugging port (ver Etapa 0)
- Sessão da Shopee Seller Center ativa no Chrome

```bash
# Instalar dependências (uma vez apenas)
pip3 install scikit-learn Pillow numpy playwright
python3 -m playwright install chromium
```

---

## Etapa 0 — Abrir Chrome com Debugging (usuário executa uma vez)

Feche o Chrome normal e execute:

```bash
open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="/Users/lompa-marketplace/Library/Application Support/Google/Chrome/Default"
```

Depois navegue para `https://seller.shopee.com.br` e confirme que está logado.

---

## Etapa 1 — Verificar configuração do produto

O usuário fornece:
1. **Pasta com as fotos brutas** (ex: `/Users/lompa/fotos/camiseta-nova/`)
2. **Arquivo `produto.json`** com dados do anúncio

Se o `produto.json` não existir, **crie um com os dados fornecidos pelo usuário** usando o template em `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/produto-exemplo.json`.

Certifique-se que o campo `pasta_fotos` aponta para a pasta correta.

---

## Etapa 2 — Analisar e organizar fotos por cor

// turbo
```bash
python3 /Users/lompa-marketplace/Documents/MEDIA-SHOPEE/analisa-fotos.py "<PASTA_FOTOS>"
```

Após rodar, leia o arquivo `relatorio.json` gerado na pasta e **mostre ao usuário** as cores detectadas e a quantidade de fotos por cor, no formato:

```
📊 Cores detectadas:
  🎨 vermelho  → 4 fotos
  🎨 preto     → 6 fotos
  🎨 azul      → 3 fotos

Deseja criar anúncios para TODAS as cores ou apenas uma específica?
```

Aguarde confirmação do usuário sobre quais cores publicar.

---

## Etapa 3 — Dry Run (inspeção sem salvar)

Para cada cor confirmada, execute primeiro em modo dry-run:

```bash
python3 /Users/lompa-marketplace/Documents/MEDIA-SHOPEE/publicar-shopee.py \
  --config "<CAMINHO_PRODUTO_JSON>" \
  --cor "<COR>" \
  --dry-run
```

Informe ao usuário o caminho dos screenshots em `/tmp/shopee-audit/` para que possa revisar.

---

## Etapa 4 — Criar rascunho (com confirmação)

Após aprovação do dry-run, execute para cada cor:

```bash
python3 /Users/lompa-marketplace/Documents/MEDIA-SHOPEE/publicar-shopee.py \
  --config "<CAMINHO_PRODUTO_JSON>" \
  --cor "<COR>"
```

> ⚠️ Este comando **SALVA COMO RASCUNHO**. O anúncio não fica público até o usuário publicar manualmente na Seller Center.

---

## Etapa 5 — Publicar (opcional, requer confirmação explícita)

Somente se o usuário solicitar explicitamente:

```bash
python3 /Users/lompa-marketplace/Documents/MEDIA-SHOPEE/publicar-shopee.py \
  --config "<CAMINHO_PRODUTO_JSON>" \
  --cor "<COR>" \
  --publicar
```

---

## Etapa 6 — Resumo Final

Ao concluir, informe:
- Quantos rascunhos/anúncios foram criados
- Caminho dos screenshots de auditoria
- Próximos passos sugeridos (revisar rascunhos, preencher atributos faltantes, etc.)

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| `Não foi possível conectar ao Chrome` | Verificar se o Chrome está aberto com `--remote-debugging-port=9222` |
| `Pasta de fotos para 'X' não encontrada` | Executar a Etapa 2 antes da Etapa 3 |
| Campo não encontrado na Seller Center | A Shopee pode ter atualizado a UI — executar com `--debug` e enviar screenshot |
| Foto não faz upload | Verificar se a foto tem ≤ 2MB (usar `/comprimir` se necessário) |
