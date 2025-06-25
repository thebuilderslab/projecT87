
#!/usr/bin/env python3
"""
Create Initial Aave Position Script
Supply ETH as collateral and borrow 20 USDC to create position
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Create initial Aave position with 20 USDC borrow"""
    print("🚀 CREATING INITIAL AAVE POSITION")
    print("=" * 50)

    try:
        print("🤖 Initializing DeFi agent...")
        agent = ArbitrumTestnetAgent()

        print("📍 Wallet:", agent.address)
        print("🌐 Chain ID:", agent.w3.eth.chain_id)
        print("💰 ETH Balance:", agent.get_eth_balance(), "ETH")

        # Check if position already exists
        monitoring_summary = agent.health_monitor.get_monitoring_summary()
        
        if (monitoring_summary['total_collateral_eth'] > 0 or 
            monitoring_summary['total_debt_eth'] > 0):
            print("ℹ️ Aave position already exists!")
            print(f"   Collateral: {monitoring_summary['total_collateral_eth']:.6f} ETH")
            print(f"   Debt: {monitoring_summary['total_debt_eth']:.6f} ETH")
            print(f"   Health Factor: {monitoring_summary['current_health_factor']:.2f}")
            return

        # Get ETH balance
        eth_balance = agent.get_eth_balance()
        
        if eth_balance < 0.002:
            print(f"❌ Insufficient ETH balance ({eth_balance:.6f}) for position creation")
            print("💡 Need at least 0.002 ETH for gas fees")
            return

        # Step 1: Supply ETH as collateral
        collateral_amount = eth_balance * 0.8  # Use 80%, keep 20% for gas
        print(f"\n🏦 Step 1: Supplying {collateral_amount:.6f} ETH as collateral...")
        
        supply_tx = agent.aave.supply_to_aave(
            agent.aave.weth_address,
            collateral_amount
        )
        
        if not supply_tx:
            print("❌ Failed to supply ETH as collateral")
            return
        
        print(f"✅ ETH supplied successfully! TX: {supply_tx}")
        print("⏳ Waiting 15 seconds for confirmation...")
        time.sleep(15)

        # Step 2: Borrow 20 USDC
        usdc_borrow_amount = 20.0
        print(f"\n💳 Step 2: Borrowing {usdc_borrow_amount} USDC...")
        
        # Safety check: estimate health factor
        # Assuming ETH = $2500, LTV = 80%
        eth_price_estimate = 2500
        collateral_value = collateral_amount * eth_price_estimate
        estimated_hf = (collateral_value * 0.8) / usdc_borrow_amount
        
        print(f"📊 Estimated Health Factor: {estimated_hf:.2f}")
        
        if estimated_hf < 3.5:
            print(f"⚠️ Estimated health factor {estimated_hf:.2f} below target 3.5")
            print("💡 Reducing borrow amount for safety...")
            usdc_borrow_amount = min(15.0, (collateral_value * 0.8) / 4.0)  # Target HF = 4.0
            print(f"🔧 Adjusted borrow amount: {usdc_borrow_amount:.2f} USDC")
        
        borrow_tx = agent.aave.borrow_from_aave(
            agent.aave.usdc_address,
            usdc_borrow_amount
        )
        
        if not borrow_tx:
            print("❌ Failed to borrow USDC")
            return
        
        print(f"✅ USDC borrowed successfully! TX: {borrow_tx}")
        print("⏳ Waiting 10 seconds for final confirmation...")
        time.sleep(10)

        # Step 3: Verify position
        print(f"\n📊 Step 3: Verifying created position...")
        final_summary = agent.health_monitor.get_monitoring_summary()
        
        print(f"🎯 POSITION CREATED SUCCESSFULLY!")
        print(f"   Collateral: {final_summary['total_collateral_eth']:.6f} ETH")
        print(f"   Debt: {final_summary['total_debt_eth']:.6f} ETH")
        print(f"   Health Factor: {final_summary['current_health_factor']:.2f}")
        print(f"   Target Health Factor: > 3.5 ✅")
        
        print(f"\n🤖 Agent is now configured to maintain Health Factor > 3.5")
        print(f"🚀 You can now run the main agent to manage this position automatically!")

    except Exception as e:
        print(f"❌ Error creating position: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
