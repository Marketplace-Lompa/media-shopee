#!/usr/bin/env python3
"""
Smoke Test — Prompt Only (sem geração de imagem).

Valida se o prompt gerado pelo pipeline respeita os contratos do mode
solicitado, sem consumir créditos de API de imagem.

Usage:
  python scripts/backend/experiments/test_prompt_only.py [--mode MODE] [--image PATH]

Exemplo:
  python scripts/backend/experiments/test_prompt_only.py --mode lifestyle
  python scripts/backend/experiments/test_prompt_only.py --mode natural --image /path/to/ref.jpg

Saída: JSON com prompt completo + metadados em docs/reports/smoke-{mode}-result.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Adiciona o backend ao path
_ROOT = Path(__file__).resolve().parents[3]
_BACKEND = _ROOT / "app" / "backend"
sys.path.insert(0, str(_BACKEND))

_REPORTS = _ROOT / "docs" / "reports"
_DEFAULT_IMAGE = (
    _ROOT / "app" / "tests" / "samples" / "poncho-ruana-listras" / "IMG_3321.jpg"
)

# ──────────────────────────────────────────────
# Contratos por mode — keywords que DEVEM existir
# e keywords que NÃO DEVEM existir no prompt
# ──────────────────────────────────────────────
_CONTRACTS: dict[str, dict] = {
    "lifestyle": {
        "must_contain_any": [
            # Verbos/frases de ação real que o Gemini usa
            "mid-activity", "mid-action", "arranging", "browsing",
            "reaching", "adjusting", "carrying", "walking",
            "leans", "leaning", "reach for", "picking up",
            "pouring", "setting down", "mid-morning", "mid-stride",
            "checking", "scrolling", "holding", "sipping",
        ],
        "must_not_contain": [
            "catalog-worthy", "standing pose",
            "premium fashion", "showroom",
        ],
        "label": "Lifestyle — ação obrigatória, zero editorial",
    },
    "natural": {
        "must_contain_any": [
            # Indicadores candid / não-posado
            "encountered", "ordinary", "unposed", "casual",
            "candid", "everyday", "routine", "observational",
            "lived-in", "mid-stride", "pauses", "unkempt",
            "real-life", "natural light", "imperfect",
            "caught in", "transitional", "messy", "shifted",
            "away from the camera", "not looking", "looking away",
            "quiet", "morning light",
        ],
        "must_not_contain": [
            "catalog-worthy", "editorial", "premium",
            "showroom", "curated",
        ],
        "label": "Natural — candid paparazzi, sem curadoria",
    },
    "editorial_commercial": {
        "must_contain_any": [
            # Tom editorial / composição autoral
            "editorial", "commercial", "composed", "authored",
            "commanding", "assertive", "intentional",
            "directly into the lens", "looking into the lens",
            "defined", "geometric shadows", "structured",
        ],
        "must_not_contain": [
            "candid", "paparazzi", "snapshot",
        ],
        "label": "Editorial — composição autoral",
    },
    "catalog_clean": {
        "must_contain_any": [
            # Olhar direto para câmera
            "looking directly", "direct eye contact", "into the camera",
            "into the lens", "at the viewer", "facing the camera",
            "looking at the camera", "warm smile", "open smile",
            "approachable", "confident",
        ],
        "must_not_contain": [
            "looking away", "looking down", "candid",
            "mid-activity", "mid-action",
        ],
        "label": "Catalog Clean — olhar para câmera, pose comercial",
    },
}


def _run_prompt_test(mode: str, image_path: Path) -> dict:
    """Executa o pipeline de prompt sem gerar imagem."""
    from agent import run_agent

    if not image_path.exists():
        print(f"❌ Imagem não encontrada: {image_path}")
        sys.exit(1)

    image_bytes = image_path.read_bytes()
    result = run_agent(
        user_prompt=None,
        uploaded_images=[image_bytes],
        pool_context="",
        aspect_ratio="9:16",
        resolution="1024x1536",
        mode=mode,
    )
    return result


def _validate_contract(prompt: str, mode: str) -> list[str]:
    """Retorna lista de violações encontradas."""
    contract = _CONTRACTS.get(mode)
    if not contract:
        return [f"⚠️  Sem contrato definido para mode '{mode}' — skipping validation"]

    violations = []
    low = prompt.lower()

    # Verifica presença obrigatória
    must_any = contract.get("must_contain_any", [])
    if must_any and not any(kw in low for kw in must_any):
        violations.append(
            f"❌ MISSING: nenhuma keyword de contrato encontrada: {must_any}"
        )

    # Verifica ausência obrigatória
    for forbidden in contract.get("must_not_contain", []):
        if forbidden.lower() in low:
            violations.append(f"❌ LEAK: keyword proibida encontrada: '{forbidden}'")

    return violations


def main():
    parser = argparse.ArgumentParser(description="Smoke test de prompt por mode")
    parser.add_argument("--mode", default="lifestyle", help="Mode a testar (default: lifestyle)")
    parser.add_argument("--image", default=str(_DEFAULT_IMAGE), help="Caminho da imagem de referência")
    args = parser.parse_args()

    mode = args.mode.strip().lower()
    image_path = Path(args.image)

    print(f"\n🧪 Smoke Test — Prompt Only")
    print(f"   Mode: {mode}")
    print(f"   Image: {image_path.name}")
    print(f"   {'─' * 40}")

    result = _run_prompt_test(mode, image_path)
    prompt = result.get("prompt", "")

    # Valida contrato
    violations = _validate_contract(prompt, mode)

    # Salva resultado
    _REPORTS.mkdir(parents=True, exist_ok=True)
    out_file = _REPORTS / f"smoke-{mode}-result.json"
    out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Report
    contract = _CONTRACTS.get(mode, {})
    print(f"\n📋 Contrato: {contract.get('label', mode)}")
    print(f"📝 Prompt ({len(prompt.split())} words):")
    print(f"   {prompt[:200]}...")
    print(f"\n💾 Resultado salvo em: {out_file}")

    if violations:
        print(f"\n{'='*50}")
        print(f"❌ FALHOU — {len(violations)} violação(ões):")
        for v in violations:
            print(f"   {v}")
        sys.exit(1)
    else:
        print(f"\n✅ APROVADO — contrato {mode} respeitado")
        sys.exit(0)


if __name__ == "__main__":
    main()
