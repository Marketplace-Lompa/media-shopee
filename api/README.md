# API — Scripts Diretos Google AI Studio

Este módulo contém scripts Python para **uso direto da API** do Google AI Studio, independente do Antigravity.

Use quando precisar:
- Gerar imagens com proporções específicas (9:16, 4:5, etc.) via linha de comando
- Testar modelos diretamente
- Automatizar geração em lote
- Integrar com outros sistemas

---

## Scripts disponíveis

| Script | Descrição | Uso |
|---|---|---|
| `gerar_imagem.py` | CLI para geração de imagens (Nano Banana 2 + Imagen 4) | `python gerar_imagem.py --help` |
| `gerar_video.py` | CLI para geração de vídeos (Veo 3.1) | `python gerar_video.py --help` |
| `analisa_fotos.py` | Análise de fotos de produtos | `python analisa_fotos.py` |
| `compress_shopee.py` | Compressão de imagens para Shopee | `python compress_shopee.py` |
| `download_shopee_images.py` | Download de imagens de anúncios | `python download_shopee_images.py` |
| `publicar_shopee.py` | Publicação automática na Shopee | `python publicar_shopee.py` |

---

## Pré-requisitos

```bash
# Instalar dependências
pip install google-genai pillow python-dotenv

# Configurar API Key no .env (raiz do projeto)
GOOGLE_AI_API_KEY=sua_chave
```

---

## Exemplos rápidos

```bash
# Gerar imagem 9:16 em 2K com Nano Banana 2
python api/scripts/gerar_imagem.py \
  --prompt "Modelo feminina brasileira, blusa branca, estúdio branco" \
  --proporcao 9:16 \
  --resolucao 2K

# Gerar vídeo 6s com Veo 3.1
python api/scripts/gerar_video.py \
  --prompt "Modelo caminhando em rua de São Paulo ao entardecer" \
  --duracao 6 \
  --proporcao 9:16
```

---

## Documentação da API

Ver pasta `api/docs/`:

| Arquivo | Conteúdo |
|---|---|
| `autenticacao.md` | Setup da API Key e configuração |
| `nano-banana.md` | **Referência completa do Nano Banana 2** ← modelo principal |
| `imagen4.md` | Imagen 4 (fotorrealismo avançado) |
| `veo.md` | Veo 3.1 (geração de vídeo) |
| `precos.md` | Comparativo de preços e estimativas |
