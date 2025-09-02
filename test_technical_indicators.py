
#!/usr/bin/env python3
"""
Test Technical Indicators Readiness
Verifies that technical indicators can be calculated with sufficient data
"""

import time
from datetime import datetime

def test_technical_indicators():
    """Test if technical indicators are ready and working"""
    print("🔍 TESTING TECHNICAL INDICATORS READINESS")
    print("=" * 50)
    
    try:
        # Test 1: Check if market signal strategy can be imported
        print("\n1️⃣ Testing Market Signal Strategy Import...")
        from market_signal_strategy import MarketSignalStrategy
        print("   ✅ Market signal strategy imported successfully")
        
        # Test 2: Initialize strategy with mock agent
        print("\n2️⃣ Testing Strategy Initialization...")
        class MockAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        
        agent = MockAgent()
        strategy = MarketSignalStrategy(agent)
        
        if strategy.initialization_successful:
            print("   ✅ Strategy initialized successfully")
        else:
            print("   ❌ Strategy initialization failed")
            return False
        
        # Test 3: Force data collection for technical indicators
        print("\n3️⃣ Testing Data Collection for Technical Indicators...")
        
        # Get initial status
        status = strategy.get_strategy_status()
        initial_points = status.get('price_history_points', 0)
        print(f"   Initial price history points: {initial_points}")
        
        # Force multiple data collections to build history
        print("   🔄 Collecting market data to build price history...")
        for i in range(10):
            try:
                analysis = strategy.get_market_analysis()
                if analysis and not analysis.get('error'):
                    print(f"   📊 Data point {i+1}/10 collected")
                else:
                    print(f"   ⚠️ Data point {i+1}/10 failed")
                time.sleep(0.5)  # Small delay between collections
            except Exception as e:
                print(f"   ❌ Error collecting data point {i+1}: {e}")
        
        # Test 4: Check technical indicators readiness
        print("\n4️⃣ Testing Technical Indicators Readiness...")
        final_status = strategy.get_strategy_status()
        
        price_points = final_status.get('price_history_points', 0)
        tech_indicators_ready = final_status.get('technical_indicators_ready', False)
        data_source = final_status.get('data_source', 'Unknown')
        
        print(f"   Price History Points: {price_points}")
        print(f"   Technical Indicators Ready: {'✅' if tech_indicators_ready else '❌'}")
        print(f"   Data Source: {data_source}")
        
        # Test 5: Try to generate market signals
        print("\n5️⃣ Testing Market Signal Generation...")
        try:
            signals = strategy.analyze_market_signals()
            if signals and signals.get('status') == 'success':
                print("   ✅ Market signals generated successfully")
                print(f"   Signal: {signals.get('recommendation', 'UNKNOWN')}")
                print(f"   Action: {signals.get('action', 'unknown')}")
                print(f"   Confidence: {signals.get('confidence_level', 0):.2f}")
            else:
                print(f"   ⚠️ Signal generation status: {signals.get('status', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Signal generation failed: {e}")
        
        # Test 6: Check enhanced analyzer status
        print("\n6️⃣ Testing Enhanced Analyzer Status...")
        if hasattr(strategy, 'enhanced_analyzer') and strategy.enhanced_analyzer:
            analyzer = strategy.enhanced_analyzer
            if hasattr(analyzer, 'price_history'):
                arb_history = analyzer.price_history.get('ARB', [])
                btc_history = analyzer.price_history.get('BTC', [])
                print(f"   ARB price history: {len(arb_history)} points")
                print(f"   BTC price history: {len(btc_history)} points")
                
                if len(arb_history) >= 5:
                    print("   ✅ Sufficient data for basic technical analysis")
                    return True
                else:
                    print("   ⚠️ Insufficient data for technical analysis")
            else:
                print("   ❌ Enhanced analyzer has no price history")
        else:
            print("   ❌ Enhanced analyzer not available")
        
        return tech_indicators_ready
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_technical_indicators()
    if success:
        print(f"\n🎉 Technical indicators are ready and working!")
        print(f"💡 System can now perform enhanced market analysis")
    else:
        print(f"\n⚠️ Technical indicators need more data points")
        print(f"💡 Run the system for a few minutes to collect sufficient data")
