# Backend Manual Scripts

Use esta área para scripts que dependem dos módulos de `app/backend`, mas não fazem parte do runtime da aplicação.

- `validation/`: validação manual e loops de avaliação
- `diagnostics/`: diagnósticos pontuais de integração e grounding
- `experiments/`: smoke tests e protótipos operacionais

Regra prática: se um arquivo não é importado pela app em produção, ele deve viver aqui e não em `app/backend/`.
