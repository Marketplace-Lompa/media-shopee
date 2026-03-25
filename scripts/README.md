# Scripts do Projeto

## `scripts/dev/`

- `local-studio.sh`: launcher deterministico do Studio local com host/portas configuraveis
- `start-dev.sh`: wrapper compatível para subir backend e frontend sem limpar portas
- `restart-services.sh`: wrapper compatível para limpar apenas as portas alvo e reiniciar o studio

## `scripts/diagnostics/`

- checks rápidos e inspeções manuais
- scripts que não fazem parte da suíte de testes automatizados
- utilitários para validar comportamento do pipeline sem poluir a raiz do repositório

## `scripts/backend/`

- `validation/`: harnesses de validação do pipeline e autotestes manuais
- `diagnostics/`: inspeções isoladas de grounding e image search
- `experiments/`: smoke tests e explorações experimentais do backend
