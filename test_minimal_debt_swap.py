#!/usr/bin/env python3
"""
MINIMAL DEBT SWAP TEST
Test $2 DAI debt → ARB debt swap to prove pipeline works before full cycle
"""

import json
from production_debt_swap_executor import ProductionDebtSwapExecutor

def main():
    print("🧪 MINIMAL DEBT SWAP TEST")
    print("=" * 60)
    print("Testing $2 DAI debt → ARB debt swap to prove pipeline works")
    print("=" * 60)
    
    try:
        # Initialize executor
        executor = ProductionDebtSwapExecutor()
        
        # Test single debt swap - $2 amount
        test_amount = 2.0
        print(f"\n🔬 Executing test swap: ${test_amount} DAI debt → ARB debt")
        
        result = executor.execute_debt_swap('DAI', 'ARB', test_amount)
        
        print(f"\n📋 TEST RESULTS:")
        print("=" * 50)
        
        if result['success']:
            print(f"✅ SUCCESS: Debt swap executed successfully")
            print(f"   Transaction Hash: {result['transaction_hash']}")
            print(f"   Gas Used: {result['gas_used']:,}")
            print(f"   Gas Cost: {result['gas_cost_eth']:.6f} ETH")
            print(f"   Arbiscan Link: https://arbiscan.io/tx/{result['transaction_hash']}")
            
            # Show position changes
            if result.get('position_before') and result.get('position_after'):
                before = result['position_before']
                after = result['position_after']
                
                dai_debt_change = after['debt_balances']['DAI'] - before['debt_balances']['DAI']
                arb_debt_change = after['debt_balances']['ARB'] - before['debt_balances']['ARB']
                
                print(f"\n📊 POSITION CHANGES:")
                print(f"   DAI Debt Change: {dai_debt_change:.6f}")
                print(f"   ARB Debt Change: {arb_debt_change:.6f}")
                print(f"   Health Factor: {before['health_factor']:.6f} → {after['health_factor']:.6f}")
            
            # Save test results
            timestamp = result['start_time'].replace(':', '').replace('-', '').split('T')[0] + '_' + result['start_time'].replace(':', '').replace('-', '').split('T')[1].split('.')[0]
            filename = f"minimal_test_result_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\n📄 Test results saved to: {filename}")
            print(f"✅ MINIMAL TEST PASSED - Pipeline proven to work!")
            
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            
            # Save failure details for debugging
            with open('minimal_test_failure.json', 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"❌ MINIMAL TEST FAILED - Check failure details")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    main()