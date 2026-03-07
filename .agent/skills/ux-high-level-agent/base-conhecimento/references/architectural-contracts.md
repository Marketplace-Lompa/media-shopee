# Architectural Contracts (v0.2)

Estes contratos garantem a interoperabilidade entre as camadas da Skill de UX de forma agnóstica à plataforma.

## 1. EvidenceBundle (Capacidade: L4 -> L2)
Representa a captura bruta da interface.

```json
{
  "id": "evidence-uuid",
  "schema_version": "1.0",
  "timestamp": "ISO-8601",
  "capabilities": ["visual_capture", "ui_tree_inspection"],
  "viewport": { "width": 1440, "height": 900, "density": 2.0 },
  "assets": {
    "screenshot": "path/to/image.png",
    "ui_tree": "path/to/hierarchy.json" 
  },
  "metadata": {
    "platform": "web|ios|android|desktop",
    "provider": "PlaywrightAdapter/1.0"
  }
}
```

## 2. UXProfile / BiasProfile (Capacidade: L0 -> L2)
Manifesto de calibragem do agente para o projeto.

```json
{
  "schema_version": "1.0",
  "profile": {
    "minimalista": "alto",
    "disruptivo": "baixo"
  },
  "weights": {
    "precision_vs_creativity": 0.8
  },
  "constraints": ["accessibility_first", "dark_mode_priority"]
}
```

## 3. ScreenIntentSpec (Capacidade: L2 -> B/Mode)
Blueprint conceitual da interface antes da tradução.

```json
{
  "id": "intent-uuid",
  "layout_type": "dashboard-command-center",
  "elements": [
    { "role": "primary-action", "label": "Enviar", "priority": 1 }
  ],
  "visual_tone": "minimal-premium"
}
```

## 4. TokenSpec (Capacidade: L2 -> L5)
Definição de design neutra. Evite termos específicos de CSS (ex: use `rounding` em vez de `border-radius`).

```json
{
  "component_id": "btn-primary",
  "style": {
    "rounding": "soft",
    "surface": "brand-primary",
    "motion_duration": "fast"
  }
}
```

## 5. UI Translator Output (Capacidade: L5 -> Projeto)
Resultado da tradução para a stack real.

```json
{
  "code": "...",
  "unsupported_features_report": [
    { "feature": "complex-gradient", "reason": "Not supported by target stack" }
  ]
}
```

## 6. KnowledgeOverlayManifest (Capacidade: L3)
Define a política de cascata de memória.

```json
{
  "strategy": "LocalOverGlobal",
  "conflict_policy": {
    "heuristics": "replace",
    "cases": "append",
    "styles": "merge"
  },
  "provenance_tracking": true
}
```
