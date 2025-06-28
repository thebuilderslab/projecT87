
#!/usr/bin/env python3
"""
Quick agent status checker to monitor when agent is ready
"""

import time
import requests
import json

def check_agent_status():
    """Check if agent is ready and functional"""
    url = "http://localhost:5000/api/wallet_status"
    
    try:
        print("🔍 Checking agent status...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'error' not in data:
                print("✅ AGENT STATUS: READY")
                print(f"   Wallet: {data.get('wallet_address', 'Unknown')}")
                print(f"   Network: {data.get('network_name', 'Unknown')}")
                print(f"   ETH Balance: {data.get('eth_balance', 0):.6f}")
                print(f"   Health Factor: {data.get('health_factor', 0):.4f}")
                
                if data.get('health_factor', 0) > 0:
                    print("✅ AAVE INTEGRATION: ACTIVE")
                else:
                    print("⚠️ AAVE INTEGRATION: CHECKING...")
                
                return True
            else:
                print(f"❌ AGENT ERROR: {data['error']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard not running - start with 'python web_dashboard.py'")
        return False
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

def monitor_agent_status(check_interval=5):
    """Monitor agent status until ready"""
    print("🤖 DeFi Agent Status Monitor")
    print("=" * 40)
    
    attempts = 0
    max_attempts = 20  # 100 seconds total
    
    while attempts < max_attempts:
        attempts += 1
        print(f"\n📊 Status Check #{attempts}")
        
        if check_agent_status():
            print("\n🎉 AGENT IS READY FOR OPERATION!")
            print("🌐 Access dashboard at your Replit webview URL")
            return True
        
        if attempts < max_attempts:
            print(f"⏳ Waiting {check_interval} seconds before next check...")
            time.sleep(check_interval)
    
    print(f"\n⚠️ Agent not ready after {max_attempts} attempts")
    print("💡 Check the dashboard console for initialization errors")
    return False

if __name__ == "__main__":
    monitor_agent_status()
