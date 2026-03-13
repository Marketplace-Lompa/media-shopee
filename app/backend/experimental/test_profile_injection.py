"""
test_profile_injection.py
=========================
Testa se o profile de modelo (diversity target / name blend) aparece
no prompt final compilado pelo run_agent.

Execução:
    cd app/backend
    python test_profile_injection.py
"""
import sys, os, textwrap, json
sys.path.insert(0, os.path.dirname(__file__))

# ─── Cores ANSI ────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ok   = lambda msg: print(f"{GREEN}  ✅ {msg}{RESET}")
fail = lambda msg: print(f"{RED}  ❌ {msg}{RESET}")
warn = lambda msg: print(f"{YELLOW}  ⚠️  {msg}{RESET}")
info = lambda msg: print(f"{CYAN}  ℹ  {msg}{RESET}")
hdr  = lambda msg: print(f"\n{BOLD}{msg}{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 1 — _sample_diversity_target(): perfil deve ser curto e ter name blend
# ══════════════════════════════════════════════════════════════════════════════
hdr("═══ TESTE 1: _sample_diversity_target() compacto ═══")
from agent_runtime.diversity import _sample_diversity_target
from agent_runtime.compiler import _count_words

results = []
for i in range(6):
    profile, scenario, pose = _sample_diversity_target()
    wc = _count_words(profile)
    results.append((profile, wc))
    has_blend   = "features blend" in profile
    has_quote   = "'" in profile
    is_compact  = wc <= 20
    line = f"[{i+1}] ({wc}w) {profile}"
    if has_blend and has_quote and is_compact:
        ok(line)
    else:
        fail(line)
        if not has_blend:  warn("  → falta 'features blend'")
        if not has_quote:  warn("  → falta nome entre aspas")
        if not is_compact: warn(f"  → muito longo ({wc}w > 20w)")

max_w = max(w for _, w in results)
info(f"Máximo de palavras no profile: {max_w}w (limite seguro: 20w)")


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 2 — _compile_prompt_v2(): perfil deve aparecer como cláusula P3
# ══════════════════════════════════════════════════════════════════════════════
hdr("═══ TESTE 2: _compile_prompt_v2() injeta model_profile em force_cover_defaults ═══")
from agent_runtime.compiler import _compile_prompt_v2

# Contrato de ruana (caso exato do usuário)
contract = {
    "enabled": True,
    "confidence": 0.80,
    "garment_subtype": "ruana_wrap",
    "sleeve_type": "cape_like",
    "sleeve_length": "three_quarter",
    "front_opening": "open",
    "hem_shape": "rounded",
    "garment_length": "upper_thigh",
    "silhouette_volume": "draped",
    "must_keep": ["horizontal stripes", "textured knit"],
}

profile, scenario, pose = _sample_diversity_target()
camera_words = 22  # simula "Sony A7III, 85mm f/1.8. Visible pores, fabric creases."
budget = max(80, 165 - camera_words)   # 143w — novo budget reference-only mode

result, debug = _compile_prompt_v2(
    prompt="RAW photo, full-body wide shot.",   # base mínimo (force_cover_defaults)
    has_images=True,
    has_prompt=False,                            # force_cover_defaults = True
    contract=contract,
    guided_brief=None,
    guided_enabled=False,
    guided_set_detection=None,
    grounding_mode="off",
    pipeline_mode="reference_mode",
    word_budget=budget,
    pose_hint=None,
    profile_hint=profile,
)

total_w = debug["total_words"]
used_sources = {c["source"] for c in debug["used_clauses"]}
dropped = [(c["text"][:60], c["reason"]) for c in debug["discarded_clauses"]]

print(f"\n  Profile injetado: «{profile}»")
print(f"  Budget: {budget}w   |   Usado: {total_w}w\n")

# Verifica cláusulas esperadas
checks = {
    "model_profile": ("profile na cláusula model_profile", "model_profile" in used_sources),
    "auto_cover_default": ("cover composition", "auto_cover_default" in used_sources),
    "quality_texture": ("texture fidelity", "quality_texture" in used_sources),
    "quality_model": ("quality_model", "quality_model" in used_sources),
    "bottom_complement": ("bottom complement (evita skirt leak)", "bottom_complement" in used_sources),
}
for key, (label, passed) in checks.items():
    (ok if passed else fail)(f"{label}  [{key}]")

if dropped:
    print()
    for txt, reason in dropped[:6]:
        warn(f"DROPPED [{reason}]: {txt}…")

# Verifica que name blend está no texto final
has_blend_in_final = "features blend" in result
if has_blend_in_final:
    ok("'features blend' presente no prompt final ✓")
else:
    fail("'features blend' AUSENTE no prompt final")

print(f"\n  {BOLD}Prompt compilado:{RESET}")
for line in textwrap.wrap(result, 100):
    print(f"    {line}")


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 3 — run_agent() com imagem real: prompt final deve conter name blend
# ══════════════════════════════════════════════════════════════════════════════
hdr("═══ TESTE 3: run_agent() com imagem real ═══")
from pathlib import Path

# Fixture estável: app/tests/output/poncho-teste (ruana/poncho crochet de ~3-5 MB)
ref_dir = Path(__file__).resolve().parent.parent / "tests" / "output" / "poncho-teste"
ref_images = sorted(ref_dir.glob("IMG_*.jpg"))[:2]

if not ref_images:
    warn(f"Nenhuma imagem de referência encontrada em {ref_dir} — pulando Teste 3")
else:
    imgs = [p.read_bytes() for p in ref_images]
    info(f"Usando {len(imgs)} imagens de referência: {[p.name for p in ref_images[:2]]}")

    from pipeline_effectiveness import select_diversity_target
    diversity_target = select_diversity_target(seed_hint="", guided_brief=None)
    info(f"diversity_target.profile_prompt = «{diversity_target.get('profile_prompt', '???')}»")

    try:
        from agent import run_agent
        result_agent = run_agent(
            user_prompt="",           # sem texto → force_cover_defaults
            uploaded_images=imgs,
            pool_context="",
            aspect_ratio="2:3",
            resolution="1024x1536",
            use_grounding=False,
            grounding_mode="off",
            diversity_target=diversity_target,
            guided_brief=None,
        )
        final_prompt = result_agent.get("prompt", "")
        base_prompt  = result_agent.get("base_prompt", "")
        camera       = result_agent.get("camera_and_realism", "")
        compiler_dbg = result_agent.get("prompt_compiler_debug", {})

        print(f"\n  base_prompt  ({_count_words(base_prompt)}w): {base_prompt[:120]}")
        print(f"  camera       ({_count_words(camera)}w): {camera[:120]}")
        print(f"  budget usado : {compiler_dbg.get('total_words','?')}w / {compiler_dbg.get('word_budget','?')}w")

        used_src = {c["source"] for c in (compiler_dbg.get("used_clauses") or [])}
        print(f"  cláusulas    : {sorted(used_src)}")

        # FIX-A: Gemini pode ecoar o diversity profile no base_prompt em vez de o compiler
        # injetá-lo como P2. Aceitamos qualquer sinal de profile no prompt final:
        _profile_signals_in_prompt = ("features blend", "blend reminiscent", "blend of")
        has_blend   = any(sig in final_prompt.lower() for sig in _profile_signals_in_prompt)
        has_profile = "model_profile" in used_src
        # Se Gemini já ecoou o profile no base, model_profile P2 é corretamente omitido.
        profile_ok = has_blend  # profile pode vir do base ou do P2 — ambos válidos
        # "pores" and "peach fuzz" are legitimate in the catalog_clean camera block.
        # Use strong persona signals that only appear when Gemini truly mis-routes
        # model-persona text into camera_and_realism.
        beauty_in_camera = any(kw in camera.lower() for kw in [
            "beauty", "brasileir", "features blend",
            "flawless unretouched", "editorial talent", "lookbook model",
        ])

        print()
        (ok if profile_ok else fail)("diversity profile presente no prompt final (via base ou P2)")
        if has_profile:
            ok("model_profile injetado como P2 clause")
        else:
            info("model_profile P2 omitido (Gemini já ecoou profile no base — FIX-A correto)")
        (warn if beauty_in_camera else ok)(
            "beauty text no camera_and_realism" if beauty_in_camera
            else "camera_and_realism limpo (sem beauty text)"
        )

        print(f"\n  {BOLD}Prompt final completo:{RESET}")
        for line in textwrap.wrap(final_prompt, 100):
            print(f"    {line}")

    except Exception as e:
        fail(f"run_agent() lançou exceção: {e}")
        import traceback; traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
hdr("═══ FIM DOS TESTES ═══\n")
