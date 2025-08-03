
#!/usr/bin/env python3
"""
Test Debt Swap Configuration - Verify market signals are properly configured
"""

import os
import time
from datetime import datetime

def test_debt_swap_configuration():
    """Test current debt swap configuration"""
    print("🔍 DEBT SWAP CONFIGURATION TEST")
    print("=" * 40)
    
    # Check environment variables
    print("\n📋 Environment Configuration:")
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'NOT_SET')
    btc_threshold = os.getenv('BTC_DROP_THRESHOLD', 'NOT_SET')
    dai_threshold = os.getenv('DAI_TO_ARB_THRESHOLD', 'NOT_SET')
    arb_rsi = os.getenv('ARB_RSI_OVERSOLD', 'NOT_SET')
    
    print(f"   MARKET_SIGNAL_ENABLED: {market_enabled}")
    print(f"   BTC_DROP_THRESHOLD: {btc_threshold}")
    print(f"   DAI_TO_ARB_THRESHOLD: {dai_threshold}")
    print(f"   ARB_RSI_OVERSOLD: {arb_rsi}")
    
    # Validation
    config_valid = True
    if market_enabled.lower() != 'true':
        print(f"   ❌ Market signals not enabled")
        config_valid = False
    else:
        print(f"   ✅ Market signals enabled")
    
    # Test agent initialization
    print(f"\n🤖 Agent Market Signal Test:")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            print(f"   ✅ Market Signal Strategy: Initialized")
            print(f"   📊 Strategy enabled: {agent.market_signal_strategy.market_signal_enabled}")
            print(f"   🎯 BTC threshold: {agent.market_signal_strategy.btc_drop_threshold*100:.1f}%")
            print(f"   📈 DAI→ARB threshold: {agent.market_signal_strategy.dai_to_arb_threshold:.0%}")
            
            # Test market analysis
            print(f"\n📊 Live Market Analysis Test:")
            signal = agent.market_signal_strategy.analyze_market_signals()
            if signal:
                print(f"   ✅ Signal generated: {signal.signal_type}")
                print(f"   📈 BTC change: {signal.btc_price_change:.2f}%")
                print(f"   🎯 Confidence: {signal.confidence:.2f}")
                print(f"   📊 ARB RSI: {signal.arb_technical_score:.1f}")
                
                # Test execution readiness
                should_execute = agent.market_signal_strategy.should_execute_trade()
                print(f"   🚀 Ready to execute: {'YES' if should_execute else 'NO'}")
                
                if should_execute:
                    print(f"   🎉 DEBT SWAP CONDITIONS MET - System ready to execute!")
                else:
                    print(f"   ⏳ Waiting for market conditions to align")
            else:
                print(f"   ⚠️ No signal generated (normal if conditions not met)")
        else:
            print(f"   ❌ Market Signal Strategy: Not initialized")
            config_valid = False
            
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")
        config_valid = False
    
    # Summary
    print(f"\n📝 Configuration Summary:")
    if config_valid and market_enabled.lower() == 'true':
        print(f"   ✅ DEBT SWAP SYSTEM: READY")
        print(f"   🔄 System will monitor market conditions and execute swaps automatically")
        print(f"   📊 Check dashboard console for real-time debt swap monitoring")
    else:
        print(f"   ❌ DEBT SWAP SYSTEM: NOT READY")
        print(f"   💡 Ensure MARKET_SIGNAL_ENABLED=true in Replit Secrets")
        print(f"   🔧 Verify all environment variables are properly set")

if __name__ == "__main__":
    test_debt_swap_configuration()
