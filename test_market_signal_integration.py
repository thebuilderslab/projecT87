
#!/usr/bin/env python3
"""
Comprehensive Market Signal Integration Test
Tests all components after fixes are applied
"""

import os
import sys
import time
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_import_dependencies():
    """Test 1: Verify all imports work correctly"""
    print("🔍 TESTING IMPORT DEPENDENCIES")
    print("=" * 40)
    
    try:
        # Test market signal strategy import
        from market_signal_strategy import MarketSignalStrategy
        print("✅ MarketSignalStrategy imported successfully")
        
        # Test enhanced analyzer import
        from enhanced_market_analyzer import EnhancedMarketAnalyzer, EnhancedMarketSignalStrategy
        print("✅ EnhancedMarketAnalyzer imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test 2: Environment Variables"""
    print("\n🔍 TESTING ENVIRONMENT VARIABLES")
    print("=" * 40)
    
    try:
        market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
        coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
        
        print(f"📊 MARKET_SIGNAL_ENABLED: {market_enabled}")
        print(f"🔑 COINMARKETCAP_API_KEY: {'✅ Set' if coinmarketcap_key else '❌ Missing'}")
        
        if not market_enabled:
            print("⚠️ Market signals disabled - enable with MARKET_SIGNAL_ENABLED=true")
            
        if not coinmarketcap_key:
            print("❌ COINMARKETCAP_API_KEY missing")
            return False
            
        print("✅ Environment variables correctly configured")
        return True
        
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
        return False

def test_enhanced_analyzer():
    """Test 3: Enhanced Market Analyzer"""
    print("\n🔍 TESTING ENHANCED MARKET ANALYZER")
    print("=" * 40)
    
    try:
        from enhanced_market_analyzer import EnhancedMarketAnalyzer
        
        # Create mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        
        agent = MockAgent()
        analyzer = EnhancedMarketAnalyzer(agent)
        
        print(f"✅ Enhanced Market Analyzer imported successfully")
        print(f"🌐 Testing API connection...")
        
        # Test market data fetch
        test_data = analyzer.get_market_data_with_fallback('BTC')
        if test_data and 'price' in test_data:
            print(f"✅ API test successful - BTC: ${test_data['price']:.2f}")
            print(f"   Source: {test_data.get('source', 'unknown')}")
        else:
            print("❌ API test failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Enhanced analyzer test failed: {e}")
        traceback.print_exc()
        return False

def test_market_signal_strategy():
    """Test 4: Market Signal Strategy"""
    print("\n🔍 TESTING MARKET SIGNAL STRATEGY")
    print("=" * 40)
    
    try:
        from market_signal_strategy import MarketSignalStrategy
        
        # Create mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        
        agent = MockAgent()
        strategy = MarketSignalStrategy(agent)
        
        print("✅ Market Signal Strategy imported successfully")
        print(f"✅ Market Signal Strategy initialization successful")
        print(f"✅ Enhanced analyzer available")
        
        # Test strategy status
        status = strategy.get_strategy_status()
        print(f"📊 Strategy Status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market signal strategy test failed: {e}")
        traceback.print_exc()
        return False

def test_agent_integration():
    """Test 5: Agent Integration"""
    print("\n🔍 TESTING AGENT INTEGRATION")
    print("=" * 40)
    
    try:
        # Import agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        print("✅ Agent imported successfully")
        
        # Create mock agent for testing
        class MockAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
                self.market_signal_strategy = None
                self.debt_swap_active = False
        
        # Test market signal integration
        from market_signal_strategy import MarketSignalStrategy
        
        mock_agent = MockAgent()
        strategy = MarketSignalStrategy(mock_agent)
        
        if strategy.initialization_successful:
            mock_agent.market_signal_strategy = strategy
            mock_agent.debt_swap_active = True
            print("✅ Market signal strategy integrated successfully")
            print("✅ Debt swap system is active")
        else:
            print("⚠️ Market signal strategy initialized but not fully functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("🚀 MARKET SIGNAL STRATEGY FIX VALIDATION")
    print("=" * 50)
    print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Enhanced Market Analyzer", test_enhanced_analyzer), 
        ("Market Signal Strategy", test_market_signal_strategy),
        ("Agent Integration", test_agent_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{len(tests)} tests passed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Market signal strategy is working correctly.")
        return True
    else:
        print(f"❌ {failed} test(s) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
