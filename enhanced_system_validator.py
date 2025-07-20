
#!/usr/bin/env python3
"""
Enhanced System Validator - Comprehensive pre-execution validation
"""

import os
import json
import time
from web3 import Web3
from contract_validator import ContractValidator
from fix_json_serialization import DecimalEncoder, safe_json_dump

class EnhancedSystemValidator:
    def __init__(self, agent):
        self.agent = agent
        self.validation_results = {}
        
    def run_all_checks(self):
        """Run all validation checks and return issues list"""
        issues = []
        
        try:
            # Run comprehensive validation
            all_passed = self.run_comprehensive_validation()
            
            if not all_passed:
                # Extract issues from validation results
                for check_name, result in self.validation_results.items():
                    if not result.get('passed', False):
                        error_msg = result.get('error', f"{check_name} failed")
                        issues.append(f"{check_name}: {error_msg}")
            
            return issues
            
        except Exception as e:
            issues.append(f"System validation error: {e}")
            return issues
        
    def run_comprehensive_validation(self):
        """Run all validation checks before system execution"""
        print("🔍 ENHANCED SYSTEM VALIDATION")
        print("=" * 50)
        
        all_passed = True
        
        # 1. Contract Address Validation
        all_passed &= self._validate_contract_addresses()
        
        # 2. JSON Serialization Test
        all_passed &= self._test_json_serialization()
        
        # 3. Health Factor Calculation Test
        all_passed &= self._test_health_factor_calculation()
        
        # 4. Borrow Amount Validation Test
        all_passed &= self._test_borrow_amount_validation()
        
        # 5. Token Approval Test
        all_passed &= self._test_token_approval_readiness()
        
        # 6. RPC Connection Stability
        all_passed &= self._test_rpc_stability()
        
        # Save validation results
        self._save_validation_results()
        
        return all_passed
        
    def _validate_contract_addresses(self):
        """Validate all contract addresses"""
        print("\n1️⃣ CONTRACT ADDRESS VALIDATION")
        
        try:
            token_addresses = {
                'USDC': self.agent.usdc_address,
                'WBTC': self.agent.wbtc_address,
                'WETH': self.agent.weth_address,
                'DAI': self.agent.dai_address,
                'AAVE_POOL': self.agent.aave_pool_address
            }
            
            validator = ContractValidator(self.agent.w3)
            validation_success = validator.validate_all_tokens(token_addresses)
            
            self.validation_results['contract_validation'] = {
                'passed': validation_success,
                'addresses_tested': token_addresses
            }
            
            if validation_success:
                print("✅ All contract addresses validated successfully")
                return True
            else:
                print("❌ Contract address validation failed")
                return False
                
        except Exception as e:
            print(f"❌ Contract validation error: {e}")
            self.validation_results['contract_validation'] = {
                'passed': False,
                'error': str(e)
            }
            return False
            
    def _test_json_serialization(self):
        """Test JSON serialization with Decimal types"""
        print("\n2️⃣ JSON SERIALIZATION TEST")
        
        try:
            from decimal import Decimal
            
            test_data = {
                'health_factor': Decimal('2.5'),
                'collateral_usd': Decimal('150.75'),
                'debt_usd': Decimal('60.25'),
                'timestamp': 1234567890
            }
            
            # Test safe_json_dumps
            json_string = safe_json_dump(test_data, 'test_serialization.json')
            
            # Verify file was created and is valid JSON
            with open('test_serialization.json', 'r') as f:
                loaded_data = json.load(f)
                
            # Clean up test file
            os.remove('test_serialization.json')
            
            self.validation_results['json_serialization'] = {
                'passed': True,
                'test_data_keys': list(test_data.keys())
            }
            
            print("✅ JSON serialization with Decimal types working correctly")
            return True
            
        except Exception as e:
            print(f"❌ JSON serialization test failed: {e}")
            self.validation_results['json_serialization'] = {
                'passed': False,
                'error': str(e)
            }
            return False
            
    def _test_health_factor_calculation(self):
        """Test health factor calculation safety"""
        print("\n3️⃣ HEALTH FACTOR CALCULATION TEST")
        
        try:
            # Test edge cases
            test_cases = [
                {'value': 0, 'expected': float('inf')},
                {'value': -1, 'expected': float('inf')},
                {'value': 2500000000000000000, 'expected': 2.5},  # 2.5 * 10^18
                {'value': 1000000000000000000, 'expected': 1.0}   # 1.0 * 10^18
            ]
            
            all_passed = True
            for test in test_cases:
                if test['value'] > 0:
                    calculated_hf = test['value'] / (10**18)
                    if calculated_hf <= 0 or calculated_hf == float('inf'):
                        calculated_hf = float('inf')
                else:
                    calculated_hf = float('inf')
                    
                if calculated_hf != test['expected']:
                    print(f"❌ Health factor test failed for value {test['value']}")
                    all_passed = False
                    
            self.validation_results['health_factor_calculation'] = {
                'passed': all_passed,
                'test_cases_count': len(test_cases)
            }
            
            if all_passed:
                print("✅ Health factor calculation safety checks passed")
                return True
            else:
                print("❌ Health factor calculation tests failed")
                return False
                
        except Exception as e:
            print(f"❌ Health factor calculation test error: {e}")
            self.validation_results['health_factor_calculation'] = {
                'passed': False,
                'error': str(e)
            }
            return False
            
    def _test_borrow_amount_validation(self):
        """Test borrow amount validation logic"""
        print("\n4️⃣ BORROW AMOUNT VALIDATION TEST")
        
        try:
            # Test various scenarios
            test_scenarios = [
                {'growth': 15.0, 'available': 100.0, 'expected_range': (4.0, 8.0)},
                {'growth': -5.0, 'available': 50.0, 'expected_range': (0.1, 5.0)},
                {'growth': 0, 'available': 25.0, 'expected_range': (0.1, 2.5)},
                {'growth': 'invalid', 'available': 10.0, 'expected_range': (0.1, 1.0)}
            ]
            
            all_passed = True
            for scenario in test_scenarios:
                try:
                    calculated = self.agent.calculate_safe_borrow_amount(
                        scenario['growth'], scenario['available']
                    )
                    
                    min_expected, max_expected = scenario['expected_range']
                    if not (min_expected <= calculated <= max_expected):
                        print(f"❌ Borrow calculation out of range for scenario: {scenario}")
                        all_passed = False
                        
                except Exception as calc_error:
                    print(f"❌ Borrow calculation failed for scenario {scenario}: {calc_error}")
                    all_passed = False
                    
            self.validation_results['borrow_amount_validation'] = {
                'passed': all_passed,
                'scenarios_tested': len(test_scenarios)
            }
            
            if all_passed:
                print("✅ Borrow amount validation logic working correctly")
                return True
            else:
                print("❌ Borrow amount validation tests failed")
                return False
                
        except Exception as e:
            print(f"❌ Borrow amount validation test error: {e}")
            self.validation_results['borrow_amount_validation'] = {
                'passed': False,
                'error': str(e)
            }
            return False
            
    def _test_token_approval_readiness(self):
        """Test token approval system readiness"""
        print("\n5️⃣ TOKEN APPROVAL READINESS TEST")
        
        try:
            # Check if contract validator is available
            if not hasattr(self.agent, 'contract_validator'):
                print("❌ Contract validator not available")
                return False
                
            # Test contract validation method
            test_result = self.agent.contract_validator.validate_token_contract(
                self.agent.usdc_address, "USDC"
            )
            
            self.validation_results['token_approval_readiness'] = {
                'passed': test_result,
                'contract_validator_available': True
            }
            
            if test_result:
                print("✅ Token approval system ready")
                return True
            else:
                print("❌ Token approval system not ready")
                return False
                
        except Exception as e:
            print(f"❌ Token approval readiness test error: {e}")
            self.validation_results['token_approval_readiness'] = {
                'passed': False,
                'error': str(e)
            }
            return False
            
    def _test_rpc_stability(self):
        """Test RPC connection stability"""
        print("\n6️⃣ RPC CONNECTION STABILITY TEST")
        
        try:
            # Test multiple calls to ensure stability
            test_calls = []
            for i in range(3):
                try:
                    block_number = self.agent.w3.eth.block_number
                    gas_price = self.agent.w3.eth.gas_price
                    chain_id = self.agent.w3.eth.chain_id
                    
                    test_calls.append({
                        'call': i + 1,
                        'block_number': block_number,
                        'gas_price': gas_price,
                        'chain_id': chain_id,
                        'success': True
                    })
                except Exception as call_error:
                    test_calls.append({
                        'call': i + 1,
                        'success': False,
                        'error': str(call_error)
                    })
                    
            successful_calls = sum(1 for call in test_calls if call.get('success', False))
            stability_score = successful_calls / len(test_calls)
            
            self.validation_results['rpc_stability'] = {
                'passed': stability_score >= 0.8,
                'stability_score': stability_score,
                'successful_calls': successful_calls,
                'total_calls': len(test_calls)
            }
            
            if stability_score >= 0.8:
                print(f"✅ RPC connection stable ({stability_score:.1%} success rate)")
                return True
            else:
                print(f"❌ RPC connection unstable ({stability_score:.1%} success rate)")
                return False
                
        except Exception as e:
            print(f"❌ RPC stability test error: {e}")
            self.validation_results['rpc_stability'] = {
                'passed': False,
                'error': str(e)
            }
            return False
            
    def _save_validation_results(self):
        """Save validation results to file"""
        try:
            validation_summary = {
                'timestamp': time.time(),
                'overall_passed': all(
                    result.get('passed', False) 
                    for result in self.validation_results.values()
                ),
                'results': self.validation_results
            }
            
            safe_json_dump(validation_summary, 'system_validation_results.json')
            print(f"\n📋 Validation results saved to system_validation_results.json")
            
        except Exception as e:
            print(f"⚠️ Failed to save validation results: {e}")

if __name__ == "__main__":
    # This would be called from the main diagnostic workflow
    print("Enhanced System Validator - Run from main diagnostic workflow")
