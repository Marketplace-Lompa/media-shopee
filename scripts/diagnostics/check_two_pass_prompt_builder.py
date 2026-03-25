"""Valida os locks gerados pelo prompt builder do fluxo two-pass."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.two_pass_flow import build_art_direction_two_pass_edit_prompt

def check_mode(mode):
    print(f"\n======== VALIDANDO FIDELIDADE: '{mode.upper()}' ==========")
    art_dir = {
        "request": {
            "fidelity_mode": mode,
            "directive_hints": {"angle_directive": "MANDATORY SHOT ANGLE: Full back view."}
        }
    }
    
    prompt = build_art_direction_two_pass_edit_prompt(
        art_direction=art_dir,
        structural_contract={},
        identity_names=["Anna BR Model"],
        locks=["garment architecture"] # Apenas mock para passar os required
    )
    
    # Adicionando simulacao do que a run_pipeline faz na hora de colocar estrita
    orig_prompt = prompt
    locks_used = ["garment architecture"]
    if mode == "estrita":
         locks_used.append("pose")
         locks_used.append("garment mapping")
    
    prompt_str = orig_prompt.replace(
        "Keep the garment exactly the same: garment architecture.", 
        "Keep the garment exactly the same: " + ", ".join(locks_used) + "."
    )
    
    print("\n[RESULTADO DO PROMPT]")
    if "Keep the garment exactly the same: garment architecture, pose, garment mapping" in prompt_str:
         print(f"[!] 🚨 PERIGO ('{mode}'): A flag 'estrita' forçou na linha 785 -> 'pose, garment mapping'. A modelo não vai poder virar de costas.")
    else:
         print(f"[v] ✅ SAFE ('{mode}'): Pose não está listada entre os locks obrigatórios! Ângulo livre para girar.")

def main():
    check_mode("balanceada")
    check_mode("estrita")


if __name__ == "__main__":
    main()
