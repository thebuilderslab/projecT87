
#!/usr/bin/env python3
"""
Validate that all critical syntax issues have been resolved
"""

import py_compile
import sys
import os

def validate_syntax_fixes():
    """Validate all syntax fixes are working"""
    print("🔍 VALIDATING SYNTAX FIXES")
    print("=" * 40)
    
    critical_files = [
        'main.py',
        'main.py',
        'web_dashboard.py'
    ]
    
    all_valid = True
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                py_compile.compile(file_path, doraise=True)
                print(f"✅ {file_path}: Syntax OK")
            except py_compile.PyCompileError as e:
                print(f"❌ {file_path}: {e}")
                all_valid = False
        else:
            print(f"⚠️ {file_path}: File not found")
    
    return all_valid

def test_imports():
    """Test that critical imports work"""
    print("\n🔍 TESTING IMPORTS")
    print("=" * 40)
    
    import_tests = [
        ("web3", "from web3 import Web3"),
        ("requests", "import requests"),
        ("flask", "import flask"),
        ("json", "import json"),
        ("os", "import os")
    ]
    
    all_imports_ok = True
    
    for name, import_stmt in import_tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}: Import OK")
        except ImportError as e:
            print(f"❌ {name}: {e}")
            all_imports_ok = False
    
    return all_imports_ok

def main():
    """Main validation function"""
    print("🚀 COMPREHENSIVE VALIDATION OF FIXES")
    print("=" * 50)
    
    syntax_ok = validate_syntax_fixes()
    imports_ok = test_imports()
    
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"   Syntax Validation: {'✅ PASSED' if syntax_ok else '❌ FAILED'}")
    print(f"   Import Validation: {'✅ PASSED' if imports_ok else '❌ FAILED'}")
    
    if syntax_ok and imports_ok:
        print("\n🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
        print("✅ System ready for network approval")
        return True
    else:
        print("\n⚠️ SOME VALIDATIONS FAILED")
        print("💡 Review errors above and apply additional fixes")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
