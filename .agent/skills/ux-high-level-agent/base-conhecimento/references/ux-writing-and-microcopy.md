# UX Writing and Microcopy

## Purpose

Orientar a producao de texto em interfaces. Microcopy e tao importante quanto layout e motion para a experiencia do usuario. Texto ruim numa UI excelente ainda e uma UI ruim.

## Principios Fundamentais

### 1. Clareza sobre Criatividade
- O usuario precisa entender, nao admirar
- Copy inteligente que confunde e pior que copy simples que funciona
- Jargao tecnico so quando o publico e tecnico

### 2. Acao sobre Descricao
- Dizer o que o usuario pode fazer, nao o que o sistema e
- "Comece a monitorar" > "Sistema de monitoramento disponivel"
- CTAs com verbo de acao: "Criar conta" nao "Cadastro"

### 3. Empatia sobre Eficiencia
- Em erros: nao culpar o usuario
- "Nao encontramos resultados" > "Busca invalida"
- "Ops, algo deu errado do nosso lado" > "Erro 500"

### 4. Consistencia sobre Variedade
- Mesmo conceito = mesma palavra em toda a interface
- Se e "projeto" na nav, nao e "workspace" no dashboard e "area" no settings
- Criar glossario do produto com termos canonicos

## Anatomia do Microcopy por Componente

### Buttons / CTAs
```
Primario:  [Verbo] + [Objeto]     -> "Criar projeto"
                                   -> "Enviar mensagem"
                                   -> "Comecar teste gratis"

Secundario: [Verbo contextual]    -> "Saiba mais"
                                   -> "Ver detalhes"
                                   -> "Pular por agora"

Destrutivo: [Verbo explicito]     -> "Deletar conta"
                                   -> "Remover membro"
            NUNCA "OK" ou "Sim"    -> Usuario precisa saber o que confirma
```

#### Regras de CTA
- Maximo 3-4 palavras (ideal: 2)
- Comeca com verbo
- Sem ponto final
- Nao repetir o mesmo CTA com significados diferentes na mesma pagina
- CTA primario: acao principal da pagina (1 por secao, idealmente)

### Headlines / Titles
```
Hero:     Proposta de valor em 1 linha
          "Gerencie financas sem complexidade"
          NAO: "Bem-vindo ao FinanceApp"

Section:  O que o usuario vai encontrar aqui
          "Funcionalidades que simplificam seu dia"
          NAO: "Funcionalidades" (vago)

Card:     Beneficio concreto
          "Relatorios automaticos"
          NAO: "Modulo 3"
```

#### Regras de headline
- Hero: maximo 8-10 palavras
- Subtitulo: expandir com contexto, maximo 2 linhas
- Evitar superlativos vazios ("o melhor", "incrivel", "revolucionario")
- Usar numeros quando possivel ("50% mais rapido" > "muito mais rapido")

### Forms

#### Labels
- Curto e especifico: "Email corporativo" > "Insira seu endereco de email da empresa"
- Sempre visivel (nunca so placeholder)
- Sem dois pontos no final

#### Placeholders
- Exemplo de formato, nao instrucao: "joao@empresa.com" > "Digite seu email"
- Nunca como substituto do label
- Tom mais leve que o label (cor mais clara, mas com contraste AA)

#### Helper Text
- Quando antecipar duvida: "Minimo 8 caracteres, incluindo 1 numero"
- Posicionar abaixo do campo, antes do erro
- Tom informativo e neutro

#### Error Messages
```
Formato:  [O que aconteceu] + [Como resolver]

Bom:      "Email invalido. Use o formato nome@dominio.com"
Ruim:     "Erro no campo email"
Pessimo:  "Validation error: field_email regex mismatch"
```

#### Success Messages
- Confirmacao breve: "Salvo" / "Enviado" / "Copiado"
- Para acoes maiores: "Conta criada! Verifique seu email para ativar"

### Empty States
```
Formato:  [Estado] + [Explicacao] + [Acao]

"Nenhum projeto ainda"
"Crie seu primeiro projeto para comecar a organizar suas tarefas."
[Criar projeto]
```

#### Regras de empty state
- Tom encorajador, nao clinico
- Distinguir "vazio porque novo" vs "vazio porque filtrado"
- Filtro sem resultado: "Nenhum resultado para [termo]. Tente termos mais amplos."
- Inbox vazio: "Tudo em dia!" (celebrar, nao reportar ausencia)

### Tooltips
- Maximo 1-2 linhas
- Responder: "O que isso faz?" ou "Por que preciso disso?"
- Nao repetir o que ja esta visivel no label
- Usar para explicar conceitos, nao para instrucoes basicas

### Notifications / Toasts
```
Sucesso:   "Projeto salvo"                          (3-5s, auto-dismiss)
Info:      "Nova versao disponivel. Recarregue."     (persistente com acao)
Warning:   "Sua sessao expira em 5 minutos"          (persistente)
Erro:      "Falha ao salvar. Tente novamente."       (persistente com retry)
```

#### Regras de notification
- Comeca com o que aconteceu, nao com "Atencao:" ou "Sucesso!"
- Acoes: maximo 1-2 botoes (link de acao principal + dismiss)
- Nao empilhar mais de 3 toasts simultaneos
- Prioridade visual: erro > warning > info > sucesso

### Modais / Dialogs
```
Titulo:   [O que vai acontecer]
          "Deletar projeto X?"

Body:     [Consequencia]
          "Todos os dados e arquivos serao removidos permanentemente."

Actions:  [Cancelar] [Deletar projeto]     <- especifico, nao "Sim" / "OK"
```

### Loading States
```
Curto (<3s):   Nenhum texto, so skeleton/spinner
Medio (3-10s): "Carregando seus dados..."
Longo (>10s):  "Processando... Isso pode levar alguns segundos."
Background:    "Gerando relatorio. Voce sera notificado quando estiver pronto."
```

### 404 / Error Pages
```
Tom leve + opcoes de recuperacao:

"Pagina nao encontrada"
"O endereco pode ter sido movido ou digitado incorretamente."
[Ir para inicio]  [Buscar]
```

## Tom de Voz por Contexto

### Profissional / SaaS B2B
- Direto, confiavel, sem excesso de personalidade
- "Gerencie equipes com clareza" > "Vamos revolucionar a gestao!"
- Humor: quase zero, reservado para empty states inofensivos

### Consumer / B2C
- Mais acessivel, leve, pode ser amigavel
- "Encontre ofertas perto de voce" > "Consulte estabelecimentos na area"
- Humor: dosado, nunca em erros ou acoes destrutivas

### Fintech / Health
- Preciso, transparente, empatetico
- Numeros exatos, sem ambiguidade
- Nunca banalizar erros envolvendo dinheiro ou saude

### Creative / Agency
- Mais expressivo, pode brincar com linguagem
- Ainda precisa ser claro em CTAs e navegacao
- Criatividade na voz, nao na usabilidade

## Anti-Patterns de Escrita

- **"Clique aqui"** -> Usar texto descritivo do destino
- **"Voce tem certeza?"** -> Descrever a consequencia da acao
- **Placeholder como label** -> Desaparece ao digitar, perde contexto
- **Lorem ipsum em produção** -> Nunca; copy real ou placeholder declarado
- **Mensagem de erro generica** -> "Algo deu errado" sem proximo passo
- **Dupla negacao** -> "Nao deseja nao receber?" (ilegivel)
- **Excesso de exclamacao** -> "Parabens!!!" (infantil em contexto profissional)
- **Tom passivo-agressivo** -> "Senha errada. De novo." (hostil)

## Checklist de UX Writing (Pre-Ship)

- [ ] CTAs com verbo de acao + objeto
- [ ] Nenhum "Clique aqui" ou "Saiba mais" sem contexto
- [ ] Labels de form visiveis (nao so placeholder)
- [ ] Mensagens de erro especificas com sugestao de correcao
- [ ] Empty states com orientacao e CTA
- [ ] Terminologia consistente em toda a interface
- [ ] Tom adequado ao contexto e publico
- [ ] Textos de loading para acoes > 3s
- [ ] Confirmacao explicita em acoes destrutivas
- [ ] Nenhum jargao tecnico exposto ao usuario final
