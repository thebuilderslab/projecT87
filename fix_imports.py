
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
        'from enhanced_rpc_manager import': 'from enhanced_rpc_manager import',
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
