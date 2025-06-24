
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
    """Trigger immediate emergency stop with comprehensive logging"""
    
    emergency_details = {
        'reason': reason,
        'timestamp': time.time(),
        'datetime': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'triggered_by': 'manual',
        'system_state': capture_system_state()
    }
    
    with open(EMERGENCY_STOP_FILE, 'w') as f:
        f.write(f"EMERGENCY STOP ACTIVE\n")
        f.write(f"Reason: {reason}\n")
        f.write(f"Timestamp: {time.time()}\n")
        f.write(f"DateTime: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
        f.write(f"System State: {json.dumps(emergency_details['system_state'], indent=2)}\n")
    
    log_emergency_action("EMERGENCY_STOP_ACTIVATED", reason)
    
    # Save detailed emergency report
    with open(f"emergency_report_{int(time.time())}.json", 'w') as f:
        json.dump(emergency_details, f, indent=2)
    
    print("🚨 EMERGENCY STOP ACTIVATED!")
    print("🛑 All agent operations will halt immediately")
    print(f"📁 Emergency stop file created: {EMERGENCY_STOP_FILE}")
    print(f"📋 Reason: {reason}")
    print(f"📊 System state captured in emergency report")
    print("\n🔧 To resume operations:")
    print("1. Investigate the issue thoroughly")
    print("2. Review emergency report")
    print("3. Run: python emergency_stop.py clear")
    print("4. Restart the agent")

def capture_system_state():
    """Capture current system state for emergency analysis"""
    try:
        return {
            'timestamp': time.time(),
            'active_processes': True,  # Could implement process checking
            'recent_performance': get_recent_performance_summary(),
            'wallet_status': 'unknown',  # Could implement wallet checking
            'api_status': 'unknown'      # Could implement API checking
        }
    except Exception as e:
        return {'error': str(e)}

def get_recent_performance_summary():
    """Get summary of recent performance for emergency analysis"""
    try:
        if os.path.exists('performance_log.json'):
            recent_data = []
            with open('performance_log.json', 'r') as f:
                for line in f.readlines()[-10:]:  # Last 10 entries
                    try:
                        recent_data.append(json.loads(line))
                    except:
                        continue
            
            if recent_data:
                avg_performance = sum(p['performance_metric'] for p in recent_data) / len(recent_data)
                return {
                    'avg_recent_performance': avg_performance,
                    'recent_entries': len(recent_data),
                    'last_timestamp': recent_data[-1].get('timestamp', 0)
                }
        
        return {'status': 'no_recent_data'}
    except Exception as e:
        return {'error': str(e)}

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
