import sys
from pathlib import Path
backend_dir = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_dir))
from agent_runtime.marketplace_orchestrator import _resolve_runtime_options
import pprint

policy = {"runtime_defaults": {}}
res = _resolve_runtime_options(policy=policy, preset="", scene_preference="", fidelity_mode="", pose_flex_mode="")
pprint.pprint(res)
