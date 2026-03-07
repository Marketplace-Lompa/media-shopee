# Accessibility and Inclusion (UX High-Level)

## Purpose

Garantir que toda interface produzida pelo agente seja utilizavel por pessoas com deficiencias visuais, motoras, cognitivas e auditivas. Acessibilidade nao e checklist final, e restricao de design desde o inicio.

## Baseline: WCAG 2.1 AA (Minimo Obrigatorio)

### Perceivable

#### Contraste
- Texto normal: ratio minimo **4.5:1** contra fundo
- Texto grande (>=18pt ou >=14pt bold): ratio minimo **3:1**
- Componentes UI e graficos informativos: ratio minimo **3:1** contra adjacente
- Placeholder text: mesmo ratio de texto normal (nao usar como unico label)
- Testar contraste em todos os estados: default, hover, focus, disabled, active

#### Alternativas textuais
- Toda imagem informativa precisa de `alt` descritivo
- Imagens decorativas: `alt=""` ou `role="presentation"`
- Icones sem texto adjacente: `aria-label` obrigatorio
- Graficos complexos: descricao longa via `aria-describedby` ou texto adjacente

#### Adaptabilidade
- Informacao nao pode depender apenas de cor (usar forma, texto ou icone adicional)
- Conteudo deve fazer sentido em leitura linear (sem CSS)
- Orientacao nao pode ser restrita (suportar portrait e landscape)

### Operable

#### Teclado
- Todo interativo acessivel via teclado: `Tab`, `Enter`, `Space`, `Escape`, setas
- Ordem de foco logica e previsivel (seguir DOM order, evitar `tabindex` > 0)
- Foco visivel e claro em todos os interativos (nunca `outline: none` sem substituto)
- Skip link para conteudo principal como primeiro focusable
- Nenhum keyboard trap (exceto modais com focus trap intencional + `Escape` para sair)

#### Touch targets
- Tamanho minimo: **44x44px** (WCAG 2.2) ou **40x40px** (minimo aceitavel interno)
- Spacing entre alvos adjacentes: minimo **8px** para evitar ativacao acidental
- Em mobile, CTAs primarios: minimo **48x48px** recomendado

#### Tempo e motion
- `prefers-reduced-motion`: obrigatorio em toda animacao
- Nenhuma animacao essencial para compreensao (deve funcionar estaticamente)
- Auto-play de conteudo: pausavel/paravel pelo usuario
- Timeout em acoes: aviso com opcao de extender

### Understandable

#### Linguagem
- `lang` attribute no `<html>` e em trechos de idioma diferente
- Labels descritivos em forms (nao depender de placeholder)
- Mensagens de erro especificas e proximas ao campo

#### Previsibilidade
- Foco nao causa mudanca de contexto automatica
- Input nao causa submissao automatica sem aviso
- Navegacao consistente entre paginas/secoes

#### Assistencia em erros
- Erros identificados e descritos em texto
- Sugestoes de correcao quando possivel
- Oportunidade de revisar antes de submissao irreversivel

### Robust

#### Compatibilidade
- HTML semantico valido (parser nao pode quebrar AT)
- `role`, `name`, `value` corretos para custom widgets
- Status messages via `aria-live` (nao depender de visual)

## WCAG 2.2 Enhancements (Recomendado)

### Focus Not Obscured (2.4.11 AA)
- Elemento com foco nao pode ser completamente coberto por sticky headers, footers, banners
- Regra pratica: garantir pelo menos 50% do focusable visivel quando recebe foco
- Sticky nav + footer = calcular area util de foco

### Dragging Movements (2.5.7 AA)
- Qualquer acao de drag deve ter alternativa nao-drag (botoes, inputs)
- Sortable lists: incluir move up/down buttons
- Sliders: permitir input numerico alternativo

### Target Size (2.5.8 AA)
- Alvos interativos: minimo **24x24px** (AA), **44x44px** (AAA)
- Excecoes: links inline em texto, alvos com equivalente maior na pagina

### Consistent Help (3.2.6 A)
- Mecanismo de ajuda em posicao consistente entre paginas
- Help links, chat, FAQ: mesma localizacao relativa

## Semantic HTML Patterns (Obrigatorio)

### Landmarks
```
<header>     -> banner (unico por pagina)
<nav>        -> navigation (pode ter multiplos com aria-label)
<main>       -> main (unico por pagina)
<aside>      -> complementary
<footer>     -> contentinfo (unico por pagina)
<section>    -> region (com aria-label ou aria-labelledby)
<form>       -> form (com aria-label ou aria-labelledby)
```

### Headings
- Hierarquia sequencial: h1 > h2 > h3 (nao pular niveis)
- Um unico `h1` por pagina (titulo principal)
- Headings descrevem conteudo da secao (nao usados por tamanho visual)
- Secoes sem heading visivel: `aria-label` no container ou heading visually-hidden

### Lists
- Itens de navegacao: `<ul>` + `<li>` (screen readers anunciam contagem)
- Steps sequenciais: `<ol>` + `<li>`
- Termos e definicoes: `<dl>` + `<dt>` + `<dd>`

## ARIA Patterns por Componente

### Modal / Dialog
```
role="dialog" + aria-modal="true"
aria-labelledby -> titulo do modal
Focus trap: Tab circula dentro do modal
Escape: fecha o modal
Ao fechar: foco retorna ao trigger
```

### Accordion
```
<button aria-expanded="true|false" aria-controls="panel-id">
<div id="panel-id" role="region" aria-labelledby="button-id">
Enter/Space: toggle
```

### Tabs
```
role="tablist" > role="tab" + role="tabpanel"
aria-selected="true" na tab ativa
Arrow keys: navegar entre tabs
Tab key: mover para o tabpanel
```

### Menu / Dropdown
```
role="menu" > role="menuitem"
aria-expanded no trigger
Arrow keys: navegar itens
Enter: selecionar
Escape: fechar e retornar foco ao trigger
```

### Toast / Notification
```
role="status" ou aria-live="polite" (informativo)
role="alert" ou aria-live="assertive" (urgente/erro)
Nao usar assertive para sucesso/info
Auto-dismiss: minimo 5 segundos + opcao de pausar
```

### Toggle / Switch
```
role="switch" + aria-checked="true|false"
Texto visivel do estado: "On" / "Off" (nao depender so de cor)
Space: toggle
```

### Carousel / Slider
```
role="region" + aria-label + aria-roledescription="carousel"
Botoes prev/next com aria-label
Indicadores com aria-current
Pause automatico quando focado
```

## Cognitive Accessibility (Frequentemente Ignorada)

### Reducao de carga cognitiva
- Limitar opcoes visiveis por bloco (regra de Miller: 7 +/- 2, preferir 5)
- Progressive disclosure: mostrar detalhes sob demanda
- Agrupamento visual claro (proximity + whitespace)
- Consistencia de patterns: mesmo tipo de acao = mesma aparencia

### Legibilidade
- Line-height minimo: 1.5x tamanho da fonte para body text
- Largura maxima de linha: 80 caracteres (ideal: 60-75)
- Paragrafo spacing: minimo 2x font-size entre paragrafos
- Letter-spacing: minimo 0.12em entre caracteres (quando override aplicado)

### Navegacao previsivel
- Breadcrumbs em hierarquias profundas (>2 niveis)
- Indicador de localizacao ativo em nav
- Feedback imediato em acoes (nao deixar usuario sem resposta >100ms)

### Formularios acessiveis
- Labels visiveis permanentes (nao so placeholder que desaparece)
- Instrucoes antes do campo (nao so apos erro)
- Agrupamento com `<fieldset>` + `<legend>` para conjuntos relacionados
- Autocomplete attributes (`name`, `email`, `tel`, `address-line1`)
- Erro: indicar campo + descrever problema + sugerir correcao

## Dark Mode / Theme Accessibility

- Testar contraste em ambos os temas (light e dark)
- Nao invertir cores simplesmente; repensar hierarquia de superficies
- Sombras podem perder funcao em dark mode (substituir por bordas sutis)
- Imagens com fundo transparente: verificar se permanecem visiveis
- Preferir `prefers-color-scheme` para deteccao automatica
- Prover toggle manual (alguns usuarios preferem dark em ambiente claro)

## Playwright Accessibility Probes

### O que automatizar
- Verificar landmarks: `page.locator('header, main, nav, footer').count()`
- Verificar alt texts: `page.locator('img:not([alt])').count()` deve ser 0
- Verificar focus visibility: `page.keyboard.press('Tab')` + screenshot
- Verificar skip link: focus no primeiro Tab deve ser skip link
- Verificar heading order: extrair headings e validar sequencia

### O que requer revisao manual
- Qualidade dos alt texts (nao so existencia)
- Significado das labels ARIA (nao so presenca)
- Fluxo de leitura em screen reader (ordem logica)
- Contraste em estados interativos (hover, focus, active)

## Checklist Rapido (Pre-Ship)

- [ ] Contraste AA em texto e componentes UI
- [ ] Todos os interativos acessiveis via teclado
- [ ] Focus visivel em todos os interativos
- [ ] Skip link funcional
- [ ] Landmarks semanticos presentes
- [ ] Headings em hierarquia correta
- [ ] Imagens informativas com alt descritivo
- [ ] Forms com labels visiveis e error handling acessivel
- [ ] `prefers-reduced-motion` respeitado
- [ ] Touch targets >= 40px no mobile
- [ ] `aria-live` em acoes assincronas
- [ ] Modal com focus trap + Escape + retorno de foco
- [ ] `lang` attribute no HTML
- [ ] Nenhuma informacao transmitida apenas por cor
