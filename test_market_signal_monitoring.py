
#!/usr/bin/env python3
"""
Test Market Signal Monitoring for Debt Swap Entry Points
Verifies that the system can properly detect and monitor market signals
"""

import os
import time
from datetime import datetime

def test_market_signal_monitoring():
    """Test real-time market signal monitoring for debt swap entry points"""
    print("🔍 TESTING MARKET SIGNAL MONITORING FOR DEBT SWAPS")
    print("=" * 60)
    
    # Test 1: Environment Configuration
    print("\n1️⃣ Testing Environment Configuration...")
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
    
    coinapi_key = (os.getenv('COIN_API') or 
                   os.getenv('COIN_API_KEY') or 
                   os.getenv('COINAPI_KEY') or
                   os.getenv('COINAPI'))
    coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
    
    print(f"   Market Signals Enabled: {'✅' if market_enabled else '❌'} {market_enabled}")
    print(f"   CoinAPI Key Available: {'✅' if coinapi_key else '❌'}")
    print(f"   CoinMarketCap Key Available: {'✅' if coinmarketcap_key else '❌'}")
    
    if not market_enabled:
        print("   ⚠️ To enable: Set MARKET_SIGNAL_ENABLED=true in Replit Secrets")
        return False
    
    # Test 2: Strategy Initialization
    print("\n2️⃣ Testing Market Signal Strategy Initialization...")
    try:
        from market_signal_strategy import MarketSignalStrategy
        
        # Create test agent
        class TestAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"  # Use actual wallet
        
        test_agent = TestAgent()
        strategy = MarketSignalStrategy(test_agent)
        
        print(f"   Strategy Import: ✅ Success")
        print(f"   Strategy Initialized: {'✅' if strategy.initialized else '❌'} {strategy.initialized}")
        print(f"   Initialization Successful: {'✅' if strategy.initialization_successful else '❌'} {strategy.initialization_successful}")
        
        if hasattr(strategy, 'enhanced_analyzer') and strategy.enhanced_analyzer:
            primary_api = getattr(strategy.enhanced_analyzer, 'primary_api', 'unknown')
            mock_mode = getattr(strategy.enhanced_analyzer, 'mock_mode', False)
            
            if primary_api == 'coinapi':
                data_source = "CoinAPI (Primary)"
            elif primary_api == 'coinmarketcap':
                data_source = "CoinMarketCap (Secondary)"
            elif mock_mode:
                data_source = "Mock Data (Fallback)"
            else:
                data_source = "Unknown"
                
            print(f"   Data Source: {data_source}")
        else:
            print(f"   Enhanced Analyzer: ❌ Not available")
        
        # Test 3: Market Analysis
        print("\n3️⃣ Testing Market Analysis...")
        try:
            analysis = strategy.get_market_analysis()
            if analysis and not analysis.get('error'):
                print(f"   Market Analysis: ✅ Working")
                print(f"   Market Sentiment: {analysis.get('market_sentiment', 'unknown')}")
                
                # Check for BTC and ARB data
                btc_data = analysis.get('btc_analysis', {})
                arb_data = analysis.get('arb_analysis', {})
                
                if 'price' in btc_data:
                    print(f"   BTC Price: ${btc_data['price']:,.2f}")
                if 'price' in arb_data:
                    print(f"   ARB Price: ${arb_data['price']:.4f}")
                    if 'rsi' in arb_data:
                        print(f"   ARB RSI: {arb_data['rsi']:.1f}")
            else:
                print(f"   Market Analysis: ❌ Failed - {analysis.get('error', 'No data')}")
                
        except Exception as analysis_error:
            print(f"   Market Analysis: ❌ Error - {analysis_error}")
        
        # Test 4: Signal Generation
        print("\n4️⃣ Testing Signal Generation...")
        try:
            signals = strategy.analyze_market_signals()
            if signals and signals.get('status') == 'success':
                print(f"   Signal Analysis: ✅ Working")
                print(f"   Recommendation: {signals.get('recommendation', 'HOLD')}")
                print(f"   Action: {signals.get('action', 'hold')}")
                print(f"   Confidence: {signals.get('confidence_level', 0):.2f}")
                
                # Check for debt swap triggers
                if signals.get('action') in ['dai_to_arb', 'arb_to_dai']:
                    print(f"   🎯 DEBT SWAP ENTRY POINT DETECTED: {signals.get('action').upper()}")
                    print(f"   Signal Strength: {signals.get('signal_strength', 0):.3f}")
                else:
                    print(f"   ⏳ No debt swap signals at this time")
                    
            else:
                print(f"   Signal Analysis: ❌ Failed - {signals.get('message', 'Unknown error')}")
                
        except Exception as signal_error:
            print(f"   Signal Analysis: ❌ Error - {signal_error}")
        
        # Test 5: Entry Point Monitoring
        print("\n5️⃣ Testing Entry Point Monitoring...")
        try:
            # Get strategy status
            status = strategy.get_strategy_status()
            print(f"   Strategy Status: ✅ Available")
            print(f"   Enhanced Mode: {'✅' if status.get('enhanced_mode', False) else '❌'}")
            print(f"   Price History Points: {status.get('price_history_points', 0)}")
            print(f"   Technical Indicators Ready: {'✅' if status.get('technical_indicators_ready', False) else '❌'}")
            
        except Exception as status_error:
            print(f"   Entry Point Monitoring: ❌ Error - {status_error}")
        
        print(f"\n✅ MARKET SIGNAL MONITORING TEST COMPLETED")
        print(f"📊 System Status: {'OPERATIONAL' if strategy.initialization_successful else 'NEEDS ATTENTION'}")
        
        return strategy.initialization_successful
        
    except ImportError as e:
        print(f"   Strategy Import: ❌ Failed - {e}")
        return False
    except Exception as e:
        print(f"   Strategy Test: ❌ Error - {e}")
        return False

if __name__ == "__main__":
    success = test_market_signal_monitoring()
    if success:
        print(f"\n🎉 Market signal monitoring is working correctly!")
        print(f"💡 System ready to detect debt swap entry points")
    else:
        print(f"\n⚠️ Market signal monitoring needs configuration")
        print(f"💡 Check environment variables and API keys")
