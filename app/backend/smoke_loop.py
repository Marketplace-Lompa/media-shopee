"""
Loop de geração — roda pipeline COMPLETO por imagem (diversidade + agente + geração).
Simula N requests independentes para a mesma peça.
"""
import os, sys, pathlib, time

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
from history import add_entry as history_add

N_IMAGES = 5  # quantas imagens gerar no loop
SESSION = "loop_v8"

RED   = "\033[91m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
BOLD  = "\033[1m"
RESET = "\033[0m"

# ── Carregar referências ──
img_dir = ROOT.parent / "tests" / "output" / "poncho-teste"
img_files = sorted(img_dir.glob("*.jpg"))[:3]
if not img_files:
    print(f"{RED}Nenhuma imagem em {img_dir}{RESET}")
    sys.exit(1)

uploaded = [f.read_bytes() for f in img_files]
for f in img_files:
    print(f"  Ref: {f.name}")

# ── ETAPA 1: Triagem Unificada (1x — mesma peça) ──
print(f"\n{BOLD}[1/2] Triagem Unificada (1x){RESET}")
unified = _infer_unified_vision_triage(uploaded, None)
aesthetic = unified.get("garment_aesthetic", {}) if unified else {}
sc = unified.get("structural_contract", {}) if unified else {}
print(f"  hint: {unified.get('garment_hint', '?')}")
print(f"  aesthetic: {aesthetic}")
print(f"  contract: subtype={sc.get('garment_subtype')} volume={sc.get('silhouette_volume')}")

# structural_hint — silhueta + volume (fixo, mesma peça)
_structural_hint = None
if sc:
    _hint_parts = [sc.get("garment_subtype", "")]
    if sc.get("silhouette_volume"):
        _hint_parts.append(f"{sc['silhouette_volume']} silhouette")
    if sc.get("sleeve_type") and sc.get("sleeve_type") != "set-in":
        _hint_parts.append(f"{sc['sleeve_type']} sleeves")
    _structural_hint = ", ".join(p for p in _hint_parts if p) or None
print(f"  structural_hint: {_structural_hint}")

# grounding triage (1x — depende da peça, não do modelo)
triage = compute_grounding_triage(
    user_prompt=None,
    image_analysis=unified.get("image_analysis", "") if unified else None,
    has_images=True,
)

# ── ETAPA 2: Loop completo — diversidade + agente + geração por imagem ──
print(f"\n{BOLD}[2/2] Gerando {N_IMAGES} imagens (pipeline completo por iteração){RESET}")
generated = []
for i in range(N_IMAGES):
    t0 = time.time()
    step = f"[{i+1}/{N_IMAGES}]"
    try:
        # A) Diversidade — novo perfil/cenário/pose a cada iteração
        diversity_target = select_diversity_target(
            seed_hint="",
            guided_brief=None,
            garment_aesthetic=aesthetic,
            structural_contract=sc,
        )
        profile = diversity_target.get("profile_id", "?")
        scenario = diversity_target.get("scenario_id", "?")
        pose = diversity_target.get("pose_id", "?")
        print(f"  {YELLOW}{step}{RESET} profile={profile} scenario={scenario} pose={pose}")

        # B) Agente — compila prompt com o novo diversity_target
        result = run_agent(
            user_prompt=None,
            uploaded_images=uploaded,
            pool_context="POOL_RUNTIME_DISABLED",
            aspect_ratio="9:16",
            resolution="1024x1536",
            use_grounding=triage.get("use_grounding", False),
            grounding_mode=triage.get("grounding_mode", "lexical"),
            diversity_target=diversity_target,
            unified_vision_triage_result=unified,
        )

        prompt_final = result.get("prompt", "")
        thinking_level = result.get("thinking_level", "MINIMAL")
        grounded_images = list(result.pop("_grounded_images", []) or [])

        # C) Geração
        batch = generate_images(
            prompt=prompt_final,
            thinking_level=thinking_level,
            aspect_ratio="9:16",
            resolution="1024x1536",
            n_images=1,
            uploaded_images=uploaded,
            grounded_images=grounded_images if grounded_images else None,
            session_id=SESSION,
            start_index=i + 1,
            structural_hint=_structural_hint,
        )
        elapsed = time.time() - t0
        img = batch[0]
        generated.append(img)

        # Registrar no histórico para aparecer no dashboard
        try:
            history_add(
                session_id=SESSION,
                filename=img["filename"],
                url=img["url"],
                prompt=prompt_final,
                thinking_level=thinking_level,
                aspect_ratio="9:16",
                resolution="1024x1536",
                grounding_effective=bool(grounded_images),
                references=[f.name for f in img_files],
            )
        except Exception:
            pass

        print(f"  {GREEN}{step}{RESET} {img['filename']} — {img['size_kb']} KB — {elapsed:.1f}s")
        print(f"        prompt: {prompt_final[:120]}...")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  {RED}{step} FALHOU em {elapsed:.1f}s: {e}{RESET}")

# ── Resumo ──
print(f"\n{BOLD}{'='*60}")
print(f"RESULTADO: {len(generated)}/{N_IMAGES} imagens geradas")
print(f"{'='*60}{RESET}")
for img in generated:
    print(f"  {img['path']}")

if generated:
    print(f"\n  {GREEN}Abra as imagens em:{RESET}")
    out_dir = pathlib.Path(generated[0]["path"]).parent
    print(f"  open {out_dir}")
