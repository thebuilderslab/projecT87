import threading
import subprocess
import time
import sys
import os

def run_agent():
    """Run the autonomous agent in a loop to handle crashes/restarts"""
    while True:
        try:
            print("🚀 Starting Autonomous Agent...", flush=True)
            subprocess.run([sys.executable, "run_autonomous_mainnet.py"])
            print("⚠️ Agent stopped. Restarting in 5 seconds...", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"❌ Agent execution error: {e}. Restarting...", flush=True)
            time.sleep(5)

def run_dashboard():
    """Run the web dashboard in a loop"""
    while True:
        try:
            print("📊 Starting Web Dashboard...", flush=True)
            subprocess.run([sys.executable, "web_dashboard.py"])
            print("⚠️ Dashboard stopped. Restarting in 5 seconds...", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"❌ Dashboard execution error: {e}. Restarting...", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    print("🤖 SYSTEM LAUNCH: Dual-Process Mode", flush=True)

    agent_thread = threading.Thread(target=run_agent, daemon=True)
    agent_thread.start()

    run_dashboard()
