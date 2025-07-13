
#!/usr/bin/env python3
"""
System Readiness Check - Verifies all components are ready for operation
"""

import os
import sys
import time
import subprocess
import requests
from datetime import datetime

def check_autonomous_agent():
    """Check if autonomous agent is running"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        return 'run_autonomous_mainnet.py' in result.stdout
    except:
        return False

def check_dashboard_health():
    """Check if dashboard is accessible"""
    ports_to_check = [5000, 5001, 5002, 8080]
    
    for port in ports_to_check:
        try:
            response = requests.get(f'http://localhost:{port}/api/test', timeout=5)
            if response.status_code == 200:
                return True, port
        except:
            continue
    return False, None

def check_secrets():
    """Verify critical secrets are available"""
    required_secrets = ['PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 'NETWORK_MODE']
    missing = []
    
    for secret in required_secrets:
        if not os.getenv(secret):
            missing.append(secret)
    
    return len(missing) == 0, missing

def main():
    print("🔍 SYSTEM READINESS CHECK")
    print("=" * 50)
    
    # Check 1: Secrets
    secrets_ok, missing_secrets = check_secrets()
    if secrets_ok:
        print("✅ Secrets: All required secrets available")
    else:
        print(f"❌ Secrets: Missing {missing_secrets}")
        return False
    
    # Check 2: Autonomous Agent
    agent_running = check_autonomous_agent()
    if agent_running:
        print("✅ Autonomous Agent: Running and monitoring")
    else:
        print("❌ Autonomous Agent: Not running")
        print("💡 Start with: python run_autonomous_mainnet.py")
        return False
    
    # Check 3: Dashboard
    dashboard_ok, port = check_dashboard_health()
    if dashboard_ok:
        print(f"✅ Dashboard: Accessible on port {port}")
    else:
        print("❌ Dashboard: Not accessible")
        print("💡 Start with: python web_dashboard.py")
        return False
    
    # Check 4: Emergency Stop
    emergency_active = os.path.exists('EMERGENCY_STOP_ACTIVE.flag')
    if not emergency_active:
        print("✅ Emergency Stop: Not active")
    else:
        print("⚠️ Emergency Stop: Currently active")
        print("💡 Clear with: python emergency_stop.py clear")
    
    print("\n" + "=" * 50)
    
    if secrets_ok and agent_running and dashboard_ok and not emergency_active:
        print("🎉 SYSTEM STATUS: READY FOR OPERATION")
        print(f"🌐 Dashboard: http://localhost:{port}")
        print("🤖 Autonomous agent monitoring your Aave position")
        print("💰 Waiting for $12+ collateral growth to trigger actions")
        return True
    else:
        print("❌ SYSTEM STATUS: NOT READY")
        print("💡 Fix the issues above and run this check again")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
