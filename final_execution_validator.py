
#!/usr/bin/env python3
"""
Final Execution Validator - Last check before autonomous deployment
"""

import os
import sys
import subprocess

def run_final_validation():
    """Run final validation sequence"""
    print("🎯 FINAL EXECUTION VALIDATION FOR DEPLOYMENT")
    print("=" * 60)
    
    validation_steps = [
        {
            'name': 'DAI Compliance Enforcement',
            'command': 'python dai_compliance_enforcer.py',
            'critical': True
        },
        {
            'name': 'System Compliance Check',
            'command': 'python system_compliance_checker.py',
            'critical': True
        },
        {
            'name': 'System Integration Validation',
            'command': 'python validate_system_integration.py',
            'critical': True
        },
        {
            'name': 'Comprehensive System Verification',
            'command': 'python comprehensive_system_verifier.py',
            'critical': True
        },
        {
            'name': 'Final DAI Compliance Validation',
            'command': 'python dai_compliance_final_validator.py',
            'critical': True
        }
    ]
    
    results = {}
    
    for step in validation_steps:
        print(f"\n🔍 Running: {step['name']}")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                step['command'].split(),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"✅ {step['name']}: PASSED")
                results[step['name']] = 'PASSED'
            else:
                print(f"❌ {step['name']}: FAILED")
                print(f"Error output: {result.stderr}")
                results[step['name']] = 'FAILED'
                
                if step['critical']:
                    print(f"🚨 Critical validation failed: {step['name']}")
                    return False
                    
        except subprocess.TimeoutExpired:
            print(f"⏰ {step['name']}: TIMEOUT")
            results[step['name']] = 'TIMEOUT'
            
            if step['critical']:
                print(f"🚨 Critical validation timed out: {step['name']}")
                return False
                
        except Exception as e:
            print(f"❌ {step['name']}: ERROR - {e}")
            results[step['name']] = 'ERROR'
            
            if step['critical']:
                print(f"🚨 Critical validation error: {step['name']}")
                return False
    
    # Generate final report
    print("\n" + "=" * 60)
    print("📊 FINAL VALIDATION REPORT")
    print("=" * 60)
    
    passed_count = len([r for r in results.values() if r == 'PASSED'])
    total_count = len(results)
    
    print(f"✅ Passed validations: {passed_count}/{total_count}")
    
    for name, result in results.items():
        status = "✅" if result == "PASSED" else "❌"
        print(f"   {status} {name}: {result}")
    
    if passed_count == total_count:
        print(f"\n🎉 ALL VALIDATIONS PASSED")
        print(f"🚀 SYSTEM READY FOR AUTONOMOUS DEPLOYMENT")
        print(f"💡 Execute: python main.py")
        return True
    else:
        print(f"\n❌ VALIDATION FAILURES DETECTED")
        print(f"🔧 Resolve failures before deployment")
        return False

def main():
    """Main execution"""
    success = run_final_validation()
    
    if not success:
        sys.exit(1)
    
    return True

if __name__ == "__main__":
    main()
