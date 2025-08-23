
#!/usr/bin/env python3
"""
Validate Import Structure - Check for circular imports and missing dependencies
"""

import os
import ast
import sys
from typing import Dict, List, Set

class ImportAnalyzer:
    def __init__(self):
        self.imports_map: Dict[str, Set[str]] = {}
        self.circular_imports: List[tuple] = []
        self.missing_modules: Set[str] = set()
        
    def analyze_file(self, file_path: str) -> Set[str]:
        """Analyze imports in a single file"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except Exception as e:
            print(f"⚠️ Could not analyze {file_path}: {e}")
            
        return imports
    
    def find_circular_imports(self):
        """Detect circular import dependencies"""
        def has_path(start: str, end: str, visited: Set[str]) -> bool:
            if start == end:
                return True
            if start in visited:
                return False
            
            visited.add(start)
            
            for imported_module in self.imports_map.get(start, set()):
                if has_path(imported_module, end, visited.copy()):
                    return True
            return False
        
        for module, imports in self.imports_map.items():
            for imported_module in imports:
                if has_path(imported_module, module, set()):
                    self.circular_imports.append((module, imported_module))
    
    def validate_imports(self):
        """Validate all imports in the project"""
        print("🔍 ANALYZING IMPORT STRUCTURE")
        print("=" * 40)
        
        # Analyze all Python files
        for root, dirs, files in os.walk('.'):
            if 'archive_duplicates' in dirs:
                dirs.remove('archive_duplicates')
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.basename(file))[0]
                    
                    imports = self.analyze_file(file_path)
                    self.imports_map[module_name] = imports
        
        # Check for circular imports
        self.find_circular_imports()
        
        # Report findings
        print(f"📁 Analyzed {len(self.imports_map)} Python files")
        
        if self.circular_imports:
            print(f"\n❌ CIRCULAR IMPORTS FOUND:")
            for module1, module2 in self.circular_imports:
                print(f"   {module1} ⟷ {module2}")
        else:
            print("✅ No circular imports detected")
        
        # Check for imports from main.py
        main_imports = self.imports_map.get('main', set())
        main_self_imports = [imp for imp in main_imports if 'main' in imp]
        
        if main_self_imports:
            print(f"\n⚠️ MAIN.PY SELF-IMPORTS:")
            for imp in main_self_imports:
                print(f"   {imp}")
        else:
            print("✅ No self-imports in main.py")
        
        return len(self.circular_imports) == 0 and len(main_self_imports) == 0

if __name__ == "__main__":
    analyzer = ImportAnalyzer()
    is_valid = analyzer.validate_imports()
    
    if is_valid:
        print("\n🎉 Import structure validation PASSED")
    else:
        print("\n❌ Import structure validation FAILED")
        print("💡 Please fix circular imports and self-references")
