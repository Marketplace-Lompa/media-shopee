# Plano de Implementação: UX/UI Nível Higgsfield AI

Este plano descreve as etapas para transformar a interface do MEDIA-SHOPEE em um "Command Center" de alto nível, inspirado na plataforma Higgsfield AI. O foco será em estética premium (dark mode profundo), interações fluidas (micro-motion) e clareza visual, sem a necessidade de adicionar frameworks CSS pesados (manteremos Vanilla CSS + Framer Motion).

## User Review Required

> [!WARNING]
> Este plano propõe mudanças estéticas significativas no frontend da aplicação. A identidade visual será atualizada para um tom mais cinematográfico e profissional, focado em "criadores" (Creators/Filmmakers aesthetic).

## Proposed Changes

### Global Design System (`app/frontend/src/index.css`)

Substituição da paleta atual e inclusão de utilitários premium:
- Redefinir `--surface-bg` para preto absoluto ou quase absoluto (`#050505` ou `#0a0a0a`) para contraste máximo estilo sala de cinema.
- Atualizar tipografia para usar letter-spacing mais elegante em headings.
- Adicionar tokens de **Glassmorphism** (fundos semitransparentes translúcidos com backdrop-blur) para painéis flutuantes e modais.
- Aprimorar `--surface-border-subtle` para usar bordas quase imperceptíveis que dão profundidade.
- Melhorar a definição do skeleton loader (shimmer) para ficar mais fosco e sofisticado.

#### [MODIFY] `index.css`

### App Shell & Layout (`app/frontend/src/App.tsx`)

- Ajustar o layout principal para se comportar como um software nativo (workspace edge-to-edge).
- Refinar a Lightbox para uso de backdrop-blur massivo e animações de escala mais lentas/suaves.

#### [MODIFY] `App.tsx`

### Componentes Core (`app/frontend/src/components/*`)

- **`Sidebar.tsx`**: Tornar a navegação lateral mais esguia, com ícones minimalistas e indicadores de active state mais sutis (pill-shaped markers e fade-ins).
- **`ChatInput.tsx`**: Transformar a barra de input em uma "Floating Command Bar", semelhante a interfaces de IA modernas, com bordas translúcidas e glow dinâmico.
- **`Gallery.tsx`** e **`PoolPanel.tsx`**: Ajustar o espaçamento do grid de imagens (masonry/bento style), implementando hover states de reveal suave nas ações das imagens (download, edit) e arredondamentos elegantes.

#### [MODIFY] `Sidebar.tsx`
#### [MODIFY] `ChatInput.tsx`
#### [MODIFY] `Gallery.tsx`

## Verification Plan

### Testes Manuais Visuais
Após a aplicação das mudanças:
1. O usuário (ou eu mesmo, via auditoria) deve abrir a interface web (http://localhost:5173).
2. Avaliar visualmente o contraste do novo Dark Mode.
3. Testar `hover` e cliques nos botões da Sidebar e na Galeria.
4. Testar a transição da Lightbox para garantir performance de framerate (sem lentidão com o backdrop blur).
5. Observar responsividade em dispositivos mobile simulados.
