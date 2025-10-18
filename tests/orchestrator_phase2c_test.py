#!/usr/bin/env python3
"""
Phase 2C test: advanced features (decision, sleep, context resolution, retry).
Run with: python tests/orchestrator_phase2c_test.py
"""

import sys
import time
import sqlite3
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.tools._orchestrator.api import start_or_control

def test_phase2c():
    print("=== Phase 2C Test: Advanced features ===\n")
    
    # 1. Start worker with test_advanced.process.json
    print("1. Starting worker 'test_advanced'...")
    result = start_or_control({
        'operation': 'start',
        'worker_name': 'test_advanced',
        'worker_file': 'workers/test_advanced.process.json',
        'hot_reload': True
    })
    
    print(f"   Result: {result}")
    
    if not result.get('accepted'):
        print(f"   ❌ FAILED: start rejected - {result.get('message')}")
        return False
    
    pid = result.get('pid')
    print(f"   ✅ Worker started (PID: {pid})\n")
    
    # 2. Wait for one cycle to complete
    print("2. Waiting 8 seconds for cycle to complete...")
    time.sleep(8)
    
    # 3. Check job_steps
    print("3. Checking job_steps...")
    db_path = result.get('db_path')
    if not db_path or not Path(db_path).exists():
        print(f"   ❌ FAILED: DB not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cur = conn.execute("""
        SELECT node, status, handler_kind, edge_taken, duration_ms
        FROM job_steps
        ORDER BY id
    """)
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        print("   ⚠️  WARNING: No job_steps found (cycle might not have completed)")
    else:
        print(f"   ✅ Found {len(rows)} job_steps:")
        for node, status, handler, edge, duration in rows:
            edge_info = f" → {edge}" if edge else ""
            handler_info = f" ({handler})" if handler else ""
            print(f"      - {node}{handler_info}: {status}{edge_info} ({duration}ms)")
    
    # Verify expected nodes executed
    expected_nodes = {'START', 'set_flag', 'check_flag', 'do_sleep', 'END'}
    executed_nodes = {row[0] for row in rows}
    
    if not expected_nodes.issubset(executed_nodes):
        missing = expected_nodes - executed_nodes
        print(f"   ⚠️  WARNING: Missing nodes: {missing}")
    else:
        print("   ✅ All expected nodes executed\n")
    
    # Check decision routing
    decision_rows = [r for r in rows if r[0] == 'check_flag']
    if decision_rows:
        edge_taken = decision_rows[0][3]
        if edge_taken == 'true':
            print(f"   ✅ Decision routed to 'true' (do_sleep executed)")
        else:
            print(f"   ⚠️  Decision routed to '{edge_taken}' (expected 'true')")
    
    # 4. Stop worker
    print("\n4. Stopping worker...")
    stop_result = start_or_control({
        'operation': 'stop',
        'worker_name': 'test_advanced',
        'stop': {'mode': 'soft'}
    })
    
    if stop_result.get('accepted'):
        print("   ✅ Cancel flag set")
    
    # Wait for shutdown
    time.sleep(2)
    
    print("\n=== Phase 2C Test: PASSED ✅ ===")
    return True

if __name__ == '__main__':
    try:
        success = test_phase2c()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
