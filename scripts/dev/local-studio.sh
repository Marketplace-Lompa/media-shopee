#!/usr/bin/env bash

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

MODE="start"
HOST="${HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-20}"
BACKEND_LOG="${BACKEND_LOG:-/tmp/media-shopee-backend.log}"
FRONTEND_LOG="${FRONTEND_LOG:-/tmp/media-shopee-frontend.log}"

BACKEND_PID=""
FRONTEND_PID=""

usage() {
    cat <<'EOF'
Uso:
  ./scripts/dev/local-studio.sh [start|restart] [--host HOST] [--backend-port PORT] [--frontend-port PORT] [--timeout SEGUNDOS]

Exemplos:
  ./scripts/dev/local-studio.sh start
  ./scripts/dev/local-studio.sh restart
  ./scripts/dev/local-studio.sh restart --backend-port 8010
  HOST=0.0.0.0 BACKEND_PORT=8010 ./scripts/dev/local-studio.sh restart

Comportamento:
  start   -> valida que as portas estao livres e sobe os servicos
  restart -> libera apenas as portas alvo e sobe os servicos
EOF
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo -e "${RED}Erro: comando obrigatorio ausente: $1${NC}"
        exit 1
    fi
}

require_numeric() {
    local label="$1"
    local value="$2"
    if [[ ! "$value" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Erro: ${label} precisa ser numerico. Recebido: ${value}${NC}"
        exit 1
    fi
}

port_pids() {
    lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null || true
}

assert_port_free() {
    local port="$1"
    local pids
    pids="$(port_pids "$port")"
    if [[ -n "$pids" ]]; then
        echo -e "${RED}Porta ${port} ocupada pelos PIDs: ${pids}${NC}"
        return 1
    fi
}

kill_port() {
    local port="$1"
    local pids
    pids="$(port_pids "$port")"
    if [[ -z "$pids" ]]; then
        echo -e "${BLUE}Porta ${port} ja estava livre.${NC}"
        return 0
    fi

    echo -e "${YELLOW}Liberando porta ${port} (PIDs: ${pids})...${NC}"
    kill $pids 2>/dev/null || true
    sleep 1

    pids="$(port_pids "$port")"
    if [[ -n "$pids" ]]; then
        echo -e "${YELLOW}Forcando encerramento na porta ${port}...${NC}"
        kill -9 $pids 2>/dev/null || true
        sleep 1
    fi

    pids="$(port_pids "$port")"
    if [[ -n "$pids" ]]; then
        echo -e "${RED}Erro: nao foi possivel liberar a porta ${port}.${NC}"
        return 1
    fi
}

format_url_host() {
    if [[ "$1" == *:* ]]; then
        printf '[%s]' "$1"
    else
        printf '%s' "$1"
    fi
}

tail_log() {
    local label="$1"
    local log_file="$2"
    if [[ -f "$log_file" ]]; then
        echo -e "${YELLOW}Ultimas linhas de ${label} (${log_file}):${NC}"
        tail -n 40 "$log_file" || true
    fi
}

cleanup() {
    local exit_code=$?
    trap - EXIT INT TERM

    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    exit "$exit_code"
}

handle_interrupt() {
    echo
    echo -e "${RED}Encerrando Studio local...${NC}"
    exit 0
}

wait_for_url() {
    local url="$1"
    local label="$2"
    local log_file="$3"
    local attempts=$((TIMEOUT_SECONDS * 2))
    local attempt=1

    while [[ $attempt -le $attempts ]]; do
        if curl -fsS "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}${label} pronto em ${url}${NC}"
            return 0
        fi
        sleep 0.5
        attempt=$((attempt + 1))
    done

    echo -e "${RED}Timeout aguardando ${label} em ${url}.${NC}"
    tail_log "$label" "$log_file"
    return 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        start|restart)
            MODE="$1"
            shift
            ;;
        --host)
            HOST="${2:-}"
            shift 2
            ;;
        --backend-port)
            BACKEND_PORT="${2:-}"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="${2:-}"
            shift 2
            ;;
        --timeout)
            TIMEOUT_SECONDS="${2:-}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Argumento desconhecido: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

require_numeric "BACKEND_PORT" "$BACKEND_PORT"
require_numeric "FRONTEND_PORT" "$FRONTEND_PORT"
require_numeric "TIMEOUT_SECONDS" "$TIMEOUT_SECONDS"

require_cmd curl
require_cmd lsof
require_cmd npm

PYTHON_BIN="$ROOT_DIR/app/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    echo -e "${RED}Erro: Python do venv nao encontrado em ${PYTHON_BIN}.${NC}"
    echo "Crie o ambiente em app/.venv antes de subir o Studio local."
    exit 1
fi

if [[ ! -d "$ROOT_DIR/app/frontend/node_modules" ]]; then
    echo -e "${RED}Erro: dependencias do frontend ausentes em app/frontend/node_modules.${NC}"
    echo "Execute: npm -C app/frontend install"
    exit 1
fi

CHECK_HOST="$HOST"
if [[ "$CHECK_HOST" == "0.0.0.0" ]]; then
    CHECK_HOST="127.0.0.1"
elif [[ "$CHECK_HOST" == "::" ]]; then
    CHECK_HOST="::1"
fi

CHECK_HOST_URL="$(format_url_host "$CHECK_HOST")"
BACKEND_URL="http://${CHECK_HOST_URL}:${BACKEND_PORT}"
FRONTEND_URL="http://${CHECK_HOST_URL}:${FRONTEND_PORT}"

trap cleanup EXIT
trap handle_interrupt INT TERM

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Studio local MEDIA-SHOPEE (${MODE})${NC}"
echo -e "${BLUE}================================================${NC}"
echo "Host           : ${HOST}"
echo "Backend porta  : ${BACKEND_PORT}"
echo "Frontend porta : ${FRONTEND_PORT}"
echo "Backend log    : ${BACKEND_LOG}"
echo "Frontend log   : ${FRONTEND_LOG}"
echo

if [[ "$MODE" == "restart" ]]; then
    kill_port "$BACKEND_PORT"
    kill_port "$FRONTEND_PORT"
else
    assert_port_free "$BACKEND_PORT" || {
        echo "Use restart-services.sh ou local-studio.sh restart para limpar a porta."
        exit 1
    }
    assert_port_free "$FRONTEND_PORT" || {
        echo "Use restart-services.sh ou local-studio.sh restart para limpar a porta."
        exit 1
    }
fi

: >"$BACKEND_LOG"
: >"$FRONTEND_LOG"

echo -e "${GREEN}[1/2] Iniciando backend...${NC}"
(
    cd "$ROOT_DIR/app/backend"
    exec "$PYTHON_BIN" -m uvicorn main:app --host "$HOST" --port "$BACKEND_PORT" --reload --log-level info
) >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${RED}Falha ao iniciar o backend.${NC}"
    tail_log "backend" "$BACKEND_LOG"
    exit 1
fi

wait_for_url "${BACKEND_URL}/health" "Backend" "$BACKEND_LOG"

echo
echo -e "${GREEN}[2/2] Iniciando frontend...${NC}"
(
    cd "$ROOT_DIR/app/frontend"
    export VITE_HOST="$HOST"
    export VITE_PORT="$FRONTEND_PORT"
    export VITE_PROXY_TARGET="$BACKEND_URL"
    exec npm run dev -- --host "$HOST" --port "$FRONTEND_PORT" --strictPort
) >"$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo -e "${RED}Falha ao iniciar o frontend.${NC}"
    tail_log "frontend" "$FRONTEND_LOG"
    exit 1
fi

wait_for_url "${FRONTEND_URL}/" "Frontend" "$FRONTEND_LOG"

echo
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Ambiente pronto.${NC}"
echo "Frontend: ${FRONTEND_URL}"
echo "Backend : ${BACKEND_URL}"
echo -e "${BLUE}================================================${NC}"
echo -e "${RED}Pressione CTRL+C para encerrar ambos os servicos.${NC}"

while true; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${RED}Backend encerrou inesperadamente.${NC}"
        tail_log "backend" "$BACKEND_LOG"
        exit 1
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${RED}Frontend encerrou inesperadamente.${NC}"
        tail_log "frontend" "$FRONTEND_LOG"
        exit 1
    fi
    sleep 1
done
