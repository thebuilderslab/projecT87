
#!/usr/bin/env python3
"""
System Cleanup Scanner
Scans all files for leftover merger fragments and syntax issues
Removes problematic code to restore system functionality
"""

import os
import re
import ast
import sys
import shutil
from datetime import datetime

class SystemCleanupScanner:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixed_files = []
        
    def scan_file_for_issues(self, file_path):
        """Scan a single file for syntax and merger issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for syntax errors
            try:
                ast.parse(content)
                print(f"✅ {file_path}: Syntax OK")
                return True
            except SyntaxError as e:
                print(f"❌ {file_path}: Syntax Error - {e}")
                return False
                
        except Exception as e:
            print(f"⚠️ {file_path}: Could not scan - {e}")
            return False
    
    def fix_common_issues(self, file_path):
        """Fix common merger artifacts and syntax issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remove duplicate imports
            lines = content.split('\n')
            seen_imports = set()
            fixed_lines = []
            
            for line in lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    if line.strip() not in seen_imports:
                        seen_imports.add(line.strip())
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # Remove merger markers
            merger_patterns = [
                r'# --- Merged from.*?---',
                r'# Removed duplicate:.*',
                r'<<<<<<< HEAD.*?>>>>>>> .*',
                r'=======',
            ]
            
            for pattern in merger_patterns:
                content = re.sub(pattern, '', content, flags=re.DOTALL)
            
            # Fix indentation issues
            content = self.fix_indentation(content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_files.append(file_path)
                print(f"🔧 Fixed: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Could not fix {file_path}: {e}")
            return False
    
    def fix_indentation(self, content):
        """Fix basic indentation issues"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            
            # Fix mixed tabs/spaces - convert tabs to 4 spaces
            line = line.expandtabs(4)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def run_cleanup(self):
        """Run comprehensive cleanup"""
        print("🧹 SYSTEM CLEANUP SCANNER")
        print("=" * 50)
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk('.'):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'archive_duplicates']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    python_files.append(os.path.join(root, file))
        
        print(f"📁 Found {len(python_files)} Python files to scan")
        
        # Scan and fix files
        syntax_errors = []
        for file_path in python_files:
            if not self.scan_file_for_issues(file_path):
                syntax_errors.append(file_path)
                # Try to fix the file
                self.fix_common_issues(file_path)
        
        # Rescan fixed files
        remaining_errors = []
        for file_path in syntax_errors:
            if not self.scan_file_for_issues(file_path):
                remaining_errors.append(file_path)
        
        # Report results
        print(f"\n📊 CLEANUP RESULTS:")
        print(f"   Files scanned: {len(python_files)}")
        print(f"   Files fixed: {len(self.fixed_files)}")
        print(f"   Remaining errors: {len(remaining_errors)}")
        
        if remaining_errors:
            print(f"\n❌ Files still have issues:")
            for file_path in remaining_errors:
                print(f"   - {file_path}")
            print("\n💡 These files may need manual review")
            return False
        else:
            print(f"\n✅ All syntax issues resolved!")
            return True

def main():
    """Run system cleanup"""
    scanner = SystemCleanupScanner()
    success = scanner.run_cleanup()
    
    if success:
        print("\n🔄 Testing system functionality...")
        
        # Test import of main module
        try:
            import main
            print("✅ main.py imports successfully")
        except Exception as e:
            print(f"❌ main.py import failed: {e}")
            return False
        
        print("\n🎉 SYSTEM CLEANUP COMPLETE")
        print("Ready to run Full System Control")
        return True
    else:
        print("\n❌ CLEANUP INCOMPLETE")
        print("Manual review required")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
