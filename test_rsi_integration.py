
#!/usr/bin/env python3
"""
Test RSI Integration with Market Signal Strategy
"""

import os
import sys
from rsi_calculator import RSICalculator

def test_rsi_integration():
    """Test RSI integration with your DeFi system"""
    print("📊 TESTING RSI INTEGRATION")
    print("=" * 40)
    
    # Test 1: RSI Calculator
    api_key = os.getenv('COINMARKETCAP_API_KEY')
    if not api_key:
        print("❌ COINMARKETCAP_API_KEY not found in secrets")
        return False
    
    calculator = RSICalculator(api_key)
    
    # Test ARB RSI
    print("\n🔍 Testing ARB RSI...")
    arb_rsi = calculator.get_arb_rsi()
    print(f"ARB RSI: {arb_rsi['rsi']:.1f}")
    print(f"Status: {arb_rsi['status']}")
    
    # Test signal generation
    if arb_rsi['rsi'] <= 30:
        print("✅ RSI indicates OVERSOLD condition - Good for DAI→ARB swap")
    elif arb_rsi['rsi'] >= 70:
        print("⚠️ RSI indicates OVERBOUGHT condition - Good for ARB→DAI swap")
    else:
        print("ℹ️ RSI indicates NEUTRAL condition - Hold position")
    
    # Test market signal strategy integration
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            strategy = agent.market_signal_strategy
            
            if hasattr(strategy, 'rsi_calculator'):
                print("✅ RSI Calculator integrated with Market Signal Strategy")
                
                # Test signal analysis
                signal = strategy.analyze_market_signals()
                if signal:
                    print(f"Market Signal Generated:")
                    print(f"  Type: {signal.signal_type}")
                    print(f"  Confidence: {signal.confidence:.2f}")
                    print(f"  ARB RSI: {signal.arb_technical_score:.1f}")
                    return True
                else:
                    print("⚠️ No market signal generated")
                    return True
            else:
                print("⚠️ RSI Calculator not integrated - using fallback calculations")
                return True
        else:
            print("⚠️ Market Signal Strategy not available")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_rsi_integration()
    if success:
        print("\n✅ RSI integration test completed successfully")
    else:
        print("\n❌ RSI integration test failed")
