
#!/usr/bin/env python3
"""
Test to verify CoinAPI is configured as primary market data source
"""

import os
import sys

def test_coinapi_secrets():
    """Test if CoinAPI key is in Replit Secrets"""
    print("🔍 TESTING COINAPI IN REPLIT SECRETS")
    print("=" * 40)
    
    coinapi_key = os.getenv('COINAPI_KEY') or os.getenv('COIN_API_KEY')
    coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
    
    print(f"COINAPI_KEY: {'✅ Present' if coinapi_key else '❌ Missing'}")
    print(f"COIN_API_KEY: {'✅ Present' if os.getenv('COIN_API_KEY') else '❌ Missing'}")
    print(f"COINMARKETCAP_API_KEY: {'✅ Present' if coinmarketcap_key else '❌ Missing'}")
    
    if coinapi_key:
        print(f"✅ CoinAPI key found: {coinapi_key[:8]}...")
        print(f"📏 Key length: {len(coinapi_key)} characters")
        return True
    else:
        print("❌ CoinAPI key not found in Replit Secrets")
        print("💡 Add COINAPI_KEY to your Replit Secrets")
        return False

def test_enhanced_market_analyzer_priority():
    """Test that enhanced_market_analyzer uses CoinAPI as primary"""
    print("\n🔍 TESTING ENHANCED MARKET ANALYZER COINAPI PRIORITY")
    print("=" * 50)
    
    try:
        from enhanced_market_analyzer import EnhancedMarketAnalyzer
        
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"
        
        analyzer = EnhancedMarketAnalyzer(MockAgent())
        
        print(f"✅ Enhanced Market Analyzer imported successfully")
        print(f"🎯 Primary API: {getattr(analyzer, 'primary_api', 'Unknown')}")
        print(f"📊 Initialized: {getattr(analyzer, 'initialized', False)}")
        print(f"🔄 Mock mode: {getattr(analyzer, 'mock_mode', 'Unknown')}")
        
        if hasattr(analyzer, 'coinapi_client') and analyzer.coinapi_client:
            print("✅ CoinAPI client initialized")
        else:
            print("❌ CoinAPI client not initialized")
        
        # Test data fetching
        print("\n📊 Testing market data fetching...")
        btc_data = analyzer.get_market_data_with_fallback('BTC')
        
        if btc_data:
            source = btc_data.get('source', 'unknown')
            price = btc_data.get('price', 'N/A')
            print(f"✅ BTC Data received: ${price}")
            print(f"🎯 Data source: {source}")
            
            if 'coinapi' in source.lower():
                print("🎉 SUCCESS: CoinAPI is being used as primary data source!")
                return True
            else:
                print("⚠️ WARNING: CoinAPI not being used as primary")
                return False
        else:
            print("❌ No data received")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_system_integration():
    """Test CoinAPI integration in the main system"""
    print("\n🔍 TESTING SYSTEM INTEGRATION")
    print("=" * 30)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Check if agent initializes with CoinAPI
        print("🤖 Testing agent initialization...")
        
        # Mock the agent creation to test market signal strategy
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"
        
        mock_agent = MockAgent()
        
        # Import market signal strategy
        from market_signal_strategy import MarketSignalStrategy
        
        strategy = MarketSignalStrategy(mock_agent)
        
        if hasattr(strategy, 'enhanced_analyzer') and strategy.enhanced_analyzer:
            primary_api = getattr(strategy.enhanced_analyzer, 'primary_api', 'Unknown')
            print(f"🎯 Market Signal Strategy API: {primary_api}")
            
            if primary_api == 'coinapi':
                print("✅ SUCCESS: CoinAPI is primary in market signal strategy!")
                return True
            else:
                print(f"⚠️ WARNING: Market signal strategy using {primary_api} instead of CoinAPI")
                return False
        else:
            print("❌ Enhanced analyzer not found in market signal strategy")
            return False
            
    except Exception as e:
        print(f"❌ System integration test failed: {e}")
        return False

def main():
    """Run all CoinAPI verification tests"""
    print("🚀 COINAPI PRIMARY DATA SOURCE VERIFICATION")
    print("=" * 60)
    
    tests = [
        ("Replit Secrets", test_coinapi_secrets),
        ("Enhanced Market Analyzer", test_enhanced_market_analyzer_priority),
        ("System Integration", test_system_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COINAPI VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 CoinAPI is properly configured as primary data source!")
    else:
        print("⚠️ CoinAPI configuration needs attention")
        print("\n💡 RECOMMENDATIONS:")
        print("1. Ensure COINAPI_KEY is added to Replit Secrets")
        print("2. Verify the API key is valid and has sufficient quota")
        print("3. Check that enhanced_market_analyzer.py is using the updated code")

if __name__ == "__main__":
    main()
