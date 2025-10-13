import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'tool_audit.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(**params):
    # Bootstrap: délègue à l'impl interne
    from ._tool_audit.api import run as _run
    return _run(**params)
