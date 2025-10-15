import json, sys, os
from .core import run_loop
from .db import get_db_path, get_state_kv


def main():
    # Accept optional argv: db_path; otherwise use global DB
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if not db_path:
        db_path = get_db_path()

    # Read params from DB state (written by API at start)
    raw = get_state_kv(db_path, '__global__', 'params') or '{}'
    try:
        params = json.loads(raw)
    except Exception:
        params = {}

    run_loop(db_path, params)


if __name__ == '__main__':
    main()
