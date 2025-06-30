
#!/usr/bin/env python3
"""
Check Zapper API Integration Status
"""

import os
from third_party_data_integration import ThirdPartyDataProvider

def check_zapper_status():
    """Check if Zapper API is properly configured"""
    print("🔍 ZAPPER API INTEGRATION CHECK")
    print("=" * 50)
    
    # Check API key
    zapper_key = os.getenv('ZAPPER_API_KEY')
    if not zapper_key:
        print("❌ ZAPPER_API_KEY not found in environment")
        print("💡 Add ZAPPER_API_KEY to your Replit Secrets")
        return False
    
    print(f"✅ ZAPPER_API_KEY found (length: {len(zapper_key)})")
    
    # Test with your wallet
    wallet_address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    provider = ThirdPartyDataProvider()
    
    print(f"\n🔄 Testing Zapper API with wallet: {wallet_address}")
    zapper_data = provider.get_zapper_portfolio(wallet_address)
    
    if zapper_data:
        print("✅ Zapper API call successful!")
        print(f"📊 Health Factor: {zapper_data.get('health_factor', 'N/A')}")
        print(f"📊 Collateral: ${zapper_data.get('total_collateral_usd', 0):,.2f}")
        print(f"📊 Debt: ${zapper_data.get('total_debt_usd', 0):,.2f}")
        print(f"📊 Source: {zapper_data.get('source', 'unknown')}")
        return True
    else:
        print("❌ Zapper API call failed")
        print("💡 This could be due to:")
        print("   - Invalid API key")
        print("   - Rate limiting")
        print("   - No Aave positions found")
        return False

if __name__ == "__main__":
    success = check_zapper_status()
    if not success:
        print("\n💡 To enable Zapper API:")
        print("1. Get API key from https://zapper.fi/")
        print("2. Add ZAPPER_API_KEY to Replit Secrets")
        print("3. Restart dashboard")
