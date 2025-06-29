#!/usr/bin/env python3
"""
Swap 40.6293 USDC for WBTC and supply as collateral
Execute: python swap_usdc_for_wbtc.py
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Main function to execute the USDC to WBTC swap with real gas estimation"""
    print("🔄 USDC → WBTC SWAP EXECUTION")
    print("=" * 50)

    # Verify private key is loaded from Replit Secrets
    private_key = os.getenv('PRIVATE_KEY') or os.getenv('PRIVATE_KEY2')
    if private_key:
        print(f"✅ Private key loaded from Replit Secrets (length: {len(private_key)})")
    else:
        print("❌ No private key found in Replit Secrets")
        return

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

        # Check current USDC balance with better error handling
        try:
            usdc_balance = agent.aave.get_token_balance(agent.usdc_address)
            print(f"💰 Current USDC balance: {usdc_balance:.4f}")
        except Exception as e:
            print(f"❌ Failed to get USDC balance: {e}")
            print("💡 This might be due to:")
            print("   1. Incorrect token contract address")
            print("   2. Network connection issues")
            print("   3. RPC provider problems")

            # Try alternative balance check
            try:
                from web3 import Web3
                usdc_contract = agent.w3.eth.contract(
                    address=agent.usdc_address,
                    abi=[{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]
                )
                balance_wei = usdc_contract.functions.balanceOf(agent.address).call()
                usdc_balance = balance_wei / (10 ** 6)  # USDC has 6 decimals
                print(f"💰 Alternative check - USDC balance: {usdc_balance:.4f}")
            except Exception as alt_e:
                print(f"❌ Alternative balance check also failed: {alt_e}")
                print(f"💡 Please check wallet balance manually at: https://arbiscan.io/address/{agent.address}")
                return

        usdc_amount = 40.6293
        if usdc_balance < usdc_amount:
            print(f"❌ Insufficient USDC balance. Need {usdc_amount:.4f}, have {usdc_balance:.4f}")
            print("💡 Funding options:")
            print(f"   1. Send USDC to: {agent.address}")
            print("   2. Use https://app.uniswap.org/ to swap ETH → USDC")
            print("   3. Bridge from another chain using https://bridge.arbitrum.io/")
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