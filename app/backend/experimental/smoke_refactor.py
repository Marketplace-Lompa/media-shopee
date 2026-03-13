"""
MT-R8 — Smoke tests de não-regressão pós-refatoração agent.py → agent_runtime/.

Roda:
  1) Referência sem prompt (MODE 2 + grounding auto)
  2) Prompt textual sem referência (MODE 1)

Valida contrato de retorno: prompt, base_prompt, camera_and_realism, grounding, reason_codes.
"""
import os, sys, json, pathlib, traceback

# ── env ──
ROOT = pathlib.Path(__file__).resolve().parent
ENV_FILE = ROOT.parent.parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(ROOT))

from agent import run_agent, normalize_prompt_text
from grounding_policy import compute_grounding_triage

# ── helpers ──
RED   = "\033[91m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
BOLD  = "\033[1m"
RESET = "\033[0m"

REQUIRED_KEYS = [
    "prompt", "base_prompt", "camera_and_realism",
    "grounding", "pipeline_mode", "shot_type",
    "thinking_level", "realism_level",
    "structural_contract", "diversity_target",
    "prompt_compiler_debug",
]

def _validate_result(result: dict, label: str) -> list[str]:
    """Retorna lista de erros encontrados."""
    errors = []
    for key in REQUIRED_KEYS:
        if key not in result:
            errors.append(f"[{label}] MISSING key: {key}")

    prompt = result.get("prompt", "")
    base_prompt = result.get("base_prompt", "")
    camera = result.get("camera_and_realism", "")
    grounding = result.get("grounding", {})

    if not prompt or len(prompt) < 30:
        errors.append(f"[{label}] prompt too short ({len(prompt)} chars)")
    if not base_prompt or len(base_prompt) < 20:
        errors.append(f"[{label}] base_prompt too short ({len(base_prompt)} chars)")
    if not camera or len(camera) < 10:
        errors.append(f"[{label}] camera_and_realism empty or too short")
    if not isinstance(grounding, dict):
        errors.append(f"[{label}] grounding is not a dict")
    else:
        for gk in ("effective", "mode", "engine"):
            if gk not in grounding:
                errors.append(f"[{label}] grounding missing '{gk}'")

    # reason_codes vive dentro de grounding
    if isinstance(grounding, dict) and "reason_codes" not in grounding:
        errors.append(f"[{label}] grounding missing 'reason_codes'")

    # Diversity target deve existir
    dt = result.get("diversity_target")
    if not isinstance(dt, dict):
        errors.append(f"[{label}] diversity_target not a dict")

    # Compiler debug deve ter word counts
    debug = result.get("prompt_compiler_debug", {})
    if not isinstance(debug, dict):
        errors.append(f"[{label}] prompt_compiler_debug not a dict")
    elif "final_words" not in debug:
        errors.append(f"[{label}] prompt_compiler_debug missing 'final_words'")

    return errors


def _print_result_summary(result: dict, label: str):
    print(f"\n{BOLD}── {label} ──{RESET}")
    print(f"  pipeline_mode:    {result.get('pipeline_mode')}")
    print(f"  shot_type:        {result.get('shot_type')}")
    print(f"  thinking_level:   {result.get('thinking_level')}")
    print(f"  realism_level:    {result.get('realism_level')}")
    print(f"  camera_profile:   {result.get('camera_profile')}")

    prompt = result.get("prompt", "")
    print(f"  prompt ({len(prompt)} chars): {prompt[:200]}{'…' if len(prompt) > 200 else ''}")

    grounding = result.get("grounding", {})
    print(f"  grounding.mode:   {grounding.get('mode')}")
    print(f"  grounding.engine: {grounding.get('engine')}")
    print(f"  grounding.effective: {grounding.get('effective')}")
    rc = grounding.get("reason_codes", [])
    print(f"  reason_codes:     {rc}")

    sc = result.get("structural_contract", {})
    if sc.get("enabled"):
        print(f"  structural:       subtype={sc.get('garment_subtype')} sleeve={sc.get('sleeve_type')}/{sc.get('sleeve_length')} conf={sc.get('confidence')}")
    else:
        print(f"  structural:       disabled")

    ia = result.get("image_analysis", "")
    if ia:
        print(f"  image_analysis:   {ia[:150]}")

    debug = result.get("prompt_compiler_debug", {})
    print(f"  compiler_debug:   final_words={debug.get('final_words')} base_budget={debug.get('base_budget')} camera_words={debug.get('camera_words')}")


# ══════════════════════════════════════════════════════════════════════════════
# SMOKE 1: Referência sem prompt (MODE 2 — grounding auto)
# ══════════════════════════════════════════════════════════════════════════════
all_errors = []
results = {}

print(f"\n{BOLD}{'='*70}")
print(f"SMOKE 1: Referência sem prompt (MODE 2 + grounding auto)")
print(f"{'='*70}{RESET}")

img_dir = ROOT.parent / "tests" / "output" / "poncho-teste"
img_files = sorted(img_dir.glob("*.jpg"))[:2]
if not img_files:
    print(f"{RED}  ❌ Nenhuma imagem de teste encontrada em {img_dir}{RESET}")
    sys.exit(1)

uploaded = []
for f in img_files:
    uploaded.append(f.read_bytes())
    print(f"  📸 Loaded: {f.name} ({len(uploaded[-1])} bytes)")

try:
    # Compute grounding triage como o router faz
    triage = compute_grounding_triage(
        user_prompt=None,
        image_analysis=None,
        has_images=True,
    )
    use_grounding = triage.get("use_grounding", False)
    grounding_mode = triage.get("grounding_mode", "lexical")
    print(f"  Triage: use_grounding={use_grounding} mode={grounding_mode}")

    result1 = run_agent(
        user_prompt=None,
        uploaded_images=uploaded,
        pool_context="",
        aspect_ratio="9:16",
        resolution="1024x1536",
        use_grounding=use_grounding,
        grounding_mode=grounding_mode,
    )
    results["smoke1"] = result1
    _print_result_summary(result1, "SMOKE 1 — Reference (no prompt)")
    errs = _validate_result(result1, "SMOKE1")
    all_errors.extend(errs)
    for e in errs:
        print(f"  {RED}❌ {e}{RESET}")
    if not errs:
        print(f"  {GREEN}✅ Contrato de retorno OK{RESET}")
except Exception as ex:
    print(f"  {RED}❌ CRASH: {ex}{RESET}")
    traceback.print_exc()
    all_errors.append(f"[SMOKE1] CRASH: {ex}")


# ══════════════════════════════════════════════════════════════════════════════
# SMOKE 2: Prompt textual sem referência (MODE 1)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}{'='*70}")
print(f"SMOKE 2: Prompt textual sem referência (MODE 1)")
print(f"{'='*70}{RESET}")

try:
    triage2 = compute_grounding_triage(
        user_prompt="Vestido midi floral com fenda lateral, tecido fluido",
        image_analysis=None,
        has_images=False,
    )
    use_grounding2 = triage2.get("use_grounding", False)
    grounding_mode2 = triage2.get("grounding_mode", "lexical")
    print(f"  Triage: use_grounding={use_grounding2} mode={grounding_mode2}")

    result2 = run_agent(
        user_prompt="Vestido midi floral com fenda lateral, tecido fluido",
        uploaded_images=None,
        pool_context="",
        aspect_ratio="9:16",
        resolution="1024x1536",
        use_grounding=use_grounding2,
        grounding_mode=grounding_mode2,
    )
    results["smoke2"] = result2
    _print_result_summary(result2, "SMOKE 2 — Text prompt (no images)")
    errs = _validate_result(result2, "SMOKE2")
    all_errors.extend(errs)
    for e in errs:
        print(f"  {RED}❌ {e}{RESET}")
    if not errs:
        print(f"  {GREEN}✅ Contrato de retorno OK{RESET}")
except Exception as ex:
    print(f"  {RED}❌ CRASH: {ex}{RESET}")
    traceback.print_exc()
    all_errors.append(f"[SMOKE2] CRASH: {ex}")


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO FINAL
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}{'='*70}")
print(f"RESULTADO FINAL")
print(f"{'='*70}{RESET}")

if all_errors:
    print(f"\n{RED}{BOLD}❌ {len(all_errors)} ERRO(S) ENCONTRADO(S):{RESET}")
    for e in all_errors:
        print(f"  {RED}• {e}{RESET}")
    sys.exit(1)
else:
    print(f"\n{GREEN}{BOLD}✅ TODOS OS SMOKE TESTS PASSARAM — sem regressão de contrato.{RESET}")

# Dump JSON para referência do relatório
report_data = {}
for k, v in results.items():
    safe = {rk: rv for rk, rv in v.items() if rk != "_grounded_images"}
    report_data[k] = safe

out_path = ROOT / "smoke_refactor_results.json"
out_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False, default=str))
print(f"\n  📄 Resultados salvos em {out_path}")
