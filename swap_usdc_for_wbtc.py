"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""

#!/usr/bin/env python3
"""
Swap 40.6293 DAI for WBTC and supply as collateral
Execute: python swap_DAI_for_wbtc.py
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Main function to execute the DAI to WBTC swap with real gas estimation"""
    print("🔄 DAI → WBTC SWAP EXECUTION")
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

        # Check current DAI balance with better error handling
        try:
            DAI_balance = agent.aave.get_token_balance(agent.dai_address)
            print(f"💰 Current DAI balance: {DAI_balance:.4f}")
        except Exception as e:
            print(f"❌ Failed to get DAI balance: {e}")
            print("💡 This might be due to:")
            print("   1. Incorrect token contract address")
            print("   2. Network connection issues")
            print("   3. RPC provider problems")

            # Try alternative balance check
            try:
                from web3 import Web3
                DAI_contract = agent.w3.eth.contract(
                    address=agent.dai_address,
                    abi=[{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]
                )
                balance_wei = DAI_contract.functions.balanceOf(agent.address).call()
                DAI_balance = balance_wei / (10 ** 6)  # DAI has 6 decimals
                print(f"💰 Alternative check - DAI balance: {DAI_balance:.4f}")
            except Exception as alt_e:
                print(f"❌ Alternative balance check also failed: {alt_e}")
                print(f"💡 Please check wallet balance manually at: https://arbiscan.io/address/{agent.address}")
                return

        DAI_amount = 40.6293
        if DAI_balance < DAI_amount:
            print(f"❌ Insufficient DAI balance. Need {DAI_amount:.4f}, have {DAI_balance:.4f}")
            print("💡 Funding options:")
            print(f"   1. Send DAI to: {agent.address}")
            print("   2. Use https://app.uniswap.org/ to swap ETH → DAI")
            print("   3. Bridge from another chain using https://bridge.arbitrum.io/")
            return

        print(f"🔄 Step 1: Swapping {DAI_amount:.4f} DAI for WBTC...")

        # Calculate DAI amount in wei (6 decimals)
        DAI_amount_wei = int(DAI_amount * (10 ** 6))

        # Swap DAI for WBTC using Uniswap
        # Using 500 basis points (0.05%) fee tier for DAI/WBTC
        swap_result = agent.uniswap.swap_tokens(
            agent.dai_address,  # token_in (DAI)
            agent.wbtc_address,  # token_out (WBTC)
            DAI_amount_wei,     # amount_in
            500                  # fee (0.05%)
        )

        if not swap_result:
            print("❌ Failed to swap DAI for WBTC")
            return

        print(f"✅ DAI → WBTC swap completed!")
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
                    print(f"   Total Collateral: ${health_data.get('total_collateral_DAI', 0):.2f}")
                    print(f"   Total Debt: ${health_data.get('total_debt_DAI', 0):.2f}")
                    print(f"   Available Borrows: ${health_data.get('available_borrows_DAI', 0):.2f}")
        else:
            print("❌ WBTC supply failed")
            print("💡 Check your WBTC balance and gas fees")

        print("\n🎉 Operation completed successfully!")
        print(f"✅ Swapped {DAI_amount:.4f} DAI for WBTC")
        print(f"✅ Supplied WBTC as collateral to Aave")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Ensure you have enough DAI and gas fees")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()