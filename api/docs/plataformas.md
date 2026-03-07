# Google AI Studio vs. Vertex AI — Guia de Plataformas

> Decisão estratégica: qual plataforma usar para cada tipo de projeto.  
> Atualizado: Março/2026

---

## Comparativo Principal

| Característica | Google AI Studio | Vertex AI |
|---|---|---|
| **Perfil de usuário** | Desenvolvedores, pesquisadores, startups | Empresas, escala corporativa |
| **Custo** | Free tier + faturamento por token | Pay-as-you-go + infraestrutura |
| **SLA garantido** | ❌ Não disponível | ✅ 99.9% |
| **Segurança** | Básica | Enterprise (HIPAA, VPC-SC, CMEK) |
| **Customização** | Ajuste fino limitado | Supervised Tuning, RLHF, Destilação |
| **Faturamento** | Tokens + créditos mensais | Uso por segundo/unidade |
| **Grounding** | ✅ Google Search + Image Search | ✅ + Google Maps |
| **Prototipagem** | ✅ Ideal | ❌ Overhead maior |
| **Produção em escala** | ⚠️ Funciona, sem SLA | ✅ Recomendado |

---

## Quando usar cada plataforma

### ✅ Use Google AI Studio se:
- Você é desenvolvedor individual ou startup early-stage
- Está prototipando, testando e iterando rapidamente
- Não precisa de SLA formal
- Seu volume é compatível com o free tier e paid tier básico
- Projeto MEDIA-SHOPEE ← **este é o nosso caso**

### ✅ Use Vertex AI se:
- Empresa com compliance regulatório (saúde, finanças, governo)
- Precisa de SLA formal (99.9% uptime)
- Requer criptografia CMEK ou isolamento VPC
- Escala de milhões de requests/dia
- Precisa de fine-tuning supervisionado (RLHF)

---

## Migração entre plataformas

O SDK unificado **Google Gen AI** facilita a migração:

```python
# Google AI Studio (API Key)
client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

# Vertex AI (Service Account — apenas trocar autenticação)
client = genai.Client(
    vertexai=True,
    project="meu-projeto-gcp",
    location="us-central1"
)

# O restante do código é IDÊNTICO
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[...],
    config=...
)
```

> ⚠️ Modelos ajustados (fine-tuned) no AI Studio **precisam ser retreinados** no Vertex AI para aproveitar o pipeline MLOps completo.

---

## Nossa decisão: Google AI Studio

Para o projeto MEDIA-SHOPEE, usamos **Google AI Studio** por:

1. **Free tier suficiente** para iteração criativa (~500 img/dia)
2. **Sem overhead** de infraestrutura GCP
3. **API Key simples** — sem Service Account, IAM, VPC
4. **Sem SLA necessário** — workflow criativo tolera variabilidade
5. **Mesmos modelos** (Nano Banana 2, Veo 3.1) disponíveis em ambas

→ Se escalar para produção B2B ou precisar de HIPAA, migrar para Vertex AI é apenas uma linha de código.
