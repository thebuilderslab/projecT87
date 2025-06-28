
#!/usr/bin/env python3
"""Clean dashboard launcher with error handling"""

import os
import sys
import time

def ensure_environment():
    """Ensure basic environment setup"""
    # Create basic files if missing
    if not os.path.exists('user_settings.json'):
        basic_settings = {
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'auto_mode': True,
            'exploration_rate': 0.1
        }
        import json
        with open('user_settings.json', 'w') as f:
            json.dump(basic_settings, f, indent=2)
        print("✅ Created user_settings.json")

def launch_dashboard():
    """Launch the dashboard"""
    try:
        print("🚀 LAUNCHING DEFI AGENT DASHBOARD")
        print("=" * 40)
        
        # Clear any emergency stops
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        if os.path.exists(emergency_file):
            os.remove(emergency_file)
            print("✅ Cleared emergency stop")
        
        ensure_environment()
        
        # Import and start dashboard
        from web_dashboard import app
        print("✅ Web dashboard imported successfully")
        print("🌐 Starting on port 5000...")
        print("🔗 Access via your Replit webview URL")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ Dashboard launch failed: {e}")
        print("🔧 Check syntax and environment setup")

if __name__ == "__main__":
    launch_dashboard()
