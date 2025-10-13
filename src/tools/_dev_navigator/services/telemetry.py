import time
from functools import wraps

def with_telemetry(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        try:
            res = fn(*args, **kwargs)
            res = res if isinstance(res, dict) else {"data": res}
            duration_ms = int((time.time() - t0) * 1000)
            stats = res.get("stats", {})
            stats.update({"duration_ms": duration_ms})
            res["stats"] = stats
            return res
        except Exception:
            # let upper layer handle
            raise
    return wrapper
