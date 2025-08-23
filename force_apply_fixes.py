
#!/usr/bin/env python3
"""
Force apply critical fixes to ensure changes take effect
"""

import os
import shutil
import glob

def backup_files():
    """Create backups of critical files"""
    print("💾 Creating backups...")
    
    backup_dir = "backup_before_fixes"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    critical_files = ['main.py', 'arbitrum_testnet_agent.py', 'aave_integration.py']
    
    for file in critical_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))
            print(f"   ✅ Backed up {file}")

def clear_python_cache():
    """Clear Python cache files"""
    print("\n🧹 Clearing Python cache...")
    
    # Remove __pycache__ directories
    for cache_dir in glob.glob("**/__pycache__", recursive=True):
        shutil.rmtree(cache_dir)
        print(f"   ✅ Removed {cache_dir}")
    
    # Remove .pyc files
    for pyc_file in glob.glob("**/*.pyc", recursive=True):
        os.remove(pyc_file)
        print(f"   ✅ Removed {pyc_file}")

def fix_main_py_syntax():
    """Fix critical syntax errors in main.py"""
    print("\n🔧 Fixing main.py syntax errors...")
    
    if not os.path.exists('main.py'):
        print("   ❌ main.py not found")
        return False
    
    with open('main.py', 'r') as f:
        content = f.read()
    
    fixes_applied = 0
    
    # Fix the derived function signature
    if 'def derived(self, locals.Dict] = None) :' in content:
        content = content.replace(
            'def derived(self, locals.Dict] = None) :',
            'def derived(self, locals: dict = None):'
        )
        fixes_applied += 1
        print("   ✅ Fixed derived function signature")
    
    # Remove duplicate function definitions
    lines = content.split('\n')
    cleaned_lines = []
    function_definitions = set()
    
    for line in lines:
        if line.strip().startswith('def '):
            func_signature = line.strip()
            if func_signature not in function_definitions:
                function_definitions.add(func_signature)
                cleaned_lines.append(line)
            else:
                print(f"   ✅ Removed duplicate: {func_signature[:50]}...")
                fixes_applied += 1
        else:
            cleaned_lines.append(line)
    
    if fixes_applied > 0:
        with open('main.py', 'w') as f:
            f.write('\n'.join(cleaned_lines))
        print(f"   ✅ Applied {fixes_applied} fixes to main.py")
        return True
    else:
        print("   ✅ No fixes needed in main.py")
        return True

def validate_syntax():
    """Validate syntax of all Python files"""
    print("\n✅ Validating syntax...")
    
    import ast
    python_files = glob.glob("*.py")
    
    syntax_errors = []
    for file in python_files:
        try:
            with open(file, 'r') as f:
                ast.parse(f.read(), file)
            print(f"   ✅ {file}: Syntax OK")
        except SyntaxError as e:
            syntax_errors.append((file, e.lineno, e.msg))
            print(f"   ❌ {file}: Line {e.lineno}: {e.msg}")
    
    return len(syntax_errors) == 0

def main():
    print("🚀 FORCE APPLYING CRITICAL FIXES")
    print("=" * 40)
    
    # Backup files
    backup_files()
    
    # Clear cache
    clear_python_cache()
    
    # Fix main.py
    main_fixed = fix_main_py_syntax()
    
    # Validate syntax
    syntax_valid = validate_syntax()
    
    print(f"\n📊 RESULTS:")
    print(f"   main.py fixed: {'✅' if main_fixed else '❌'}")
    print(f"   Syntax valid: {'✅' if syntax_valid else '❌'}")
    
    if main_fixed and syntax_valid:
        print(f"\n🎉 ALL CRITICAL FIXES APPLIED SUCCESSFULLY!")
        print(f"   Changes should now take effect properly.")
        return True
    else:
        print(f"\n❌ Some issues remain. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🔄 RECOMMENDED NEXT STEPS:")
        print(f"   1. Run: python verify_changes.py")
        print(f"   2. Test your system")
        print(f"   3. If issues persist, check file permissions")
