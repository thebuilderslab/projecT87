
#!/usr/bin/env python3
"""
Start Dashboard - Simple dashboard launcher
"""

import os
import sys
import time
import subprocess
import socket

def get_available_port(start_port=5000):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    return 8080

def start_dashboard():
    """Start the web dashboard"""
    print("🌐 Starting DeFi Agent Dashboard...")
    
    # Check if web_dashboard.py exists
    if not os.path.exists('web_dashboard.py'):
        print("❌ web_dashboard.py not found")
        return False
    
    try:
        port = get_available_port(5000)
        print(f"🌐 Dashboard will start on port {port}")
        
        # Set environment variables for safe mode
        os.environ['DASHBOARD_SAFE_MODE'] = 'true'
        os.environ['DASHBOARD_PORT'] = str(port)
        
        # Start the dashboard
        subprocess.run([sys.executable, 'web_dashboard.py'], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dashboard failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    start_dashboard()
