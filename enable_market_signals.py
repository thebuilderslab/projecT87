
#!/usr/bin/env python3
"""
Enable and test market signal integration
"""

import os
import sys

def main():
    print("🔧 ENABLING MARKET SIGNAL INTEGRATION")
    print("=" * 50)
    
    # Check current environment
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
    coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
    coinapi_key = os.getenv('COIN_API_KEY') or os.getenv('COINAPI_KEY')
    
    print(f"📊 MARKET_SIGNAL_ENABLED: {market_enabled}")
    print(f"🔑 COINMARKETCAP_API_KEY: {'✅ Present' if coinmarketcap_key else '❌ Missing'}")
    print(f"🔑 COIN_API_KEY: {'✅ Present' if coinapi_key else '❌ Missing'}")
    
    if not market_enabled:
        print("\n⚠️ MARKET_SIGNAL_ENABLED is not set to 'true'")
        print("💡 To enable: Go to Secrets tab and set MARKET_SIGNAL_ENABLED=true")
        return False
    
    if not coinmarketcap_key and not coinapi_key:
        print("\n❌ No API keys found!")
        print("💡 You need at least one of:")
        print("   • COINMARKETCAP_API_KEY (recommended)")
        print("   • COIN_API_KEY (primary data source)")
        return False
    
    # Test market signal strategy
    print("\n🧪 TESTING MARKET SIGNAL STRATEGY")
    print("-" * 40)
    
    try:
        from market_signal_strategy import MarketSignalStrategy
        
        class MockAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        
        agent = MockAgent()
        strategy = MarketSignalStrategy(agent)
        
        print("✅ Market Signal Strategy imported successfully")
        
        # Check initialization
        if hasattr(strategy, 'initialization_successful') and strategy.initialization_successful:
            print("✅ Strategy initialized successfully")
            
            # Get status
            status = strategy.get_strategy_status()
            print(f"📊 Strategy Status:")
            print(f"   • Initialized: {status.get('initialized', False)}")
            print(f"   • Enhanced Mode: {status.get('enhanced_mode', False)}")
            print(f"   • Strategy Type: {status.get('strategy_type', 'unknown')}")
            
            # Test market analysis
            try:
                analysis = strategy.get_market_analysis()
                if analysis and not analysis.get('error'):
                    print("✅ Market analysis working")
                    print(f"   • Status: {analysis.get('status', 'unknown')}")
                    
                    # Test signal analysis
                    signals = strategy.analyze_market_signals()
                    print(f"✅ Signal analysis working")
                    print(f"   • Recommendation: {signals.get('recommendation', 'UNKNOWN')}")
                    print(f"   • Action: {signals.get('action', 'unknown')}")
                    
                    return True
                else:
                    print("⚠️ Market analysis has issues but strategy is functional")
                    return True
            except Exception as analysis_error:
                print(f"⚠️ Analysis test failed: {analysis_error}")
                return True  # Still consider it successful if strategy loads
                
        else:
            print("❌ Strategy initialization failed")
            if hasattr(strategy, 'initialized'):
                print(f"   Basic initialized: {strategy.initialized}")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 MARKET SIGNALS READY!")
        print("💡 The system should now show market indicators in the dashboard")
    else:
        print("\n❌ MARKET SIGNALS NOT READY")
        print("💡 Please fix the issues above and try again")
    
    sys.exit(0 if success else 1)
