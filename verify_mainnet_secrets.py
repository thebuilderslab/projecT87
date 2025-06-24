
#!/usr/bin/env python3
"""
MAINNET SECRETS VERIFICATION
Comprehensive verification of all required secrets for mainnet deployment
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv
import requests
import time

def verify_arbitrum_rpc():
    """Verify ARBITRUM_RPC_URL connectivity and mainnet status"""
    print("🔍 VERIFYING ARBITRUM_RPC_URL...")
    
    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    print(f"RPC URL: {rpc_url}")
    
    if 'sepolia' in rpc_url.lower() or 'testnet' in rpc_url.lower():
        print("❌ ERROR: RPC URL appears to be testnet, not mainnet!")
        return False
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            print("❌ ERROR: Cannot connect to Arbitrum RPC")
            return False
        
        # Verify chain ID is Arbitrum Mainnet (42161)
        chain_id = w3.eth.chain_id
        if chain_id != 42161:
            print(f"❌ ERROR: Wrong network! Expected 42161 (Arbitrum Mainnet), got {chain_id}")
            return False
        
        # Get latest block
        latest_block = w3.eth.get_block('latest')
        block_number = latest_block.number
        
        print(f"✅ Successfully connected to Arbitrum Mainnet")
        print(f"✅ Chain ID: {chain_id} (Arbitrum Mainnet)")
        print(f"✅ Latest block: {block_number}")
        print(f"✅ Web3 provider connected: True")
        
        return True
        
    except Exception as e:
        print(f"❌ RPC connection error: {e}")
        return False

def verify_private_key():
    """Verify PRIVATE_KEY format and mainnet readiness"""
    print("\n🔍 VERIFYING PRIVATE_KEY...")
    
    # Try both PRIVATE_KEY and PRIVATE_KEY2
    private_key = os.getenv('PRIVATE_KEY2') or os.getenv('PRIVATE_KEY')
    
    if not private_key:
        print("❌ ERROR: No PRIVATE_KEY or PRIVATE_KEY2 found in secrets")
        return False
    
    # Validate format - handle both 0x-prefixed and raw hex keys
    if private_key.startswith('0x'):
        hex_part = private_key[2:]
        expected_length = 66
    else:
        hex_part = private_key
        expected_length = 64
    
    if len(private_key) not in [64, 66]:
        print(f"❌ ERROR: Private key should be 64 or 66 characters long, got {len(private_key)}")
        return False
    
    try:
        # Test if it's valid hex
        bytes.fromhex(hex_part)
        print("✅ Private key format is valid (64-character hexadecimal)")
        if private_key.startswith('0x'):
            print("✅ Private key has 0x prefix")
        else:
            print("✅ Private key is raw hex (will be handled correctly)")
        print("✅ Ready for mainnet wallet operations")
        print("⚠️  ENSURE this wallet is funded on Arbitrum Mainnet!")
        
        return True
        
    except ValueError:
        print("❌ ERROR: Private key contains invalid hexadecimal characters")
        return False

def verify_coinmarketcap_api():
    """Verify COINMARKETCAP_API_KEY"""
    print("\n🔍 VERIFYING COINMARKETCAP_API_KEY...")
    
    api_key = os.getenv('COINMARKETCAP_API_KEY')
    
    if not api_key:
        print("❌ ERROR: COINMARKETCAP_API_KEY not found in secrets")
        return False
    
    if len(api_key) < 10:
        print("❌ ERROR: COINMARKETCAP_API_KEY appears too short")
        return False
    
    # Test API connectivity
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }
        params = {'symbol': 'ARB'}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            arb_price = data['data']['ARB']['quote']['USD']['price']
            print(f"✅ CoinMarketCap API key is valid")
            print(f"✅ Successfully fetched ARB price: ${arb_price:.4f}")
            return True
        else:
            print(f"❌ API test failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ CoinMarketCap API test error: {e}")
        return False

def verify_additional_secrets():
    """Verify PROMPT_KEY, MAINET_ACCOUNT_KEY, OPTIMIZER_API_KEY"""
    print("\n🔍 VERIFYING ADDITIONAL SECRETS...")
    
    # PROMPT_KEY is required
    prompt_key = os.getenv('PROMPT_KEY')
    if not prompt_key:
        print("❌ ERROR: PROMPT_KEY not found in secrets")
        print("💡 PROMPT_KEY is required for AI-driven features")
        return False
    else:
        print("✅ PROMPT_KEY: Present and configured")
    
    # Optional secrets with functionality explanations
    optional_secrets = {
        'MAINET_ACCOUNT_KEY': 'Advanced account management features and multi-wallet support',
        'OPTIMIZER_API_KEY': 'Gas optimization and yield strategy enhancements'
    }
    
    for secret_name, functionality in optional_secrets.items():
        value = os.getenv(secret_name)
        
        if not value or len(value.strip()) == 0:
            print(f"⚠️  WARNING: {secret_name} not found or empty")
            print(f"   Impact: {functionality} will use default/fallback behavior")
        else:
            print(f"✅ {secret_name}: Present and configured")
    
    print("\n💡 FUNCTIONALITY IMPACT OF PLACEHOLDER VALUES:")
    print("   • MAINET_ACCOUNT_KEY: If placeholder, multi-wallet features disabled")
    print("   • OPTIMIZER_API_KEY: If placeholder, basic gas estimation used instead of optimization")
    print("   • Core DeFi operations (Aave, Uniswap) will work with placeholder values")
    
    return True

def verify_network_mode():
    """Verify NETWORK_MODE is set to mainnet"""
    print("\n🔍 VERIFYING NETWORK_MODE...")
    
    network_mode = os.getenv('NETWORK_MODE', 'testnet')
    
    if network_mode.lower() != 'mainnet':
        print(f"❌ ERROR: NETWORK_MODE is '{network_mode}' but should be 'mainnet'")
        print("💡 Please set NETWORK_MODE=mainnet in Replit Secrets")
        return False
    
    print(f"✅ NETWORK_MODE: {network_mode}")
    return True

def main():
    """Main verification function"""
    load_dotenv()
    
    print("🚀 MAINNET SECRETS VERIFICATION")
    print("=" * 60)
    print("This script verifies all secrets required for mainnet deployment")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Run all verification checks
    checks = [
        ("Arbitrum RPC URL", verify_arbitrum_rpc),
        ("Private Key", verify_private_key),
        ("CoinMarketCap API", verify_coinmarketcap_api),
        ("Additional Secrets", verify_additional_secrets),
        ("Network Mode", verify_network_mode)
    ]
    
    for check_name, check_function in checks:
        result = check_function()
        if not result:
            all_checks_passed = False
        time.sleep(1)  # Brief pause between checks
    
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("🎉 ALL MAINNET SECRETS VERIFIED SUCCESSFULLY!")
        print("✅ Ready for mainnet deployment")
        print("🚀 Next step: Run the '🚀 MAINNET DEPLOY' workflow")
    else:
        print("❌ SOME SECRETS NEED ATTENTION")
        print("💡 Please fix the issues above in Replit Secrets")
        print("🔄 Then run this script again to verify")
    
    print("=" * 60)
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
