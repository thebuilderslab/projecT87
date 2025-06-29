
#!/usr/bin/env python3
"""
Quick readiness verification for the DeFi agent
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def verify_system_readiness():
    """Comprehensive readiness check"""
    print("🔍 VERIFYING SYSTEM READINESS")
    print("=" * 50)
    
    issues = []
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: {agent.network_mode} (Chain ID: {agent.w3.eth.chain_id})")
        
        # Check ETH balance
        eth_balance = agent.get_eth_balance()
        print(f"⚡ ETH Balance: {eth_balance:.6f} ETH")
        
        if eth_balance < 0.001:
            issues.append("Low ETH balance - may not cover gas fees")
        
        # Initialize integrations
        if agent.initialize_integrations():
            print("✅ DeFi integrations initialized")
            
            # Test USDC balance
            if hasattr(agent, 'aave'):
                usdc_balance = agent.aave.get_token_balance(agent.usdc_address)
                print(f"💵 USDC Balance: {usdc_balance:.6f}")
                
                if usdc_balance > 0:
                    print("✅ USDC balance detected - ready for swaps!")
                else:
                    issues.append("No USDC balance detected")
            
            # Test network connectivity
            network_ok, status = agent.check_network_status()
            if network_ok:
                print("✅ Network connectivity verified")
            else:
                issues.append(f"Network issue: {status}")
        else:
            issues.append("DeFi integrations failed to initialize")
        
        # Final assessment
        print(f"\n🎯 READINESS ASSESSMENT:")
        if len(issues) == 0:
            print("🎉 SYSTEM IS READY!")
            print("✅ All critical components working")
            print("🚀 Ready to run autonomous mode")
            return True
        else:
            print(f"⚠️ {len(issues)} ISSUE(S) FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            
            # Check if issues are just funding related
            funding_issues = [issue for issue in issues if 'balance' in issue.lower() or 'usdc' in issue.lower()]
            if len(funding_issues) == len(issues):
                print(f"\n💡 All issues are funding-related. You can:")
                print("1. Fund your wallet with ETH and USDC")
                print("2. Or set up test mode with lower requirements:")
                print("   python funding_bypass_handler.py")
            else:
                print(f"\n💡 Fix these issues and re-run verification")
            return False
            
    except Exception as e:
        print(f"❌ Critical error during verification: {e}")
        return False

if __name__ == "__main__":
    verify_system_readiness()
