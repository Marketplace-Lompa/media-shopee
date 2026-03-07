---
description: Baixa imagens de um anúncio da Shopee via Playwright headless e salva em pasta separada por produto.
---

# Puxar Foto Shopee

Ao receber o comando `/puxar-foto-shopee` acompanhado de uma URL de anúncio da Shopee, execute o fluxo completo: download das imagens + geração de prompt para o Nano Banana Pro.

## Pré-requisitos

- Python 3 + `playwright` + `requests` instalados
- Chromium headless instalado (`python3 -m playwright install chromium`)

## Fluxo

1. O usuário fornece a URL do anúncio da Shopee (ex: `https://shopee.com.br/...-i.123456.789012`)

// turbo
2. Execute o script de download:
```bash
python3 /Users/lompa-marketplace/Documents/MEDIA-SHOPEE/download_shopee_images.py '<URL_DO_ANUNCIO>'
```

3. As imagens serão salvas automaticamente em:
```
/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/shopee_downloads/<item_id>/
```

4. Após o download, informe ao usuário quantas imagens foram salvas e o caminho da pasta.

5. **Automaticamente**, analise as imagens salvas na pasta do produto (visualize pelo menos 3 fotos representativas) e execute o workflow `/edit-image` para gerar o prompt do Nano Banana Pro baseado na roupa das fotos.

## Observações

- O script roda 100% em background (headless), sem abrir janela.
- Imagens menores que 50KB (ícones/thumbnails) são removidas automaticamente.
- Se o Playwright não estiver instalado, rode antes:
```bash
pip3 install --break-system-packages playwright requests
python3 -m playwright install chromium
```
