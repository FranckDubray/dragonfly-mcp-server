import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', '..', 'tool_specs', 'excel_row.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
