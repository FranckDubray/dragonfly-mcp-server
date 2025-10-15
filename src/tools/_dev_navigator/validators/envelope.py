from typing import Any, Dict

from ..services.constants import DEFAULT_LIMIT, MAX_LIMIT
from ..services.root_guard import ensure_under_allowed_roots

ALLOWED_OPS = {
    "compose","overview","tree","search","outline","open","endpoints","tests","metrics",
    "symbol_info","find_callers","find_callees","find_references","call_patterns"
}

FIELDS_ENUM = {"anchors_only", "anchors+snippets", "full"}
MODE_ENUM = {"fast", "balanced", "thorough"}
DOC_POLICY_ENUM = {"outline_only", "allow_docs"}
CONSISTENCY_ENUM = {"best_effort", "require_same_release"}


def _ensure_type(obj: Dict[str, Any], key: str, expected, default=None):
    if key not in obj or obj[key] is None:
        if default is not None:
            obj[key] = default
            return
        raise ValueError(f"Missing parameter: {key}")
    if expected == int and isinstance(obj[key], bool):
        raise ValueError(f"Invalid type for {key}: bool not allowed where int expected")
    if not isinstance(obj[key], expected):
        raise ValueError(f"Invalid type for {key}: expected {expected.__name__}")


def validate_envelope(p: Dict[str, Any]) -> Dict[str, Any]:
    p = dict(p)  # shallow copy
    _ensure_type(p, "operation", str)
    if p["operation"] not in ALLOWED_OPS:
        raise ValueError("Invalid operation")
    _ensure_type(p, "path", str)

    # SECURITY: ensure path is under allowed roots (project root ./ OR clones root ../)
    try:
        abs_ok = ensure_under_allowed_roots(p["path"])  # raises if invalid
        p["path"] = abs_ok
    except ValueError as e:
        raise ValueError("Invalid path: not under allowed roots (./ or ../)") from e

    # Optionals with defaults (20KB policy)
    p.setdefault("limit", DEFAULT_LIMIT)
    p.setdefault("fields", "anchors_only")
    p.setdefault("mode", "fast")
    p.setdefault("verbose", False)
    p.setdefault("doc_policy", "outline_only")
    p.setdefault("use_release_index", True)
    p.setdefault("consistency_mode", "best_effort")

    # Type checks
    if not isinstance(p["limit"], int) or p["limit"] < 1 or p["limit"] > MAX_LIMIT:
        raise ValueError(f"Invalid limit (1..{MAX_LIMIT})")
    if p["fields"] not in FIELDS_ENUM:
        raise ValueError("Invalid fields")
    if p["mode"] not in MODE_ENUM:
        raise ValueError("Invalid mode")
    if p["doc_policy"] not in DOC_POLICY_ENUM:
        raise ValueError("Invalid doc_policy")
    if p["consistency_mode"] not in CONSISTENCY_ENUM:
        raise ValueError("Invalid consistency_mode")

    # Arrays
    if "pins" in p and (not isinstance(p["pins"], list) or not all(isinstance(x, str) for x in p["pins"])):
        raise ValueError("pins must be array of strings")
    if "explicit_allowlist" in p and (not isinstance(p["explicit_allowlist"], list) or not all(isinstance(x, str) for x in p["explicit_allowlist"])):
        raise ValueError("explicit_allowlist must be array of strings")

    # Q&A optional parameters sanity (types only; semantic checks occur in qna)
    # symbol_info
    if "fqname" in p and not isinstance(p["fqname"], str):
        raise ValueError("fqname must be string")
    if "symbol_key" in p and not isinstance(p["symbol_key"], str):
        raise ValueError("symbol_key must be string")
    if "line" in p and not isinstance(p["line"], int):
        raise ValueError("line must be integer")
    # find_callers / call_patterns
    if "callee_key" in p and not isinstance(p["callee_key"], str):
        raise ValueError("callee_key must be string")
    # find_callees
    if "caller_symbol_id" in p and not isinstance(p["caller_symbol_id"], int):
        raise ValueError("caller_symbol_id must be integer")
    # find_references
    if "symbol_id" in p and not isinstance(p["symbol_id"], int):
        raise ValueError("symbol_id must be integer")
    if "kind" in p and not isinstance(p["kind"], str):
        raise ValueError("kind must be string")

    return p
