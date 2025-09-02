
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
