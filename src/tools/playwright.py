import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'playwright.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Bootstrap run(): délègue à l'impl interne pour éviter les side-effects à l'import

def run(**params):
    from ._playwright.api import execute  # import tardif pour éviter effets de bord
    return execute(**params)
