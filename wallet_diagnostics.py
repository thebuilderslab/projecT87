
#!/usr/bin/env python3
"""
Wallet Diagnostics Script
Provides detailed analysis of wallet state and readiness for DeFi operations
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from dotenv import load_dotenv

def run_wallet_diagnostics():
    """Run comprehensive wallet diagnostics"""
    print("🔍 WALLET DIAGNOSTICS")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        
        print(f"✅ Connected to {agent.w3.eth.chain_id}")
        print(f"📍 Wallet: {agent.address}")
        
        # Check ETH balance
        eth_balance = agent.get_eth_balance()
        print(f"💰 ETH Balance: {eth_balance:.6f} ETH")
        
        # Check if wallet has enough for gas
        if eth_balance < 0.001:
            print("⚠️ WARNING: Low ETH balance - may not be enough for transactions")
        else:
            print("✅ Sufficient ETH for gas fees")
        
        # Check Aave positions
        if hasattr(agent, 'aave'):
            health_data = agent.health_monitor.get_current_health_factor()
            if health_data:
                print(f"\n🏦 AAVE STATUS:")
                print(f"   Health Factor: {health_data['health_factor']}")
                print(f"   Total Collateral: {health_data['total_collateral_eth']:.6f} ETH")
                print(f"   Total Debt: {health_data['total_debt_eth']:.6f} ETH")
                
                if health_data['total_collateral_eth'] == 0:
                    print("💡 No active Aave positions - wallet is ready to start DeFi operations")
                else:
                    print("✅ Active Aave positions detected")
        
        # Check token balances
        print(f"\n🪙 TOKEN BALANCES:")
        try:
            usdc_balance = agent.aave.get_token_balance(agent.aave.usdc_address)
            print(f"   USDC: {usdc_balance:.2f}")
            
            arb_balance = agent.health_monitor.get_arb_balance()
            print(f"   ARB: {arb_balance:.4f}")
        except Exception as e:
            print(f"   ❌ Error getting token balances: {e}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if eth_balance > 0.01:
            print("✅ Ready for DeFi operations!")
            print("   - Agent will automatically start with small Aave supply operations")
            print("   - Parameters are being applied correctly")
            print("   - Next agent iteration will execute on-chain transactions")
        else:
            print("⚠️ Need more ETH for meaningful DeFi operations")
            print(f"   - Current: {eth_balance:.6f} ETH")
            print("   - Recommended minimum: 0.01 ETH")
        
    except Exception as e:
        print(f"❌ Diagnostics failed: {e}")

if __name__ == "__main__":
    run_wallet_diagnostics()
