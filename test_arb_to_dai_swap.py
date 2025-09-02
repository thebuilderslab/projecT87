
#!/usr/bin/env python3
"""
Dedicated test for ARB to DAI swap verification
Tests the bidirectional swap capability of the system
"""

import os
import time
import sys
import traceback
from datetime import datetime

def test_arb_for_dai():
    """Test ARB to DAI swap operation with comprehensive validation"""
    print("🔄 TESTING ARB → DAI SWAP")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    try:
        # Initialize agent
        print("\n🤖 Initializing agent...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: Chain ID {agent.w3.eth.chain_id}")
        
        # Initialize integrations
        print("\n🔧 Initializing DeFi integrations...")
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        print("✅ All integrations initialized successfully")
        
        # Check initial balances
        print("\n📊 INITIAL BALANCES:")
        try:
            arb_balance = agent.get_arb_balance()
            dai_balance = agent.get_dai_balance()
            eth_balance = agent.get_eth_balance()
            
            print(f"   ARB: {arb_balance:.6f}")
            print(f"   DAI: {dai_balance:.6f}")
            print(f"   ETH: {eth_balance:.6f}")
            
            if eth_balance < 0.001:
                print("❌ Insufficient ETH for gas fees")
                return False
                
        except Exception as balance_error:
            print(f"❌ Balance check failed: {balance_error}")
            return False
        
        # Ensure we have ARB to swap
        if arb_balance < 0.001:
            print("⚠️ Insufficient ARB balance for swap test")
            
            # Try to get some ARB through a DAI swap first
            if dai_balance > 1.0:
                print("🔄 Converting small DAI to ARB for test setup...")
                setup_swap_amount = min(1.0, dai_balance * 0.1)
                
                try:
                    setup_result = agent.uniswap.swap_dai_for_arb(setup_swap_amount)
                    if setup_result and setup_result.get('success'):
                        print("✅ Setup DAI→ARB swap successful")
                        time.sleep(5)  # Wait for confirmation
                        arb_balance = agent.get_arb_balance()
                        print(f"   New ARB balance: {arb_balance:.6f}")
                    else:
                        print("❌ Could not acquire ARB for test")
                        return False
                        
                except Exception as setup_error:
                    print(f"❌ Setup swap failed: {setup_error}")
                    return False
            else:
                print("❌ Insufficient DAI to acquire ARB for test")
                return False
        
        # Calculate test swap amount
        swap_amount = min(0.01, arb_balance * 0.1)  # Use 10% or 0.01 ARB max
        print(f"\n🎯 EXECUTING ARB → DAI SWAP: {swap_amount:.6f} ARB")
        
        # Verify Uniswap integration
        if not hasattr(agent, 'uniswap') or not agent.uniswap:
            print("❌ Uniswap integration not available")
            return False
            
        # Verify swap method exists
        if not hasattr(agent.uniswap, 'swap_arb_for_dai'):
            print("❌ swap_arb_for_dai method not available")
            return False
        
        # Execute the ARB to DAI swap
        try:
            print("🔄 Initiating ARB → DAI swap...")
            swap_result = agent.uniswap.swap_arb_for_dai(swap_amount)
            
            if swap_result and swap_result.get('success'):
                tx_hash = swap_result.get('tx_hash')
                print(f"✅ APPROVED SWAP: ARB → DAI")
                print(f"📋 Transaction Hash: {tx_hash}")
                print(f"🔗 Verify on Arbiscan: https://arbiscan.io/tx/{tx_hash}")
                print(f"💰 Amount swapped: {swap_amount:.6f} ARB")
                
                # Wait for transaction confirmation
                print("⏳ Waiting for transaction confirmation...")
                time.sleep(10)
                
                # Check final balances
                print("\n📊 FINAL BALANCES:")
                final_arb = agent.get_arb_balance()
                final_dai = agent.get_dai_balance()
                
                arb_change = final_arb - arb_balance
                dai_change = final_dai - dai_balance
                
                print(f"   ARB: {final_arb:.6f} (change: {arb_change:+.6f})")
                print(f"   DAI: {final_dai:.6f} (change: {dai_change:+.6f})")
                
                # Verify swap occurred correctly
                if arb_change < -0.0001 and dai_change > 0.0001:
                    print("✅ ARB → DAI SWAP VERIFIED SUCCESSFUL")
                    print("🎉 Balance changes confirm successful token exchange")
                    return True
                else:
                    print("⚠️ Balance changes do not reflect expected swap")
                    print(f"   Expected: ARB decrease, DAI increase")
                    print(f"   Actual: ARB {arb_change:+.6f}, DAI {dai_change:+.6f}")
                    return False
                    
            else:
                print("❌ ARB → DAI swap failed")
                print(f"   Swap result: {swap_result}")
                return False
                
        except Exception as swap_error:
            print(f"❌ ARB → DAI swap execution error: {swap_error}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Test failed with critical error: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test execution with comprehensive reporting"""
    print("🧪 ARB TO DAI SWAP VERIFICATION TEST")
    print("=" * 60)
    
    test_start_time = datetime.now()
    print(f"📅 Test started: {test_start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Run the test
    success = test_arb_for_dai()
    
    test_end_time = datetime.now()
    test_duration = test_end_time - test_start_time
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"📅 Test completed: {test_end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"⏱️ Test duration: {test_duration.total_seconds():.1f} seconds")
    
    if success:
        print("✅ ARB → DAI SWAP TEST: PASSED")
        print("🎉 Bidirectional swap capability CONFIRMED")
        print("🚀 System ready for full deployment")
    else:
        print("❌ ARB → DAI SWAP TEST: FAILED")
        print("⚠️ Bidirectional swap capability NOT confirmed")
        print("🔧 Manual intervention required")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
