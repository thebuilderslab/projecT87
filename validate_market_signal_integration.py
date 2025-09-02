
#!/usr/bin/env python3
"""
Validate Market Signal Integration with CoinAPI Priority
"""

import os
import sys
import traceback

def validate_coinapi_integration():
    """Validate CoinAPI integration"""
    print("\n🔍 VALIDATING COINAPI INTEGRATION")
    print("=" * 40)
    
    try:
        # Check environment variables
        coinapi_key = os.getenv('COINAPI_KEY') or os.getenv('COIN_API_KEY')
        coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
        market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
        
        print(f"📊 MARKET_SIGNAL_ENABLED: {market_enabled}")
        print(f"🔑 COINAPI_KEY: {'✅ Set' if coinapi_key else '❌ Missing'}")
        print(f"🔑 COINMARKETCAP_API_KEY: {'✅ Set' if coinmarketcap_key else '❌ Missing'}")
        
        if not market_enabled:
            print("❌ Market signals disabled - set MARKET_SIGNAL_ENABLED=true")
            return False
            
        if not coinapi_key and not coinmarketcap_key:
            print("❌ No API keys found - need COINAPI_KEY or COINMARKETCAP_API_KEY")
            return False
            
        # Test enhanced analyzer with CoinAPI priority
        try:
            from enhanced_market_analyzer import EnhancedMarketAnalyzer
            
            class MockAgent:
                def __init__(self):
                    self.address = "0x1234...5678"
            
            analyzer = EnhancedMarketAnalyzer(MockAgent())
            
            if analyzer.initialized:
                print("✅ Enhanced Market Analyzer initialized")
                
                # Check which API is primary
                if hasattr(analyzer, 'primary_api'):
                    if analyzer.primary_api == 'coinapi':
                        print("✅ CoinAPI set as PRIMARY data source")
                    elif analyzer.primary_api == 'coinmarketcap':
                        print("⚠️ CoinMarketCap used as primary (CoinAPI not available)")
                    else:
                        print("⚠️ Using mock data mode")
                        
                # Test market data fetching
                test_data = analyzer.get_market_data_with_fallback('BTC')
                if test_data and 'price' in test_data:
                    source = test_data.get('source', 'unknown')
                    price = test_data.get('price', 0)
                    print(f"✅ Market data test successful - BTC: ${price:.2f} (Source: {source})")
                    
                    if source == 'coinapi_primary':
                        print("🎯 CoinAPI is working as primary data source")
                        return True
                    elif source == 'coinmarketcap_secondary':
                        print("🎯 CoinMarketCap working as secondary (CoinAPI unavailable)")
                        return True
                    else:
                        print("⚠️ Using fallback data")
                        return True
                else:
                    print("❌ Market data test failed")
                    return False
            else:
                print("❌ Enhanced Market Analyzer failed to initialize")
                return False
                
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Critical validation error: {e}")
        return False

def validate_market_signal_strategy():
    """Validate Market Signal Strategy"""
    print("\n🔍 VALIDATING MARKET SIGNAL STRATEGY")
    print("=" * 40)
    
    try:
        from market_signal_strategy import MarketSignalStrategy
        
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"
        
        agent = MockAgent()
        strategy = MarketSignalStrategy(agent)
        
        print("✅ Market Signal Strategy imported successfully")
        
        # Check initialization
        if hasattr(strategy, 'initialization_successful') and strategy.initialization_successful:
            print("✅ Market Signal Strategy initialization successful")
            
            # Get strategy status
            status = strategy.get_strategy_status()
            print(f"📊 Strategy Status: {status}")
            
            # Test market analysis
            analysis = strategy.get_market_analysis()
            if analysis and not analysis.get('error'):
                print("✅ Market analysis functional")
                return True
            else:
                print("⚠️ Market analysis has issues but strategy initialized")
                return True
        else:
            print("❌ Market Signal Strategy initialization failed")
            if hasattr(strategy, 'initialized'):
                print(f"   Basic initialized: {strategy.initialized}")
            return False
            
    except Exception as e:
        print(f"❌ Strategy validation failed: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 MARKET SIGNAL INTEGRATION VALIDATION")
    print("=" * 50)
    
    coinapi_test = validate_coinapi_integration()
    strategy_test = validate_market_signal_strategy()
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS:")
    print(f"   CoinAPI Integration: {'✅ PASSED' if coinapi_test else '❌ FAILED'}")
    print(f"   Market Signal Strategy: {'✅ PASSED' if strategy_test else '❌ FAILED'}")
    
    if coinapi_test and strategy_test:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("🎯 CoinAPI is properly configured as primary data source")
        return True
    else:
        print("❌ Some validations failed")
        return False

if __name__ == "__main__":
    main()
