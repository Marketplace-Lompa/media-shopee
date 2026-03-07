---
description: Comprimir imagens da pasta input para no máximo 2MB e salvar no output
---

# Comprimir Imagens (/comprimir)

Ao receber o comando `/comprimir`, executar o script de compressão nas imagens da pasta `input/`.

## Execução

// turbo
1. Rodar o script de compressão:
```bash
python3 /Users/lompa-marketplace/Documents/MEDIA-SHOPEE/compress_shopee.py
```

## Comportamento

- O script comprime todas as imagens (.jpg, .jpeg, .png, .webp) da pasta `input/`
- Limite máximo: **2MB** por imagem
- Qualidade inicial: **92%** (reduz em -5% até atingir o limite)
- Proporções e dimensões são **sempre preservadas**
- Após compressão bem-sucedida, o **original é removido** do `input/`
- Resultado salvo na pasta `output/`

## Após execução

- Informar ao usuário o resultado (quantas imagens comprimidas, tamanhos)
- Se nenhuma imagem for encontrada no `input/`, avisar o usuário
