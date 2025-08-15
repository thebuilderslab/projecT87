
#!/usr/bin/env python3
"""
Test Zapper API Integration - Force Call
"""

import os
from third_party_data_integration import ThirdPartyDataProvider

def test_zapper_forced():
    """Force test Zapper API integration"""
    print("🧪 FORCING ZAPPER API TEST")
    print("=" * 50)
    
    # Check environment
    zapper_key = os.getenv('ZAPPER_API_KEY')
    if zapper_key:
        print(f"✅ ZAPPER_API_KEY found (length: {len(zapper_key)})")
        print(f"🔑 Key starts with: {zapper_key[:8]}...")
    else:
        print("❌ ZAPPER_API_KEY not found in environment")
        return False
    
    # Test wallet
    wallet_address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    print(f"🔍 Testing with wallet: {wallet_address}")
    
    # Initialize provider
    provider = ThirdPartyDataProvider()
    
    # Force test
    print("\n🔄 FORCING Zapper portfolio fetch...")
    zapper_data = provider.get_zapper_portfolio(wallet_address)
    
    if zapper_data:
        print("✅ ZAPPER API FORCED SUCCESS!")
        print(f"📊 Data received:")
        for key, value in zapper_data.items():
            print(f"   {key}: {value}")
        return True
    else:
        print("❌ ZAPPER API FORCED CALL FAILED")
        return False

if __name__ == "__main__":
    test_zapper_forced()
