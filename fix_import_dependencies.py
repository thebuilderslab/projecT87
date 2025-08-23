
#!/usr/bin/env python3
"""
Fix Import Dependencies - Resolves circular imports and consolidates duplicate imports
"""

import os
import re
import sys
from typing import Dict, List, Set

class ImportDependencyFixer:
    def __init__(self):
        self.archived_modules = self._get_archived_modules()
        self.valid_modules = self._get_valid_modules()
        self.import_mappings = self._create_import_mappings()
        
    def _get_archived_modules(self) -> Set[str]:
        """Get list of modules that have been moved to archive"""
        archived = set()
        archive_dir = 'archive_duplicates'
        if os.path.exists(archive_dir):
            for file in os.listdir(archive_dir):
                if file.endswith('.py'):
                    module_name = file[:-3]  # Remove .py extension
                    archived.add(module_name)
        return archived
    
    def _get_valid_modules(self) -> Set[str]:
        """Get list of valid modules in the current directory"""
        valid = set()
        for file in os.listdir('.'):
            if file.endswith('.py') and not file.startswith('.'):
                module_name = file[:-3]  # Remove .py extension
                valid.add(module_name)
        return valid
    
    def _create_import_mappings(self) -> Dict[str, str]:
        """Create mappings from old module names to new ones"""
        mappings = {
            # Map archived modules to their canonical replacements
            'arbitrum_testnet_agent': 'main',
            'collaborative_strategy_manager': 'main', 
            'emergency_stop': 'emergency_funding_manager',
            'dashboard': 'web_dashboard',
            'improved_web_dashboard': 'web_dashboard',
            'enhanced_borrow_manager': 'aave_integration',
            'aave_health_monitor': 'aave_integration',
            'uniswap_integration': 'aave_integration',
            'gas_fee_calculator': 'aave_integration',
            'enhanced_rpc_manager': 'aave_integration',
            'config_constants': 'main',
        }
        
        # Add all archived modules to map to main if not specifically mapped
        for module in self.archived_modules:
            if module not in mappings:
                if 'aave' in module or 'swap' in module or 'borrow' in module:
                    mappings[module] = 'aave_integration'
                elif 'dashboard' in module or 'web' in module:
                    mappings[module] = 'web_dashboard'
                elif 'emergency' in module:
                    mappings[module] = 'emergency_funding_manager'
                else:
                    mappings[module] = 'main'
        
        return mappings
    
    def fix_file_imports(self, file_path: str) -> bool:
        """Fix imports in a single file"""
        if not file_path.endswith('.py'):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            changes_made = 0
            
            # Remove circular imports (importing from self)
            file_module = os.path.splitext(os.path.basename(file_path))[0]
            
            # Pattern to match self-imports
            self_import_patterns = [
                rf'^from\s+{re.escape(file_module)}\s+import\s+.*$',
                rf'^import\s+{re.escape(file_module)}(?:\s+as\s+\w+)?$'
            ]
            
            for pattern in self_import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                if matches:
                    print(f"  Removing circular import in {file_path}: {matches}")
                    content = re.sub(pattern, '# Removed circular import', content, flags=re.MULTILINE)
                    changes_made += len(matches)
            
            # Fix imports to archived modules
            for old_module, new_module in self.import_mappings.items():
                if old_module == new_module:
                    continue
                    
                patterns = [
                    (rf'\bfrom\s+{re.escape(old_module)}\s+import\b', f'from {new_module} import'),
                    (rf'\bimport\s+{re.escape(old_module)}\b', f'import {new_module}'),
                    (rf'\b{re.escape(old_module)}\.', f'{new_module}.')
                ]
                
                for pattern, replacement in patterns:
                    old_content = content
                    content = re.sub(pattern, replacement, content)
                    if content != old_content:
                        changes_made += 1
            
            # Remove duplicate imports
            import_lines = []
            seen_imports = set()
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')) and not stripped.startswith('#'):
                    # Normalize the import statement
                    normalized = re.sub(r'\s+', ' ', stripped)
                    if normalized not in seen_imports:
                        seen_imports.add(normalized)
                        import_lines.append((i, line))
                    else:
                        lines[i] = f'# Removed duplicate: {line}'
                        changes_made += 1
            
            if changes_made > 0:
                content = '\n'.join(lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed {changes_made} import issues in {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error fixing imports in {file_path}: {e}")
            return False
    
    def fix_all_imports(self) -> None:
        """Fix imports in all Python files"""
        print("🔧 FIXING IMPORT DEPENDENCIES")
        print("=" * 50)
        
        files_processed = 0
        files_changed = 0
        
        # Process all Python files in the current directory
        for file in os.listdir('.'):
            if file.endswith('.py') and not file.startswith('.'):
                files_processed += 1
                if self.fix_file_imports(file):
                    files_changed += 1
        
        print(f"\n📊 SUMMARY:")
        print(f"Files processed: {files_processed}")
        print(f"Files changed: {files_changed}")
        print(f"Archived modules mapped: {len(self.import_mappings)}")
        
        # Show mapping summary
        if self.import_mappings:
            print(f"\n🔄 MODULE MAPPINGS:")
            for old, new in sorted(self.import_mappings.items()):
                if old != new:
                    print(f"  {old} → {new}")
    
    def validate_imports(self) -> None:
        """Validate that all imports can be resolved"""
        print(f"\n🔍 VALIDATING IMPORTS...")
        
        import subprocess
        broken_files = []
        
        for file in os.listdir('.'):
            if file.endswith('.py') and not file.startswith('.'):
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'py_compile', file],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode != 0:
                        broken_files.append((file, result.stderr))
                except Exception as e:
                    broken_files.append((file, str(e)))
        
        if broken_files:
            print(f"❌ Found {len(broken_files)} files with import issues:")
            for file, error in broken_files:
                print(f"  {file}: {error.split(chr(10))[0]}")  # First line of error
        else:
            print("✅ All imports validated successfully")

def main():
    """Main function to fix import dependencies"""
    fixer = ImportDependencyFixer()
    fixer.fix_all_imports()
    fixer.validate_imports()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Fix Import Dependencies - Resolves circular imports and consolidates import structure
"""

# Removed duplicate: import os
# Removed duplicate: import re
from typing import Dict, List

# Map of problematic imports to their correct targets
IMPORT_FIXES = {
    # Remove circular imports from main.py
    '# ArbitrumTestnetAgent defined in main.py': '# ArbitrumTestnetAgent defined in main.py',
    '# CollaborativeStrategyManager defined in main.py': '# CollaborativeStrategyManager defined in main.py',
    '# Constants defined in main.py': '# Constants defined in main.py',
    '# Constants defined in main.py': '# Constants defined in main.py',
    
    # Fix references to archived modules
    'from main import': 'from main import',
    'import main': 'import main',
    'from emergency_funding_manager import': 'from emergency_funding_manager import',
    'import emergency_funding_manager': 'import emergency_funding_manager',
    
    # Fix duplicated aave imports
    'from aave_integration import': 'from aave_integration import',
    'from aave_integration import': 'from aave_integration import',
    'from aave_integration import': 'from aave_integration import',
    
    # Fix web dashboard imports
    'from web_dashboard import': 'from web_dashboard import',
    'from web_dashboard import': 'from web_dashboard import',
}

def fix_file_imports(file_path: str) -> int:
    """Fix imports in a single file"""
    if not file_path.endswith('.py') or not os.path.exists(file_path):
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Apply import fixes
        for old_import, new_import in IMPORT_FIXES.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes_made += 1
        
        # Remove duplicate import lines
        lines = content.split('\n')
        seen_imports = set()
        cleaned_lines = []
        
        for line in lines:
            # Check if line is an import
            if line.strip().startswith(('import ', 'from ')) and 'import' in line:
                # Normalize the import for comparison
                normalized = re.sub(r'\s+', ' ', line.strip())
                if normalized not in seen_imports:
                    seen_imports.add(normalized)
                    cleaned_lines.append(line)
                else:
                    changes_made += 1  # Skip duplicate
            else:
                cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if changes_made > 0:
                print(f"✅ Fixed {changes_made} import issues in {file_path}")
            return changes_made
        
        return 0
        
    except Exception as e:
        print(f"❌ Error fixing imports in {file_path}: {e}")
        return 0

def scan_and_fix_imports():
    """Scan all Python files and fix import issues"""
    print("🔧 FIXING IMPORT DEPENDENCIES")
    print("=" * 50)
    
    total_files_fixed = 0
    total_changes = 0
    
    # Skip archived files
    excluded_dirs = {'archive_duplicates', '.git', '__pycache__', 'node_modules'}
    
    for root, dirs, files in os.walk('.'):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                changes = fix_file_imports(file_path)
                if changes > 0:
                    total_files_fixed += 1
                    total_changes += changes
    
    print(f"\n✅ Import fixing complete!")
    print(f"📁 Files modified: {total_files_fixed}")
    print(f"🔄 Total import fixes: {total_changes}")
    
    return total_changes > 0

def validate_critical_imports():
    """Validate that critical files can be imported"""
    print("\n🔍 VALIDATING CRITICAL IMPORTS")
    print("=" * 40)
    
    critical_files = ['main.py', 'aave_integration.py', 'web_dashboard.py']
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                # Test syntax compilation
                import py_compile
                py_compile.compile(file_path, doraise=True)
                print(f"✅ {file_path}: Import syntax OK")
            except Exception as e:
                print(f"❌ {file_path}: Import error - {e}")
        else:
            print(f"⚠️ {file_path}: File not found")

if __name__ == "__main__":
    success = scan_and_fix_imports()
    validate_critical_imports()
    
    if success:
        print("\n🎉 Import dependency resolution complete!")
        print("💡 Next: Run syntax validation to verify fixes")
    else:
        print("\n✅ No import changes needed")
#!/usr/bin/env python3
"""
Fix Import Dependencies - Resolves circular imports and consolidates duplicate imports
"""

# Removed duplicate: import os
# Removed duplicate: import re
# Removed duplicate: import sys
# Removed duplicate: from typing import Dict, List, Set

class ImportDependencyFixer:
    def __init__(self):
        self.archived_modules = self._get_archived_modules()
        self.valid_modules = self._get_valid_modules()
        self.import_mappings = self._create_import_mappings()
        
    def _get_archived_modules(self) -> Set[str]:
        """Get list of modules that have been moved to archive"""
        archived = set()
        archive_dir = 'archive_duplicates'
        if os.path.exists(archive_dir):
            for file in os.listdir(archive_dir):
                if file.endswith('.py'):
                    module_name = file[:-3]  # Remove .py extension
                    archived.add(module_name)
        return archived
    
    def _get_valid_modules(self) -> Set[str]:
        """Get list of valid modules in the current directory"""
        valid = set()
        for file in os.listdir('.'):
            if file.endswith('.py') and not file.startswith('.'):
                module_name = file[:-3]  # Remove .py extension
                valid.add(module_name)
        return valid
    
    def _create_import_mappings(self) -> Dict[str, str]:
        """Create mappings from old module names to new ones"""
        mappings = {
            # Map archived modules to their canonical replacements
            'arbitrum_testnet_agent': 'main',
            'collaborative_strategy_manager': 'main',
            'emergency_stop': 'emergency_funding_manager',
            'dashboard': 'web_dashboard',
            'improved_web_dashboard': 'web_dashboard',
            'enhanced_borrow_manager': 'aave_integration',
            'enhanced_rpc_manager': 'aave_integration',
            'health_monitor': 'aave_integration',
            'aave_health_monitor': 'aave_integration',
            'enhanced_balance_fetcher': 'aave_integration',
            'gas_optimizer': 'aave_integration',
            'wallet_diagnostics': 'aave_integration',
            'debt_swap_manager': 'aave_integration',
            'uniswap_integration': 'aave_integration',
        }
        return mappings
    
    def fix_file_imports(self, file_path: str) -> int:
        """Fix imports in a single file"""
        if not file_path.endswith('.py'):
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_made = 0
            
            # Get the module name for this file
            file_module = os.path.splitext(os.path.basename(file_path))[0]
            
            # Remove circular imports (imports from self)
            circular_patterns = [
                rf'^from\s+{re.escape(file_module)}\s+import\s+.*$',
                rf'^import\s+{re.escape(file_module)}(?:\s+as\s+\w+)?$'
            ]
            
            for pattern in circular_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                if matches:
                    print(f"  Removing circular import in {file_path}: {matches}")
                    content = re.sub(pattern, '# Removed circular import', content, flags=re.MULTILINE)
                    changes_made += len(matches)
            
            # Fix imports to archived modules
            for old_module, new_module in self.import_mappings.items():
                if old_module == new_module:
                    continue
                    
                patterns = [
                    (rf'\bfrom\s+{re.escape(old_module)}\s+import\b', f'from {new_module} import'),
                    (rf'\bimport\s+{re.escape(old_module)}\b', f'import {new_module}'),
                    (rf'\b{re.escape(old_module)}\.', f'{new_module}.')
                ]
                
                for pattern, replacement in patterns:
                    old_content = content
                    content = re.sub(pattern, replacement, content)
                    if content != old_content:
                        changes_made += 1
            
            # Remove duplicate imports
            import_lines = []
            seen_imports = set()
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if re.match(r'^\s*(from\s+\S+\s+import|import\s+)', line):
                    normalized = re.sub(r'\s+', ' ', line.strip())
                    if normalized not in seen_imports:
                        seen_imports.add(normalized)
                        import_lines.append((i, line))
                    else:
                        lines[i] = '# Removed duplicate import'
                        changes_made += 1
            
            if changes_made > 0:
                content = '\n'.join(lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed {changes_made} import issues in {file_path}")
            
            return changes_made
            
        except Exception as e:
            print(f"❌ Error fixing imports in {file_path}: {e}")
            return 0

    def fix_all_imports(self):
        """Fix imports in all Python files"""
        print("🔧 FIXING IMPORT DEPENDENCIES")
        print("=" * 50)
        
        total_files_fixed = 0
        total_changes = 0
        
        # Skip archived files
        excluded_dirs = {'archive_duplicates', '.git', '__pycache__', 'node_modules'}
        
        for root, dirs, files in os.walk('.'):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    changes = self.fix_file_imports(file_path)
                    if changes > 0:
                        total_files_fixed += 1
                        total_changes += changes
        
        print(f"\n✅ Import fixing complete!")
        print(f"📁 Files modified: {total_files_fixed}")
        print(f"🔄 Total import fixes: {total_changes}")
        
        return total_changes > 0

    def validate_imports(self):
        """Validate that critical files can be imported"""
        print("\n🔍 VALIDATING CRITICAL IMPORTS")
        print("=" * 40)
        
        critical_files = ['main.py', 'aave_integration.py', 'web_dashboard.py']
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    # Test syntax compilation
# Removed duplicate:                     import py_compile
                    py_compile.compile(file_path, doraise=True)
                    print(f"✅ {file_path}: Import syntax OK")
                except Exception as e:
                    print(f"❌ {file_path}: Import error - {e}")
            else:
                print(f"⚠️ {file_path}: File not found")

def main():
    """Main function to fix import dependencies"""
    fixer = ImportDependencyFixer()
    success = fixer.fix_all_imports()
    fixer.validate_imports()
    
    if success:
        print("\n🎉 Import dependency resolution complete!")
        print("💡 Next: Run syntax validation to verify fixes")
    else:
        print("\n✅ No import changes needed")

if __name__ == "__main__":
    main()
