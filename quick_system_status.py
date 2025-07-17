
#!/usr/bin/env python3
"""
Quick System Status Checker - Fast overview of system readiness
"""

import os
import sys

def quick_status_check():
    """Quick system status check"""
    print("⚡ QUICK SYSTEM STATUS CHECK")
    print("=" * 40)
    
    status = {
        'secrets': 0,
        'files': 0, 
        'syntax': 0,
        'ready': False
    }
    
    # Check secrets
    secrets = ['PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 'NETWORK_MODE']
    for secret in secrets:
        if os.getenv(secret):
            status['secrets'] += 1
    
    print(f"🔐 Secrets: {status['secrets']}/3 configured")
    
    # Check critical files
    files = ['arbitrum_testnet_agent.py', 'web_dashboard.py', 'complete_autonomous_launcher.py']
    for file in files:
        if os.path.exists(file):
            status['files'] += 1
    
    print(f"📁 Files: {status['files']}/3 present")
    
    # Quick syntax check on main agent
    try:
        with open('arbitrum_testnet_agent.py', 'r') as f:
            compile(f.read(), 'arbitrum_testnet_agent.py', 'exec')
        status['syntax'] = 1
        print(f"✅ Syntax: Main agent file valid")
    except:
        print(f"❌ Syntax: Main agent has errors")
    
    # Overall readiness
    if status['secrets'] == 3 and status['files'] == 3 and status['syntax'] == 1:
        status['ready'] = True
        print(f"\n🎉 STATUS: READY FOR LAUNCH!")
        print(f"💡 Run: python verified_system_launcher.py")
    else:
        print(f"\n⚠️ STATUS: NEEDS ATTENTION")
        if status['secrets'] < 3:
            print(f"   • Add missing secrets to Replit Secrets")
        if status['files'] < 3:
            print(f"   • Some critical files missing")  
        if status['syntax'] < 1:
            print(f"   • Fix syntax errors in main agent")
    
    print("=" * 40)
    return status['ready']

if __name__ == "__main__":
    quick_status_check()
