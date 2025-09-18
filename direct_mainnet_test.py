#!/usr/bin/env python3
"""
DIRECT MAINNET DEBT SWAP TEST
Simplified approach for executing comprehensive debt swap validation
"""

import os
import time
import json
from datetime import datetime

def execute_direct_mainnet_test():
    """Execute direct mainnet debt swap test"""
    
    print("🚀 DIRECT MAINNET DEBT SWAP TEST")
    print("=" * 80)
    
    test_results = {
        'test_id': f"direct_test_{int(time.time())}",
        'start_time': datetime.now().isoformat(),
        'test_parameters': {
            'from_asset': 'DAI',
            'to_asset': 'ARB',
            'swap_amount_usd': 25.0
        },
        'execution_results': None,
        'critical_fixes_validated': False,
        'production_ready': False
    }
    
    try:
        # Import and initialize the production executor
        from production_debt_swap_executor import ProductionDebtSwapExecutor
        
        print("🔧 Initializing Production Debt Swap Executor...")
        executor = ProductionDebtSwapExecutor()
        
        print(f"✅ Executor initialized for: {executor.user_address}")
        print(f"   Network: Arbitrum Mainnet")
        print(f"   Aave Debt Switch V3: {executor.aave_debt_switch_v3}")
        
        # Get initial position
        print("\n📊 VALIDATING INITIAL POSITION")
        print("-" * 50)
        initial_position = executor.get_aave_position()
        
        if not initial_position:
            raise Exception("Could not fetch initial position")
            
        dai_debt = initial_position['debt_balances'].get('DAI', 0)
        health_factor = initial_position.get('health_factor', 0)
        
        print(f"   DAI Debt: {dai_debt:.2f} DAI")
        print(f"   Health Factor: {health_factor:.6f}")
        print(f"   Available Borrows: ${initial_position['available_borrows_usd']:.2f}")
        
        if dai_debt < 25.0:
            raise Exception(f"Insufficient DAI debt: {dai_debt:.2f} < 25.0")
        if health_factor < 1.5:
            raise Exception(f"Health factor too low: {health_factor:.6f} < 1.5")
            
        # Execute comprehensive debt swap
        print(f"\n🚀 EXECUTING COMPREHENSIVE DEBT SWAP")
        print("-" * 50)
        print(f"   Operation: DAI debt → ARB debt")
        print(f"   Amount: ${test_results['test_parameters']['swap_amount_usd']}")
        
        execution_start = time.time()
        
        # Call the main execution method
        execution_result = executor.execute_debt_swap(
            from_asset='DAI',
            to_asset='ARB', 
            swap_amount_usd=25.0
        )
        
        execution_duration = int((time.time() - execution_start) * 1000)
        test_results['execution_results'] = execution_result
        test_results['execution_duration_ms'] = execution_duration
        
        print(f"\n📊 EXECUTION COMPLETED IN {execution_duration}ms")
        
        # Validate critical fixes
        print(f"\n🔍 VALIDATING CRITICAL FIXES")
        print("-" * 50)
        
        fixes_validated = validate_fixes_in_execution(execution_result)
        test_results['critical_fixes_validated'] = fixes_validated
        
        # Assess production readiness
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT")
        print("-" * 50)
        
        production_score = calculate_readiness_score(test_results)
        test_results['production_readiness_score'] = production_score
        test_results['production_ready'] = production_score >= 80
        
        print(f"   Production Score: {production_score}/100")
        print(f"   Transaction Success: {execution_result.get('success', False)}")
        print(f"   Transaction Hash: {execution_result.get('transaction_hash', 'N/A')}")
        print(f"   Critical Fixes Applied: {fixes_validated}")
        print(f"   Production Ready: {test_results['production_ready']}")
        
        if execution_result.get('transaction_hash'):
            arbitrum_explorer = f"https://arbiscan.io/tx/{execution_result['transaction_hash']}"
            print(f"   🔗 Arbitrum Explorer: {arbitrum_explorer}")
            test_results['verification_link'] = arbitrum_explorer
        
        # Save results
        test_results['end_time'] = datetime.now().isoformat()
        test_results['test_success'] = execution_result.get('success', False)
        
        # Write results to file
        results_file = f"direct_test_results_{test_results['test_id']}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved: {results_file}")
        
        return test_results
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        test_results['error'] = str(e)
        test_results['test_success'] = False
        test_results['end_time'] = datetime.now().isoformat()
        return test_results

def validate_fixes_in_execution(execution_result):
    """Validate that all critical fixes are applied"""
    
    print("   Checking critical fixes implementation...")
    
    fixes_status = {
        'offset_288': False,
        'zeroed_permits': False,
        'enhanced_validation': False,
        'resilient_dependencies': False
    }
    
    # Check if execution has comprehensive logging (indicates fixes applied)
    if execution_result.get('comprehensive_logging'):
        print("   ✅ Comprehensive logging present")
        
        # Check for offset parameter
        contract_params = execution_result.get('comprehensive_logging', {}).get('contract_interaction', {}).get('transaction_params', {})
        if contract_params.get('offset') == 288:
            fixes_status['offset_288'] = True
            print("   ✅ Offset=288 validated")
        
        # Check for permit zeroing
        if contract_params.get('permits_zeroed', False):
            fixes_status['zeroed_permits'] = True
            print("   ✅ Zeroed permits validated")
        
        # Check for enhanced validation
        validation_logs = execution_result.get('comprehensive_logging', {}).get('validation', {})
        if validation_logs.get('total_validations', 0) >= 6:
            fixes_status['enhanced_validation'] = True
            print("   ✅ Enhanced validation validated")
        
        # Check system resilience (successful execution regardless of API availability)
        if execution_result.get('success', False):
            fixes_status['resilient_dependencies'] = True
            print("   ✅ Resilient dependencies validated")
    
    # Check if execution has step-wise logging (indicates comprehensive implementation)
    if execution_result.get('stepwise_diff') and len(execution_result['stepwise_diff'].get('step_by_step_log', [])) >= 6:
        print("   ✅ Complete 6-step process validated")
    
    all_fixes_applied = all(fixes_status.values())
    
    if all_fixes_applied:
        print("   ✅ ALL CRITICAL FIXES VALIDATED")
    else:
        failed_fixes = [fix for fix, status in fixes_status.items() if not status]
        print(f"   ❌ Missing fixes: {', '.join(failed_fixes)}")
    
    return all_fixes_applied

def calculate_readiness_score(test_results):
    """Calculate production readiness score"""
    
    score = 0
    
    # Transaction execution (40 points)
    if test_results.get('test_success', False):
        score += 40
        print(f"   +40 points: Transaction executed successfully")
    
    # Critical fixes applied (40 points)
    if test_results.get('critical_fixes_validated', False):
        score += 40
        print(f"   +40 points: All critical fixes validated")
    
    # Performance (10 points)
    duration = test_results.get('execution_duration_ms', 999999)
    if duration < 60000:  # Under 60 seconds
        score += 10
        print(f"   +10 points: Fast execution ({duration}ms)")
    
    # Real transaction hash (10 points)
    execution_result = test_results.get('execution_results', {})
    if execution_result.get('transaction_hash'):
        score += 10
        print(f"   +10 points: Real transaction hash generated")
    
    return min(score, 100)

if __name__ == "__main__":
    print("🚀 Starting Direct Mainnet Test...")
    results = execute_direct_mainnet_test()
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    print("=" * 80)
    print(f"Test Success: {results.get('test_success', False)}")
    print(f"Production Score: {results.get('production_readiness_score', 0)}/100")
    print(f"Production Ready: {results.get('production_ready', False)}")
    
    if results.get('verification_link'):
        print(f"Verification: {results['verification_link']}")
    
    print("=" * 80)