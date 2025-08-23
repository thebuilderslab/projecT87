
#!/usr/bin/env python3
"""
Comprehensive System Verifier
Validates all system components before deployment
"""

import os
import sys
import subprocess
import traceback
from datetime import datetime

class ComprehensiveSystemVerifier:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed_tests = []
        
    def validate_syntax(self):
        """Validate Python file syntax"""
        print("🔍 SYNTAX VALIDATION")
        print("=" * 50)
        
        critical_files = [
            'main.py',
            'web_dashboard.py', 
            'aave_integration.py',
            'aave_integration.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    result = subprocess.run(
                        ['python', '-m', 'py_compile', file_path],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"✅ {file_path}: Syntax OK")
                        self.passed_tests.append(f"Syntax: {file_path}")
                    else:
                        error_msg = result.stderr.strip()
                        print(f"❌ {file_path}: {error_msg}")
                        self.errors.append(f"Syntax error in {file_path}: {error_msg}")
                except Exception as e:
                    error_msg = f"Failed to check {file_path}: {e}"
                    print(f"❌ {file_path}: {error_msg}")
                    self.errors.append(error_msg)
            else:
                warning_msg = f"File not found: {file_path}"
                print(f"⚠️ {file_path}: Not found")
                self.warnings.append(warning_msg)
                
    def validate_imports(self):
        """Validate critical imports"""
        print("\n🔍 IMPORT VALIDATION")
        print("=" * 50)
        
        import_tests = [
            ('web3', 'from web3 import Web3'),
            ('requests', 'import requests'),
            ('flask', 'from flask import Flask'),
            ('json', 'import json'),
            ('os', 'import os')
        ]
        
        for name, import_stmt in import_tests:
            try:
                exec(import_stmt)
                print(f"✅ {name}: Import successful")
                self.passed_tests.append(f"Import: {name}")
            except ImportError as e:
                error_msg = f"Import failed for {name}: {e}"
                print(f"❌ {name}: {error_msg}")
                self.errors.append(error_msg)
                
    def validate_secrets(self):
        """Validate environment secrets"""
        print("\n🔍 SECRETS VALIDATION")
        print("=" * 50)
        
        required_secrets = [
            'NETWORK_MODE',
            'COINMARKETCAP_API_KEY',
            'PRIVATE_KEY',
            'ARBITRUM_RPC_URL'
        ]
        
        for secret in required_secrets:
            value = os.getenv(secret)
            if value and len(value.strip()) > 0:
                print(f"✅ {secret}: Available")
                self.passed_tests.append(f"Secret: {secret}")
            else:
                error_msg = f"Missing or empty secret: {secret}"
                print(f"❌ {secret}: Missing")
                self.errors.append(error_msg)
                
    def validate_network_config(self):
        """Validate network configuration"""
        print("\n🔍 NETWORK CONFIGURATION")
        print("=" * 50)
        
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        arbitrum_rpc = os.getenv('ARBITRUM_RPC_URL', '')
        
        if network_mode == 'mainnet':
            if 'arb1.arbitrum.io' in arbitrum_rpc:
                print("✅ Network: Mainnet configuration correct")
                self.passed_tests.append("Network: Mainnet config")
            else:
                error_msg = "Mainnet mode but RPC URL not mainnet"
                print(f"❌ Network: {error_msg}")
                self.errors.append(error_msg)
        else:
            print(f"⚠️ Network: Mode is {network_mode}")
            self.warnings.append(f"Network mode: {network_mode}")
            
    def run_full_verification(self):
        """Run complete system verification"""
        print("🚀 COMPREHENSIVE SYSTEM VERIFICATION")
        print("=" * 60)
        
        self.validate_syntax()
        self.validate_imports()
        self.validate_secrets()
        self.validate_network_config()
        
        # Generate summary
        print(f"\n📊 VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {len(self.passed_tests)}")
        print(f"⚠️ Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        if self.errors:
            print(f"\n❌ CRITICAL ERRORS:")
            for error in self.errors:
                print(f"   • {error}")
                
        if self.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
                
        success = len(self.errors) == 0
        
        if success:
            print(f"\n🎉 SYSTEM READY FOR DEPLOYMENT")
        else:
            print(f"\n🛑 SYSTEM NOT READY - FIX ERRORS FIRST")
            
        return success

def main():
    """Main verification function"""
    verifier = ComprehensiveSystemVerifier()
    success = verifier.run_full_verification()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
