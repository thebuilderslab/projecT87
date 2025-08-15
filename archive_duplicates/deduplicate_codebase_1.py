
#!/usr/bin/env python3
"""
Comprehensive Codebase Deduplication Script
Uses Git history to identify canonical files, merges missing features, and refactors imports
"""

import os
import difflib
import shutil
import subprocess
from collections import defaultdict
import re
import ast
import json
from datetime import datetime

# Keywords to group files by functionality
KEYWORDS = [
    "diagnostic", "compliance", "launcher", "dashboard", "sync", "test", 
    "emergency", "health_monitor", "fetcher", "validator", "borrow", 
    "aave", "uniswap", "integration", "rpc", "gas", "agent", "autonomous",
    "strategy", "market_signal", "enhanced", "fix", "comprehensive"
]

BASE_DIR = "."
REPORT_FILE = "keep_remove_report.txt"
ARCHIVE_DIR = "archive_duplicates"

def scan_files():
    """Scan for all Python files in the project"""
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
    
    return py_files

def extract_functions_and_classes(file_path):
    """Extract function and class names from a Python file"""
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
        
        return functions, classes
    except Exception as e:
        print(f"⚠️ Error parsing {file_path}: {e}")
        return [], []

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
    
    return groups

def git_latest_commit_date(file_path):
    """Get the latest Git commit timestamp for a file"""
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
    """Calculate a complexity score based on file size and content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = len(content.split('\n'))
        functions, classes = extract_functions_and_classes(file_path)
        
        # Complexity score: lines + functions*5 + classes*10
        score = lines + len(functions) * 5 + len(classes) * 10
        return score
    except Exception:
        return 0

def choose_canonical(files):
    """Choose canonical file based on Git history, complexity, and naming"""
    if len(files) == 1:
        return files[0]
    
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
    
    # Return file with highest score
    file_scores.sort(key=lambda x: x[1], reverse=True)
    return file_scores[0][0]

def compare_file_contents(canonical, other_file):
    """Compare two files and identify unique content in the other file"""
    try:
        with open(canonical, 'r', encoding='utf-8') as f1:
            canonical_content = f1.read()
        
        with open(other_file, 'r', encoding='utf-8') as f2:
            other_content = f2.read()
        
        # Extract functions and classes from both files
        canon_funcs, canon_classes = extract_functions_and_classes(canonical)
        other_funcs, other_classes = extract_functions_and_classes(other_file)
        
        # Find unique functions and classes
        unique_funcs = set(other_funcs) - set(canon_funcs)
        unique_classes = set(other_classes) - set(canon_classes)
        
        return unique_funcs, unique_classes, canonical_content, other_content
    
    except Exception as e:
        print(f"⚠️ Error comparing {canonical} and {other_file}: {e}")
        return set(), set(), "", ""

def merge_missing_code(canonical, old_file):
    """Merge missing functions and classes from old file into canonical"""
    unique_funcs, unique_classes, canonical_content, other_content = compare_file_contents(canonical, old_file)
    
    if not unique_funcs and not unique_classes:
        return False  # Nothing to merge
    
    try:
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
            return True
    
    except Exception as e:
        print(f"⚠️ Error merging code from {old_file}: {e}")
    
    return False

def archive_file(file_path):
    """Move file to archive directory"""
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
    """Refactor import statements throughout the project"""
    print("🔄 Refactoring imports...")
    
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

def generate_report(canonical_map, merge_results):
    """Generate detailed deduplication report"""
    report_lines = [
        "CODEBASE DEDUPLICATION REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total duplicates processed: {len(canonical_map)}",
        ""
    ]
    
    # Group by category for report
    groups = defaultdict(list)
    for old_file, canonical_file in canonical_map.items():
        # Determine category
        name_lower = os.path.basename(old_file).lower()
        category = "misc"
        for kw in KEYWORDS:
            if kw in name_lower:
                category = kw
                break
        groups[category].append((old_file, canonical_file))
    
    for category, files in groups.items():
        report_lines.append(f"\n[{category.upper()}]")
        report_lines.append("-" * 20)
        
        canonical_files = set(canonical for _, canonical in files)
        for canonical in canonical_files:
            report_lines.append(f"Canonical: {canonical}")
            
            # List archived files for this canonical
            archived = [old for old, canon in files if canon == canonical]
            for old_file in archived:
                merge_status = "✅ Merged" if merge_results.get(old_file, False) else "📋 No unique content"
                report_lines.append(f"  Archived: {old_file} - {merge_status}")
    
    # Summary statistics
    report_lines.extend([
        "\nSUMMARY",
        "=" * 20,
        f"Files archived: {len(canonical_map)}",
        f"Files with merged content: {sum(merge_results.values())}",
        f"Canonical files retained: {len(set(canonical_map.values()))}",
        ""
    ])
    
    return "\n".join(report_lines)

def main():
    """Main deduplication process"""
    print("🚀 Starting comprehensive codebase deduplication...")
    
    # Scan and group files
    files = scan_files()
    print(f"📁 Found {len(files)} Python files")
    
    groups = group_by_keyword(files)
    print(f"📊 Grouped into {len(groups)} categories")
    
    canonical_map = {}  # old_file -> canonical_file
    merge_results = {}  # old_file -> bool (whether merge was successful)
    
    # Process each group
    for category, group_files in groups.items():
        if len(group_files) < 2:
            continue  # No duplicates to process
        
        print(f"\n🔍 Processing {category} group ({len(group_files)} files)")
        
        canonical = choose_canonical(group_files)
        print(f"📌 Canonical: {os.path.basename(canonical)}")
        
        for f in group_files:
            if f != canonical:
                # Merge missing code
                merge_success = merge_missing_code(canonical, f)
                merge_results[f] = merge_success
                
                # Archive the old file
                archive_path = archive_file(f)
                canonical_map[f] = canonical
                
                status = "✅ Merged" if merge_success else "📋 Archived"
                print(f"  {status}: {os.path.basename(f)}")
    
    # Refactor imports
    if canonical_map:
        refactor_imports(canonical_map)
    
    # Generate report
    report_content = generate_report(canonical_map, merge_results)
    with open(REPORT_FILE, "w", encoding="utf-8") as rf:
        rf.write(report_content)
    
    print(f"\n✅ Deduplication complete!")
    print(f"📄 Report: {REPORT_FILE}")
    print(f"📁 Archived files: {ARCHIVE_DIR}/")
    print(f"🔄 Files processed: {len(canonical_map)}")

if __name__ == "__main__":
    main()
