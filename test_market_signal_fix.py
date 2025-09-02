
#!/usr/bin/env python3
"""
Test Market Signal Strategy Fixes
Validates that all components are working correctly
"""

import os
import sys
import time
from datetime import datetime

def test_environment_variables():
    """Test that required environment variables are set"""
    print("🔍 TESTING ENVIRONMENT VARIABLES")
    print("=" * 40)
    
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED')
    api_key = os.getenv('COINMARKETCAP_API_KEY')
    
    print(f"📊 MARKET_SIGNAL_ENABLED: {market_enabled}")
    print(f"🔑 COINMARKETCAP_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
    
    if market_enabled != 'true':
        print("❌ MARKET_SIGNAL_ENABLED must be set to 'true'")
        return False
    
    if not api_key or len(api_key) < 10:
        print("❌ COINMARKETCAP_API_KEY is missing or invalid")
        return False
    
    print("✅ Environment variables correctly configured")
    return True

def test_enhanced_market_analyzer():
    """Test the Enhanced Market Analyzer"""
    print("\n🔍 TESTING ENHANCED MARKET ANALYZER")
    print("=" * 40)
    
    try:
        from enhanced_market_analyzer import EnhancedMarketAnalyzer
        
        api_key = os.getenv('COINMARKETCAP_API_KEY')
        analyzer = EnhancedMarketAnalyzer(api_key)
        
        print("✅ Enhanced Market Analyzer imported successfully")
        
        # Test API connection
        print("🌐 Testing API connection...")
        btc_data = analyzer.get_market_data_with_fallback('BTC')
        
        if btc_data and 'price' in btc_data:
            print(f"✅ API test successful - BTC: ${btc_data['price']:.2f}")
            print(f"   Source: {btc_data.get('source', 'unknown')}")
            return True
        else:
            print("❌ API test failed - no valid data returned")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_market_signal_strategy():
    """Test the Market Signal Strategy"""
    print("\n🔍 TESTING MARKET SIGNAL STRATEGY")
    print("=" * 40)
    
    try:
        from market_signal_strategy import MarketSignalStrategy
        
        api_key = os.getenv('COINMARKETCAP_API_KEY')
        strategy = MarketSignalStrategy(api_key)
        
        print("✅ Market Signal Strategy imported successfully")
        
        if strategy.initialization_successful:
            print("✅ Market Signal Strategy initialization successful")
            
            # Test signal generation
            if strategy.enhanced_analyzer:
                print("✅ Enhanced analyzer available")
                return True
            else:
                print("❌ Enhanced analyzer not available")
                return False
        else:
            print("❌ Market Signal Strategy initialization failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_agent_integration():
    """Test the agent integration"""
    print("\n🔍 TESTING AGENT INTEGRATION")
    print("=" * 40)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("✅ Agent imported successfully")
        
        # Create agent instance (this will initialize market signal strategy)
        agent = ArbitrumTestnetAgent()
        
        print("✅ Agent created successfully")
        
        if agent.market_signal_strategy:
            print("✅ Market signal strategy integrated successfully")
            if agent.debt_swap_active:
                print("✅ Debt swap system is active")
            else:
                print("⚠️ Debt swap system is not active")
            return True
        else:
            print("❌ Market signal strategy not integrated")
            return False
            
    except Exception as e:
        print(f"❌ Agent integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 MARKET SIGNAL STRATEGY FIX VALIDATION")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Enhanced Market Analyzer", test_enhanced_market_analyzer),
        ("Market Signal Strategy", test_market_signal_strategy),
        ("Agent Integration", test_agent_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
    
    print(f"\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Market signal strategy is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
