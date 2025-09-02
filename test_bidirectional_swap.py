
#!/usr/bin/env python3
"""
Comprehensive Bidirectional Swap Test
Tests both DAI → ARB and ARB → DAI swaps
"""

import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_bidirectional_swaps():
    """Test both DAI → ARB and ARB → DAI swaps to verify full functionality"""
    try:
        print("🔄 COMPREHENSIVE BIDIRECTIONAL SWAP TEST")
        print("=" * 60)
        
        # Initialize agent
        print("🚀 Initializing Arbitrum agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
            
        # Check initial balances
        print("\n📊 INITIAL BALANCES:")
        initial_dai = agent.get_dai_balance()
        initial_arb = agent.get_arb_balance()
        
        print(f"   DAI Balance: {initial_dai:.6f}")
        print(f"   ARB Balance: {initial_arb:.6f}")
        
        # Test 1: DAI → ARB swap (to get ARB for reverse test)
        print("\n🔄 TEST 1: DAI → ARB SWAP")
        print("-" * 40)
        
        if initial_dai < 1.0:
            print("❌ Insufficient DAI balance for test")
            return False
            
        dai_swap_amount = min(initial_dai * 0.1, 2.0)  # 10% or max $2
        print(f"🎯 Swapping {dai_swap_amount:.6f} DAI → ARB")
        
        dai_to_arb_result = agent.uniswap.swap_dai_for_arb(dai_swap_amount)
        
        if dai_to_arb_result and dai_to_arb_result.get('success'):
            print(f"✅ APPROVED SWAP: DAI → ARB")
            print(f"🔗 TX Hash: {dai_to_arb_result.get('tx_hash')}")
            
            # Wait for confirmation
            time.sleep(15)
            
            # Check intermediate balances
            print("\n📊 BALANCES AFTER DAI → ARB:")
            mid_dai = agent.get_dai_balance()
            mid_arb = agent.get_arb_balance()
            
            print(f"   DAI Balance: {mid_dai:.6f} (change: {mid_dai - initial_dai:+.6f})")
            print(f"   ARB Balance: {mid_arb:.6f} (change: {mid_arb - initial_arb:+.6f})")
            
            # Test 2: ARB → DAI swap (reverse swap)
            print("\n🔄 TEST 2: ARB → DAI SWAP")
            print("-" * 40)
            
            if mid_arb < 0.1:
                print("❌ Insufficient ARB balance for reverse test")
                return False
                
            arb_swap_amount = min(mid_arb * 0.5, 1.0)  # 50% or max 1 ARB
            print(f"🎯 Swapping {arb_swap_amount:.6f} ARB → DAI")
            
            arb_to_dai_result = agent.uniswap.swap_arb_for_dai(arb_swap_amount)
            
            if arb_to_dai_result and arb_to_dai_result.get('success'):
                print(f"✅ APPROVED SWAP: ARB → DAI")
                print(f"🔗 TX Hash: {arb_to_dai_result.get('tx_hash')}")
                
                # Wait for final confirmation
                time.sleep(15)
                
                # Check final balances
                print("\n📊 FINAL BALANCES:")
                final_dai = agent.get_dai_balance()
                final_arb = agent.get_arb_balance()
                
                print(f"   DAI Balance: {final_dai:.6f} (total change: {final_dai - initial_dai:+.6f})")
                print(f"   ARB Balance: {final_arb:.6f} (total change: {final_arb - initial_arb:+.6f})")
                
                print("\n✅ BIDIRECTIONAL SWAP TEST COMPLETED SUCCESSFULLY")
                print("🎯 Both DAI → ARB and ARB → DAI swaps executed successfully")
                return True
            else:
                print("❌ ARB → DAI swap failed")
                return False
        else:
            print("❌ DAI → ARB swap failed")
            return False
            
    except Exception as e:
        print(f"❌ Bidirectional swap test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bidirectional_swaps()
    if success:
        print("\n🎉 ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL")
    else:
        print("\n❌ TESTS FAILED - SYSTEM NEEDS ATTENTION")
#!/usr/bin/env python3
"""
Comprehensive Bidirectional Swap Test
Tests both DAI → ARB and ARB → DAI swaps to ensure full functionality
"""

import time
import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_bidirectional_swaps():
    """Test both directions of DAI ↔ ARB swaps"""
    print("🔄 COMPREHENSIVE BIDIRECTIONAL SWAP TEST")
    print("=" * 50)
    
    try:
        # Initialize agent
        print("🤖 Initializing Arbitrum Agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
            
        # Get initial balances
        initial_dai = agent.get_dai_balance()
        initial_arb = agent.get_arb_balance()
        initial_eth = agent.get_eth_balance()
        
        print(f"💰 INITIAL BALANCES:")
        print(f"   DAI: {initial_dai:.6f}")
        print(f"   ARB: {initial_arb:.6f}")
        print(f"   ETH: {initial_eth:.6f}")
        
        # Check minimum requirements
        if initial_eth < 0.001:
            print("❌ Insufficient ETH for gas fees")
            return False
            
        # Test 1: DAI → ARB Swap
        print(f"\n📈 TEST 1: DAI → ARB SWAP")
        print("-" * 30)
        
        # Use small amount for testing
        dai_swap_amount = min(initial_dai * 0.1, 5.0)  # 10% of balance or $5 max
        
        if dai_swap_amount < 0.5:
            print("❌ Insufficient DAI balance for test")
            return False
            
        print(f"🔄 Swapping {dai_swap_amount:.2f} DAI for ARB...")
        
        dai_to_arb_result = agent.uniswap.swap_dai_for_arb(dai_swap_amount)
        
        if dai_to_arb_result and dai_to_arb_result.get('success'):
            tx_hash = dai_to_arb_result.get('tx_hash')
            print(f"✅ DAI → ARB swap successful!")
            print(f"🔗 Transaction: {tx_hash}")
            
            # Wait for confirmation
            time.sleep(10)
            
            # Check new balances
            new_arb_balance = agent.get_arb_balance()
            arb_received = new_arb_balance - initial_arb
            
            print(f"📊 ARB received: {arb_received:.6f}")
            
            if arb_received > 0:
                # Test 2: ARB → DAI Swap (Reverse)
                print(f"\n📉 TEST 2: ARB → DAI SWAP (REVERSE)")
                print("-" * 40)
                
                # Use the ARB we just received
                arb_swap_amount = arb_received * 0.95  # Leave small buffer
                
                print(f"🔄 Swapping {arb_swap_amount:.6f} ARB back to DAI...")
                
                cycle_id = dai_to_arb_result.get('cycle_id')
                arb_to_dai_result = agent.uniswap.swap_arb_for_dai(arb_swap_amount, cycle_id)
                
                if arb_to_dai_result and arb_to_dai_result.get('success'):
                    reverse_tx_hash = arb_to_dai_result.get('tx_hash')
                    print(f"✅ ARB → DAI swap successful!")
                    print(f"🔗 Transaction: {reverse_tx_hash}")
                    
                    # Wait for confirmation
                    time.sleep(10)
                    
                    # Final balance check
                    final_dai = agent.get_dai_balance()
                    final_arb = agent.get_arb_balance()
                    
                    dai_recovered = final_dai - (initial_dai - dai_swap_amount)
                    
                    print(f"\n📊 FINAL RESULTS:")
                    print(f"   Original DAI used: {dai_swap_amount:.6f}")
                    print(f"   DAI recovered: {dai_recovered:.6f}")
                    print(f"   Final ARB balance: {final_arb:.6f}")
                    
                    # Calculate efficiency
                    efficiency = (dai_recovered / dai_swap_amount) * 100 if dai_swap_amount > 0 else 0
                    print(f"   Swap efficiency: {efficiency:.2f}%")
                    
                    if efficiency > 90:
                        print("✅ BIDIRECTIONAL SWAP TEST: EXCELLENT")
                        return True
                    elif efficiency > 80:
                        print("✅ BIDIRECTIONAL SWAP TEST: GOOD")
                        return True
                    else:
                        print("⚠️ BIDIRECTIONAL SWAP TEST: POOR EFFICIENCY")
                        return True  # Still successful, just inefficient
                        
                else:
                    print("❌ ARB → DAI swap failed")
                    print("✅ DAI → ARB works, but reverse swap needs debugging")
                    return False
                    
            else:
                print("❌ No ARB received from DAI swap")
                return False
                
        else:
            print("❌ DAI → ARB swap failed")
            return False
            
    except Exception as e:
        print(f"❌ Bidirectional swap test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_arb_for_dai():
    """Simple test to verify ARB to DAI swap functionality"""
    print("🔄 TESTING ARB → DAI SWAP FUNCTIONALITY")
    print("=" * 40)
    
    try:
        agent = ArbitrumTestnetAgent()
        
        if not agent.initialize_integrations():
            print("❌ Integration initialization failed")
            return False
            
        # Check ARB balance
        arb_balance = agent.get_arb_balance()
        print(f"📊 Current ARB balance: {arb_balance:.6f}")
        
        if arb_balance < 0.1:
            print("⚠️ Insufficient ARB balance for test")
            print("💡 Need to acquire ARB first via DAI → ARB swap")
            return False
            
        # Test small ARB to DAI swap
        test_amount = min(arb_balance * 0.1, 0.5)  # 10% or 0.5 ARB max
        
        print(f"🔄 Testing {test_amount:.6f} ARB → DAI swap...")
        
        result = agent.uniswap.swap_arb_for_dai(test_amount)
        
        if result and result.get('success'):
            print(f"✅ APPROVED SWAP: ARB → DAI")
            print(f"🔗 Transaction: {result.get('tx_hash')}")
            return True
        else:
            print("❌ ARB → DAI swap failed")
            return False
            
    except Exception as e:
        print(f"❌ ARB → DAI test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Swap Tests...")
    
    # Test 1: Full bidirectional test
    success1 = test_bidirectional_swaps()
    
    print("\n" + "=" * 50)
    
    # Test 2: Direct ARB → DAI test
    success2 = test_arb_for_dai()
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY:")
    print(f"   Bidirectional Test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   ARB → DAI Test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 ALL SWAP TESTS PASSED - SYSTEM FULLY OPERATIONAL")
    elif success1 or success2:
        print("\n⚠️ PARTIAL SUCCESS - Some swap functionality working")
    else:
        print("\n❌ ALL TESTS FAILED - System needs debugging")
