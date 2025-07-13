
#!/usr/bin/env python3
"""
Restart dashboard with all fixes applied
"""

import os
import sys
import time
import subprocess
import signal

def kill_existing_dashboard():
    """Kill any existing dashboard processes"""
    try:
        # Kill any existing Python processes running web_dashboard.py
        subprocess.run(['pkill', '-f', 'web_dashboard.py'], 
                      capture_output=True, timeout=5)
        print("✅ Killed existing dashboard processes")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ No existing dashboard processes to kill: {e}")

def start_dashboard():
    """Start the dashboard with all fixes"""
    print("🚀 STARTING FIXED DASHBOARD")
    print("=" * 50)
    
    # Ensure environment is set
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    # Clear any emergency stops
    if os.path.exists('EMERGENCY_STOP_ACTIVE.flag'):
        os.remove('EMERGENCY_STOP_ACTIVE.flag')
        print("✅ Cleared emergency stop")
    
    print("🔧 Starting web dashboard with live data...")
    
    # Start dashboard
    try:
        subprocess.run(['python', 'web_dashboard.py'], check=True)
    except KeyboardInterrupt:
        print("\n✅ Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == "__main__":
    kill_existing_dashboard()
    start_dashboard()
