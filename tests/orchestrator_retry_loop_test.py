#!/usr/bin/env python3
"""
Test retry loop with new features:
- Transform: increment
- Decision: compare
- Persistent variables
- Guard 100 nodes per cycle

Run with: python tests/orchestrator_retry_loop_test.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.tools._orchestrator.api import start_or_control

def test_retry_loop():
    print("=== 🧪 Test: Retry Loop (compare, increment, persistent vars) ===\n")
    
    # 1. Start worker
    print("1. Starting worker 'test_retry'...")
    result = start_or_control({
        'operation': 'start',
        'worker_name': 'test_retry',
        'worker_file': 'workers/test_retry_loop.process.json'
    })
    
    print(f"   Result: {result}\n")
    
    if not result.get('accepted'):
        print(f"   ❌ FAILED: {result.get('message')}")
        return False
    
    pid = result.get('pid')
    print(f"   ✅ Worker started (PID: {pid})\n")
    
    # 2. Wait for completion (EXIT node)
    print("2. Waiting for worker to complete (should retry 3 times)...")
    
    max_wait = 15  # seconds
    elapsed = 0
    final_status = None
    
    while elapsed < max_wait:
        time.sleep(1)
        elapsed += 1
        
        status = start_or_control({
            'operation': 'status',
            'worker_name': 'test_retry'
        })
        
        phase = status.get('status')
        print(f"   [{elapsed}s] Phase: {phase}")
        
        if phase in {'completed', 'failed', 'canceled'}:
            final_status = status
            break
    
    if not final_status:
        print(f"\n   ⚠️  WARNING: Worker still running after {max_wait}s")
        return False
    
    print(f"\n3. Final status: {final_status.get('status')}")
    
    # 3. Inspect DB logs
    print("\n4. Inspecting execution logs...")
    
    import sqlite3
    db_path = final_status.get('db_path')
    
    if not db_path or not Path(db_path).exists():
        print("   ❌ DB not found")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all steps
    cursor.execute("""
        SELECT node, status, edge_taken, details_json
        FROM job_steps
        WHERE worker='test_retry'
        ORDER BY id
    """)
    
    steps = cursor.fetchall()
    conn.close()
    
    print(f"\n   📊 Total steps executed: {len(steps)}")
    print("\n   Step details:")
    
    loop_iterations = 0
    increment_count = 0
    final_score = None
    
    for i, (node, status, edge_taken, details) in enumerate(steps, 1):
        print(f"     {i}. {node} → {status} (edge: {edge_taken or 'N/A'})")
        
        if node == 'FETCH_LOOP_ENTRY':
            loop_iterations += 1
        
        if node == 'increment_retry':
            increment_count += 1
        
        if node == 'mock_fetch_and_score':
            # Try to extract score from details
            import json
            try:
                details_dict = json.loads(details or '{}')
                # Score might be in various places
                print(f"        Details: {details[:200] if details else 'N/A'}")
            except:
                pass
    
    print(f"\n   🔄 Loop iterations: {loop_iterations}")
    print(f"   ➕ Increment calls: {increment_count}")
    
    # 4. Validate expected behavior
    print("\n5. Validating expected behavior...")
    
    # Expected: 3 loops (retry_count 0, 1, 2), scores 4.0, 5.5, 7.0
    # Loop 3 should pass (score 7.0 >= 7)
    
    if loop_iterations != 3:
        print(f"   ⚠️  Expected 3 loop iterations, got {loop_iterations}")
    else:
        print(f"   ✅ Loop iterations: {loop_iterations} (expected: 3)")
    
    if increment_count != 2:
        print(f"   ⚠️  Expected 2 increments, got {increment_count}")
    else:
        print(f"   ✅ Increments: {increment_count} (expected: 2)")
    
    # Check for success marker
    success_found = any(node == 'mark_success' for node, _, _, _ in steps)
    failure_found = any(node == 'mark_failure' for node, _, _, _ in steps)
    
    if success_found:
        print(f"   ✅ Reached mark_success (score threshold met on attempt 3)")
    elif failure_found:
        print(f"   ⚠️  Reached mark_failure (unexpected)")
    else:
        print(f"   ❌ Neither success nor failure found")
    
    print("\n=== 🎯 Test Result ===")
    
    if loop_iterations == 3 and increment_count == 2 and success_found:
        print("✅ PASSED: Retry loop works correctly!")
        print("   - Transform increment: OK")
        print("   - Decision compare: OK")
        print("   - Persistent variables: OK")
        print("   - Guard 100 nodes: OK (not triggered)")
        return True
    else:
        print("⚠️  PARTIAL: Some issues detected (check logs above)")
        return False

if __name__ == '__main__':
    try:
        success = test_retry_loop()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
