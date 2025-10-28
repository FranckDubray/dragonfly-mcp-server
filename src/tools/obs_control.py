import json, os, importlib


def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'obs_control.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(**params):
    # Délégation vers l'implémentation interne si disponible.
    try:
        module_name = __name__.rsplit('.', 1)[0] + '._obs_control.api'
        api = importlib.import_module(module_name)
        return api.run(**params)
    except ModuleNotFoundError:
        return {
            "ok": False,
            "error": "not_implemented",
            "message": "obs_control est enregistré (spec OK). Implémentation à venir. /execute renverra not_implemented tant que _obs_control n’est pas ajouté."
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "unexpected_error",
            "message": f"obs_control: erreur inattendue (impl. absente ou incomplète): {type(e).__name__}"
        }
