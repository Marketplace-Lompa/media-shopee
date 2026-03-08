# Tooling & DevOps Learnings

Configuração de ambiente, git, terminal, CI/CD e ferramentas de desenvolvimento.

---

## Índice rápido

| Data | Severidade | Resumo |
|---|---|---|
| 2026-03-07 | 🟡 | venv não estava no .gitignore → commit poluído com 2375 arquivos |
| 2026-03-07 | 🟡 | 2>&1 mascara progresso real de comandos longos |

---

## Aprendizados detalhados

---

### [2026-03-07] venv não estava no .gitignore — commit poluído com 2375 arquivos

**Severidade:** 🟡 Importante (commits poluídos, pushes lentos)

**Contexto:** O venv foi criado em `app/.venv/` mas o `.gitignore` não tinha a entrada `app/.venv/`.

**Solução:** Adicionar ao `.gitignore`:
```
# Python venv
app/.venv/
.venv/
venv/
```

**Ação corretiva pendente:** Remover o `.venv` trackado com `git rm -r --cached app/.venv/` no próximo commit.

---

### [2026-03-07] 2>&1 mascara progresso real de comandos longos

**Severidade:** 🟡 Importante (perde observabilidade)

**Contexto:** Redirecionar stderr para stdout (`2>&1`) impedia de acompanhar o progresso real de comandos.

**Problema:** Com `2>&1`, warnings e progress bars são misturados ao stdout normal, e o buffer pode não exibir output parcial até o comando terminar.

**Solução:** Não usar `2>&1` em comandos interativos ou longos. Deixar stderr separado.

**Regra:**
> Só usar `2>&1` quando explicitamente necessário (ex: capturar erros para parsing). Para comandos de desenvolvimento, manter stderr separado.

---

*Próxima entrada: adicionar via `/train` na próxima sessão.*
