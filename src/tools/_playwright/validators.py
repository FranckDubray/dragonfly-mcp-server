import re

ID_RE = re.compile(r'^[A-Za-z0-9._-]{4,64}$')


def validate_params(p: dict) -> None:
    op = p.get('operation')
    if op not in {"record_start", "record_list", "record_delete", "play"}:
        raise ValueError("operation invalide")

    if op in {"record_start", "record_delete", "play"}:
        rid = p.get('recording_id')
        if not rid or not isinstance(rid, str) or not ID_RE.match(rid):
            raise ValueError("recording_id invalide (^[A-Za-z0-9._-]{4,64}$)")

    if op == "play":
        mode = p.get('mode', 'run_all')
        if mode not in {"run_all", "run_until", "run_step"}:
            raise ValueError("mode invalide")
        if mode in {"run_until", "run_step"}:
            tsi = p.get('target_step_index')
            if not isinstance(tsi, int) or tsi < 0:
                raise ValueError("target_step_index requis (entier >= 0)")

    # bornes numériques de base
    if 'limit' in p:
        lim = p['limit']
        if not isinstance(lim, int) or lim < 1 or lim > 500:
            raise ValueError("limit doit être entre 1 et 500")
