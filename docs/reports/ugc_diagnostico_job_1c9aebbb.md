# Diagnóstico Técnico — Job `1c9aebbb`

## 1. Resumo Executivo
O job `1c9aebbb` preservou bem a **fidelidade estrutural da peça** (resultado técnico forte), mas falhou parcialmente em **desvinculação criativa da referência** no resultado UGC.

Em termos práticos:
- peça correta: **sim**
- linguagem UGC creator/influencer: **parcial**
- risco de "parecer cópia da referência": **presente**

## 2. Evidências
- Imagem final: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/v2edit_1c9aebbb_1/edit_v2edit_1c9aebbb_1_1.png`
- Relatório do job: `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/outputs/v2diag_1c9aebbb/report.json`

Indicadores extraídos do report:
- `stage2.fidelity_gate.verdict`: `pass`
- `stage2.fidelity_gate.fidelity_score`: `0.95`
- `issue_codes`: `[]`
- `identity_reference_risk`: `high`
- `worn_reference_count`: `10`
- `detail_reference_count`: `0`
- `reference_guard_strength`: `high`

## 3. O Que Funcionou
1. Contrato estrutural da peça foi respeitado:
- `garment_subtype=ruana_wrap`
- `sleeve_type=cape_like`
- `hem_shape=cocoon`
- `opening_continuity=continuous`

2. O gate visual confirmou preservação:
- textura e padrão de listras corretos
- arquitetura da peça correta
- sem perda estrutural no resultado final

## 4. O Que Falhou
1. Incoerência de seleção de direção de arte no UGC:
- `scene_family=br_elevator_mirror` (indoor)
- `lighting_profile=coastal_late_morning` (outdoor)
- `styling_profile=off_white_shorts` (vibe de referência, pouca autonomia)

2. Alto acoplamento à referência por composição/energia visual:
- muitas referências vestidas (`worn`) e nenhuma referência de detalhe (`detail`)
- o sistema protegeu peça, mas não separou suficientemente a assinatura visual humana/contextual

## 5. Causa-Raiz
A causa-raiz não está no bloco de fidelidade da peça. Está em três pontos de política:

1. **Vazamento de compatibilidade entre módulos**
- `scene`, `lighting` e `styling` ainda podem ser escolhidos com combinações semanticamente incompatíveis.

2. **Pack de referência enviesado para pessoas vestindo a peça**
- quando `identity_reference_risk` sobe e faltam detalhes de peça isolada, cresce a chance de reproduzir "vibe" da referência.

3. **Guard de identidade forte, mas com foco em traços faciais**
- o guard atual reduz clone de rosto, porém ainda permite herdar linguagem de pose/cenário/styling em excesso.

## 6. Impacto no Produto
- Risco comercial: usuário percebe "IA copiando a referência".
- Risco de confiança: mesmo com fidelidade da peça alta, o resultado pode ser rejeitado por falta de autonomia criativa.
- Risco operacional: inconsistência entre jobs (alguns ótimos UGC, outros com cara de reaproveitamento).

## 7. Plano de Correção (Prioridade)

### P0 — Bloqueio de combinações incoerentes (imediato)
Implementar filtro duro de compatibilidade no sampler:
- indoor mirror/boutique **não pode** usar iluminação outdoor (`coastal_late_morning`, `golden_hour_soft`)
- peça aberta/drapeada espacialmente sensível **não pode** cair em styling de baixa sustentação visual
- `ugc_intent` precisa restringir também `styling`, não só scene/camera/pose

### P1 — Rebalanceamento automático do pack de referência
Quando `identity_reference_risk` for `high`:
- limitar referência vestida
- forçar inclusão de âncoras de detalhe/estrutura
- reduzir transferência de energia humana/contextual

### P1 — Guard semântico anti-cópia contextual
Adicionar cláusulas explícitas no stage2:
- não repetir composição, enquadramento e gesto dominante das referências
- manter peça fiel, mas criar contexto e corporalidade novos

### P2 — Auditoria de coerência no report
Incluir no report uma seção de coerência entre:
- scene vs lighting
- scene vs styling
- ugc_intent vs pose
para detectar regressões automaticamente.

## 8. Critério de Sucesso
Considerar a correção validada quando, em bateria de jobs UGC:
1. fidelidade de peça permanecer >= 0.90
2. não houver combinação incoerente `scene/lighting/styling`
3. cair o número de outputs percebidos como "cópia da referência"
4. manter diversidade de modelo, pose e cenário com leitura comercial.

## 9. Conclusão
O pipeline já resolve bem a fidelidade da peça neste caso. O gap principal agora é **autonomia criativa com coerência de direção de arte**.

Ou seja: não precisamos refazer o núcleo de fidelidade; precisamos fechar a política que decide **como** a peça fiel é encenada no UGC.
