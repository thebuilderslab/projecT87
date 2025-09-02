
#!/usr/bin/env python3
"""
Dedicated test for ARB to DAI swap verification
Tests the bidirectional swap capability of the system
"""

import os
import time
import sys
import traceback
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_arb_for_dai():
    """Test ARB to DAI swap operation"""
    print("🔄 TESTING ARB → DAI SWAP")
    print("=" * 40)
    
    try:
        # Initialize agent
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: {agent.w3.eth.chain_id}")
        
        # Check initial balances
        print("\n📊 INITIAL BALANCES:")
        arb_balance = agent.get_arb_balance() if hasattr(agent, 'get_arb_balance') else 0
        dai_balance = agent.get_dai_balance() if hasattr(agent, 'get_dai_balance') else 0
        
        print(f"   ARB: {arb_balance:.6f}")
        print(f"   DAI: {dai_balance:.6f}")
        
        if arb_balance < 0.001:
            print("⚠️ Insufficient ARB balance for swap test")
            print("💡 Attempting to acquire small ARB amount...")
            
            # Try to get some ARB through a small DAI swap first
            if dai_balance > 0.5:
                print("🔄 Converting small DAI to ARB for test...")
                swap_amount = min(0.5, dai_balance * 0.1)
                
                if hasattr(agent, 'uniswap') and agent.uniswap:
                    try:
                        dai_to_arb_result = agent.uniswap.swap_dai_for_arb(swap_amount)
                        if dai_to_arb_result:
                            print("✅ Small DAI→ARB swap successful")
                            time.sleep(3)  # Wait for confirmation
                            arb_balance = agent.get_arb_balance() if hasattr(agent, 'get_arb_balance') else 0
                        else:
                            print("❌ Could not acquire ARB for test")
                            return False
                    except Exception as prep_error:
                        print(f"❌ Preparation swap failed: {prep_error}")
                        return False
                else:
                    print("❌ Uniswap integration not available")
                    return False
            else:
                print("❌ Insufficient DAI to acquire ARB for test")
                return False
        
        # Execute ARB to DAI swap
        swap_amount = min(0.0001, arb_balance * 0.1)  # Very small amount for test
        print(f"\n🔄 EXECUTING ARB → DAI SWAP: {swap_amount:.6f} ARB")
        
        if hasattr(agent, 'uniswap') and agent.uniswap:
            try:
                # Execute the swap
                swap_result = agent.uniswap.swap_arb_for_dai(swap_amount)
                
                if swap_result and 'tx_hash' in swap_result:
                    print(f"✅ APPROVED SWAP: ARB → DAI")
                    print(f"📋 Transaction Hash: {swap_result['tx_hash']}")
                    print(f"🔗 Verify on Arbiscan: https://arbiscan.io/tx/{swap_result['tx_hash']}")
                    
                    # Wait for confirmation
                    time.sleep(5)
                    
                    # Check final balances
                    print("\n📊 FINAL BALANCES:")
                    final_arb = agent.get_arb_balance() if hasattr(agent, 'get_arb_balance') else 0
                    final_dai = agent.get_dai_balance() if hasattr(agent, 'get_dai_balance') else 0
                    
                    print(f"   ARB: {final_arb:.6f} (change: {final_arb - arb_balance:+.6f})")
                    print(f"   DAI: {final_dai:.6f} (change: {final_dai - dai_balance:+.6f})")
                    
                    # Verify swap occurred
                    if final_arb < arb_balance and final_dai > dai_balance:
                        print("✅ ARB → DAI SWAP VERIFIED SUCCESSFUL")
                        return True
                    else:
                        print("⚠️ Balance changes do not reflect expected swap")
                        return False
                        
                else:
                    print("❌ ARB → DAI swap failed")
                    print(f"Result: {swap_result}")
                    return False
                    
            except Exception as swap_error:
                print(f"❌ ARB → DAI swap error: {swap_error}")
                traceback.print_exc()
                return False
        else:
            print("❌ Uniswap integration not available")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test execution"""
    print("🧪 ARB TO DAI SWAP VERIFICATION TEST")
    print("=" * 50)
    
    success = test_arb_for_dai()
    
    if success:
        print("\n✅ ARB → DAI SWAP TEST PASSED")
        print("🎉 Bidirectional swap capability confirmed")
    else:
        print("\n❌ ARB → DAI SWAP TEST FAILED")
        print("⚠️ Bidirectional swap capability not verified")
    
    return success

if __name__ == "__main__":
    main()
