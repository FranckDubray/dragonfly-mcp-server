import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'orchestrator.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Expose run() for POST /execute direct usage
# Engine logic lives under _orchestrator; we just forward to API layer.
def run(**params):
    from ._orchestrator.api import start_or_control
    return start_or_control(params)
