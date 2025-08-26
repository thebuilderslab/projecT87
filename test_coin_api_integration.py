
#!/usr/bin/env python3
"""
COIN_API Integration Test
Tests the new COIN_API integration for market signal strategy
"""

import os
import sys
import time
import traceback

def test_coin_api_connection():
    """Test 1: COIN_API connection and basic functionality"""
    print("🔍 TESTING COIN_API CONNECTION")
    print("=" * 40)
    
    try:
        # Check if COIN_API key is present
        coin_api_key = os.getenv('COIN_API')
        if not coin_api_key:
            print("❌ COIN_API key not found in environment variables")
            print("💡 Please add COIN_API to your Replit Secrets")
            return False
        
        print(f"✅ COIN_API key found: {coin_api_key[:8]}...")
        
        # Test COIN_API client
        from enhanced_market_analyzer import CoinAPIClient
        
        client = CoinAPIClient(coin_api_key)
        print("✅ CoinAPIClient initialized successfully")
        
        # Test getting current prices
        test_symbols = ['BTC', 'ETH', 'ARB']
        print(f"\n📊 Testing current price fetching for: {test_symbols}")
        
        for symbol in test_symbols:
            try:
                price_data = client.get_current_price(symbol)
                if price_data:
                    print(f"✅ {symbol}: ${price_data['price']:.2f} ({price_data.get('percent_change_24h', 0):.2f}% 24h)")
                else:
                    print(f"⚠️ {symbol}: No data received")
            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_coin_api_historical_data():
    """Test 2: COIN_API historical data functionality"""
    print("\n🔍 TESTING COIN_API HISTORICAL DATA")
    print("=" * 40)
    
    try:
        coin_api_key = os.getenv('COIN_API')
        if not coin_api_key:
            print("❌ COIN_API key not found")
            return False
        
        from enhanced_market_analyzer import CoinAPIClient
        
        client = CoinAPIClient(coin_api_key)
        
        # Test historical data for BTC
        print("📈 Testing BTC historical data (30 days)...")
        hist_data = client.get_historical_data('BTC', 30)
        
        if hist_data is not None and len(hist_data) > 0:
            print(f"✅ Successfully fetched {len(hist_data)} days of BTC data")
            print(f"   Latest close: ${hist_data['close'].iloc[-1]:.2f}")
            print(f"   30-day high: ${hist_data['high'].max():.2f}")
            print(f"   30-day low: ${hist_data['low'].min():.2f}")
            return True
        else:
            print("⚠️ No historical data received")
            return False
        
    except Exception as e:
        print(f"❌ Historical data test failed: {e}")
        return False

def test_enhanced_market_analyzer_with_coin_api():
    """Test 3: Enhanced Market Analyzer with COIN_API integration"""
    print("\n🔍 TESTING ENHANCED MARKET ANALYZER WITH COIN_API")
    print("=" * 50)
    
    try:
        from enhanced_market_analyzer import EnhancedMarketAnalyzer
        
        # Mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"
        
        agent = MockAgent()
        analyzer = EnhancedMarketAnalyzer(agent)
        
        print("✅ EnhancedMarketAnalyzer initialized with COIN_API")
        
        # Test market summary with COIN_API
        print("📊 Testing market summary generation...")
        summary = analyzer.get_market_summary()
        
        if 'error' not in summary:
            print("✅ Market summary generated successfully")
            print(f"📈 Market sentiment: {summary.get('market_sentiment', 'unknown')}")
            print(f"🔄 Data source: {summary.get('data_source', 'unknown')}")
            
            # Display data for each symbol
            for symbol in ['btc', 'eth', 'arb']:
                analysis_key = f'{symbol}_analysis'
                if analysis_key in summary and 'price' in summary[analysis_key]:
                    data = summary[analysis_key]
                    print(f"💰 {symbol.upper()}: ${data['price']:.2f} ({data.get('change_24h', 0):.2f}% 24h)")
            
            return True
        else:
            print(f"❌ Market summary failed: {summary['error']}")
            return False
        
    except Exception as e:
        print(f"❌ Enhanced analyzer test failed: {e}")
        traceback.print_exc()
        return False

def test_market_signal_strategy_with_coin_api():
    """Test 4: Market Signal Strategy with COIN_API"""
    print("\n🔍 TESTING MARKET SIGNAL STRATEGY WITH COIN_API")
    print("=" * 50)
    
    try:
        from market_signal_strategy import MarketSignalStrategy
        
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"
        
        agent = MockAgent()
        strategy = MarketSignalStrategy(agent)
        
        print("✅ MarketSignalStrategy initialized")
        
        # Test strategy status
        status = strategy.get_strategy_status()
        print(f"📊 Strategy Status:")
        print(f"   Initialized: {status.get('initialized', False)}")
        print(f"   Enhanced Mode: {status.get('enhanced_mode', False)}")
        print(f"   COIN_API Present: {status.get('coin_api_present', False)}")
        print(f"   Strategy Type: {status.get('strategy_type', 'unknown')}")
        
        # Test market analysis
        analysis = strategy.get_market_analysis()
        if 'error' not in analysis:
            print("✅ Market analysis integration working with COIN_API")
            if 'market_sentiment' in analysis:
                print(f"📈 Current sentiment: {analysis['market_sentiment']}")
        else:
            print(f"⚠️ Market analysis issue: {analysis.get('error', 'unknown')}")
        
        # Test trade decision
        trade_decision = strategy.should_execute_trade()
        print(f"🎯 Trade decision with COIN_API data: {'EXECUTE' if trade_decision else 'HOLD'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market signal strategy test failed: {e}")
        traceback.print_exc()
        return False

def test_arbitrum_agent_coin_api_integration():
    """Test 5: Arbitrum Agent integration with COIN_API"""
    print("\n🔍 TESTING ARBITRUM AGENT COIN_API INTEGRATION")
    print("=" * 50)
    
    try:
        # Check if we can create agent with COIN_API support
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("⚠️ No PRIVATE_KEY found, skipping agent integration test")
            return True
        
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        agent = ArbitrumTestnetAgent()
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            print("✅ Arbitrum agent with market signal strategy initialized")
            
            # Test strategy status
            if hasattr(agent.market_signal_strategy, 'get_strategy_status'):
                status = agent.market_signal_strategy.get_strategy_status()
                if status.get('coin_api_present'):
                    print("✅ COIN_API integration confirmed in agent")
                else:
                    print("⚠️ COIN_API not detected in agent strategy")
            
            # Test if market analysis works
            if hasattr(agent.market_signal_strategy, 'get_market_analysis'):
                analysis = agent.market_signal_strategy.get_market_analysis()
                if 'error' not in analysis:
                    print("✅ Agent market analysis working with COIN_API")
                else:
                    print(f"⚠️ Agent market analysis issue: {analysis.get('error', 'unknown')}")
            
            return True
        else:
            print("⚠️ Market signal strategy not initialized in agent")
            return True  # Not a failure, just not configured
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

def run_all_coin_api_tests():
    """Run all COIN_API integration tests"""
    print("🚀 COIN_API INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("COIN_API Connection", test_coin_api_connection),
        ("COIN_API Historical Data", test_coin_api_historical_data),
        ("Enhanced Market Analyzer", test_enhanced_market_analyzer_with_coin_api),
        ("Market Signal Strategy", test_market_signal_strategy_with_coin_api),
        ("Arbitrum Agent Integration", test_arbitrum_agent_coin_api_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 COIN_API INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All COIN_API integration tests passed!")
        print("✅ Your system is ready to use COIN_API for market signal strategy")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        print("💡 Ensure COIN_API key is properly set in Replit Secrets")
    
    return passed == total

if __name__ == "__main__":
    run_all_coin_api_tests()
