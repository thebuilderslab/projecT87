
#!/usr/bin/env python3
"""
Test Debt Swap Triggers - Check if conditions are met for debt swapping
"""

import os
import time
from datetime import datetime

def test_debt_swap_triggers():
    """Test current debt swap trigger conditions"""
    print("🔍 DEBT SWAP TRIGGER TEST")
    print("=" * 40)
    
    # Check environment variables
    print("\n📋 Environment Configuration:")
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false')
    btc_threshold = os.getenv('BTC_DROP_THRESHOLD', '0.01')
    dai_to_arb_threshold = os.getenv('DAI_TO_ARB_THRESHOLD', '0.7')
    arb_rsi_oversold = os.getenv('ARB_RSI_OVERSOLD', '30')
    
    print(f"   MARKET_SIGNAL_ENABLED: {market_enabled}")
    print(f"   BTC_DROP_THRESHOLD: {btc_threshold}")
    print(f"   DAI_TO_ARB_THRESHOLD: {dai_to_arb_threshold}")
    print(f"   ARB_RSI_OVERSOLD: {arb_rsi_oversold}")
    
    # Check if debt swap would be triggered
    print(f"\n🎯 Debt Swap Readiness:")
    if market_enabled.lower() == 'true':
        print("   ✅ Market signals are ENABLED")
        print("   🔍 System will monitor for:")
        print(f"      • BTC drops ≥ {float(btc_threshold)*100:.1f}%")
        print(f"      • ARB RSI ≤ {arb_rsi_oversold}")
        print(f"      • Confidence ≥ {float(dai_to_arb_threshold)*100:.0f}%")
    else:
        print("   ❌ Market signals are DISABLED")
        print("   💡 To enable debt swaps, set MARKET_SIGNAL_ENABLED=true in Replit Secrets")
    
    # Check if autonomous system is running
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            print("   ✅ Market Signal Strategy initialized")
            
            # Test current market conditions
            signal = agent.market_signal_strategy.analyze_market_signals()
            if signal:
                print(f"\n📊 Current Market Analysis:")
                print(f"   BTC Price Change: {getattr(signal, 'btc_price_change', signal.get('btc_price_change', 0.0)) if hasattr(signal, 'get') else getattr(signal, 'btc_price_change', 0.0):.2f}%")
                print(f"   ARB RSI: {signal.arb_rsi:.1f}")
                print(f"   Confidence: {signal.confidence:.1%}")
                print(f"   Should Execute: {signal.should_execute}")
                
                if signal.should_execute:
                    print("   🚀 DEBT SWAP WOULD BE TRIGGERED NOW!")
                else:
                    print("   ⏳ Waiting for trigger conditions...")
            else:
                print("   ⚠️ No market signal data available")
        else:
            print("   ❌ Market Signal Strategy not initialized")
            
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
    
    print(f"\n📝 To see debt swap logs in the console:")
    print(f"   1. Ensure MARKET_SIGNAL_ENABLED=true in Secrets")
    print(f"   2. Wait for market conditions to trigger")
    print(f"   3. Monitor console for 'DEBT SWAP' messages")
    print(f"   4. Check performance_log.json for operation details")

if __name__ == "__main__":
    test_debt_swap_triggers()
