# Stitch Reference

Origem: `stitch.zip` analisado em 2026-03-24  
Objetivo: preservar este material como referência de UX, direção visual e framing de produto para uso posterior no Studio.

---

## O que é este material

Esta pasta guarda uma referência externa de interface para um workspace de IA com foco profissional.

O pacote original continha:

- [DESIGN.md](./DESIGN.md)
- [code.html](./code.html)
- [screen.png](./screen.png)

Classificação do material:

- `DESIGN.md`
  - documento de direção visual e design system
- `code.html`
  - mockup HTML estático com Tailwind via CDN
- `screen.png`
  - screenshot da proposta visual

Importante:

- isto **não** é uma base pronta de implementação;
- isto **não** é frontend de produção;
- isto **é** uma referência de produto e UX de alto nível.

---

## Por que foi guardado

Este material conversa bem com a direção que o Studio vem tomando:

- tom profissional em vez de estética “AI toy”
- foco em operação de mídia para marketplace
- contexto ativo visível no topo
- distinção clara entre setup, modos de produção e saída
- sensação de ferramenta de produção, não de playground

Em vez de apenas manter o `zip` solto fora do repo, esta pasta registra o material como referência viva de UX.

---

## O que vale absorver depois

### 1. Contexto ativo no topo

O mockup mostra uma barra de contexto com:

- categoria ativa
- modo de trabalho
- canal
- preset
- contexto de cena

Isso é valioso porque transforma o produto de “prompt input” em “workspace configurado”.

### 2. Modo de produção como conceito central

O bloco `Production Modes` é uma boa referência para organizar o produto por intenção operacional:

- on model
- clean catalog
- color variations
- details
- lifestyle premium

Essa lógica aproxima a UI do trabalho real do usuário.

### 3. Framing de ferramenta premium

O `DESIGN.md` propõe uma estética útil para o Studio:

- monocromática
- técnica
- editorial
- sem tropeços visuais de produto genérico de IA

Isso é especialmente útil para um produto voltado a e-commerce profissional.

### 4. Separação forte entre input e output

O layout valoriza:

- área de setup e entrada
- área de preview/produção
- resumo operacional de saída

Isso é mais maduro do que interfaces centradas apenas em chat.

---

## O que não deve ser absorvido cegamente

### 1. Não tratar o HTML como base técnica

O [code.html](./code.html) é estático:

- sem estado real
- sem integração com backend
- sem modelagem de componentes do produto
- sem evidência de acessibilidade robusta
- sem comportamento real de app

Ele é útil como referência visual, não como fundação de frontend.

### 2. Não importar rótulos genéricos sem adaptação

Alguns labels do mockup são bons como direção, mas não necessariamente casam com o fluxo real atual do Studio.

Eles devem servir como inspiração, não como contrato.

### 3. Não deixar a estética liderar a lógica

O principal valor deste material está no framing de produto e hierarquia de interface.

A implementação futura deve continuar guiada pela lógica do sistema:

- categoria
- workflow
- contexto ativo
- geração
- revisão
- histórico
- biblioteca

---

## Leitura recomendada desta pasta

1. Ver [screen.png](./screen.png)
   - para entender rapidamente a proposta visual e de hierarquia
2. Ler [DESIGN.md](./DESIGN.md)
   - para absorver a linguagem de design system
3. Consultar [code.html](./code.html)
   - apenas para inspeção estrutural e tokens visuais

---

## Aplicação futura no projeto

Quando este material for usado, ele deve influenciar principalmente:

- home do Studio
- organização do fluxo `criar`
- conceito de barra de contexto ativo
- exposição de categoria, workflow e preset
- tom visual geral do produto

Não deve ser usado diretamente para:

- copiar layout 1:1
- definir arquitetura de componentes
- decidir estados de aplicação
- substituir discovery de UX do produto atual

---

## Resumo executivo

Esta referência é valiosa porque mostra um Studio de IA com cara de ferramenta profissional de produção.

O maior valor aqui não é o HTML em si, mas:

- a direção visual
- a hierarquia de informação
- a ideia de `contexto ativo`
- a organização por `modos de produção`

Essa pasta foi criada para que esse material possa ser revisitado mais tarde com rastreabilidade e sem depender de um arquivo solto em `Downloads`.
