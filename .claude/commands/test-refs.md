# test-refs — Referências de teste do projeto

Quando invocado, liste os produtos disponíveis em `app/tests/samples/` e retorne os caminhos para uso em testes.

## Estrutura

```
app/tests/samples/          ← referências brutas de produto
  poncho-ruana-listras/
    IMG_*.jpg               ← fotos brutas do produto (usadas como input do pipeline)
    styled_*.jpeg           ← editoriais/inspiração (NÃO entram no pipeline)

app/tests/output/           ← imagens geradas pelos testes
  gen_*.png
```

## Passos

1. Liste as subpastas de `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/samples/`
2. Para cada produto, liste apenas os arquivos `IMG_*` (referências brutas)
3. Ignore `styled_*` e `gen_*` — esses não devem ser passados como input ao pipeline
4. Retorne os caminhos absolutos prontos para uso em scripts de teste

O pipeline (`reference_selector`) faz a curadoria automaticamente — basta passar os `IMG_*` da pasta do produto.

## Script de teste

```bash
# Triage rápida (sem geração, seguro com servidores ativos)
python app/tests/test_pipeline_fixture.py

# Geração completa (pare os servidores antes)
python app/tests/test_pipeline_fixture.py --generate

# Produto específico
python app/tests/test_pipeline_fixture.py --product poncho-ruana-listras
```

## Uso

`/test-refs` → mostra todos os produtos disponíveis com seus caminhos de input
`/test-refs poncho` → filtra pelo produto especificado
