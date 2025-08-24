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

def test_defi_integrations():
    """Test DeFi integrations specifically"""
    print("\n🔍 TESTING DEFI INTEGRATIONS...")
    print("=" * 60)

    issues = []
    warnings = []

    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()

        # Test DeFi integrations initialization separately
        try:
            success = agent.initialize_integrations()
            if success:
                print("   DeFi integrations: ✅ Success")
            else:
                print("   DeFi integrations: ⚠️ Partial success")
                warnings.append("Some DeFi integrations may have issues")
        except Exception as integration_error:
            print(f"   DeFi integrations: ❌ Failed - {integration_error}")
            issues.append("DeFi integrations failed to initialize")

            # Check if it's the specific enhanced_borrow_manager error
            if "enhanced_borrow_manager.py" in str(integration_error):
                issues.append("Enhanced borrow manager has syntax errors")

        print("   Agent initialization: ✅ Success")

        # Test enhanced borrow manager specifically
        try:
            from enhanced_borrow_manager import EnhancedBorrowManager
            ebm = EnhancedBorrowManager(agent)
            print("   Enhanced Borrow Manager: ✅ Success")
        except Exception as ebm_error:
            print(f"   Enhanced Borrow Manager: ❌ Failed - {ebm_error}")
            issues.append("Enhanced Borrow Manager initialization failed")

        # Test Aave integration
        if hasattr(agent, 'aave') and agent.aave:
            try:
                # Test gas parameter calculation
                gas_params = agent.get_optimized_gas_params('aave_borrow', 'normal')
                print(f"   Gas optimization: ✅ Success - {gas_params}")
            except Exception as gas_error:
                print(f"   Gas optimization: ⚠️ Warning - {gas_error}")
                warnings.append("Gas optimization may have issues")

        diagnostic_passed = len(issues) == 0

    except Exception as e:
        print(f"   Agent initialization: ❌ Failed - {e}")
        issues.append("Agent initialization failed")
        diagnostic_passed = False

    if issues:
        print("\n❌ DIAGNOSTIC ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")

    if warnings:
        print("\n⚠️ DIAGNOSTIC WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")

    return diagnostic_passed

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
    print("🔍 Step 2: DeFi Integration Test")
    print("🚀 Step 3: Autonomous Launch (if tests pass)")
    print("=" * 60)

    # Step 1: Run diagnostic
    diagnostic_passed = run_diagnostic()

    # Step 2: Test DeFi integrations specifically
    defi_passed = test_defi_integrations()

    if diagnostic_passed and defi_passed:
        print("\n✅ ALL DIAGNOSTICS PASSED - SYSTEM READY FOR LAUNCH!")
        print("🎉 All critical components verified")

        # Wait a moment for user to see results
        time.sleep(3)

        # Step 3: Launch system
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
        print("   • Fix enhanced_borrow_manager.py method signatures")

        return False

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)