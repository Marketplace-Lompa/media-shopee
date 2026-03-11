"""
Art Director Intelligence — Smoke test com imagens reais de poncho/ruana.

Roda MODE 2 (referência sem texto) e avalia:
  1. garment_aesthetic extraído (color_temperature, formality, season, vibe)
  2. garment_narrative preenchido (descrição rica da peça sem pessoa)
  3. Diversidade garment-aware (cenário/modelo complementam a peça)
  4. Prompt final contém narrativa da peça (não apenas geometria)
  5. Gera imagem via Nano Banana e salva para avaliação visual
"""
import os, sys, pathlib, json, traceback

ROOT = pathlib.Path(__file__).resolve().parent
ENV_FILE = ROOT.parent.parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(ROOT))

from agent import run_agent
from grounding_policy import compute_grounding_triage
from pipeline_effectiveness import select_diversity_target
from agent_runtime.triage import _infer_unified_vision_triage
from generator import generate_images

RED   = "\033[91m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
BOLD  = "\033[1m"
RESET = "\033[0m"

# ── Carregar 2 imagens de referência ──
img_dir = ROOT.parent / "tests" / "output" / "poncho-teste"
img_files = sorted(img_dir.glob("*.jpg"))[:2]
if not img_files:
    print(f"{RED}  Nenhuma imagem de teste encontrada em {img_dir}{RESET}")
    sys.exit(1)

uploaded = []
for f in img_files:
    uploaded.append(f.read_bytes())
    print(f"  Loaded: {f.name} ({len(uploaded[-1])//1024} KB)")

print(f"\n{BOLD}{'='*70}")
print(f"ETAPA 1: Triagem Unificada (garment_aesthetic + garment_narrative)")
print(f"{'='*70}{RESET}")

unified = _infer_unified_vision_triage(uploaded, None)
if unified:
    print(f"\n  garment_hint:      {unified.get('garment_hint')}")
    print(f"  image_analysis:    {unified.get('image_analysis', '')[:200]}")

    aesthetic = unified.get("garment_aesthetic", {})
    print(f"\n  {BOLD}garment_aesthetic:{RESET}")
    print(f"    color_temperature: {aesthetic.get('color_temperature')}")
    print(f"    formality:         {aesthetic.get('formality')}")
    print(f"    season:            {aesthetic.get('season')}")
    print(f"    vibe:              {aesthetic.get('vibe')}")

    sc = unified.get("structural_contract", {})
    print(f"\n  structural_contract:")
    print(f"    subtype={sc.get('garment_subtype')} sleeve={sc.get('sleeve_type')}/{sc.get('sleeve_length')}")
    print(f"    volume={sc.get('silhouette_volume')} conf={sc.get('confidence')}")
else:
    print(f"  {RED}Triagem unificada falhou!{RESET}")
    aesthetic = None
    sc = None

print(f"\n{BOLD}{'='*70}")
print(f"ETAPA 2: Diversidade Garment-Aware")
print(f"{'='*70}{RESET}")

diversity_target = select_diversity_target(
    seed_hint="",
    guided_brief=None,
    garment_aesthetic=aesthetic,
    structural_contract=sc,
)
print(f"\n  profile_id:     {diversity_target.get('profile_id')}")
print(f"  profile_prompt: {diversity_target.get('profile_prompt')}")
print(f"  scenario_id:    {diversity_target.get('scenario_id')}")
print(f"  scenario_prompt:{diversity_target.get('scenario_prompt')}")
print(f"  pose_id:        {diversity_target.get('pose_id')}")
print(f"  lighting_hint:  {diversity_target.get('lighting_hint')}")
print(f"  aesthetic used:  {diversity_target.get('garment_aesthetic')}")

print(f"\n{BOLD}{'='*70}")
print(f"ETAPA 3: run_agent() MODE 2 (sem texto)")
print(f"{'='*70}{RESET}")

try:
    triage = compute_grounding_triage(
        user_prompt=None,
        image_analysis=unified.get("image_analysis", "") if unified else None,
        has_images=True,
    )
    use_grounding = triage.get("use_grounding", False)
    grounding_mode = triage.get("grounding_mode", "lexical")

    result = run_agent(
        user_prompt=None,
        uploaded_images=uploaded,
        pool_context="POOL_RUNTIME_DISABLED",
        aspect_ratio="9:16",
        resolution="1024x1536",
        use_grounding=use_grounding,
        grounding_mode=grounding_mode,
        diversity_target=diversity_target,
        unified_vision_triage_result=unified,
    )

    prompt_final = result.get("prompt", "")
    garment_narrative = result.get("garment_narrative", "")

    print(f"\n  {BOLD}garment_narrative:{RESET}")
    print(f"    {garment_narrative if garment_narrative else '(vazio)'}")

    print(f"\n  {BOLD}prompt final ({len(prompt_final)} chars):{RESET}")
    print(f"    {prompt_final[:400]}")

    # Verificações
    errors = []
    if not aesthetic:
        errors.append("garment_aesthetic ausente")
    if aesthetic and aesthetic.get("vibe") == "minimalist" and aesthetic.get("color_temperature") == "neutral":
        print(f"  {YELLOW}  garment_aesthetic pode ser default (minimalist/neutral) — verificar se Gemini analisou{RESET}")

    if not garment_narrative:
        print(f"  {YELLOW}  garment_narrative vazio — Gemini pode não ter preenchido o campo{RESET}")

    # Verificar se prompt tem cores/textura (não apenas geometria)
    _color_words = {"warm", "earth", "caramel", "terracotta", "cream", "brown", "beige",
                    "neutral", "striped", "crochet", "knit", "open-stitch", "handmade"}
    _has_color = any(w in prompt_final.lower() for w in _color_words)
    if _has_color:
        print(f"  {GREEN}  Prompt contém descrição de cores/textura da peça{RESET}")
    else:
        print(f"  {YELLOW}  Prompt pode não ter descrição rica da peça (sem palavras de cor/textura){RESET}")

    # Verificar lighting_hint
    _lighting = diversity_target.get("lighting_hint", "")
    if _lighting:
        if _lighting[:20] in prompt_final:
            print(f"  {GREEN}  lighting_hint injetado no prompt{RESET}")
        else:
            print(f"  {YELLOW}  lighting_hint gerado mas pode ter sido descartado por budget{RESET}")

    debug = result.get("prompt_compiler_debug", {})
    print(f"\n  compiler_debug:")
    print(f"    final_words:    {debug.get('final_words')}")
    print(f"    base_words:     {debug.get('base_words')}")
    print(f"    base_budget:    {debug.get('base_budget')}")
    used_sources = [c.get("source") for c in debug.get("used_clauses", [])]
    print(f"    used_clauses:   {used_sources}")
    discarded = debug.get("discarded_clauses", [])
    if discarded:
        print(f"    discarded:      {[(d.get('text', '')[:40], d.get('reason', '')) for d in discarded]}")

    print(f"\n{BOLD}{'='*70}")
    print(f"ETAPA 4: Geração de Imagem via Nano Banana")
    print(f"{'='*70}{RESET}")

    thinking_level = result.get("thinking_level", "MINIMAL")
    grounded_images = list(result.pop("_grounded_images", []) or [])

    # Construir structural_hint para Nano Banana (mesma lógica dos routers)
    _structural_hint = None
    if sc:
        _hint_parts = [sc.get("garment_subtype", "")]
        if sc.get("silhouette_volume"):
            _hint_parts.append(f"{sc['silhouette_volume']} silhouette")
        if sc.get("sleeve_type") and sc.get("sleeve_type") != "set-in":
            _hint_parts.append(f"{sc['sleeve_type']} sleeves")
        _structural_hint = ", ".join(p for p in _hint_parts if p) or None
    print(f"  structural_hint: {_structural_hint}")

    batch = generate_images(
        prompt=prompt_final,
        thinking_level=thinking_level,
        aspect_ratio="9:16",
        resolution="1024x1536",
        n_images=1,
        uploaded_images=uploaded,
        grounded_images=grounded_images if grounded_images else None,
        session_id="art_director_test_v2",
        start_index=1,
        structural_hint=_structural_hint,
    )

    for img in batch:
        print(f"\n  {GREEN}Imagem gerada:{RESET}")
        print(f"    path:      {img.get('path')}")
        print(f"    size:      {img.get('size_kb')} KB")
        print(f"    mime_type: {img.get('mime_type')}")

    print(f"\n{BOLD}{'='*70}")
    print(f"RESULTADO")
    print(f"{'='*70}{RESET}")
    if errors:
        for e in errors:
            print(f"  {RED}{e}{RESET}")
    else:
        print(f"  {GREEN}Art Director Intelligence operacional!{RESET}")
        print(f"  Veja a imagem gerada em: {batch[0].get('path') if batch else 'N/A'}")

except Exception as ex:
    print(f"  {RED}CRASH: {ex}{RESET}")
    traceback.print_exc()
