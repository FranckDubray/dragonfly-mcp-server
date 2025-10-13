from typing import Dict, Optional

def make_anchor(path: str, start_line: int, start_col: int = 0,
                end_line: Optional[int] = None, end_col: Optional[int] = None) -> Dict:
    a = {
        "path": path,
        "start_line": int(start_line),
        "start_col": int(start_col),
    }
    if end_line is not None:
        a["end_line"] = int(end_line)
    if end_col is not None:
        a["end_col"] = int(end_col)
    return a
