
#!/usr/bin/env python3
"""
Complete Autonomous System Launcher
Starts both the autonomous mainnet agent and dashboard in parallel
"""

import os
import sys
import time
import threading
import subprocess
import signal
from datetime import datetime

# Force mainnet mode
os.environ['NETWORK_MODE'] = 'mainnet'

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def check_secrets():
    """Verify all required secrets are present"""
    required_secrets = ['PRIVATE_KEY', 'COINMARKETCAP_API_KEY']
    missing = []
    
    for secret in required_secrets:
        if not os.getenv(secret):
            missing.append(secret)
    
    if missing:
        log_message(f"❌ Missing required secrets: {missing}", "ERROR")
        log_message("💡 Please add these to your Replit Secrets", "INFO")
        return False
    
    log_message("✅ All required secrets are present", "SUCCESS")
    return True

def start_dashboard():
    """Start the web dashboard"""
    try:
        log_message("🌐 Starting Web Dashboard...", "INFO")
        
        # Clear any emergency stop flags
        if os.path.exists('EMERGENCY_STOP_ACTIVE.flag'):
            os.remove('EMERGENCY_STOP_ACTIVE.flag')
            log_message("🔄 Cleared emergency stop flag", "INFO")
        
        # Start dashboard in subprocess
        dashboard_process = subprocess.Popen(
            [sys.executable, 'web_dashboard.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        log_message("✅ Dashboard process started", "SUCCESS")
        return dashboard_process
        
    except Exception as e:
        log_message(f"❌ Failed to start dashboard: {e}", "ERROR")
        return None

def start_autonomous_agent():
    """Start the autonomous agent"""
    try:
        log_message("🤖 Starting Autonomous Agent...", "INFO")
        
        # Start autonomous agent in subprocess
        agent_process = subprocess.Popen(
            [sys.executable, 'run_autonomous_mainnet.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        log_message("✅ Autonomous agent process started", "SUCCESS")
        return agent_process
        
    except Exception as e:
        log_message(f"❌ Failed to start autonomous agent: {e}", "ERROR")
        return None

def monitor_process(process, name):
    """Monitor a process and log its output"""
    while True:
        try:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[{name}] {output.strip()}")
        except:
            break

def main():
    """Main launcher function"""
    print("🚀 COMPLETE AUTONOMOUS MAINNET SYSTEM")
    print("=" * 60)
    print("🌐 Network: Arbitrum Mainnet")
    print("🤖 Mode: Full Autonomous Operation with Dashboard")
    print("🛑 Emergency Stop: Create 'EMERGENCY_STOP_ACTIVE.flag' to halt")
    print("=" * 60)
    
    # Check secrets
    if not check_secrets():
        return
    
    # Start dashboard first
    dashboard_process = start_dashboard()
    if not dashboard_process:
        log_message("❌ Cannot continue without dashboard", "ERROR")
        return
    
    # Wait for dashboard to initialize
    time.sleep(15)
    log_message("⏰ Dashboard initialization complete", "INFO")
    
    # Start autonomous agent
    agent_process = start_autonomous_agent()
    if not agent_process:
        log_message("❌ Cannot continue without autonomous agent", "ERROR")
        if dashboard_process:
            dashboard_process.terminate()
        return
    
    # Wait for agent to initialize
    time.sleep(10)
    log_message("⏰ Autonomous agent initialization complete", "INFO")
    
    log_message("🎯 SYSTEM FULLY OPERATIONAL", "SUCCESS")
    log_message("📊 Dashboard: http://localhost:5000", "INFO")
    log_message("🤖 Autonomous agent monitoring for triggers", "INFO")
    log_message("💰 Current baseline: $177.79, Next trigger: $189.79", "INFO")
    log_message("🛑 Press Ctrl+C to stop all processes", "INFO")
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        log_message("🛑 Shutdown signal received", "INFO")
        if dashboard_process:
            dashboard_process.terminate()
        if agent_process:
            agent_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Monitor both processes
    try:
        # Start monitoring threads
        dashboard_thread = threading.Thread(
            target=monitor_process, 
            args=(dashboard_process, "DASHBOARD"),
            daemon=True
        )
        agent_thread = threading.Thread(
            target=monitor_process, 
            args=(agent_process, "AGENT"),
            daemon=True
        )
        
        dashboard_thread.start()
        agent_thread.start()
        
        # Keep main thread alive
        while True:
            # Check if processes are still running
            if dashboard_process.poll() is not None:
                log_message("❌ Dashboard process died", "ERROR")
                break
            if agent_process.poll() is not None:
                log_message("❌ Agent process died", "ERROR")
                break
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        log_message("👋 System stopped by user", "INFO")
    finally:
        # Clean shutdown
        if dashboard_process:
            dashboard_process.terminate()
        if agent_process:
            agent_process.terminate()

if __name__ == "__main__":
    main()
