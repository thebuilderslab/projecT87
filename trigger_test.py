
#!/usr/bin/env python3
"""
Manual Trigger Test - Allows testing autonomous functions without waiting for $12 growth
"""

import os
import time

def create_trigger_test():
    """Create trigger test flag to force autonomous sequence"""
    trigger_file = 'trigger_test.flag'
    
    with open(trigger_file, 'w') as f:
        f.write(f"MANUAL TRIGGER TEST ACTIVATED\n")
        f.write(f"Timestamp: {time.time()}\n")
        f.write(f"DateTime: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Purpose: Test autonomous borrow sequence\n")
    
    print(f"✅ Trigger test flag created: {trigger_file}")
    print(f"🚀 Next agent cycle will execute autonomous sequence")
    print(f"💡 To remove: python -c \"import os; os.remove('{trigger_file}')\"")

def remove_trigger_test():
    """Remove trigger test flag"""
    trigger_file = 'trigger_test.flag'
    
    if os.path.exists(trigger_file):
        os.remove(trigger_file)
        print(f"✅ Trigger test flag removed")
    else:
        print(f"ℹ️ No trigger test flag found")

def check_trigger_status():
    """Check current trigger status"""
    trigger_file = 'trigger_test.flag'
    baseline_file = 'agent_baseline.json'
    
    print(f"🔍 TRIGGER STATUS CHECK:")
    print(f"   Manual trigger active: {os.path.exists(trigger_file)}")
    
    if os.path.exists(baseline_file):
        import json
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
            baseline_collateral = baseline_data.get('last_collateral_value_usd', 0)
            print(f"   Current baseline: ${baseline_collateral:.2f}")
            print(f"   Target for natural trigger: ${baseline_collateral + 12:.2f}")
    
    print(f"   Commands:")
    print(f"     Activate test: python trigger_test.py create")
    print(f"     Remove test: python trigger_test.py remove")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'create':
            create_trigger_test()
        elif command == 'remove':
            remove_trigger_test()
        elif command == 'status':
            check_trigger_status()
        else:
            print(f"Usage: python trigger_test.py [create|remove|status]")
    else:
        check_trigger_status()
