---
name: validate-frontend
description: Validate frontend UX/rendering with Playwright in headless mode, capturing screenshots and runtime evidence without opening browser windows. Use when asked to verify if pages render correctly, detect visible layout regressions, or confirm authenticated dashboard flows.
---

# Validate Frontend

Use this skill to prove frontend UX status with runtime evidence, without disturbing the user's screen.

## Non-Intrusive Principle

- Always run Playwright headless (no browser window on screen).
- Use screenshots and console/runtime output as proof.
- Do not edit code unless user explicitly asks for fixes.

## Preconditions

1. Frontend should be reachable at `https://local.lompa.com.br:3000`.
2. Backend must be online for authenticated dashboard flows.
3. Bypass auth token works only when backend is not in production mode.

## Execution Workflow

1. Preflight checks:
- Verify host responds:
  - `curl -k -I https://local.lompa.com.br:3000`
- If down, report blocker before running tests.

2. Run validation suite (headless):
```bash
cd /Users/lompa-marketplace/Documents/lompa-marketplace/erp-lompa/frontend
CI=1 npx playwright test e2e/validate-frontend.spec.ts --project=chromium --reporter=list
```

3. Inspect generated artifacts:
- `frontend/e2e/screenshots/home.png`
- `frontend/e2e/screenshots/produtos.png`
- `frontend/e2e/screenshots/pedidos.png`
- `frontend/e2e/screenshots/integracoes.png`
- `frontend/e2e/screenshots/configuracoes.png`

4. Report per page:
- `PASS` / `FAIL`
- final URL (to detect `/login` or unexpected redirects)
- visible layout issues (overflow, clipping, overlap, blank content)
- relevant console errors captured during run

## Failure Triage

- Redirected to `/login`:
  - backend offline, cookie not accepted, or production mode blocking bypass token.
- Blank/partial screen:
  - check console errors and runtime exceptions.
- Layout regressions:
  - point to screenshot + likely component/area affected.

## Output Contract

Use concise, evidence-first output:

```markdown
# Frontend Validation

## Environment
- URL: ...
- Server reachable: yes/no
- Test command: ...

## Page Results
- home: PASS/FAIL — notes
- produtos: PASS/FAIL — notes
- pedidos: PASS/FAIL — notes
- integracoes: PASS/FAIL — notes
- configuracoes: PASS/FAIL — notes

## Console/Runtime Issues
- ...

## Overall
- Status: HEALTHY | DEGRADED | BROKEN
- Next action: ...
```
