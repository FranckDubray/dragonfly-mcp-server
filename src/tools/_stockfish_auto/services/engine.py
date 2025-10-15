"""
Stockfish UCI engine wrapper (local binary required)
"""
from __future__ import annotations
import os
import shutil
import subprocess
import threading
import time
from typing import Dict, Any, List, Optional


class StockfishNotFound(Exception):
    pass


def find_engine_path() -> str:
    # Env override
    p = os.environ.get('STOCKFISH_PATH')
    if p and os.path.exists(p) and os.access(p, os.X_OK):
        return p
    # Common PATH lookup
    p = shutil.which('stockfish')
    if p:
        return p
    # Homebrew path (Apple Silicon)
    for cand in (
        '/opt/homebrew/bin/stockfish',
        '/usr/local/bin/stockfish',
        '/usr/bin/stockfish',
    ):
        if os.path.exists(cand) and os.access(cand, os.X_OK):
            return cand
    raise StockfishNotFound(
        "Stockfish binary not found. Install it (e.g. brew install stockfish) or set STOCKFISH_PATH."
    )


class Engine:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or find_engine_path()
        self.proc: Optional[subprocess.Popen[str]] = None
        self.lines: List[str] = []
        self._reader: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def start(self) -> None:
        self.proc = subprocess.Popen(
            [self.path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self.cmd('uci')
        self._wait_for('uciok', 3.0)

    def close(self) -> None:
        try:
            if self.proc and self.proc.poll() is None:
                self.cmd('quit')
                self._stop.set()
                self.proc.terminate()
        except Exception:
            pass

    def cmd(self, s: str) -> None:
        if not self.proc or not self.proc.stdin:
            raise RuntimeError('Engine not started')
        self.proc.stdin.write(s + '\n')
        self.proc.stdin.flush()

    def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        out = self.proc.stdout
        while not self._stop.is_set():
            line = out.readline()
            if not line:
                break
            with self._lock:
                self.lines.append(line.rstrip('\n'))

    def _wait_for(self, token: str, timeout: float) -> None:
        deadline = time.time() + timeout
        idx = 0
        while time.time() < deadline:
            with self._lock:
                new = self.lines[idx:]
                idx = len(self.lines)
            for l in new:
                if token in l:
                    return
            time.sleep(0.01)
        raise TimeoutError(f"Timeout waiting for '{token}'")

    def set_options(self, options: Dict[str, Any]) -> None:
        for k, v in options.items():
            if v is None:
                continue
            self.cmd(f"setoption name {k} value {v}")
        self.cmd('isready')
        self._wait_for('readyok', 5.0)

    def new_game(self) -> None:
        self.cmd('ucinewgame')
        self.cmd('isready')
        self._wait_for('readyok', 5.0)

    def position(self, startpos: bool, fen: Optional[str], moves: Optional[List[str]]) -> None:
        if startpos:
            cmd = 'position startpos'
        else:
            if not fen:
                raise ValueError('FEN required when startpos=false')
            cmd = f'position fen {fen}'
        if moves:
            cmd += ' moves ' + ' '.join(moves)
        self.cmd(cmd)
        # Ensure engine ready after setting the position (sync)
        self.cmd('isready')
        self._wait_for('readyok', 5.0)

    def go(self, movetime_ms: Optional[int] = None, depth: Optional[int] = None, searchmoves: Optional[List[str]] = None, timeout_s: float = 180.0, min_floor_s: float = 120.0) -> Dict[str, Any]:
        """
        Run a search. For long blocking analysis use higher floors.
        For quick calls in analyze_game, set min_floor_s=0 and timeout_s small.
        """
        if movetime_ms is None and depth is None:
            movetime_ms = 2000
        go = 'go'
        if searchmoves:
            go += ' searchmoves ' + ' '.join(searchmoves)
        if depth is not None:
            go += f' depth {depth}'
        if movetime_ms is not None:
            go += f' movetime {movetime_ms}'
        # Mark starting index
        with self._lock:
            start_idx = len(self.lines)
        self.cmd(go)
        # Wait for bestmove up to deadline
        dynamic = (movetime_ms or 0)/1000.0 + 5.0
        floor_s = max(0.0, min_floor_s)
        deadline = time.time() + max(timeout_s, floor_s, dynamic)
        bestmove_line = None
        last_info_any: Dict[int, str] = {}
        last_info_complete: Dict[int, str] = {}
        while time.time() < deadline:
            with self._lock:
                new = self.lines[start_idx:]
                start_idx = len(self.lines)
            for l in new:
                if l.startswith('info '):
                    mpv = _parse_multipv(l)
                    if mpv >= 1:
                        last_info_any[mpv] = l
                        if (' score ' in (' ' + l + ' ') or ' score' in l) and (' pv ' in (' ' + l + ' ') or ' pv' in l):
                            last_info_complete[mpv] = l
                elif l.startswith('bestmove'):
                    bestmove_line = l
                    break
            if bestmove_line:
                break
            time.sleep(0.005)
        if not bestmove_line:
            try:
                self.cmd('stop')
            except Exception:
                pass
            grace_deadline = time.time() + 2.0
            while time.time() < grace_deadline and not bestmove_line:
                with self._lock:
                    new = self.lines[start_idx:]
                    start_idx = len(self.lines)
                for l in new:
                    if l.startswith('bestmove'):
                        bestmove_line = l
                        break
                time.sleep(0.005)
        if not bestmove_line:
            raise TimeoutError('Search did not finish before timeout')
        infos_lines: List[str] = []
        for mpv in sorted(set(list(last_info_any.keys()) + list(last_info_complete.keys()))):
            infos_lines.append(last_info_complete.get(mpv) or last_info_any.get(mpv))
        return {
            'bestmove': _parse_bestmove(bestmove_line),
            'infos': [_parse_info(l) for l in infos_lines if l]
        }


def _parse_multipv(info_line: str) -> int:
    parts = info_line.split()
    try:
        i = parts.index('multipv')
        return int(parts[i+1])
    except Exception:
        return 1


def _parse_bestmove(line: str) -> Dict[str, Any]:
    parts = line.split()
    bm = parts[1] if len(parts) > 1 else None
    ponder = parts[3] if len(parts) > 3 and parts[2] == 'ponder' else None
    return {'move': bm, 'ponder': ponder}


def _parse_info(line: str) -> Dict[str, Any]:
    parts = line.split()
    d = {'depth': None, 'seldepth': None, 'multipv': 1, 'score': None, 'nps': None, 'nodes': None, 'time_ms': None, 'pv': []}
    def get_after(tok: str):
        try:
            i = parts.index(tok)
            return parts[i+1]
        except Exception:
            return None
    depth = get_after('depth'); sel = get_after('seldepth'); mpv = get_after('multipv')
    st = get_after('score'); val = None; unit = None
    if st in ('cp', 'mate'):
        try:
            val = int(get_after('cp')) if st == 'cp' else int(get_after('mate'))
            unit = st
        except Exception:
            pass
    nps = get_after('nps'); nodes = get_after('nodes'); t = get_after('time')
    pv = []
    if ' pv ' in (' ' + line + ' '):
        try:
            i = parts.index('pv')
            pv = parts[i+1:]
        except Exception:
            pv = []
    wdl = None
    if ' wdl ' in (' ' + line + ' '):
        try:
            i = parts.index('wdl')
            wdl = [int(parts[i+1]), int(parts[i+2]), int(parts[i+3])]
        except Exception:
            wdl = None
    def to_int(x):
        try:
            return int(x) if x is not None else None
        except Exception:
            return None
    return {
        'depth': to_int(depth),
        'seldepth': to_int(sel),
        'multipv': to_int(mpv) or 1,
        'score': {'type': unit, 'value': val} if unit else None,
        'nps': to_int(nps),
        'nodes': to_int(nodes),
        'time_ms': to_int(t),
        'pv': pv,
        'wdl': wdl,
    }
