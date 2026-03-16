import sys
from pathlib import Path

backend_dir = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_dir))

from agent_runtime.pipeline_v2 import run_pipeline_v2
import uuid

def mock_image():
    dummy = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    return dummy

def test_fidelity_impact():
    modes = ["balanceada", "estrita"]
    for mode in modes:
        try:
            print(f"\n[ MODO: {mode.upper()} ]")
            res = run_pipeline_v2(
                prompt="Ultra realistic casual street fashion. A woman posing outdoors, back view.",
                uploaded_bytes=[mock_image()],
                fidelity_mode=mode,
                directive_hints={"angle_directive": "MANDATORY SHOT ANGLE: Full back view. The model is facing entirely away from the camera."},
                n_images=1,
            )
            # Imprime o prompt exato do loop que define o Lock
            observability_prompt = res.get('edit_prompt', '')
            if "Keep the garment exactly the same: pose, garment mapping" in observability_prompt:
                print("==> 🚨 LOCK FATAL DETECTADO!: O Stage 2 forçou 'pose, garment mapping'. Impossible to change angle!")
            else:
                print("==> ✅ LENTO E LIVRE: 'pose' não está locada, o gerador pode seguir o angle_directive.")
                
        except Exception as e:
            # We purposely ignore generation failure, we just want to see if the string built the prompt!
            if "Stage 2 falhou" in str(e) or "Pipeline v2 requer" in str(e) or "list index out of range" in str(e):
                pass
            print(f"Gerador mock estourou, mas podemos checar logs manuais se precisar. {type(e)}")

test_fidelity_impact()
