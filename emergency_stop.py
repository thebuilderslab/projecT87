
#!/usr/bin/env python3
"""
EMERGENCY STOP UTILITY
Use this to immediately halt all mainnet operations
"""

import os
import sys

def emergency_stop():
    """Trigger immediate emergency stop"""
    emergency_file = 'EMERGENCY_STOP.txt'
    
    with open(emergency_file, 'w') as f:
        f.write(f"EMERGENCY STOP TRIGGERED\n")
        f.write(f"Manual trigger via emergency_stop.py\n")
        f.write(f"Timestamp: {__import__('time').time()}\n")
    
    print("🚨 EMERGENCY STOP ACTIVATED!")
    print("🛑 All mainnet operations will halt immediately")
    print(f"📁 Emergency stop file created: {emergency_file}")
    print("\n🔧 To resume operations:")
    print("1. Investigate the issue")
    print("2. Delete the EMERGENCY_STOP.txt file")
    print("3. Restart the agent")

def clear_emergency_stop():
    """Clear emergency stop"""
    emergency_file = 'EMERGENCY_STOP.txt'
    
    if os.path.exists(emergency_file):
        os.remove(emergency_file)
        print("✅ Emergency stop cleared")
        print("🔄 You can now restart the agent")
    else:
        print("ℹ️ No emergency stop file found")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'clear':
        clear_emergency_stop()
    else:
        emergency_stop()
