
#!/usr/bin/env python3
"""
Start Working Dashboard - Simple launcher
"""

import os
import subprocess
import time

def main():
    print("🚀 Starting Working Dashboard based on old dashboard.py")
    print("=" * 50)
    
    # Set environment
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    # Clear any emergency stops
    emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
    if os.path.exists(emergency_file):
        os.remove(emergency_file)
        print("✅ Cleared emergency stop")
    
    print("🌐 Launching dashboard on port 5000...")
    print("🔗 Access via your Replit webview URL")
    
    # Run the working dashboard
    try:
        subprocess.run(['python', 'working_dashboard.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == '__main__':
    main()
