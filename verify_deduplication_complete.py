
import os
import re
import subprocess

ARCHIVE_DIR = "archive_duplicates"
REPORT_FILE = "keep_remove_report.txt"
VER_REPORT = "verification_report.txt"

def main():
    results = []

    # 1. Check archive exists
    if os.path.isdir(ARCHIVE_DIR):
        archived_files = os.listdir(ARCHIVE_DIR)
        results.append(f"✅ Archive dir exists: {len(archived_files)} files archived")
    else:
        results.append("❌ Archive dir not found")
        archived_files = []

    # 2. Verify canonical merge markers
    canonical_files_checked = 0
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE) as f:
            report = f.read().splitlines()
        for line in report:
            if "Canonical:" in line:
                canonical_path = line.split("Canonical:")[-1].strip()
                if os.path.exists(canonical_path):
                    canonical_files_checked += 1
                    with open(canonical_path) as cf:
                        content = cf.read()
                    if "# --- Merged from older version" in content:
                        results.append(f"✅ Merged content found in {canonical_path}")
                    else:
                        results.append(f"⚠️ No merge marker in {canonical_path} (may not need merge)")
                else:
                    results.append(f"❌ Canonical file missing: {canonical_path}")
    else:
        results.append("❌ keep_remove_report.txt missing")

    # 3. Check imports referencing archived files
    bad_imports = []
    if archived_files:
        for root, _, files in os.walk("."):
            if "archive_duplicates" in root:
                continue
            for filename in files:
                if filename.endswith(".py"):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        for archived_file in archived_files:
                            mod_name = os.path.splitext(archived_file)[0]
                            if re.search(rf"\b(import|from)\s+{re.escape(mod_name)}\b", content):
                                bad_imports.append(f"{filename} -> {mod_name}")
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

    # 4. Run syntax check on main files
    syntax_errors = []
    main_files = ["main.py", "web_dashboard.py", "aave_integration.py"]
    
    for filename in main_files:
        if os.path.exists(filename):
            try:
                subprocess.check_call(
                    ["python", "-m", "py_compile", filename],
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                results.append(f"✅ Syntax OK: {filename}")
            except subprocess.CalledProcessError:
                syntax_errors.append(filename)
                results.append(f"❌ Syntax error: {filename}")
        else:
            results.append(f"⚠️ File not found: {filename}")

    # 5. Summary
    results.append("\n📊 VERIFICATION SUMMARY:")
    results.append(f"   Archived files: {len(archived_files)}")
    results.append(f"   Canonical files checked: {canonical_files_checked}")
    results.append(f"   Bad imports found: {len(bad_imports)}")
    results.append(f"   Syntax errors: {len(syntax_errors)}")
    
    overall_success = (
        len(archived_files) > 0 and 
        len(bad_imports) == 0 and 
        len(syntax_errors) == 0
    )
    
    if overall_success:
        results.append("🎉 DEDUPLICATION VERIFICATION: SUCCESS")
    else:
        results.append("❌ DEDUPLICATION VERIFICATION: ISSUES FOUND")

    # Write report
    with open(VER_REPORT, "w") as f:
        f.write("\n".join(results))
    
    # Print results
    for result in results:
        print(result)
    
    return overall_success

if __name__ == "__main__":
    success = main()
    print(f"\n📄 Report saved: {VER_REPORT}")
    exit(0 if success else 1)
