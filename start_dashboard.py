
#!/usr/bin/env python3
"""Alternative dashboard startup with error handling"""

import os
import sys
import time
import subprocess

def setup_environment():
    """Ensure environment is properly set up"""
    if not os.path.exists('.env'):
        print("⚠️ Creating basic .env file...")
        with open('.env', 'w') as f:
            f.write("NETWORK_MODE=mainnet\n")
            f.write("PRIVATE_KEY=your_private_key_here\n")
            f.write("COINMARKETCAP_API_KEY=your_api_key_here\n")

def check_syntax():
    """Check for syntax errors"""
    files_to_check = ['arbitrum_testnet_agent.py', 'web_dashboard.py']
    
    for file in files_to_check:
        try:
            with open(file, 'r') as f:
                compile(f.read(), file, 'exec')
            print(f"✅ {file}: Syntax OK")
        except SyntaxError as e:
            print(f"❌ {file}: Syntax Error at line {e.lineno}: {e.msg}")
            return False
    return True

def start_dashboard():
    """Start the dashboard with error handling"""
    try:
        print("🚀 Starting DeFi Agent Dashboard...")
        
        # Import and run
        from web_dashboard import app
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ Dashboard startup failed: {e}")
        print("💡 Check your environment variables and syntax")

if __name__ == "__main__":
    print("🤖 DeFi Agent Dashboard Launcher")
    print("=" * 40)
    
    setup_environment()
    
    if check_syntax():
        start_dashboard()
    else:
        print("❌ Fix syntax errors before continuing")
#!/usr/bin/env python3
"""
Simple dashboard startup script for preview
"""

import os
import sys

def start_dashboard():
    """Start the web dashboard with proper error handling"""
    print("🚀 Starting DeFi Agent Dashboard Preview")
    print("=" * 50)
    
    # Set environment for preview
    os.environ['NETWORK_MODE'] = 'mainnet'
    os.environ['AUTO_START_DASHBOARD'] = 'true'
    
    # Clear any emergency stops
    if os.path.exists('EMERGENCY_STOP_ACTIVE.flag'):
        os.remove('EMERGENCY_STOP_ACTIVE.flag')
        print("✅ Cleared emergency stop for preview")
    
    try:
        # Import and start dashboard
        import web_dashboard
        print("✅ Dashboard imported successfully")
        
        # Start the Flask app
        port = 5000
        print(f"🌐 Starting dashboard on port {port}")
        print(f"🔗 Preview will be available at your Replit preview URL")
        
        web_dashboard.app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_dashboard()
