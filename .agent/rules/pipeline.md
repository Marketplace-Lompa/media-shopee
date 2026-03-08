# Pipeline Stability Rules

Este arquivo define as regras de operação para Inteligências Artificiais e Agentes atuando neste repositório, garantindo a estabilidade do pipeline de desenvolvimento (Frontend React + Backend FastAPI).

## Contexto do Problema
Modificações profundas no código (especialmente no backend) durante processos pesados de leitura/escrita podem causar travamentos (Código 137 na memória) ou portas fantasmas deixadas abertas, resultando em "Erro Desconhecido" no frontend.

## Regras Obrigatórias para qualquer LLM/Agent

1. **Evite Hot-Reloading Tóxico:**
   Se estiver editando o backend (`app/backend/`) e houver sessões de geração pesadas rodando, avise o usuário ou use o script de orquestração em vez de depender apenas do hot-reload infinito.

2. **Como Ligar o Projeto:**
   NUNCA peça para o usuário rodar `npm run dev` e `uvicorn` soltos em abas separadas. O repositório possui um orquestrador mestre.
   - Script Master: `./start-dev.sh` (A partir da raiz do projeto).
   - Ele lida com ambos os servidores e possui travas de concorrência e memória.

3. **Como Reiniciar o Workspace em caso de Crash (O /restart):**
   Sempre que o usuário reportar "Caiu", "Não está gerando", ou "O backend parou", NÃO invente soluções complexas de imediato e NÃO mande o usuário reiniciar nada.
   
   Apenas leia o `.agent/workflows/restart.md` (ou proceda com a automação de `/restart`) que consiste em:
   - Limpar portas manualmente: `lsof -ti :5173,8000 | xargs kill -9`
   - Rodar o script: `./start-dev.sh`

4. **Autonomia:**
   O agente DEVE executar o script de restart ele mesmo no terminal (não diga para o usuário "rode este comando", *você* deve rodá-lo por ele).
