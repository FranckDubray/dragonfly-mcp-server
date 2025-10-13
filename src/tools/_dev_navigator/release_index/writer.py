from typing import Dict, List, Optional
import sqlite3


def insert_file(cur: sqlite3.Cursor, relpath: str, size: int, mtime: int, content_hash: str,
                is_binary: int = 0, is_test: int = 0, is_generated: int = 0) -> int:
    cur.execute(
        "INSERT INTO files(relpath, size, mtime, content_hash, is_binary, is_test, is_generated) VALUES (?,?,?,?,?,?,?)",
        (relpath, int(size), int(mtime), content_hash, int(is_binary), int(is_test), int(is_generated))
    )
    return int(cur.lastrowid)


def bulk_insert_symbols(cur: sqlite3.Cursor, file_id: int, symbols: List[Dict]) -> List[int]:
    ids: List[int] = []
    for s in symbols:
        cur.execute(
            """
            INSERT INTO symbols(file_id, name, fqname, symbol_key, kind, lang,
                                 start_line, start_col, end_line, end_col, signature, container_symbol_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                file_id, s.get('name'), s.get('fqname'), s.get('symbol_key'), s.get('kind'), s.get('lang'),
                s.get('anchor', {}).get('start_line'), s.get('anchor', {}).get('start_col'),
                s.get('anchor', {}).get('end_line'), s.get('anchor', {}).get('end_col'),
                s.get('signature'), None
            )
        )
        ids.append(int(cur.lastrowid))
    return ids


def bulk_link_container_symbols(cur: sqlite3.Cursor, file_id: int, symbols: List[Dict], ids: List[int]):
    # Assign container_symbol_id for methods inside classes
    name_to_id = {}
    for s, sid in zip(symbols, ids):
        if s.get('kind') == 'class':
            name_to_id[s.get('name')] = sid
    for s, sid in zip(symbols, ids):
        if s.get('kind') in ('function','method') and s.get('container_kind') == 'class':
            cid = name_to_id.get(s.get('container_name'))
            if cid:
                cur.execute("UPDATE symbols SET container_symbol_id=? WHERE id=?", (cid, sid))


def bulk_insert_calls(cur: sqlite3.Cursor, file_id: int, calls: List[Dict], symbols: List[Dict], ids: List[int]):
    # Map caller name -> id for this file
    func_map = {s.get('name'): sid for s, sid in zip(symbols, ids) if s.get('kind') in ('function','method')}
    for c in calls:
        caller_id = func_map.get(c.get('caller_symbol_name'))
        a = c.get('anchor', {})
        cur.execute(
            """
            INSERT INTO calls(file_id, callee_symbol_id, callee_key, caller_symbol_id,
                              start_line, start_col, args_shape, is_test, snippet)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                file_id, None, c.get('callee_key'), caller_id,
                a.get('start_line'), a.get('start_col'), c.get('args_shape'), int(c.get('is_test', 0)), None
            )
        )
        # Also index as a reference of kind 'call'
        cur.execute(
            "INSERT INTO references_(file_id, symbol_id, symbol_key, kind, start_line, start_col, end_line, end_col, snippet) VALUES (?,?,?,?,?,?,?,?,?)",
            (file_id, None, c.get('callee_key'), 'call', a.get('start_line'), a.get('start_col'), None, None, None)
        )


def bulk_insert_imports(cur: sqlite3.Cursor, file_id: int, imports: List[Dict]):
    for im in imports:
        cur.execute(
            "INSERT INTO imports(from_file_id, to_file_id, to_key, kind, raw) VALUES (?,?,?,?,?)",
            (file_id, None, im.get('to_key'), im.get('kind'), im.get('raw'))
        )
        # Also a reference of kind 'import'
        cur.execute(
            "INSERT INTO references_(file_id, symbol_id, symbol_key, kind, start_line, start_col, end_line, end_col, snippet) VALUES (?,?,?,?,?,?,?,?,?)",
            (file_id, None, im.get('to_key'), 'import', None, None, None, None, None)
        )


def bulk_insert_endpoints(cur: sqlite3.Cursor, file_id: int, endpoints: List[Dict]):
    for e in endpoints:
        a = e.get('source_anchor', {})
        cur.execute(
            "INSERT INTO endpoints(kind, method, path_or_name, source_file_id, source_line, framework_hint) VALUES (?,?,?,?,?,?)",
            (e.get('kind'), e.get('method'), e.get('path_or_name'), file_id, a.get('start_line'), e.get('framework_hint'))
        )


def upsert_dir_stats(cur: sqlite3.Cursor, dir_counters: Dict[str, Dict[str, int]]):
    for d, stats in dir_counters.items():
        cur.execute(
            "INSERT INTO dir_stats(dir_path, files, bytes) VALUES (?,?,?)",
            (d, int(stats.get('files', 0)), int(stats.get('bytes', 0)))
        )
