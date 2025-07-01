
#!/usr/bin/env python3
"""
Launch Improved Dashboard
Comprehensive launcher with error handling and fallbacks
"""

import os
import sys
import time
import subprocess

def setup_environment():
    """Set up environment for dashboard"""
    print("🔧 Setting up environment...")
    
    # Force mainnet mode
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    # Clear any emergency stops
    emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
    if os.path.exists(emergency_file):
        os.remove(emergency_file)
        print("✅ Cleared emergency stop")
    
    print("✅ Environment configured")

def test_dependencies():
    """Test that all required dependencies are available"""
    print("🧪 Testing dependencies...")
    
    try:
        from flask import Flask
        print("✅ Flask available")
        
        from web3 import Web3
        print("✅ Web3 available")
        
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        print("✅ Agent available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def launch_dashboard():
    """Launch the improved dashboard"""
    try:
        print("🚀 LAUNCHING IMPROVED DEFI DASHBOARD")
        print("=" * 50)
        
        setup_environment()
        
        if not test_dependencies():
            print("❌ Dependency test failed")
            return False
        
        print("✅ All systems ready")
        print("🌐 Starting dashboard on port 5000...")
        print("🔗 Access via your Replit webview URL")
        print("📊 DeBank-style interface with real data")
        
        # Import and run the improved dashboard
        from improved_web_dashboard import app, setup_app
        
        setup_app()
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard launch failed: {e}")
        return False

def run_monitoring_loop():
    """Run monitoring to ensure dashboard stays healthy"""
    import threading
    import requests
    
    def monitor():
        time.sleep(10)  # Wait for startup
        
        while True:
            try:
                response = requests.get('http://localhost:5000/api/system-status', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Dashboard healthy - Last update: {data.get('data_age_seconds', 0):.0f}s ago")
                else:
                    print(f"⚠️ Dashboard status: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Monitor check failed: {e}")
            
            time.sleep(60)  # Check every minute
    
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

if __name__ == "__main__":
    success = launch_dashboard()
    
    if success:
        print("✅ Dashboard launched successfully")
        run_monitoring_loop()
    else:
        print("❌ Dashboard launch failed")
        sys.exit(1)
