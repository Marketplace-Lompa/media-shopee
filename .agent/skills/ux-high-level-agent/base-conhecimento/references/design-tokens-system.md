# Design Tokens System

## Purpose

Padronizar a definicao de tokens de design de forma agnostica a stack, garantindo consistencia visual entre componentes, breakpoints e temas. Tokens sao o contrato entre design e implementacao.

## O que sao Design Tokens

Decisoes de design representadas como dados. Nao sao CSS, nao sao Figma variables, sao a camada semantica que alimenta ambos.

```
Decisao de design -> Token -> Implementacao (CSS/Tailwind/React/Swift/etc.)
```

## Hierarquia de Tokens (3 Niveis)

### Level 1: Primitive Tokens (Core)
Valores brutos sem significado semantico.

```yaml
color:
  gray-50: "#fafafa"
  gray-100: "#f5f5f5"
  gray-200: "#e5e5e5"
  gray-300: "#d4d4d4"
  gray-400: "#a3a3a3"
  gray-500: "#737373"
  gray-600: "#525252"
  gray-700: "#404040"
  gray-800: "#262626"
  gray-900: "#171717"
  gray-950: "#0a0a0a"
  blue-500: "#3b82f6"
  blue-600: "#2563eb"
  green-500: "#22c55e"
  red-500: "#ef4444"
  amber-500: "#f59e0b"

spacing:
  0: "0px"
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  5: "20px"
  6: "24px"
  8: "32px"
  10: "40px"
  12: "48px"
  16: "64px"
  20: "80px"
  24: "96px"

radius:
  none: "0px"
  sm: "4px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  2xl: "24px"
  full: "9999px"

font-size:
  xs: "12px"
  sm: "14px"
  base: "16px"
  lg: "18px"
  xl: "20px"
  2xl: "24px"
  3xl: "30px"
  4xl: "36px"
  5xl: "48px"
  6xl: "60px"
  7xl: "72px"

font-weight:
  normal: 400
  medium: 500
  semibold: 600
  bold: 700
  extrabold: 800

line-height:
  tight: 1.1
  snug: 1.25
  normal: 1.5
  relaxed: 1.625
  loose: 2.0

duration:
  instant: "0ms"
  fast: "150ms"
  normal: "300ms"
  slow: "500ms"
  slower: "700ms"

easing:
  default: "cubic-bezier(0.4, 0, 0.2, 1)"
  in: "cubic-bezier(0.4, 0, 1, 1)"
  out: "cubic-bezier(0, 0, 0.2, 1)"
  in-out: "cubic-bezier(0.4, 0, 0.2, 1)"
  spring: "cubic-bezier(0.34, 1.56, 0.64, 1)"
```

### Level 2: Semantic Tokens (Significado)
Primitivos mapeados para funcao de design.

```yaml
color:
  # Surfaces
  surface-primary: "{color.white}"          # fundo principal
  surface-secondary: "{color.gray-50}"      # fundo secundario
  surface-tertiary: "{color.gray-100}"      # fundo terciario
  surface-inverse: "{color.gray-900}"       # fundo invertido (dark sections)
  surface-overlay: "rgba(0,0,0,0.5)"        # backdrop de modais

  # Text
  text-primary: "{color.gray-900}"          # texto principal
  text-secondary: "{color.gray-600}"        # texto de suporte
  text-tertiary: "{color.gray-400}"         # texto meta/hint
  text-inverse: "{color.white}"             # texto em superficies escuras
  text-link: "{color.blue-600}"             # links
  text-link-hover: "{color.blue-700}"       # links em hover

  # Brand
  brand-primary: "{color.blue-600}"
  brand-primary-hover: "{color.blue-700}"
  brand-secondary: "{color.gray-100}"

  # Feedback
  feedback-success: "{color.green-500}"
  feedback-error: "{color.red-500}"
  feedback-warning: "{color.amber-500}"
  feedback-info: "{color.blue-500}"

  # Border
  border-default: "{color.gray-200}"
  border-strong: "{color.gray-300}"
  border-focus: "{color.blue-500}"
  border-error: "{color.red-500}"

spacing:
  # Layout
  page-gutter: "{spacing.4}"               # mobile
  page-gutter-md: "{spacing.6}"            # tablet
  page-gutter-lg: "{spacing.8}"            # desktop
  section-gap: "{spacing.16}"              # entre secoes
  section-gap-lg: "{spacing.24}"           # entre secoes em desktop

  # Components
  card-padding: "{spacing.4}"
  card-padding-lg: "{spacing.6}"
  input-padding-x: "{spacing.3}"
  input-padding-y: "{spacing.2}"
  button-padding-x: "{spacing.4}"
  button-padding-y: "{spacing.2}"
  stack-gap: "{spacing.2}"                 # gap padrao entre itens empilhados
  inline-gap: "{spacing.2}"               # gap padrao entre itens inline

radius:
  button: "{radius.md}"
  card: "{radius.lg}"
  input: "{radius.md}"
  modal: "{radius.xl}"
  badge: "{radius.full}"
  avatar: "{radius.full}"

typography:
  # Escalas por funcao
  hero: { size: "{font-size.5xl}", weight: "{font-weight.bold}", line-height: "{line-height.tight}" }
  h1: { size: "{font-size.4xl}", weight: "{font-weight.bold}", line-height: "{line-height.tight}" }
  h2: { size: "{font-size.3xl}", weight: "{font-weight.semibold}", line-height: "{line-height.snug}" }
  h3: { size: "{font-size.2xl}", weight: "{font-weight.semibold}", line-height: "{line-height.snug}" }
  h4: { size: "{font-size.xl}", weight: "{font-weight.medium}", line-height: "{line-height.snug}" }
  body: { size: "{font-size.base}", weight: "{font-weight.normal}", line-height: "{line-height.normal}" }
  body-sm: { size: "{font-size.sm}", weight: "{font-weight.normal}", line-height: "{line-height.normal}" }
  caption: { size: "{font-size.xs}", weight: "{font-weight.normal}", line-height: "{line-height.normal}" }
  label: { size: "{font-size.sm}", weight: "{font-weight.medium}", line-height: "{line-height.tight}" }
  button: { size: "{font-size.sm}", weight: "{font-weight.semibold}", line-height: "{line-height.tight}" }

shadow:
  sm: "0 1px 2px rgba(0,0,0,0.05)"
  md: "0 4px 6px -1px rgba(0,0,0,0.1)"
  lg: "0 10px 15px -3px rgba(0,0,0,0.1)"
  xl: "0 20px 25px -5px rgba(0,0,0,0.1)"
  card: "{shadow.sm}"
  dropdown: "{shadow.lg}"
  modal: "{shadow.xl}"
  sticky-header: "0 1px 3px rgba(0,0,0,0.08)"

motion:
  # Transitions por contexto
  hover: { duration: "{duration.fast}", easing: "{easing.default}" }
  expand: { duration: "{duration.normal}", easing: "{easing.out}" }
  modal-enter: { duration: "{duration.normal}", easing: "{easing.out}" }
  modal-exit: { duration: "{duration.fast}", easing: "{easing.in}" }
  page-transition: { duration: "{duration.slow}", easing: "{easing.in-out}" }
  scroll-linked: { easing: "{easing.spring}", stiffness: 100, damping: 30 }

z-index:
  base: 0
  dropdown: 100
  sticky: 200
  overlay: 300
  modal: 400
  toast: 500
  tooltip: 600
```

### Level 3: Component Tokens (Especifico)
Tokens vinculados a um componente especifico.

```yaml
button-primary:
  bg: "{color.brand-primary}"
  bg-hover: "{color.brand-primary-hover}"
  text: "{color.text-inverse}"
  border: "none"
  radius: "{radius.button}"
  padding: "{button-padding-y} {button-padding-x}"
  font: "{typography.button}"
  shadow: "none"
  shadow-hover: "{shadow.sm}"

button-secondary:
  bg: "transparent"
  bg-hover: "{color.surface-secondary}"
  text: "{color.text-primary}"
  border: "1px solid {color.border-default}"
  radius: "{radius.button}"
  padding: "{button-padding-y} {button-padding-x}"

card:
  bg: "{color.surface-primary}"
  border: "1px solid {color.border-default}"
  radius: "{radius.card}"
  padding: "{card-padding}"
  shadow: "{shadow.card}"
  shadow-hover: "{shadow.md}"

input:
  bg: "{color.surface-primary}"
  border: "1px solid {color.border-default}"
  border-focus: "2px solid {color.border-focus}"
  border-error: "1px solid {color.border-error}"
  radius: "{radius.input}"
  padding: "{input-padding-y} {input-padding-x}"
  text: "{color.text-primary}"
  placeholder: "{color.text-tertiary}"
```

## Dark Mode Token Mapping

Nao inverter; remapear semanticamente.

```yaml
# Superficies (dark mode)
surface-primary: "{color.gray-900}"
surface-secondary: "{color.gray-800}"
surface-tertiary: "{color.gray-700}"
surface-inverse: "{color.white}"

# Texto (dark mode)
text-primary: "{color.gray-50}"
text-secondary: "{color.gray-400}"
text-tertiary: "{color.gray-500}"
text-inverse: "{color.gray-900}"

# Bordas (dark mode)
border-default: "{color.gray-700}"
border-strong: "{color.gray-600}"

# Shadows (dark mode - frequentemente ineficazes)
card: "none"                              # substituir por borda sutil
dropdown: "0 4px 12px rgba(0,0,0,0.4)"   # sombras mais fortes em dark
```

## Breakpoint Tokens

```yaml
breakpoints:
  sm: "640px"     # mobile landscape
  md: "768px"     # tablet portrait (minimo para tablet layout)
  lg: "1024px"    # tablet landscape / desktop small
  xl: "1280px"    # desktop
  2xl: "1440px"   # desktop wide (viewport de referencia)

container:
  sm: "640px"
  md: "768px"
  lg: "1024px"
  xl: "1280px"
  max: "1200px"   # largura maxima de conteudo
```

## Regras de Aplicacao

### Principio: Semantic First
- Nunca usar primitivos diretamente em componentes (usar semanticos)
- Excecao: one-off values em prototipacao rapida (marcar como `TODO: tokenize`)

### Principio: Fewer is Better
- Iniciar com subset minimo e expandir sob demanda
- Cada token adicionado e compromisso de manutencao
- Se dois tokens tem mesmo valor e mesmo significado, unificar

### Principio: Responsive by Default
- Tokens de spacing/typography devem ter variantes por breakpoint quando necessario
- Nao criar token responsivo se a variacao for trivial (use CSS clamp)

### Principio: Theme-Agnostic Naming
- Nomes descrevem funcao, nao aparencia
- `surface-primary` nao `white-background`
- `feedback-error` nao `red-text`
- `text-secondary` nao `gray-text`

## Como o Agente Usa Tokens

### Em reconstrucao
1. Extrair paleta e escala da referencia
2. Mapear para primitivos
3. Criar semanticos por funcao
4. Aplicar em componentes

### Em auditoria
- Verificar se componentes similares usam mesmos tokens
- Encontrar "magic numbers" (valores inline sem token)
- Medir consistencia de spacing/radius/shadow

### Em review
- Tokens inconsistentes entre componentes -> `Finding: Medium`
- Ausencia de dark mode mapping -> `Finding: Minor` (a menos que dark mode seja requisito)
- Spacing sem escala previsivel -> `Finding: Medium`
