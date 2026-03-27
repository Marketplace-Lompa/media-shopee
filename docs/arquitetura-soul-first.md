# Arquitetura Soul-First — Pipeline Unificado

> **Status**: Em migração  
> **Última atualização**: 2026-03-26

---

## Visão Geral

O sistema gera imagens de moda e-commerce com modelos brasileiras vestindo a roupa do vendedor. Existem dois fluxos de entrada que convergem na mesma espinha dorsal de execução:

```
┌─────────────────────────────────────────────────────────────┐
│                       ENTRADA DO JOB                        │
│                                                             │
│   Texto puro (sem imagem)    │    Com imagem de referência  │
└──────────────┬───────────────┴──────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    AGENT.PY (Cérebro)                        │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │  Modes   │  │  Souls   │  │  Triage  │  │  Diversity  │ │
│  │ (preset) │  │  (vida)  │  │ (visão)  │  │  (casting)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘ │
│       └──────────────┴─────────────┴───────────────┘        │
│                         │                                    │
│                    Prompt Criativo                            │
└─────────────────────────┬────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
   ┌────────────────┐        ┌─────────────────────┐
   │  SEM IMAGEM    │        │   COM IMAGEM         │
   │                │        │                      │
   │  Prompt vai    │        │  ┌────────────────┐  │
   │  direto pro    │        │  │  FIDELITY.PY   │  │
   │  generator     │        │  │  (Proteção)    │  │
   │                │        │  │                │  │
   │                │        │  │  Shell de      │  │
   │                │        │  │  fidelidade    │  │
   │                │        │  │  envolve o     │  │
   │                │        │  │  prompt        │  │
   │                │        │  └───────┬────────┘  │
   │                │        │          │           │
   └───────┬────────┘        └──────────┼───────────┘
           │                            │
           ▼                            ▼
┌──────────────────────────────────────────────────────────────┐
│               GENERATOR.PY (Espinha Dorsal)                  │
│                                                              │
│           Nano Banana 2 (gemini-3.1-flash-image)             │
│                                                              │
│   ┌─────────────────────┐  ┌──────────────────────────────┐ │
│   │  generate_images()  │  │  edit_image()                │ │
│   │  (texto → imagem)   │  │  (imagem base → imagem final)│ │
│   └─────────────────────┘  └──────────────────────────────┘ │
│                                                              │
│   • Retry com backoff (transient + quota)                    │
│   • Preparação de referências (resize, compress)             │
│   • Image grounding (Google Image Search)                    │
│   • lock_person (true/false)                                 │
│   • Extração + persistência em disco                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Camadas

### 1. Motor (Guidelines & Regras)
**Arquivos**: `agent_runtime/constants.py`, `agent_runtime/prompt_context.py`

O motor define as boas práticas do Nano Banana, as regras de segurança (anti-clonagem de identidade), o schema de resposta do agente, e o knowledge base de referência. É a constituição do sistema.

### 2. Diretor (Identidade Criativa)
**Arquivo**: `agent_runtime/prompt_context.py` → `build_system_instruction()`

O system instruction do Gemini Flash define quem o agente é: um diretor de fotografia de moda brasileira. Ele fala como profissional, pensa em luz/cena/modelo, e tem personalidade consistente.

### 3. Modes (Presets Criativos)
**Arquivo**: `agent_runtime/modes.py`

Cada mode é um perfil criativo completo:
- `catalog_clean` — fundo limpo, luz flat, foco total na peça
- `natural` — lifestyle brasileiro, luz natural, cenário casual
- `editorial_commercial` — moda editorial, drama, contraste
- `lifestyle` — UGC real, imperfeições naturais, autenticidade

O mode define: `framing_profile`, `camera_type`, `lighting_profile`, `pose_energy`, `casting_profile`, `capture_geometry`.

### 4. Souls (Vida aos Modes)
**Arquivo**: `agent_runtime/modes.py` → `describe_mode_defaults()`

O soul é a descrição em prosa que injeta personalidade no mode. É a diferença entre "luz natural lateral" (preset técnico) e "Aquela luz dourada de fim de tarde entrando pela janela do apartamento, criando sombras suaves no rosto da modelo..." (soul). O Gemini responde melhor ao soul.

### 5. Triage (Visão Computacional)
**Arquivo**: `agent_runtime/triage.py`

Quando o job tem imagem de entrada, o triage:
- Analisa a peça (tipo, subtipo, construção, silhueta)
- Gera `structural_contract` (o contrato de fidelidade da peça)
- Detecta conjuntos (sets de peças coordenadas)
- Produz `look_contract` (coerência visual do look)
- Gera `image_analysis` (descrição textual da peça)

Compartilhado entre ambos os fluxos.

### 6. Fidelity (Proteção de Transferência)
**Arquivo**: `agent_runtime/fidelity.py`

Acionado **exclusivamente** no fluxo com imagem. Responsabilidades:
- `compile_edit_prompt()` — envolve o prompt criativo do agente com locks de proteção
- `should_use_image_grounding()` — decide se ativa Google Image Search
- `derive_garment_material_text()` — detecta material para instruções de textura
- `build_structure_guard_clauses()` — guards estruturais (manga, barra, silhueta)
- `build_pattern_lock()` — lock de padrões visuais (listras, crochet, chevron)
- `build_reference_policy()` — política de uso de referências (identidade vs garment)

### 7. Generator (Espinha Dorsal de Execução)
**Arquivo**: `generator.py`

Infraestrutura estável. **Nunca mexemos aqui** na refatoração. Responsabilidades:
- Interface com a API Nano Banana 2
- `generate_images()` — gera imagem do zero a partir de prompt + referências
- `edit_image()` — edita imagem existente preservando roupa (`lock_person=False`)
- Preparação de referências (resize, compress, EXIF transpose)
- Retry inteligente (transient errors, quota 429)
- Image grounding (Google Image Search para peças complexas)
- Persistência em disco

---

## Fluxos

### Fluxo 1: Texto Puro (sem imagem)

```
Router → agent.run_agent(prompt, mode)
  → Agent entende o mode, aplica soul
  → Agent gera prompt criativo via Gemini Flash
  → Router chama generator.generate_images(prompt)
  → Nano Banana gera a imagem
```

### Fluxo 2: Com Imagem de Referência

```
Router → agent.run_agent(images, mode)
  → Triage analisa as imagens (structural_contract)
  → Agent entende peça + mode, aplica soul
  → Agent gera prompt criativo via Gemini Flash
  →
  → Fidelity envolve prompt com shell de proteção
  → Router chama generator.generate_images() → imagem base (stage 1)
  → Router chama generator.edit_image(base, fidelity_prompt) → imagem final (stage 2)
```

### Stage 1 vs Stage 2 (Two-Pass)

| Aspecto | Stage 1 (Base) | Stage 2 (Edit) |
|---------|---------------|----------------|
| **Função** | `generate_images()` | `edit_image()` |
| **Objetivo** | Gerar imagem com roupa fiel | Criar cena/modelo mantendo roupa |
| **lock_person** | N/A | `False` (troca modelo) |
| **Referências** | Imagens da triagem | Edit anchors + identity safe |
| **Thinking** | MINIMAL (velocidade) | HIGH ou MINIMAL (fidelidade) |

---

## Módulos Legados (Em Remoção)

| Módulo | Status | Substituído por |
|--------|--------|----------------|
| `pipeline_v2.py` | 🔴 Legado | agent.py + fidelity.py + router |
| `art_direction_sampler.py` | 🔴 Removido | modes.py (souls) |
| `two_pass_flow.py` | 🔴 Removido | fidelity.py |
| `target_builder.py` | 🟡 Em análise | modes.py + diversity |
| `scene_engine.py` | 🔴 Legado | Agent via Gemini |
| `pose_engine.py` | 🔴 Legado | Agent via Gemini |

---

## Princípios de Design

1. **Fonte única de verdade criativa**: `modes.py` — todo soul, preset e direção artística vêm daqui
2. **Separação cérebro/proteção/execução**: agent cria, fidelity protege, generator executa
3. **Fidelity é opt-in**: só ativado quando há imagem de entrada
4. **Generator é infraestrutura**: nunca é alterado durante refatoração criativa
5. **Sem pools hardcoded**: o agente (Gemini) decide cena, pose, modelo — não arrays estáticos
6. **Triagem compartilhada**: `triage.py` serve ambos os fluxos
