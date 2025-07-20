
#!/usr/bin/env python3
"""
Dependency Validator - Ensures all required modules and components are available
"""

import os
import sys
import importlib
from typing import List, Dict, Tuple

class DependencyValidator:
    def __init__(self):
        self.required_modules = [
            'web3',
            'eth_account', 
            'requests',
            'time',
            'json',
            'os'
        ]
        
        self.required_files = [
            'arbitrum_testnet_agent.py',
            'aave_integration.py',
            'uniswap_integration.py', 
            'aave_health_monitor.py',
            'gas_fee_calculator.py',
            'enhanced_borrow_manager.py',
            'config_constants.py',
            'rpc_circuit_breaker.py',
            'unified_aave_data_fetcher.py'
        ]
        
        self.validation_results = {
            'modules': {},
            'files': {},
            'overall_success': False,
            'critical_failures': [],
            'warnings': []
        }

    def validate_python_modules(self) -> Dict[str, bool]:
        """Validate required Python modules are available"""
        print("🔍 VALIDATING PYTHON MODULES")
        print("=" * 40)
        
        for module in self.required_modules:
            try:
                importlib.import_module(module)
                self.validation_results['modules'][module] = True
                print(f"✅ {module}: Available")
            except ImportError as e:
                self.validation_results['modules'][module] = False
                self.validation_results['critical_failures'].append(f"Missing module: {module}")
                print(f"❌ {module}: Missing - {e}")
        
        return self.validation_results['modules']

    def validate_required_files(self) -> Dict[str, bool]:
        """Validate required project files exist"""
        print("\n🔍 VALIDATING REQUIRED FILES")
        print("=" * 40)
        
        for file_path in self.required_files:
            if os.path.exists(file_path):
                self.validation_results['files'][file_path] = True
                print(f"✅ {file_path}: Found")
            else:
                self.validation_results['files'][file_path] = False
                self.validation_results['critical_failures'].append(f"Missing file: {file_path}")
                print(f"❌ {file_path}: Missing")
        
        return self.validation_results['files']

    def validate_environment_variables(self) -> Dict[str, bool]:
        """Validate required environment variables"""
        print("\n🔍 VALIDATING ENVIRONMENT VARIABLES")
        print("=" * 40)
        
        required_env_vars = [
            'WALLET_PRIVATE_KEY',
            'COINMARKETCAP_API_KEY',
            'NETWORK_MODE'
        ]
        
        env_results = {}
        for var in required_env_vars:
            value = os.getenv(var)
            if value:
                env_results[var] = True
                print(f"✅ {var}: Available")
            else:
                env_results[var] = False
                self.validation_results['critical_failures'].append(f"Missing environment variable: {var}")
                print(f"❌ {var}: Missing")
        
        return env_results

    def validate_file_syntax(self) -> Dict[str, bool]:
        """Validate Python files have correct syntax"""
        print("\n🔍 VALIDATING FILE SYNTAX")
        print("=" * 40)
        
        syntax_results = {}
        python_files = [f for f in self.required_files if f.endswith('.py')]
        
        for file_path in python_files:
            if not os.path.exists(file_path):
                syntax_results[file_path] = False
                continue
                
            try:
                with open(file_path, 'r') as f:
                    source = f.read()
                
                compile(source, file_path, 'exec')
                syntax_results[file_path] = True
                print(f"✅ {file_path}: Syntax OK")
                
            except SyntaxError as e:
                syntax_results[file_path] = False
                self.validation_results['critical_failures'].append(f"Syntax error in {file_path}: Line {e.lineno}")
                print(f"❌ {file_path}: Syntax Error - Line {e.lineno}: {e.msg}")
                
            except Exception as e:
                syntax_results[file_path] = False
                self.validation_results['warnings'].append(f"Could not validate {file_path}: {e}")
                print(f"⚠️ {file_path}: Could not validate - {e}")
        
        return syntax_results

    def run_comprehensive_validation(self) -> Dict:
        """Run all validation checks and return comprehensive results"""
        print("🚀 COMPREHENSIVE DEPENDENCY VALIDATION")
        print("=" * 50)
        
        # Run all validations
        module_results = self.validate_python_modules()
        file_results = self.validate_required_files()
        env_results = self.validate_environment_variables()
        syntax_results = self.validate_file_syntax()
        
        # Calculate overall success
        all_modules_ok = all(module_results.values())
        all_files_ok = all(file_results.values())
        all_env_ok = all(env_results.values())
        all_syntax_ok = all(syntax_results.values())
        
        self.validation_results['overall_success'] = (
            all_modules_ok and all_files_ok and all_env_ok and all_syntax_ok
        )
        
        # Summary
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 30)
        print(f"Python Modules: {'✅ PASS' if all_modules_ok else '❌ FAIL'}")
        print(f"Required Files: {'✅ PASS' if all_files_ok else '❌ FAIL'}")
        print(f"Environment Variables: {'✅ PASS' if all_env_ok else '❌ FAIL'}")
        print(f"File Syntax: {'✅ PASS' if all_syntax_ok else '❌ FAIL'}")
        print(f"Overall Status: {'✅ READY' if self.validation_results['overall_success'] else '❌ ISSUES FOUND'}")
        
        if self.validation_results['critical_failures']:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in self.validation_results['critical_failures']:
                print(f"   - {failure}")
        
        if self.validation_results['warnings']:
            print(f"\n⚠️ WARNINGS:")
            for warning in self.validation_results['warnings']:
                print(f"   - {warning}")
        
        return self.validation_results

    def generate_fix_commands(self) -> List[str]:
        """Generate commands to fix common dependency issues"""
        fix_commands = []
        
        # Check for missing modules
        missing_modules = [module for module, available in self.validation_results['modules'].items() if not available]
        if missing_modules:
            fix_commands.append(f"pip install {' '.join(missing_modules)}")
        
        return fix_commands

def validate_system_dependencies():
    """Main function to validate all system dependencies"""
    validator = DependencyValidator()
    results = validator.run_comprehensive_validation()
    
    if not results['overall_success']:
        print(f"\n🔧 SUGGESTED FIXES:")
        fix_commands = validator.generate_fix_commands()
        for cmd in fix_commands:
            print(f"   {cmd}")
    
    return results['overall_success']

if __name__ == "__main__":
    success = validate_system_dependencies()
    sys.exit(0 if success else 1)
