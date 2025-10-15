"""
Per-move annotation analysis for Stockfish Auto-75
"""
import io
from typing import Dict, Any, List, Optional, Tuple
from .services.engine import Engine, StockfishNotFound
from .core import _auto_threads, _auto_hash_mb, _quality_movetime_ms, _mk_options, _format_infos


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


def _eval_position_with_engine(eng: Engine, fen: str, movetime_ms: int, played_uci: Optional[str] = None) -> Tuple[Optional[int], Dict[str, Any]]:
    eng.new_game()
    eng.position(startpos=False, fen=fen, moves=None)
    res = eng.go(movetime_ms=movetime_ms, searchmoves=[played_uci] if played_uci else None)
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
    pgn = analyze.get('pgn')
    max_moves = int(analyze.get('max_moves', 200))
    blunder_cp = int(analyze.get('blunder_threshold_cp', 150))
    inacc_cp = int(analyze.get('inaccuracy_threshold_cp', 50))
    limit = int(analyze.get('limit', 100))

    try:
        from chess import pgn as chess_pgn, Board
    except Exception:
        return {
            'error': 'python-chess is required for analyze_game. Please install: pip install python-chess',
            'hint': 'This is only needed for PGN parsing.'
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
            return {'error': 'Invalid PGN'}

        board = game.board()
        total_events = 0
        returned_events: List[Dict[str, Any]] = []
        movetime = _quality_movetime_ms(quality)

        ply = 0
        for move in game.mainline_moves():
            if ply >= max_moves:
                break
            fen_before = board.fen()
            uci = move.uci()
            san = board.san(move)
            best_cp, best_res = _eval_position_with_engine(eng, fen_before, movetime_ms=movetime)
            played_cp, played_res = _eval_position_with_engine(eng, fen_before, movetime_ms=movetime, played_uci=uci)

            classification = None
            drop = None
            if best_cp is not None and played_cp is not None:
                drop = best_cp - played_cp
                if drop >= blunder_cp:
                    classification = 'blunder'
                elif drop >= inacc_cp:
                    classification = 'inaccuracy'

            if classification:
                total_events += 1
                if len(returned_events) < limit:
                    returned_events.append({
                        'ply': ply + 1,
                        'move_number': (ply // 2) + 1,
                        'side': 'w' if board.turn else 'b',
                        'played': {
                            'uci': uci,
                            'san': san,
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
            board.push(move)
            ply += 1

        eng.close()
        truncated = total_events > len(returned_events)
        return {
            'engine': {
                'threads': threads,
                'hash_mb': hash_mb,
                'quality': quality,
                'movetime_ms': movetime,
                'multipv': 1
            },
            'result': {
                'annotated_events_returned': len(returned_events),
                'total_events': total_events,
                'truncated': truncated,
                'events': returned_events
            }
        }
    except StockfishNotFound as e:
        return {
            'error': str(e),
            'hint': 'Install Stockfish locally (e.g. brew install stockfish) or set STOCKFISH_PATH to the binary path.'
        }
    except Exception as e:
        return {'error': f'Engine error: {str(e)}'}
