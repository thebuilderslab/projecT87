
#!/usr/bin/env python3
"""
COMPREHENSIVE SECRET LINKAGE VERIFICATION
Verifies all required secrets are properly linked to the app
"""

import os
import sys
from dotenv import load_dotenv

def verify_secret_linkage():
    """Verify all critical secrets are properly linked"""
    print("🔐 COMPREHENSIVE SECRET LINKAGE VERIFICATION")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # All secrets that should be linked to this app
    required_secrets = {
        'ZAPPER_API_KEY': 'Third-party portfolio data integration',
        'ARBITRUM_RPC_URL': 'Direct blockchain RPC access', 
        'PRIVATE_KEY': 'Wallet operations (primary)',
        'PROMPT_KEY': 'AI-driven features and automation',
        'OPTIMIZER_API_KEY': 'Gas optimization and yield strategies',
        'ARBISCAN_API_KEY': 'Arbitrum blockchain explorer data',
        'NETWORK_MODE': 'Network configuration (mainnet/testnet)',
        'COINMARKETCAP_API_KEY': 'Real-time price data',
        'PRIVATE_KEY2': 'Wallet operations (backup)'
    }
    
    linked_secrets = {}
    missing_secrets = []
    
    print("🔍 CHECKING SECRET LINKAGE STATUS:")
    print("-" * 60)
    
    for secret_name, description in required_secrets.items():
        value = os.getenv(secret_name)
        
        if value and len(value.strip()) > 0:
            # Don't print actual secret values for security
            if 'KEY' in secret_name and secret_name != 'NETWORK_MODE':
                display_value = f"{'*' * 8}...{value[-4:] if len(value) > 8 else '****'}"
            else:
                display_value = value if len(value) < 20 else f"{value[:10]}...{value[-4:]}"
            
            print(f"✅ {secret_name}: LINKED")
            print(f"   📝 {description}")
            print(f"   🔹 Value: {display_value}")
            linked_secrets[secret_name] = True
        else:
            print(f"❌ {secret_name}: NOT LINKED")
            print(f"   📝 {description}")
            print(f"   ⚠️  Impact: Feature may be disabled or use fallback")
            missing_secrets.append(secret_name)
        print()
    
    print("=" * 60)
    print("📊 LINKAGE SUMMARY:")
    print(f"✅ Linked secrets: {len(linked_secrets)}/{len(required_secrets)}")
    print(f"❌ Missing secrets: {len(missing_secrets)}")
    
    if missing_secrets:
        print(f"\n🔧 MISSING SECRETS TO LINK:")
        for secret in missing_secrets:
            print(f"   • {secret}: {required_secrets[secret]}")
        
        print(f"\n💡 TO FIX MISSING SECRETS:")
        print(f"1. Go to Replit Secrets (🔐 icon in sidebar)")
        print(f"2. Click '+ New Secret' for each missing secret")
        print(f"3. Add the secret name and value")
        print(f"4. Restart your application")
    
    # Test critical functionality with current secrets
    print(f"\n🧪 TESTING FUNCTIONALITY WITH LINKED SECRETS:")
    print("-" * 60)
    
    # Test network access
    if os.getenv('ARBITRUM_RPC_URL'):
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(os.getenv('ARBITRUM_RPC_URL')))
            if w3.is_connected():
                print(f"✅ Arbitrum RPC: Connected (Chain ID: {w3.eth.chain_id})")
            else:
                print(f"❌ Arbitrum RPC: Connection failed")
        except Exception as e:
            print(f"❌ Arbitrum RPC: Error - {e}")
    
    # Test CoinMarketCap API
    if os.getenv('COINMARKETCAP_API_KEY'):
        try:
            import requests
            headers = {'X-CMC_PRO_API_KEY': os.getenv('COINMARKETCAP_API_KEY')}
            response = requests.get(
                'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                headers=headers,
                params={'symbol': 'ETH'},
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ CoinMarketCap API: Working")
            else:
                print(f"❌ CoinMarketCap API: Failed ({response.status_code})")
        except Exception as e:
            print(f"❌ CoinMarketCap API: Error - {e}")
    
    # Test wallet access
    if os.getenv('PRIVATE_KEY') or os.getenv('PRIVATE_KEY2'):
        try:
            from eth_account import Account
            private_key = os.getenv('PRIVATE_KEY2') or os.getenv('PRIVATE_KEY')
            if private_key and len(private_key.strip()) >= 64:
                account = Account.from_key(private_key)
                print(f"✅ Wallet Access: Valid (Address: {account.address[:10]}...)")
            else:
                print(f"❌ Wallet Access: Invalid private key format")
        except Exception as e:
            print(f"❌ Wallet Access: Error - {e}")
    
    print("=" * 60)
    
    if len(missing_secrets) == 0:
        print("🎉 ALL SECRETS SUCCESSFULLY LINKED!")
        print("✅ Your app has access to all required secrets")
        print("🚀 Ready for full functionality")
        return True
    else:
        print("⚠️  SOME SECRETS NEED TO BE LINKED")
        print("💡 Link the missing secrets in Replit Secrets to enable full functionality")
        return False

if __name__ == "__main__":
    success = verify_secret_linkage()
    sys.exit(0 if success else 1)
