#!/bin/bash

# Cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Iniciando Ambiente de Desenvolvimento MEDIA-SHOPEE${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Função para matar os processos quando o script for interrompido (Ctrl+C)
cleanup() {
    echo -e "\n${RED}Encerrando servidores (Frontend e Backend)...${NC}"
    # Mata todos os processos em background iniciados por este script
    kill $(jobs -p) 2>/dev/null
    wait $(jobs -p) 2>/dev/null
    echo -e "${GREEN}Servidores encerrados com sucesso.${NC}"
    exit
}

# Configura o trap para capturar Ctrl+C (SIGINT) e chamar a função cleanup
trap cleanup SIGINT SIGTERM

# Diretório base
BASE_DIR="$(pwd)"

# 1. Iniciando o Backend
echo -e "${GREEN}[1/2] Iniciando Backend (FastAPI + Uvicorn)...${NC}"
cd "$BASE_DIR/app/backend" || { echo -e "${RED}Erro: Diretório app/backend não encontrado.${NC}"; exit 1; }

# Verifica se o ambiente virtual existe. Se sim, usa o python dele, senão usa o uvicorn global.
if [ -d "../.venv" ]; then
    echo -e "      Usando ambiente virtual em app/.venv"
    source ../.venv/bin/activate
fi

# Inicia o uvicorn em background. 
# Mantemos o --reload para dev, mas `--limit-concurrency` e `--log-level` protegem contra engasgos.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info --limit-concurrency 10 &
BACKEND_PID=$!
echo -e "      Backend rodando no PID: $BACKEND_PID\n"

# 2. Iniciando o Frontend
echo -e "${GREEN}[2/2] Iniciando Frontend (Vite + React)...${NC}"
cd "$BASE_DIR/app/frontend" || { echo -e "${RED}Erro: Diretório app/frontend não encontrado.${NC}"; exit 1; }

# Inicia o Vite em background
npm run dev &
FRONTEND_PID=$!
echo -e "      Frontend rodando no PID: $FRONTEND_PID\n"

# Retorna ao diretório raiz
cd "$BASE_DIR"

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✨ AMBIENTE PRONTO! ✨${NC}"
echo -e "Frontend URIs : http://localhost:5173"
echo -e "Backend URIs  : http://localhost:8000"
echo -e "${BLUE}================================================${NC}"
echo -e "${RED}Pressione CTRL+C para derrubar tudo.${NC}\n"

# Aguarda indefinidamente os processos em background
wait
