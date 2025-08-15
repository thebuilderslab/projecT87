
#!/usr/bin/env python3
"""
Comprehensive System Audit Script
Combines all deduplication, syntax checking, and error reporting features
"""

import os
import difflib
import shutil
import subprocess
import re
import ast
import json
from collections import defaultdict
from datetime import datetime

# Enhanced keywords for feature grouping
KEYWORDS = [
    "diagnostic", "compliance", "launcher", "dashboard", "sync", "test", 
    "emergency", "health_monitor", "fetcher", "validator", "borrow", 
    "aave", "uniswap", "integration", "rpc", "gas", "agent", "autonomous",
    "strategy", "market_signal", "enhanced", "fix", "comprehensive", "web"
]

BASE_DIR = "."
ARCHIVE_DIR = "archive_duplicates"
REPORT_FILE = "comprehensive_audit_report.txt"

def scan_files():
    """Scan for all Python files in the project"""
    print("🔍 Scanning and grouping files by feature keyword...")
    
    py_files = []
    excluded_dirs = {'.git', '__pycache__', 'node_modules', '.replit_cache', 'archive_duplicates'}
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for f in files:
            if f.endswith(".py") and not f.startswith('.'):
                full_path = os.path.join(root, f)
                if os.path.getsize(full_path) > 0:  # Skip empty files
                    py_files.append(full_path)
    
    print(f"📁 Found {len(py_files)} Python files")
    return py_files

def group_by_keyword(files):
    """Group files by functionality keywords"""
    groups = defaultdict(list)
    
    for f in files:
        name_lower = os.path.basename(f).lower()
        matched = False
        
        # Check for exact keyword matches first
        for kw in KEYWORDS:
            if kw in name_lower:
                groups[kw].append(f)
                matched = True
                break
        
        # Special grouping logic for similar files
        if not matched:
            if any(word in name_lower for word in ['start', 'run', 'launch', 'main']):
                groups["launcher"].append(f)
                matched = True
            elif any(word in name_lower for word in ['monitor', 'health', 'status']):
                groups["health_monitor"].append(f)
                matched = True
            elif any(word in name_lower for word in ['web', 'dashboard', 'ui']):
                groups["dashboard"].append(f)
                matched = True
        
        if not matched:
            groups["misc"].append(f)
    
    print(f"📊 Grouped into {len(groups)} feature categories")
    return groups

def git_latest_commit_date(file_path):
    """Git-based canonical file selection using commit history"""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", file_path],
            capture_output=True, text=True, check=True, cwd=BASE_DIR)
        
        if result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return timestamp
        else:
            # File not in Git, use modification time
            return int(os.path.getmtime(file_path))
    except Exception:
        # Fallback to file modification time
        return int(os.path.getmtime(file_path))

def get_file_complexity_score(file_path):
    """Calculate complexity score for canonical selection"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = len(content.split('\n'))
        
        # Count functions and classes
        try:
            tree = ast.parse(content)
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        except:
            functions = classes = 0
        
        # Complexity score: lines + functions*5 + classes*10
        score = lines + functions * 5 + classes * 10
        return score
    except Exception:
        return 0

def choose_canonical(files):
    """Choose canonical file based on Git history, complexity, and naming"""
    if len(files) == 1:
        return files[0], []
    
    print(f"🔍 Git-based canonical file selection for {len(files)} files...")
    
    # Score each file
    file_scores = []
    
    for f in files:
        score = 0
        
        # Git recency (most important factor)
        git_date = git_latest_commit_date(f)
        score += git_date / 1000  # Normalize timestamp
        
        # Complexity bonus
        complexity = get_file_complexity_score(f)
        score += complexity
        
        # Naming bonus (prefer non-test, non-diagnostic files for main functionality)
        name = os.path.basename(f).lower()
        if not any(word in name for word in ['test', 'diagnostic', 'debug', 'temp']):
            score += 1000
        
        # Prefer files without version numbers or dates
        if not re.search(r'_v?\d+|_\d{4}\d{2}\d{2}', name):
            score += 500
        
        file_scores.append((f, score))
    
    # Return file with highest score as canonical, rest as duplicates
    file_scores.sort(key=lambda x: x[1], reverse=True)
    canonical = file_scores[0][0]
    duplicates = [f[0] for f in file_scores[1:]]
    
    return canonical, duplicates

def extract_functions_and_classes(file_path):
    """Extract function and class definitions from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        return functions, classes, content
    except Exception as e:
        print(f"⚠️ Error parsing {file_path}: {e}")
        return [], [], ""

def merge_missing_code(canonical, old_file):
    """Auto-merge missing code from older/duplicate files into canonicals"""
    print(f"🔄 Auto-merging missing code from {os.path.basename(old_file)} into {os.path.basename(canonical)}")
    
    try:
        # Get function and class info from both files
        canon_funcs, canon_classes, canonical_content = extract_functions_and_classes(canonical)
        other_funcs, other_classes, other_content = extract_functions_and_classes(old_file)
        
        # Find unique functions and classes
        unique_funcs = set(other_funcs) - set(canon_funcs)
        unique_classes = set(other_classes) - set(canon_classes)
        
        if not unique_funcs and not unique_classes:
            return False  # Nothing to merge
        
        # Parse the old file to extract unique function/class code
        other_tree = ast.parse(other_content)
        lines = other_content.split('\n')
        
        additions = []
        additions.append(f"\n# --- Merged from {os.path.basename(old_file)} ---")
        
        for node in ast.walk(other_tree):
            if isinstance(node, ast.FunctionDef) and node.name in unique_funcs:
                # Extract function code
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
                func_code = '\n'.join(lines[start_line:end_line])
                additions.append(f"\n{func_code}")
            
            elif isinstance(node, ast.ClassDef) and node.name in unique_classes:
                # Extract class code
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
                class_code = '\n'.join(lines[start_line:end_line])
                additions.append(f"\n{class_code}")
        
        if len(additions) > 1:  # More than just the header comment
            with open(canonical, 'a', encoding='utf-8') as f:
                f.write('\n'.join(additions))
            print(f"✅ Merged {len(unique_funcs)} functions and {len(unique_classes)} classes")
            return True
    
    except Exception as e:
        print(f"⚠️ Error merging code from {old_file}: {e}")
    
    return False

def archive_file(file_path):
    """Archive old duplicate files"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # Preserve directory structure in archive
    rel_path = os.path.relpath(file_path, BASE_DIR)
    archive_path = os.path.join(ARCHIVE_DIR, rel_path)
    
    # Create subdirectories if needed
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    
    # Handle naming conflicts
    counter = 1
    base_archive_path = archive_path
    while os.path.exists(archive_path):
        name, ext = os.path.splitext(base_archive_path)
        archive_path = f"{name}_{counter}{ext}"
        counter += 1
    
    shutil.move(file_path, archive_path)
    return archive_path

def refactor_imports(canonical_map):
    """Automatically refactor import paths project-wide to point to canonicals"""
    print("🔄 Automatically refactoring import paths project-wide...")
    
    files_updated = 0
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip archive directory
        if ARCHIVE_DIR in dirs:
            dirs.remove(ARCHIVE_DIR)
        
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    original_content = content
                    
                    for old_file, canonical_file in canonical_map.items():
                        old_module = os.path.splitext(os.path.basename(old_file))[0]
                        canonical_module = os.path.splitext(os.path.basename(canonical_file))[0]
                        
                        if old_module == canonical_module:
                            continue  # Same module name, no change needed
                        
                        # Replace import statements
                        patterns = [
                            (rf'\bfrom\s+{re.escape(old_module)}\b', f'from {canonical_module}'),
                            (rf'\bimport\s+{re.escape(old_module)}\b', f'import {canonical_module}'),
                            (rf'{re.escape(old_module)}\.', f'{canonical_module}.'),
                        ]
                        
                        for pattern, replacement in patterns:
                            content = re.sub(pattern, replacement, content)
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(content)
                        files_updated += 1
                
                except Exception as e:
                    print(f"⚠️ Error refactoring imports in {file_path}: {e}")
    
    print(f"✅ Updated imports in {files_updated} files")

def static_syntax_check(files):
    """Static syntax checks and error collection"""
    print("🔍 Static syntax checks and error collection...")
    
    syntax_errors = []
    for file_path in files:
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                first_line = error_msg.split('\n')[0] if error_msg else "Unknown syntax error"
                syntax_errors.append(f"{file_path}: {first_line}")
        except Exception as e:
            syntax_errors.append(f"{file_path}: Error during syntax check - {e}")
    
    return syntax_errors

def find_import_errors(archived_files):
    """Find imports referencing archived files"""
    import_errors = []
    archived_mods = {os.path.splitext(os.path.basename(f))[0] for f in archived_files}
    
    for root, dirs, files in os.walk(BASE_DIR):
        if ARCHIVE_DIR in dirs:
            dirs.remove(ARCHIVE_DIR)
        
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    for mod in archived_mods:
                        import_pattern = re.compile(rf'\b(import|from)\s+{re.escape(mod)}\b')
                        if import_pattern.search(content):
                            import_errors.append(f"{file_path}: import of archived module '{mod}' detected")
                except Exception:
                    continue
    
    return import_errors

def run_basic_tests():
    """Run basic tests if available"""
    test_errors = []
    
    # Check if main files can be imported
    critical_files = ['main.py', 'web_dashboard.py', 'aave_integration.py']
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                module_name = os.path.splitext(file_path)[0]
                result = subprocess.run(
                    ["python", "-c", f"import {module_name}; print('Import OK: {module_name}')"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    test_errors.append(f"Import test failed for {file_path}: {result.stderr.strip()}")
            except Exception as e:
                test_errors.append(f"Import test error for {file_path}: {e}")
    
    return test_errors

def generate_comprehensive_report(groups, canonical_map, merge_results, syntax_errors, import_errors, test_errors):
    """Generate comprehensive report listing features, files, and all blocking errors"""
    report_lines = [
        "COMPREHENSIVE SYSTEM AUDIT REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total duplicates processed: {len(canonical_map)}",
        ""
    ]
    
    # Feature breakdown
    report_lines.append("FEATURE BREAKDOWN:")
    report_lines.append("-" * 30)
    
    for feature, files in groups.items():
        report_lines.append(f"\nFeature: {feature.upper()}")
        
        if len(files) == 1:
            report_lines.append(f"  Single file: {files[0]}")
        else:
            # Find canonical for this feature
            canonical_files = set()
            archived_files = []
            
            for f in files:
                is_canonical = True
                for old_file, canonical_file in canonical_map.items():
                    if f == old_file:
                        is_canonical = False
                        archived_files.append(f)
                        break
                    elif f == canonical_file:
                        canonical_files.add(f)
                
                if is_canonical and f not in canonical_files:
                    canonical_files.add(f)
            
            for canonical in canonical_files:
                report_lines.append(f"  Canonical: {canonical}")
            
            for archived in archived_files:
                merge_status = "✅ Merged" if merge_results.get(archived, False) else "📋 No unique content"
                report_lines.append(f"  Archived: {archived} - {merge_status}")
    
    # Error summary
    report_lines.extend([
        "\nERROR SUMMARY:",
        "=" * 30,
        f"Syntax errors: {len(syntax_errors)}",
        f"Import errors: {len(import_errors)}",
        f"Test errors: {len(test_errors)}",
        ""
    ])
    
    # Detailed errors
    if syntax_errors:
        report_lines.append("SYNTAX ERRORS:")
        report_lines.append("-" * 20)
        for error in syntax_errors:
            report_lines.append(f"  {error}")
        report_lines.append("")
    
    if import_errors:
        report_lines.append("IMPORT ERRORS:")
        report_lines.append("-" * 20)
        for error in import_errors:
            report_lines.append(f"  {error}")
        report_lines.append("")
    
    if test_errors:
        report_lines.append("TEST ERRORS:")
        report_lines.append("-" * 20)
        for error in test_errors:
            report_lines.append(f"  {error}")
        report_lines.append("")
    
    # Final status
    total_errors = len(syntax_errors) + len(import_errors) + len(test_errors)
    if total_errors == 0:
        report_lines.append("🎉 AUDIT STATUS: ALL CHECKS PASSED")
    else:
        report_lines.append(f"❌ AUDIT STATUS: {total_errors} BLOCKING ERRORS FOUND")
    
    return "\n".join(report_lines)

def main():
    """Main comprehensive audit process"""
    print("🚀 Starting comprehensive system audit...")
    print("=" * 50)
    
    # Step 1: Scan and group files
    files = scan_files()
    groups = group_by_keyword(files)
    
    canonical_map = {}  # old_file -> canonical_file
    merge_results = {}  # old_file -> bool (whether merge was successful)
    all_canonicals = []
    archived_files = []
    
    # Step 2-4: Process each group for deduplication
    print("\n🔍 Processing feature groups for deduplication...")
    
    for feature, group_files in groups.items():
        if len(group_files) < 2:
            all_canonicals.extend(group_files)
            continue  # No duplicates to process
        
        print(f"\n📁 Processing {feature} group ({len(group_files)} files)")
        
        canonical, duplicates = choose_canonical(group_files)
        all_canonicals.append(canonical)
        print(f"📌 Canonical: {os.path.basename(canonical)}")
        
        for old_file in duplicates:
            # Auto-merge missing code
            merge_success = merge_missing_code(canonical, old_file)
            merge_results[old_file] = merge_success
            
            # Archive the old file
            archive_path = archive_file(old_file)
            archived_files.append(old_file)
            canonical_map[old_file] = canonical
            
            status = "✅ Merged" if merge_success else "📋 Archived"
            print(f"  {status}: {os.path.basename(old_file)}")
    
    # Step 5: Refactor imports
    if canonical_map:
        print(f"\n🔄 Archiving old duplicate files...")
        print(f"📁 Archived {len(archived_files)} duplicate files")
        refactor_imports(canonical_map)
    
    # Step 6: Static syntax checks
    syntax_errors = static_syntax_check(all_canonicals)
    
    # Step 7: Check for broken imports
    import_errors = find_import_errors(archived_files)
    
    # Step 8: Basic functionality tests
    test_errors = run_basic_tests()
    
    # Step 9: Generate comprehensive report
    report_content = generate_comprehensive_report(
        groups, canonical_map, merge_results, 
        syntax_errors, import_errors, test_errors
    )
    
    # Save and display report
    with open(REPORT_FILE, "w", encoding="utf-8") as rf:
        rf.write(report_content)
    
    print(f"\n📄 Outputs a report listing features, files, and all blocking errors:")
    print("=" * 70)
    print(report_content)
    
    print(f"\n✅ Comprehensive audit complete!")
    print(f"📄 Full report saved: {REPORT_FILE}")
    print(f"📁 Archived files location: {ARCHIVE_DIR}/")
    
    # Summary of completed tasks
    print(f"\n🎯 COMPLETED TASKS:")
    print(f"✅ Scanning and grouping files by feature keyword")
    print(f"✅ Git-based canonical file selection")
    print(f"✅ Auto-merging missing code from older/duplicate files into canonicals")
    print(f"✅ Archiving old duplicate files")
    print(f"✅ Automatically refactoring import paths project-wide to point to canonicals")
    print(f"✅ Static syntax checks and error collection")
    print(f"✅ Outputs a report listing features, files, and all blocking errors")

if __name__ == "__main__":
    main()
