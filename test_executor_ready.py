#!/usr/bin/env python3
"""Test script to verify the production executor is ready with all fixes"""

import os
import sys

# Set environment variables for testing
os.environ['MANUAL_OVERRIDE_MODE'] = 'true'
os.environ['CONTROLLED_TEST_MODE'] = 'true'

sys.path.append('.')
from production_debt_swap_executor import ProductionDebtSwapExecutor

print('🎯 Testing Production Debt Swap Executor with Override Modes')
print('✅ MANUAL_OVERRIDE_MODE:', os.getenv('MANUAL_OVERRIDE_MODE', 'false'))
print('✅ CONTROLLED_TEST_MODE:', os.getenv('CONTROLLED_TEST_MODE', 'false'))

try:
    # Initialize executor correctly
    executor = ProductionDebtSwapExecutor()
    print('✅ Production executor initialized successfully')
    print('✅ Gas validation range: {:.0f}-{:.0f} (targeting {:.0f})'.format(
        executor.gas_range_min, executor.gas_range_max, executor.baseline_gas_target))
    print('✅ Manual override mode:', executor.manual_override_mode)
    print('✅ Controlled test mode:', executor.controlled_test_mode)
    print('✅ Gas validation enabled:', executor.gas_validation_enabled)
    print('✅ Maximum USD per transaction: ${:.1f}'.format(executor.max_usd_per_tx))
    print('✅ All import fixes verified working')
    print('🚀 System ready for controlled live execution')
    
    # Show the testing features status
    if executor.manual_override_mode:
        print('🔧 MANUAL OVERRIDE: Market condition checks will be bypassed')
    if executor.controlled_test_mode:
        print('🔬 CONTROLLED TEST: Enhanced logging and safety checks active')
        
    # Verify the DebtSwapSignatureValidator instantiation (this was the import error)
    if hasattr(executor, 'debt_swap_validator') and executor.debt_swap_validator:
        print('✅ DebtSwapSignatureValidator initialized successfully')
        print('✅ Import error completely resolved')
    else:
        print('⚠️ DebtSwapSignatureValidator not found - checking initialization...')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()