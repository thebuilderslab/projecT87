
#!/usr/bin/env python3
"""
Network Approval Validator
Comprehensive validation system to achieve network approval status
"""

import os
import sys
import ast
import py_compile
import subprocess
import json
from datetime import datetime

class NetworkApprovalValidator:
    def __init__(self):
        self.validation_results = {
            'syntax_validation': False,
            'import_validation': False,
            'secrets_validation': False,
            'integration_validation': False,
            'security_validation': False,
            'performance_validation': False
        }
        self.critical_issues = []
        self.warnings = []
        
    def validate_syntax_comprehensive(self):
        """Comprehensive syntax validation for all critical files"""
        print("🔍 COMPREHENSIVE SYNTAX VALIDATION")
        print("=" * 60)
        
        critical_files = [
            'main.py',
            'web_dashboard.py', 
            'aave_integration.py',
            'uniswap_integration.py',
            'system_validator.py',
            'comprehensive_syntax_validator.py'
        ]
        
        syntax_errors = []
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                print(f"\n📁 Validating: {file_path}")
                
                # Method 1: py_compile validation
                try:
                    py_compile.compile(file_path, doraise=True)
                    print(f"  ✅ py_compile: OK")
                except py_compile.PyCompileError as e:
                    error_msg = f"py_compile error in {file_path}: {e}"
                    print(f"  ❌ py_compile: {e}")
                    syntax_errors.append(error_msg)
                    continue
                
                # Method 2: AST validation
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                    ast.parse(source, file_path)
                    print(f"  ✅ AST parse: OK")
                except SyntaxError as e:
                    error_msg = f"AST parse error in {file_path} line {e.lineno}: {e.msg}"
                    print(f"  ❌ AST parse: Line {e.lineno}: {e.msg}")
                    syntax_errors.append(error_msg)
                    continue
                    
                # Method 3: Compile validation
                try:
                    compile(source, file_path, 'exec')
                    print(f"  ✅ compile: OK")
                except SyntaxError as e:
                    error_msg = f"compile error in {file_path} line {e.lineno}: {e.msg}"
                    print(f"  ❌ compile: Line {e.lineno}: {e.msg}")
                    syntax_errors.append(error_msg)
            else:
                print(f"⚠️  {file_path}: File not found")
                self.warnings.append(f"Missing file: {file_path}")
        
        if syntax_errors:
            self.critical_issues.extend(syntax_errors)
            return False
            
        self.validation_results['syntax_validation'] = True
        return True
    
    def validate_imports_comprehensive(self):
        """Comprehensive import validation"""
        print(f"\n🔍 COMPREHENSIVE IMPORT VALIDATION")
        print("=" * 60)
        
        # Critical imports for DeFi operations
        critical_imports = [
            ("web3", "from web3 import Web3"),
            ("requests", "import requests"),
            ("flask", "from flask import Flask"),
            ("json", "import json"),
            ("os", "import os"),
            ("sys", "import sys"),
            ("time", "import time"),
            ("subprocess", "import subprocess"),
            ("dotenv", "from dotenv import load_dotenv"),
            ("decimal", "from decimal import Decimal")
        ]
        
        # Optional imports for enhanced functionality
        optional_imports = [
            ("eth_account", "from eth_account import Account"),
            ("eth_abi", "import eth_abi"),
            ("numpy", "import numpy"),
            ("pandas", "import pandas")
        ]
        
        import_failures = []
        
        for name, import_stmt in critical_imports:
            try:
                exec(import_stmt)
                print(f"  ✅ {name}: Critical import OK")
            except ImportError as e:
                error_msg = f"Critical import failure for {name}: {e}"
                print(f"  ❌ {name}: {e}")
                import_failures.append(error_msg)
        
        for name, import_stmt in optional_imports:
            try:
                exec(import_stmt)
                print(f"  ✅ {name}: Optional import OK")
            except ImportError as e:
                print(f"  ⚠️  {name}: Optional import failed: {e}")
                self.warnings.append(f"Optional import failed: {name}")
        
        if import_failures:
            self.critical_issues.extend(import_failures)
            return False
            
        self.validation_results['import_validation'] = True
        return True
    
    def validate_secrets_comprehensive(self):
        """Comprehensive secrets validation"""
        print(f"\n🔍 COMPREHENSIVE SECRETS VALIDATION")
        print("=" * 60)
        
        # Critical secrets required for operation
        critical_secrets = [
            'NETWORK_MODE',
            'ARBITRUM_RPC_URL', 
            'PRIVATE_KEY',
            'COINMARKETCAP_API_KEY'
        ]
        
        # Optional secrets for enhanced functionality
        optional_secrets = [
            'PROMPT_KEY',
            'OPTIMIZER_API_KEY',
            'ARBISCAN_API_KEY',
            'PRIVATE_KEY2'
        ]
        
        missing_critical = []
        
        for secret in critical_secrets:
            value = os.getenv(secret)
            if value and len(value.strip()) > 0:
                print(f"  ✅ {secret}: Available")
            else:
                missing_critical.append(secret)
                print(f"  ❌ {secret}: Missing or empty")
        
        for secret in optional_secrets:
            value = os.getenv(secret)
            if value and len(value.strip()) > 0:
                print(f"  ✅ {secret}: Available (optional)")
            else:
                print(f"  ⚠️  {secret}: Missing (optional)")
                self.warnings.append(f"Optional secret missing: {secret}")
        
        if missing_critical:
            self.critical_issues.extend([f"Missing critical secret: {s}" for s in missing_critical])
            return False
            
        self.validation_results['secrets_validation'] = True
        return True
    
    def validate_integrations(self):
        """Validate DeFi integrations"""
        print(f"\n🔍 DEFI INTEGRATIONS VALIDATION")
        print("=" * 60)
        
        integration_issues = []
        
        # Test Aave integration
        try:
            from aave_integration import EnhancedBorrowManager
            print(f"  ✅ Aave integration: Import OK")
        except Exception as e:
            error_msg = f"Aave integration failed: {e}"
            print(f"  ❌ Aave integration: {e}")
            integration_issues.append(error_msg)
        
        # Test Uniswap integration
        try:
            from uniswap_integration import UniswapV3Integration
            print(f"  ✅ Uniswap integration: Import OK")
        except Exception as e:
            error_msg = f"Uniswap integration failed: {e}"
            print(f"  ❌ Uniswap integration: {e}")
            integration_issues.append(error_msg)
        
        # Test Web3 connectivity
        try:
            from web3 import Web3
            rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                print(f"  ✅ Web3 connectivity: OK")
            else:
                error_msg = "Web3 connection failed"
                print(f"  ❌ Web3 connectivity: Failed")
                integration_issues.append(error_msg)
        except Exception as e:
            error_msg = f"Web3 setup failed: {e}"
            print(f"  ❌ Web3 setup: {e}")
            integration_issues.append(error_msg)
        
        if integration_issues:
            self.critical_issues.extend(integration_issues)
            return False
            
        self.validation_results['integration_validation'] = True
        return True
    
    def validate_security(self):
        """Validate security configurations"""
        print(f"\n🔍 SECURITY VALIDATION")
        print("=" * 60)
        
        security_issues = []
        
        # Validate private key format
        private_key = os.getenv('PRIVATE_KEY2') or os.getenv('PRIVATE_KEY')
        if private_key:
            if len(private_key) in [64, 66]:
                print(f"  ✅ Private key format: Valid")
            else:
                error_msg = f"Private key format invalid: {len(private_key)} characters"
                print(f"  ❌ Private key format: Invalid ({len(private_key)} chars)")
                security_issues.append(error_msg)
        else:
            error_msg = "No private key found"
            print(f"  ❌ Private key: Missing")
            security_issues.append(error_msg)
        
        # Validate network mode
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        if network_mode.lower() == 'mainnet':
            print(f"  ✅ Network mode: Mainnet ready")
        else:
            print(f"  ⚠️  Network mode: {network_mode} (not mainnet)")
            self.warnings.append(f"Network mode is {network_mode}, not mainnet")
        
        # Check emergency stop mechanism
        if os.path.exists('emergency_funding_manager.py'):
            print(f"  ✅ Emergency stop: Available")
        else:
            print(f"  ⚠️  Emergency stop: Not found")
            self.warnings.append("Emergency stop mechanism not found")
        
        if security_issues:
            self.critical_issues.extend(security_issues)
            return False
            
        self.validation_results['security_validation'] = True
        return True
    
    def validate_performance(self):
        """Validate performance requirements"""
        print(f"\n🔍 PERFORMANCE VALIDATION")
        print("=" * 60)
        
        performance_issues = []
        
        # Test file structure
        required_files = [
            'main.py',
            'web_dashboard.py',
            'aave_integration.py'
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  ✅ {file_path}: Exists ({size:,} bytes)")
            else:
                error_msg = f"Required file missing: {file_path}"
                print(f"  ❌ {file_path}: Missing")
                performance_issues.append(error_msg)
        
        # Test basic functionality
        try:
            result = subprocess.run([sys.executable, '-c', 'import main; print("Basic import test passed")'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  ✅ Basic functionality: OK")
            else:
                error_msg = f"Basic functionality test failed: {result.stderr}"
                print(f"  ❌ Basic functionality: Failed")
                performance_issues.append(error_msg)
        except Exception as e:
            error_msg = f"Performance test failed: {e}"
            print(f"  ❌ Performance test: {e}")
            performance_issues.append(error_msg)
        
        if performance_issues:
            self.critical_issues.extend(performance_issues)
            return False
            
        self.validation_results['performance_validation'] = True
        return True
    
    def generate_approval_report(self):
        """Generate final network approval report"""
        print(f"\n🎯 NETWORK APPROVAL REPORT")
        print("=" * 60)
        
        total_validations = len(self.validation_results)
        passed_validations = sum(self.validation_results.values())
        success_rate = (passed_validations / total_validations * 100) if total_validations > 0 else 0
        
        print(f"📊 VALIDATION STATISTICS:")
        print(f"   Total Validations: {total_validations}")
        print(f"   Passed: {passed_validations}")
        print(f"   Failed: {total_validations - passed_validations}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for validation, status in self.validation_results.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {validation.replace('_', ' ').title()}: {'PASSED' if status else 'FAILED'}")
        
        if self.critical_issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.critical_issues)}):")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"   {i}. {issue}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        # Final approval status
        if len(self.critical_issues) == 0 and passed_validations >= 4:
            print(f"\n🎉 NETWORK APPROVAL STATUS: ✅ APPROVED")
            print(f"✅ System meets all requirements for network approval")
            print(f"🚀 Ready for mainnet deployment")
            return True
        elif len(self.critical_issues) <= 2 and passed_validations >= 3:
            print(f"\n⚠️  NETWORK APPROVAL STATUS: 🔶 CONDITIONAL APPROVAL")
            print(f"⚠️  System meets minimum requirements with minor issues")
            print(f"🔧 Address remaining issues for full approval")
            return False
        else:
            print(f"\n❌ NETWORK APPROVAL STATUS: ❌ REJECTED")
            print(f"❌ System requires significant fixes before approval")
            print(f"🛑 Address all critical issues before resubmission")
            return False
    
    def run_full_validation(self):
        """Run complete validation suite"""
        print("🚀 NETWORK APPROVAL VALIDATION SUITE")
        print("=" * 60)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all validations
        syntax_ok = self.validate_syntax_comprehensive()
        imports_ok = self.validate_imports_comprehensive()
        secrets_ok = self.validate_secrets_comprehensive()
        integrations_ok = self.validate_integrations()
        security_ok = self.validate_security()
        performance_ok = self.validate_performance()
        
        # Generate final report
        approval_status = self.generate_approval_report()
        
        return approval_status

def main():
    """Main validation entry point"""
    validator = NetworkApprovalValidator()
    approval_status = validator.run_full_validation()
    
    return 0 if approval_status else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
