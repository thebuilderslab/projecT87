
#!/usr/bin/env python3
"""
Verified System Launcher - Runs diagnostic first, then launches if system is ready
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def run_diagnostic():
    """Run comprehensive system diagnostic"""
    print("🔍 RUNNING SYSTEM DIAGNOSTIC FIRST...")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, 'system_comprehensive_diagnostic.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("Diagnostic errors:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Diagnostic timed out")
        return False
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False

def launch_autonomous_system():
    """Launch the complete autonomous system"""
    print("\n🚀 LAUNCHING VERIFIED AUTONOMOUS SYSTEM...")
    print("=" * 60)
    
    # Force mainnet mode
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    try:
        # Launch the complete autonomous system
        subprocess.run([sys.executable, 'complete_autonomous_launcher.py'])
        
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
    except Exception as e:
        print(f"❌ Launch failed: {e}")

def main():
    """Main launcher with diagnostic verification"""
    print("🎯 VERIFIED AUTONOMOUS SYSTEM LAUNCHER")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("🔍 Step 1: System Diagnostic")
    print("🚀 Step 2: Autonomous Launch (if diagnostic passes)")
    print("=" * 60)
    
    # Step 1: Run diagnostic
    diagnostic_passed = run_diagnostic()
    
    if diagnostic_passed:
        print("\n✅ DIAGNOSTIC PASSED - SYSTEM READY FOR LAUNCH!")
        print("🎉 All critical components verified")
        
        # Wait a moment for user to see results
        time.sleep(3)
        
        # Step 2: Launch system
        launch_autonomous_system()
        
    else:
        print("\n❌ DIAGNOSTIC FAILED - SYSTEM NOT READY")
        print("🔧 Please fix the issues identified above before launching")
        print("💡 Review the diagnostic report and fix critical issues")
        print("\n📋 Common fixes:")
        print("   • Add PRIVATE_KEY to Replit Secrets")
        print("   • Add COINMARKETCAP_API_KEY to Replit Secrets") 
        print("   • Fix any syntax errors in code files")
        print("   • Ensure NETWORK_MODE is set to 'mainnet'")
        
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
