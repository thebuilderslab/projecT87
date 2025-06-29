
#!/usr/bin/env python3
"""
Swap 40.6293 USDC for WBTC and supply as collateral
Execute: python swap_usdc_for_wbtc.py
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Swap 40.6293 USDC for WBTC and supply as collateral to Aave"""
    print("🔄 USDC → WBTC → AAVE SUPPLY")
    print("=" * 50)

    # Force mainnet mode from environment
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    print(f"🌐 Network Mode: {network_mode}")

    if network_mode == 'mainnet':
        print("🚨 MAINNET MODE - Using real funds!")

    try:
        print("🤖 Initializing DeFi agent...")
        agent = ArbitrumTestnetAgent()

        print("📍 Wallet:", agent.address)
        print("🌐 Chain ID:", agent.w3.eth.chain_id)

        # Initialize integrations
        print("🔧 Initializing integrations...")
        success = agent.initialize_integrations()
        if not success:
            print("❌ Failed to initialize integrations")
            return

        # Verify integrations are working
        if not agent.aave or not agent.uniswap:
            print("❌ Required integrations not available")
            return

        # Check current USDC balance
        usdc_balance = agent.aave.get_token_balance(agent.usdc_address)
        print(f"💰 Current USDC balance: {usdc_balance:.4f}")

        usdc_amount = 40.6293
        if usdc_balance < usdc_amount:
            print(f"❌ Insufficient USDC balance. Need {usdc_amount:.4f}, have {usdc_balance:.4f}")
            print("💡 Please ensure you have enough USDC in your wallet")
            return

        print(f"🔄 Step 1: Swapping {usdc_amount:.4f} USDC for WBTC...")
        
        # Calculate USDC amount in wei (6 decimals)
        usdc_amount_wei = int(usdc_amount * (10 ** 6))
        
        # Swap USDC for WBTC using Uniswap
        # Using 500 basis points (0.05%) fee tier for USDC/WBTC
        swap_result = agent.uniswap.swap_tokens(
            agent.usdc_address,  # token_in (USDC)
            agent.wbtc_address,  # token_out (WBTC)
            usdc_amount_wei,     # amount_in
            500                  # fee (0.05%)
        )

        if not swap_result:
            print("❌ Failed to swap USDC for WBTC")
            return

        print(f"✅ USDC → WBTC swap completed!")
        print(f"🔗 Transaction hash: {swap_result}")
        
        if agent.w3.eth.chain_id == 42161:
            print(f"📊 View on Arbiscan: https://arbiscan.io/tx/{swap_result}")

        # Wait for swap confirmation
        print("⏳ Waiting for swap confirmation...")
        time.sleep(10)

        # Check WBTC balance after swap
        wbtc_balance = agent.aave.get_token_balance(agent.wbtc_address)
        print(f"💰 WBTC received: {wbtc_balance:.8f} WBTC")

        if wbtc_balance < 0.00000001:  # Minimum threshold
            print("❌ No WBTC received from swap")
            return

        print(f"🏦 Step 2: Supplying {wbtc_balance:.8f} WBTC to Aave as collateral...")
        
        # Supply all received WBTC to Aave
        supply_result = agent.aave.supply_wbtc_to_aave(wbtc_balance)

        if supply_result:
            print("✅ WBTC supply completed successfully!")
            print(f"🔗 Transaction hash: {supply_result}")
            if agent.w3.eth.chain_id == 42161:
                print(f"📊 View on Arbiscan: https://arbiscan.io/tx/{supply_result}")
            
            # Wait and check updated position
            print("⏳ Waiting for supply confirmation...")
            time.sleep(10)
            
            # Get updated Aave position
            if hasattr(agent, 'health_monitor'):
                print("\n📊 Updated Aave Position:")
                health_data = agent.health_monitor.get_current_health_factor()
                if health_data:
                    print(f"   Health Factor: {health_data['health_factor']:.4f}")
                    print(f"   Total Collateral: ${health_data.get('total_collateral_usdc', 0):.2f}")
                    print(f"   Total Debt: ${health_data.get('total_debt_usdc', 0):.2f}")
                    print(f"   Available Borrows: ${health_data.get('available_borrows_usdc', 0):.2f}")
        else:
            print("❌ WBTC supply failed")
            print("💡 Check your WBTC balance and gas fees")

        print("\n🎉 Operation completed successfully!")
        print(f"✅ Swapped {usdc_amount:.4f} USDC for WBTC")
        print(f"✅ Supplied WBTC as collateral to Aave")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Ensure you have enough USDC and gas fees")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
