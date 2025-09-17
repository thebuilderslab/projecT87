#!/usr/bin/env python3
"""
Debt Swap Test Runner - Live test execution
"""

from production_debt_swap_executor import ProductionDebtSwapExecutor
import os
import time

def main():
    print('🧪 DEBT SWAP TEST EXECUTION')
    print('=' * 50)

    try:
        # Initialize executor
        print('📦 Initializing Production Debt Swap Executor...')
        executor = ProductionDebtSwapExecutor()
        print(f'✅ Executor initialized: {executor.user_address}')
        
        # Check current position
        print('\n📊 Checking current Aave position...')
        position = executor.get_aave_position()
        print(f'📊 Current Position:')
        print(f'   Health Factor: {position.get("health_factor", 0):.4f}')
        print(f'   Total Debt: ${position.get("total_debt_usd", 0):.2f}')
        print(f'   Total Collateral: ${position.get("total_collateral_usd", 0):.2f}')
        
        # Validate position is safe for testing
        health_factor = position.get("health_factor", 0)
        if health_factor < 1.5:
            print(f'⚠️ Health factor {health_factor:.4f} too low for testing. Minimum 1.5 required.')
            return
            
        # Test with minimum safe amount ($30 - above $25 minimum)
        test_amount = 30.0
        print(f'\n🚀 EXECUTING DEBT SWAP TEST: ${test_amount}')
        print(f'Direction: DAI debt → ARB debt')
        print(f'Using unified validation & gas optimization system')
        
        # Execute the debt swap with unified system
        start_time = time.time()
        result = executor.execute_debt_swap('DAI', 'ARB', test_amount)
        execution_time = time.time() - start_time
        
        # Display results
        print(f'\n📊 TEST RESULTS:')
        print(f'=' * 30)
        print(f'Success: {result.get("success", False)}')
        print(f'Execution Time: {execution_time:.2f}s')
        print(f'Transaction Hash: {result.get("transaction_hash", "N/A")}')
        
        # Enhanced gas parameters
        if result.get('gas_optimization'):
            gas_info = result['gas_optimization']
            if gas_info.get('final_params'):
                params = gas_info['final_params']
                print(f'Gas Limit: {params.get("gas", 0):,}')
                print(f'Gas Price: {params.get("gasPrice", 0):,} wei')
                print(f'Est. Cost: ${params.get("estimated_cost_usd", 0):.4f} USD')
                print(f'Budget Capped: {params.get("budget_capped", False)}')
        
        # Root-cause validation results
        if result.get('root_cause_validation'):
            validation = result['root_cause_validation']
            print(f'\n🔧 Root-Cause Validation:')
            print(f'   Overall Success: {validation.get("success", False)}')
            print(f'   Signature Valid: {validation.get("signature_valid", False)}')
            print(f'   Calldata Valid: {validation.get("calldata_valid", False)}')
            print(f'   Amount Valid: {validation.get("amount_valid", False)}')
        
        # Error reporting
        if result.get('error'):
            print(f'\n❌ Error: {result["error"]}')
            
            # Show full diagnostics on error
            if result.get('full_mismatch_diagnostics'):
                diagnostics = result['full_mismatch_diagnostics']
                print(f'\n🔍 Full Diagnostics:')
                print(f'   Function Selector: {diagnostics.get("function_selector", "N/A")}')
                print(f'   Signature Analysis: {diagnostics.get("mismatch_analysis", {})}')
        
        # Final status message
        final_status = result.get('final_status', 'EXECUTION INCOMPLETE')
        if result.get('success'):
            print(f'\n🎉 {final_status}')
        else:
            print(f'\n⚠️ Test completed with issues - see error details above')
            
        # Generate and save diagnostic report
        if hasattr(executor, 'generate_diagnostic_report'):
            print(f'\n📋 Generating diagnostic report...')
            report = executor.generate_diagnostic_report(result)
            
            # Save report to file
            timestamp = int(time.time())
            report_file = f'debt_swap_test_report_{timestamp}.txt'
            with open(report_file, 'w') as f:
                f.write(report)
            print(f'📄 Report saved to: {report_file}')
            
            # Show summary
            print(f'\n📋 DIAGNOSTIC SUMMARY:')
            print('=' * 50)
            lines = report.split('\n')
            # Show last 10 meaningful lines
            meaningful_lines = [line for line in lines[-15:] if line.strip() and '=' not in line]
            for line in meaningful_lines[-8:]:
                print(line)
                
    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()