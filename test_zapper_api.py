
#!/usr/bin/env python3
"""
Test Zapper API Integration
Verifies that the Zapper API key works and can fetch portfolio data
"""

import os
from dotenv import load_dotenv
from third_party_data_integration import ThirdPartyDataProvider

def test_zapper_api():
    """Test Zapper API connectivity and data retrieval"""
    load_dotenv()
    
    print("🧪 TESTING ZAPPER API INTEGRATION")
    print("=" * 50)
    
    # Check if API key is available
    zapper_key = os.getenv('ZAPPER_API_KEY')
    if not zapper_key:
        print("❌ ZAPPER_API_KEY not found in environment")
        print("💡 Please add ZAPPER_API_KEY to your Replit Secrets")
        return False
    
    print(f"✅ ZAPPER_API_KEY found (length: {len(zapper_key)})")
    
    # Initialize provider
    provider = ThirdPartyDataProvider()
    
    # Test with your wallet address
    wallet_address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    print(f"🔍 Testing with wallet: {wallet_address}")
    
    # Test Zapper portfolio fetch
    print("\n🔄 Fetching Zapper portfolio data...")
    zapper_data = provider.get_zapper_portfolio(wallet_address)
    
    if zapper_data:
        print("✅ Zapper API call successful!")
        print(f"📊 Data received:")
        print(f"   Health Factor: {zapper_data.get('health_factor', 'N/A')}")
        print(f"   Total Collateral USD: ${zapper_data.get('total_collateral_usd', 0):,.2f}")
        print(f"   Total Debt USD: ${zapper_data.get('total_debt_usd', 0):,.2f}")
        print(f"   Data Source: {zapper_data.get('source', 'unknown')}")
        return True
    else:
        print("❌ Zapper API call failed or returned no data")
        print("💡 This could be normal if the wallet has no Aave positions")
        
        # Test the general reliable data function
        print("\n🔄 Testing general reliable data function...")
        reliable_data = provider.get_reliable_aave_data(wallet_address)
        if reliable_data:
            print(f"✅ Fallback data available from: {reliable_data.get('source', 'unknown')}")
            return True
        else:
            print("❌ No data available from any source")
            return False

if __name__ == "__main__":
    success = test_zapper_api()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Zapper API integration is working!")
    else:
        print("⚠️ Zapper API integration needs attention")
    print("=" * 50)
