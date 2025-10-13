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
