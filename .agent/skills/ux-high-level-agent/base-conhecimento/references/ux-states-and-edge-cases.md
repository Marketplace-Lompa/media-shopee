# UX States and Edge Cases

## Purpose

Documentar todos os estados que uma interface pode assumir alem do "happy path". O agente deve considerar e implementar estes estados em toda reconstrucao ou auditoria, porque a maioria dos problemas de UX aparece fora do estado ideal.

## The 9 States of UI (Framework Obrigatorio)

### 1. Ideal State (Happy Path)
- Conteudo carregado, dados presentes, usuario logado, tudo funcional
- E o estado que a maioria dos designers prototipa
- **Regra:** Nunca projetar apenas este estado

### 2. Empty State (Zero Data)
- Primeiro acesso, lista sem itens, busca sem resultados, inbox vazio
- **Impacto:** Momento critico de retencao; usuario decide se continua ou abandona

#### Patterns
- Ilustracao + headline + descricao + CTA acionavel
- Distinguir "vazio porque novo" vs "vazio porque filtrado" vs "vazio porque deletou tudo"
- Nunca mostrar tabela/lista vazia sem explicacao
- Empty state e oportunidade de onboarding, nao mensagem de erro

#### Exemplos por contexto
- Dashboard sem dados: "Comece conectando sua primeira fonte de dados" + CTA
- Busca sem resultados: "Nenhum resultado para X. Tente termos mais amplos" + sugestoes
- Lista filtrada vazia: "Nenhum item corresponde aos filtros atuais" + botao limpar filtros
- Inbox vazio: "Tudo em dia!" (celebrar, nao punir)

### 3. Loading State
- Dados sendo buscados, acao em processamento, pagina carregando
- **Impacto:** Percepcao de velocidade e confianca no sistema

#### Patterns por duracao
- **< 100ms:** Nenhum indicador necessario (percepcao instantanea)
- **100ms - 1s:** Indicador sutil (opacity reduction, pulse leve no container)
- **1s - 3s:** Skeleton screen ou spinner contextual
- **3s - 10s:** Progress bar ou mensagem de status
- **> 10s:** Background processing com notificacao

#### Skeleton Screens (Preferido sobre Spinners)
- Reproduzir layout aproximado do conteudo esperado
- Usar blocos de cor neutra com animacao shimmer sutil
- Manter dimensoes realistas (nao blocos genericos)
- Skeleton deve desaparecer suavemente ao carregar (fade, nao snap)
- Nunca misturar skeleton com conteudo real no mesmo container

#### Regras de loading
- Indicador proximo da acao (nao spinner global para acao local)
- Manter layout estavel (nao causar layout shift ao carregar)
- Se possivel, carregar progressivamente (conteudo acima do fold primeiro)
- Desabilitar botao durante submissao (prevenir double-click)

### 4. Error State
- Falha de rede, validacao, permissao, servidor, timeout
- **Impacto:** Momento de maior frustacao; comunicacao clara reduz abandono

#### Patterns por tipo
- **Validacao de form:** Inline, proximo ao campo, vermelho sutil + icone + texto
- **Erro de rede:** Banner/toast com opcao de retry
- **Erro de servidor (500):** Pagina dedicada com tom empatetico + opcoes de recuperacao
- **404:** Pagina com busca, links uteis, tom leve
- **Timeout:** Mensagem + auto-retry ou botao manual
- **Permissao negada:** Explicar por que + como obter acesso

#### Regras de error
- Nunca mostrar stack trace, codigos HTTP ou mensagens tecnicas ao usuario
- Sempre oferecer proximo passo (retry, contato, voltar, alternativa)
- Erros de form: nao limpar campos ja preenchidos
- Scroll automatico para o primeiro erro em forms longos
- `aria-live="assertive"` para erros criticos, `polite` para validacao

### 5. Success State
- Acao completada, item salvo, pagamento aprovado, form enviado
- **Impacto:** Confirmacao de que o sistema respondeu corretamente

#### Patterns
- Toast/snackbar para acoes menores (save, copy, toggle)
- Pagina de confirmacao para acoes maiores (compra, cadastro, envio)
- Animacao sutil de checkmark (nao exagerar)
- Proximos passos claros apos sucesso

#### Regras de success
- Feedback visivel por no minimo 3 segundos (auto-dismiss)
- Nao bloquear fluxo com modais de sucesso para acoes triviais
- Tom positivo mas nao infantil
- Se houver numero de referencia/protocolo, exibi-lo com opcao de copiar

### 6. Partial State (Incomplete Data)
- Conteudo parcialmente carregado, perfil incompleto, lista com mix de dados
- **Impacto:** Interface inconsistente se nao tratada

#### Patterns
- Placeholders visuais para dados faltantes (avatar generico, "--" em campos)
- Progress indicator de completude ("Perfil 60% completo")
- Distinguir campo "nao preenchido" de campo "carregando"
- Card com dados parciais deve manter layout estavel (sem colapso)

### 7. Disabled State
- Acao indisponivel por pre-requisito, permissao, ou contexto
- **Impacto:** Confusao se usuario nao entende por que esta desabilitado

#### Patterns
- Visual: reduced opacity (0.4-0.5) + cursor `not-allowed`
- Tooltip ou texto adjacente explicando pre-requisito
- Preferir esconder completamente se a acao nunca sera disponivel
- Se dependente de outra acao: indicar o que fazer primeiro

#### Regras de disabled
- Nunca desabilitar sem explicacao acessivel
- `aria-disabled="true"` + descricao do motivo
- Nao remover do tab order (usuario de teclado precisa encontrar e entender)
- Botao de submit: desabilitar so durante processamento, nao durante preenchimento

### 8. Destructive/Danger State
- Deletar, cancelar assinatura, remover acesso, acao irreversivel
- **Impacto:** Erro aqui tem custo alto; prevencao e obrigatoria

#### Patterns
- Confirmacao explicita (dialog com descricao da consequencia)
- Botao de confirmacao com texto especifico ("Deletar conta" nao "OK")
- Delay antes de habilitar confirmacao em acoes criticas (3-5s)
- Cor de perigo no CTA destrutivo (vermelho) + tom neutro no cancelar
- Undo quando possivel (soft delete > hard delete)

#### Regras de destructive
- Nunca em um unico clique sem confirmacao
- Descrever exatamente o que sera perdido
- Oferecer alternativas quando possivel ("pausar" vs "cancelar")
- Double-confirmation para acoes que afetam outros usuarios

### 9. Offline / Degraded State
- Sem conexao, API indisponivel, funcionalidade parcial
- **Impacto:** Usuario perde confianca se a interface "quebra silenciosamente"

#### Patterns
- Banner persistente indicando modo offline
- Dados em cache visiveis com indicador de "ultima sincronizacao"
- Fila de acoes para sincronizar quando reconectar
- Desabilitar acoes que requerem rede com explicacao

## Edge Cases Criticos (Watchlist do Agente)

### Conteudo
- Texto extremamente longo (nome, email, descricao sem limite)
- Texto vazio ou whitespace-only
- Caracteres especiais, emoji, RTL text
- Numeros muito grandes ou negativos
- Datas invalidas ou no futuro/passado distante
- Imagens com aspect ratio inesperado
- Listas com 0, 1, 2, e 1000+ itens

### Responsividade
- Viewport entre breakpoints (ex: 500px, nao e mobile nem tablet tipico)
- Zoom 200% (WCAG requirement)
- Landscape mobile (frequentemente esquecido)
- Split-screen / PiP no mobile
- Notch / safe area em devices modernos

### Interacao
- Double-click rapido em botoes de submit
- Back button do browser apos submit
- Multiplas tabs com mesma aplicacao
- Copy-paste em campos de senha/confirmacao
- Autofill do browser quebrando layout de forms

### Performance
- Conexao lenta (3G simulation)
- Muitos itens renderizados simultaneamente (virtualizar?)
- Imagens pesadas em mobile
- JavaScript desabilitado (degradacao graceful?)

## Como o Agente Deve Usar Este Documento

### Durante auditoria
- Para cada componente, verificar: quais destes 9 estados foram tratados?
- Priorizar estados por frequencia de ocorrencia no contexto

### Durante reconstrucao
- Implementar pelo menos: ideal + loading + empty + error para todo componente com dados
- Implementar disabled + destructive quando houver acoes

### Durante review
- Encontrou componente sem loading state? -> `Finding: Medium`
- Encontrou acao destrutiva sem confirmacao? -> `Finding: High`
- Encontrou empty state sem orientacao? -> `Finding: Medium`
- Encontrou erro mostrando mensagem tecnica? -> `Finding: High`

## Severidade de Achados por Estado

| Estado ausente | Severidade padrao |
|---|---|
| Error sem tratamento | High |
| Destructive sem confirmacao | High |
| Loading sem indicador (>1s) | Medium |
| Empty sem orientacao | Medium |
| Disabled sem explicacao | Medium |
| Success sem feedback | Minor |
| Partial sem placeholder | Minor |
| Offline sem indicador | Context-dependent |
