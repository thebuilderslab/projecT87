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

    def verify_syntax(self):
        """Verify syntax of main files"""
        print("🔍 Verifying syntax...")

        main_files = ['main.py', 'aave_integration.py', 'web_dashboard.py']
        syntax_ok = True

        for file_path in main_files:
            if os.path.exists(file_path):
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'py_compile', file_path],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"✅ {file_path}: Syntax OK")
                    else:
                        print(f"❌ {file_path}: Syntax Error")
                        self.errors.append(f"Syntax error in {file_path}")
                        syntax_ok = False
                except Exception as e:
                    print(f"⚠️ {file_path}: Could not verify - {e}")
                    self.warnings.append(f"Could not verify {file_path}")
            else:
                print(f"⚠️ {file_path}: File not found")
                self.warnings.append(f"Missing file: {file_path}")

        return syntax_ok

    def verify_imports(self):
        """Verify critical imports work"""
        print("\n🔍 Verifying imports...")

        import_tests = [
            ('main', 'Main module'),
            ('aave_integration', 'Aave integration'),
            ('emergency_funding_manager', 'Emergency manager')
        ]

        imports_ok = True
        for module_name, description in import_tests:
            try:
                __import__(module_name)
                print(f"✅ {description}: Import OK")
            except Exception as e:
                print(f"❌ {description}: Import failed - {e}")
                self.errors.append(f"Import error in {module_name}")
                imports_ok = False

        return imports_ok

    def verify_environment(self):
        """Verify environment variables"""
        print("\n🔍 Verifying environment...")

        required_vars = ['NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY']
        env_ok = True

        for var in required_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: Set")
            else:
                print(f"❌ {var}: Missing")
                self.errors.append(f"Missing environment variable: {var}")
                env_ok = False

        return env_ok

    def run_verification(self):
        """Run complete verification"""
        print("🔍 COMPREHENSIVE SYSTEM VERIFICATION")
        print("=" * 60)

        results = {
            'syntax': self.verify_syntax(),
            'imports': self.verify_imports(),
            'environment': self.verify_environment()
        }

        print(f"\n📊 VERIFICATION RESULTS:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.title()}: {status}")

        all_passed = all(results.values())

        if self.errors:
            print(f"\n❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"   - {error}")

        if self.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")

        if all_passed:
            print(f"\n🎉 ALL VERIFICATIONS PASSED!")
            print(f"✅ System ready for operation")
        else:
            print(f"\n❌ VERIFICATION FAILED")
            print(f"🔧 Fix errors before proceeding")

        return all_passed

def main():
    """Run verification"""
    verifier = ComprehensiveSystemVerifier()
    success = verifier.run_verification()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)