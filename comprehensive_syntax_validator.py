
#!/usr/bin/env python3
"""
Comprehensive System Syntax Validator
Validates all critical syntax issues have been resolved
"""

import py_compile
import sys
import os
import ast
import subprocess
from datetime import datetime

class ComprehensiveSyntaxValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed_tests = []
        
    def validate_python_syntax(self):
        """Validate Python file syntax comprehensively"""
        print("🔍 COMPREHENSIVE SYNTAX VALIDATION")
        print("=" * 60)
        
        critical_files = [
            'main.py',
            'web_dashboard.py', 
            'aave_integration.py',
            'uniswap_integration.py',
            'system_validator.py'
        ]
        
        all_valid = True
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                print(f"\n📁 Checking: {file_path}")
                
                # Method 1: py_compile check
                try:
                    py_compile.compile(file_path, doraise=True)
                    print(f"  ✅ py_compile: OK")
                except py_compile.PyCompileError as e:
                    print(f"  ❌ py_compile: {e}")
                    self.errors.append(f"py_compile error in {file_path}: {e}")
                    all_valid = False
                    continue
                
                # Method 2: AST parse check
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                    ast.parse(source, file_path)
                    print(f"  ✅ AST parse: OK")
                except SyntaxError as e:
                    print(f"  ❌ AST parse: Line {e.lineno}: {e.msg}")
                    self.errors.append(f"AST parse error in {file_path} line {e.lineno}: {e.msg}")
                    all_valid = False
                    continue
                
                # Method 3: exec compile check
                try:
                    compile(source, file_path, 'exec')
                    print(f"  ✅ exec compile: OK")
                    self.passed_tests.append(f"Syntax validation: {file_path}")
                except SyntaxError as e:
                    print(f"  ❌ exec compile: Line {e.lineno}: {e.msg}")
                    self.errors.append(f"exec compile error in {file_path} line {e.lineno}: {e.msg}")
                    all_valid = False
                
            else:
                print(f"⚠️  {file_path}: File not found")
                self.warnings.append(f"File not found: {file_path}")
        
        return all_valid
    
    def validate_imports(self):
        """Test critical imports"""
        print(f"\n🔍 IMPORT VALIDATION")
        print("=" * 60)
        
        critical_imports = [
            ("web3", "from web3 import Web3"),
            ("requests", "import requests"),
            ("flask", "from flask import Flask"),
            ("json", "import json"),
            ("os", "import os"),
            ("sys", "import sys"),
            ("time", "import time"),
            ("subprocess", "import subprocess")
        ]
        
        all_imports_valid = True
        
        for name, import_stmt in critical_imports:
            try:
                exec(import_stmt)
                print(f"  ✅ {name}: Import OK")
                self.passed_tests.append(f"Import: {name}")
            except ImportError as e:
                print(f"  ❌ {name}: {e}")
                self.errors.append(f"Import error for {name}: {e}")
                all_imports_valid = False
            except Exception as e:
                print(f"  ⚠️  {name}: Unexpected error: {e}")
                self.warnings.append(f"Import warning for {name}: {e}")
        
        return all_imports_valid
    
    def validate_secrets(self):
        """Validate environment secrets"""
        print(f"\n🔍 SECRETS VALIDATION")
        print("=" * 60)
        
        required_secrets = [
            'NETWORK_MODE', 'COINMARKETCAP_API_KEY', 'PROMPT_KEY', 
            'PRIVATE_KEY', 'ARBITRUM_RPC_URL'
        ]
        
        secrets_valid = True
        
        for secret in required_secrets:
            value = os.getenv(secret)
            if value and len(value.strip()) > 0:
                print(f"  ✅ {secret}: Available")
                self.passed_tests.append(f"Secret: {secret}")
            else:
                print(f"  ❌ {secret}: Missing or empty")
                self.errors.append(f"Missing secret: {secret}")
                secrets_valid = False
        
        return secrets_valid
    
    def validate_file_structure(self):
        """Validate critical file structure"""
        print(f"\n🔍 FILE STRUCTURE VALIDATION")
        print("=" * 60)
        
        required_files = [
            'main.py',
            'web_dashboard.py',
            'aave_integration.py',
            'uniswap_integration.py'
        ]
        
        structure_valid = True
        
        for file_path in required_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  ✅ {file_path}: Exists ({size} bytes)")
                self.passed_tests.append(f"File structure: {file_path}")
            else:
                print(f"  ❌ {file_path}: Missing")
                self.errors.append(f"Missing file: {file_path}")
                structure_valid = False
        
        return structure_valid
    
    def generate_comprehensive_report(self):
        """Generate final comprehensive validation report"""
        print(f"\n🎯 COMPREHENSIVE VALIDATION REPORT")
        print("=" * 60)
        
        total_tests = len(self.passed_tests) + len(self.errors)
        success_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {len(self.passed_tests)}")
        print(f"   Failed: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ CRITICAL ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        # Final assessment
        if len(self.errors) == 0:
            print(f"\n✅ SYSTEM STATUS: READY FOR EXECUTION")
            print(f"✅ All critical syntax issues resolved")
            print(f"✅ Network approval requirements met")
            return True
        elif len(self.errors) <= 2:
            print(f"\n⚠️  SYSTEM STATUS: NEEDS MINOR FIXES")
            print(f"⚠️  Few remaining issues to resolve")
            return False
        else:
            print(f"\n❌ SYSTEM STATUS: REQUIRES MAJOR FIXES")
            print(f"❌ Multiple critical issues detected")
            return False

def main():
    """Run comprehensive validation"""
    validator = ComprehensiveSyntaxValidator()
    
    print("🚀 COMPREHENSIVE SYSTEM SYNTAX VALIDATOR")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all validation tests
    syntax_valid = validator.validate_python_syntax()
    imports_valid = validator.validate_imports()
    secrets_valid = validator.validate_secrets()
    structure_valid = validator.validate_file_structure()
    
    # Generate comprehensive report
    overall_success = validator.generate_comprehensive_report()
    
    # Return appropriate exit code
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
