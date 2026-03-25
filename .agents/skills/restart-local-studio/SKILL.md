---
name: restart-local-studio
description: Reinicie ou suba o Studio local do MEDIA-SHOPEE de forma deterministica, usando os scripts em scripts/dev para validar portas, limpar apenas as portas alvo quando necessario e permitir troca explicita das portas do backend/frontend.
---

# Restart Local Studio

Use esta skill quando o usuario pedir para iniciar ou reiniciar frontend e backend locais deste workspace.

## Fluxo padrao

1. Use `./scripts/dev/start-dev.sh` quando o usuario quiser apenas subir o Studio e as portas precisarem permanecer intactas.
2. Use `./scripts/dev/restart-services.sh` quando o objetivo for limpar as portas alvo e religar os dois servicos.
3. Valide o resultado com:
   - `curl -fsS http://127.0.0.1:<backend-port>/health`
   - `curl -fsSI http://127.0.0.1:<frontend-port>/`
4. Informe as URLs finais e se algum `--backend-port`, `--frontend-port` ou `--host` foi usado.

## Defaults e overrides

- Host padrao: `127.0.0.1`
- Backend padrao: `8000`
- Frontend padrao: `5173`
- Override de backend: `./scripts/dev/restart-services.sh --backend-port 8010`
- Override de frontend: `./scripts/dev/restart-services.sh --frontend-port 5174`
- Override de host: `./scripts/dev/restart-services.sh --host 0.0.0.0`

## Regras operacionais

- Nao editar o script para trocar porta; prefira flags ou variaveis de ambiente.
- Nao instalar dependencias automaticamente se `app/.venv` ou `app/frontend/node_modules` estiverem ausentes; reporte o bloqueio com o comando necessario.
- Se `start-dev.sh` falhar porque a porta esta ocupada, troque para `restart-services.sh` ou informe claramente qual PID/porta bloqueou a subida.
- Se o usuario mencionar que ja usa a `8000` em outro projeto, proponha `--backend-port 8010` como primeiro ajuste.
