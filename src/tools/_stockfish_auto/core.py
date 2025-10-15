"""
Core logic for Stockfish Auto-75 (UCI invocation, local engine required)
"""
import multiprocessing
import io
import time
from typing import Dict, Any, List, Optional, Tuple
from .services.engine import Engine, StockfishNotFound


def _auto_threads(target_percent: int) -> int:
    try:
        cores = multiprocessing.cpu_count()
    except NotImplementedError:
        cores = 1
    threads = max(1, int(cores * target_percent / 100))
    return max(1, threads)


def _auto_hash_mb(target_percent: int) -> int:
    try:
        import psutil  # optional
        total_mb = int(psutil.virtual_memory().total / (1024 * 1024))
    except Exception:
        total_mb = 16384
    hash_mb = int(total_mb * (target_percent / 100.0) * 0.25)
    return max(512, min(8192, hash_mb))


def _quality_movetime_ms(quality: str) -> int:
    return {'fast': 1000, 'balanced': 2000, 'deep': 5000}[quality]


def _mk_options(threads: int, hash_mb: int, multipv: int) -> Dict[str, Any]:
    return {
        'Threads': threads,
        'Hash': hash_mb,
        'MultiPV': multipv,
        'UCI_ShowWDL': True,
        'Use NNUE': True,
    }


def _format_infos(infos: List[Dict[str, Any]], limit: int) -> Dict[str, Any]:
    infos_sorted = sorted(infos, key=lambda x: x.get('multipv', 1))
    total = len(infos_sorted)
    cut = infos_sorted[:limit]
    return {
        'returned_count': len(cut),
        'total_count': total,
        'truncated': total > len(cut),
        'lines': [
            {
                'multipv': i.get('multipv', 1),
                'depth': i.get('depth'),
                'score': i.get('score'),
                'wdl': i.get('wdl'),
                'nps': i.get('nps'),
                'pv': i.get('pv'),
            } for i in cut
        ]
    }


def _score_to_cp(score: Optional[Dict[str, Any]]) -> Optional[int]:
    if not score:
        return None
    st = score.get('type')
    val = score.get('value')
    if st == 'cp':
        return int(val) if isinstance(val, int) else None
    if st == 'mate':
        try:
            m = int(val)
            return 100000 if m > 0 else -100000
        except Exception:
            return None
    return None


def evaluate_position(position: Dict[str, Any], limit: int = 3, quality: str = 'balanced', resource_target_percent: int = 75, searchmoves: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
    t0 = time.time()
    try:
        threads = _auto_threads(resource_target_percent)
        hash_mb = _auto_hash_mb(resource_target_percent)
        options = _mk_options(threads, hash_mb, limit)
        eng = Engine()
        eng.start()
        eng.set_options(options)
        startpos = bool(position.get('startpos', True))
        fen: Optional[str] = position.get('fen')
        moves: Optional[List[str]] = position.get('moves')
        eng.new_game()
        eng.position(startpos=startpos, fen=fen, moves=moves)
        res = eng.go(movetime_ms=_quality_movetime_ms(quality), searchmoves=searchmoves)
        eng.close()
        infos = res.get('infos', [])
        formatted = _format_infos(infos, limit)
        return {
            'engine': {
                'threads': threads,
                'hash_mb': hash_mb,
                'quality': quality,
                'movetime_ms': _quality_movetime_ms(quality),
                'multipv': limit
            },
            'bestmove': res.get('bestmove'),
            'result': formatted,
            'elapsed_ms': int((time.time() - t0) * 1000)
        }
    except StockfishNotFound as e:
        return {
            'error': str(e),
            'hint': 'Install Stockfish locally (e.g. brew install stockfish) or set STOCKFISH_PATH to the binary path.',
            'elapsed_ms': int((time.time() - t0) * 1000)
        }
    except Exception as e:
        return {'error': f'Engine error: {str(e)}', 'elapsed_ms': int((time.time() - t0) * 1000)}


def _eval_position_with_engine(eng: Engine, fen: str, movetime_ms: int, played_uci: Optional[str] = None) -> Tuple[Optional[int], Dict[str, Any]]:
    eng.new_game()
    eng.position(startpos=False, fen=fen, moves=None)
    # Ensure quick return: no min floor, short timeout
    res = eng.go(
        movetime_ms=movetime_ms,
        searchmoves=[played_uci] if played_uci else None,
        timeout_s=(movetime_ms / 1000.0) + 2.0,
        min_floor_s=0.0,
    )
    infos = res.get('infos', [])
    info = None
    for i in infos:
        if i.get('multipv', 1) == 1:
            info = i
            break
    if not info and infos:
        info = infos[0]
    cp = _score_to_cp(info.get('score') if info else None)
    return cp, res


def analyze_game(analyze: Dict[str, Any], quality: str = 'balanced', resource_target_percent: int = 75, **kwargs) -> Dict[str, Any]:
    t0 = time.time()
    pgn = analyze.get('pgn')
    max_moves = int(analyze.get('max_moves', 200))
    blunder_cp = int(analyze.get('blunder_threshold_cp', 150))
    inacc_cp = int(analyze.get('inaccuracy_threshold_cp', 50))
    limit = int(analyze.get('limit', 100))
    budget_s = int(analyze.get('max_time_sec', 30))

    try:
        from chess import pgn as chess_pgn
    except Exception:
        return {
            'error': 'python-chess is required for analyze_game. Please install: pip install python-chess',
            'hint': 'This is only needed for PGN parsing.',
            'elapsed_ms': int((time.time() - t0) * 1000)
        }
    try:
        threads = _auto_threads(resource_target_percent)
        hash_mb = _auto_hash_mb(resource_target_percent)
        options = _mk_options(threads, hash_mb, 1)
        eng = Engine()
        eng.start()
        eng.set_options(options)

        game = chess_pgn.read_game(io.StringIO(pgn))
        if game is None:
            eng.close()
            return {'error': 'Invalid PGN', 'elapsed_ms': int((time.time() - t0) * 1000)}

        board = game.board()
        # Stage A: quick scan all plies with small movetime to find top hotspots
        quick_ms = 200 if quality == 'fast' else 300
        candidates: List[Dict[str, Any]] = []
        ply = 0
        for move in game.mainline_moves():
            if ply >= max_moves:
                break
            # If we are very close to budget, stop scanning
            if (time.time() - t0) >= budget_s * 0.6:  # keep time for deep pass
                break
            fen_before = board.fen()
            uci = move.uci()
            # best eval
            best_cp, _ = _eval_position_with_engine(eng, fen_before, movetime_ms=quick_ms)
            # played eval (approx by eval after move)
            board.push(move)
            fen_after = board.fen()
            played_cp, _ = _eval_position_with_engine(eng, fen_after, movetime_ms=quick_ms)
            board.pop()
            if best_cp is not None and played_cp is not None:
                drop = best_cp - played_cp
                candidates.append({
                    'ply': ply + 1,
                    'fen': fen_before,
                    'uci': uci,
                    'drop_est': drop,
                })
            board.push(move)
            ply += 1
        # Rewind board to start for deep pass
        # Re-parse to clean iterator state
        game = chess_pgn.read_game(io.StringIO(pgn))
        board = game.board()

        # Stage B: deep analyze top-K by estimated drop
        candidates.sort(key=lambda x: x['drop_est'] if x['drop_est'] is not None else -999999, reverse=True)
        K = min(limit, max(1, len(candidates)))
        remaining_s = max(0.0, budget_s - (time.time() - t0))
        deep_ms_each = max(200, int((remaining_s * 1000) / max(1, K * 2)))  # 2 calls per hotspot (best + played)

        returned_events: List[Dict[str, Any]] = []
        counted = 0
        for c in candidates[:K]:
            if (time.time() - t0) >= budget_s:
                break
            fen_before = c['fen']
            # deep best
            best_cp, best_res = _eval_position_with_engine(eng, fen_before, movetime_ms=deep_ms_each)
            # find SAN for reporting
            # Recompute move SAN by playing moves up to ply (lightweight)
            # For speed, we skip SAN resolution; keep UCI only in deep pass.
            played_cp, played_res = _eval_position_with_engine(eng, fen_before, movetime_ms=deep_ms_each, played_uci=c['uci'])
            classification = None
            drop = None
            if best_cp is not None and played_cp is not None:
                drop = best_cp - played_cp
                if drop >= blunder_cp:
                    classification = 'blunder'
                elif drop >= inacc_cp:
                    classification = 'inaccuracy'
            if classification:
                returned_events.append({
                    'ply': c['ply'],
                    'played': {
                        'uci': c['uci'],
                        'eval_cp': played_cp,
                        'pv': played_res.get('infos', [{}])[0].get('pv') if played_res.get('infos') else []
                    },
                    'best': {
                        'eval_cp': best_cp,
                        'bestmove': best_res.get('bestmove'),
                        'pv': best_res.get('infos', [{}])[0].get('pv') if best_res.get('infos') else []
                    },
                    'drop_cp': drop,
                    'classification': classification,
                })
                counted += 1
            if counted >= limit:
                break

        eng.close()
        return {
            'engine': {
                'threads': threads,
                'hash_mb': hash_mb,
                'quality': quality,
                'movetime_ms': deep_ms_each,
                'multipv': 1
            },
            'result': {
                'annotated_events_returned': len(returned_events),
                'total_events': len(returned_events),
                'truncated': False,
                'events': returned_events,
                'coverage': {
                    'quick_scanned_plies': ply,
                    'candidates_considered': len(candidates),
                    'deep_ms_each': deep_ms_each
                }
            },
            'elapsed_ms': int((time.time() - t0) * 1000)
        }
    except StockfishNotFound as e:
        return {
            'error': str(e),
            'hint': 'Install Stockfish locally (e.g. brew install stockfish) or set STOCKFISH_PATH to the binary path.',
            'elapsed_ms': int((time.time() - t0) * 1000)
        }
    except Exception as e:
        return {'error': f'Engine error: {str(e)}', 'elapsed_ms': int((time.time() - t0) * 1000)}
