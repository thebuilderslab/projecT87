#!/usr/bin/env python3
"""
Test to verify CoinAPI is configured as primary market data source
"""

import os
import sys
import requests # Import requests for API calls

def test_coinapi_secrets():
    """Test if CoinAPI key is in Replit Secrets"""
    print("🔍 TESTING COINAPI IN REPLIT SECRETS")
    print("=" * 40)

    # Use COIN_API as the primary environment variable name
    coinapi_key = os.getenv('COIN_API')
    coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')

    print(f"COIN_API: {'✅ Present' if coinapi_key else '❌ Missing'}")
    print(f"COINMARKETCAP_API_KEY: {'✅ Present' if coinmarketcap_key else '❌ Missing'}")

    if coinapi_key:
        print(f"✅ CoinAPI key found: {coinapi_key[:8]}...")
        print(f"📏 Key length: {len(coinapi_key)} characters")
        return True
    else:
        print("❌ CoinAPI key not found in Replit Secrets")
        print("💡 Add COIN_API to your Replit Secrets")
        return False

def test_enhanced_market_analyzer_priority():
    """Test that enhanced_market_analyzer uses CoinAPI as primary"""
    print("\n🔍 TESTING ENHANCED MARKET ANALYZER COINAPI PRIORITY")
    print("=" * 50)

    try:
        # Assume enhanced_market_analyzer.py exists and has the EnhancedMarketAnalyzer class
        from enhanced_market_analyzer import EnhancedMarketAnalyzer

        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"

        # Initialize EnhancedMarketAnalyzer, assuming it uses COIN_API
        # The actual implementation of EnhancedMarketAnalyzer is not provided,
        # so we're making assumptions based on the context.
        analyzer = EnhancedMarketAnalyzer(MockAgent())

        print(f"✅ Enhanced Market Analyzer imported successfully")
        # These attributes are assumed to be set within EnhancedMarketAnalyzer
        print(f"🎯 Primary API: {getattr(analyzer, 'primary_api', 'Unknown')}")
        print(f"📊 Initialized: {getattr(analyzer, 'initialized', False)}")
        print(f"🔄 Mock mode: {getattr(analyzer, 'mock_mode', 'Unknown')}")

        # Check if the CoinAPI client is initialized within the analyzer
        if hasattr(analyzer, 'coinapi_client') and analyzer.coinapi_client:
            print("✅ CoinAPI client initialized")
        else:
            print("❌ CoinAPI client not initialized")

        # Test data fetching, assuming get_market_data_with_fallback is implemented
        print("\n📊 Testing market data fetching...")
        # This call will depend on the actual implementation of EnhancedMarketAnalyzer
        # and its ability to fetch data using COIN_API.
        btc_data = analyzer.get_market_data_with_fallback('BTC')

        if btc_data:
            source = btc_data.get('source', 'unknown')
            price = btc_data.get('price', 'N/A')
            print(f"✅ BTC Data received: ${price}")
            print(f"🎯 Data source: {source}")

            # Verify that the data source indicates CoinAPI
            if 'coinapi' in source.lower():
                print("🎉 SUCCESS: CoinAPI is being used as primary data source!")
                return True
            else:
                print("⚠️ WARNING: CoinAPI not being used as primary")
                return False
        else:
            print("❌ No data received")
            return False

    except ImportError:
        print("❌ Failed to import EnhancedMarketAnalyzer. Ensure 'enhanced_market_analyzer.py' exists.")
        return False
    except Exception as e:
        print(f"❌ Test failed during EnhancedMarketAnalyzer execution: {e}")
        return False

def test_system_integration():
    """Test CoinAPI integration in the main system"""
    print("\n🔍 TESTING SYSTEM INTEGRATION")
    print("=" * 30)

    try:
        # Assume arbitrum_testnet_agent.py exists and has the ArbitrumTestnetAgent class
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        # Mock the agent creation to test market signal strategy
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"

        mock_agent = MockAgent()

        # Assume market_signal_strategy.py exists and has the MarketSignalStrategy class
        from market_signal_strategy import MarketSignalStrategy

        # Initialize the strategy, assuming it depends on an enhanced_analyzer
        strategy = MarketSignalStrategy(mock_agent)

        # Check if the strategy has an enhanced_analyzer and if its primary_api is 'coinapi'
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

    except ImportError as e:
        print(f"❌ Failed to import necessary modules for system integration test: {e}")
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
        print("1. Ensure COIN_API is added to Replit Secrets")
        print("2. Verify the API key is valid and has sufficient quota")
        print("3. Check that enhanced_market_analyzer.py and market_signal_strategy.py are using the updated code")

if __name__ == "__main__":
    main()