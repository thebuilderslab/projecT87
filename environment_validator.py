
#!/usr/bin/env python3
"""
Environment Variable Validator for Market Signal Strategy
Ensures all required environment variables are properly set
"""

import os

def validate_market_signal_environment():
    """Validate all required environment variables for market signal strategy"""
    print("🔍 VALIDATING MARKET SIGNAL ENVIRONMENT VARIABLES")
    print("=" * 55)
    
    required_vars = {
        'MARKET_SIGNAL_ENABLED': 'true',
        'BTC_DROP_THRESHOLD': '0.003',  # 0.3% drop threshold
        'DAI_TO_ARB_THRESHOLD': '0.90',  # 90% confidence threshold
        'ARB_RSI_OVERSOLD': '25',
        'SIGNAL_COOLDOWN': '300',  # 5 minutes
        'BTC_1H_DROP_THRESHOLD': '0.002',  # 0.2% in 1 hour
        'ARB_1H_MOMENTUM_THRESHOLD': '0.003'
    }
    
    missing_vars = []
    incorrect_vars = []
    
    for var, recommended_value in required_vars.items():
        current_value = os.getenv(var)
        
        if current_value is None:
            missing_vars.append((var, recommended_value))
            print(f"❌ {var}: NOT SET (recommended: {recommended_value})")
        else:
            print(f"✅ {var}: {current_value}")
            
            # Validate specific values
            if var == 'MARKET_SIGNAL_ENABLED' and current_value.lower() != 'true':
                incorrect_vars.append((var, current_value, 'true'))
    
    print("\n" + "=" * 55)
    
    if missing_vars or incorrect_vars:
        print("⚠️  ENVIRONMENT ISSUES DETECTED:")
        
        if missing_vars:
            print("\n🔧 ADD THESE TO REPLIT SECRETS:")
            for var, value in missing_vars:
                print(f"   {var} = {value}")
        
        if incorrect_vars:
            print("\n🔧 UPDATE THESE IN REPLIT SECRETS:")
            for var, current, recommended in incorrect_vars:
                print(f"   {var}: '{current}' → '{recommended}'")
                
        print("\n💡 Go to Replit Secrets tab and add/update these variables")
        return False
    else:
        print("✅ ALL ENVIRONMENT VARIABLES PROPERLY CONFIGURED")
        return True

if __name__ == "__main__":
    validate_market_signal_environment()
import os

def validate_environment_variables():
    """Validate all required environment variables"""
    print("🔍 VALIDATING MARKET SIGNAL ENVIRONMENT VARIABLES")
    print("=" * 55)
    
    required_vars = {
        'MARKET_SIGNAL_ENABLED': 'true',
        'BTC_DROP_THRESHOLD': '0.003',
        'DAI_TO_ARB_THRESHOLD': '0.90',
        'ARB_RSI_OVERSOLD': '25',
        'SIGNAL_COOLDOWN': '300',
        'BTC_1H_DROP_THRESHOLD': '0.002',
        'ARB_1H_MOMENTUM_THRESHOLD': '0.003'
    }
    
    missing_vars = []
    
    for var, recommended in required_vars.items():
        value = os.getenv(var)
        if value is None:
            print(f"❌ {var}: NOT SET (recommended: {recommended})")
            missing_vars.append((var, recommended))
        else:
            print(f"✅ {var}: {value}")
    
    if missing_vars:
        print("\n" + "=" * 55)
        print("⚠️  ENVIRONMENT ISSUES DETECTED:")
        print("\n🔧 ADD THESE TO REPLIT SECRETS:")
        for var, recommended in missing_vars:
            print(f"   {var} = {recommended}")
        print("\n💡 Go to Replit Secrets tab and add/update these variables")
        return False
    else:
        print("\n✅ All environment variables properly configured")
        return True

if __name__ == "__main__":
    validate_environment_variables()
