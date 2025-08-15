
#!/usr/bin/env python3
"""
Quick Dashboard Fix - Start dashboard with proper error handling
"""

import os
import sys
import time
import threading
import subprocess

def check_dashboard_running():
    """Check if dashboard is already running"""
    try:
        import requests
        response = requests.get("http://127.0.0.1:5000/api/test", timeout=3)
        return True
    except:
        return False

def start_dashboard():
    """Start the web dashboard"""
    print("🚀 STARTING DASHBOARD")
    print("=" * 30)
    
    # Check if already running
    if check_dashboard_running():
        print("✅ Dashboard is already running!")
        print("🌐 Access it via your Replit webview URL")
        return
    
    # Force environment setup
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    print("🔧 Setting up environment...")
    print("🌐 Starting dashboard on port 5000...")
    
    try:
        # Import and start dashboard
        from web_dashboard import app
        
        print("✅ Dashboard module loaded successfully")
        print("🔗 Dashboard will be accessible at your Replit webview URL")
        print("📊 Loading wallet data and Aave positions...")
        
        # Start the Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ Dashboard startup error: {e}")
        
        # Try alternative dashboard
        try:
            print("🔄 Trying alternative dashboard...")
            from improved_web_dashboard import app as alt_app, setup_app
            setup_app()
            alt_app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        except Exception as e2:
            print(f"❌ Alternative dashboard failed: {e2}")
            print("💡 Try running: python web_dashboard.py")

if __name__ == "__main__":
    start_dashboard()
