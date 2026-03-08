# MEDIA-SHOPEE — Hub de Mídia para Marketplace

Scripts, skills e aplicação local para geração de imagens/vídeos de produtos (Shopee e similares).

---

## Visão geral

Este repositório tem **dois modos de operação**:

1. **Ferramenta de prompt (manual)**
Use skills/workflows para montar prompts e executar manualmente em plataformas como AI Studio, Nano e Veo.

2. **Plataforma via API (automatizada)**
Use scripts Python e o Studio Local (`app/`) para geração reproduzível e operação em lote.

Guia recomendado: [`docs/guias/modos-do-projeto.md`](docs/guias/modos-do-projeto.md)

---

## Estrutura principal

```text
MEDIA-SHOPEE/
├── .agent/                     # Skills e workflows para uso manual
├── api/                        # Scripts Python + documentação técnica
│   ├── scripts/
│   └── docs/
├── app/                        # Studio Local (frontend + backend)
│   ├── backend/
│   └── frontend/
├── docs/
│   ├── decisoes/
│   ├── guias/
│   └── learnings/
├── prompts/                    # Prompts salvos
├── input/ output/              # Entrada/saída de mídia (não versionado)
└── shopee_downloads/ relatorios/
```

---

## Quickstart

### Pré-requisito comum

```bash
echo "GOOGLE_AI_API_KEY=sua_chave" > .env
```

### A) Modo manual (prompt tooling)

1. Use as skills em `.agent/skills/` e workflows em `.agent/workflows/`.
2. Salve prompts aprovados em `prompts/`.
3. Leve os prompts para execução manual na plataforma de geração.

Referência: [`docs/guias/prompts-shopee.md`](docs/guias/prompts-shopee.md)

### B) Modo API (scripts)

```bash
pip install google-genai pillow python-dotenv
python api/scripts/gerar_imagem.py --help
python api/scripts/gerar_video.py --help
```

Referência: [`api/README.md`](api/README.md)

### C) Modo plataforma local (Studio)

Backend:
```bash
pip install -r app/backend/requirements.txt
uvicorn app.backend.main:app --reload --port 8000
```

Frontend:
```bash
npm -C app/frontend install
npm -C app/frontend run dev
```

Acesse `http://localhost:5173`.

---

## Documentação chave

- Arquitetura de modos: [`docs/guias/modos-do-projeto.md`](docs/guias/modos-do-projeto.md)
- Guia de prompts: [`docs/guias/prompts-shopee.md`](docs/guias/prompts-shopee.md)
- Decisão de modelo padrão: [`docs/decisoes/modelo-padrao.md`](docs/decisoes/modelo-padrao.md)
- API scripts: [`api/README.md`](api/README.md)
- Preços (snapshot): [`api/docs/precos.md`](api/docs/precos.md)
- Veo: [`api/docs/veo.md`](api/docs/veo.md)

---

## Segurança

- `.env` é obrigatório e não deve ser commitado.
- Em caso de exposição de chave, rotacione imediatamente no AI Studio.
