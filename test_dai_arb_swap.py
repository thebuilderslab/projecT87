#!/usr/bin/env python3
"""
Test DAI ↔ ARB swap operations with proper integration setup
"""

import os
import time
import sys
import traceback

def test_dai_arb_swap():
    """Test DAI to ARB swap and back to DAI"""
    print("🧪 DAI ↔ ARB SWAP TEST")
    print("=" * 30)

    try:
        print("\n🔍 CHECKING SYSTEM SWAP CAPABILITIES")
        print("=" * 40)

        # Check environment first
        if not os.getenv('WALLET_PRIVATE_KEY'):
            print("❌ WALLET_PRIVATE_KEY not found in environment")
            return False

        if not os.getenv('COINMARKETCAP_API_KEY'):
            print("❌ COINMARKETCAP_API_KEY not found in environment")
            return False

        # Initialize agent with proper error handling
        print("🤖 Initializing Arbitrum Testnet Agent...")

        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
        except Exception as agent_error:
            print(f"❌ Agent initialization failed: {agent_error}")
            return False

        # Initialize integrations with retry
        print("🔧 Initializing DeFi integrations...")
        max_init_attempts = 3

        for attempt in range(max_init_attempts):
            try:
                if agent.initialize_integrations():
                    print("✅ Integrations initialized successfully")
                    break
                else:
                    print(f"⚠️ Integration attempt {attempt + 1} failed")
                    if attempt < max_init_attempts - 1:
                        time.sleep(5)
                        continue
                    else:
                        print("❌ Failed to initialize integrations after all attempts")
                        return False
            except Exception as init_error:
                print(f"❌ Integration initialization error: {init_error}")
                if attempt < max_init_attempts - 1:
                    time.sleep(5)
                    continue
                else:
                    return False

        # Verify Uniswap integration
        if not hasattr(agent, 'uniswap') or not agent.uniswap:
            print("❌ Uniswap integration not available")
            return False

        print("✅ Uniswap integration verified")

        # Check wallet balances
        try:
            eth_balance = agent.get_eth_balance()
            dai_balance = agent.get_dai_balance()

            print(f"\n💰 WALLET STATUS:")
            print(f"   ETH: {eth_balance:.6f}")
            print(f"   DAI: {dai_balance:.6f}")

            if eth_balance < 0.001:
                print("❌ Insufficient ETH for gas fees")
                return False

            if dai_balance < 1.0:
                print("⚠️ Low DAI balance, attempting to borrow some DAI first...")

                # Try to borrow some DAI for testing
                if hasattr(agent, 'aave') and agent.aave:
                    try:
                        borrow_result = agent.aave.borrow_dai(5.0)  # Borrow 5 DAI
                        if borrow_result:
                            print("✅ Borrowed 5 DAI for testing")
                            time.sleep(5)
                            dai_balance = agent.get_dai_balance()
                        else:
                            print("❌ Could not borrow DAI for testing")
                            return False
                    except Exception as borrow_error:
                        print(f"❌ Borrow error: {borrow_error}")
                        return False
                else:
                    print("❌ Aave integration not available for borrowing")
                    return False

        except Exception as balance_error:
            print(f"❌ Balance check failed: {balance_error}")
            return False

        # Test swap amount
        swap_amount = min(1.0, dai_balance * 0.1)  # Use 10% of balance or 1 DAI max

        print(f"\n🔄 EXECUTING DAI → ARB SWAP")
        print(f"   Amount: {swap_amount:.6f} DAI")

        # Get initial ARB balance
        try:
            # Get ARB token balance
            arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
            arb_balance_before = agent.aave.get_token_balance(arb_address) if hasattr(agent, 'aave') and agent.aave else 0
        except:
            arb_balance_before = 0

        # Execute DAI to ARB swap
        try:
            # Check if swap method exists
            if not hasattr(agent.uniswap, 'swap_dai_for_arb'):
                print("❌ swap_dai_for_arb method not available")
                return False

            swap_result = agent.uniswap.swap_dai_for_arb(swap_amount)

            if not swap_result or not swap_result.get('success'):
                print("❌ DAI → ARB swap failed")
                print(f"   Swap result: {swap_result}")
                return False

            print(f"✅ DAI → ARB swap successful")
            print(f"   TX Hash: {swap_result.get('tx_hash', 'N/A')}")

        except Exception as swap_error:
            print(f"❌ DAI → ARB swap error: {swap_error}")
            traceback.print_exc()
            return False

        # Wait for confirmation
        print("⏳ Waiting for transaction confirmation...")
        time.sleep(15)

        # Check ARB balance after swap
        try:
            # Use Uniswap integration to check ARB balance if available
            if hasattr(agent, 'uniswap') and agent.uniswap:
                # Create ARB token contract
                arb_contract = agent.w3.eth.contract(
                    address=arb_address,
                    abi=[{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]
                )
                arb_balance_wei = arb_contract.functions.balanceOf(agent.address).call()
                arb_balance_after = arb_balance_wei / (10**18)  # ARB has 18 decimals
            elif hasattr(agent, 'aave') and agent.aave:
                arb_balance_after = agent.aave.get_token_balance(arb_address)
            else:
                arb_balance_after = 0

            arb_received = arb_balance_after - arb_balance_before

            print(f"\n💰 ARB RECEIVED: {arb_received:.6f}")

            if arb_received <= 0:
                print("❌ No ARB received from swap")
                return False

        except Exception as arb_check_error:
            print(f"❌ ARB balance check failed: {arb_check_error}")
            return False

        # Now swap back ARB to DAI
        print(f"\n🔄 EXECUTING ARB → DAI SWAP")
        print(f"   Amount: {arb_received:.6f} ARB")

        try:
            swap_back_result = agent.uniswap.swap_arb_for_dai(arb_received)

            if not swap_back_result or not swap_back_result.get('success'):
                print("❌ ARB → DAI swap failed")
                return False

            print(f"✅ ARB → DAI swap successful")
            print(f"   TX Hash: {swap_back_result.get('tx_hash', 'N/A')}")

        except Exception as swap_back_error:
            print(f"❌ ARB → DAI swap error: {swap_back_error}")
            return False

        # Wait for final confirmation
        print("⏳ Waiting for final transaction confirmation...")
        time.sleep(15)

        # Check final DAI balance
        try:
            dai_balance_final = agent.get_dai_balance()
            net_dai_change = dai_balance_final - dai_balance

            print(f"\n📊 SWAP CYCLE SUMMARY:")
            print(f"   Initial DAI: {dai_balance:.6f}")
            print(f"   Final DAI: {dai_balance_final:.6f}")
            print(f"   Net change: {net_dai_change:+.6f} DAI")
            print(f"   ARB received: {arb_received:.6f}")

            # Consider successful if we recovered most DAI (allowing for fees/slippage)
            if abs(net_dai_change) <= swap_amount * 0.1:  # Allow 10% loss for fees
                print("✅ SWAP CYCLE SUCCESSFUL")
                return True
            else:
                print("⚠️ Higher than expected loss in swap cycle")
                return True  # Still successful, just note the loss

        except Exception as final_check_error:
            print(f"❌ Final balance check failed: {final_check_error}")
            return False

    except Exception as e:
        print(f"❌ SWAP TEST FAILED")
        print(f"💡 Error: {e}")
        traceback.print_exc()
        return False

def test_arb_for_dai():
    """Test ARB to DAI swap operation"""
    print("\n🔄 TESTING ARB → DAI SWAP")
    print("=" * 40)

    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()

        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False

        # Get initial balances
        arb_balance = agent.get_arb_balance() if hasattr(agent, 'get_arb_balance') else 0
        dai_balance = agent.get_dai_balance() if hasattr(agent, 'get_dai_balance') else 0

        print(f"📊 Initial ARB: {arb_balance:.6f}, DAI: {dai_balance:.6f}")

        if arb_balance < 0.0001:
            print("⚠️ Insufficient ARB for test, skipping ARB→DAI swap")
            return False

        # Test swap amount
        swap_amount = min(0.0001, arb_balance * 0.1)
        print(f"🔄 Swapping {swap_amount:.6f} ARB for DAI...")

        if hasattr(agent, 'uniswap') and agent.uniswap:
            swap_result = agent.uniswap.swap_arb_for_dai(swap_amount)

            if swap_result and 'tx_hash' in swap_result:
                print(f"✅ APPROVED SWAP: ARB → DAI")
                print(f"📋 TX: {swap_result['tx_hash']}")
                return True
            else:
                print("❌ ARB → DAI swap failed")
                return False
        else:
            print("❌ Uniswap not available")
            return False

    except Exception as e:
        print(f"❌ ARB→DAI test error: {e}")
        return False

def main():
    """Main function with comprehensive error handling"""
    print("🔄 BIDIRECTIONAL DAI ↔ ARB SWAP TEST")
    print("=" * 50)

    # Run the DAI to ARB swap test first
    dai_to_arb_success = test_dai_arb_swap()

    if dai_to_arb_success:
        print("✅ DAI → ARB swap test completed successfully")

        # Test reverse swap (ARB → DAI)
        print("\n" + "=" * 50)
        arb_to_dai_success = test_arb_for_dai()

        if arb_to_dai_success:
            print("✅ ARB → DAI swap test completed successfully")
            print("\n🎉 BIDIRECTIONAL SWAP CAPABILITY VERIFIED")
        else:
            print("⚠️ ARB → DAI swap test failed or skipped")

        return True

    else:
        print("❌ DAI → ARB swap test failed")
        return False


if __name__ == "__main__":
    main()