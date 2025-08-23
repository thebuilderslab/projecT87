
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
