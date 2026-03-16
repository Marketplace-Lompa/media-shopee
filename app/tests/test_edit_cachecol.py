#!/usr/bin/env python3
"""
Teste iterativo: adicionar cachecol do conjunto à imagem gerada 03aeccb8.

Base  : app/tests/output/gen_03aeccb8_back_or_side.png
Ref   : app/tests/samples/poncho-ruana-listras/IMG_3328.jpg (poncho + cachecol)
Output: app/tests/output/edit_cachecol_v{N}.png

Uso:
  python app/tests/test_edit_cachecol.py
  python app/tests/test_edit_cachecol.py --no-crop   # sem crop da referência
"""
from __future__ import annotations
import argparse, json, sys, time
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "app" / "tests" / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

BASE_IMAGE  = OUTPUT_DIR / "gen_03aeccb8_back_or_side.png"
REF_IMAGE   = ROOT / "app/tests/samples/poncho-ruana-listras/IMG_3328.jpg"


# ── Pré-processo da referência ────────────────────────────────────────────────

def prepare_reference(crop: bool = True) -> bytes:
    """
    Fotos já corrigidas de EXIF — apenas redimensiona para economizar tokens.
    Cachecol visível: enrolado no pescoço, caindo pela frente do corpo.
    """
    from PIL import Image
    with Image.open(REF_IMAGE) as img:
        # Reduz resolução mantendo aspecto — não precisa mais de crop agressivo
        img.thumbnail((1024, 1024))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=88)
        return buf.getvalue()


# ── Teste ─────────────────────────────────────────────────────────────────────

def run(crop: bool) -> None:
    from edit_agent import refine_edit_instruction
    from generator import edit_image

    print(f"\n{'═'*60}")
    print(f"  BASE    : {BASE_IMAGE.name}")
    print(f"  REF     : {REF_IMAGE.name}  (crop={'sim' if crop else 'não'})")
    print(f"{'═'*60}\n")

    if not BASE_IMAGE.exists():
        print(f"❌ Base não encontrada: {BASE_IMAGE}")
        sys.exit(1)
    if not REF_IMAGE.exists():
        print(f"❌ Referência não encontrada: {REF_IMAGE}")
        sys.exit(1)

    source_bytes = BASE_IMAGE.read_bytes()
    ref_bytes    = prepare_reference(crop=crop)

    # Salvar referência processada para inspecionar
    ref_debug = OUTPUT_DIR / f"edit_cachecol_ref_{'crop' if crop else 'full'}.jpg"
    ref_debug.write_bytes(ref_bytes)
    print(f"[REF] Referência processada salva: {ref_debug.name}\n")

    # Cachecol como peça solta: cruzado no peito, caindo até a cintura — não integrado
    instruction = (
        "incluir o cachecol do conjunto como acessório solto: "
        "cruzado levemente no peito e caindo pelas duas extremidades até a cintura, "
        "visivelmente separado da ruana (nao é uma gola). "
        "A ruana continua aberta na frente exatamente como está."
    )

    # ── Etapa 1: Edit Agent ───────────────────────────────────────────────────
    print("[STEP 1] Refinando instrução com Edit Agent...")
    t0 = time.time()
    analysis = refine_edit_instruction(
        edit_instruction=instruction,
        source_image_bytes=source_bytes,
        source_prompt=None,
        reference_images_bytes=[ref_bytes],
    )
    print(f"[STEP 1] concluído em {time.time()-t0:.1f}s\n")

    print(f"  edit_type  : {analysis['edit_type']}")
    print(f"  confidence : {analysis['confidence']}")
    print(f"  ref_item   : {analysis.get('reference_item_description','—')[:120]}")
    print(f"  summary_pt : {analysis.get('change_summary_ptbr','—')}")
    print(f"\n  PROMPT FINAL ({len(analysis['final_prompt'])} chars):")
    print(f"  {analysis['final_prompt']}\n")

    # ── Etapa 2: Edição com Nano Banana ──────────────────────────────────────
    print("[STEP 2] Gerando edição com Nano Banana...")
    t1 = time.time()

    # Session ID único por tentativa
    suffix = "crop" if crop else "full"
    import uuid
    session_id = f"edit_cachecol_{suffix}_{str(uuid.uuid4())[:6]}"

    results = edit_image(
        source_image_bytes=source_bytes,
        edit_prompt=analysis["final_prompt"],
        aspect_ratio="4:5",
        resolution="1K",
        thinking_level="HIGH",
        session_id=session_id,
        reference_images_bytes=[ref_bytes],
    )
    print(f"[STEP 2] concluído em {time.time()-t1:.1f}s\n")

    if not results:
        print("❌ FALHA: Nano não retornou imagem")
        sys.exit(1)

    result = results[0]
    src_path = Path(result["path"])

    # Copiar para output de teste com nome legível
    out_name = f"edit_cachecol_{suffix}_result.png"
    out_path = OUTPUT_DIR / out_name
    import shutil
    shutil.copy(src_path, out_path)

    print(f"{'─'*60}")
    print(f"  ✅ RESULTADO: {out_path}")
    print(f"  size: {result['size_kb']} KB")
    print(f"{'─'*60}\n")

    # Salvar log da sessão
    log = {
        "session_id": session_id,
        "base": str(BASE_IMAGE),
        "reference": str(REF_IMAGE),
        "crop": crop,
        "instruction": instruction,
        "edit_type": analysis["edit_type"],
        "confidence": analysis["confidence"],
        "reference_item_description": analysis.get("reference_item_description"),
        "final_prompt": analysis["final_prompt"],
        "output": str(out_path),
    }
    log_path = OUTPUT_DIR / f"edit_cachecol_{suffix}_log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    print(f"  Log: {log_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-crop", action="store_true", help="Não recortar referência")
    args = parser.parse_args()
    run(crop=not args.no_crop)


if __name__ == "__main__":
    main()
