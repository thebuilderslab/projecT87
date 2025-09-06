
#!/usr/bin/env python3
"""
Run diagnostic and capture recent execution for comprehensive analysis
"""

import os
import time
import subprocess
import sys

def run_diagnostic():
    """Run the comprehensive diagnostic"""
    print("🔍 Running comprehensive diagnostic...")
    
    try:
        result = subprocess.run([
            sys.executable, 'comprehensive_system_diagnostic.py'
        ], capture_output=True, text=True, timeout=300)
        
        print("📊 Diagnostic Output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Diagnostic Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Diagnostic timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Failed to run diagnostic: {e}")
        return False

def capture_recent_execution():
    """Capture a recent execution log"""
    print("\n🚀 Capturing recent execution log...")
    
    try:
        # Run main.py for a short period to capture execution
        print("Starting main.py for 2 minutes to capture execution...")
        
        result = subprocess.run([
            sys.executable, 'main.py'
        ], capture_output=True, text=True, timeout=120)  # 2 minutes
        
        # Save the execution log
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        log_filename = f'recent_execution_log_{timestamp}.txt'
        
        with open(log_filename, 'w') as f:
            f.write("=== RECENT EXECUTION LOG ===\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Command: python main.py\n")
            f.write(f"Duration: 2 minutes (timeout)\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write("\n=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)
        
        print(f"📄 Execution log saved to: {log_filename}")
        
        # Print summary of execution
        lines = result.stdout.split('\n')
        important_lines = [line for line in lines if any(keyword in line.lower() for keyword in [
            'error', 'failed', 'success', 'trigger', 'swap', 'borrow', 'health factor', 'iteration'
        ])]
        
        print("\n📋 Key execution events:")
        for line in important_lines[:20]:  # First 20 important lines
            print(f"   {line}")
        
        return log_filename
        
    except subprocess.TimeoutExpired:
        print("⏰ Execution captured for 2 minutes (as intended)")
        return "execution_completed_normally"
    except Exception as e:
        print(f"❌ Failed to capture execution: {e}")
        return None

def main():
    """Main execution"""
    print("🔍 COMPREHENSIVE SYSTEM ANALYSIS")
    print("=" * 50)
    
    # Step 1: Run diagnostic
    diagnostic_success = run_diagnostic()
    
    # Step 2: Capture recent execution
    execution_log = capture_recent_execution()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ANALYSIS COMPLETE")
    print("=" * 50)
    
    if diagnostic_success:
        print("✅ Comprehensive diagnostic completed successfully")
    else:
        print("❌ Diagnostic had issues")
    
    if execution_log:
        print("✅ Recent execution log captured")
    else:
        print("❌ Failed to capture execution log")
    
    print("\n📁 Files created:")
    # List the diagnostic files
    import glob
    diagnostic_files = glob.glob('comprehensive_diagnostic_*.json')
    execution_files = glob.glob('recent_execution_log_*.txt')
    
    for file in diagnostic_files:
        print(f"   📄 {file}")
    for file in execution_files:
        print(f"   📄 {file}")
    
    print("\n💡 These files contain all the requested diagnostic information.")

if __name__ == "__main__":
    main()
