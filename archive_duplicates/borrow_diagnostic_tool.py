
#!/usr/bin/env python3
"""
Borrow Diagnostic Tool
Comprehensive diagnostics for borrowing system issues
"""

import os
import json
import time
from datetime import datetime
from web3 import Web3

class BorrowDiagnosticTool:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.diagnostics = {}

    def run_comprehensive_borrow_diagnostic(self):
        """Run comprehensive borrow diagnostic"""
        print("🔍 COMPREHENSIVE BORROWING DIAGNOSTIC")
        print("=" * 50)

        try:
            # Initialize results
            self.diagnostics = {
                'timestamp': datetime.now().isoformat(),
                'wallet_address': self.agent.address,
                'network_mode': self.agent.network_mode,
                'tests': {}
            }

            # Test 1: Network and connectivity
            self._test_network_connectivity()
            
            # Test 2: Contract validation
            self._test_contract_validation()
            
            # Test 3: Aave position analysis
            self._test_aave_position()
            
            # Test 4: Gas and ETH analysis
            self._test_gas_readiness()
            
            # Test 5: Enhanced borrow manager
            self._test_enhanced_borrow_manager()
            
            # Test 6: Simulation test
            self._test_borrow_simulation()

            # Generate final report
            self._generate_diagnostic_report()
            
            return self.diagnostics

        except Exception as e:
            print(f"❌ Comprehensive diagnostic failed: {e}")
            self.diagnostics['critical_error'] = str(e)
            return self.diagnostics

    def _test_network_connectivity(self):
        """Test network connectivity and RPC health"""
        print("\n1️⃣ Testing Network Connectivity...")
        test_result = {
            'connected': False,
            'chain_id': None,
            'block_number': None,
            'gas_price': None,
            'issues': []
        }

        try:
            if not self.w3.is_connected():
                test_result['issues'].append("Web3 not connected")
                return

            test_result['connected'] = True
            test_result['chain_id'] = self.w3.eth.chain_id
            test_result['block_number'] = self.w3.eth.block_number
            test_result['gas_price'] = self.w3.eth.gas_price

            print(f"   ✅ Connected to chain {test_result['chain_id']}")
            print(f"   ✅ Latest block: {test_result['block_number']}")
            print(f"   ✅ Gas price: {Web3.from_wei(test_result['gas_price'], 'gwei'):.2f} gwei")

        except Exception as e:
            test_result['issues'].append(f"Network test failed: {e}")
            print(f"   ❌ Network connectivity failed: {e}")

        self.diagnostics['tests']['network'] = test_result

    def _test_contract_validation(self):
        """Test all contract addresses"""
        print("\n2️⃣ Testing Contract Validation...")
        test_result = {
            'contracts_valid': {},
            'aave_pool_valid': False,
            'issues': []
        }

        try:
            # Test token contracts
            contracts = {
                'USDC': self.agent.usdc_address,
                'WBTC': self.agent.wbtc_address,
                'WETH': self.agent.weth_address,
                'DAI': self.agent.dai_address
            }

            for name, address in contracts.items():
                try:
                    if not Web3.is_address(address):
                        test_result['contracts_valid'][name] = False
                        test_result['issues'].append(f"Invalid {name} address")
                        continue

                    code = self.w3.eth.get_code(Web3.to_checksum_address(address))
                    if code == b'':
                        test_result['contracts_valid'][name] = False
                        test_result['issues'].append(f"No contract at {name} address")
                        continue

                    test_result['contracts_valid'][name] = True
                    print(f"   ✅ {name}: Valid contract")

                except Exception as e:
                    test_result['contracts_valid'][name] = False
                    test_result['issues'].append(f"{name} validation failed: {e}")
                    print(f"   ❌ {name}: {e}")

            # Test Aave pool
            try:
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

                pool_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.agent.aave_pool_address),
                    abi=pool_abi
                )

                # Test with agent's address
                account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
                test_result['aave_pool_valid'] = True
                print(f"   ✅ Aave Pool: Valid and accessible")

            except Exception as e:
                test_result['issues'].append(f"Aave pool validation failed: {e}")
                print(f"   ❌ Aave Pool: {e}")

        except Exception as e:
            test_result['issues'].append(f"Contract validation failed: {e}")
            print(f"   ❌ Contract validation error: {e}")

        self.diagnostics['tests']['contracts'] = test_result

    def _test_aave_position(self):
        """Test current Aave position"""
        print("\n3️⃣ Testing Aave Position...")
        test_result = {
            'position_accessible': False,
            'collateral_usd': 0,
            'debt_usd': 0,
            'available_borrows_usd': 0,
            'health_factor': 0,
            'can_borrow': False,
            'issues': []
        }

        try:
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

            pool_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.agent.aave_pool_address),
                abi=pool_abi
            )

            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()

            test_result['position_accessible'] = True
            test_result['collateral_usd'] = account_data[0] / (10**8)
            test_result['debt_usd'] = account_data[1] / (10**8)
            test_result['available_borrows_usd'] = account_data[2] / (10**8)
            test_result['health_factor'] = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"   ✅ Collateral: ${test_result['collateral_usd']:,.2f}")
            print(f"   ✅ Debt: ${test_result['debt_usd']:,.2f}")
            print(f"   ✅ Available Borrows: ${test_result['available_borrows_usd']:,.2f}")
            print(f"   ✅ Health Factor: {test_result['health_factor']:.4f}")

            # Determine if can borrow
            test_result['can_borrow'] = (
                test_result['health_factor'] > 1.5 and
                test_result['available_borrows_usd'] >= 1.0
            )

            if test_result['can_borrow']:
                print(f"   ✅ Position ready for borrowing")
            else:
                reasons = []
                if test_result['health_factor'] <= 1.5:
                    reasons.append(f"Low health factor: {test_result['health_factor']:.4f}")
                if test_result['available_borrows_usd'] < 1.0:
                    reasons.append(f"Low available borrows: ${test_result['available_borrows_usd']:.2f}")
                test_result['issues'].extend(reasons)
                print(f"   ⚠️ Position not ready: {', '.join(reasons)}")

        except Exception as e:
            test_result['issues'].append(f"Aave position test failed: {e}")
            print(f"   ❌ Aave position test failed: {e}")

        self.diagnostics['tests']['aave_position'] = test_result

    def _test_gas_readiness(self):
        """Test ETH balance and gas readiness"""
        print("\n4️⃣ Testing Gas Readiness...")
        test_result = {
            'eth_balance': 0,
            'sufficient_for_gas': False,
            'estimated_gas_cost': 0,
            'issues': []
        }

        try:
            eth_balance = self.agent.get_eth_balance()
            test_result['eth_balance'] = float(eth_balance)

            # Estimate gas cost for borrow operation
            current_gas_price = self.w3.eth.gas_price
            estimated_gas_limit = 300000  # Conservative estimate for borrow
            estimated_cost_wei = current_gas_price * estimated_gas_limit
            estimated_cost_eth = Web3.from_wei(estimated_cost_wei, 'ether')
            test_result['estimated_gas_cost'] = float(estimated_cost_eth)

            min_eth_needed = estimated_cost_eth * 2  # 2x buffer
            test_result['sufficient_for_gas'] = eth_balance >= min_eth_needed

            print(f"   ✅ ETH Balance: {eth_balance:.6f} ETH")
            print(f"   ✅ Estimated Gas Cost: {estimated_cost_eth:.6f} ETH")

            if test_result['sufficient_for_gas']:
                print(f"   ✅ Sufficient ETH for gas operations")
            else:
                shortage = min_eth_needed - eth_balance
                test_result['issues'].append(f"Need {shortage:.6f} more ETH for gas")
                print(f"   ⚠️ Need {shortage:.6f} more ETH")

        except Exception as e:
            test_result['issues'].append(f"Gas readiness test failed: {e}")
            print(f"   ❌ Gas readiness test failed: {e}")

        self.diagnostics['tests']['gas_readiness'] = test_result

    def _test_enhanced_borrow_manager(self):
        """Test enhanced borrow manager"""
        print("\n5️⃣ Testing Enhanced Borrow Manager...")
        test_result = {
            'manager_available': False,
            'validation_method_exists': False,
            'fallback_methods_available': 0,
            'issues': []
        }

        try:
            # Check if enhanced borrow manager exists
            if hasattr(self.agent, 'enhanced_borrow_manager') and self.agent.enhanced_borrow_manager:
                test_result['manager_available'] = True
                ebm = self.agent.enhanced_borrow_manager
                print(f"   ✅ Enhanced Borrow Manager: Available")

                # Check validation method
                if hasattr(ebm, '_validate_borrow_conditions'):
                    test_result['validation_method_exists'] = True
                    print(f"   ✅ Validation Method: Available")
                else:
                    test_result['issues'].append("Validation method missing")

                # Check fallback methods
                fallback_methods = [
                    'safe_borrow_with_fallbacks',
                    '_validate_borrow_conditions'
                ]
                
                available_methods = sum(1 for method in fallback_methods if hasattr(ebm, method))
                test_result['fallback_methods_available'] = available_methods
                print(f"   ✅ Fallback Methods: {available_methods}/{len(fallback_methods)}")

            else:
                test_result['issues'].append("Enhanced borrow manager not initialized")
                print(f"   ❌ Enhanced Borrow Manager: Not available")

        except Exception as e:
            test_result['issues'].append(f"Enhanced borrow manager test failed: {e}")
            print(f"   ❌ Enhanced borrow manager test failed: {e}")

        self.diagnostics['tests']['enhanced_borrow_manager'] = test_result

    def _test_borrow_simulation(self):
        """Test borrow operation simulation"""
        print("\n6️⃣ Testing Borrow Simulation...")
        test_result = {
            'simulation_possible': False,
            'recommended_amount': 0,
            'safety_checks_passed': False,
            'issues': []
        }

        try:
            # Get current position data
            aave_test = self.diagnostics['tests'].get('aave_position', {})
            
            if not aave_test.get('position_accessible'):
                test_result['issues'].append("Cannot access Aave position for simulation")
                return

            available_borrows = aave_test.get('available_borrows_usd', 0)
            health_factor = aave_test.get('health_factor', 0)

            # Calculate recommended borrow amount
            if available_borrows > 0 and health_factor > 1.5:
                # Conservative: 10% of available capacity, min $0.50, max $5.00
                recommended = min(max(available_borrows * 0.1, 0.5), 5.0)
                test_result['recommended_amount'] = recommended
                test_result['simulation_possible'] = True
                test_result['safety_checks_passed'] = True
                
                print(f"   ✅ Simulation Possible: Yes")
                print(f"   ✅ Recommended Amount: ${recommended:.2f}")
                print(f"   ✅ Safety Checks: Passed")
            else:
                reasons = []
                if available_borrows <= 0:
                    reasons.append("No available borrows")
                if health_factor <= 1.5:
                    reasons.append(f"Low health factor: {health_factor:.4f}")
                test_result['issues'].extend(reasons)
                print(f"   ⚠️ Simulation not recommended: {', '.join(reasons)}")

        except Exception as e:
            test_result['issues'].append(f"Borrow simulation failed: {e}")
            print(f"   ❌ Borrow simulation failed: {e}")

        self.diagnostics['tests']['borrow_simulation'] = test_result

    def _generate_diagnostic_report(self):
        """Generate final diagnostic report"""
        print("\n📊 DIAGNOSTIC SUMMARY")
        print("=" * 30)

        total_tests = len(self.diagnostics['tests'])
        passed_tests = 0
        critical_issues = []

        for test_name, test_data in self.diagnostics['tests'].items():
            issues = test_data.get('issues', [])
            
            if test_name == 'network' and test_data.get('connected'):
                passed_tests += 1
                print(f"✅ Network: PASSED")
            elif test_name == 'contracts' and test_data.get('aave_pool_valid'):
                passed_tests += 1
                print(f"✅ Contracts: PASSED")
            elif test_name == 'aave_position' and test_data.get('position_accessible'):
                passed_tests += 1
                print(f"✅ Aave Position: PASSED")
            elif test_name == 'gas_readiness' and test_data.get('sufficient_for_gas'):
                passed_tests += 1
                print(f"✅ Gas Readiness: PASSED")
            elif test_name == 'enhanced_borrow_manager' and test_data.get('manager_available'):
                passed_tests += 1
                print(f"✅ Enhanced Borrow Manager: PASSED")
            elif test_name == 'borrow_simulation' and test_data.get('simulation_possible'):
                passed_tests += 1
                print(f"✅ Borrow Simulation: PASSED")
            else:
                print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
                critical_issues.extend(issues)

        print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} tests passed")

        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues[:5]:  # Show top 5 issues
                print(f"   • {issue}")

        # Save diagnostic report
        self._save_diagnostic_report()

        return passed_tests >= (total_tests * 0.8)  # 80% pass rate

    def _save_diagnostic_report(self):
        """Save diagnostic report to file"""
        try:
            filename = f"borrow_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            from fix_json_serialization import safe_json_dump
            success = safe_json_dump(self.diagnostics, filename)
            
            if success:
                print(f"\n💾 Diagnostic report saved: {filename}")
            else:
                print(f"\n⚠️ Failed to save diagnostic report")

        except Exception as e:
            print(f"⚠️ Error saving report: {e}")

def run_borrow_diagnostic():
    """Run the borrow diagnostic tool"""
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("🚀 Initializing Borrow Diagnostic Tool...")
        agent = ArbitrumTestnetAgent()
        
        # Initialize integrations if needed
        if not hasattr(agent, 'aave') or not agent.aave:
            print("🔄 Initializing DeFi integrations...")
            agent.initialize_integrations()
        
        diagnostic_tool = BorrowDiagnosticTool(agent)
        results = diagnostic_tool.run_comprehensive_borrow_diagnostic()
        
        return results
        
    except Exception as e:
        print(f"❌ Borrow diagnostic failed: {e}")
        return None

if __name__ == "__main__":
    run_borrow_diagnostic()
