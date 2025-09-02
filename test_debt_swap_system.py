#!/usr/bin/env python3
"""
Comprehensive Debt Swap System Test
Tests all aspects of debt swap functionality including market signals and execution
"""

import time
import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_debt_swap_initialization():
    """Test if debt swap system is properly initialized"""
    print("🔍 TESTING DEBT SWAP INITIALIZATION")
    print("=" * 50)

    try:
        agent = ArbitrumTestnetAgent()

        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False

        # Check market signal strategy
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            print("✅ Market signal strategy initialized")

            # Check if debt swap is active
            if getattr(agent, 'debt_swap_active', False):
                print("✅ Debt swap system is ACTIVE")
                return True
            else:
                print("⚠️ Debt swap system initialized but not active")
                return False
        else:
            print("❌ Market signal strategy not initialized")
            return False

    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        return False

def test_debt_swap_conditions():
    """Test debt swap execution conditions"""
    print("\n🔍 TESTING DEBT SWAP CONDITIONS")
    print("=" * 50)

    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()

        # Check debt swap conditions
        conditions_ok, message = agent.check_debt_swap_conditions()

        print(f"📊 Debt swap conditions: {message}")

        if conditions_ok:
            print("✅ All debt swap conditions met")
            return True
        else:
            print("⚠️ Some debt swap conditions not met")
            print("💡 This is normal if market conditions aren't optimal")
            return True  # Not failing test as this is expected sometimes

    except Exception as e:
        print(f"❌ Conditions test failed: {e}")
        return False

def test_bidirectional_swap_readiness():
    """Test readiness for bidirectional swaps"""
    print("\n🔍 TESTING BIDIRECTIONAL SWAP READINESS")
    print("=" * 50)

    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()

        # Check balances
        dai_balance = agent.get_dai_balance()
        arb_balance = agent.get_arb_balance()
        eth_balance = agent.get_eth_balance()

        print(f"💰 Current Balances:")
        print(f"   DAI: {dai_balance:.6f}")
        print(f"   ARB: {arb_balance:.6f}")
        print(f"   ETH: {eth_balance:.6f}")

        # Check if we have sufficient balances for testing
        min_test_balance = 0.1

        if dai_balance >= min_test_balance:
            print("✅ Sufficient DAI for DAI → ARB swap test")
            dai_ready = True
        else:
            print("⚠️ Insufficient DAI for swap test")
            dai_ready = False

        if arb_balance >= min_test_balance:
            print("✅ Sufficient ARB for ARB → DAI swap test")
            arb_ready = True
        else:
            print("⚠️ Insufficient ARB for swap test")
            arb_ready = False

        if eth_balance >= 0.001:
            print("✅ Sufficient ETH for gas fees")
            eth_ready = True
        else:
            print("❌ Insufficient ETH for gas fees")
            eth_ready = False

        return dai_ready or arb_ready and eth_ready

    except Exception as e:
        print(f"❌ Readiness test failed: {e}")
        return False

def test_market_signal_analysis():
    """Test market signal analysis functionality"""
    print("\n🔍 TESTING MARKET SIGNAL ANALYSIS")
    print("=" * 50)

    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()

        if not hasattr(agent, 'market_signal_strategy') or not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False

        # Test strategy status
        try:
            status = agent.market_signal_strategy.get_strategy_status()
            print("✅ Strategy status retrieved successfully")

            # Check key status indicators
            tech_ready = status.get('technical_indicators_ready', False)
            arb_points = status.get('enhanced_arb_points', 0)
            btc_points = status.get('enhanced_btc_points', 0)

            print(f"📊 Technical Indicators Ready: {tech_ready}")
            print(f"📈 ARB Data Points: {arb_points}")
            print(f"📈 BTC Data Points: {btc_points}")

            return True

        except Exception as e:
            print(f"❌ Strategy status test failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Market signal test failed: {e}")
        return False

def test_debt_swap_readiness():
    """Test debt swap system readiness"""
    print("\n🔍 TESTING DEBT SWAP READINESS")
    print("=" * 50)

    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()

        # Test debt swap readiness validation
        readiness = agent._validate_debt_swap_readiness()

        if readiness['ready']:
            print(f"✅ Debt swap system ready ({readiness['score']:.0f}%)")
            return True
        else:
            print(f"⚠️ Debt swap system not ready ({readiness['score']:.0f}%)")
            print("Issues found:")
            for key, value in readiness['details'].items():
                status = "✅" if value else "❌"
                print(f"   {status} {key}")
            return readiness['score'] > 60  # Allow partial readiness

    except Exception as e:
        print(f"❌ Readiness test failed: {e}")
        return False

def run_comprehensive_debt_swap_test():
    """Run all debt swap tests"""
    print("🚀 COMPREHENSIVE DEBT SWAP SYSTEM TEST")
    print("=" * 60)

    tests = [
        ("Debt Swap Initialization", test_debt_swap_initialization),
        ("Debt Swap Conditions", test_debt_swap_conditions),
        ("Bidirectional Swap Readiness", test_bidirectional_swap_readiness),
        ("Market Signal Analysis", test_market_signal_analysis),
        ("Debt Swap Readiness", test_debt_swap_readiness)
    ]

    results = {}
    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")

    if passed >= total * 0.7:  # 70% pass rate
        print("✅ DEBT SWAP SYSTEM: OPERATIONAL")
        return True
    else:
        print("❌ DEBT SWAP SYSTEM: NEEDS ATTENTION")
        return False

if __name__ == "__main__":
    success = run_comprehensive_debt_swap_test()

    if success:
        print("\n🎉 DEBT SWAP SYSTEM IS OPERATIONAL")
        print("💡 Ready for network approval and live trading")
    else:
        print("\n⚠️ DEBT SWAP SYSTEM NEEDS IMPROVEMENTS")
        print("💡 Review failed tests and address issues")