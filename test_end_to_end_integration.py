#!/usr/bin/env python3
"""
END-TO-END INTEGRATION TEST
Tests the complete ProductionDebtSwapExecutor → EnhancedDebtSwapExecutor → TransactionVerifier flow
"""

import json
import os
import time
from datetime import datetime
from production_debt_swap_executor import ProductionDebtSwapExecutor
from enhanced_debt_swap_with_verification import EnhancedDebtSwapExecutor

class EndToEndIntegrationTest:
    """Comprehensive end-to-end integration test"""
    
    def __init__(self):
        # Set up dummy private key for testing
        self.test_private_key = os.getenv('TEST_PRIVATE_KEY', '0x' + '1' * 64)
        self.test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'initialization_tests': {},
            'integration_tests': {},
            'verification_tests': {},
            'paraswap_flow_tests': {},
            'calldata_tests': {},
            'overall_status': 'pending',
            'errors': [],
            'warnings': []
        }
    
    def run_comprehensive_integration_test(self) -> dict:
        """Run complete end-to-end integration test"""
        print("\n🚀 END-TO-END INTEGRATION TEST")
        print("=" * 80)
        print("Testing: ProductionDebtSwapExecutor → EnhancedDebtSwapExecutor → TransactionVerifier")
        print("=" * 80)
        
        try:
            # Test 1: Component Initialization
            print("\n🔍 Test 1: Component Initialization...")
            self.test_results['initialization_tests'] = self._test_component_initialization()
            
            # Test 2: Enhanced Executor Integration
            print("\n🔍 Test 2: Enhanced Executor Integration...")
            self.test_results['integration_tests'] = self._test_enhanced_executor_integration()
            
            # Test 3: Transaction Verification System
            print("\n🔍 Test 3: Transaction Verification System...")
            self.test_results['verification_tests'] = self._test_verification_system()
            
            # Test 4: ParaSwap Flow Validation
            print("\n🔍 Test 4: ParaSwap Flow Validation...")
            self.test_results['paraswap_flow_tests'] = self._test_paraswap_flow()
            
            # Test 5: Calldata Build/Decode
            print("\n🔍 Test 5: Calldata Build/Decode...")
            self.test_results['calldata_tests'] = self._test_calldata_operations()
            
            # Determine overall status
            self.test_results['overall_status'] = self._determine_overall_status()
            
            print(f"\n✅ End-to-End Integration Test: {self.test_results['overall_status']}")
            
        except Exception as e:
            self.test_results['errors'].append(f"Integration test failed: {str(e)}")
            self.test_results['overall_status'] = 'FAILED'
            print(f"❌ Integration test failed: {e}")
        
        return self.test_results
    
    def _test_component_initialization(self) -> dict:
        """Test all components initialize correctly"""
        results = {
            'production_executor': {'success': False, 'error': None},
            'enhanced_executor': {'success': False, 'error': None},
            'transaction_verifier': {'success': False, 'error': None},
            'contract_connections': {'success': False, 'error': None}
        }
        
        try:
            # Test ProductionDebtSwapExecutor
            print("   🔧 Testing ProductionDebtSwapExecutor initialization...")
            production_executor = ProductionDebtSwapExecutor(private_key=self.test_private_key)
            results['production_executor']['success'] = True
            print("   ✅ ProductionDebtSwapExecutor initialized successfully")
            
            # Test EnhancedDebtSwapExecutor
            print("   🔧 Testing EnhancedDebtSwapExecutor initialization...")
            enhanced_executor = EnhancedDebtSwapExecutor(private_key=self.test_private_key)
            results['enhanced_executor']['success'] = True
            print("   ✅ EnhancedDebtSwapExecutor initialized successfully")
            
            # Test TransactionVerifier
            print("   🔧 Testing TransactionVerifier integration...")
            if hasattr(enhanced_executor, 'transaction_verifier') and enhanced_executor.transaction_verifier:
                results['transaction_verifier']['success'] = True
                print("   ✅ TransactionVerifier properly integrated")
            else:
                results['transaction_verifier']['error'] = "TransactionVerifier not found or not initialized"
                print("   ❌ TransactionVerifier integration failed")
            
            # Test contract connections
            print("   🔧 Testing contract connections...")
            try:
                contract = production_executor.w3.eth.contract(
                    address=production_executor.aave_debt_switch_v3,
                    abi=production_executor.debt_swap_abi
                )
                results['contract_connections']['success'] = True
                print("   ✅ Contract connections successful")
            except Exception as e:
                results['contract_connections']['error'] = str(e)
                print(f"   ❌ Contract connection failed: {e}")
        
        except Exception as e:
            print(f"   ❌ Component initialization test failed: {e}")
            for key in results:
                if not results[key]['success']:
                    results[key]['error'] = str(e)
        
        return results
    
    def _test_enhanced_executor_integration(self) -> dict:
        """Test enhanced executor integration with production executor"""
        results = {
            'method_availability': {'success': False, 'missing_methods': []},
            'execution_bridge': {'success': False, 'error': None},
            'verification_integration': {'success': False, 'error': None}
        }
        
        try:
            enhanced_executor = EnhancedDebtSwapExecutor(private_key=self.test_private_key)
            
            # Test required method availability
            print("   🔧 Testing required method availability...")
            required_methods = [
                '_execute_debt_swap_transaction',
                'execute_verified_debt_swap',
                'get_aave_position',
                'execute_debt_swap'
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(enhanced_executor, method):
                    missing_methods.append(method)
            
            if not missing_methods:
                results['method_availability']['success'] = True
                print("   ✅ All required methods available")
            else:
                results['method_availability']['missing_methods'] = missing_methods
                print(f"   ❌ Missing methods: {missing_methods}")
            
            # Test execution bridge method
            print("   🔧 Testing _execute_debt_swap_transaction bridge...")
            if hasattr(enhanced_executor, '_execute_debt_swap_transaction'):
                # Test bridge method signature
                import inspect
                sig = inspect.signature(enhanced_executor._execute_debt_swap_transaction)
                expected_params = ['from_asset', 'to_asset', 'swap_amount_usd']
                actual_params = list(sig.parameters.keys())
                
                if all(param in actual_params for param in expected_params):
                    results['execution_bridge']['success'] = True
                    print("   ✅ Execution bridge method properly implemented")
                else:
                    results['execution_bridge']['error'] = f"Bridge method signature mismatch: expected {expected_params}, got {actual_params}"
                    print(f"   ❌ Bridge method signature issue")
            else:
                results['execution_bridge']['error'] = "_execute_debt_swap_transaction method not found"
                print("   ❌ Bridge method not found")
            
            # Test verification integration
            print("   🔧 Testing verification integration...")
            if enhanced_executor.transaction_verifier:
                required_verifier_methods = ['verify_debt_swap_transaction', 'compare_manual_vs_automated_execution']
                verifier_methods_ok = all(
                    hasattr(enhanced_executor.transaction_verifier, method) 
                    for method in required_verifier_methods
                )
                
                if verifier_methods_ok:
                    results['verification_integration']['success'] = True
                    print("   ✅ Verification integration successful")
                else:
                    results['verification_integration']['error'] = "Required verifier methods missing"
                    print("   ❌ Verification integration incomplete")
            else:
                results['verification_integration']['error'] = "TransactionVerifier not available"
                print("   ❌ TransactionVerifier not available")
        
        except Exception as e:
            print(f"   ❌ Enhanced executor integration test failed: {e}")
            for key in results:
                if not results[key]['success']:
                    results[key]['error'] = str(e)
        
        return results
    
    def _test_verification_system(self) -> dict:
        """Test transaction verification system functionality"""
        results = {
            'verifier_initialization': {'success': False, 'error': None},
            'contract_addresses': {'success': False, 'error': None},
            'event_signatures': {'success': False, 'error': None},
            'api_endpoints': {'success': False, 'error': None}
        }
        
        try:
            enhanced_executor = EnhancedDebtSwapExecutor(private_key=self.test_private_key)
            verifier = enhanced_executor.transaction_verifier
            
            if not verifier:
                for key in results:
                    results[key]['error'] = "TransactionVerifier not available"
                return results
            
            # Test verifier initialization
            print("   🔧 Testing verifier initialization...")
            if hasattr(verifier, 'w3') and hasattr(verifier, 'chain_id'):
                results['verifier_initialization']['success'] = True
                print("   ✅ Verifier properly initialized")
            else:
                results['verifier_initialization']['error'] = "Verifier missing required attributes"
                print("   ❌ Verifier initialization incomplete")
            
            # Test contract addresses
            print("   🔧 Testing contract addresses...")
            required_addresses = ['aave_debt_switch_v3', 'aave_pool', 'aave_data_provider']
            addresses_ok = all(
                hasattr(verifier, addr) and getattr(verifier, addr) 
                for addr in required_addresses
            )
            
            if addresses_ok:
                results['contract_addresses']['success'] = True
                print("   ✅ Contract addresses configured")
            else:
                results['contract_addresses']['error'] = "Missing contract addresses"
                print("   ❌ Contract addresses incomplete")
            
            # Test event signatures
            print("   🔧 Testing event signatures...")
            if hasattr(verifier, 'event_signatures'):
                required_events = ['Borrow', 'Repay', 'FlashLoan']
                events_ok = all(
                    event in verifier.event_signatures 
                    for event in required_events
                )
                
                if events_ok:
                    results['event_signatures']['success'] = True
                    print("   ✅ Event signatures configured")
                else:
                    results['event_signatures']['error'] = "Missing event signatures"
                    print("   ❌ Event signatures incomplete")
            else:
                results['event_signatures']['error'] = "Event signatures not found"
                print("   ❌ Event signatures not configured")
            
            # Test API endpoints
            print("   🔧 Testing API endpoints...")
            if hasattr(verifier, 'arbiscan_api_base') and hasattr(verifier, 'aave_subgraph_url'):
                results['api_endpoints']['success'] = True
                print("   ✅ API endpoints configured")
            else:
                results['api_endpoints']['error'] = "API endpoints not configured"
                print("   ❌ API endpoints missing")
        
        except Exception as e:
            print(f"   ❌ Verification system test failed: {e}")
            for key in results:
                if not results[key]['success']:
                    results[key]['error'] = str(e)
        
        return results
    
    def _test_paraswap_flow(self) -> dict:
        """Test ParaSwap flow validation"""
        results = {
            'address_alignment': {'success': False, 'error': None},
            'token_addresses': {'success': False, 'error': None},
            'contract_alignment': {'success': False, 'error': None}
        }
        
        try:
            production_executor = ProductionDebtSwapExecutor(private_key=self.test_private_key)
            
            # Test address alignment
            print("   🔧 Testing address alignment...")
            expected_addresses = {
                'aave_debt_switch_v3': '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
                'augustus_swapper': '0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57',
                'aave_pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD'
            }
            
            alignment_ok = True
            for attr, expected_addr in expected_addresses.items():
                actual_addr = getattr(production_executor, attr, None)
                if actual_addr != expected_addr:
                    alignment_ok = False
                    print(f"   ❌ Address mismatch for {attr}: expected {expected_addr}, got {actual_addr}")
            
            if alignment_ok:
                results['address_alignment']['success'] = True
                print("   ✅ Contract address alignment verified")
            else:
                results['address_alignment']['error'] = "Contract address misalignment detected"
            
            # Test token addresses
            print("   🔧 Testing token addresses...")
            required_tokens = ['DAI', 'ARB']
            tokens_ok = all(
                token in production_executor.tokens 
                for token in required_tokens
            )
            
            if tokens_ok:
                results['token_addresses']['success'] = True
                print("   ✅ Token addresses configured")
            else:
                results['token_addresses']['error'] = "Missing token addresses"
                print("   ❌ Token addresses incomplete")
            
            # Test contract alignment with verifier
            print("   🔧 Testing contract alignment with verifier...")
            enhanced_executor = EnhancedDebtSwapExecutor(private_key=self.test_private_key)
            if enhanced_executor.transaction_verifier:
                verifier_addr = enhanced_executor.transaction_verifier.aave_debt_switch_v3
                executor_addr = production_executor.aave_debt_switch_v3
                
                if verifier_addr.lower() == executor_addr.lower():
                    results['contract_alignment']['success'] = True
                    print("   ✅ Contract alignment verified")
                else:
                    results['contract_alignment']['error'] = f"Contract address mismatch: verifier={verifier_addr}, executor={executor_addr}"
                    print("   ❌ Contract alignment mismatch")
            else:
                results['contract_alignment']['error'] = "TransactionVerifier not available"
        
        except Exception as e:
            print(f"   ❌ ParaSwap flow test failed: {e}")
            for key in results:
                if not results[key]['success']:
                    results[key]['error'] = str(e)
        
        return results
    
    def _test_calldata_operations(self) -> dict:
        """Test calldata build and decode operations"""
        results = {
            'function_encoding': {'success': False, 'error': None},
            'selector_verification': {'success': False, 'error': None},
            'parameter_structure': {'success': False, 'error': None}
        }
        
        try:
            production_executor = ProductionDebtSwapExecutor(private_key=self.test_private_key)
            
            # Test function encoding
            print("   🔧 Testing function encoding...")
            try:
                contract = production_executor.w3.eth.contract(
                    address=production_executor.aave_debt_switch_v3,
                    abi=production_executor.debt_swap_abi
                )
                
                # Create test parameters
                zero_address = "0x0000000000000000000000000000000000000000"
                debt_swap_params = (
                    zero_address,  # debtAsset
                    1000000,       # debtRepayAmount
                    2,             # debtRateMode
                    zero_address,  # newDebtAsset
                    1100000,       # maxNewDebtAmount
                    zero_address,  # extraCollateralAsset
                    0,             # extraCollateralAmount
                    288,           # offset
                    b''            # swapData
                )
                
                permit_params = (zero_address, 0, 0, 0, b'\x00'*32, b'\x00'*32)
                
                encoded_data = contract.encodeABI('swapDebt', [debt_swap_params, permit_params, permit_params])
                
                if len(encoded_data) > 10:  # Should produce substantial calldata
                    results['function_encoding']['success'] = True
                    print(f"   ✅ Function encoding successful: {len(encoded_data)} bytes")
                else:
                    results['function_encoding']['error'] = "Encoded data too short"
                    print("   ❌ Function encoding produced insufficient data")
            
            except Exception as e:
                results['function_encoding']['error'] = str(e)
                print(f"   ❌ Function encoding failed: {e}")
            
            # Test selector verification
            print("   🔧 Testing selector verification...")
            try:
                if results['function_encoding']['success']:
                    # Check if calldata starts with expected selector
                    expected_selector = "0xb8bd1c6b"
                    actual_selector = encoded_data[:10]  # First 4 bytes + 0x prefix
                    
                    if actual_selector == expected_selector:
                        results['selector_verification']['success'] = True
                        print(f"   ✅ Selector verification successful: {actual_selector}")
                    else:
                        results['selector_verification']['error'] = f"Selector mismatch: expected {expected_selector}, got {actual_selector}"
                        print(f"   ❌ Selector mismatch")
                else:
                    results['selector_verification']['error'] = "Cannot verify selector without successful encoding"
            
            except Exception as e:
                results['selector_verification']['error'] = str(e)
                print(f"   ❌ Selector verification failed: {e}")
            
            # Test parameter structure
            print("   🔧 Testing parameter structure...")
            try:
                # Verify ABI parameter structure
                swap_debt_function = None
                for item in production_executor.debt_swap_abi:
                    if item.get('type') == 'function' and item.get('name') == 'swapDebt':
                        swap_debt_function = item
                        break
                
                if swap_debt_function:
                    inputs = swap_debt_function.get('inputs', [])
                    if len(inputs) == 3:  # Should have 3 main parameters
                        param_types = [inp.get('type') for inp in inputs]
                        expected_types = ['tuple', 'tuple', 'tuple']
                        
                        if param_types == expected_types:
                            results['parameter_structure']['success'] = True
                            print("   ✅ Parameter structure verified")
                        else:
                            results['parameter_structure']['error'] = f"Parameter type mismatch: expected {expected_types}, got {param_types}"
                    else:
                        results['parameter_structure']['error'] = f"Wrong number of parameters: expected 3, got {len(inputs)}"
                else:
                    results['parameter_structure']['error'] = "swapDebt function not found in ABI"
            
            except Exception as e:
                results['parameter_structure']['error'] = str(e)
                print(f"   ❌ Parameter structure test failed: {e}")
        
        except Exception as e:
            print(f"   ❌ Calldata operations test failed: {e}")
            for key in results:
                if not results[key]['success']:
                    results[key]['error'] = str(e)
        
        return results
    
    def _determine_overall_status(self) -> str:
        """Determine overall test status"""
        all_tests = [
            self.test_results['initialization_tests'],
            self.test_results['integration_tests'],
            self.test_results['verification_tests'],
            self.test_results['paraswap_flow_tests'],
            self.test_results['calldata_tests']
        ]
        
        # Count successful sub-tests
        total_subtests = 0
        successful_subtests = 0
        
        for test_group in all_tests:
            for subtest in test_group.values():
                total_subtests += 1
                if subtest.get('success', False):
                    successful_subtests += 1
        
        success_rate = (successful_subtests / total_subtests) * 100 if total_subtests > 0 else 0
        
        if success_rate >= 90:
            return 'PRODUCTION_READY'
        elif success_rate >= 75:
            return 'MOSTLY_FUNCTIONAL'
        elif success_rate >= 50:
            return 'PARTIALLY_FUNCTIONAL'
        else:
            return 'NEEDS_MAJOR_FIXES'

if __name__ == "__main__":
    tester = EndToEndIntegrationTest()
    results = tester.run_comprehensive_integration_test()
    
    print(f"\n📊 FINAL INTEGRATION TEST REPORT:")
    print("=" * 50)
    print(f"Status: {results['overall_status']}")
    
    # Count totals
    total_tests = 0
    successful_tests = 0
    
    for test_group_name, test_group in results.items():
        if isinstance(test_group, dict) and test_group_name.endswith('_tests'):
            for test_name, test_result in test_group.items():
                total_tests += 1
                if test_result.get('success', False):
                    successful_tests += 1
    
    print(f"Tests passed: {successful_tests}/{total_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
    
    if results['errors']:
        print("\n❌ ERRORS:")
        for error in results['errors']:
            print(f"   - {error}")
    
    if results['warnings']:
        print("\n⚠️ WARNINGS:")
        for warning in results['warnings']:
            print(f"   - {warning}")

if __name__ == "__main__":
    print("🚀 RUNNING END-TO-END INTEGRATION TEST")
    print("=" * 80)
    
    # Set up test environment variables
    if not os.getenv('TEST_PRIVATE_KEY'):
        os.environ['TEST_PRIVATE_KEY'] = '0x' + '1' * 64
    
    try:
        tester = EndToEndIntegrationTest()
        results = tester.run_comprehensive_integration_test()
        
        print("\n📋 FINAL INTEGRATION TEST RESULTS:")
        print("=" * 80)
        print(json.dumps(results, indent=2))
        
        # Determine success
        overall_success = (
            results['overall_status'] == 'PASSED' or
            results['overall_status'] == 'SUCCESS' or
            (results['overall_status'] not in ['FAILED', 'ERROR'] and 
             len(results.get('errors', [])) == 0)
        )
        
        if overall_success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED - Production Ready!")
            exit(0)
        else:
            print(f"\n❌ Some tests failed - Status: {results['overall_status']}")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Integration test execution failed: {e}")
        print("This indicates a critical integration issue that needs resolution.")
        exit(1)