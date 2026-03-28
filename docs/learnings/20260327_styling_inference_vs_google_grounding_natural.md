# Experimento — Styling inference vs Google Search grounding (`natural`)

Data: 2026-03-27

## Objetivo

Comparar, de forma isolada e fora do pipeline principal, 3 abordagens para completar o look a partir da mesma peça de referência:

1. `look_contract` atual da triagem visual
2. segunda chamada Gemini pós-triagem para `look completion`
3. grounding oficial com `Google Search`

## Setup

- Imagem de referência:
  - `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/v2diag_1b3d7b0a/inputs/original_references/01_ref_curated_1.png`
- Prompt do usuário:
  - `foto comercial natural, mulher brasileira real, look completo e elegante`
- Execução:
  - triagem via `resolve_prompt_agent_visual_triage(...)`
  - segunda chamada multimodal Gemini para styling
  - grounding oficial via `_run_grounding_research(...)`

## Resultado 1 — `look_contract` da triagem

`image_analysis`

> This garment is a camel-colored knit pullover featuring a prominent raised geometric pattern of intersecting diagonal lines forming a diamond or trellis grid. The textile is a medium-weight knit with a visible ribbed texture on the neckline and a high-relief stitch that creates depth and shadow within the pattern. The overall aesthetic is warm, tactile, and sophisticated, suitable for refined casual wear.

`look_contract`

```json
{
  "bottom_style": "calça de alfaiataria de lã ou jeans dark wash",
  "bottom_color": "marrom chocolate, bege areia, azul marinho",
  "color_family": "monocromático terroso ou contrastes suaves",
  "season": "outono-inverno",
  "occasion": "work-casual ou elegante",
  "forbidden_bottoms": [
    "shorts de tactel",
    "saia de tule",
    "calça legging brilhante",
    "bermuda cargo"
  ],
  "accessories": "relógio dourado, bota de couro cano curto, cinto fino",
  "style_keywords": [
    "texturizado",
    "sofisticado",
    "atemporal"
  ],
  "confidence": 0.95
}
```

Leitura:

- ainda puxa para `sofisticado / work-casual / elegante`
- ainda induz styling mais arrumado do que o `natural` precisa

## Resultado 2 — Segunda chamada Gemini pós-triagem

Prompt isolado:

> You are a Brazilian fashion stylist. Based ONLY on the garment analysis below, suggest a believable complete look that complements the garment without overpowering it. Focus on lower body and footwear first. Accessories are optional and minimal. Do not sound editorial. Do not over-style. Return plain text in 1 short paragraph.

Resposta:

> Para complementar essa blusa de tricô com textura marcante, uma escolha elegante e muito atual para a mulher brasileira é uma calça de alfaiataria em tom off-white ou areia, com modelagem pantalona ou wide leg de cintura alta, que traz fluidez ao visual. Nos pés, uma sandália de tiras finas em couro caramelo ou um scarpin de bico fino em tom nude ajudam a alongar a silhueta de forma natural. Para finalizar com sofisticação discreta, use apenas um cinto fino de couro no mesmo tom do calçado e brincos pequenos em dourado fosco, mantendo o foco na riqueza do trabalho geométrico do tricô.

Leitura:

- mesmo pedindo `do not sound editorial` e `do not over-style`, o modelo ainda escolheu:
  - alfaiataria clara
  - sandália fina / scarpin
  - acessórios discretos mas arrumados
- isso sugere que a análise da peça (`sophisticated`, `refined casual wear`) está contaminando forte a inferência de styling

## Resultado 3 — Grounding oficial com Google Search

Queries executadas:

- `how to photograph textured knit sweaters professional techniques`
- `garment drape of geometric knit pullover sweater`
- `suéter de tricô geométrico texturizado nome em inglês e português silhueta caimento fotografia`
- `textured geometric knit pullover sweater Portuguese English name silhouette drape photography`
- `professional photography poses for textured knitwear to show pattern`
- `how textured geometric knit fabric drapes on the body structure vs fluid`
- `technical name for textured geometric knit sweater relief knit jacquard intarsia`
- `silhouette of textured geometric knit pullover boxy relaxed straight`

Metadados:

- `effective = false`
- `engine = none`
- `sources = []`
- `reason_codes = ["grounding_internal_suppressed", "grounding_no_sources"]`

Leitura:

- o grounding oficial funcionou como mecanismo de busca, mas não retornou fontes externas utilizáveis
- por política correta do runtime, o texto interno foi suprimido e não contaminou o prompt
- neste caso, o grounding não agregou nada prático ao styling

## Conclusões

1. O `look_contract` atual continua sofisticando demais a peça para `natural`.
2. A segunda chamada Gemini pós-triagem, do jeito cru, não resolve isso sozinha: ela herda o viés da análise da peça e continua arrumando o look.
3. O grounding oficial com Google Search não trouxe valor neste caso porque retornou queries, mas nenhuma fonte útil.

## Próximo passo sugerido

Se quisermos melhorar o `natural`, o ponto mais promissor não é grounding. O alvo mais forte é:

1. reduzir o léxico de sofisticação em `triage.py` para este tipo de peça
2. condicionar um `styling inference pass` pelo `mode` (`natural`) e não só pela análise da roupa
3. manter o grounding oficial como ferramenta de nomenclatura/silhueta/fotografia, não como resolvedor principal de look
