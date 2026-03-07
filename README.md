# MEDIA-SHOPEE — Hub de Geração de Mídia para Shopee

> Scripts, skills e configurações para criação de imagens e vídeos de produtos.  
> Repositório: [github.com/Marketplace-Lompa/media-shopee](https://github.com/Marketplace-Lompa/media-shopee)

---

## Estrutura do Projeto

```
MEDIA-SHOPEE/
│
├── .agent/                     # 🤖 ANTIGRAVITY — Skills, Workflows, Agentes
│   ├── agents/                 # Agentes customizados do Antigravity
│   ├── skills/                 # Skills especializadas
│   │   ├── ecommerce/          # Fotografia de e-commerce Shopee
│   │   ├── frames/             # Frames para interpolação de vídeo AI
│   │   ├── moda/               # Vocabulário têxtil e descrição de roupas
│   │   ├── moda-ml/            # Regras específicas para Mercado Livre
│   │   ├── realismo/           # Técnicas de fotorrealismo em AI image
│   │   └── shopee-publisher/   # Boas práticas de publicação na Shopee
│   └── workflows/              # Workflows de slash command
│       ├── comprimir.md        # /comprimir
│       ├── create-image.md     # /create-image
│       ├── criar-produto-shopee.md  # /criar-produto-shopee
│       ├── edit-image.md       # /edit-image
│       ├── puxar-foto-shopee.md    # /puxar-foto-shopee
│       └── shopee.md           # /shopee
│
├── api/                        # 🔌 API DIRETA — Scripts Python + Documentação
│   ├── scripts/                # Scripts Python para uso direto da API
│   │   ├── gerar_imagem.py     # CLI: gera imagem com Nano Banana 2 ou Imagen 4
│   │   ├── gerar_video.py      # CLI: gera vídeo com Veo 3.1
│   │   ├── analisa_fotos.py    # Análise automática de fotos de produtos
│   │   ├── compress_shopee.py  # Compressão de imagens (máx. 2MB Shopee)
│   │   ├── download_shopee_images.py  # Download de fotos de anúncios
│   │   └── publicar_shopee.py  # Publicação automática na Shopee
│   ├── docs/                   # Documentação técnica da API
│   │   ├── autenticacao.md     # Setup API Key e autenticação
│   │   ├── nano-banana.md      # ⭐ Referência completa Nano Banana 2
│   │   ├── imagen4.md          # Imagen 4 (fotorrealismo)
│   │   ├── veo.md              # Veo 3.1 (geração de vídeo)
│   │   └── precos.md           # Comparativo de preços
│   └── README.md               # Guia do módulo API
│
├── docs/                       # 📚 DOCUMENTAÇÃO GERAL
│   ├── decisoes/               # ADRs — Architecture Decision Records
│   │   └── modelo-padrao.md    # Decisão: Nano Banana 2 como modelo padrão
│   └── guias/                  # Guias de uso
│       └── prompts-shopee.md   # Guia de prompts para e-commerce Shopee
│
├── prompts/                    # 📝 Prompts salvos por produto
│   └── [produto].md
│
├── input/                      # 📥 Imagens de entrada (não versionado)
├── output/                     # 📤 Imagens/vídeos gerados (não versionado)
├── shopee_downloads/           # 📦 Downloads da Shopee (não versionado)
├── relatorios/                 # 📊 Relatórios gerados (não versionado)
│
├── .agent/                     # Antigravity (ver acima)
├── .env                        # 🔑 API Keys — NÃO commitar
├── .gitignore
├── produto-exemplo.json        # Estrutura de exemplo de produto
├── nano-banana-pro-guia.md     # Guia legado Nano Banana Pro
└── antigravity-skills-guia.md  # Guia de skills do Antigravity
```

---

## Dois Mundos Separados

### 🤖 Módulo Antigravity `.agent/`
Funciona **dentro do Antigravity IDE**. Use com slash commands:

| Comando | O que faz |
|---|---|
| `/shopee` | Gera 3 prompts (hero, medium, macro) para um produto |
| `/create-image` | Cria prompt novo do zero para uma imagem |
| `/edit-image` | Edita imagem existente (muda pose, cenário, cor) |
| `/comprimir` | Comprime imagens da pasta `input/` para máx. 2MB |
| `/criar-produto-shopee` | Fluxo completo: analisa fotos → cria anúncio na Shopee |
| `/puxar-foto-shopee` | Baixa fotos de um anúncio existente |

### 🔌 Módulo API `api/`
Scripts Python para **uso direto fora do Antigravity**:

```bash
# Gerar imagem 9:16
python api/scripts/gerar_imagem.py \
  --prompt "Sua descrição aqui" \
  --proporcao 9:16 \
  --resolucao 2K

# Ver todos os parâmetros
python api/scripts/gerar_imagem.py --help
```

---

## Modelo Padrão

**`gemini-3.1-flash-image-preview` (Nano Banana 2)**

Escolhido por: velocidade (4–6s), custo ($0.067/img), qualidade (95% do Pro) e recursos exclusivos (Grounding Search + Thinking Mode).

→ Ver decisão completa em [`docs/decisoes/modelo-padrao.md`](docs/decisoes/modelo-padrao.md)  
→ Ver referência técnica em [`api/docs/nano-banana.md`](api/docs/nano-banana.md)

---

## Setup Rápido

```bash
# 1. Configurar API Key
echo "GOOGLE_AI_API_KEY=sua_chave" > .env

# 2. Instalar dependências
pip install google-genai pillow python-dotenv

# 3. Testar
python api/scripts/gerar_imagem.py \
  --prompt "Modelo feminina, blusa branca, estúdio" \
  --proporcao 9:16
```
