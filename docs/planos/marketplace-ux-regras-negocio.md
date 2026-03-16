# Plano Marketplace UX + Regras de Negócio (Shopee/ML) com Shots Independentes

Data: 2026-03-15

## 1. Resumo

Implementar um fluxo de Marketplace em que **cada foto é gerada de forma independente** (um prompt por slot), evitando geração múltipla com mesmo prompt para capa/ângulos/cores.

O fluxo terá 2 operações separadas:

1. **Variação principal**: gera exatamente **5 fotos** (kit fixo).
2. **Variações de cor**: a partir da variação principal + referências de cor, gera **3 fotos por cor**.

## 2. Mudanças de implementação

### 2.1 Domínio de negócio (núcleo)

1. Criar `marketplace_policy_resolver` com canais `shopee` e `mercado_livre` usando a mesma lógica base, com ajustes finos por canal.
2. Definir receitas de shot (imutáveis):
   - `main_variation` (5): `hero_front`, `front_3_4`, `back_or_side`, `fabric_closeup`, `functional_detail_or_size`.
   - `color_variation` (3 por cor): `color_hero_front`, `color_front_3_4`, `color_detail`.
3. Separar claramente “gerar variação principal” de “gerar cores” como operações distintas.

### 2.2 API e interfaces públicas

1. Adicionar payload específico de marketplace (novo contrato):
   - `marketplace_channel: 'shopee' | 'mercado_livre'`
   - `operation: 'main_variation' | 'color_variations'`
   - `base_reference_images[]` (obrigatório)
   - `color_reference_images[]` (obrigatório em `color_variations`)
   - `detected_colors[]` (preenchido pelo backend/agente)
2. Criar endpoint assíncrono dedicado para orquestração de anúncio marketplace (parent job + child jobs por shot).
3. Cada child job chama pipeline com `n_images=1` (sempre), eliminando dependência de multi-output para slots diferentes.

### 2.3 Orquestrador backend

1. Implementar `marketplace_orchestrator` com execução **sequencial por padrão** para máxima consistência visual.
2. Pipeline de `main_variation`:
   - montar 5 prompts especializados com travas de fidelidade de peça e composição por shot.
3. Pipeline de `color_variations`:
   - extrair/detectar cores das referências enviadas;
   - para cada cor detectada, gerar 3 shots independentes;
   - informar ao usuário no retorno quais cores foram detectadas e executadas.
4. Corrigir inconsistência técnica existente:
   - centralizar validação de parâmetros (`aspect_ratio`, `resolution`, `n_images`) e aplicar igual em rotas síncronas, assíncronas, stream e v2;
   - manter limite legado de `n_images` para modo genérico, mas marketplace não expõe `n_images` ao usuário.

### 2.4 UX frontend (sem poluição visual)

1. Manter dentro da tela `Criar` como **modo Marketplace** (não criar nova aba).
2. Fluxo guiado em 3 passos:
   - Passo 1: Canal (`Shopee`/`Mercado Livre`) + Operação (`Variação principal`/`Variações de cor`).
   - Passo 2: Upload de referências obrigatórias (principal e, quando aplicável, cores).
   - Passo 3: Resumo do pacote a gerar (5 fixas ou 3 por cor detectada) + confirmação.
3. Em modo Marketplace:
   - ocultar controle manual de `QTD`;
   - exibir contagem derivada da receita;
   - mostrar instrução explícita: “Para gerar cores, use referências da variação principal + fotos das cores”.

### 2.5 Documentação

1. Criar/atualizar guia operacional com esse fluxo final:
   - principal com 5 fotos fixas;
   - cores em etapa separada com 3 por cor;
   - shots independentes por slot;
   - diferenças leves de policy por canal.

## 3. Plano de testes

### 3.1 Unitários

1. Resolver de policy por canal.
2. Builder de shot recipes (5 e 3 por cor).
3. Detecção/normalização de cores a partir de referências.

### 3.2 Integração backend

1. `main_variation` retorna exatamente 5 imagens.
2. `color_variations` retorna `3 x N_cores_detectadas`.
3. Garantia de `n_images=1` por child job.
4. Validação central unificada ativa em todas as rotas de geração.

### 3.3 E2E frontend

1. Fluxo completo de variação principal.
2. Fluxo completo de variações de cor.
3. Estados de loading, erro parcial por shot e resumo final.

### 3.4 Regressão

1. Modo de geração atual (não-marketplace) continua funcional sem mudança de comportamento.

## 4. Assunções e defaults

1. Fluxo Marketplace ficará dentro de `Criar`.
2. Execução padrão sequencial para qualidade e previsibilidade.
3. `main_variation` e `color_variations` são operações separadas.
4. Variações de cor geram **3 imagens por cor** por padrão.
5. Mesmo sistema lógico para Shopee e Mercado Livre, com policy overlay por canal.
