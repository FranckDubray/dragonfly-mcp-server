# Crash logger: logs complete context snapshots on errors
# Critical for debugging production issues

import sqlite3
import json
import traceback
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def _utcnow_str() -> str:
    """UTC ISO8601 microseconds"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

def _sanitize_context(ctx: Dict[str, Any], max_size: int = 100000) -> str:
    """
    Sanitize and serialize context (mask PII, limit size).
    
    Args:
        ctx: Context dict (worker_ctx or cycle_ctx)
        max_size: Max JSON size in bytes (default: 100KB)
    
    Returns:
        JSON string (sanitized, truncated if needed)
    """
    try:
        # Deep copy to avoid mutating original
        import copy
        sanitized = copy.deepcopy(ctx)
        
        # TODO: Implement PII masking (emails, tokens, passwords)
        # For now: basic serialization with truncation
        
        json_str = json.dumps(sanitized, separators=(',', ':'), ensure_ascii=False, default=str)
        
        # Truncate if too large
        if len(json_str) > max_size:
            truncated = json_str[:max_size]
            # Try to close JSON properly
            if truncated.count('{') > truncated.count('}'):
                truncated += '}'
            if truncated.count('[') > truncated.count(']'):
                truncated += ']'
            json_str = truncated + f'\n... (truncated, original size: {len(json_str)} bytes)'
        
        return json_str
    
    except Exception as e:
        # Fallback: return error message if serialization fails
        return json.dumps({"error": f"Failed to serialize context: {str(e)[:200]}"})


def _format_full_traceback(error: Exception) -> str:
    """
    Format complete Python traceback with all details.
    
    Includes:
    - Full stack trace with file/line/function
    - Exception chain (cause)
    - Local variables at each frame
    
    Args:
        error: Exception object
    
    Returns:
        Formatted traceback string (max 20KB)
    """
    lines = []
    
    # Exception type and message
    lines.append(f"{'='*70}")
    lines.append(f"EXCEPTION: {type(error).__module__}.{type(error).__name__}")
    lines.append(f"MESSAGE: {str(error)}")
    lines.append(f"{'='*70}\n")
    
    # Full traceback with locals
    if error.__traceback__:
        lines.append("TRACEBACK (most recent call last):")
        lines.append("-" * 70)
        
        tb = error.__traceback__
        frame_num = 0
        
        while tb:
            frame = tb.tb_frame
            lineno = tb.tb_lineno
            filename = frame.f_code.co_filename
            func_name = frame.f_code.co_name
            
            # Frame header
            lines.append(f"\nFrame {frame_num}: {func_name}()")
            lines.append(f"  File: {filename}:{lineno}")
            
            # Try to get source line
            try:
                import linecache
                line = linecache.getline(filename, lineno).strip()
                if line:
                    lines.append(f"  Code: {line}")
            except:
                pass
            
            # Local variables (sanitized)
            lines.append("  Locals:")
            try:
                for var_name, var_value in frame.f_locals.items():
                    # Skip large objects
                    if var_name.startswith('_'):
                        continue
                    
                    try:
                        # Try to repr, fallback to type
                        var_repr = repr(var_value)
                        if len(var_repr) > 200:
                            var_repr = f"{type(var_value).__name__} (size: {len(str(var_value))} chars)"
                        lines.append(f"    {var_name} = {var_repr}")
                    except:
                        lines.append(f"    {var_name} = <repr failed>")
            except:
                lines.append("    <locals unavailable>")
            
            tb = tb.tb_next
            frame_num += 1
        
        lines.append("-" * 70)
    
    # Exception chain (cause)
    if error.__cause__:
        lines.append("\n" + "="*70)
        lines.append("CAUSED BY:")
        lines.append("="*70)
        lines.append(str(error.__cause__))
        lines.append("\n" + ''.join(traceback.format_tb(error.__cause__.__traceback__)))
    
    # Exception context (during handling)
    if error.__context__ and error.__context__ is not error.__cause__:
        lines.append("\n" + "="*70)
        lines.append("DURING HANDLING OF:")
        lines.append("="*70)
        lines.append(str(error.__context__))
        lines.append("\n" + ''.join(traceback.format_tb(error.__context__.__traceback__)))
    
    # Join and truncate
    full_trace = '\n'.join(lines)
    
    # Limit to 20KB
    if len(full_trace) > 20000:
        full_trace = full_trace[:20000] + f"\n... (truncated, original size: {len(full_trace)} bytes)"
    
    return full_trace


def log_crash(
    db_path: str,
    worker: str,
    cycle_id: str,
    node: str,
    error: Exception,
    worker_ctx: Dict[str, Any],
    cycle_ctx: Dict[str, Any]
) -> None:
    """
    Log a crash with complete context snapshot.
    
    Args:
        db_path: SQLite DB path
        worker: Worker name
        cycle_id: Cycle ID
        node: Node name where crash occurred
        error: Exception object
        worker_ctx: Worker context (read-only constants)
        cycle_ctx: Cycle context (current state)
    
    Side-effects:
        Inserts row in crash_logs table with full context dumps
    """
    crashed_at = _utcnow_str()
    error_message = str(error)[:2000]  # Truncate to 2KB
    error_type = f"{type(error).__module__}.{type(error).__name__}"
    error_code = getattr(error, 'code', None)
    
    # Get FULL stack trace with locals
    stack_trace = _format_full_traceback(error)
    
    # Serialize contexts (with sanitization)
    worker_ctx_json = _sanitize_context(worker_ctx, max_size=50000)  # 50KB max
    cycle_ctx_json = _sanitize_context(cycle_ctx, max_size=100000)  # 100KB max
    
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            INSERT INTO crash_logs (
                worker, cycle_id, node, crashed_at, error_message,
                error_type, error_code, worker_ctx_json, cycle_ctx_json, stack_trace
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            worker, cycle_id, node, crashed_at, error_message,
            error_type, error_code, worker_ctx_json, cycle_ctx_json, stack_trace
        ))
        conn.commit()
    finally:
        conn.close()


def get_recent_crashes(db_path: str, worker: str, limit: int = 10) -> list:
    """
    Get recent crash logs for a worker.
    
    Args:
        db_path: SQLite DB path
        worker: Worker name
        limit: Max number of crashes to return
    
    Returns:
        List of crash dicts (most recent first)
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("""
            SELECT id, worker, cycle_id, node, crashed_at, error_message,
                   error_type, error_code, worker_ctx_json, cycle_ctx_json, stack_trace
            FROM crash_logs
            WHERE worker = ?
            ORDER BY crashed_at DESC
            LIMIT ?
        """, (worker, limit))
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def print_crash_report(crash: dict) -> None:
    """
    Pretty-print a crash report for debugging.
    
    Args:
        crash: Crash dict from get_recent_crashes()
    """
    print("\n" + "="*80)
    print(f"CRASH REPORT #{crash['id']}")
    print("="*80)
    print(f"Worker:    {crash['worker']}")
    print(f"Cycle:     {crash['cycle_id']}")
    print(f"Node:      {crash['node']}")
    print(f"Time:      {crash['crashed_at']}")
    print(f"Error:     {crash['error_type']}")
    print(f"Message:   {crash['error_message']}")
    if crash['error_code']:
        print(f"Code:      {crash['error_code']}")
    print("\n" + "-"*80)
    print("STACK TRACE:")
    print("-"*80)
    print(crash['stack_trace'])
    print("\n" + "-"*80)
    print("CYCLE CONTEXT (preview):")
    print("-"*80)
    try:
        ctx = json.loads(crash['cycle_ctx_json'])
        print(json.dumps(ctx, indent=2)[:1000] + "\n... (truncated)")
    except:
        print(crash['cycle_ctx_json'][:1000])
    print("="*80 + "\n")
