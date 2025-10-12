from __future__ import annotations
"""
SSE parsing utilities for LLM streaming responses
"""
import os
import logging

LOG = logging.getLogger(__name__)


def flags():
    """Parse environment flags for streaming debug/dump"""
    trace = os.getenv("LLM_STREAM_TRACE", "").strip().lower() in ("1", "true", "yes", "on", "debug")
    dump_mode = os.getenv("LLM_STREAM_DUMP", "").strip().lower()
    dump = dump_mode in ("1", "true", "yes", "on", "debug", "all")
    if dump_mode == "all":
        dump_max = 10000
    else:
        try:
            dump_max = int(os.getenv("LLM_STREAM_DUMP_MAX", "50"))
        except Exception:
            dump_max = 50
    incl_choices = os.getenv("LLM_STREAM_INCLUDE_CHOICES", "").strip().lower() in ("1", "true", "yes", "on", "debug")
    return trace, dump, dump_max, incl_choices


def extract_data_str(line: str) -> str | None:
    """Accept both 'data: {...}' and 'data:{...}' and trim space."""
    if not line.startswith('data:'):
        return None
    return line[5:].lstrip()


def stats_init():
    """Initialize SSE statistics dict"""
    return dict(
        total_lines=0,
        parsed_lines=0,
        non_data_lines=0,
        empty_lines=0,
        json_errors=0,
        done=False,
        choices_total=0,
        choices_with_delta=0,
        delta_tool_calls_total=0,
        message_tool_calls_total=0,
        delta_function_call_total=0,
        message_function_call_total=0,
        provider_tool_calls_total=0,
        delta_content_bytes=0,
        ids_seen=[],
        final_seen_finish_reason=None,
    )
