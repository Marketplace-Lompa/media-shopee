# Autenticação e Configuração — Google AI Studio API

> Atualizada em: Março/2026

---

## Visão Geral

Existem **dois caminhos** para usar a API do Google AI Studio:

| Caminho | Quando usar | Custo |
|---|---|---|
| **API Key (Gemini API)** | Desenvolvimento, free tier, projetos pessoais | Grátis até limite |
| **Service Account (Vertex AI)** | Produção, billing avançado, volume alto | Pay-per-use |

Para o uso deste projeto (Shopee/e-commerce), **API Key** é suficiente.

---

## Obtendo a API Key

1. Acesse 👉 [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Clique em **"Create API Key"**
3. Selecione ou crie um projeto Google Cloud
4. Copie a chave gerada

> ⚠️ **Nunca** commite a chave no repositório. Use sempre variáveis de ambiente.

---

## Configuração do Projeto

### Arquivo `.env`

```env
GOOGLE_AI_API_KEY=sua_chave_aqui
```

### Instalação das dependências

```bash
pip install google-genai pillow python-dotenv
```

### Inicialização padrão (todos os scripts)

```python
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
```

---

## Variáveis de Ambiente Disponíveis

| Variável | Descrição | Obrigatória |
|---|---|---|
| `GOOGLE_AI_API_KEY` | Chave da API do Google AI Studio | ✅ Sim |
| `GOOGLE_CLOUD_PROJECT` | ID do projeto Google Cloud (para billing) | Só paid tier |

---

## Segurança

- ✅ `.env` já está no `.gitignore` deste projeto
- ✅ Nunca logamos a chave nos scripts
- ✅ Rotacionar a chave em caso de exposição: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## Testando a configuração

```python
# test_auth.py
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

# Teste simples — deve retornar texto
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=["Diga 'API funcionando!' em português"]
)
print(response.text)
```

---

## Links

- 🔑 [Criar/gerenciar API Keys](https://aistudio.google.com/apikey)
- 📖 [Documentação de autenticação](https://ai.google.dev/gemini-api/docs/api-key)
- 💰 [Billing Google Cloud](https://console.cloud.google.com/billing)
