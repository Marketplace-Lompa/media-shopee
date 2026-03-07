# Tasks — Aplicação Local de Geração de Imagens

## Fase 1 — Planejamento
- [x] Entender o fluxo do usuário
- [x] Criar implementation_plan.md
- [ ] Aprovação do usuário

## Fase 2 — Backend (FastAPI)
- [ ] Setup do projeto (estrutura de pastas, deps, .env)
- [ ] Módulo de sessões/produtos (criar, listar, deletar)
- [ ] Módulo de upload de imagens (referências)
- [ ] Módulo LoRA-like (adicionar imagens geradas ao pool de referência)
- [ ] Prompt Agent — lê skills + analisa imagens + otimiza prompt para Nano Banana
- [ ] Endpoint de geração de imagens (injeta agent + safety config + parâmetros de marketplace)
- [ ] Endpoint de galeria (imagens geradas por sessão)
- [ ] WebSocket ou SSE para streaming do progresso de geração

## Fase 3 — Frontend (React + Vite)
- [ ] Setup do projeto React com design system minimalista
- [ ] Sidebar de sessões/produtos
- [ ] Área de upload de referências (drag & drop)
- [ ] Visualizador do pool de referência (incluir geradas no LoRA)
- [ ] Chat interface com agente de prompts
- [ ] Área de geração: prompt editável + parâmetros (proporção, resolução)
- [ ] Galeria de resultados com ação "adicionar ao pool"

## Fase 4 — Verificação
- [ ] Testar backend endpoints via curl/httpie
- [ ] Testar fluxo completo frontend → backend → Gemini → geração
- [ ] Testar adição de imagem gerada ao pool de referência
