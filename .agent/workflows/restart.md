---
description: Reinicia os servidores de desenvolvimento (Frontend React e Backend FastAPI). Limpa portas travadas e inicia o pipeline estabilizado.
---

Quando você utilizar o comando `/restart`, siga os passos abaixo de forma autônoma:

1. Na raiz do projeto, prefira o launcher determinístico:
```bash
./scripts/dev/restart-services.sh
```
2. Se o backend precisar subir em outra porta, passe explicitamente:
```bash
./scripts/dev/restart-services.sh --backend-port 8010
```
3. Valide a saúde do backend e do frontend:
```bash
curl -fsS http://127.0.0.1:<backend-port>/health
curl -fsSI http://127.0.0.1:5173/
```
4. Responda ao usuário informando as URLs finais e qualquer override de porta/host que tenha sido usado.
