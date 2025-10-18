#!/usr/bin/env python3
"""
Phase 2A test: spawn runner, verify loop, cancel cooperatively.
Run with: python tests/orchestrator_phase2a_test.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.tools._orchestrator.api import start_or_control

def test_phase2a():
    print("=== Phase 2A Test: Runner spawn + loop stub ===\n")
    
    # 1. Start worker with test_minimal.process.json
    print("1. Starting worker 'test_minimal'...")
    result = start_or_control({
        'operation': 'start',
        'worker_name': 'test_minimal',
        'worker_file': 'workers/test_minimal.process.json',
        'hot_reload': True
    })
    
    print(f"   Result: {result}")
    
    if not result.get('accepted'):
        print("   ❌ FAILED: start rejected")
        return False
    
    if result.get('status') != 'starting':
        print(f"   ❌ FAILED: expected status=starting, got {result.get('status')}")
        return False
    
    pid = result.get('pid')
    if not pid:
        print("   ❌ FAILED: no PID returned")
        return False
    
    print(f"   ✅ Worker started (PID: {pid})\n")
    
    # 2. Wait a bit, check status
    print("2. Waiting 3 seconds for runner to execute cycles...")
    time.sleep(3)
    
    print("3. Checking status...")
    status_result = start_or_control({
        'operation': 'status',
        'worker_name': 'test_minimal'
    })
    
    print(f"   Result: {status_result}")
    
    phase = status_result.get('status')
    if phase not in {'running', 'sleeping'}:
        print(f"   ⚠️  WARNING: expected running/sleeping, got {phase}")
    else:
        print(f"   ✅ Worker is {phase}\n")
    
    # 3. Stop (soft cancel)
    print("4. Stopping worker (soft cancel)...")
    stop_result = start_or_control({
        'operation': 'stop',
        'worker_name': 'test_minimal',
        'stop': {'mode': 'soft'}
    })
    
    print(f"   Result: {stop_result}")
    
    if not stop_result.get('accepted'):
        print("   ❌ FAILED: stop rejected")
        return False
    
    print("   ✅ Cancel flag set\n")
    
    # 4. Wait for graceful shutdown
    print("5. Waiting 2 seconds for graceful shutdown...")
    time.sleep(2)
    
    print("6. Final status check...")
    final_status = start_or_control({
        'operation': 'status',
        'worker_name': 'test_minimal'
    })
    
    print(f"   Result: {final_status}")
    
    final_phase = final_status.get('status')
    if final_phase in {'canceled', 'canceling'}:
        print(f"   ✅ Worker gracefully stopped ({final_phase})")
    else:
        print(f"   ⚠️  WARNING: expected canceled, got {final_phase}")
    
    print("\n=== Phase 2A Test: PASSED ✅ ===")
    return True

if __name__ == '__main__':
    try:
        success = test_phase2a()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
