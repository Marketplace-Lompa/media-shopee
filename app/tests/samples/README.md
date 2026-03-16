# Samples de produto para testes

Cada subpasta representa um produto real usado como referência nos testes de pipeline.

```
samples/
  nome-do-produto/
    foto1.jpg
    foto2.jpg
    ...
```

## Como usar

```bash
# Triage rápida (sem chamada de API de geração)
python app/tests/test_pipeline_fixture.py --product poncho-ruana-listras

# Geração completa (chama API Gemini — pare o servidor antes)
python app/tests/test_pipeline_fixture.py --product poncho-ruana-listras --generate
```

## Regras

- Coloque apenas fotos **brutas do produto** (input), sem resultados gerados
- Resultados gerados ficam em `app/tests/output/`
- Para adicionar produto novo: crie pasta com nome em kebab-case e jogue as fotos dentro

## Produtos disponíveis

| Pasta | Descrição | Fotos |
|---|---|---|
| `poncho-ruana-listras/` | Poncho-ruana crochê, listras olive green + rosa blush | 10 product shots + 8 styled |
