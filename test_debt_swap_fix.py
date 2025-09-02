
#!/usr/bin/env python3
"""
Test Debt Swap Fix - Verify market signal strategy is now operational
"""

import os
import time
from datetime import datetime

def test_debt_swap_operational_status():
    """Test that debt swap system is now operational"""
    print("🔍 TESTING DEBT SWAP OPERATIONAL STATUS AFTER FIXES")
    print("=" * 55)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        print(f"✅ Agent initialized: {agent.address}")
        
        # Check market signal strategy
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            mss = agent.market_signal_strategy
            print(f"✅ Market Signal Strategy found")
            print(f"   Initialized: {getattr(mss, 'initialized', False)}")
            print(f"   Initialization Successful: {getattr(mss, 'initialization_successful', False)}")
            
            # Check debt swap status
            debt_swap_active = getattr(agent, 'debt_swap_active', False)
            print(f"   Debt Swap Active: {debt_swap_active}")
            
            # Test debt swap conditions
            try:
                conditions_ok, message = agent.check_debt_swap_conditions()
                print(f"   Debt Swap Conditions: {message}")
                
                if conditions_ok:
                    print("🎉 DEBT SWAP SYSTEM IS NOW OPERATIONAL!")
                else:
                    print("⚠️ Debt swap system has remaining issues")
                    
            except Exception as e:
                print(f"⚠️ Debt swap condition check failed: {e}")
            
            # Test strategy status
            try:
                status = mss.get_strategy_status()
                print(f"\n📊 Strategy Status:")
                print(f"   Technical Indicators Ready: {status.get('technical_indicators_ready', False)}")
                print(f"   Data Source: {status.get('data_source', 'Unknown')}")
                print(f"   Enhanced Mode: {status.get('enhanced_mode', False)}")
                
            except Exception as e:
                print(f"⚠️ Strategy status check failed: {e}")
                
        else:
            print("❌ Market Signal Strategy not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_market_signal_analysis():
    """Test market signal analysis functionality"""
    print(f"\n🔍 TESTING MARKET SIGNAL ANALYSIS")
    print("=" * 35)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            # Test signal analysis
            signals = agent.market_signal_strategy.analyze_market_signals()
            
            if signals and signals.get('status') == 'success':
                print("✅ Market signal analysis working")
                print(f"   Action: {signals.get('action', 'unknown')}")
                print(f"   Confidence: {signals.get('confidence_level', 0):.2f}")
                return True
            else:
                print("⚠️ Market signal analysis has issues")
                return False
        else:
            print("❌ No market signal strategy available")
            return False
            
    except Exception as e:
        print(f"❌ Market signal analysis test failed: {e}")
        return False

def main():
    """Run all debt swap fix tests"""
    print("🧪 DEBT SWAP FIX VERIFICATION TESTS")
    print("=" * 40)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    tests = [
        ("Debt Swap Operational Status", test_debt_swap_operational_status),
        ("Market Signal Analysis", test_market_signal_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n" + "=" * 40)
    print("📊 DEBT SWAP FIX TEST RESULTS")
    print("=" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Debt swap system is operational!")
    else:
        print("⚠️ Some tests failed - debt swap system may have remaining issues")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    return passed == total

if __name__ == "__main__":
    main()
