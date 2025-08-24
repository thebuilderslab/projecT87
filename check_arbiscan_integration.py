
#!/usr/bin/env python3
"""
Check Arbiscan API Integration Status
"""

import os
import requests
from third_party_data_integration import ThirdPartyDataProvider

def check_arbiscan_status():
    """Check if Arbiscan API is properly configured"""
    print("🔍 ARBISCAN API INTEGRATION CHECK")
    print("=" * 50)
    
    # Check API key
    arbiscan_key = os.getenv('ARBISCAN_API_KEY')
    if not arbiscan_key:
        print("❌ ARBISCAN_API_KEY not found in environment")
        print("💡 Add ARBISCAN_API_KEY to your Replit Secrets")
        return False
    
    print(f"✅ ARBISCAN_API_KEY found (length: {len(arbiscan_key)})")
    
    # Test with your wallet
    wallet_address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    provider = ThirdPartyDataProvider()
    
    print(f"\n🔄 Testing Arbiscan API with wallet: {wallet_address}")
    
    # Test USDC balance
    usdc_address = "0xaf88D065eEc38FAD0aEfF3e253e648a15cEE23DC"
    usdc_balance = provider.get_arbiscan_token_balance(wallet_address, usdc_address)
    
    if usdc_balance is not None:
        print(f"✅ USDC Balance: {usdc_balance:.6f} USDC")
    else:
        print("❌ Failed to get USDC balance")
    
    # Test Aave data
    aave_data = provider.get_arbiscan_aave_data(wallet_address)
    
    if aave_data:
        print("✅ Arbiscan Aave data retrieved successfully!")
        print(f"📊 Total Collateral: ${aave_data['total_collateral_usd']:,.2f}")
        print(f"📊 Token Balances:")
        for token, balance in aave_data['token_balances'].items():
            print(f"   {token}: {balance:.6f}")
        print(f"📊 Source: {aave_data['source']}")
        return True
    else:
        print("❌ Arbiscan Aave data retrieval failed")
        return False

def test_direct_arbiscan_api():
    """Test direct Arbiscan API call"""
    print("\n🔄 DIRECT ARBISCAN API TEST")
    print("=" * 30)
    
    api_key = os.getenv('ARBISCAN_API_KEY')
    wallet_address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    usdc_address = "0xaf88D065eEc38FAD0aEfF3e253e648a15cEE23DC"
    
    url = "https://api.arbiscan.io/api"
    params = {
        'module': 'account',
        'action': 'tokenbalance',
        'contractaddress': usdc_address,
        'address': wallet_address,
        'tag': 'latest',
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response: {data}")
            
            if data.get('status') == '1':
                balance_wei = int(data.get('result', '0'))
                balance_usdc = balance_wei / 1000000  # USDC has 6 decimals
                print(f"✅ Raw USDC Balance: {balance_wei} wei")
                print(f"✅ Formatted USDC Balance: {balance_usdc:.6f} USDC")
                return True
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return False

if __name__ == "__main__":
    success1 = check_arbiscan_status()
    success2 = test_direct_arbiscan_api()
    
    if success1 or success2:
        print("\n🎉 Arbiscan API is working!")
        print("💡 Your dashboard will now use more accurate on-chain data")
    else:
        print("\n💡 To enable Arbiscan API:")
        print("1. Get API key from https://arbiscan.io/apis")
        print("2. Add ARBISCAN_API_KEY to Replit Secrets")
        print("3. Restart dashboard")
