#!/usr/bin/env python3
"""
Supply WBTC to Aave V3 Script
Execute: python supply_wbtc.py
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Supply 0.0004087 WBTC to Aave V3 as collateral"""
    print("🪙 WBTC Supply to Aave V3")
    print("=" * 50)

    # Force mainnet mode from environment
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    print(f"🌐 Network Mode: {network_mode}")

    if network_mode == 'mainnet':
        print("🚨 MAINNET MODE - Using real funds!")

    try:
        print("🤖 Initializing DeFi agent...")
        agent = ArbitrumTestnetAgent(network_mode)

        print("📍 Wallet:", agent.address)
        print("🌐 Chain ID:", agent.w3.eth.chain_id)

        # Initialize Aave integration if not already done
        if not hasattr(agent, 'aave'):
            from aave_integration import AaveArbitrumIntegration
            agent.aave = AaveArbitrumIntegration(agent.w3, agent.account)

        # Supply 0.0004087 WBTC to Aave V3
        wbtc_amount = 0.0004087
        print(f"🏦 Supplying {wbtc_amount} WBTC to Aave V3...")

        result = agent.aave.supply_wbtc_to_aave(wbtc_amount)

        if result:
            print("✅ WBTC supply completed successfully!")
            print(f"🔗 Transaction hash: {result}")
            if agent.w3.eth.chain_id == 42161:
                print(f"📊 View on Arbiscan: https://arbiscan.io/tx/{result}")
        else:
            print("❌ WBTC supply failed")
            print("💡 Check your WBTC balance and gas fees")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Ensure your wallet is properly funded and try again")

if __name__ == "__main__":
    main()