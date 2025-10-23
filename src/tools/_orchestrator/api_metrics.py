# Metrics computation helpers (<7KB)

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict


def _safe_int(x):
    try:
        return int(x)
    except Exception:
        try:
            return int(float(x))
        except Exception:
            return 0


def _accumulate_usage(tot: Dict[str, int], usage: Dict[str, Any]):
    """Accumulate usage fields returned by call_llm into a total dict."""
    if not isinstance(usage, dict):
        return
    tot['prompt_tokens'] = tot.get('prompt_tokens', 0) + _safe_int(usage.get('prompt_tokens', 0))
    tot['completion_tokens'] = tot.get('completion_tokens', 0) + _safe_int(usage.get('completion_tokens', 0))
    tot['total_tokens'] = tot.get('total_tokens', 0) + _safe_int(usage.get('total_tokens', 0))
    # Costs
    tot['input_token_cost'] = tot.get('input_token_cost', 0) + _safe_int(usage.get('input_token_cost', 0))
    tot['output_token_cost'] = tot.get('output_token_cost', 0) + _safe_int(usage.get('output_token_cost', 0))
    tot['total_token_cost'] = tot.get('total_token_cost', 0) + _safe_int(usage.get('total_token_cost', 0))
    # Prices (keep last non-null seen)
    if usage.get('input_token_price') is not None:
        tot['input_token_price'] = usage.get('input_token_price')
    if usage.get('output_token_price') is not None:
        tot['output_token_price'] = usage.get('output_token_price')
    # Count calls
    tot['calls'] = tot.get('calls', 0) + 1


def compute_metrics_window(db_path: str, worker: str, minutes: int = 60) -> Dict[str, Any]:
    """Compute compact metrics over the last N minutes from job_steps.
    Includes aggregated LLM usage ('token_llm' dict) and 'llm_tokens' shortcut.
    """
    if minutes <= 0:
        minutes = 60
    cutoff_dt = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    cutoff = cutoff_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    nodes_executed = 0
    sum_duration = 0
    count_duration = 0
    errors = {"io": 0, "validation": 0, "permission": 0, "timeout": 0}
    retries_attempts = 0
    nodes_with_retries = set()
    token_llm: Dict[str, Any] = {}

    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            cur = conn.execute(
                """
                SELECT node, status, duration_ms, details_json
                FROM job_steps
                WHERE worker=? AND started_at >= ?
                """,
                (worker, cutoff)
            )
            for node, status, duration_ms, details_json in cur:
                nodes_executed += 1
                if isinstance(duration_ms, int):
                    sum_duration += duration_ms
                    count_duration += 1
                # Parse details lightly
                dj = None
                if details_json:
                    try:
                        dj = json.loads(details_json)
                    except Exception:
                        dj = None
                # Errors by category
                if status == 'failed' and isinstance(dj, dict):
                    err = dj.get('error') or {}
                    cat = err.get('category')
                    if cat in errors:
                        errors[cat] += 1
                # Retries: count _retry_ rows and attempts fields
                if '_retry_' in node:
                    retries_attempts += 1
                    parent = node.split('_retry_')[0]
                    nodes_with_retries.add(parent)
                elif isinstance(dj, dict) and isinstance(dj.get('attempts'), int) and dj['attempts'] > 1:
                    retries_attempts += max(0, dj['attempts'] - 1)
                    nodes_with_retries.add(node)
                # LLM usage aggregation
                if isinstance(dj, dict) and isinstance(dj.get('usage'), dict):
                    _accumulate_usage(token_llm, dj['usage'])
        finally:
            conn.close()
    except Exception:
        # On error, return minimal metrics instead of failing status
        return {
            "window": "0m",
            "nodes_executed": 0,
            "avg_duration_ms": 0,
            "errors": {"io": 0, "validation": 0, "permission": 0, "timeout": 0},
            "retries": {"attempts": 0, "nodes_with_retries": 0},
            "llm_tokens": 0,
            "token_llm": {}
        }

    avg_duration = int(sum_duration / count_duration) if count_duration > 0 else 0
    label = f"{minutes//60}h" if minutes % 60 == 0 else f"{minutes}m"
    llm_tokens_total = int(token_llm.get('total_tokens', 0)) if token_llm else 0
    return {
        "window": label,
        "nodes_executed": nodes_executed,
        "avg_duration_ms": avg_duration,
        "errors": errors,
        "retries": {"attempts": retries_attempts, "nodes_with_retries": len(nodes_with_retries)},
        "llm_tokens": llm_tokens_total,
        "token_llm": token_llm or {}
    }


def parse_metrics_window_minutes(metrics_param: Dict[str, Any]) -> int:
    """Parse a compact window parameter (e.g., '5m', '15m', '1h') into minutes. Defaults to 60."""
    if not isinstance(metrics_param, dict):
        return 60
    win = metrics_param.get('window')
    if win is None:
        return 60
    try:
        if isinstance(win, (int, float)):
            return max(1, int(win))
        s = str(win).strip().lower()
        if s.endswith('m'):
            return max(1, int(s[:-1]))
        if s.endswith('h'):
            h = int(s[:-1])
            return max(1, h * 60)
        return max(1, int(s))
    except Exception:
        return 60
