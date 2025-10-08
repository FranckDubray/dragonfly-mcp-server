from __future__ import annotations
import os
import sys
import json
import math
import logging
from typing import Any
from fastapi.responses import JSONResponse

LOG = logging.getLogger(__name__)

# Env-configurable knobs
BIGINT_AS_STRING = os.getenv('BIGINT_AS_STRING', '1').strip().lower() in ('1','true','yes','on')
BIGINT_STR_THRESHOLD = int(os.getenv('BIGINT_STR_THRESHOLD', '1000'))

# Lift Python 3.11+ safety cap for int->str to support very large factorials
try:
    if hasattr(sys, 'set_int_max_str_digits'):
        val = os.getenv('PY_INT_MAX_STR_DIGITS', '0').strip()  # 0 = unlimited
        sys.set_int_max_str_digits(0 if val == '' else int(val))
        LOG.info(f"int->str max digits set to {val or 'unlimited'}")
except Exception as e:
    LOG.warning(f"Could not set int max str digits: {e}")

# Surrogates handling
_SUR_MIN = 0xD800
_SUR_MAX = 0xDFFF

def strip_surrogates(s: str) -> str:
    try:
        if any(_SUR_MIN <= ord(ch) <= _SUR_MAX for ch in s):
            return ''.join(ch if not (_SUR_MIN <= ord(ch) <= _SUR_MAX) else '\ufffd' for ch in s)
    except Exception:
        pass
    return s


def sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize an object to make it JSON-compliant,
    incl. huge ints, NaN/Inf, invalid surrogates in strings, and sanitize dict KEYS.
    """
    if isinstance(obj, dict):
        safe_dict = {}
        for k, v in obj.items():
            try:
                if isinstance(k, str):
                    key = strip_surrogates(k)
                else:
                    key = strip_surrogates(str(k))
            except Exception:
                key = str(k)
            safe_dict[key] = sanitize_for_json(v)
        return safe_dict
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, int):
        try:
            if BIGINT_AS_STRING:
                s = str(obj)
                if len(s) > BIGINT_STR_THRESHOLD:
                    return s
        except Exception:
            pass
        return obj
    elif isinstance(obj, float):
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        elif math.isnan(obj):
            return "NaN"
        else:
            return obj
    elif isinstance(obj, str):
        return strip_surrogates(obj)
    else:
        return obj


class SafeJSONResponse(JSONResponse):
    """JSONResponse that automatically sanitizes content before encoding."""
    def render(self, content: Any) -> bytes:
        sanitized = sanitize_for_json(content)
        return json.dumps(
            sanitized,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
