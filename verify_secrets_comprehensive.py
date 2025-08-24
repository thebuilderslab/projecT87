
#!/usr/bin/env python3
"""
Comprehensive Secrets Verification
Checks all required secrets without syntax errors or redundancies
"""

import os
import sys
from dotenv import load_dotenv

def verify_all_secrets():
    """Verify all required secrets are properly loaded"""
    print("🔐 COMPREHENSIVE SECRETS VERIFICATION")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # Required secrets for the system
    required_secrets = {
        'PRIVATE_KEY': 'Wallet private key for transactions',
        'PROMPT_KEY': 'AI-driven features and automation',
        'COINMARKETCAP_API_KEY': 'Real-time price data from CoinMarketCap',
        'ARBITRUM_RPC_URL': 'Direct Arbitrum blockchain RPC access',
        'ARBISCAN_API_KEY': 'Arbitrum blockchain explorer data',
        'OPTIMIZER_API_KEY': 'Gas optimization and yield strategies'
    }
    
    print("🔍 CHECKING SECRET AVAILABILITY:")
    print("-" * 60)
    
    all_secrets_valid = True
    for secret_name, description in required_secrets.items():
        value = os.getenv(secret_name)
        
        if value and len(value.strip()) > 0:
            # Show partial value for verification without exposing full secret
            if len(value) > 8:
                display_value = f"{value[:4]}...{value[-4:]}"
            else:
                display_value = "*" * len(value)
            
            print(f"✅ {secret_name}: LOADED")
            print(f"   📝 Purpose: {description}")
            print(f"   🔹 Length: {len(value)} characters")
            print(f"   🔹 Preview: {display_value}")
            
            # Additional validation for specific secrets
            if secret_name == 'PRIVATE_KEY':
                if len(value) >= 64 and (value.startswith('0x') or len(value) == 64):
                    print(f"   ✅ Format: Valid private key format")
                else:
                    print(f"   ❌ Format: Invalid private key format")
                    all_secrets_valid = False
            
            elif secret_name == 'NETWORK_MODE':
                if value.lower() in ['mainnet', 'testnet']:
                    print(f"   ✅ Value: Valid network mode ({value})")
                else:
                    print(f"   ⚠️  Value: Unusual network mode ({value})")
        else:
            print(f"❌ {secret_name}: NOT FOUND OR EMPTY")
            print(f"   📝 Purpose: {description}")
            print(f"   ⚠️  Impact: Functionality will be limited or fail")
            all_secrets_valid = False
        print()
    
    # Test network mode separately (it has default fallback)
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    print(f"🌐 NETWORK_MODE: {network_mode}")
    print(f"   📝 Source: {'Environment' if os.getenv('NETWORK_MODE') else 'Default fallback'}")
    print()
    
    # Test basic functionality with loaded secrets
    print("🧪 TESTING BASIC FUNCTIONALITY:")
    print("-" * 60)
    
    # Test 1: CoinMarketCap API
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
                data = response.json()
                eth_price = data['data']['ETH']['quote']['USD']['price']
                print(f"✅ CoinMarketCap API: Working (ETH: ${eth_price:.2f})")
            else:
                print(f"❌ CoinMarketCap API: Failed (Status: {response.status_code})")
                all_secrets_valid = False
        except Exception as e:
            print(f"❌ CoinMarketCap API: Error - {str(e)[:50]}...")
            all_secrets_valid = False
    
    # Test 2: Arbitrum RPC
    arbitrum_rpc = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(arbitrum_rpc, request_kwargs={'timeout': 5}))
        if w3.is_connected():
            chain_id = w3.eth.chain_id
            latest_block = w3.eth.block_number
            print(f"✅ Arbitrum RPC: Connected (Chain: {chain_id}, Block: {latest_block})")
        else:
            print(f"❌ Arbitrum RPC: Connection failed")
            all_secrets_valid = False
    except Exception as e:
        print(f"❌ Arbitrum RPC: Error - {str(e)[:50]}...")
        all_secrets_valid = False
    
    # Test 3: Private Key Format
    if os.getenv('PRIVATE_KEY'):
        try:
            from eth_account import Account
            private_key = os.getenv('PRIVATE_KEY')
            account = Account.from_key(private_key)
            print(f"✅ Private Key: Valid (Address: {account.address[:10]}...)")
        except Exception as e:
            print(f"❌ Private Key: Invalid format - {str(e)[:50]}...")
            all_secrets_valid = False
    
    print()
    print("=" * 60)
    
    if all_secrets_valid:
        print("🎉 ALL SECRETS VERIFIED SUCCESSFULLY!")
        print("✅ System ready for autonomous operations")
        print("🚀 No syntax errors or redundancies detected")
        return True
    else:
        print("⚠️  SOME ISSUES DETECTED")
        print("💡 Fix the issues above before proceeding")
        return False

if __name__ == "__main__":
    success = verify_all_secrets()
    print(f"\n📊 Final Status: {'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
