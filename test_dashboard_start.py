
#!/usr/bin/env python3
"""
Test Dashboard Startup
Quick test to verify web dashboard can start correctly
"""

import os
import time
import subprocess
import requests
from dotenv import load_dotenv

def test_dashboard_startup():
    """Test if the dashboard starts correctly"""
    print("🧪 TESTING DASHBOARD STARTUP")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Check environment variables
    print("🔍 Environment Check:")
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    private_key = os.getenv('PRIVATE_KEY')
    cmc_key = os.getenv('COINMARKETCAP_API_KEY')
    
    print(f"   NETWORK_MODE: {network_mode}")
    print(f"   PRIVATE_KEY: {'✅ Set' if private_key else '❌ Missing'}")
    print(f"   COINMARKETCAP_API_KEY: {'✅ Set' if cmc_key else '❌ Missing'}")
    
    if not private_key:
        print("❌ PRIVATE_KEY is required")
        return False
    
    # Test web dashboard import
    try:
        print("\n📱 Testing web dashboard import...")
        import web_dashboard
        print("✅ Web dashboard imported successfully")
    except Exception as e:
        print(f"❌ Web dashboard import failed: {e}")
        return False
    
    # Test agent initialization
    try:
        print("\n🤖 Testing agent initialization...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"   Wallet: {agent.address}")
        print(f"   Network: {agent.w3.eth.chain_id}")
        print(f"   Balance: {agent.get_eth_balance():.6f} ETH")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test enhanced Aave data function
    try:
        print("\n🏦 Testing enhanced Aave data retrieval...")
        from web_dashboard import get_enhanced_aave_data
        aave_data = get_enhanced_aave_data(agent)
        if aave_data:
            print("✅ Enhanced Aave data retrieved successfully")
            print(f"   Health Factor: {aave_data['health_factor']}")
            print(f"   Collateral: ${aave_data['total_collateral_usdc']:,.2f}")
            print(f"   Data Source: {aave_data['data_source']}")
        else:
            print("⚠️ No Aave data retrieved (might be no position)")
    except Exception as e:
        print(f"❌ Enhanced Aave data test failed: {e}")
        return False
    
    print("\n✅ ALL TESTS PASSED!")
    print("🚀 Dashboard should now work correctly")
    print("\n💡 To start the dashboard, run:")
    print("   python web_dashboard.py")
    
    return True

if __name__ == "__main__":
    test_dashboard_startup()
