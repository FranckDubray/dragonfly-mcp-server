import json, sys, os, signal, time
from .core import run_loop


def _sig_name(sig: int) -> str:
    try:
        return signal.Signals(sig).name
    except Exception:
        return str(sig)


def setup_signal_handlers(db_path: str):
    from .db import set_state_kv, begin_step, end_step

    def handler(sig, frame):
        sig_name = _sig_name(sig)
        t0 = time.time()
        try:
            begin_step(db_path, '__global__', 'signal_shutdown', 'signal_shutdown', {"signal": sig_name})
        except Exception:
            pass
        try:
            set_state_kv(db_path, '__global__', 'last_signal', sig_name)
            set_state_kv(db_path, '__global__', 'phase', 'canceling')
            set_state_kv(db_path, '__global__', 'cancel', 'true')
        except Exception:
            pass
        try:
            end_step(db_path, '__global__', 'signal_shutdown', 'signal_shutdown', 'succeeded', t0, {"signal": sig_name})
        except Exception:
            pass
        # Do not hard-exit immediately: let run_loop notice cancel and exit cleanly.
        # As a safety, if another signal arrives, default handler will terminate.

    # POSIX
    try:
        signal.signal(signal.SIGTERM, handler)
    except Exception:
        pass
    try:
        signal.signal(signal.SIGINT, handler)
    except Exception:
        pass
    # Windows console break (when applicable)
    try:
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, handler)
    except Exception:
        pass


def main():
    # Exige un db_path en argument (passé par _spawn_detached)
    if len(sys.argv) < 2:
        raise SystemExit("runner: db_path argument is required")
    db_path = sys.argv[1]

    # Set up graceful signal handling
    setup_signal_handlers(db_path)

    # Read params from DB state (written by API at start)
    from .db import get_state_kv
    raw = get_state_kv(db_path, '__global__', 'params') or '{}'
    try:
        params = json.loads(raw)
    except Exception:
        params = {}

    run_loop(db_path, params)


if __name__ == '__main__':
    main()
