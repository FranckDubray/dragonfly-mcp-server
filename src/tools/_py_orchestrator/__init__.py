# Python orchestrator package
# Path bootstrap to ensure 'src' package is importable when server cwd/PYTHONPATH differ.
import sys
from pathlib import Path
try:
    _ROOT = Path(__file__).resolve().parents[3]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
except Exception:
    pass

# Public imports for worker authoring convenience
from .runtime import step, Next, Exit, SubGraph, SubGraphRef, Process
