
#!/usr/bin/env python3
"""
Test Market Signal Strategy On-Chain
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_market_signal_integration():
    """Test market signal strategy integration"""
    print("🧪 TESTING MARKET SIGNAL STRATEGY")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        
        # Initialize integrations
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        # Test market signal strategy
        if agent.market_signal_strategy:
            print("✅ Market signal strategy initialized")
            
            # Test signal generation
            should_trade = agent.market_signal_strategy.should_execute_trade()
            print(f"📊 Trade signal: {should_trade}")
            
            # Test market data fetching
            try:
                market_data = agent.market_signal_strategy.get_market_data()
                print(f"📈 Market data retrieved: {bool(market_data)}")
            except Exception as e:
                print(f"⚠️ Market data fetch: {e}")
            
            # Test technical indicators
            try:
                if hasattr(agent.market_signal_strategy, 'calculate_technical_indicators'):
                    indicators = agent.market_signal_strategy.calculate_technical_indicators({
                        'price_1h': 0.75,
                        'price_24h': 0.73
                    })
                    print(f"📊 Technical indicators: {indicators}")
            except Exception as e:
                print(f"⚠️ Technical indicators: {e}")
            
            return True
        else:
            print("⚠️ Market signal strategy not available")
            return False
            
    except Exception as e:
        print(f"❌ Market signal test failed: {e}")
        return False

def test_integration_with_autonomous_system():
    """Test market signals with autonomous system"""
    print("\n🔄 TESTING AUTONOMOUS INTEGRATION")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Test a full autonomous cycle
        performance = agent.run_real_defi_task(1, 1, {
            'test_mode': True,
            'market_signals_enabled': True
        })
        
        print(f"🎯 Autonomous cycle performance: {performance}")
        
        if performance > 0.3:
            print("✅ Integration successful")
            return True
        else:
            print("⚠️ Integration needs optimization")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MARKET SIGNAL ON-CHAIN TESTING")
    print("=" * 60)
    
    # Test 1: Market signal strategy
    signal_test = test_market_signal_integration()
    
    # Test 2: Integration with autonomous system
    integration_test = test_integration_with_autonomous_system()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"   Market Signals: {'✅ PASS' if signal_test else '❌ FAIL'}")
    print(f"   Integration: {'✅ PASS' if integration_test else '❌ FAIL'}")
    
    if signal_test and integration_test:
        print(f"\n🎉 ALL TESTS PASSED - SYSTEM READY FOR ON-CHAIN OPERATION")
    else:
        print(f"\n⚠️ SOME TESTS FAILED - REVIEW ISSUES BEFORE DEPLOYMENT")
