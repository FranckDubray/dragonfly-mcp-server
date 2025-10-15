import os, json, time
from urllib import request, error

BASE_URL = os.environ.get('MCP_BASE_URL', 'http://127.0.0.1:8000')
EXECUTE_URL = BASE_URL.rstrip('/') + '/execute'


def _post_execute(payload: dict, timeout: float = 10.0) -> dict:
    data = json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    req = request.Request(EXECUTE_URL, data=data, headers=headers, method='POST')
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body) if body else {}
    except error.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
            return json.loads(body)
        except Exception:
            raise
    except Exception:
        raise


def call_with_retry(tool: str, params: dict, retries: int = 3, backoff: float = 0.5, timeout: float = 10.0) -> dict:
    last_err = None
    for i in range(max(1, retries)):
        try:
            return _post_execute({"tool": tool, "params": params}, timeout=timeout)
        except Exception as e:
            last_err = e
            if i < retries - 1:
                time.sleep(backoff * (2 ** i))
    if last_err:
        raise last_err
    return {}
