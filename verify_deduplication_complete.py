
#!/usr/bin/env python3
"""
Comprehensive Deduplication Verification Script
Verifies that the deduplication process completed successfully according to instructions
"""

import os
import re
import subprocess
import ast
from collections import defaultdict

ARCHIVE_DIR = "archive_duplicates"
REPORT_FILE = "keep_remove_report.txt"
VER_REPORT = "verification_report.txt"

def check_archive_exists():
    """Check if archive directory exists and contains expected files"""
    results = []
    archived_files = []
    
    if os.path.isdir(ARCHIVE_DIR):
        for root, dirs, files in os.walk(ARCHIVE_DIR):
            for f in files:
                if f.endswith('.py'):
                    archived_files.append(f)
        results.append(f"✅ Archive directory exists with {len(archived_files)} Python files")
    else:
        results.append("❌ Archive directory 'archive_duplicates/' not found")
    
    return results, archived_files

def verify_canonical_files():
    """Verify canonical files exist and contain merged content markers"""
    results = []
    canonical_files = []
    
    if not os.path.exists(REPORT_FILE):
        results.append("❌ keep_remove_report.txt not found")
        return results, canonical_files
    
    with open(REPORT_FILE, 'r') as f:
        report_content = f.read()
    
    # Extract canonical files from report
    canonical_pattern = r'Canonical:\s*(.+)'
    canonical_matches = re.findall(canonical_pattern, report_content)
    
    for canonical_path in canonical_matches:
        canonical_path = canonical_path.strip()
        canonical_files.append(canonical_path)
        
        if os.path.exists(canonical_path):
            try:
                with open(canonical_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for merge markers
                if "# --- Merged from" in content:
                    results.append(f"✅ Canonical file {canonical_path} contains merged content")
                else:
                    results.append(f"⚠️ Canonical file {canonical_path} has no merge markers (may not have needed merging)")
                
                # Syntax check
                try:
                    ast.parse(content)
                    results.append(f"✅ Syntax valid for {canonical_path}")
                except SyntaxError as e:
                    results.append(f"❌ Syntax error in {canonical_path}: {e}")
                    
            except Exception as e:
                results.append(f"❌ Error reading {canonical_path}: {e}")
        else:
            results.append(f"❌ Canonical file not found: {canonical_path}")
    
    return results, canonical_files

def check_import_refactoring(archived_files):
    """Check that imports have been refactored to point to canonical files"""
    results = []
    bad_imports = []
    
    # Get module names from archived files
    archived_modules = [os.path.splitext(f)[0] for f in archived_files]
    
    # Search all Python files for imports to archived modules
    for root, dirs, files in os.walk("."):
        # Skip archive directory
        if ARCHIVE_DIR in dirs:
            dirs.remove(ARCHIVE_DIR)
        
        for filename in files:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for module_name in archived_modules:
                        # Check for various import patterns
                        patterns = [
                            rf'\bfrom\s+{re.escape(module_name)}\s+import\b',
                            rf'\bimport\s+{re.escape(module_name)}\b',
                            rf'{re.escape(module_name)}\.(\w+)',
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, content):
                                bad_imports.append(f"{filepath} imports {module_name}")
                                break
                                
                except Exception as e:
                    results.append(f"⚠️ Error checking imports in {filepath}: {e}")
    
    if bad_imports:
        results.append(f"❌ Found {len(bad_imports)} imports to archived files:")
        for bad_import in bad_imports[:5]:  # Show first 5
            results.append(f"   - {bad_import}")
        if len(bad_imports) > 5:
            results.append(f"   ... and {len(bad_imports) - 5} more")
    else:
        results.append("✅ No imports to archived files found")
    
    return results

def run_syntax_checks():
    """Run syntax checks on all Python files"""
    results = []
    syntax_errors = []
    files_checked = 0
    
    for root, dirs, files in os.walk("."):
        # Skip problematic directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.replit_cache', ARCHIVE_DIR, '.pythonlibs'}]
        
        for filename in files:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                files_checked += 1
                
                try:
                    result = subprocess.run(
                        ['python', '-m', 'py_compile', filepath],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        syntax_errors.append(f"{filepath}: {result.stderr.strip()}")
                        
                except subprocess.TimeoutExpired:
                    syntax_errors.append(f"{filepath}: Compilation timeout")
                except Exception as e:
                    syntax_errors.append(f"{filepath}: {e}")
    
    if syntax_errors:
        results.append(f"❌ Found {len(syntax_errors)} syntax errors:")
        for error in syntax_errors[:3]:  # Show first 3
            results.append(f"   - {error}")
        if len(syntax_errors) > 3:
            results.append(f"   ... and {len(syntax_errors) - 3} more")
    else:
        results.append(f"✅ Syntax check passed for {files_checked} files")
    
    return results

def run_functional_tests():
    """Run available functional tests"""
    results = []
    
    # Try different test runners
    test_commands = [
        (['python', '-m', 'pytest', '-v', '--tb=short'], "pytest"),
        (['python', '-m', 'unittest', 'discover', '-v'], "unittest"),
        (['python', 'test_agent.py'], "test_agent.py"),
        (['python', 'verify_readiness.py'], "verify_readiness.py")
    ]
    
    tests_run = False
    
    for cmd, test_name in test_commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                results.append(f"✅ {test_name} tests passed")
                tests_run = True
            else:
                results.append(f"❌ {test_name} tests failed: {result.stderr[:100]}...")
                tests_run = True
            break
            
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            results.append(f"⚠️ {test_name} tests timed out")
            tests_run = True
            break
        except Exception as e:
            results.append(f"⚠️ Error running {test_name}: {e}")
    
    if not tests_run:
        results.append("⚠️ No test framework found or available")
    
    return results

def generate_verification_report():
    """Generate comprehensive verification report"""
    print("🔍 Starting deduplication verification...")
    
    all_results = []
    
    # 1. Check archive exists
    print("\n📁 Checking archive directory...")
    archive_results, archived_files = check_archive_exists()
    all_results.extend(archive_results)
    
    # 2. Verify canonical files
    print("\n📋 Verifying canonical files...")
    canonical_results, canonical_files = verify_canonical_files()
    all_results.extend(canonical_results)
    
    # 3. Check import refactoring
    print("\n🔄 Checking import refactoring...")
    import_results = check_import_refactoring(archived_files)
    all_results.extend(import_results)
    
    # 4. Run syntax checks
    print("\n🔍 Running syntax checks...")
    syntax_results = run_syntax_checks()
    all_results.extend(syntax_results)
    
    # 5. Run functional tests
    print("\n🧪 Running functional tests...")
    test_results = run_functional_tests()
    all_results.extend(test_results)
    
    # Generate summary
    summary = []
    summary.append("DEDUPLICATION VERIFICATION REPORT")
    summary.append("=" * 50)
    summary.append(f"Verification completed at: {__import__('datetime').datetime.now()}")
    summary.append("")
    summary.append("RESULTS:")
    summary.append("-" * 20)
    
    for result in all_results:
        summary.append(result)
    
    summary.append("")
    summary.append("SUMMARY STATISTICS:")
    summary.append("-" * 20)
    summary.append(f"Files archived: {len(archived_files)}")
    summary.append(f"Canonical files verified: {len(canonical_files)}")
    
    # Count success/failure
    success_count = sum(1 for r in all_results if r.startswith("✅"))
    warning_count = sum(1 for r in all_results if r.startswith("⚠️"))
    error_count = sum(1 for r in all_results if r.startswith("❌"))
    
    summary.append(f"Successful checks: {success_count}")
    summary.append(f"Warnings: {warning_count}")
    summary.append(f"Errors: {error_count}")
    
    if error_count == 0:
        summary.append("")
        summary.append("🎉 DEDUPLICATION VERIFICATION PASSED!")
    else:
        summary.append("")
        summary.append("⚠️ DEDUPLICATION VERIFICATION HAD ISSUES - SEE ABOVE")
    
    # Write report
    report_content = "\n".join(summary)
    with open(VER_REPORT, 'w') as f:
        f.write(report_content)
    
    # Print results
    print("\n" + "=" * 50)
    print(report_content)
    print(f"\n📄 Full verification report saved to {VER_REPORT}")

if __name__ == "__main__":
    generate_verification_report()
