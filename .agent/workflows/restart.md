---
description: Reinicia os servidores de desenvolvimento (Frontend React e Backend FastAPI). Limpa portas travadas e inicia o pipeline estabilizado.
---

Quando você utilizar o comando `/restart`, siga os passos abaixo de forma autônoma:

1. Mate os processos antigos que eventualmente ficaram travados (FastAPI na 8000, Vite na 5173) e confirme se o seu Mac não estava segurando processos zumbis.
// turbo-all
2. Limpe as portas executando o comando (na raiz do projeto):
```bash
lsof -ti :5173,8000 | xargs kill -9 2>/dev/null || true
```
3. Execute o script mestre `start-dev.sh` contendo o orquestrador seguro com limites de memória:
```bash
./start-dev.sh
```
4. Responda ao usuário com uma mensagem curta e clara informando que o ambiente local (Portas 5173 e 8000) foi reiniciado com sucesso via script estabilizado, e valide se a saúde do projeto está okay.
