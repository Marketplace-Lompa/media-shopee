#!/bin/bash
echo "Encerrando portas 8000 e 5173..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
echo "Portas limpas."
./start-dev.sh
