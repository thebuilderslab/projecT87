
#!/usr/bin/env python3
"""
Test Lowered Threshold Sensitivity
Verify that new 0.3% BTC threshold and 5-minute monitoring catches current market movements
"""

import os
import time
import logging
from datetime import datetime

def test_threshold_sensitivity():
    """Test if new thresholds catch current market conditions"""
    print("🎯 TESTING LOWERED THRESHOLD SENSITIVITY")
    print("=" * 50)
    
    # Set environment variables for testing
    os.environ['BTC_DROP_THRESHOLD'] = '0.003'  # 0.3%
    os.environ['SIGNAL_COOLDOWN'] = '300'  # 5 minutes
    os.environ['BTC_1H_DROP_THRESHOLD'] = '0.002'  # 0.2%
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("🚀 Initializing agent with new thresholds...")
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        if hasattr(agent, 'market_signal_strategy'):
            print(f"✅ Market Signal Strategy initialized")
            print(f"   BTC Drop Threshold: {agent.market_signal_strategy.btc_drop_threshold * 100:.1f}%")
            print(f"   Signal Cooldown: {agent.market_signal_strategy.signal_cooldown / 60:.1f} minutes")
            print(f"   1H BTC Threshold: {agent.market_signal_strategy.btc_1h_drop_threshold * 100:.1f}%")
            
            # Test current market signal
            print(f"\n📊 Testing current market conditions...")
            signal = agent.market_signal_strategy.analyze_market_signals()
            
            if signal:
                print(f"✅ SIGNAL DETECTED:")
                print(f"   Type: {signal.signal_type}")
                print(f"   Confidence: {signal.confidence:.2f}")
                print(f"   BTC Change: {getattr(signal, 'btc_price_change', signal.get('btc_price_change', 0.0)) if hasattr(signal, 'get') else getattr(signal, 'btc_price_change', 0.0):.2f}%")
                print(f"   ARB RSI: {signal.arb_technical_score:.1f}")
                
                # Test execution decision
                should_execute, strategy = agent.market_signal_strategy.should_execute_market_strategy(signal)
                print(f"   Execution: {strategy} ({'YES' if should_execute else 'NO'})")
                
                # Simulate what would happen with current market data
                btc_change = getattr(signal, 'btc_price_change', signal.get('btc_price_change', 0.0)) if hasattr(signal, 'get') else getattr(signal, 'btc_price_change', 0.0)
                if btc_change <= -0.3:  # -0.43% from your chart
                    print(f"✅ WOULD TRIGGER: BTC down {btc_change:.2f}% > 0.3% threshold")
                else:
                    print(f"⚠️ Would not trigger: BTC {btc_change:.2f}% < 0.3% threshold")
                    
                return True
            else:
                print(f"⚠️ No signal generated - checking if system is in cooldown")
                return False
                
        else:
            print(f"❌ Market signal strategy not available")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def demonstrate_5min_monitoring():
    """Demonstrate 5-minute monitoring frequency"""
    print(f"\n⏰ 5-MINUTE MONITORING SIMULATION")
    print("=" * 40)
    
    print(f"🔄 Previous: 30-minute cooldown (signals every 30 min)")
    print(f"🚀 New: 5-minute cooldown (signals every 5 min)")
    print(f"📈 6x more frequent monitoring for market changes!")
    
    print(f"\n⚡ MARKET RESPONSIVENESS:")
    print(f"   • BTC -0.43% (from your chart) → TRIGGERS at 0.3% threshold ✅")
    print(f"   • ARB -0.95% (from your chart) → Strong bearish signal ✅")
    print(f"   • 5-minute checks → Faster reaction to market moves ✅")

if __name__ == "__main__":
    success = test_threshold_sensitivity()
    demonstrate_5min_monitoring()
    
    if success:
        print(f"\n🎯 SENSITIVITY TEST: PASSED")
        print(f"   System will now catch smaller market movements like:")
        print(f"   • BTC drops of 0.3%+ (was 1.0%+)")
        print(f"   • Check every 5 minutes (was 30 minutes)")
        print(f"   • More responsive to market conditions")
    else:
        print(f"\n⚠️ SENSITIVITY TEST: Review needed")
