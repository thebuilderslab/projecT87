#!/usr/bin/env python3
"""
Validation Integration Demo - Comprehensive 7-Step Pre-Transaction Validation
Demonstrates integration with existing debt swap system and validates a test transaction.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from web3 import Web3

# Import our new comprehensive validation system
from comprehensive_transaction_validator import ComprehensiveTransactionValidator, create_debt_swap_validation_test

# Import existing system components for integration
try:
    from production_debt_swap_executor import ProductionDebtSwapExecutor
    PRODUCTION_EXECUTOR_AVAILABLE = True
except ImportError:
    PRODUCTION_EXECUTOR_AVAILABLE = False
    print("⚠️ ProductionDebtSwapExecutor not available - using standalone validation")

try:
    from debt_swap_utils import DebtSwapSignatureValidator
    DEBT_SWAP_UTILS_AVAILABLE = True
except ImportError:
    DEBT_SWAP_UTILS_AVAILABLE = False
    print("⚠️ DebtSwapSignatureValidator not available")

try:
    from gas_optimization import CoinAPIGasOptimizer
    GAS_OPTIMIZER_AVAILABLE = True
except ImportError:
    GAS_OPTIMIZER_AVAILABLE = False
    print("⚠️ CoinAPIGasOptimizer not available")


class ValidationIntegrationDemo:
    """
    Demonstrates integration of comprehensive validation system with existing debt swap infrastructure.
    Shows how validation prevents transaction reverts through 7-step validation process.
    """
    
    def __init__(self):
        """Initialize the validation integration demo"""
        print("🔒 VALIDATION INTEGRATION DEMO")
        print("=" * 80)
        print("Demonstrating 7-step pre-transaction validation system")
        print("to minimize revert risk for DeFi transactions.")
        print("=" * 80)
        
        # Initialize Web3 connection
        self.rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to Arbitrum RPC: {self.rpc_url}")
        
        print(f"✅ Connected to Arbitrum (Chain ID: {self.w3.eth.chain_id})")
        
        # Get user address from environment or use example
        self.private_key = os.getenv('PRIVATE_KEY')
        if self.private_key:
            account = self.w3.eth.account.from_key(self.private_key)
            self.user_address = self.w3.to_checksum_address(account.address)
            print(f"✅ Using wallet address: {self.user_address}")
        else:
            # Use example address for demonstration (read-only operations)
            self.user_address = "0x742d35Cc6634C0532925a3b8D8e39de4f07BACAB"  # Example address
            print(f"⚠️ Using example address for demo: {self.user_address}")
        
        # Initialize comprehensive validator
        coin_api_key = os.getenv('COIN_API')
        self.validator = ComprehensiveTransactionValidator(
            w3=self.w3,
            user_address=self.user_address,
            coin_api_key=coin_api_key
        )
        
        # Initialize optional integrations
        self.production_executor = None
        self.gas_optimizer = None
        
        if PRODUCTION_EXECUTOR_AVAILABLE and self.private_key:
            try:
                self.production_executor = ProductionDebtSwapExecutor(self.private_key)
                print("✅ ProductionDebtSwapExecutor integrated")
            except Exception as e:
                print(f"⚠️ ProductionDebtSwapExecutor initialization failed: {e}")
        
        if GAS_OPTIMIZER_AVAILABLE:
            try:
                self.gas_optimizer = CoinAPIGasOptimizer(self.w3, max_usd_per_tx=10.0)
                print("✅ CoinAPIGasOptimizer integrated")
            except Exception as e:
                print(f"⚠️ CoinAPIGasOptimizer initialization failed: {e}")

    def demonstrate_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Demonstrate the comprehensive 7-step validation system with a test debt swap transaction.
        Shows how validation catches potential issues before transaction submission.
        """
        
        print(f"\n🚀 COMPREHENSIVE VALIDATION DEMONSTRATION")
        print("=" * 80)
        print("Creating test debt swap transaction and validating through all 7 steps...")
        print("=" * 80)
        
        # Create test debt swap parameters
        test_params = create_debt_swap_validation_test()
        
        # Enhance test parameters with current network data
        test_params = self._enhance_test_parameters(test_params)
        
        print(f"\n📋 TEST TRANSACTION PARAMETERS:")
        print(f"   Type: {test_params['transaction_type']}")
        print(f"   From Token: {test_params['from_token']}")
        print(f"   To Token: {test_params['to_token']}")
        print(f"   Amount: {test_params['amount']}")
        print(f"   Contract: {test_params['contract_address']}")
        print(f"   Gas Limit: {test_params['gas_limit']:,}")
        print(f"   Gas Price: {test_params['gas_price'] / 1e9:.2f} gwei")
        
        # Execute comprehensive validation
        print(f"\n🔒 EXECUTING 7-STEP VALIDATION...")
        validation_report = self.validator.validate_transaction_comprehensive(test_params)
        
        # Generate detailed analysis
        detailed_analysis = {
            'validation_summary': {
                'total_steps': len(validation_report['validation_steps']),
                'passed_steps': sum(1 for step in validation_report['validation_steps'].values() if step['status'] == 'PASS'),
                'failed_steps': sum(1 for step in validation_report['validation_steps'].values() if step['status'] == 'FAIL'),
                'warning_steps': sum(1 for step in validation_report['validation_steps'].values() if step['status'] == 'WARN'),
                'execution_time_ms': validation_report['execution_time_ms'],
                'recommendation': validation_report['final_recommendation']
            },
            'key_findings': validation_report['errors'][:5] if validation_report['errors'] else ['No critical errors detected'],
            'warnings': validation_report['warnings'][:3] if validation_report['warnings'] else ['No warnings'],
            'critical_success': validation_report['final_recommendation'] == 'HALT' and len(validation_report['errors']) > 0
        }
        
        # Save validation report to file
        report_filename = f"validation_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump({
                'validation_report': validation_report,
                'detailed_analysis': detailed_analysis,
                'test_parameters': test_params
            }, f, indent=2, default=str)
        
        print(f"\n📊 Validation report saved to: {report_filename}")
        
        return {
            'validation_report': validation_report,
            'detailed_analysis': detailed_analysis,
            'test_parameters': test_params,
            'report_file': report_filename
        }

    def demonstrate_integration_benefits(self) -> Dict[str, Any]:
        """
        Demonstrate how the validation system integrates with and enhances existing components.
        """
        
        print(f"\n🔗 INTEGRATION BENEFITS DEMONSTRATION")
        print("=" * 80)
        
        integration_benefits = {
            'comprehensive_validator': {
                'available': True,
                'benefits': [
                    "7-step validation process",
                    "Pre-transaction simulation", 
                    "Health factor validation",
                    "Gas optimization checks",
                    "Contract verification",
                    "Comprehensive error handling"
                ]
            },
            'production_debt_swap_executor': {
                'available': PRODUCTION_EXECUTOR_AVAILABLE,
                'integration': "Enhanced with validation before execution",
                'benefits': ["Prevents failed transactions", "Reduces gas waste", "Improves success rate"]
            },
            'gas_optimizer': {
                'available': GAS_OPTIMIZER_AVAILABLE,
                'integration': "Validation includes gas optimization checks",
                'benefits': ["Real-time gas price validation", "Cost estimation", "Budget management"]
            },
            'debt_swap_utils': {
                'available': DEBT_SWAP_UTILS_AVAILABLE,
                'integration': "Signature validation enhanced with comprehensive checks",
                'benefits': ["Calldata validation", "Function signature verification", "Error bubbling"]
            }
        }
        
        # Demonstrate enhanced gas optimization
        if self.gas_optimizer:
            print(f"\n⛽ GAS OPTIMIZATION INTEGRATION:")
            try:
                eth_price_result = self.gas_optimizer.get_eth_price_coinapi()
                print(f"   ETH Price: ${eth_price_result['price']:.2f} ({eth_price_result['source']})")
                
                gas_params = self.gas_optimizer.optimize_gas_parameters(
                    operation_type='debt_swap',
                    swap_amount_usd=50.0
                )
                print(f"   Optimized Gas Limit: {gas_params['gas_limit']:,}")
                print(f"   Optimized Gas Price: {gas_params['gas_price'] / 1e9:.2f} gwei")
                print(f"   Estimated Cost: ${gas_params['estimated_cost_usd']:.4f}")
                
                integration_benefits['gas_optimization_demo'] = {
                    'eth_price': eth_price_result['price'],
                    'optimized_gas': gas_params
                }
                
            except Exception as e:
                print(f"   Gas optimization demo failed: {e}")
        
        # Show validation coverage
        print(f"\n🛡️ VALIDATION COVERAGE:")
        coverage_areas = [
            "Parameter validation (amounts, addresses, limits)",
            "Pre-transaction simulation (revert detection)",
            "Balance and allowance verification",
            "Health factor safety checks",
            "Network fee optimization",
            "Contract and ABI verification",
            "Comprehensive error handling"
        ]
        
        for i, area in enumerate(coverage_areas, 1):
            print(f"   {i}. ✅ {area}")
        
        return integration_benefits

    def demonstrate_revert_prevention(self) -> Dict[str, Any]:
        """
        Demonstrate how validation prevents common transaction revert scenarios.
        """
        
        print(f"\n🛡️ REVERT PREVENTION DEMONSTRATION")
        print("=" * 80)
        
        # Create scenarios that would cause reverts
        revert_scenarios = [
            {
                'name': 'Insufficient Gas',
                'params': {
                    'transaction_type': 'debt_swap',
                    'from_token': 'DAI',
                    'to_token': 'ARB',
                    'amount': '50.0',
                    'contract_address': '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
                    'gas_limit': 1000,  # Too low
                    'gas_price': 100000000
                },
                'expected_issue': 'Insufficient gas limit'
            },
            {
                'name': 'Invalid Contract Address',
                'params': {
                    'transaction_type': 'debt_swap',
                    'from_token': 'DAI',
                    'to_token': 'ARB',
                    'amount': '50.0',
                    'contract_address': '0x0000000000000000000000000000000000000000',  # Invalid
                    'gas_limit': 500000,
                    'gas_price': 100000000
                },
                'expected_issue': 'Invalid contract address'
            },
            {
                'name': 'Excessive Gas Price',
                'params': {
                    'transaction_type': 'debt_swap',
                    'from_token': 'DAI',
                    'to_token': 'ARB',
                    'amount': '50.0',
                    'contract_address': '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
                    'gas_limit': 500000,
                    'gas_price': 100000000000  # 100 gwei - too high for Arbitrum
                },
                'expected_issue': 'Excessive gas price'
            }
        ]
        
        prevention_results = []
        
        for scenario in revert_scenarios:
            print(f"\n🧪 Testing Scenario: {scenario['name']}")
            print(f"   Expected Issue: {scenario['expected_issue']}")
            
            # Run validation on problematic parameters
            validation_result = self.validator.validate_transaction_comprehensive(scenario['params'])
            
            detected_issues = validation_result['errors'] + validation_result['warnings']
            issue_detected = any(scenario['expected_issue'].lower() in issue.lower() for issue in detected_issues)
            
            result = {
                'scenario': scenario['name'],
                'expected_issue': scenario['expected_issue'],
                'validation_status': validation_result['overall_status'],
                'recommendation': validation_result['final_recommendation'],
                'issue_detected': issue_detected,
                'detected_issues': detected_issues[:3],  # First 3 issues
                'prevention_successful': validation_result['final_recommendation'] in ['HALT', 'REQUIRE_FIXES']
            }
            
            prevention_results.append(result)
            
            status_emoji = "✅" if result['prevention_successful'] else "❌"
            print(f"   {status_emoji} Prevention Result: {result['validation_status']} → {result['recommendation']}")
            if result['detected_issues']:
                print(f"   🔍 Issues Detected: {len(result['detected_issues'])} (showing first 3)")
                for issue in result['detected_issues']:
                    print(f"      • {issue}")
        
        # Summary
        successful_preventions = sum(1 for r in prevention_results if r['prevention_successful'])
        total_scenarios = len(prevention_results)
        
        print(f"\n📊 REVERT PREVENTION SUMMARY:")
        print(f"   Scenarios Tested: {total_scenarios}")
        print(f"   Successfully Prevented: {successful_preventions}")
        print(f"   Prevention Rate: {(successful_preventions/total_scenarios)*100:.1f}%")
        
        return {
            'scenarios_tested': prevention_results,
            'prevention_rate': (successful_preventions/total_scenarios)*100,
            'total_scenarios': total_scenarios,
            'successful_preventions': successful_preventions
        }

    def generate_comprehensive_report(self, demo_results: Dict[str, Any]) -> str:
        """
        Generate a comprehensive structured report showing all validation results.
        """
        
        report_lines = []
        report_lines.append("🔒 COMPREHENSIVE 7-STEP PRE-TRANSACTION VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append(f"User Address: {self.user_address}")
        report_lines.append(f"Network: Arbitrum (Chain ID: {self.w3.eth.chain_id})")
        report_lines.append("=" * 80)
        
        # Validation Results Summary
        validation_report = demo_results['validation_report']
        risk_assessment = validation_report['risk_assessment']
        
        report_lines.append(f"\n📊 VALIDATION RESULTS SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Overall Status: {validation_report['overall_status']}")
        report_lines.append(f"Final Recommendation: {validation_report['final_recommendation']}")
        report_lines.append(f"Success Rate: {risk_assessment['success_rate']:.1f}%")
        report_lines.append(f"Total Execution Time: {validation_report['execution_time_ms']:.1f}ms")
        report_lines.append(f"Total Errors: {risk_assessment['total_errors']}")
        report_lines.append(f"Total Warnings: {risk_assessment['total_warnings']}")
        
        # Step-by-Step Results
        report_lines.append(f"\n📋 VALIDATION STEPS DETAILED RESULTS")
        report_lines.append("-" * 60)
        
        steps_info = [
            ("step_1_parameter_validation", "Parameter Validation"),
            ("step_2_simulation", "Pre-Transaction Simulation"),
            ("step_3_balances_allowances", "Balance & Allowance Checks"),
            ("step_4_health_factor", "Health Factor Validation"),
            ("step_5_network_fees", "Network Fee Settings"),
            ("step_6_contract_abi", "Contract & ABI Verification"),
            ("step_7_error_handling", "Error Handling")
        ]
        
        for step_id, step_name in steps_info:
            if step_id in validation_report['validation_steps']:
                step_result = validation_report['validation_steps'][step_id]
                status_emoji = "✅" if step_result['status'] == 'PASS' else "⚠️" if step_result['status'] == 'WARN' else "❌"
                
                report_lines.append(f"\n{status_emoji} {step_name}")
                report_lines.append(f"   Status: {step_result['status']}")
                report_lines.append(f"   Execution Time: {step_result.get('execution_time_ms', 0):.1f}ms")
                report_lines.append(f"   Message: {step_result.get('message', 'No message')}")
                
                if step_result.get('details'):
                    report_lines.append(f"   Key Details:")
                    for key, value in list(step_result['details'].items())[:3]:  # Show first 3 details
                        report_lines.append(f"      • {key}: {value}")
                
                if step_result.get('errors'):
                    report_lines.append(f"   Errors ({len(step_result['errors'])}):")
                    for error in step_result['errors'][:2]:  # Show first 2 errors
                        report_lines.append(f"      • {error}")
                
                if step_result.get('warnings'):
                    report_lines.append(f"   Warnings ({len(step_result['warnings'])}):")
                    for warning in step_result['warnings'][:2]:  # Show first 2 warnings
                        report_lines.append(f"      • {warning}")
        
        # Transaction Parameters
        test_params = demo_results['test_parameters']
        report_lines.append(f"\n📋 TRANSACTION PARAMETERS")
        report_lines.append("-" * 40)
        report_lines.append(f"Transaction Type: {test_params['transaction_type']}")
        report_lines.append(f"From Token: {test_params['from_token']}")
        report_lines.append(f"To Token: {test_params['to_token']}")
        report_lines.append(f"Amount: {test_params['amount']}")
        report_lines.append(f"Contract Address: {test_params['contract_address']}")
        report_lines.append(f"Gas Limit: {test_params['gas_limit']:,}")
        report_lines.append(f"Gas Price: {test_params['gas_price'] / 1e9:.2f} gwei")
        
        # Risk Assessment
        report_lines.append(f"\n🎯 RISK ASSESSMENT")
        report_lines.append("-" * 40)
        
        if validation_report['final_recommendation'] == 'PROCEED':
            report_lines.append("✅ RECOMMENDATION: PROCEED")
            report_lines.append("   Transaction appears safe to execute")
            report_lines.append("   All critical validations passed")
        elif validation_report['final_recommendation'] == 'PROCEED_WITH_CAUTION':
            report_lines.append("⚠️ RECOMMENDATION: PROCEED WITH CAUTION")
            report_lines.append("   Transaction may proceed but has warnings")
            report_lines.append("   Monitor execution carefully")
        elif validation_report['final_recommendation'] == 'REQUIRE_FIXES':
            report_lines.append("🔧 RECOMMENDATION: REQUIRE FIXES")
            report_lines.append("   Transaction parameters need adjustment")
            report_lines.append("   Address warnings before proceeding")
        else:  # HALT
            report_lines.append("❌ RECOMMENDATION: HALT")
            report_lines.append("   Transaction should NOT be executed")
            report_lines.append("   Critical issues detected")
        
        # Integration Benefits
        if 'integration_benefits' in demo_results:
            integration = demo_results['integration_benefits']
            report_lines.append(f"\n🔗 SYSTEM INTEGRATION")
            report_lines.append("-" * 40)
            
            for component, info in integration.items():
                if isinstance(info, dict) and 'available' in info:
                    status = "✅ Available" if info['available'] else "❌ Not Available"
                    report_lines.append(f"{component.replace('_', ' ').title()}: {status}")
        
        # Revert Prevention Results
        if 'revert_prevention' in demo_results:
            prevention = demo_results['revert_prevention']
            report_lines.append(f"\n🛡️ REVERT PREVENTION ANALYSIS")
            report_lines.append("-" * 40)
            report_lines.append(f"Scenarios Tested: {prevention['total_scenarios']}")
            report_lines.append(f"Successfully Prevented: {prevention['successful_preventions']}")
            report_lines.append(f"Prevention Rate: {prevention['prevention_rate']:.1f}%")
        
        # Footer
        report_lines.append(f"\n" + "=" * 80)
        report_lines.append("🔒 Comprehensive Transaction Validator v1.0")
        report_lines.append("   7-Step Pre-Transaction Validation System")
        report_lines.append("   Designed to minimize DeFi transaction revert risk")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)

    def _enhance_test_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance test parameters with current network data"""
        
        # Get current gas price from network
        try:
            current_gas_price = self.w3.eth.gas_price
            # Use slightly higher than current for better success probability
            params['gas_price'] = max(current_gas_price, 100000000)  # At least 0.1 gwei
        except:
            pass
        
        # Add realistic function data for debt swap
        # This is a partial function selector for swapDebt - in real usage this would be complete
        params['function_data'] = '0xb8bd1c6b' + '0' * 120  # Simplified for demo
        
        return params

    def run_full_demonstration(self) -> Dict[str, Any]:
        """
        Run the complete demonstration of the 7-step validation system.
        """
        
        print(f"\n🚀 STARTING FULL VALIDATION DEMONSTRATION")
        print("=" * 80)
        
        try:
            # Step 1: Demonstrate comprehensive validation
            print(f"\n1️⃣ COMPREHENSIVE VALIDATION")
            validation_demo = self.demonstrate_comprehensive_validation()
            
            # Step 2: Show integration benefits
            print(f"\n2️⃣ INTEGRATION BENEFITS")
            integration_demo = self.demonstrate_integration_benefits()
            
            # Step 3: Demonstrate revert prevention
            print(f"\n3️⃣ REVERT PREVENTION")
            prevention_demo = self.demonstrate_revert_prevention()
            
            # Combine all results
            full_results = {
                **validation_demo,
                'integration_benefits': integration_demo,
                'revert_prevention': prevention_demo
            }
            
            # Step 4: Generate comprehensive report
            print(f"\n4️⃣ GENERATING COMPREHENSIVE REPORT")
            report_text = self.generate_comprehensive_report(full_results)
            
            # Save report to file
            report_filename = f"comprehensive_validation_report_{int(time.time())}.txt"
            with open(report_filename, 'w') as f:
                f.write(report_text)
            
            print(f"\n📊 DEMONSTRATION COMPLETE")
            print("=" * 80)
            print(f"📄 Comprehensive report saved to: {report_filename}")
            print(f"📊 JSON data saved to: {validation_demo['report_file']}")
            print("=" * 80)
            
            # Print key summary
            validation_report = validation_demo['validation_report']
            print(f"\n🎯 KEY RESULTS SUMMARY:")
            print(f"   Overall Status: {validation_report['overall_status']}")
            print(f"   Final Recommendation: {validation_report['final_recommendation']}")
            print(f"   Success Rate: {validation_report['risk_assessment']['success_rate']:.1f}%")
            print(f"   Revert Prevention Rate: {prevention_demo['prevention_rate']:.1f}%")
            
            return {
                **full_results,
                'report_file': report_filename,
                'demonstration_complete': True
            }
            
        except Exception as e:
            print(f"❌ Demonstration failed: {e}")
            return {
                'demonstration_complete': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # Run the full demonstration
    demo = ValidationIntegrationDemo()
    results = demo.run_full_demonstration()
    
    if results.get('demonstration_complete'):
        print(f"\n✅ VALIDATION SYSTEM DEMONSTRATION SUCCESSFUL")
        print(f"🔒 7-step validation system operational and integrated")
    else:
        print(f"\n❌ DEMONSTRATION FAILED: {results.get('error', 'Unknown error')}")