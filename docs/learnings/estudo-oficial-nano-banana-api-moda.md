# Estudo Oficial: Nano Banana via API com foco em Moda

Revisado em: 2026-03-11

## Escopo

Este estudo foi consolidado a partir de documentacao oficial atual da Google, com foco em:

- Gemini Developer API (`ai.google.dev`)
- Vertex AI / Google Cloud (`docs.cloud.google.com`)
- Uso pratico no segmento de moda
- Diferenca entre controle por parametro, ajuste por prompt e o que **nao** tem garantia oficial de determinismo

> Observacao importante:
> A documentacao oficial atual usa o nome **Nano Banana** de forma explicita, mas em duas geracoes diferentes:
> - **Nano Banana** = `gemini-2.5-flash-image`
> - **Nano Banana 2** = `gemini-3.1-flash-image-preview`
>
> Isso importa porque custo, estabilidade, capacidades e limites mudam bastante entre um e outro.

---

## 1. Resumo executivo

Para moda, a conclusao pratica e esta:

- **Nano Banana / Gemini Image** e muito bom para geracao e edicao conversacional, troca de fundo, composicao com referencias, iteracao rapida e criacao editorial/lifestyle.
- **Nao trate Nano Banana como ferramenta oficialmente deterministica de pixel**. A documentacao oficial do Gemini expoe varios controles, mas a garantia clara de repetibilidade por `seed` aparece nas docs do **Imagen**, nao nas docs do Gemini Image.
- Se o objetivo principal for **controle fino, repetibilidade, negative prompt, desligar prompt rewriter, ou seed com comportamento oficialmente documentado**, o caminho oficial mais forte hoje e **Imagen no Vertex AI**.
- Se o objetivo for **vestir uma pessoa com uma roupa** com pipeline proprio de moda, o produto oficial mais alinhado nao e Nano Banana puro, e sim **Virtual Try-On** (`virtual-try-on-001`).
- Se o objetivo for **pegar packshot/produto e recolocar em novo contexto publicitario**, o produto oficial mais aderente e **Imagen product recontext preview** (`imagen-product-recontext-preview-06-30`).

Em outras palavras:

- **Nano Banana**: melhor para criatividade, edicao natural e fluxos multimodais.
- **Imagen**: melhor quando controle e repetibilidade sao prioridade.
- **Virtual Try-On / Product Recontext**: melhor quando o problema ja e especificamente fashion-commerce.

---

## 2. O que a Google chama de Nano Banana hoje

### 2.1 Mapa oficial de modelos

| Nome oficial na doc | Model ID | Superficie | Status | Leitura pratica |
| --- | --- | --- | --- | --- |
| Nano Banana | `gemini-2.5-flash-image` | Gemini Developer API / Vertex AI | Estavel no Gemini API | Modelo rapido, barato, bom para alto volume |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | Gemini Developer API | Preview | Mais recursos, mais flexibilidade, mas com risco de mudanca |
| Nano Banana Pro | `gemini-3-pro-image-preview` | Gemini Developer API | Preview | Maior qualidade e melhor texto/razao visual |

### 2.2 Diferenca relevante entre 2.5 e 3.1

| Tema | `gemini-2.5-flash-image` | `gemini-3.1-flash-image-preview` |
| --- | --- | --- |
| Status | Stable | Preview |
| Caching | Suportado | Nao suportado |
| Search grounding | Nao suportado no model card do Gemini API | Suportado |
| Thinking | Nao suportado | Suportado |
| Inputs | Imagens + texto | Texto + imagem + PDF |
| Input token limit | 65,536 | 131,072 |
| Output token limit | 32,768 | 32,768 |
| Uso recomendado | alto volume, menor risco operacional | fluxos mais ricos, grounding, PDF, raciocinio visual |

### 2.3 Implicacao para moda

- Use **2.5** quando o gargalo for volume, custo e previsibilidade operacional.
- Use **3.1** quando voce precisar:
  - consumir briefing em PDF
  - usar Search grounding
  - iterar com mais contexto
  - fazer exploracao editorial mais rica

> Inferencia a partir das fontes:
> para producao critica de ecommerce, o 2.5 tende a ser a base mais segura; o 3.1 entra como camada de exploracao ou casos premium enquanto continuar em preview.

---

## 3. O que esta oficialmente disponivel via API

### 3.1 Gemini Developer API: recursos confirmados

Na pagina oficial de image generation e nos model cards, os recursos confirmados para Gemini Image incluem:

- geracao texto -> imagem
- edicao imagem + texto -> imagem
- retorno intercalado de texto e imagem
- modo somente imagem via `response_modalities=["Image"]`
- controle de `aspect_ratio`
- controle de `image_size`
- multi-turn via chat
- grounding com `google_search`
- grounding com **Google Image Search** dentro do mesmo tool
- watermark SynthID em imagens geradas

### 3.2 Parametros da Gemini API que sao claramente documentados

Controles confirmados nas docs:

- `responseModalities` / `response_modalities`
- `imageConfig`
- `aspectRatio` / `aspect_ratio`
- `imageSize` / `image_size`
- `tools` com `google_search`
- `seed` existe no schema generico de `GenerateContentConfig`

### 3.3 Ponto critico sobre `seed`

O schema generico da Gemini API documenta `seed` como:

- "Seed used in decoding. If not set, the request uses a randomly generated seed."

Mas a documentacao oficial de **Gemini image generation** nao traz uma pagina equivalente a "generate deterministic images" para Nano Banana, nem promete repetibilidade igual a do Imagen.

Conclusao prudente:

- **Nao e seguro vender Nano Banana como deterministicamente repetivel so porque o schema tem `seed`.**
- A garantia oficial e explicita de repetibilidade por `seed` aparece nas docs do **Imagen**, nao nas do Gemini Image.

---

## 4. O que e deterministico, o que e prompt-driven e o que nao e garantido

### 4.1 Controle por parametro: relativamente rigido

Esses itens sao controlados por configuracao de API, nao por semantica aberta do prompt:

| Controle | Gemini Image | Observacao para moda |
| --- | --- | --- |
| Modelo | Sim | define custo, latencia, disponibilidade e recursos |
| `response_modalities` | Sim | use `["Image"]` se nao quiser texto extra |
| `aspect_ratio` | Sim | essencial para PDP, feed, story, banner |
| `image_size` | Sim | define custo e nivel de detalhe |
| Tooling de grounding | Sim | relevante para pesquisa visual/tendencias |
| Historico de chat | Sim | ajuda iteracao progressiva |
| Watermark SynthID | Sim no Gemini; padrao ativo no Imagen | afeta compliance e, no Imagen, afeta determinismo com `seed` |

Aspect ratios mostrados na doc do Gemini Image:

- `1:1`
- `1:4`
- `1:8`
- `2:3`
- `3:2`
- `3:4`
- `4:1`
- `4:3`
- `4:5`
- `5:4`
- `8:1`
- `9:16`
- `16:9`
- `21:9`

Image sizes mostrados na doc:

- `512`
- `1K`
- `2K`
- `4K`

### 4.2 Controle por prompt: forte, mas sem garantia mecanica

Esses itens sao majoritariamente guiados por prompt:

- estetica visual
- estilo fotografico
- iluminacao
- pose
- enquadramento
- humor editorial
- materialidade percebida
- direcao de arte
- o que preservar na edicao
- o que transformar na edicao

Na pratica de moda, quase tudo que faz a imagem "parecer campanha", "parecer catalogo", "parecer lookbook", "parecer luxo", "parecer fast fashion" continua sendo engenharia de prompt.

### 4.3 O que nao tem garantia oficial forte no Nano Banana

Para planejamento realista, trate estes pontos como **nao garantidos** no Gemini Image:

- repetir exatamente o mesmo pixel output em reruns
- edicao cirurgica por regiao como se houvesse mascara explicita
- preservar com 100% de fidelidade microdetalhes de estampa, trama e caimento em qualquer transformacao
- retornar exatamente a quantidade de imagens pedida
- renderizar texto dentro da imagem de forma sempre confiavel em um unico passo
- manter consistencia perfeita entre multiplas imagens geradas no mesmo lote

As docs de limitacoes do Gemini Image explicitam, entre outras coisas:

- o modelo pode nao criar exatamente o numero de imagens solicitado
- prompts ambiguos podem retornar texto sem imagem
- o modelo pode criar texto como se fosse imagem
- para imagem com texto, o recomendado e gerar o texto primeiro e a imagem depois

---

## 5. O que as fontes oficiais dizem que e melhor para moda

### 5.1 Quando Nano Banana faz sentido

Nano Banana e forte em:

- troca de fundo sem mascara
- edicao conversacional
- combinar referencias
- gerar cena editorial a partir de brief
- misturar texto e imagem no mesmo fluxo
- fazer refinamentos em varios turnos

Para moda isso e excelente em:

- campanha editorial
- lifestyle para redes sociais
- mockups criativos
- exploracao de conceito
- versoes de uma mesma ideia
- ajuste progressivo de iluminacao, pose e cenario

### 5.2 Quando Imagen faz mais sentido

Na comparacao oficial do Vertex AI, a Google posiciona:

- **Gemini Image** como recomendacao padrao por flexibilidade, entendimento contextual e edicao conversacional sem mascara
- **Imagen 4** como melhor em qualidade/latencia e mais adequado quando o trabalho pede comportamento mais especializado

Para moda, isso empurra Imagen para cenarios como:

- fundo e corte mais controlados
- geracao de catalogo mais repetivel
- necessidade de `negative prompt`
- seed deterministicamente documentado
- desligar/ligar prompt rewriting
- controle mais fino sobre pessoas e watermark

Ressalva importante da doc oficial de Imagen:

- o comportamento deterministico por `seed` e documentado no Imagen
- mas a propria doc diz que isso depende de `addWatermark=false`
- o prompt rewriter (`enhancePrompt`) tambem pode ser ligado/desligado e influencia aderencia versus qualidade

### 5.3 Quando usar Product Recontext

O endpoint oficial:

- `imagen-product-recontext-preview-06-30`

Serve melhor que Nano Banana puro quando a tarefa e:

- pegar imagem de produto
- manter o produto como ancora
- criar novo contexto publicitario
- gerar outdoor/lifestyle a partir de packshot

Para ecommerce de moda, isto e muito valioso em:

- transformar packshot de bolsa em criativo de campanha
- recolocar calcado, acessorio ou roupa em ambiente aspiracional
- gerar variacoes para banner sem refazer sessao fotografica

### 5.4 Quando usar Virtual Try-On

O endpoint oficial:

- `virtual-try-on-001`

Recebe:

- `personImage`
- `productImages`

Para moda, isso e o produto oficial mais aderente quando o objetivo e:

- vestir uma pessoa com uma roupa
- demonstrar produto em corpo humano
- reduzir a "criatividade" livre e aumentar aderencia ao caso de uso de provador

Conclusao pratica:

- **Nao use Nano Banana puro como substituto automatico de VTO quando a exigencia principal e fidelidade de roupa em corpo.**

---

## 6. Boas praticas oficiais e como adaptar para moda

### 6.1 Seja especifico

A doc oficial de best practices do Gemini Image fala claramente:

- seja especifico
- mais detalhes dao mais controle
- forneca contexto e intencao

Para moda, isso significa nomear:

- tipo de peca
- modelagem
- tecido
- textura
- padronagem
- cor
- fit
- gola
- manga
- comprimento
- acabamento
- publico-alvo
- canal de uso

Exemplo ruim:

```text
Crie uma foto elegante de moda.
```

Exemplo melhor:

```text
Crie uma imagem fotorealista de ecommerce premium de uma blusa feminina de tricot canelado, gola alta dobrada, manga longa, caimento reto, textura de fio medio visivel, cor off-white, em modelo em pe, enquadramento 3/4, iluminacao frontal suave de estudio, fundo cinza-claro limpo, retorno somente imagem.
```

### 6.2 Diga o contexto e a intencao

A doc oficial recomenda explicar o objetivo da imagem.

Em moda, isso muda muito o resultado:

- `foto principal de PDP`
- `criativo para campanha de inverno`
- `story vertical para marketplace`
- `hero banner para landing page`
- `lookbook editorial`

O modelo responde melhor quando entende para que o ativo sera usado.

### 6.3 Itere em pequenos passos

A doc oficial recomenda refinamento iterativo e follow-up prompts.

Para moda, a melhor sequencia costuma ser:

1. gerar a base
2. ajustar fundo
3. ajustar iluminacao
4. ajustar pose
5. ajustar acessorios
6. ajustar crop/final framing

Isso e superior a um prompt monolitico com 30 restricoes.

### 6.4 Descreva o que voce quer, nao so o que voce nao quer

As best practices do Gemini Image orientam:

- descreva positivamente o resultado desejado

Isso e especialmente importante porque:

- **negative prompt e oficialmente documentado para Imagen**
- para Gemini, o caminho principal continua sendo descricao positiva

Em moda:

Evite:

```text
Nao deixe parecer barato, nao deixe fundo ruim, nao deixe a modelo estranha, nao deixe parecer IA.
```

Prefira:

```text
Visual premium de estudio, fundo neutro limpo, pele natural, proporcoes humanas realistas, textura de tecido preservada, look principal claramente legivel.
```

### 6.5 Separe texto e imagem quando houver lettering

A doc oficial de limitacoes diz:

- para gerar imagem com texto, gere o texto primeiro e depois a imagem com esse texto

Aplicacao em moda:

- slogan em poster
- etiqueta promocional
- tipografia em hero banner
- frase editorial sobreposta

Nao aposte tudo em um unico passo se o texto for critico.

### 6.6 Peca explicitamente imagem

A doc de limitacoes tambem diz:

- se o prompt for ambiguo, o modelo pode retornar texto sem imagem

Para evitar isso:

- sempre declare `response_modalities=["Image"]` quando o objetivo for imagem pura
- ou diga no prompt: `retorne somente imagem`

### 6.7 Use poucas referencias e use referencias boas

As docs oficiais deixam claro:

- `gemini-2.5-flash-image` funciona melhor com ate 3 imagens de entrada
- `gemini-3-pro-image-preview` funciona melhor com ate 14 no total
- o guide tambem indica que `gemini-3.1-flash-image-preview` suporta semelhanca de personagem de ate 4 personagens e fidelidade de ate 10 objetos em um workflow

Para moda, a recomendacao pratica e:

- 1 imagem da roupa principal
- 1 imagem de styling ou cenario
- opcionalmente 1 terceira imagem de detalhe

Nao monte um "moodboard caotico" de muitas referencias conflitantes no 2.5.

### 6.8 Multi-turn para edicao e superior a um unico mega prompt

O fluxo de chat do Gemini Image permite continuar no mesmo chat e editar a imagem ao longo dos turnos.

Em moda, isso funciona muito bem para:

- "mantenha a roupa, troque o fundo"
- "agora aqueca a iluminacao"
- "agora faca crop 4:5"
- "agora reduza os acessorios"

Isso reduz drift criativo.

### 6.9 Use grounding quando o problema for referencia externa, nao quando o problema for fidelidade de produto

Com Gemini 3.1, a doc mostra `google_search` com `webSearch` e `imageSearch`.

Isso ajuda em:

- pesquisa visual
- referencias de ave/fauna/material/ambiente
- moodboards guiados por web
- campanhas inspiradas em tendencias

Mas, para moda comercial:

- grounding **nao substitui** imagem proprietaria do produto
- grounding **nao substitui** VTO
- grounding **nao substitui** recontextualizacao especializada

Use como suporte criativo, nao como ancora de fidelidade do SKU.

---

## 7. O que evitar

### 7.1 Nao confundir controle semantico com determinismo

Ter muito controle por prompt nao significa ter repetibilidade garantida.

Para planejamento de produto:

- Nano Banana = controlavel
- Imagen com seed = deterministicamente documentado

Sao coisas diferentes.

### 7.2 Nao vender `seed` do Gemini como garantia de reproducao

O schema generico do `generateContent` tem `seed`, mas a documentacao de Gemini Image nao entrega a mesma promessa explicita que a documentacao de Imagen.

Evite:

- prometer rerun identico
- construir teste de regressao visual assumindo pixel match
- tratar seed como contrato forte no Nano Banana

### 7.3 Nao usar prompt ambiguo

Se o objetivo e imagem, declare isso no payload e no texto.

Evite pedidos como:

```text
Me explique e mostre um look de inverno.
```

Esse tipo de prompt abre margem para resposta textual.

### 7.4 Nao depender de negative prompt no Gemini como mecanismo principal

Se remover conteudo indesejado e requisito estrutural:

- use Imagen com negative prompt
- ou use fluxo especializado

No Gemini Image, a estrategia principal oficial e descricao positiva e iteracao.

### 7.5 Nao sobrecarregar `gemini-2.5-flash-image` com muitas referencias

As docs oficiais sao claras sobre melhor resultado com ate 3 imagens no 2.5.

Em moda, excesso de refs normalmente produz:

- drift de identidade
- mistura ruim de tecidos
- pose incoerente
- silhouette confusa

### 7.6 Nao usar preview sem fallback em fluxo core de negocio

As docs de pricing/model card deixam claro que preview:

- pode mudar antes de ficar estavel
- pode ter rate limits mais restritivos

Se o seu pipeline for core de ecommerce:

- prefira base estavel
- mantenha fallback
- separe casos premium de casos massivos

### 7.7 Nao usar Nano Banana puro para virtual try-on quando a exigencia e comercial

Para "vestir a roupa no corpo":

- o produto oficial correto e `virtual-try-on-001`

Nano Banana pode ate aproximar cenarios visuais, mas nao deve ser a primeira escolha quando o critico e:

- fidelidade de vestimenta em corpo
- uso operacional de provador
- experiencia de ecommerce fashion-tech

### 7.8 Nao ignorar safety e politicas

As docs oficiais de responsible AI deixam claro que o sistema bloqueia ou pode recusar conteudo como:

- sexualmente explicito
- exploracao infantil
- violencia extrema
- odio
- assedio
- bullying
- imagem intima nao consensual

Para moda, isso exige cuidado especial com:

- lingerie
- beachwear
- poses sensuais
- modelos jovens
- pedidos envolvendo celebridades

No Product Recontext, a doc explicita que geracao de celebridades nao e permitida em nenhum setting de `personGeneration`.

---

## 8. Recomendacao objetiva por caso de uso em moda

| Caso de uso | Melhor opcao oficial | Motivo |
| --- | --- | --- |
| Hero image de produto com fundo novo, preservando SKU | Product Recontext | mais aderente ao problema de produto |
| Provar roupa em pessoa | Virtual Try-On | endpoint proprio de try-on |
| Editorial/lifestyle criativo | Nano Banana / Nano Banana 2 | melhor fluidez conversacional e criativa |
| Ajuste progressivo da mesma imagem | Gemini Image multi-turn | edicao iterativa natural |
| Brief em PDF + geracao | Gemini 3.1 Flash Image Preview | PDF input + search grounding + thinking |
| Catalogo em volume e custo baixo | Gemini 2.5 Flash Image | estavel e mais simples operacionalmente |
| Controle mais forte com seed/negative prompt | Imagen | docs oficiais cobrem isso diretamente |

---

## 9. Templates de prompt para moda

### 9.1 Catalogo / PDP

```text
Crie uma imagem fotorealista de ecommerce de uma [peca], com foco na legibilidade da roupa.
Preserve fielmente:
- modelagem
- textura do tecido
- cor principal
- acabamentos
- caimento

Cenario:
- fundo neutro limpo
- iluminacao frontal suave de estudio
- enquadramento [3:4 ou 4:5]
- modelo em pe

Objetivo:
- imagem principal de pagina de produto

Retorne somente imagem.
```

### 9.2 Editorial

```text
Crie uma imagem editorial fotorealista de campanha para [colecao/estacao].
Peca principal: [descricao tecnica].
Direcao de arte:
- ambiente [urbano / resort / minimalista / luxo]
- iluminacao [golden hour / soft studio / diffuse daylight]
- camera [close 3/4 / full body / waist up]
- sensacao de marca [premium / aspiracional / contemporanea]

Mantenha a roupa principal claramente legivel.
Retorne somente imagem.
```

### 9.3 Edicao pontual

```text
Usando a imagem enviada, altere apenas [elemento alvo].
Mantenha exatamente como esta:
- rosto
- corpo
- pose
- roupa principal
- textura
- drapeado
- construcao da peca

Retorne somente imagem.
```

### 9.4 Prompt de pesquisa visual com grounding

```text
Pesquise referencias visuais e gere uma imagem de campanha para uma colecao de inverno premium.
Baseie a cena em referencias reais de paisagem, luz e atmosfera.
Roupa principal: sueter feminino de tricot canelado off-white, gola alta, manga longa.
Visual final: editorial sofisticado, composicao limpa, foco na leitura da malha.
Retorne somente imagem.
```

---

## 10. Exemplos de payload

### 10.1 Gemini Image: imagem pura

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        "Create a photorealistic premium fashion e-commerce image of a women's ribbed knit turtleneck sweater in off-white. Return image only."
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(
            aspect_ratio="4:5",
            image_size="1K",
        ),
    ),
)
```

### 10.2 Gemini Image: edicao com imagem de referencia

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        reference_image,
        "Change only the background to a premium warm-gray studio set. Keep the model, pose, garment construction, knit texture, drape, and color exactly as they are. Return image only."
    ],
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(
            aspect_ratio="4:5",
            image_size="2K",
        ),
    ),
)
```

### 10.3 Gemini 3.1 com Google Search + Image Search grounding

```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "Generate a premium winter fashion campaign image grounded in real visual references for atmosphere and scene composition. Return image only."
        }
      ]
    }
  ],
  "tools": [
    {
      "google_search": {
        "searchTypes": {
          "webSearch": {},
          "imageSearch": {}
        }
      }
    }
  ],
  "generationConfig": {
    "responseModalities": ["IMAGE"]
  }
}
```

### 10.4 Product Recontext no Vertex AI

```json
{
  "instances": [
    {
      "prompt": "Create a photorealistic premium ad image for this product in a refined urban winter setting.",
      "productImages": [
        {
          "image": {
            "bytesBase64Encoded": "BASE64_SUBJECT_IMAGE"
          }
        }
      ]
    }
  ],
  "parameters": {
    "personGeneration": "allow_adult",
    "addWatermark": true,
    "sampleCount": 1,
    "enhancePrompt": true
  }
}
```

### 10.5 Virtual Try-On no Vertex AI

```json
{
  "instances": [
    {
      "personImage": {
        "image": {
          "bytesBase64Encoded": "BASE64_PERSON_IMAGE"
        }
      },
      "productImages": [
        {
          "image": {
            "bytesBase64Encoded": "BASE64_PRODUCT_IMAGE"
          }
        }
      ]
    }
  ],
  "parameters": {
    "sampleCount": 1
  }
}
```

---

## 11. Custos e impacto operacional

### 11.1 Gemini 2.5 Flash Image

Na pagina oficial de pricing do Gemini API, `gemini-2.5-flash-image` aparece com:

- input pago por texto/imagem
- output de imagem equivalente a cerca de **US$ 0.039 por imagem** em ate `1024x1024`
- batch com custo reduzido

### 11.2 Gemini 3.1 Flash Image Preview

Na mesma pagina, `gemini-3.1-flash-image-preview` aparece com output de imagem tokenizado, com equivalencias mostradas pela doc:

- ~`US$ 0.045` por `0.5K`
- ~`US$ 0.067` por `1K`
- ~`US$ 0.101` por `2K`
- ~`US$ 0.151` por `4K`

Leitura pratica:

- 1K continua sendo o melhor ponto de equilibrio para moda digital comum
- 2K faz sentido quando textura e zoom de tecido importam
- 4K so vale quando o destino final realmente exige isso

---

## 12. Conclusao

Se a pergunta for "podemos usar Nano Banana via API para moda?", a resposta e **sim**, e muito bem.

Se a pergunta for "ele e a melhor opcao oficial para todo problema de moda?", a resposta e **nao**.

A escolha correta hoje fica assim:

- **Nano Banana 2 / Gemini 3.1 Flash Image Preview**
  - melhor para exploracao, grounding, briefs ricos, PDF e criacao multimodal
- **Nano Banana / Gemini 2.5 Flash Image**
  - melhor para alto volume, menor risco e integracao simples
- **Imagen**
  - melhor para controles explicitamente documentados de determinismo e negative prompt
- **Product Recontext**
  - melhor para SKU/produto em novo contexto
- **Virtual Try-On**
  - melhor para roupa em corpo

Para o segmento de moda, a recomendacao mais madura e:

- usar **Gemini Image** como motor criativo e conversacional
- usar **Imagen / Recontext / VTO** quando o caso pedir mais controle estrutural

---

## 13. Fontes oficiais

- [Gemini API image generation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Gemini 3.1 Flash Image Preview model card](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview)
- [Gemini 2.5 Flash Image model card](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-image)
- [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API generateContent reference](https://ai.google.dev/api/generate-content)
- [Vertex AI image overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/overview)
- [Gemini image generation best practices](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/gemini-image-generation-best-practices)
- [Gemini image generation limitations](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/gemini-image-generation-limitations)
- [Gemini image generation and responsible AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/gemini-image-responsible-ai)
- [Generate deterministic images with Imagen](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/generate-deterministic-images)
- [Omit content using a negative prompt](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/omit-content-using-a-negative-prompt)
- [Recontextualize product images](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/recontextualize-product-images)
- [Generate Virtual Try-On images](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/generate-virtual-try-on-images)
