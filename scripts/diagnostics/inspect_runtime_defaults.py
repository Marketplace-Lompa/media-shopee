"""Inspeciona os defaults resolvidos pelo orquestrador de marketplace."""

import pprint
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_runtime.marketplace_orchestrator import _resolve_runtime_options

policy = {"runtime_defaults": {}}
res = _resolve_runtime_options(policy=policy, preset="", scene_preference="", fidelity_mode="", pose_flex_mode="")
pprint.pprint(res)
