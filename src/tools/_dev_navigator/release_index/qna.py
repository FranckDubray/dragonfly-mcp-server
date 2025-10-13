from typing import Any, Dict

from ..services.errors import error_response
from ..services.pagination import paginate_list

SUPPORTED = {"symbol_info", "find_callers", "find_callees", "find_references", "call_patterns"}

def run(p: Dict[str, Any]) -> Dict[str, Any]:
    op = p["operation"]
    if op not in SUPPORTED:
        return error_response(op, "invalid_parameters", f"Unsupported index op: {op}")

    # Lazy import to avoid hard dependency at module import time
    try:
        from . import reader as R
    except Exception as e:
        return {
            "operation": op,
            "errors": [{"code": "release_index_missing", "message": str(e), "scope": "tool", "recoverable": True}],
            "returned_count": 0,
            "total_count": 0,
            "truncated": False,
        }

    db_path, err = R.resolve_index_db(p["path"], p.get("release_tag"), p.get("commit_hash"))
    if not db_path:
        return {
            "operation": op,
            "errors": [err],
            "returned_count": 0,
            "total_count": 0,
            "truncated": False,
        }
    conn = R._open_ro(db_path)
    try:
        limit = int(p.get("limit", 20))
        if op == "symbol_info":
            info = R.query_symbol_info(conn, p.get("fqname"), p.get("symbol_key"), p.get("path"), p.get("line"))
            return {"operation": op, "data": info or {}, "returned_count": 1 if info else 0, "total_count": 1 if info else 0, "truncated": False}
        if op == "find_callers":
            callee_key = p.get("callee_key") or p.get("symbol_key")
            if not callee_key:
                return error_response(op, "invalid_parameters", "callee_key or symbol_key required")
            items = R.query_find_callers(conn, callee_key, limit)
            page, total, next_c = paginate_list(items, limit, p.get("cursor"))
            return {"operation": op, "data": page, "returned_count": len(page), "total_count": total, "truncated": next_c is not None, "next_cursor": next_c}
        if op == "find_callees":
            sid = p.get("caller_symbol_id")
            if sid is None:
                return error_response(op, "invalid_parameters", "caller_symbol_id required")
            items = R.query_find_callees(conn, int(sid), limit)
            page, total, next_c = paginate_list(items, limit, p.get("cursor"))
            return {"operation": op, "data": page, "returned_count": len(page), "total_count": total, "truncated": next_c is not None, "next_cursor": next_c}
        if op == "find_references":
            items = R.query_find_references(conn, p.get("symbol_id"), p.get("symbol_key"), p.get("kind"), limit)
            page, total, next_c = paginate_list(items, limit, p.get("cursor"))
            return {"operation": op, "data": page, "returned_count": len(page), "total_count": total, "truncated": next_c is not None, "next_cursor": next_c}
        if op == "call_patterns":
            callee_key = p.get("callee_key") or p.get("symbol_key")
            if not callee_key:
                return error_response(op, "invalid_parameters", "callee_key or symbol_key required")
            items = R.query_call_patterns(conn, callee_key, limit)
            page, total, next_c = paginate_list(items, limit, p.get("cursor"))
            return {"operation": op, "data": page, "returned_count": len(page), "total_count": total, "truncated": next_c is not None, "next_cursor": next_c}
    finally:
        try:
            conn.close()
        except Exception:
            pass
