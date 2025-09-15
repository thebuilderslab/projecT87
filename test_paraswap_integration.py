#!/usr/bin/env python3
"""
Quick ParaSwap Integration Test
Test if the corrected API parameters resolve the 400 error
"""

import os
from corrected_debt_swap_executor import CorrectedDebtSwapExecutor

def test_paraswap_integration():
    """Test ParaSwap API integration in isolation"""
    print("🧪 TESTING PARASWAP API INTEGRATION")
    print("=" * 50)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
        
        print(f"✅ Agent initialized: {agent.address}")
        
        # Initialize executor
        executor = CorrectedDebtSwapExecutor(agent)
        
        # Test ParaSwap API call with corrected parameters
        print("\n🔄 Testing ParaSwap API with optimized parameters...")
        print("   Test: $10 DAI debt → ARB debt routing")
        
        # Convert $10 to DAI amount
        dai_amount = int(10 * 1e18)  # $10 DAI
        
        # Test the ParaSwap API call
        paraswap_result = executor.get_paraswap_calldata_reverse_routing(
            'DAI', 'ARB', dai_amount
        )
        
        if paraswap_result and 'calldata' in paraswap_result:
            print("✅ PARASWAP API INTEGRATION: SUCCESS!")
            print(f"   Expected Amount: {paraswap_result.get('expected_amount', 'N/A')}")
            print(f"   Calldata Length: {len(paraswap_result['calldata'])} chars")
            print(f"   Slippage: {paraswap_result.get('slippage_applied', 'N/A')}")
            
            # Test debt token discovery
            print("\n🔍 Testing debt token discovery...")
            arb_debt_token = executor.get_debt_token_address('ARB')
            if arb_debt_token:
                print(f"✅ ARB debt token: {arb_debt_token}")
            else:
                print("❌ Failed to get ARB debt token")
            
            return True
        else:
            print("❌ PARASWAP API INTEGRATION: FAILED")
            print(f"   Result: {paraswap_result}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"🔍 Full trace: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_paraswap_integration()
    
    if success:
        print("\n🎉 PARASWAP INTEGRATION TEST: PASSED")
        print("✅ The system can successfully get ParaSwap routing data")
        print("✅ Ready for real debt swap execution")
    else:
        print("\n❌ PARASWAP INTEGRATION TEST: FAILED")
        print("❌ API parameters need further adjustment")