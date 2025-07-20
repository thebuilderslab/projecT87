
#!/usr/bin/env python3
"""
System Readiness Verification
Verify all components are ready for autonomous operation
"""

import os
import sys
import json

def verify_system_readiness():
    """Verify all system components are ready"""
    print("🔍 SYSTEM READINESS VERIFICATION")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Environment Variables
    total_checks += 1
    required_vars = ['WALLET_PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 'NETWORK_MODE']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
    else:
        print("✅ All required environment variables present")
        checks_passed += 1
    
    # Check 2: Critical Files
    total_checks += 1
    critical_files = [
        'arbitrum_testnet_agent.py',
        'aave_integration.py',
        'uniswap_integration.py',
        'aave_health_monitor.py',
        'gas_fee_calculator.py'
    ]
    
    missing_files = []
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing critical files: {missing_files}")
    else:
        print("✅ All critical files present")
        checks_passed += 1
    
    # Check 3: JSON Serialization
    total_checks += 1
    try:
        from fix_json_serialization import safe_json_dump
        test_data = {'test': 123, 'timestamp': 1234567890}
        safe_json_dump(test_data, 'test_serialization.json')
        if os.path.exists('test_serialization.json'):
            os.remove('test_serialization.json')
            print("✅ JSON serialization working")
            checks_passed += 1
        else:
            print("❌ JSON serialization failed")
    except Exception as e:
        print(f"❌ JSON serialization error: {e}")
    
    # Check 4: Contract Validator
    total_checks += 1
    try:
        from contract_validator import ContractValidator
        print("✅ Contract validator module available")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Contract validator import failed: {e}")
    
    # Summary
    print(f"\n📊 READINESS SUMMARY: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✅ System is ready for autonomous operation")
        return True
    else:
        print("❌ System needs fixes before autonomous operation")
        return False

if __name__ == "__main__":
    success = verify_system_readiness()
    sys.exit(0 if success else 1)
