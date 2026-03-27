#!/usr/bin/env python3
"""
Teste de pipeline v2 usando fixtures de produto.

Escolhe automaticamente um produto de app/tests/fixtures/,
passa todas as imagens para o pipeline e reporta o resultado.

AVISO: --generate faz chamadas reais à API Gemini e gera imagens.
       Rode com o backend/frontend PARADOS para não competir por recursos.
       Por padrão roda apenas triage (análise das imagens, sem geração).

Uso:
  python app/tests/test_pipeline_fixture.py                          # triage only
  python app/tests/test_pipeline_fixture.py --generate               # geração completa
  python app/tests/test_pipeline_fixture.py --product poncho-ruana-listras
  python app/tests/test_pipeline_fixture.py --product poncho-ruana-listras --generate
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# ── Setup paths ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
FIXTURES_DIR = Path(__file__).resolve().parent / "samples"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


# ── Fixture discovery ─────────────────────────────────────────────────────────

def list_products() -> list[str]:
    return sorted(
        p.name for p in FIXTURES_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def load_product_images(product: str) -> tuple[list[bytes], list[str]]:
    folder = FIXTURES_DIR / product
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    # Apenas referências brutas — styled_* e gen_* não entram no pipeline
    files = sorted(
        f for f in folder.iterdir()
        if f.suffix.lower() in exts
        and not f.stem.lower().startswith(("styled_", "gen_"))
    )
    if not files:
        raise ValueError(f"Nenhuma imagem de referência bruta em samples/{product}/")
    return [f.read_bytes() for f in files], [f.name for f in files]


# ── Server check ──────────────────────────────────────────────────────────────

def _check_servers_idle() -> None:
    """Avisa se backend ou frontend estiverem ativos."""
    import socket
    busy = []
    for port, name in [(8000, "backend"), (5173, "frontend")]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                busy.append(f"{name}:{port}")
    if busy:
        print(f"\n⚠️  AVISO: servidor(es) ativos — {', '.join(busy)}")
        print("   Geração completa pode competir por recursos.")
        print("   Para teste limpo: pare os servidores antes de rodar com --generate\n")


# ── Triage only (rápido, sem geração) ────────────────────────────────────────

def run_triage(product: str) -> None:
    from agent_runtime.triage import _infer_unified_vision_triage

    images, names = load_product_images(product)
    print(f"[FIXTURE] {len(images)} imagens: {', '.join(names)}\n")

    t0 = time.time()
    result = _infer_unified_vision_triage(uploaded_images=images, user_prompt=None)
    elapsed = time.time() - t0

    if not result:
        print("❌ Triage retornou None")
        sys.exit(1)

    print(f"{'─'*55}")
    print(f"  TRIAGE ({elapsed:.1f}s)")
    print(f"{'─'*55}")
    print(f"  garment_hint      : {result.get('garment_hint')}")
    sc = result.get("structural_contract", {})
    print(f"  garment_subtype   : {sc.get('garment_subtype')}")
    print(f"  sleeve_type       : {sc.get('sleeve_type')}")
    print(f"  silhouette_volume : {sc.get('silhouette_volume')}")
    print(f"  front_opening     : {sc.get('front_opening')}")
    ae = result.get("garment_aesthetic", {})
    print(f"  vibe              : {ae.get('vibe')} | formality: {ae.get('formality')} | season: {ae.get('season')}")
    ls = result.get("lighting_signature", {})
    print(f"  integration_risk  : {ls.get('integration_risk')}")
    sd = result.get("set_detection", {})
    print(f"  is_set            : {sd.get('is_garment_set')} (score={sd.get('set_pattern_score')})")
    img_analysis = result.get("image_analysis", "")
    print(f"  image_analysis    : {img_analysis[:120]}{'…' if len(img_analysis) > 120 else ''}")
    print(f"{'─'*55}")
    print("✅ TRIAGE OK\n")


# ── Full generation ───────────────────────────────────────────────────────────

def run_generate(product: str, prompt: str | None) -> None:
    # Isola history.json para não colidir com o backend rodando
    test_output = ROOT / "app" / "tests" / "output"
    test_output.mkdir(exist_ok=True)
    os.environ.setdefault("HISTORY_PATH", str(test_output / "test_history.json"))

    from agent_runtime.pipeline_v2 import run_pipeline_v2

    images, names = load_product_images(product)
    print(f"[FIXTURE] {len(images)} imagens: {', '.join(names)}\n")

    def on_stage(stage: str, data: dict) -> None:
        print(f"  [{stage}] {data.get('message', '')}")

    t0 = time.time()
    result = run_pipeline_v2(
        uploaded_bytes=images,
        uploaded_filenames=names,
        prompt=prompt,
        on_stage=on_stage,
    )
    elapsed = time.time() - t0

    print(f"\n{'─'*55}")
    print(f"  RESULTADO ({elapsed:.1f}s)")
    print(f"{'─'*55}")
    print(f"  preset        : {result.get('preset')}")
    print(f"  fidelity_mode : {result.get('fidelity_mode')}")
    print(f"  scene_pref    : {result.get('scene_preference')}")
    print(f"  pipeline_mode : {result.get('pipeline_mode')}")

    images_out = result.get("images") or []
    failed = result.get("failed_indices") or []
    print(f"  imagens ok    : {len(images_out)} | falhas: {len(failed)}")
    for img in images_out:
        print(f"    ✅ {img.get('url')}")
    for idx in failed:
        print(f"    ❌ índice {idx} falhou")

    prompt_out = result.get("optimized_prompt") or ""
    if prompt_out:
        print(f"\n  PROMPT:\n  {prompt_out[:300]}{'…' if len(prompt_out) > 300 else ''}")
    print(f"{'─'*55}")

    if not images_out:
        print("❌ FALHA: nenhuma imagem gerada")
        sys.exit(1)
    print("✅ GERAÇÃO OK\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--generate", action="store_true",
                        help="Executa geração real (padrão: apenas triage)")
    args = parser.parse_args()

    products = list_products()
    if not products:
        print("❌ Nenhum produto em app/tests/fixtures/")
        sys.exit(1)

    product = args.product or products[0]
    if product not in products:
        print(f"❌ Produto '{product}' não encontrado. Disponíveis: {products}")
        sys.exit(1)

    print(f"\n{'═'*55}")
    print(f"  PRODUTO : {product}")
    mode = "GERAÇÃO COMPLETA" if args.generate else "TRIAGE (análise rápida)"
    print(f"  MODO    : {mode}")
    if args.prompt:
        print(f"  PROMPT  : {args.prompt}")
    print(f"{'═'*55}\n")

    if args.generate:
        _check_servers_idle()
        run_generate(product, args.prompt)
    else:
        run_triage(product)


if __name__ == "__main__":
    main()
