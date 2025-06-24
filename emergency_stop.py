
#!/usr/bin/env python3
"""
EMERGENCY STOP UTILITY
Use this to immediately halt all mainnet operations
"""

import os
import sys
import time
import json

EMERGENCY_STOP_FILE = 'EMERGENCY_STOP_ACTIVE.flag'
EMERGENCY_LOG_FILE = 'emergency_stop_log.json'

def log_emergency_action(action, reason="Manual trigger"):
    """Log emergency stop actions with timestamp"""
    log_entry = {
        'timestamp': time.time(),
        'action': action,
        'reason': reason,
        'datetime': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }
    
    # Append to log file
    if os.path.exists(EMERGENCY_LOG_FILE):
        with open(EMERGENCY_LOG_FILE, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(EMERGENCY_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def emergency_stop(reason="Manual trigger via emergency_stop.py"):
    """Trigger immediate emergency stop"""
    
    with open(EMERGENCY_STOP_FILE, 'w') as f:
        f.write(f"EMERGENCY STOP ACTIVE\n")
        f.write(f"Reason: {reason}\n")
        f.write(f"Timestamp: {time.time()}\n")
        f.write(f"DateTime: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
    
    log_emergency_action("EMERGENCY_STOP_ACTIVATED", reason)
    
    print("🚨 EMERGENCY STOP ACTIVATED!")
    print("🛑 All agent operations will halt immediately")
    print(f"📁 Emergency stop file created: {EMERGENCY_STOP_FILE}")
    print(f"📋 Reason: {reason}")
    print("\n🔧 To resume operations:")
    print("1. Investigate the issue")
    print("2. Run: python emergency_stop.py clear")
    print("3. Restart the agent")

def clear_emergency_stop():
    """Clear emergency stop"""
    
    if os.path.exists(EMERGENCY_STOP_FILE):
        os.remove(EMERGENCY_STOP_FILE)
        log_emergency_action("EMERGENCY_STOP_CLEARED", "Manual clear")
        print("✅ Emergency stop cleared")
        print("🔄 You can now restart the agent")
    else:
        print("ℹ️ No emergency stop file found")

def check_emergency_status():
    """Check if emergency stop is currently active"""
    if os.path.exists(EMERGENCY_STOP_FILE):
        print("🚨 EMERGENCY STOP IS ACTIVE")
        with open(EMERGENCY_STOP_FILE, 'r') as f:
            content = f.read()
            print(content)
        return True
    else:
        print("✅ No emergency stop active")
        return False

def get_emergency_logs():
    """Get recent emergency stop logs"""
    if os.path.exists(EMERGENCY_LOG_FILE):
        with open(EMERGENCY_LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        print("📋 Recent Emergency Stop Actions:")
        for log in logs[-5:]:  # Show last 5 actions
            print(f"  {log['datetime']}: {log['action']} - {log['reason']}")
    else:
        print("ℹ️ No emergency stop logs found")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clear':
            clear_emergency_stop()
        elif sys.argv[1] == 'status':
            check_emergency_status()
        elif sys.argv[1] == 'logs':
            get_emergency_logs()
        else:
            emergency_stop(f"Manual trigger: {' '.join(sys.argv[1:])}")
    else:
        emergency_stop()
