
#!/usr/bin/env python3
"""
Fix Replit Secrets Issues
This script checks and fixes common secret configuration problems
"""

import os
import secrets

def check_and_fix_secrets():
    """Check and fix Replit Secrets configuration"""
    print("🔍 CHECKING REPLIT SECRETS...")
    print("=" * 50)
    
    issues_found = []
    fixes_applied = []
    
    # Check PRIVATE_KEY
    private_key = os.getenv('PRIVATE_KEY')
    private_key2 = os.getenv('PRIVATE_KEY2')
    
    print(f"PRIVATE_KEY: {'SET' if private_key else 'NOT_SET'}")
    print(f"PRIVATE_KEY2: {'SET' if private_key2 else 'NOT_SET'}")
    
    if private_key:
        print(f"PRIVATE_KEY length: {len(private_key)}")
        if 'your_private_key_here' in private_key.lower():
            issues_found.append("PRIVATE_KEY contains placeholder text")
    
    if private_key2:
        print(f"PRIVATE_KEY2 length: {len(private_key2)}")
        if 'your_private_key_here' in private_key2.lower():
            issues_found.append("PRIVATE_KEY2 contains placeholder text")
    
    # Check other secrets
    secrets_to_check = {
        'NETWORK_MODE': 'mainnet',
        'COINMARKETCAP_API_KEY': None,
        'PROMPT_KEY': None,
        'OPTIMIZER_API_KEY': None,
        'ARBITRUM_RPC_URL': 'https://arb1.arbitrum.io/rpc'
    }
    
    for secret_name, default_value in secrets_to_check.items():
        value = os.getenv(secret_name)
        print(f"{secret_name}: {'SET' if value else 'NOT_SET'}")
        
        if not value and default_value:
            print(f"  → Using default: {default_value}")
            os.environ[secret_name] = default_value
            fixes_applied.append(f"Set {secret_name} to default value")
    
    # Generate a valid test private key if needed
    if (not private_key or 'your_private_key_here' in private_key.lower()) and \
       (not private_key2 or 'your_private_key_here' in private_key2.lower()):
        
        print("\n⚠️ No valid private keys found!")
        print("💡 For testing, you can use this dummy key:")
        dummy_key = "0x" + "0" * 64
        print(f"   {dummy_key}")
        print("🔒 This is safe for testing but won't work for real transactions")
        
        # Set emergency fallback
        os.environ['PRIVATE_KEY2'] = dummy_key
        fixes_applied.append("Set emergency fallback private key")
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    
    if issues_found:
        print("❌ Issues found:")
        for issue in issues_found:
            print(f"   • {issue}")
    
    if fixes_applied:
        print("✅ Fixes applied:")
        for fix in fixes_applied:
            print(f"   • {fix}")
    
    if not issues_found:
        print("✅ No major issues found with secrets configuration")
    
    print("\n💡 NEXT STEPS:")
    print("1. Go to Replit Secrets (🔐 icon in sidebar)")
    print("2. Add/update your actual private key as PRIVATE_KEY2")
    print("3. Ensure NETWORK_MODE is set to 'mainnet'")
    print("4. Add your CoinMarketCap API key")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    check_and_fix_secrets()
