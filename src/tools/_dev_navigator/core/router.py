from typing import Any, Dict

from ..services.telemetry import with_telemetry
from ..services.response import ensure_envelope
from ..services.payload_budget import enforce_cap
from . import compose as op_compose
from . import overview as op_overview
from . import tree as op_tree
from . import search as op_search
from . import outline as op_outline
from . import open_files as op_open
from . import endpoints as op_endpoints
from . import tests as op_tests
from ..release_index import qna as op_qna


@with_telemetry
def route_operation(p: Dict[str, Any]) -> Dict[str, Any]:
    op = p["operation"]
    if op == "compose":
        res = op_compose.run(p)
    elif op == "overview":
        res = op_overview.run(p)
    elif op == "tree":
        res = op_tree.run(p)
    elif op == "search":
        res = op_search.run(p)
    elif op == "outline":
        res = op_outline.run(p)
    elif op == "open":
        res = op_open.run(p)
    elif op == "endpoints":
        res = op_endpoints.run(p)
    elif op == "tests":
        res = op_tests.run(p)
    elif op in ("symbol_info", "find_callers", "find_callees", "find_references", "call_patterns"):
        res = op_qna.run(p)
    else:
        res = {
            "operation": op,
            "errors": [{"code": "invalid_parameters", "message": f"Unknown operation: {op}", "scope": "tool", "recoverable": False}],
            "returned_count": 0,
            "total_count": 0,
            "truncated": False
        }
    res = ensure_envelope(res, op)
    res = enforce_cap(res)
    return res
