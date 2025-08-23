
#!/usr/bin/env python3
"""
Debug why code changes aren't persisting
"""

import os
import ast
import sys
import time
import hashlib
import traceback

def check_file_syntax(filename):
    """Check if file has valid Python syntax"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        ast.parse(content, filename)
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax Error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {e}"

def get_file_hash(filename):
    """Get file hash to detect changes"""
    try:
        with open(filename, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def test_import(module_name):
    """Test if module can be imported"""
    try:
        __import__(module_name)
        return True, "Import successful"
    except Exception as e:
        return False, f"Import failed: {e}"

def main():
    print("🔍 DEBUGGING CHANGE PERSISTENCE ISSUES")
    print("=" * 50)
    
    critical_files = [
        'main.py',
        'arbitrum_testnet_agent.py',
        'aave_integration.py',
        'web_dashboard.py'
    ]
    
    # Check syntax errors
    print("\n1️⃣ SYNTAX VALIDATION:")
    syntax_issues = []
    for file in critical_files:
        if os.path.exists(file):
            valid, msg = check_file_syntax(file)
            status = "✅" if valid else "❌"
            print(f"   {status} {file}: {msg}")
            if not valid:
                syntax_issues.append((file, msg))
    
    # Check file permissions
    print("\n2️⃣ FILE PERMISSIONS:")
    for file in critical_files:
        if os.path.exists(file):
            readable = os.access(file, os.R_OK)
            writable = os.access(file, os.W_OK)
            print(f"   {file}: Read={readable}, Write={writable}")
    
    # Check for duplicate functions
    print("\n3️⃣ DUPLICATE FUNCTION CHECK:")
    if os.path.exists('main.py'):
        try:
            with open('main.py', 'r') as f:
                content = f.read()
            
            # Count function definitions
            function_counts = {}
            for line in content.split('\n'):
                if line.strip().startswith('def '):
                    func_name = line.split('(')[0].replace('def ', '').strip()
                    function_counts[func_name] = function_counts.get(func_name, 0) + 1
            
            duplicates = {k: v for k, v in function_counts.items() if v > 1}
            if duplicates:
                print(f"   ❌ Found duplicate functions: {duplicates}")
            else:
                print(f"   ✅ No duplicate functions found")
                
        except Exception as e:
            print(f"   ❌ Error checking duplicates: {e}")
    
    # Check import issues
    print("\n4️⃣ IMPORT VALIDATION:")
    modules_to_test = [
        'main',
        'arbitrum_testnet_agent', 
        'aave_integration'
    ]
    
    for module in modules_to_test:
        if f"{module}.py" in [f for f in os.listdir('.') if f.endswith('.py')]:
            success, msg = test_import(module)
            status = "✅" if success else "❌"
            print(f"   {status} {module}: {msg}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    if syntax_issues:
        print(f"❌ Found {len(syntax_issues)} syntax issues:")
        for file, issue in syntax_issues:
            print(f"   • {file}: {issue}")
        print(f"\n💡 RECOMMENDATION: Fix syntax errors first - they prevent code execution!")
    else:
        print(f"✅ No critical syntax issues found")
    
    # File change monitoring
    print(f"\n5️⃣ MONITORING FILE CHANGES...")
    file_hashes = {}
    for file in critical_files:
        if os.path.exists(file):
            file_hashes[file] = get_file_hash(file)
    
    print(f"Current file hashes recorded. Make a change and run this script again to verify persistence.")
    
    # Save hashes for comparison
    import json
    with open('file_hashes.json', 'w') as f:
        json.dump(file_hashes, f, indent=2)
    
    return len(syntax_issues) == 0

if __name__ == "__main__":
    success = main()
    if not success:
        print(f"\n🚨 ACTION REQUIRED: Fix syntax errors before making other changes!")
        sys.exit(1)
    else:
        print(f"\n✅ System ready for changes")
