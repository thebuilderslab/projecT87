
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
