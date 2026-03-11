# DeepThink Prompt Engineering & Arquitetura Nano Banana

**Data:** 2026-03-11  
**Fonte:** Agente DeepThink  
**Contexto:** Refinamentos lógicos, controle de pesos matemáticos, resolução de conflitos e gatilhos para o pipeline "Art Director Intelligence" com Nano Banana Pro (Gemini 3.1 Flash/Pro Image).

## 1. Mega-Prompt Base Structure (Framework KERNEL & 7 Layers)
Template programático que utiliza pesagem matemática para forçar o mecanismo de atenção na roupa (garment), enquanto permite entropia (aleatoriedade) no ambiente.

```text
[1. STYLE & ANGLE] Candid lifestyle photography, (amateur/semi-pro capture:1.2), {angle_description}.
[2. SCENE] {brazilian_location}, authentic context, (cluttered/lived-in background:0.9).
[3. MODEL HERO] {brazilian_phenotype}, {age}yo model, {pose}, (natural skin texture, visible pores, asymmetric features:1.3).
[4. CAMERA] Shot on {camera_device}, {lens_focal_length}, (subtle chromatic aberration, ISO {grain_level} noise, slight motion blur:1.2).
[5. LIGHTING] {lighting_condition}, mixed color temperature, (imperfect ambient bounce:1.1).
[6. TEXTURE LOCK] (Macro-accurate {garment_material}:1.5), exact thread count, proper fabric weight, (realistic light absorption on {garment_color}:1.4).
[7. NEGATIVE] (studio perfection:1.4), (plastic skin:1.5), (AI mannequin:1.5), symmetrical face, altered clothing silhouette, over-smoothed fabric.
```

## 2. Fidelity Lock: Cláusulas Anti-Alucinação
Cláusulas específicas para isolar o sujeito (roupa) do contexto gerado:

- **Clause 1 (Structural Strictness):** `(Zero-tolerance garment hallucination:1.5) - strictly replicate input garment mesh, draping, and hardware; do not invent or omit seams, zippers, or logos.`
- **Clause 2 (Entropy Segregation):** `Garment is a locked asset. Allow maximum generative entropy (randomness) only for model biology, pose dynamics, and background elements.`

## 3. Lógica de Disparo do Thinking (thinking_level="HIGH")
Disparar `thinking_level="HIGH"` **apenas** quando a triagem identificar dados visuais de alta frequência ou interações de luz complexas. Usar "HIGH" para peças lisas/simples desperdiça computação e arrisca "over-engineering" no tecido.

**Matriz de Disparo (Mudar de MINIMAL para HIGH se houver >0 matches):**

- **Keywords/Tecidos:** `crochet`, `lace`, `sequin`, `tweed`, `corduroy`, `sheer`, `pleated`, `metallic`, `velvet`, `bouclé`.
- **Padrões Visuais:**
  - Alta frequência espacial (listras finas, micro-poás).
  - Opacidade em camadas (tule, malha sobre tecido sólido).
  - Materiais refletivos/anisotrópicos (seda, nylon, couro).

## 4. Resolução de Conflitos Ocultos (Negative Prompts vs. Realismo)
**O Problema (Conflito Latente):**
Prompts negativos padrão de IA (como `(no blur:1.5)` ou `(sharp:1.5)`) entram em conflito destrutivo com as "7 alavancas de realismo imperfeito" (micro-desfoque, ruído). Além disso, solicitar `(highly detailed:1.5)` no prompt positivo comumente faz a IA inventar texturas que não estão na referência, destruindo o Fidelity Lock.

**A Estratégia de Resolução:**
1. **Remover Negativos Genéricos Fotográficos:** Retire termos como `blurry`, `grain`, `noise`, `bad lighting` dos prompts negativos. Queremos imperfeições fotográficas.
2. **Atacar a Estética "AI":** Use negativos estilísticos em vez de fotográficos: `(Midjourney aesthetic, 3D render, subsurface scattering, plastic, synthetic fabric:1.5)`.
3. **Isolar Negativos Anatômicos:** Agrupe as restrições anatômicas de forma rigorosa, sem vazar para o estilo: `(extra limbs, fused fingers, structural anatomy errors:1.3)`.
4. **Hierarquia Matemática de Pesos:** 
   - Fidelidade da Roupa `(1.5)` **>** Realismo/Imperfeições Intencionais `(1.2 - 1.3)` **>** Detalhes do Cenário `(0.9)`.
