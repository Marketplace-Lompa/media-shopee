# Taxonomia de Estilo (Niveis)

## Objetivo

Classificar casos de UX/UI em eixos comparaveis para facilitar reuso por estilo, nao apenas por dominio.

Exemplo de leitura:

- `disruptivo: leve`
- `medido: alto`
- `minimalista: alto`
- `profissional_clean: alto`

## Escala padrao

Usar uma destas opcoes por eixo:

- `baixo`
- `leve`
- `medio`
- `alto`

Observacao:

- `leve` e util quando o caso e perceptivel, mas ainda discreto.
- `baixo` e quase ausente.

## Eixos obrigatorios (todo caso)

### 1. `disruptivo`

Quanto o layout/linguagem visual foge de convencoes padrao do mercado.

- `baixo/leves`: conservador, previsivel, seguro
- `medio`: alguns gestos autorais
- `alto`: identidade visual ousada, composicao incomum, alto risco criativo

### 2. `medido`

Nivel de controle visual e sobriedade (ritmo, spacing, peso visual, ruido).

- `baixo`: visual agitado/irregular
- `medio`: equilibrado com alguns excessos
- `alto`: muito controlado, intencional e coeso

### 3. `minimalista`

Grau de reducao visual (ornamentos, paleta, camadas, complexidade aparente).

- `baixo`: muitos elementos e variacoes
- `medio`: limpo, mas com volume moderado de componentes
- `alto`: composicao enxuta e baixa carga visual por bloco

### 4. `profissional_clean`

Percepcao de acabamento comercial premium/clean (nao significa necessariamente minimalista).

- `baixo`: acabamento inconsistente / amador
- `medio`: bom nivel comercial
- `alto`: polimento forte, consistencia alta, visual premium

## Eixos recomendados (quando ajudar)

### 5. `motion_expressivo`

Peso da animacao na identidade da experiencia.

### 6. `densidade_informacao`

Quantidade de informacao/componente por viewport.

### 7. `playful`

Uso de elementos amigaveis/ludicos (stickers, badges, ilustrações, tags, formas).

### 8. `corporativo`

Tom institucional/enterprise vs startup/playful.

## Uso como Manifesto de Projeto (Bias)

Esta taxonomia deixa de ser apenas informativa e passa a ser **especificação de entrada** do agente.

No arquivo `ux-profile.md` (ou similar) de um projeto, deve-se declarar o perfil desejado:

```yaml
profile:
  disruptivo: leve
  medido: alto
  minimalista: alto
  profissional_clean: alto
  # Pesos de decisão (0.0 a 1.0)
  weights:
    minimalismo_vs_densidade: 0.8
    limpeza_vs_playful: 0.9
```

### Regras de Execução com Bias:
1. **Calibragem de Crítica:** Se `minimalista: alto`, o agente deve penalizar severamente o ruído visual desnecessário no `Mode C: Review`.
2. **Direção de Reconstrução:** Se `disruptivo: alto`, o agente terá liberdade para sugerir layouts não-convencionais no `Mode B: Reconstruction`.
3. **Explicabilidade:** Toda recomendação vinculada ao estilo deve ser justificada citando o eixo correspondente: *(Eixo: Minimalista -> Ação: Redução de bordas)*.
