
```python
#!/usr/bin/env python3
"""
Enhanced System Validator
Validates all system components and provides detailed diagnostics
"""

import os
import time
import json
from web3 import Web3
from datetime import datetime

class EnhancedSystemValidator:
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []

    def validate_complete_system(self):
        """Run complete system validation"""
        print("🔍 ENHANCED SYSTEM VALIDATION")
        print("=" * 40)
        
        # Run all validation checks
        checks = [
            self.validate_environment_variables,
            self.validate_file_syntax,
            self.validate_contract_addresses,
            self.validate_network_connectivity,
            self.validate_integrations,
            self.validate_transaction_parameters
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.errors.append(f"Validation check failed: {e}")
        
        return self.generate_validation_report()

    def validate_environment_variables(self):
        """Validate required environment variables"""
        print("\n1️⃣ Environment Variables")
        
        required_vars = [
            'WALLET_PRIVATE_KEY',
            'COINMARKETCAP_API_KEY', 
            'NETWORK_MODE'
        ]
        
        for var in required_vars:
            if os.getenv(var):
                print(f"   ✅ {var}: Present")
            else:
                self.errors.append(f"Missing environment variable: {var}")
                print(f"   ❌ {var}: Missing")

    def validate_file_syntax(self):
        """Validate Python file syntax"""
        print("\n2️⃣ File Syntax Validation")
        
        critical_files = [
            'arbitrum_testnet_agent.py',
            'enhanced_borrow_manager.py',
            'aave_integration.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        compile(f.read(), file_path, 'exec')
                    print(f"   ✅ {file_path}: Valid syntax")
                except SyntaxError as e:
                    error_msg = f"Syntax error in {file_path}: Line {e.lineno}"
                    self.errors.append(error_msg)
                    print(f"   ❌ {file_path}: {error_msg}")
            else:
                self.warnings.append(f"File not found: {file_path}")

    def validate_contract_addresses(self):
        """Validate contract addresses"""
        print("\n3️⃣ Contract Address Validation")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            addresses = {
                'USDC': agent.usdc_address,
                'WBTC': agent.wbtc_address, 
                'WETH': agent.weth_address,
                'Aave Pool': agent.aave_pool_address
            }
            
            for name, addr in addresses.items():
                if Web3.is_address(addr):
                    print(f"   ✅ {name}: {addr}")
                else:
                    error_msg = f"Invalid {name} address: {addr}"
                    self.errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    
        except Exception as e:
            self.errors.append(f"Contract validation failed: {e}")

    def validate_network_connectivity(self):
        """Validate network connectivity"""
        print("\n4️⃣ Network Connectivity")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            if agent.w3.is_connected():
                block_num = agent.w3.eth.block_number
                print(f"   ✅ Connected to block {block_num}")
            else:
                self.errors.append("Network not connected")
                print("   ❌ Network not connected")
                
        except Exception as e:
            self.errors.append(f"Network validation failed: {e}")

    def validate_integrations(self):
        """Validate DeFi integrations"""
        print("\n5️⃣ DeFi Integrations")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            agent.initialize_integrations()
            
            integrations = {
                'Aave': agent.aave,
                'Uniswap': agent.uniswap,
                'Enhanced Borrow Manager': agent.enhanced_borrow_manager
            }
            
            for name, integration in integrations.items():
                if integration:
                    print(f"   ✅ {name}: Initialized")
                else:
                    self.warnings.append(f"{name} not initialized")
                    print(f"   ⚠️ {name}: Not initialized")
                    
        except Exception as e:
            self.errors.append(f"Integration validation failed: {e}")

    def validate_transaction_parameters(self):
        """Validate transaction parameter generation"""
        print("\n6️⃣ Transaction Parameters")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            # Test gas parameter generation
            gas_params = agent.get_optimized_gas_params('aave_borrow', 'market')
            
            required_params = ['gas', 'gasPrice']
            for param in required_params:
                if param in gas_params and gas_params[param] > 0:
                    print(f"   ✅ {param}: {gas_params[param]}")
                else:
                    error_msg = f"Invalid gas parameter: {param}"
                    self.errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    
        except Exception as e:
            self.errors.append(f"Transaction parameter validation failed: {e}")

    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 25)
        
        total_checks = 6
        failed_checks = len(self.errors)
        passed_checks = total_checks - failed_checks
        
        print(f"✅ Passed: {passed_checks}/{total_checks}")
        print(f"❌ Failed: {failed_checks}/{total_checks}")
        print(f"⚠️ Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n🚨 CRITICAL ERRORS:")
            for i, error in enumerate(self.errors[:5], 1):
                print(f"   {i}. {error}")
                
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for i, warning in enumerate(self.warnings[:3], 1):
                print(f"   {i}. {warning}")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }
        
        try:
            with open('validation_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Detailed report saved: validation_report.json")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
        
        return len(self.errors) == 0

def main():
    """Run enhanced system validation"""
    validator = EnhancedSystemValidator()
    success = validator.validate_complete_system()
    
    if success:
        print("\n🎉 SYSTEM VALIDATION PASSED")
        print("System ready for autonomous execution!")
    else:
        print("\n⚠️ SYSTEM VALIDATION FAILED") 
        print("Fix critical errors before proceeding")
    
    return success

if __name__ == "__main__":
    main()
```
