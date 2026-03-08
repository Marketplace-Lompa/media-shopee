# Frontend & UX Learnings

Bugs visuais, padrões CSS e armadilhas de UI/UX do frontend React + Vite.

---

## Índice rápido

| Data | Severidade | Resumo |
|---|---|---|
| 2026-03-07 | 🟡 | :focus-visible global cria borda dupla em elementos compostos |

---

## Aprendizados detalhados

---

### [2026-03-07] :focus-visible global cria borda dupla em elementos compostos

**Severidade:** 🟡 Importante (borda dupla visível = UI quebrada)

**Contexto:** Input de chat com container `.chat-input-box` (borda via `:focus-within`) e `textarea` interno.

**Problema:** O `index.css` tinha regra global:
```css
:focus-visible {
  outline: 2px solid var(--brand-primary);
  outline-offset: 2px;
}
```
Isso aplicava outline no textarea interno, criando efeito de "borda dentro de borda roxa". O `outline: none` no `.chat-textarea` perdia para o `:focus-visible` global por ordem de cascade.

**Solução:** Adicionar regra com especificidade maior:
```css
.chat-textarea:focus,
.chat-textarea:focus-visible {
    outline: none;
}
```

**Regra:**
> Ao criar componentes compostos (wrapper + input), sempre suprimir `:focus-visible` no elemento interno se o wrapper já tem `:focus-within`. Usar seletor composto `.classe:focus-visible` para vencer o global.

---

*Próxima entrada: adicionar via `/train` na próxima sessão.*
