
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
        self.issues_found = []
        self.files_processed = []
        self.backup_dir = "backup_before_cleanup"
        self.critical_files = [
            'main.py',
            'aave_integration.py', 
            'web_dashboard.py',
            'system_validator.py',
            'comprehensive_system_audit.py'
        ]
        
    def create_backup(self, file_path):
        """Create backup of file before modification"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        backup_path = os.path.join(self.backup_dir, f"{os.path.basename(file_path)}.backup")
        shutil.copy2(file_path, backup_path)
        print(f"📋 Backup created: {backup_path}")
    
    def scan_for_merger_leftovers(self, file_path):
        """Scan file for common merger leftover patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            issues = []
            
            # Pattern 1: Duplicate function definitions
            function_names = {}
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    func_name = line.split('(')[0].replace('def ', '').strip()
                    if func_name in function_names:
                        issues.append(f"Duplicate function '{func_name}' at lines {function_names[func_name]} and {i+1}")
                    function_names[func_name] = i+1
            
            # Pattern 2: Merge conflict markers
            conflict_markers = ['<<<<<<<', '>>>>>>>', '=======']
            for i, line in enumerate(lines):
                for marker in conflict_markers:
                    if marker in line:
                        issues.append(f"Merge conflict marker '{marker}' at line {i+1}")
            
            # Pattern 3: Incomplete function definitions
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.endswith(':') and not stripped.startswith('#'):
                    # Check if next line is properly indented or exists
                    if i+1 < len(lines):
                        next_line = lines[i+1]
                        if next_line.strip() == '' or not next_line.startswith('    '):
                            if not any(lines[j].strip().startswith('    ') for j in range(i+1, min(i+5, len(lines)))):
                                issues.append(f"Incomplete function/class definition at line {i+1}: {stripped}")
            
            # Pattern 4: Orphaned decorators
            for i, line in enumerate(lines):
                if line.strip().startswith('@') and i+1 < len(lines):
                    next_line = lines[i+1].strip()
                    if not (next_line.startswith('def ') or next_line.startswith('class ') or next_line.startswith('@')):
                        issues.append(f"Orphaned decorator at line {i+1}: {line.strip()}")
            
            # Pattern 5: Duplicate imports
            imports_seen = set()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    if stripped in imports_seen:
                        issues.append(f"Duplicate import at line {i+1}: {stripped}")
                    imports_seen.add(stripped)
            
            return issues
            
        except Exception as e:
            print(f"❌ Error scanning {file_path}: {e}")
            return []
    
    def fix_syntax_issues(self, file_path):
        """Fix common syntax issues in file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            fixed_lines = []
            i = 0
            changes_made = False
            
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                # Fix 1: Remove merge conflict markers
                if any(marker in line for marker in ['<<<<<<<', '>>>>>>>', '=======']):
                    changes_made = True
                    print(f"  🔧 Removing merge conflict marker at line {i+1}")
                    i += 1
                    continue
                
                # Fix 2: Fix incomplete function definitions
                if stripped.endswith(':') and not stripped.startswith('#'):
                    # Look ahead to see if there's content
                    has_content = False
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j].strip() and lines[j].startswith('    '):
                            has_content = True
                            break
                    
                    if not has_content and (stripped.startswith('def ') or stripped.startswith('class ')):
                        fixed_lines.append(line)
                        if stripped.startswith('def '):
                            fixed_lines.append('        pass')
                        else:  # class
                            fixed_lines.append('    pass')
                        changes_made = True
                        print(f"  🔧 Fixed incomplete definition at line {i+1}")
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                
                i += 1
            
            # Fix 3: Remove duplicate function definitions (keep last one)
            final_lines = []
            function_definitions = {}
            
            for i, line in enumerate(fixed_lines):
                if line.strip().startswith('def '):
                    func_name = line.split('(')[0].replace('def ', '').strip()
                    if func_name in function_definitions:
                        # Mark previous definition for removal
                        prev_start = function_definitions[func_name]['start']
                        prev_end = function_definitions[func_name]['end']
                        for j in range(prev_start, prev_end + 1):
                            if j < len(final_lines):
                                final_lines[j] = None  # Mark for removal
                        changes_made = True
                        print(f"  🔧 Removing duplicate function '{func_name}'")
                    
                    # Find end of current function
                    func_end = i
                    for j in range(i+1, len(fixed_lines)):
                        if fixed_lines[j].strip() and not fixed_lines[j].startswith('    ') and not fixed_lines[j].startswith('\t'):
                            break
                        func_end = j
                    
                    function_definitions[func_name] = {'start': len(final_lines), 'end': len(final_lines) + (func_end - i)}
                
                final_lines.append(line)
            
            # Remove None entries (marked duplicates)
            final_lines = [line for line in final_lines if line is not None]
            
            if changes_made:
                # Write fixed content
                fixed_content = '\n'.join(final_lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"  ✅ Fixed syntax issues in {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            return False
    
    def validate_syntax(self, file_path):
        """Validate Python syntax of file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return True, "Syntax OK"
        except SyntaxError as e:
            return False, f"Syntax Error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def clean_file(self, file_path):
        """Clean a single file of merger leftovers"""
        print(f"\n🔍 Cleaning file: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"  ⚠️ File not found: {file_path}")
            return False
        
        # Create backup
        self.create_backup(file_path)
        
        # Scan for issues
        issues = self.scan_for_merger_leftovers(file_path)
        if issues:
            print(f"  📋 Found {len(issues)} issues:")
            for issue in issues[:5]:  # Show first 5
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more")
        
        # Fix syntax issues
        fixed = self.fix_syntax_issues(file_path)
        
        # Validate final syntax
        valid, msg = self.validate_syntax(file_path)
        if valid:
            print(f"  ✅ Syntax validation passed")
            return True
        else:
            print(f"  ❌ Syntax validation failed: {msg}")
            return False
    
    def run_cleanup(self):
        """Run complete system cleanup"""
        print("🚀 SYSTEM CLEANUP SCANNER")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success_count = 0
        total_files = len(self.critical_files)
        
        for file_path in self.critical_files:
            success = self.clean_file(file_path)
            if success:
                success_count += 1
            self.files_processed.append(file_path)
        
        print(f"\n📊 CLEANUP SUMMARY")
        print("=" * 30)
        print(f"Files processed: {len(self.files_processed)}")
        print(f"Successfully cleaned: {success_count}")
        print(f"Failed: {total_files - success_count}")
        
        if success_count == total_files:
            print("\n✅ ALL FILES CLEANED SUCCESSFULLY")
            print("🚀 System should now be ready to run")
            return True
        else:
            print(f"\n⚠️ {total_files - success_count} files still have issues")
            return False

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
