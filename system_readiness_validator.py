
#!/usr/bin/env python3
"""
System Readiness Validator - Comprehensive check for network approval readiness
"""

import os
import time
import logging
from environment_validator import validate_market_signal_environment

def validate_complete_system_readiness():
    """Validate complete system readiness for network execution"""
    print("🔍 COMPREHENSIVE SYSTEM READINESS VALIDATION")
    print("=" * 60)
    
    readiness_score = 0
    max_score = 10
    
    # Check 1: Environment Variables
    print("\n1️⃣ Environment Variables Check:")
    env_valid = validate_market_signal_environment()
    if env_valid:
        readiness_score += 2
        print("✅ Environment variables properly configured")
    else:
        print("❌ Environment variables missing or incorrect")
    
    # Check 2: Critical Files
    print("\n2️⃣ Critical Files Check:")
    critical_files = [
        'arbitrum_testnet_agent.py',
        'market_signal_strategy.py', 
        'market_data_api_fix.py',
        'aave_integration.py',
        'uniswap_integration.py'
    ]
    
    missing_files = []
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if not missing_files:
        readiness_score += 2
        print("✅ All critical files present")
    else:
        print(f"❌ Missing files: {missing_files}")
    
    # Check 3: API Keys
    print("\n3️⃣ API Keys Check:")
    required_keys = ['COINMARKETCAP_API_KEY', 'WALLET_PRIVATE_KEY']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if not missing_keys:
        readiness_score += 2
        print("✅ All required API keys present")
    else:
        print(f"❌ Missing API keys: {missing_keys}")
    
    # Check 4: Network Configuration
    print("\n4️⃣ Network Configuration Check:")
    network_mode = os.getenv('NETWORK_MODE', 'testnet')
    if network_mode == 'mainnet':
        readiness_score += 1
        print("✅ Network mode set to mainnet")
    else:
        print(f"⚠️ Network mode: {network_mode} (should be 'mainnet' for production)")
    
    # Check 5: Market Signal Configuration
    print("\n5️⃣ Market Signal Configuration Check:")
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
    if market_enabled:
        readiness_score += 1
        print("✅ Market signals enabled")
    else:
        print("⚠️ Market signals disabled")
    
    # Check 6: Safety Mechanisms
    print("\n6️⃣ Safety Mechanisms Check:")
    emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
    if not os.path.exists(emergency_file):
        readiness_score += 1
        print("✅ Emergency stop not active")
    else:
        print("⚠️ Emergency stop is active")
    
    # Check 7: Import Tests
    print("\n7️⃣ Import Tests:")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        from market_signal_strategy import MarketSignalStrategy
        from market_data_api_fix import MarketDataAPIFix
        readiness_score += 1
        print("✅ All critical modules can be imported")
    except Exception as e:
        print(f"❌ Import error: {e}")
    
    # Final Assessment
    print(f"\n📊 READINESS ASSESSMENT:")
    print(f"=" * 30)
    print(f"Score: {readiness_score}/{max_score}")
    print(f"Percentage: {(readiness_score/max_score)*100:.1f}%")
    
    if readiness_score >= 8:
        print("🎉 SYSTEM READY FOR NETWORK APPROVAL")
        print("✅ High likelihood of successful execution")
        return True
    elif readiness_score >= 6:
        print("⚠️ SYSTEM PARTIALLY READY")
        print("🔧 Address remaining issues for optimal performance")
        return False
    else:
        print("❌ SYSTEM NOT READY")
        print("🚨 Critical issues must be resolved before deployment")
        return False

if __name__ == "__main__":
    validate_complete_system_readiness()
