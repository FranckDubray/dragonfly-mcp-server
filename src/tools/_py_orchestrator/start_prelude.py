
from __future__ import annotations
from typing import Dict, Any

from .db import set_state_kv

TRANSIENT_KEYS = [
    'cancel', 'last_error', 'py.last_summary', 'py.last_call', 'py.last_result_preview',
    'debug.enabled', 'debug.mode', 'debug.pause_request', 'debug.until', 'debug.breakpoints', 'debug.command',
    'debug.paused_at', 'debug.next_node', 'debug.cycle_id', 'debug.last_step', 'debug.ctx_diff',
    'debug.watches', 'debug.watches_values', 'debug.response_id', 'debug.req_id', 'debug.executing_node',
    'debug.previous_node',
    'debug.step_trace', 'debug.trace',
    'py.graph_warnings', 'py.graph_errors'
]


def reset_transients(db_path: str, worker_name: str) -> None:
    for key in TRANSIENT_KEYS:
        try:
            set_state_kv(db_path, worker_name, key, '')
        except Exception:
            pass


def reset_llm_usage(db_path: str, worker_name: str) -> None:
    try:
        set_state_kv(db_path, worker_name, 'usage.llm.total_tokens', '0')
        set_state_kv(db_path, worker_name, 'usage.llm.input_tokens', '0')
        set_state_kv(db_path, worker_name, 'usage.llm.output_tokens', '0')
        set_state_kv(db_path, worker_name, 'usage.llm.by_model', '{}')
    except Exception:
        pass
