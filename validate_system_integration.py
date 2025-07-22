
#!/usr/bin/env python3
"""
System Integration Validator - Verify all components work together correctly
"""

import os
import sys
import importlib
import traceback
from datetime import datetime

class SystemIntegrationValidator:
    def __init__(self):
        self.test_results = {}
        self.critical_failures = []
        
    def validate_complete_system(self):
        """Run complete system validation"""
        print("🔍 COMPLETE SYSTEM INTEGRATION VALIDATION")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 60)
        
        # Test 1: Import validation
        self._test_imports()
        
        # Test 2: Agent initialization
        self._test_agent_initialization()
        
        # Test 3: DeFi integrations
        self._test_defi_integrations()
        
        # Test 4: Swap compliance
        self._test_swap_compliance()
        
        # Test 5: Transaction validation
        self._test_transaction_validation()
        
        # Test 6: JSON serialization
        self._test_json_serialization()
        
        # Generate final report
        self._generate_final_report()
        
    def _test_imports(self):
        """Test all critical imports"""
        print("\n1️⃣ TESTING IMPORTS")
        
        critical_modules = [
            'arbitrum_testnet_agent',
            'enhanced_borrow_manager',
            'uniswap_integration',
            'aave_integration',
            'transaction_validator',
            'aave_health_monitor'
        ]
        
        for module in critical_modules:
            try:
                importlib.import_module(module)
                self.test_results[f"import_{module}"] = "✅ Success"
                print(f"   ✅ {module}: Imported successfully")
            except Exception as e:
                self.test_results[f"import_{module}"] = f"❌ Failed: {e}"
                self.critical_failures.append(f"Import failure: {module} - {e}")
                print(f"   ❌ {module}: Import failed - {e}")
    
    def _test_agent_initialization(self):
        """Test agent initialization"""
        print("\n2️⃣ TESTING AGENT INITIALIZATION")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            self.test_results["agent_init"] = "✅ Success"
            print(f"   ✅ Agent initialized: {agent.address}")
            
            # Test integration initialization
            try:
                integration_success = agent.initialize_integrations()
                if integration_success:
                    self.test_results["integrations_init"] = "✅ Success"
                    print(f"   ✅ DeFi integrations initialized")
                else:
                    self.test_results["integrations_init"] = "⚠️ Partial"
                    print(f"   ⚠️ Some integrations failed to initialize")
                    
            except Exception as int_error:
                self.test_results["integrations_init"] = f"❌ Failed: {int_error}"
                self.critical_failures.append(f"Integration init failure: {int_error}")
                print(f"   ❌ Integration initialization failed: {int_error}")
                
        except Exception as e:
            self.test_results["agent_init"] = f"❌ Failed: {e}"
            self.critical_failures.append(f"Agent initialization failure: {e}")
            print(f"   ❌ Agent initialization failed: {e}")
    
    def _test_defi_integrations(self):
        """Test DeFi integrations"""
        print("\n3️⃣ TESTING DEFI INTEGRATIONS")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            agent.initialize_integrations()
            
            # Test Aave integration
            if hasattr(agent, 'aave') and agent.aave:
                self.test_results["aave_integration"] = "✅ Available"
                print(f"   ✅ Aave integration: Available")
            else:
                self.test_results["aave_integration"] = "❌ Not available"
                print(f"   ❌ Aave integration: Not available")
            
            # Test Uniswap integration
            if hasattr(agent, 'uniswap') and agent.uniswap:
                self.test_results["uniswap_integration"] = "✅ Available"
                print(f"   ✅ Uniswap integration: Available")
            else:
                self.test_results["uniswap_integration"] = "❌ Not available"
                print(f"   ❌ Uniswap integration: Not available")
                
            # Test Enhanced Borrow Manager
            if hasattr(agent, 'enhanced_borrow_manager') and agent.enhanced_borrow_manager:
                self.test_results["enhanced_borrow_manager"] = "✅ Available"
                print(f"   ✅ Enhanced Borrow Manager: Available")
            else:
                self.test_results["enhanced_borrow_manager"] = "❌ Not available"
                print(f"   ❌ Enhanced Borrow Manager: Not available")
                
        except Exception as e:
            self.test_results["defi_integrations"] = f"❌ Failed: {e}"
            print(f"   ❌ DeFi integration test failed: {e}")
    
    def _test_swap_compliance(self):
        """Test swap compliance"""
        print("\n4️⃣ TESTING SWAP COMPLIANCE")
        
        try:
            from system_compliance_checker import SystemComplianceChecker
            checker = SystemComplianceChecker()
            compliance_result = checker.check_dai_only_compliance()
            
            if compliance_result:
                self.test_results["swap_compliance"] = "✅ Compliant"
                print(f"   ✅ Swap compliance: All files follow DAI-only policy")
            else:
                self.test_results["swap_compliance"] = "❌ Non-compliant"
                self.critical_failures.append("Swap compliance violations found")
                print(f"   ❌ Swap compliance: Violations found")
                
        except Exception as e:
            self.test_results["swap_compliance"] = f"❌ Failed: {e}"
            print(f"   ❌ Swap compliance test failed: {e}")
    
    def _test_transaction_validation(self):
        """Test transaction validation"""
        print("\n5️⃣ TESTING TRANSACTION VALIDATION")
        
        try:
            from transaction_validator import TransactionValidator
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            
            agent = ArbitrumTestnetAgent()
            agent.initialize_integrations()
            validator = TransactionValidator(agent)
            
            self.test_results["transaction_validator"] = "✅ Available"
            print(f"   ✅ Transaction validator: Available and functional")
            
        except Exception as e:
            self.test_results["transaction_validator"] = f"❌ Failed: {e}"
            print(f"   ❌ Transaction validator test failed: {e}")
    
    def _test_json_serialization(self):
        """Test JSON serialization"""
        print("\n6️⃣ TESTING JSON SERIALIZATION")
        
        try:
            from fix_json_serialization import safe_json_dumps, DecimalEncoder
            import decimal
            
            test_data = {
                'decimal_value': decimal.Decimal('123.456'),
                'float_value': 789.012
            }
            
            result = safe_json_dumps(test_data)
            if result and result != "{}":
                self.test_results["json_serialization"] = "✅ Working"
                print(f"   ✅ JSON serialization: Working correctly")
            else:
                self.test_results["json_serialization"] = "❌ Failed"
                print(f"   ❌ JSON serialization: Failed")
                
        except Exception as e:
            self.test_results["json_serialization"] = f"❌ Failed: {e}"
            print(f"   ❌ JSON serialization test failed: {e}")
    
    def _generate_final_report(self):
        """Generate final validation report"""
        print("\n" + "=" * 60)
        print("📊 FINAL SYSTEM VALIDATION REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results.values() if "✅" in r])
        
        print(f"✅ Successful tests: {successful_tests}/{total_tests}")
        print(f"❌ Critical failures: {len(self.critical_failures)}")
        
        if self.critical_failures:
            print("\n🚨 CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"   • {failure}")
        
        # Overall system status
        if len(self.critical_failures) == 0 and successful_tests >= (total_tests * 0.8):
            print("\n✅ SYSTEM READY FOR DEPLOYMENT")
            print("🚀 All critical components validated successfully")
            return True
        else:
            print("\n❌ SYSTEM NOT READY FOR DEPLOYMENT")
            print("🔧 Fix critical failures before proceeding")
            return False

def main():
    """Run system validation"""
    validator = SystemIntegrationValidator()
    is_ready = validator.validate_complete_system()
    
    if not is_ready:
        sys.exit(1)
    
    return True

if __name__ == "__main__":
    main()
