
#!/usr/bin/env python3
"""
Parallel Dashboard Launcher - Runs dashboard alongside autonomous agent
"""

import os
import sys
import subprocess
import time
import threading
from datetime import datetime

def start_dashboard():
    """Start the web dashboard in background"""
    try:
        print("🌐 Starting web dashboard...")
        
        # Set environment variables for dashboard
        os.environ['DASHBOARD_MODE'] = 'autonomous_support'
        os.environ['AUTO_REFRESH'] = '30'  # Refresh every 30 seconds
        
        # Start dashboard process
        dashboard_process = subprocess.Popen([
            sys.executable, 'web_dashboard.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"✅ Dashboard started with PID: {dashboard_process.pid}")
        return dashboard_process
        
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return None

def start_autonomous_agent():
    """Start the autonomous agent"""
    try:
        print("🤖 Starting autonomous agent...")
        
        # Start autonomous agent process
        agent_process = subprocess.Popen([
            sys.executable, 'run_autonomous_mainnet.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"✅ Autonomous agent started with PID: {agent_process.pid}")
        return agent_process
        
    except Exception as e:
        print(f"❌ Failed to start autonomous agent: {e}")
        return None

def monitor_processes(dashboard_process, agent_process):
    """Monitor both processes and restart if needed"""
    while True:
        try:
            # Check dashboard
            if dashboard_process and dashboard_process.poll() is not None:
                print("⚠️ Dashboard process died, restarting...")
                dashboard_process = start_dashboard()
            
            # Check agent  
            if agent_process and agent_process.poll() is not None:
                print("⚠️ Autonomous agent process died, restarting...")
                agent_process = start_autonomous_agent()
            
            # Check for emergency stop
            if os.path.exists('EMERGENCY_STOP_ACTIVE.flag'):
                print("🛑 Emergency stop detected, shutting down...")
                if dashboard_process:
                    dashboard_process.terminate()
                if agent_process:
                    agent_process.terminate()
                break
                
            # Print status every 5 minutes
            print(f"✅ Both processes running - Dashboard PID: {dashboard_process.pid if dashboard_process else 'None'}, Agent PID: {agent_process.pid if agent_process else 'None'}")
            time.sleep(300)  # Check every 5 minutes
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down all processes...")
            if dashboard_process:
                dashboard_process.terminate()
            if agent_process:
                agent_process.terminate()
            return True  # Successful shutdown
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(10)
    
    return True  # Successful completion

def main():
    """Main launcher function"""
    print("🚀 PARALLEL AUTONOMOUS MAINNET LAUNCHER")
    print("=" * 60)
    print("🌐 This will start both dashboard AND autonomous agent")
    print("📊 Dashboard provides live data support for autonomous operations")
    print("🤖 Autonomous agent executes DeFi operations based on triggers")
    print("=" * 60)
    
    # Start dashboard first
    dashboard_process = start_dashboard()
    time.sleep(10)  # Give dashboard time to start
    
    # Start autonomous agent
    agent_process = start_autonomous_agent()
    time.sleep(5)
    
    if dashboard_process and agent_process:
        print("✅ Both processes started successfully")
        print("📊 Dashboard running in background")
        print("🤖 Autonomous agent monitoring for triggers")
        print("🛑 Press Ctrl+C to stop all processes")
        
        # Monitor both processes
        monitor_processes(dashboard_process, agent_process)
    else:
        print("❌ Failed to start one or more processes")
        if dashboard_process:
            dashboard_process.terminate()
        if agent_process:
            agent_process.terminate()

if __name__ == "__main__":
    main()
