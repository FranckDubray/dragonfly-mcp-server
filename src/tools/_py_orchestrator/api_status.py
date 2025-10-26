













from .status.status_core import build_status as _build_status


def status(params: dict) -> dict:
    out = _build_status(params)
    try:
        m = out.get('metrics') or {}
        # llm_usage peut être soit top-level, soit imbriqué dans metrics
        llm = out.get('llm_usage') or (m.get('llm_usage') if isinstance(m, dict) else {}) or {}
        if isinstance(m, dict) and isinstance(llm, dict) and llm:
            # Refléter llm_usage dans metrics pour cohérence UI
            m['llm_tokens'] = {
                'total': llm.get('total_tokens', 0),
                'input': llm.get('input_tokens', 0),
                'output': llm.get('output_tokens', 0),
            }
            m['token_llm'] = llm.get('by_model') or {}
            out['metrics'] = m
    except Exception:
        pass
    return out

 
 
 
 
 
 
 
 
 
 
 
 
