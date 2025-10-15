from typing import Any, Dict, Optional, List
import sqlite3


def query_symbol_info(conn: sqlite3.Connection, fqname: Optional[str], symbol_key: Optional[str], path: Optional[str], line: Optional[int]) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        if fqname or symbol_key:
            if fqname:
                cur.execute("SELECT id,file_id,lang,name,fqname,kind,signature,start_line,start_col,end_line,end_col FROM symbols WHERE fqname=? LIMIT 1", (fqname,))
            else:
                cur.execute("SELECT id,file_id,lang,name,fqname,kind,signature,start_line,start_col,end_line,end_col FROM symbols WHERE symbol_key=? LIMIT 1", (symbol_key,))
        elif path and line is not None:
            cur.execute(
                """
                SELECT s.id,s.file_id,s.lang,s.name,s.fqname,s.kind,s.signature,s.start_line,s.start_col,s.end_line,s.end_col
                FROM symbols s
                JOIN files f ON s.file_id=f.id
                WHERE f.relpath=? AND (? >= s.start_line AND ? <= COALESCE(s.end_line, s.start_line))
                ORDER BY (COALESCE(s.end_line, s.start_line) - s.start_line) ASC
                LIMIT 1
                """,
                (path, line, line),
            )
        else:
            return None
        row = cur.fetchone()
        if not row:
            return None
        # Fetch file path
        fpath = None
        try:
            cur2 = conn.cursor()
            cur2.execute("SELECT relpath FROM files WHERE id=?", (row[1],))
            r2 = cur2.fetchone()
            fpath = r2[0] if r2 else None
        finally:
            try:
                cur2.close()
            except Exception:
                pass
        return {
            "id": row[0],
            "file_id": row[1],
            "lang": row[2],
            "name": row[3],
            "fqname": row[4],
            "kind": row[5],
            "signature": row[6],
            "anchor": {"path": fpath, "start_line": row[7], "start_col": row[8], "end_line": row[9], "end_col": row[10]},
        }
    finally:
        cur.close()


def query_find_callers(conn: sqlite3.Connection, callee_key: str, limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT c.caller_symbol_id, COUNT(*) as freq
            FROM calls c
            WHERE c.callee_key=?
            GROUP BY c.caller_symbol_id
            ORDER BY freq DESC
            LIMIT ?
            """,
            (callee_key, limit * 2),
        )
        rows = cur.fetchall()
        items: List[Dict[str, Any]] = []
        for caller_id, freq in rows:
            if caller_id is None:
                items.append({"caller_symbol": None, "count": int(freq)})
                continue
            cur2 = conn.cursor()
            try:
                cur2.execute("SELECT fqname,name,lang FROM symbols WHERE id=?", (caller_id,))
                r2 = cur2.fetchone()
                items.append({"caller_symbol": {"id": caller_id, "fqname": r2[0] if r2 else None, "name": r2[1] if r2 else None, "lang": r2[2] if r2 else None}, "count": int(freq)})
            finally:
                cur2.close()
        return items
    finally:
        cur.close()


def query_find_callees(conn: sqlite3.Connection, caller_symbol_id: int, limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT callee_symbol_id, callee_key, COUNT(*) as freq
            FROM calls
            WHERE caller_symbol_id=?
            GROUP BY callee_symbol_id, callee_key
            ORDER BY freq DESC
            LIMIT ?
            """,
            (caller_symbol_id, limit * 2),
        )
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for sid, ckey, freq in rows:
            fq = None
            if sid is not None:
                cur2 = conn.cursor()
                try:
                    cur2.execute("SELECT fqname,name,lang FROM symbols WHERE id=?", (sid,))
                    r2 = cur2.fetchone()
                    fq = r2[0] if r2 else None
                finally:
                    cur2.close()
            out.append({"callee_symbol_id": sid, "callee_key": ckey, "fqname": fq, "count": int(freq)})
        return out
    finally:
        cur.close()


def query_find_references(conn: sqlite3.Connection, symbol_id: Optional[int], symbol_key: Optional[str], kind: Optional[str], limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        conds = []
        args: List[Any] = []
        if symbol_id is not None:
            conds.append("symbol_id=?")
            args.append(symbol_id)
        if symbol_key:
            conds.append("symbol_key=?")
            args.append(symbol_key)
        if kind:
            conds.append("kind=?")
            args.append(kind)
        where = (" WHERE " + " AND ".join(conds)) if conds else ""
        cur.execute(f"SELECT file_id,start_line,start_col,end_line,end_col FROM references_ {where} LIMIT ?", (*args, limit * 2))
        rows = cur.fetchall()
        items = []
        for file_id, sl, sc, el, ec in rows:
            cur2 = conn.cursor()
            try:
                cur2.execute("SELECT relpath FROM files WHERE id=?", (file_id,))
                r2 = cur2.fetchone()
                path = r2[0] if r2 else None
            finally:
                cur2.close()
            items.append({"anchor": {"path": path, "start_line": sl, "start_col": sc, "end_line": el, "end_col": ec}})
        return items
    finally:
        cur.close()


def query_call_patterns(conn: sqlite3.Connection, callee_key: str, limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT args_shape, COUNT(*) as freq
            FROM calls
            WHERE callee_key=?
            GROUP BY args_shape
            ORDER BY freq DESC
            LIMIT ?
            """,
            (callee_key, limit * 2),
        )
        return [{"args_shape": row[0], "freq": int(row[1])} for row in cur.fetchall()]
    finally:
        cur.close()


def query_endpoints_all(conn: sqlite3.Connection, limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT e.kind, e.method, e.path_or_name, f.relpath, e.source_line, e.framework_hint
            FROM endpoints e JOIN files f ON e.source_file_id=f.id
            ORDER BY e.path_or_name, e.method
            LIMIT ?
            """,
            (limit * 2,),
        )
        rows = cur.fetchall()
        return [
            {"kind": r[0], "method": r[1], "path_or_name": r[2], "source_path": r[3], "source_line": r[4], "framework_hint": r[5]}
            for r in rows
        ]
    finally:
        cur.close()


def query_tests_files(conn: sqlite3.Connection, limit: int) -> List[str]:
    cur = conn.cursor()
    try:
        cur.execute("SELECT relpath FROM files WHERE is_test=1 ORDER BY relpath LIMIT ?", (limit * 10,))
        return [r[0] for r in cur.fetchall()]
    finally:
        cur.close()


def query_dir_stats_all(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute("SELECT dir_path, files, bytes FROM dir_stats ORDER BY dir_path")
        return [{"path": r[0], "files": int(r[1]), "bytes": int(r[2])} for r in cur.fetchall()]
    finally:
        cur.close()

# New helpers for index-first ops

def query_files_all(conn: sqlite3.Connection, limit: int = 100000) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute("SELECT relpath, size FROM files ORDER BY relpath LIMIT ?", (int(limit),))
        return [{"relpath": r[0], "size": int(r[1])} for r in cur.fetchall()]
    finally:
        cur.close()


def query_outlines(conn: sqlite3.Connection, limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT f.relpath, s.name, s.kind, s.start_line
            FROM symbols s JOIN files f ON s.file_id=f.id
            ORDER BY f.relpath, s.start_line
            LIMIT ?
            """,
            (limit * 50,),
        )
        rows = cur.fetchall()
    finally:
        cur.close()
    items: Dict[str, List[Dict[str, Any]]] = {}
    for rel, name, kind, sl in rows:
        items.setdefault(rel, []).append({"name": name, "kind": kind, "anchor": {"path": rel, "start_line": int(sl), "start_col": 0}})
    out = [{"path": rel, "symbols": syms} for rel, syms in items.items()]
    out.sort(key=lambda x: x["path"])
    return out


def query_outline_samples(conn: sqlite3.Connection, per_file: int = 5, max_files: int = 3) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT f.relpath, s.name, s.kind, s.start_line
            FROM symbols s JOIN files f ON s.file_id=f.id
            ORDER BY f.relpath, s.start_line
            LIMIT ?
            """,
            (per_file * max_files * 10,),
        )
        rows = cur.fetchall()
    finally:
        cur.close()
    data: Dict[str, List[Dict[str, Any]]] = {}
    for rel, name, kind, sl in rows:
        if len(data.setdefault(rel, [])) < per_file:
            data[rel].append({"name": name, "kind": kind, "anchor": {"path": rel, "start_line": int(sl), "start_col": 0}})
        if len(data) >= max_files:
            break
    out = [{"path": rel, "symbols": syms} for rel, syms in data.items()]
    out.sort(key=lambda x: x["path"])
    return out


def query_functions_count(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(1) FROM symbols WHERE kind IN ('function','method')")
        r = cur.fetchone()
        return int(r[0] or 0)
    finally:
        cur.close()


def query_search_symbols_paths(conn: sqlite3.Connection, pattern: str, limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    like = f"%{pattern}%"
    try:
        cur.execute(
            """
            SELECT f.relpath, s.start_line
            FROM symbols s JOIN files f ON s.file_id=f.id
            WHERE s.name LIKE ?
            ORDER BY f.relpath, s.start_line
            LIMIT ?
            """,
            (like, limit * 2),
        )
        sym_hits = [
            {"anchor": {"path": r[0], "start_line": int(r[1]), "start_col": 0}}
            for r in cur.fetchall()
        ]
        cur.execute("SELECT relpath FROM files WHERE relpath LIKE ? ORDER BY relpath LIMIT ?", (like, limit * 2))
        path_hits = [{"anchor": {"path": r[0], "start_line": 1, "start_col": 0}} for r in cur.fetchall()]
        items = sym_hits + path_hits
        items.sort(key=lambda x: (x["anchor"]["path"], x["anchor"]["start_line"]))
        return items[: limit * 2]
    finally:
        cur.close()
