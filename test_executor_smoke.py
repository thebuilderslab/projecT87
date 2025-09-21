#!/usr/bin/env python3
"""
SMOKE TEST: Production Debt Swap Executor
Verifies that the critical import fixes work and executor instantiation succeeds
"""

import os
import sys
from datetime import datetime

def run_smoke_test():
    """Run comprehensive smoke test for ProductionDebtSwapExecutor"""
    
    print("🔧 SMOKE TEST: Production Debt Swap Executor")
    print("=" * 60)
    print(f"Test Time: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    
    test_results = {
        'import_test': False,
        'instantiation_test': False,
        'validator_test': False,
        'method_access_test': False,
        'overall_success': False
    }
    
    # Test 1: Import Test
    print(f"\n📋 TEST 1: Import Resolution")
    try:
        from production_debt_swap_executor import ProductionDebtSwapExecutor
        print("✅ ProductionDebtSwapExecutor import successful")
        test_results['import_test'] = True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return test_results
    
    # Test 2: Instantiation Test (without private key for safety)
    print(f"\n📋 TEST 2: Safe Instantiation (Mocked)")
    try:
        # Check if we have a test private key for non-mainnet testing
        test_private_key = os.getenv('TEST_PRIVATE_KEY')
        if not test_private_key:
            # Use a dummy private key just for instantiation testing (not for real transactions)
            test_private_key = '0x' + '1' * 64  # Dummy key for testing only
        
        # Override RPC to use a testnet for safety
        os.environ['ARBITRUM_RPC_URL'] = os.getenv('ARBITRUM_TESTNET_RPC', 'https://sepolia-rollup.arbitrum.io/rpc')
        
        executor = ProductionDebtSwapExecutor(private_key=test_private_key)
        print("✅ Executor instantiation successful")
        print(f"   User Address: {executor.user_address}")
        print(f"   RPC Connected: {executor.w3.is_connected()}")
        print(f"   Validator Available: {executor.debt_swap_validator is not None}")
        test_results['instantiation_test'] = True
        
        # Test 3: Validator Integration Test
        print(f"\n📋 TEST 3: Validator Integration")
        if executor.debt_swap_validator:
            print("✅ DebtSwapSignatureValidator properly initialized")
            print(f"   Expected Signature: {executor.debt_swap_validator.expected_signature}")
            test_results['validator_test'] = True
        else:
            print("❌ Validator not properly initialized")
        
        # Test 4: Method Access Test
        print(f"\n📋 TEST 4: Critical Method Access")
        try:
            # Test that we can access the validator method
            if hasattr(executor.debt_swap_validator, 'resolve_gas_estimation_failure'):
                print("✅ resolve_gas_estimation_failure method accessible")
                test_results['method_access_test'] = True
            else:
                print("❌ resolve_gas_estimation_failure method not found")
        except Exception as e:
            print(f"❌ Method access failed: {e}")
            
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        return test_results
    
    # Overall Success Calculation
    passed_tests = sum(test_results.values())
    total_tests = len(test_results) - 1  # Exclude overall_success from count
    test_results['overall_success'] = passed_tests == total_tests
    
    print(f"\n📊 SMOKE TEST SUMMARY:")
    print("=" * 40)
    print(f"✅ Import Test: {'PASS' if test_results['import_test'] else 'FAIL'}")
    print(f"✅ Instantiation Test: {'PASS' if test_results['instantiation_test'] else 'FAIL'}")
    print(f"✅ Validator Test: {'PASS' if test_results['validator_test'] else 'FAIL'}")
    print(f"✅ Method Access Test: {'PASS' if test_results['method_access_test'] else 'FAIL'}")
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if test_results['overall_success'] else '❌ SOME TESTS FAILED'}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    return test_results

if __name__ == "__main__":
    results = run_smoke_test()
    
    # Exit with proper code
    if results['overall_success']:
        print("\n🚀 SMOKE TEST COMPLETE: System ready for enhanced testing")
        sys.exit(0)
    else:
        print("\n💥 SMOKE TEST FAILED: Critical issues detected")
        sys.exit(1)