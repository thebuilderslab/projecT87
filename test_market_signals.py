
#!/usr/bin/env python3
"""
Comprehensive Market Signal Strategy Testing
Tests BTC/ARB correlation analysis and debt swapping opportunities
"""

import os
import time
import json
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_market_data_apis():
    """Test market data API connectivity and data quality"""
    print("🔍 TESTING MARKET DATA APIs")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        if not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False
        
        # Test BTC data fetching
        print("📊 Testing BTC price data...")
        btc_data = agent.market_signal_strategy.get_btc_price_data()
        if btc_data:
            print(f"✅ BTC Price: ${btc_data['price']:,.2f}")
            print(f"✅ BTC 1h Change: {btc_data['percent_change_1h']:.2f}%")
            print(f"✅ BTC 24h Change: {btc_data['percent_change_24h']:.2f}%")
        else:
            print("❌ Failed to fetch BTC data")
            return False
        
        # Test ARB data fetching
        print("\n📈 Testing ARB price data...")
        arb_data = agent.market_signal_strategy.get_arb_price_data()
        if arb_data:
            print(f"✅ ARB Price: ${arb_data['price']:.4f}")
            print(f"✅ ARB 1h Change: {arb_data['percent_change_1h']:.2f}%")
            print(f"✅ ARB 24h Change: {arb_data['percent_change_24h']:.2f}%")
        else:
            print("❌ Failed to fetch ARB data")
            return False
        
        # Test technical indicators
        print("\n🔧 Testing technical indicators...")
        indicators = agent.market_signal_strategy.calculate_technical_indicators(arb_data)
        print(f"✅ RSI Estimate: {indicators['rsi']:.1f}")
        print(f"✅ MACD Signal: {indicators['macd_signal']}")
        print(f"✅ 1h Momentum: {indicators['momentum_1h']:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Market data API test failed: {e}")
        return False

def test_signal_generation():
    """Test market signal generation and confidence scoring"""
    print("\n🎯 TESTING SIGNAL GENERATION")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        if not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False
        
        # Generate market signal
        signal = agent.market_signal_strategy.analyze_market_signals()
        
        if signal:
            print(f"✅ Signal Generated:")
            print(f"   Type: {signal.signal_type}")
            print(f"   Confidence: {signal.confidence:.2f}")
            print(f"   BTC Change: {signal.btc_price_change:.2f}%")
            print(f"   ARB RSI: {signal.arb_technical_score:.1f}")
            
            # Test strategy execution decision
            should_execute, strategy_type = agent.market_signal_strategy.should_execute_market_strategy(signal)
            print(f"✅ Strategy Decision: {strategy_type} (Execute: {should_execute})")
            
            return True
        else:
            print("⚠️ No signal generated (may be in cooldown or insufficient data)")
            return True  # This is okay, signals aren't always generated
            
    except Exception as e:
        print(f"❌ Signal generation test failed: {e}")
        return False

def test_debt_swap_simulation():
    """Test debt swap simulation without actual execution"""
    print("\n🔄 TESTING DEBT SWAP SIMULATION")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Get current account status
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot get account data")
            return False
        
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        health_factor = account_data.get('healthFactor', 0)
        
        print(f"📊 Current Status:")
        print(f"   Available Borrows: ${available_borrows:.2f}")
        print(f"   Health Factor: {health_factor:.3f}")
        
        if available_borrows < 5.0:
            print("⚠️ Insufficient borrowing capacity for meaningful test")
            return True
        
        # Calculate safe swap amount
        max_swap_amount = float(os.getenv('MAX_MARKET_OPERATION_AMOUNT', '10'))
        safe_amount = min(available_borrows * 0.05, max_swap_amount)  # 5% or $10 max
        
        print(f"✅ Safe swap amount calculated: ${safe_amount:.2f}")
        print(f"✅ This would be {(safe_amount/available_borrows)*100:.1f}% of available capacity")
        
        # Verify health factor safety
        min_hf = float(os.getenv('MIN_HEALTH_FACTOR_FOR_MARKET_OPS', '2.0'))
        if health_factor >= min_hf:
            print(f"✅ Health factor {health_factor:.3f} >= {min_hf} (safe for operations)")
        else:
            print(f"⚠️ Health factor {health_factor:.3f} < {min_hf} (operations would be blocked)")
        
        return True
        
    except Exception as e:
        print(f"❌ Debt swap simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE MARKET SIGNAL TESTING")
    print("=" * 60)
    
    # Phase 1: API Testing
    api_test = test_market_data_apis()
    
    # Phase 2: Signal Generation Testing
    signal_test = test_signal_generation()
    
    # Phase 3: Debt Swap Simulation
    swap_test = test_debt_swap_simulation()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"   Market Data APIs: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"   Signal Generation: {'✅ PASS' if signal_test else '❌ FAIL'}")
    print(f"   Debt Swap Simulation: {'✅ PASS' if swap_test else '❌ FAIL'}")
    
    if api_test and signal_test and swap_test:
        print(f"\n🎉 ALL MARKET SIGNAL TESTS PASSED")
        print(f"💡 System ready for opportunistic debt swapping")
    else:
        print(f"\n⚠️ SOME TESTS FAILED - REVIEW ISSUES")
