
#!/usr/bin/env python3
"""
Verify that code changes are actually being applied
"""

import os
import sys
import json
import hashlib
import importlib.util

def check_specific_fixes():
    """Check if specific fixes have been applied"""
    print("🔍 VERIFYING SPECIFIC FIXES...")
    
    fixes_applied = {}
    
    # Check main.py syntax fix
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Check for the fixed function signature
        if 'def derived(self, locals: dict = None):' in content:
            fixes_applied['main_syntax_fix'] = True
            print("   ✅ main.py syntax fix applied")
        else:
            fixes_applied['main_syntax_fix'] = False
            print("   ❌ main.py syntax fix NOT applied")
    
    # Check for duplicate removal
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Count verify_coinmarketcap_api functions
        count = content.count('def verify_coinmarketcap_api(')
        if count == 1:
            fixes_applied['duplicate_removal'] = True
            print("   ✅ Duplicate function removal applied")
        else:
            fixes_applied['duplicate_removal'] = False
            print(f"   ❌ Still {count} copies of verify_coinmarketcap_api")
    
    return fixes_applied

def test_import_after_fixes():
    """Test if modules can be imported after fixes"""
    print("\n🧪 TESTING IMPORTS AFTER FIXES...")
    
    import_results = {}
    
    modules_to_test = ['main', 'arbitrum_testnet_agent']
    
    for module_name in modules_to_test:
        try:
            # Clear module from cache if it exists
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Try to import
            spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                import_results[module_name] = True
                print(f"   ✅ {module_name} imports successfully")
            else:
                import_results[module_name] = False
                print(f"   ❌ {module_name} spec loading failed")
                
        except Exception as e:
            import_results[module_name] = False
            print(f"   ❌ {module_name} import failed: {e}")
    
    return import_results

def compare_file_hashes():
    """Compare current file hashes with previous ones"""
    print("\n📊 COMPARING FILE CHANGES...")
    
    if not os.path.exists('file_hashes.json'):
        print("   ⚠️ No previous hash file found. Run debug_change_persistence.py first.")
        return {}
    
    try:
        with open('file_hashes.json', 'r') as f:
            old_hashes = json.load(f)
    except:
        print("   ❌ Could not read previous hashes")
        return {}
    
    changes_detected = {}
    for file, old_hash in old_hashes.items():
        if os.path.exists(file):
            with open(file, 'rb') as f:
                new_hash = hashlib.md5(f.read()).hexdigest()
            
            if new_hash != old_hash:
                changes_detected[file] = True
                print(f"   ✅ {file} has been modified")
            else:
                changes_detected[file] = False
                print(f"   ⚠️ {file} unchanged")
        else:
            print(f"   ❌ {file} no longer exists")
    
    return changes_detected

def main():
    print("🔍 VERIFYING CHANGES ARE APPLIED")
    print("=" * 40)
    
    # Check specific fixes
    fixes = check_specific_fixes()
    
    # Test imports
    imports = test_import_after_fixes()
    
    # Compare hashes
    changes = compare_file_hashes()
    
    # Summary
    print(f"\n📋 VERIFICATION SUMMARY:")
    total_fixes = len(fixes)
    applied_fixes = sum(fixes.values())
    
    total_imports = len(imports)
    successful_imports = sum(imports.values())
    
    print(f"   Fixes Applied: {applied_fixes}/{total_fixes}")
    print(f"   Successful Imports: {successful_imports}/{total_imports}")
    
    if applied_fixes == total_fixes and successful_imports == total_imports:
        print(f"\n✅ ALL CHANGES VERIFIED SUCCESSFULLY!")
        return True
    else:
        print(f"\n❌ Some changes are not taking effect")
        
        if applied_fixes < total_fixes:
            print(f"   • {total_fixes - applied_fixes} fixes not applied")
        
        if successful_imports < total_imports:
            print(f"   • {total_imports - successful_imports} import failures")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Check file permissions")
        print(f"   2. Restart Python processes")
        print(f"   3. Clear Python cache (__pycache__)")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
