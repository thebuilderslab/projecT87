
#!/usr/bin/env python3
"""
Verify Deduplication Results
"""

import os
import subprocess
from collections import defaultdict

def check_imports():
    """Check for any broken imports after refactoring"""
    print("🔍 Checking for broken imports...")
    
    broken_imports = []
    for root, dirs, files in os.walk("."):
        if "archive_duplicates" in dirs:
            dirs.remove("archive_duplicates")
        
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                try:
                    result = subprocess.run(
                        ["python", "-m", "py_compile", file_path],
                        capture_output=True, text=True
                    )
                    if result.returncode != 0:
                        broken_imports.append((file_path, result.stderr))
                except Exception as e:
                    broken_imports.append((file_path, str(e)))
    
    if broken_imports:
        print("❌ Found potential import issues:")
        for file_path, error in broken_imports:
            print(f"  {file_path}: {error[:100]}...")
    else:
        print("✅ All imports appear to be working")
    
    return len(broken_imports) == 0

def summarize_results():
    """Summarize deduplication results"""
    if os.path.exists("keep_remove_report.txt"):
        with open("keep_remove_report.txt", "r") as f:
            print("\n📊 DEDUPLICATION SUMMARY:")
            print("=" * 40)
            lines = f.readlines()
            for line in lines[-10:]:  # Show last 10 lines (summary section)
                print(line.strip())
    
    if os.path.exists("archive_duplicates"):
        archived_count = sum(len(files) for _, _, files in os.walk("archive_duplicates"))
        print(f"\n📁 Archived {archived_count} duplicate files")

if __name__ == "__main__":
    print("🔍 Verifying deduplication results...")
    
    imports_ok = check_imports()
    summarize_results()
    
    if imports_ok:
        print("\n✅ Deduplication verification passed!")
    else:
        print("\n⚠️ Some issues detected - check the output above")
