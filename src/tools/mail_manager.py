import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'mail_manager.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Optionnel: route de compat pour POST /execute direct
# Le serveur détecte x-dragonfly.background et lance en BG, mais on
# expose run() pour tests et fallback.
def run(**params):
    from ._mail_manager.api import start_or_control
    return start_or_control(params)
