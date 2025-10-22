import json
from .validators import validate_params
from .core_record import record_start, record_list, record_delete
from .core_play import play_run


def execute(**params):
    try:
        op = params.get('operation')
        validate_params(params)

        if op == 'record_start':
            return record_start(params)
        elif op == 'record_list':
            return record_list(params)
        elif op == 'record_delete':
            return record_delete(params)
        elif op == 'play':
            return play_run(params)
        else:
            return {
                "ok": False,
                "error": f"Unsupported operation: {op}",
            }
    except Exception as e:
        # Retour d'erreur minimaliste et sûr (sans stacktrace verbeuse)
        return {"ok": False, "error": str(e)}
