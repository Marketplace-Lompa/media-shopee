import asyncio
from pathlib import Path
from agent_runtime.pipeline_v2 import run_pipeline_v2
import uuid
import os

from config import ROOT_DIR

script_dir = ROOT_DIR / "app" / "tests"
sample_dir = script_dir / "samples"
sample_dir.mkdir(parents=True, exist_ok=True)

# Procurar amostras ou criar uma dummy pra simular a imagem real da peca
ref_image_path = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
if not ref_image_path:
    print(f"Por favor, certifique-se de que ha pelo menos uma imagem na pasta {sample_dir}")
    # Gerando um byte basico para simular se nao achar (em DEV)
    dummy_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    with open(sample_dir / "dummy_test.png", "wb") as f:
        f.write(dummy_bytes)
    ref_image_path = [sample_dir / "dummy_test.png"]

ref_bytes = ref_image_path[0].read_bytes()

async def test_modes():
    session_id = f"fid_test_{uuid.uuid4().hex[:6]}"
    
    modes = ["balanceada", "estrita"]
    for mode in modes:
        print(f"\n--- Iniciando Fluxo V2 com fidelity_mode='{mode}' ---")
        try:
            res = run_pipeline_v2(
                prompt="Ultra-realistic photo of a woman walking away, showing the back of the garment.",
                uploaded_bytes=[ref_bytes],
                session_id=session_id + "_" + mode,
                fidelity_mode=mode,
                directive_hints={"angle_directive": "MANDATORY SHOT ANGLE: Full back view."},
                n_images=1
            )
            print(f"Sucesso [{mode}]. Report json está em outputs/v2diag_{session_id}_{mode}")
        except Exception as e:
            print(f"Erro no modo {mode}: {e}")

if __name__ == "__main__":
    asyncio.run(test_modes())
