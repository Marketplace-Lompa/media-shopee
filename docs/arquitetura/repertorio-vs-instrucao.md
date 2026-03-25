# Repertório vs Instrução — Plano para Reduzir Repetição no Prompt Agent

> **Status:** Contexto arquitetural consolidado
> **Escopo:** V1 · `fashion` · modo livre · sem input de imagem
> **Última atualização:** 2026-03-25

---

## 1. Problema

O Prompt Agent está sofrendo com um padrão recorrente de **repetição semântica**.

Os sintomas mais visíveis são:

- repetição de personas como `radiant Baiana`, `contemporary Mineira`, `fresh-faced Brasília native`
- repetição de cenários muito próximos entre si, mesmo quando o `mode` muda
- sensação de que o modelo está sempre orbitando o mesmo mundo visual:
  - premium urbano
  - rooftop / terrace / shopping district
  - modelo “quente comercial” com pouca distância perceptiva entre gerações

O problema não é apenas falta de diversidade.

O problema principal é que o sistema está colocando **repertório auxiliar perto demais da superfície textual do modelo**.

---

## 2. Contexto Atual

Hoje, no `text_mode` sem imagem, o Gemini recebe três camadas principais de guidance:

1. **System / Base**
- regras do agente
- regras de moda
- contrato de saída

2. **`<MODE_PRESETS>`**
- guidance abstrato do `mode`
- ex.:
  - `scenario family: clean urban or refined indoor commercial backdrop`
  - `casting: model presence should feel natural, warm, and commercially believable`

3. **`<DIVERSITY_TARGET>`**
- persona
- cenário
- pose
- formulados com texto muito específico

Exemplos atuais:

- `A radiant Baiana warm e-commerce lookbook presence...`
- `rooftop garden terrace with city skyline in late afternoon light`
- `caught mid-turn, garment flowing naturally, effortless off-duty model vibe`

Na prática, esse material entra como “ajuda”, mas o LLM lê isso como **caminho preferido de resolução**.

---

## 3. Diagnóstico Consolidado

### 3.1 O concreto está vencendo o abstrato

O `MODE_PRESETS` já está em um nível bom de abstração.

Mas o `DIVERSITY_TARGET` injeta exemplos concretos demais:

- persona pitoresca
- cenário quase pronto
- pose estilizada

Resultado:

- o modelo replica a biblioteca
- o `mode` perde parte do seu papel
- o repertório deixa de ser repertório e vira trilho

### 3.2 As listas são curtas e compartilhadas

Hoje há pools fixas para:

- `_VIBES`
- `_CASTING_TONES`
- `_POSE_POOL_BY_ENERGY`
- `_SCENARIO_POOL_BY_FAMILY`

Problemas:

- pools curtas demais
- compartilhamento entre vários `modes`
- anti-repeat real apenas para pose/cenário local
- praticamente nenhum anti-repeat útil para persona / atmosfera

### 3.3 Os cenários variam no nome, mas não no mundo

Mesmo quando os valores mudam, muitos cenários continuam semanticamente próximos:

- rooftop
- terrace
- shopping district
- urban clean
- outdoor café

Ou seja:

- a variação é lexical
- o mundo visual continua parecido

O que falta não é só anti-repeat de string.
Falta **anti-repeat atmosférico**.

---

## 4. Princípio Arquitetural

**O LLM deve sentir direção, não biblioteca.**

Isso significa:

- o sistema pode manter repertório interno
- mas não deve despejar esse repertório cru no prompt

Regra central:

**repertório interno ≠ instrução textual visível**

Hoje o sistema está confundindo essas duas coisas.

---

## 5. Decisões Tomadas

### 5.1 Estrutura principal

A arquitetura de variação visual da V1 continua sendo:

- **Base**
- **Modes**
- **Presets**

Sem `overlay` nesta fase.

### 5.2 Realismo

`realismo` não é:

- `mode`
- `preset`
- `overlay`

`realismo` é um **princípio base sempre-on**.

### 5.3 O repertório não deve mais entrar como frase pronta

As listas de apoio devem:

- continuar existindo internamente
- orientar a decisão
- alimentar tracking / anti-repeat / logging

Mas o que chega ao LLM deve ser:

- mais curto
- mais abstrato
- menos pitoresco
- menos memorável como wording

### 5.4 `MODE_PRESETS` fica como camada principal de direção

O bloco `<MODE_PRESETS>` já está no nível certo:

- abstrato
- diretivo
- sem descrever demais

O problema principal está no `DIVERSITY_TARGET`.

---

## 6. Arquitetura-Alvo

### 6.1 Três camadas mentais

1. **Regra de negócio do mode**
- define o território visual permitido
- ex.:
  - `Catálogo Clean`
  - `Natural`
  - `Lifestyle`
  - `Editorial Comercial`

2. **Repertório interno**
- pools
- famílias
- eixos semânticos
- tracking
- anti-repeat

3. **Compilação leve**
- o que efetivamente entra no prompt
- poucas instruções
- wording discreto

### 6.2 O que o modelo deve receber

O modelo deve receber:

- `MODE_PRESETS`
- hints curtos de diversidade
- name blending quando útil

O modelo não deve receber:

- biblioteca crua de personas
- cenários literais completos
- frases prontas muito características
- exemplos memoráveis demais

---

## 7. Solução Recomendada

### 7.1 Persona / casting

Migrar de rótulos prontos como:

- `radiant Baiana`
- `fresh-faced Brasília native`
- `contemporary Mineira`

Para composição mais abstrata, por exemplo:

- energia de presença
- calor humano
- polimento comercial
- name blending brasileiro

Exemplo de direção desejada:

`A warm, commercially believable Brazilian fashion model, features blend 'X' and 'Y'.`

Objetivo:

- manter diversidade facial
- reduzir estereótipo / assinatura repetitiva
- evitar âncoras fortes demais

### 7.2 Cenário

Migrar de microcenários literais para famílias semânticas realmente contrastantes.

Em vez de:

- `rooftop garden terrace with city skyline...`
- `shopping district with softly blurred storefronts...`
- `outdoor café frontage...`

Trabalhar primeiro com famílias como:

- estúdio mínimo
- urbano funcional
- urbano texturizado
- residencial casual
- natureza suave
- arquitetura premium
- cotidiano social

E só depois, se necessário, compilar uma formulação curta.

### 7.3 Pose

Pose ainda precisa de mais controle do que cenário.

Portanto:

- manter pool
- mas reduzir o wording
- frases mais curtas e funcionais

Exemplo:

- `stable standing, garment legible`
- `relaxed posture, soft weight shift`
- `candid mid-motion, garment readable`

### 7.4 `DIVERSITY_TARGET`

O bloco deve ficar mínimo.

Ele não deve mais carregar:

- meta-instruções longas
- persona pitoresca
- cenário já quase final
- pose cinematográfica pronta

Ele deve só reforçar:

- unicidade
- direção geral
- e obediência ao `mode`

---

## 8. Opções Consideradas

### Opção A — Melhorar as listas atuais

Trocar wording forte por wording mais neutro.

**Prós**
- mudança pequena

**Contras**
- continua deixando repertório textual demais no prompt

### Opção B — Repertório composicional

Transformar persona e cenário em eixos semânticos internos, compilados de forma leve.

**Prós**
- melhor equilíbrio entre direção e liberdade
- elimina rótulos fortes demais
- aumenta combinação possível

**Contras**
- exige refatorar o sampler

### Opção C — Tirar quase todo repertório do prompt

Deixar pools só server-side e mandar ao modelo quase só o `MODE_PRESETS`.

**Prós**
- reduz drasticamente a repetição

**Contras**
- pode soltar demais o modelo cedo demais

### Decisão

Seguir com:

- **Opção B como base**
- com elementos leves de **C**

Ou seja:

- repertório interno mais composicional
- `DIVERSITY_TARGET` muito mais enxuto
- `MODE_PRESETS` como camada dominante de direção

---

## 9. Plano em Microtarefas

### MT1 — Refatorar persona

Objetivo:

- tirar rótulos regionais/literais da superfície do prompt

Fazer:

- substituir `_VIBES` e `_CASTING_TONES` por eixos composicionais
- manter name blending
- reduzir especificidade regional por padrão

### MT2 — Refatorar pose

Objetivo:

- manter controle sem ancoragem exagerada

Fazer:

- encurtar frases de pose
- focar em legibilidade da peça e energia corporal

### MT3 — Refatorar cenário

Objetivo:

- aumentar contraste semântico real entre mundos visuais

Fazer:

- redesenhar famílias de cenário
- separar melhor os mundos por `mode`
- reduzir compartilhamento excessivo

### MT4 — Reescrever `DIVERSITY_TARGET`

Objetivo:

- transformar o bloco em guidance leve

Fazer:

- remover meta-instruções longas
- remover exemplos quase finais
- manter só hints discretos

### MT5 — Anti-repeat real

Objetivo:

- impedir repetição imediata de atmosfera/persona

Fazer:

- cooldown por família semântica
- memória curta por mode
- evitar repetição de wording e não só de string exata

### MT6 — Validação

Objetivo:

- provar ganho real

Fazer:

- testes estatísticos de repetição
- testes reais com os 4 `modes`
- análise comparativa:
  - fidelidade da peça
  - distância entre modes
  - repetição de persona
  - repetição de cenário
  - manutenção de qualidade comercial

---

## 10. Regra de Ouro

Se existir apenas uma mudança a fazer, que seja esta:

**parar de mostrar a biblioteca para o modelo.**

O repertório deve continuar existindo, mas como:

- estrutura de decisão
- suporte de compilação
- mecanismo de diversidade

e não como:

- texto quase final
- frase pronta
- exemplo memorável demais

---

## 11. Resumo Executivo

O problema atual não é falta de diversidade; é a forma errada de injetar repertório.

Hoje:

- listas auxiliares entram como texto forte demais
- o modelo as copia
- os `modes` perdem força
- casting e cenário convergem

Direção aprovada:

- manter `modes + presets`
- tratar repertório como estrutura interna
- usar compilação leve e abstrata
- reduzir drasticamente frases prontas no `DIVERSITY_TARGET`

Em uma frase:

**o sistema deve usar a biblioteca para decidir, não para escrever pelo modelo.**
