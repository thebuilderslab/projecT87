
#!/usr/bin/env python3

import os
import sys
from dashboard import AgentDashboard
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def run_dashboard_preview():
    """Run dashboard in preview mode - works even with zero balance"""
    print("🚀 Starting DeFi Agent Dashboard Preview")
    print("=" * 60)
    print("💡 This dashboard works even with ZERO balance!")
    print("   You can see all features before funding your wallet.")
    print("=" * 60)
    
    try:
        # Initialize agent (works with zero balance)
        agent = ArbitrumTestnetAgent()
        
        # Create dashboard
        dashboard = AgentDashboard(agent)
        
        print(f"\n📍 Your Wallet Address: {agent.address}")
        print(f"🌐 Network: Arbitrum Sepolia")
        print(f"💰 Current Balance: {agent.get_eth_balance():.6f} ETH")
        
        print(f"\n🎯 TO FUND YOUR WALLET:")
        print(f"1. Send 10 ETH and 100 DAI to: {agent.address}")
        print(f"2. Use Arbitrum Sepolia bridge: https://bridge.arbitrum.io/?destinationChain=arbitrum-sepolia")
        print(f"3. Get testnet ETH first from: https://sepoliafaucet.com/")
        
        print(f"\n🔄 Starting Interactive Dashboard...")
        print(f"   Press Ctrl+C to exit anytime")
        
        # Run the dashboard
        dashboard.run_interactive_dashboard()
        
    except KeyboardInterrupt:
        print(f"\n👋 Dashboard preview stopped. Your wallet is ready for funding!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Make sure you have PRIVATE_KEY set in your Replit secrets")

if __name__ == "__main__":
    run_dashboard_preview()
