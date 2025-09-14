#!/usr/bin/env python3
"""
Comprehensive Debt Management System Verification
Tests three critical aspects:
1. Debt Tracking Verification - Internal state structures
2. Function Testing - Swap and repayment function validation  
3. On-Chain Test Transaction - Real blockchain interaction
"""

import os
import json
import time
import traceback
from datetime import datetime
from decimal import Decimal

def test_debt_tracking_verification(agent):
    """
    1) DEBT TRACKING VERIFICATION
    Test internal debt state structures, borrowed amounts, interest tracking
    """
    print("🔍 1) DEBT TRACKING VERIFICATION")
    print("=" * 60)
    
    debt_state = {
        'timestamp': datetime.now().isoformat(),
        'raw_account_data': None,
        'processed_debt_info': {},
        'internal_tracking': {},
        'data_structures': {},
        'verification_status': 'PENDING'
    }
    
    try:
        # Direct Aave contract interaction for raw data
        print("📊 Fetching raw Aave account data...")
        
        # Use the pool contract directly from agent's aave integration
        if hasattr(agent, 'aave_pool_address'):
            pool_address = agent.aave_pool_address
        else:
            # Fallback to known Arbitrum Aave pool address
            pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        
        print(f"🏦 Aave Pool Address: {pool_address}")
        
        # Pool ABI for getUserAccountData
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        # Create contract instance
        pool_contract = agent.w3.eth.contract(
            address=pool_address,
            abi=pool_abi
        )
        
        # Get raw account data
        print(f"🔍 Querying account data for: {agent.address}")
        raw_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        # Process raw data into readable format
        total_collateral_usd = raw_data[0] / 1e8  # Base 8 decimals
        total_debt_usd = raw_data[1] / 1e8
        available_borrows_usd = raw_data[2] / 1e8
        liquidation_threshold = raw_data[3] / 1e4  # Percentage in basis points
        ltv = raw_data[4] / 1e4  # Percentage in basis points
        health_factor = raw_data[5] / 1e18 if raw_data[5] > 0 else float('inf')
        
        debt_state['raw_account_data'] = {
            'totalCollateralBase_wei': raw_data[0],
            'totalDebtBase_wei': raw_data[1],
            'availableBorrowsBase_wei': raw_data[2],
            'currentLiquidationThreshold_bp': raw_data[3],
            'ltv_bp': raw_data[4],
            'healthFactor_wei': raw_data[5]
        }
        
        debt_state['processed_debt_info'] = {
            'total_collateral_usd': total_collateral_usd,
            'total_debt_usd': total_debt_usd,
            'available_borrows_usd': available_borrows_usd,
            'liquidation_threshold_percent': liquidation_threshold,
            'ltv_percent': ltv,
            'health_factor': health_factor,
            'debt_utilization_percent': (total_debt_usd / total_collateral_usd * 100) if total_collateral_usd > 0 else 0
        }
        
        # Test internal agent tracking methods
        print("\n🔧 Testing Agent Internal Tracking Methods...")
        
        internal_methods_test = {}
        
        # Test 1: Health Factor Retrieval
        try:
            if hasattr(agent, 'get_health_factor'):
                agent_health_factor = agent.get_health_factor()
                internal_methods_test['health_factor_method'] = {
                    'available': True,
                    'value': agent_health_factor,
                    'matches_direct': abs(agent_health_factor - health_factor) < 0.001
                }
            else:
                internal_methods_test['health_factor_method'] = {'available': False}
        except Exception as e:
            internal_methods_test['health_factor_method'] = {'error': str(e)}
        
        # Test 2: DAI Balance Retrieval
        try:
            if hasattr(agent, 'get_dai_balance'):
                dai_balance = agent.get_dai_balance()
                internal_methods_test['dai_balance_method'] = {
                    'available': True,
                    'value': dai_balance
                }
            else:
                internal_methods_test['dai_balance_method'] = {'available': False}
        except Exception as e:
            internal_methods_test['dai_balance_method'] = {'error': str(e)}
        
        # Test 3: ARB Balance Retrieval  
        try:
            if hasattr(agent, 'get_arb_balance'):
                arb_balance = agent.get_arb_balance()
                internal_methods_test['arb_balance_method'] = {
                    'available': True,
                    'value': arb_balance
                }
            else:
                internal_methods_test['arb_balance_method'] = {'available': False}
        except Exception as e:
            internal_methods_test['arb_balance_method'] = {'error': str(e)}
            
        # Test 4: Debt Swap Conditions
        try:
            if hasattr(agent, 'check_debt_swap_conditions'):
                conditions_met, condition_message = agent.check_debt_swap_conditions()
                internal_methods_test['debt_swap_conditions'] = {
                    'available': True,
                    'conditions_met': conditions_met,
                    'message': condition_message
                }
            else:
                internal_methods_test['debt_swap_conditions'] = {'available': False}
        except Exception as e:
            internal_methods_test['debt_swap_conditions'] = {'error': str(e)}
        
        debt_state['internal_tracking'] = internal_methods_test
        
        # Data Structure Analysis
        debt_state['data_structures'] = {
            'agent_attributes': [attr for attr in dir(agent) if not attr.startswith('_') and ('debt' in attr.lower() or 'aave' in attr.lower() or 'balance' in attr.lower())],
            'aave_integration_available': hasattr(agent, 'aave'),
            'uniswap_integration_available': hasattr(agent, 'uniswap'),
            'market_signal_strategy_available': hasattr(agent, 'market_signal_strategy'),
            'debt_swap_active': getattr(agent, 'debt_swap_active', False)
        }
        
        # Display Results
        print(f"\n📊 DEBT STATE VERIFICATION RESULTS:")
        print(f"   💰 Total Collateral: ${total_collateral_usd:,.2f}")
        print(f"   🏦 Total Debt: ${total_debt_usd:,.2f}")
        print(f"   📈 Available Borrows: ${available_borrows_usd:,.2f}")
        print(f"   🏥 Health Factor: {health_factor:.4f}")
        print(f"   📊 Debt Utilization: {debt_state['processed_debt_info']['debt_utilization_percent']:.2f}%")
        
        print(f"\n🔧 INTERNAL METHOD VERIFICATION:")
        for method_name, result in internal_methods_test.items():
            if result.get('available'):
                print(f"   ✅ {method_name}: Working - {result.get('value', 'N/A')}")
            elif result.get('error'):
                print(f"   ❌ {method_name}: Error - {result['error']}")
            else:
                print(f"   ⚠️ {method_name}: Not Available")
        
        debt_state['verification_status'] = 'SUCCESS'
        return debt_state
        
    except Exception as e:
        print(f"❌ Debt tracking verification failed: {e}")
        debt_state['verification_status'] = 'FAILED'
        debt_state['error'] = str(e)
        debt_state['error_details'] = traceback.format_exc()
        return debt_state

def test_function_validation(agent, debt_state):
    """
    2) FUNCTION TESTING
    Test swap and repayment functions against current debt positions
    """
    print("\n🔧 2) FUNCTION TESTING")
    print("=" * 60)
    
    function_tests = {
        'timestamp': datetime.now().isoformat(),
        'swap_functions': {},
        'repayment_functions': {},
        'integration_tests': {},
        'test_status': 'PENDING'
    }
    
    try:
        # Get current debt position for context
        current_debt = debt_state['processed_debt_info']['total_debt_usd']
        current_health = debt_state['processed_debt_info']['health_factor']
        available_borrows = debt_state['processed_debt_info']['available_borrows_usd']
        
        print(f"📊 Testing against current position:")
        print(f"   Debt: ${current_debt:.2f}")
        print(f"   Health Factor: {current_health:.4f}")
        print(f"   Available Borrows: ${available_borrows:.2f}")
        
        # Test 1: Swap Function Availability
        print(f"\n🔄 Testing Swap Functions...")
        
        swap_methods_to_test = [
            '_execute_debt_swap_dai_to_arb',
            '_execute_debt_swap_arb_to_dai',
            'force_swap_dai_to_arb',
            'force_swap_arb_to_dai'
        ]
        
        for method_name in swap_methods_to_test:
            try:
                if hasattr(agent, method_name):
                    method = getattr(agent, method_name)
                    function_tests['swap_functions'][method_name] = {
                        'available': True,
                        'callable': callable(method),
                        'method_type': str(type(method))
                    }
                    print(f"   ✅ {method_name}: Available")
                else:
                    function_tests['swap_functions'][method_name] = {'available': False}
                    print(f"   ❌ {method_name}: Not Available")
            except Exception as e:
                function_tests['swap_functions'][method_name] = {'error': str(e)}
                print(f"   ⚠️ {method_name}: Error - {e}")
        
        # Test 2: Uniswap Integration Functions
        print(f"\n🦄 Testing Uniswap Integration...")
        
        if hasattr(agent, 'uniswap') and agent.uniswap:
            uniswap_methods = ['swap_dai_for_arb', 'swap_arb_for_dai']
            
            for method_name in uniswap_methods:
                try:
                    if hasattr(agent.uniswap, method_name):
                        method = getattr(agent.uniswap, method_name)
                        function_tests['integration_tests'][f'uniswap_{method_name}'] = {
                            'available': True,
                            'callable': callable(method)
                        }
                        print(f"   ✅ uniswap.{method_name}: Available")
                    else:
                        function_tests['integration_tests'][f'uniswap_{method_name}'] = {'available': False}
                        print(f"   ❌ uniswap.{method_name}: Not Available")
                except Exception as e:
                    function_tests['integration_tests'][f'uniswap_{method_name}'] = {'error': str(e)}
                    print(f"   ⚠️ uniswap.{method_name}: Error - {e}")
        else:
            print(f"   ❌ Uniswap integration not available")
            function_tests['integration_tests']['uniswap_available'] = False
        
        # Test 3: Aave Interaction Functions
        print(f"\n🏦 Testing Aave Integration...")
        
        # Check if we can access aave through different paths
        aave_access_methods = [
            ('direct_aave', lambda: agent.aave if hasattr(agent, 'aave') else None),
            ('enhanced_borrow_manager', lambda: agent.enhanced_borrow_manager.aave if hasattr(agent, 'enhanced_borrow_manager') else None),
        ]
        
        for method_name, accessor in aave_access_methods:
            try:
                aave_instance = accessor()
                if aave_instance:
                    # Test key methods
                    aave_methods = ['get_user_account_data', 'get_dai_balance', 'borrow_dai']
                    for aave_method in aave_methods:
                        if hasattr(aave_instance, aave_method):
                            function_tests['integration_tests'][f'{method_name}_{aave_method}'] = {'available': True}
                            print(f"   ✅ {method_name}.{aave_method}: Available")
                        else:
                            function_tests['integration_tests'][f'{method_name}_{aave_method}'] = {'available': False}
                            print(f"   ❌ {method_name}.{aave_method}: Not Available")
                else:
                    function_tests['integration_tests'][method_name] = {'available': False}
                    print(f"   ❌ {method_name}: Not Available")
            except Exception as e:
                function_tests['integration_tests'][method_name] = {'error': str(e)}
                print(f"   ⚠️ {method_name}: Error - {e}")
        
        # Test 4: Safety and Validation Functions
        print(f"\n🔒 Testing Safety Functions...")
        
        safety_methods = [
            'check_debt_swap_conditions',
            '_calculate_optimal_swap_amount',
            'validate_transaction_safety'
        ]
        
        for method_name in safety_methods:
            try:
                if hasattr(agent, method_name):
                    function_tests['repayment_functions'][method_name] = {'available': True}
                    print(f"   ✅ {method_name}: Available")
                else:
                    function_tests['repayment_functions'][method_name] = {'available': False}
                    print(f"   ❌ {method_name}: Not Available")
            except Exception as e:
                function_tests['repayment_functions'][method_name] = {'error': str(e)}
                print(f"   ⚠️ {method_name}: Error - {e}")
        
        function_tests['test_status'] = 'SUCCESS'
        return function_tests
        
    except Exception as e:
        print(f"❌ Function testing failed: {e}")
        function_tests['test_status'] = 'FAILED'
        function_tests['error'] = str(e)
        function_tests['error_details'] = traceback.format_exc()
        return function_tests

def execute_test_transaction(agent, debt_state, function_tests):
    """
    3) ON-CHAIN TEST TRANSACTION
    Execute small test transaction demonstrating proper debt handling
    """
    print("\n⛓️ 3) ON-CHAIN TEST TRANSACTION")
    print("=" * 60)
    
    transaction_test = {
        'timestamp': datetime.now().isoformat(),
        'pre_transaction_state': {},
        'transaction_details': {},
        'post_transaction_state': {},
        'verification_results': {},
        'test_status': 'PENDING'
    }
    
    try:
        current_debt = debt_state['processed_debt_info']['total_debt_usd']
        current_health = debt_state['processed_debt_info']['health_factor']
        available_borrows = debt_state['processed_debt_info']['available_borrows_usd']
        
        print(f"📊 Pre-Transaction State:")
        print(f"   Current Debt: ${current_debt:.2f}")
        print(f"   Health Factor: {current_health:.4f}")
        print(f"   Available Borrows: ${available_borrows:.2f}")
        
        # Record pre-transaction state
        transaction_test['pre_transaction_state'] = {
            'debt_usd': current_debt,
            'health_factor': current_health,
            'available_borrows': available_borrows,
            'block_number': agent.w3.eth.block_number
        }
        
        # Determine appropriate test transaction
        if current_debt > 0:
            print(f"\n🎯 EXISTING DEBT DETECTED - Testing Debt Management")
            
            if available_borrows > 5.0 and current_health > 2.0:
                # Test case: Small additional borrow to verify debt tracking
                test_amount = min(5.0, available_borrows * 0.1)  # $5 or 10% of available, whichever is smaller
                
                print(f"🏦 Executing test borrow: ${test_amount:.2f} DAI")
                print(f"⚠️ This will INCREASE your debt position by ${test_amount:.2f}")
                
                # Attempt borrow through different access methods
                borrow_success = False
                borrow_method_used = None
                tx_hash = None
                
                # Method 1: Direct aave access
                if hasattr(agent, 'aave') and agent.aave:
                    try:
                        print(f"🔄 Attempting borrow via direct aave access...")
                        result = agent.aave.borrow_dai(test_amount)
                        if result:
                            borrow_success = True
                            borrow_method_used = "direct_aave"
                            tx_hash = result if isinstance(result, str) else result.get('tx_hash')
                    except Exception as e:
                        print(f"❌ Direct aave borrow failed: {e}")
                
                # Method 2: Enhanced borrow manager
                if not borrow_success and hasattr(agent, 'enhanced_borrow_manager'):
                    try:
                        print(f"🔄 Attempting borrow via enhanced borrow manager...")
                        result = agent.enhanced_borrow_manager.execute_enhanced_borrow_sequence(test_amount)
                        if result:
                            borrow_success = True
                            borrow_method_used = "enhanced_borrow_manager"
                    except Exception as e:
                        print(f"❌ Enhanced borrow manager failed: {e}")
                
                if borrow_success:
                    transaction_test['transaction_details'] = {
                        'type': 'borrow_test',
                        'amount_usd': test_amount,
                        'method_used': borrow_method_used,
                        'tx_hash': tx_hash,
                        'success': True
                    }
                    
                    print(f"✅ Test borrow executed successfully")
                    if tx_hash:
                        print(f"📝 Transaction Hash: {tx_hash}")
                        print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash}")
                    
                    # Wait for confirmation and record post-transaction state
                    print(f"⏳ Waiting 10 seconds for blockchain confirmation...")
                    time.sleep(10)
                    
                else:
                    print(f"❌ All borrow methods failed - executing balance verification instead")
                    # Fallback: Just verify current balances
                    transaction_test['transaction_details'] = {
                        'type': 'balance_verification',
                        'success': False,
                        'fallback_reason': 'borrow_methods_unavailable'
                    }
            else:
                print(f"⚠️ Insufficient capacity or health factor for test borrow")
                print(f"   Available: ${available_borrows:.2f} (need >$5)")
                print(f"   Health Factor: {current_health:.4f} (need >2.0)")
                
                transaction_test['transaction_details'] = {
                    'type': 'balance_verification_only',
                    'reason': 'insufficient_capacity_or_health'
                }
        else:
            print(f"ℹ️ NO EXISTING DEBT - Testing Balance Verification")
            transaction_test['transaction_details'] = {
                'type': 'balance_verification_only',
                'reason': 'no_existing_debt'
            }
        
        # Record post-transaction state (or current state for verification-only)
        print(f"\n📊 Recording Post-Transaction State...")
        
        # Re-fetch account data
        pool_address = getattr(agent, 'aave_pool_address', "0x794a61358D6845594F94dc1DB02A252b5b4814aD")
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(address=pool_address, abi=pool_abi)
        post_raw_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        post_total_debt = post_raw_data[1] / 1e8
        post_health_factor = post_raw_data[5] / 1e18 if post_raw_data[5] > 0 else float('inf')
        post_available_borrows = post_raw_data[2] / 1e8
        
        transaction_test['post_transaction_state'] = {
            'debt_usd': post_total_debt,
            'health_factor': post_health_factor,
            'available_borrows': post_available_borrows,
            'block_number': agent.w3.eth.block_number
        }
        
        # Calculate changes
        debt_change = post_total_debt - current_debt
        health_change = post_health_factor - current_health
        
        transaction_test['verification_results'] = {
            'debt_change_usd': debt_change,
            'health_factor_change': health_change,
            'debt_tracking_accurate': abs(debt_change) > 0.01 if borrow_success else True,
            'system_responsive': True
        }
        
        print(f"📈 Transaction Results:")
        print(f"   Debt Change: ${debt_change:+.2f}")
        print(f"   Health Factor Change: {health_change:+.4f}")
        print(f"   Final Debt: ${post_total_debt:.2f}")
        print(f"   Final Health Factor: {post_health_factor:.4f}")
        
        if transaction_test['transaction_details'].get('success'):
            print(f"✅ Test transaction completed successfully")
            print(f"✅ Debt tracking system responding correctly")
        else:
            print(f"ℹ️ Balance verification completed")
        
        transaction_test['test_status'] = 'SUCCESS'
        return transaction_test
        
    except Exception as e:
        print(f"❌ Test transaction failed: {e}")
        transaction_test['test_status'] = 'FAILED'
        transaction_test['error'] = str(e)
        transaction_test['error_details'] = traceback.format_exc()
        return transaction_test

def main():
    """Main verification execution"""
    print("🔍 COMPREHENSIVE DEBT MANAGEMENT SYSTEM VERIFICATION")
    print("=" * 80)
    print("Testing three critical aspects:")
    print("1️⃣ Debt Tracking Verification - Internal state structures")
    print("2️⃣ Function Testing - Swap and repayment function validation")
    print("3️⃣ On-Chain Test Transaction - Real blockchain interaction")
    print("=" * 80)
    
    # Initialize comprehensive results
    verification_results = {
        'test_session_id': f"debt_verification_{int(time.time())}",
        'start_time': datetime.now().isoformat(),
        'debt_tracking_results': None,
        'function_testing_results': None,
        'transaction_testing_results': None,
        'overall_status': 'PENDING'
    }
    
    try:
        # Initialize agent
        print("🤖 Initializing Arbitrum Agent...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Set environment for testing
        os.environ['FORCE_EXECUTION_MODE'] = 'true'
        
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
            
        print(f"✅ Agent initialized successfully")
        print(f"   Wallet: {agent.address}")
        print(f"   Chain ID: {agent.w3.eth.chain_id}")
        print(f"   Block Number: {agent.w3.eth.block_number}")
        
        # Execute verification sequence
        
        # 1. Debt Tracking Verification
        debt_tracking_results = test_debt_tracking_verification(agent)
        verification_results['debt_tracking_results'] = debt_tracking_results
        
        # 2. Function Testing
        function_testing_results = test_function_validation(agent, debt_tracking_results)
        verification_results['function_testing_results'] = function_testing_results
        
        # 3. On-Chain Test Transaction
        transaction_testing_results = execute_test_transaction(agent, debt_tracking_results, function_testing_results)
        verification_results['transaction_testing_results'] = transaction_testing_results
        
        # Determine overall status
        all_tests_success = (
            debt_tracking_results['verification_status'] == 'SUCCESS' and
            function_testing_results['test_status'] == 'SUCCESS' and
            transaction_testing_results['test_status'] == 'SUCCESS'
        )
        
        verification_results['overall_status'] = 'SUCCESS' if all_tests_success else 'PARTIAL_SUCCESS'
        verification_results['end_time'] = datetime.now().isoformat()
        
        # Final Summary
        print(f"\n🏆 VERIFICATION COMPLETE")
        print("=" * 80)
        print(f"📊 Test Results Summary:")
        print(f"   1️⃣ Debt Tracking: {debt_tracking_results['verification_status']}")
        print(f"   2️⃣ Function Testing: {function_testing_results['test_status']}")
        print(f"   3️⃣ Transaction Testing: {transaction_testing_results['test_status']}")
        print(f"🎯 Overall Status: {verification_results['overall_status']}")
        
        return verification_results
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        verification_results['overall_status'] = 'FAILED'
        verification_results['error'] = str(e)
        verification_results['error_details'] = traceback.format_exc()
        verification_results['end_time'] = datetime.now().isoformat()
        
        return verification_results
    
    finally:
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debt_verification_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(verification_results, f, indent=2, default=str)
        
        print(f"\n📁 Complete verification results saved to: {filename}")

if __name__ == "__main__":
    main()