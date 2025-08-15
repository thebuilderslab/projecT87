
#!/usr/bin/env python3
"""
Fix broken imports after deduplication
"""

import os
import re

def fix_broken_imports():
    """Fix imports that reference archived files"""
    
    # Map of old imports to new canonical imports
    import_fixes = {
        'from aave_integration import': 'from aave_integration import',
        '# emergency_stop functionality is integrated': '# emergency_stop functionality is integrated',
        '# emergency_launch functionality is integrated': '# emergency_launch functionality is integrated',  
        '# emergency_stop functionality is integrated': '# emergency_stop functionality is integrated',
        '# emergency_launch functionality is integrated': '# emergency_launch functionality is integrated',
        '# run_autonomous functionality is integrated': '# run_autonomous functionality is integrated',
        '# run_autonomous functionality is integrated': '# run_autonomous functionality is integrated'
    }
    
    files_fixed = 0
    
    for root, dirs, files in os.walk("."):
        # Skip archived directory
        if "archive_duplicates" in dirs:
            dirs.remove("archive_duplicates")
        
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Apply import fixes
                    for old_import, new_import in import_fixes.items():
                        if old_import in content:
                            content = content.replace(old_import, new_import)
                    
                    # Write back if changed
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        files_fixed += 1
                        print(f"✅ Fixed imports in {file_path}")
                
                except Exception as e:
                    print(f"⚠️ Error processing {file_path}: {e}")
    
    print(f"\n🔧 Fixed imports in {files_fixed} files")

if __name__ == "__main__":
    print("🔧 Fixing broken imports...")
    fix_broken_imports()
    print("✅ Import fixes complete!")
#!/usr/bin/env python3
"""
Fix Imports After Deduplication
Automatically update import statements to reference canonical files
"""

import os
import re

# Mapping of archived files to their canonical replacements
IMPORT_MAPPINGS = {
    'arbitrum_testnet_agent': 'main',
    'enhanced_rpc_manager': 'aave_integration',
    'emergency_stop': 'emergency_funding_manager',
    'emergency_launch': 'emergency_funding_manager',
    'collaborative_strategy_manager': 'main',
    'enhanced_borrow_manager': 'aave_integration',
    'health_monitor': 'aave_integration',
    'web_dashboard': 'web_dashboard',  # Keep as is
    'config': 'main',
    'enhanced_contract_manager': 'aave_integration',
    'contract_validator': 'aave_integration',
    'network_validator': 'aave_integration',
    'gas_optimizer': 'aave_integration',
    'manual_controls': 'main',
    'dashboard': 'web_dashboard',
    'strategy_manager': 'main',
    'autonomous_launcher': 'main',
    'mainnet_launcher': 'main',
    'system_diagnostic': 'main',
    'wallet_diagnostics': 'aave_integration',
    'market_signal_strategy': 'main',
    'debt_swap_manager': 'aave_integration',
    'uniswap_integration': 'aave_integration',
}

def fix_file_imports(file_path):
    """Fix imports in a single file"""
    if not file_path.endswith('.py'):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Fix import statements
        for old_module, new_module in IMPORT_MAPPINGS.items():
            # Pattern 1: from old_module import ...
            pattern1 = rf'\bfrom\s+{re.escape(old_module)}\s+import\b'
            replacement1 = f'from {new_module} import'
            content, count1 = re.subn(pattern1, replacement1, content)
            changes_made += count1
            
            # Pattern 2: import old_module
            pattern2 = rf'\bimport\s+{re.escape(old_module)}\b'
            replacement2 = f'import {new_module}'
            content, count2 = re.subn(pattern2, replacement2, content)
            changes_made += count2
            
            # Pattern 3: old_module.something
            pattern3 = rf'\b{re.escape(old_module)}\.'
            replacement3 = f'{new_module}.'
            content, count3 = re.subn(pattern3, replacement3, content)
            changes_made += count3
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {changes_made} imports in {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error fixing imports in {file_path}: {e}")
        return False

def fix_all_imports():
    """Fix imports in all Python files"""
    print("🔧 Fixing imports after deduplication...")
    
    files_fixed = 0
    total_changes = 0
    
    # Process all Python files
    for root, dirs, files in os.walk('.'):
        # Skip archive directory
        if 'archive_duplicates' in dirs:
            dirs.remove('archive_duplicates')
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_file_imports(file_path):
                    files_fixed += 1
    
    print(f"✅ Import fixing complete!")
    print(f"📁 Files modified: {files_fixed}")
    
    return files_fixed > 0

if __name__ == "__main__":
    success = fix_all_imports()
    
    if success:
        print("\n🔄 Re-running verification...")
        os.system("python verify_deduplication_complete.py")
    else:
        print("\n✅ No import changes needed")
