from typing import Any, Dict

from ..services.budget_broker import compute_effective_budgets
from . import overview as op_overview
from . import tree as op_tree
from . import endpoints as op_endpoints
from . import tests as op_tests


def _with_overrides(p: Dict[str, Any], **over):
    q = dict(p)
    q.update(over)
    return q


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compose compact sections in a single call (summary-only), under strict budget.
    - Small per-section limits to respect 20KB global cap; router will enforce as a safeguard.
    - Each section returns its own pagination (next_cursor) for drill-down.
    """
    eff = compute_effective_budgets(p)
    # Conservative per-section limits
    sec_limit = max(1, min(eff.get("limit", 20), 10))

    # Force anchors_only and fast mode for compose
    base_over = {
        "fields": "anchors_only",
        "mode": "fast",
    }

    # Run sections
    ov = op_overview.run(_with_overrides(p, **base_over))
    tr = op_tree.run(_with_overrides(p, **base_over, limit=sec_limit, depth_for_tree=min(int(p.get("depth_for_tree", 3)), 2)))
    ep = op_endpoints.run(_with_overrides(p, **base_over, limit=sec_limit))
    ts = op_tests.run(_with_overrides(p, **base_over, limit=sec_limit))

    sections = {
        "overview": {
            "returned_count": ov.get("returned_count", 0),
            "total_count": ov.get("total_count", 0),
            "truncated": ov.get("truncated", False),
            "next_cursor": ov.get("next_cursor"),
            "data": ov.get("data", {}),
        },
        "tree": {
            "returned_count": tr.get("returned_count", 0),
            "total_count": tr.get("total_count", 0),
            "truncated": tr.get("truncated", False),
            "next_cursor": tr.get("next_cursor"),
            "data": tr.get("data", []),
        },
        "endpoints": {
            "returned_count": ep.get("returned_count", 0),
            "total_count": ep.get("total_count", 0),
            "truncated": ep.get("truncated", False),
            "next_cursor": ep.get("next_cursor"),
            "data": ep.get("data", []),
        },
        "tests": {
            "returned_count": ts.get("returned_count", 0),
            "total_count": ts.get("total_count", 0),
            "truncated": ts.get("truncated", False),
            "next_cursor": ts.get("next_cursor"),
            "data": ts.get("data", []),
        },
    }

    return {
        "operation": "compose",
        "sections": sections,
        "returned_count": 0,
        "total_count": 0,
        "truncated": any(v.get("truncated") for v in sections.values()),
        "stats": {}
    }
