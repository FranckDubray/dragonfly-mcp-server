"""
Validation for Stockfish Auto-75
"""
from typing import Dict, Any, List


def _validate_searchmoves(val: Any) -> List[str]:
    if val is None:
        return []
    if not isinstance(val, list):
        raise ValueError("'searchmoves' must be an array of UCI moves")
    for m in val:
        if not isinstance(m, str) or len(m) < 4:
            raise ValueError("each 'searchmoves' entry must be a UCI move string")
    return val


def validate_params(operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    p = dict(params)
    if operation == 'evaluate_position':
        pos = p.get('position', {})
        if not isinstance(pos, dict):
            raise ValueError("'position' must be an object")
        fen = pos.get('fen')
        startpos = pos.get('startpos', True)
        # Enforce mutual exclusivity: if fen is provided, startpos must be False
        if fen:
            if startpos:
                raise ValueError("'startpos' must be false when 'fen' is provided")
            pos['startpos'] = False
        elif not startpos:
            raise ValueError("Provide 'fen' or set 'startpos'=true")
        p['position'] = pos
        limit = int(p.get('limit', 3))
        if limit < 1 or limit > 5:
            raise ValueError("'limit' must be 1..5")
        p['limit'] = limit
        quality = p.get('quality', 'balanced')
        if quality not in {'fast', 'balanced', 'deep'}:
            raise ValueError("'quality' must be one of: fast, balanced, deep")
        rtp = int(p.get('resource_target_percent', 75))
        if rtp < 10 or rtp > 100:
            raise ValueError("'resource_target_percent' must be 10..100")
        p['resource_target_percent'] = rtp
        # optional searchmoves
        sm = _validate_searchmoves(p.get('searchmoves'))
        if sm:
            p['searchmoves'] = sm
    elif operation == 'analyze_game':
        analyze = p.get('analyze', {})
        if not isinstance(analyze, dict) or not analyze.get('pgn'):
            raise ValueError("'analyze.pgn' is required")
        for key, mn, mx, d in [
            ('max_moves', 1, 5000, 200),
            ('blunder_threshold_cp', 50, 1000, 150),
            ('inaccuracy_threshold_cp', 20, 300, 50),
            ('limit', 1, 200, 100),
            ('max_time_sec', 1, 600, 30),
        ]:
            v = int(analyze.get(key, d))
            if v < mn or v > mx:
                raise ValueError(f"'analyze.{key}' must be {mn}..{mx}")
            analyze[key] = v
        p['analyze'] = analyze
        rtp = int(p.get('resource_target_percent', 75))
        if rtp < 10 or rtp > 100:
            raise ValueError("'resource_target_percent' must be 10..100")
        p['resource_target_percent'] = rtp
        quality = p.get('quality', 'balanced')
        if quality not in {'fast', 'balanced', 'deep'}:
            raise ValueError("'quality' must be one of: fast, balanced, deep")
    else:
        raise ValueError(f"Unknown operation: {operation}")
    return p
