import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'dev_navigator.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Note: run() sera implémenté dans _dev_navigator/api.py (appelé par l'app factory)
# Ce stub évite tout side-effect à l'import et se conforme au guide.

def run(**params):
    # Orchestrator will import _dev_navigator.api at execution time.
    from ._dev_navigator.api import execute
    return execute(**params)
