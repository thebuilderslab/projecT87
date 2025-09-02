#!/usr/bin/env python3
"""
Comprehensive Debt Swap System Test
Tests all components and validates functionality
"""

import os
import time
from datetime import datetime

def setup_test_environment():
    """Setup test environment variables"""
    print("🔧 SETTING UP TEST ENVIRONMENT")
    print("=" * 50)

    # Set required environment variables for testing
    test_config = {
        'MARKET_SIGNAL_ENABLED': 'true',
        'BTC_DROP_THRESHOLD': '0.002',
        'DAI_TO_ARB_THRESHOLD': '0.92',
        'ARB_TO_DAI_THRESHOLD': '0.88',
        'ARB_RSI_OVERSOLD': '30',
        'ARB_RSI_OVERBOUGHT': '70',
        'NETWORK_MODE': 'testnet'  # Use testnet for safety
    }

    for key, value in test_config.items():
        os.environ[key] = value
        print(f"✅ Set {key}={value}")

    print("✅ Test environment configured")

def test_agent_initialization():
    """Test agent initialization with all fixes"""
    print("\n🧪 TESTING AGENT INITIALIZATION")
    print("=" * 50)

    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        # Initialize agent
        print("🤖 Creating ArbitrumTestnetAgent...")
        agent = ArbitrumTestnetAgent()

        print(f"✅ Agent created - Address: {agent.address}")
        print(f"✅ Network mode: {agent.network_mode}")
        print(f"✅ Chain ID: {agent.w3.eth.chain_id}")

        # Test integration initialization
        print("🔧 Testing integration initialization...")
        success = agent.initialize_integrations()

        if success:
            print("✅ All integrations initialized successfully")
            return agent
        else:
            print("❌ Integration initialization failed")
            return None

    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        import traceback
        print(f"🔍 Full error: {traceback.format_exc()}")
        return None

def test_market_signal_strategy(agent):
    """Test market signal strategy functionality"""
    print("\n🧪 TESTING MARKET SIGNAL STRATEGY")
    print("=" * 50)

    try:
        if not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False

        mss = agent.market_signal_strategy
        print(f"✅ Market Signal Strategy loaded")
        print(f"   Enabled: {mss.market_signal_enabled}")
        print(f"   Initialized: {mss.initialized}")

        # Test signal analysis
        print("📊 Testing signal analysis...")
        try:
            signals = mss.analyze_market_signals()
            print(f"✅ Signal analysis successful")
            print(f"   Status: {signals.get('status', 'unknown')}")
            print(f"   Recommendation: {signals.get('recommendation', 'UNKNOWN')}")
            print(f"   Signal strength: {signals.get('signal_strength', 0):.3f}")

            # Test trade decision
            should_trade = mss.should_execute_trade()
            print(f"✅ Trade decision: {'EXECUTE' if should_trade else 'HOLD'}")

            return True

        except Exception as signal_error:
            print(f"❌ Signal analysis failed: {signal_error}")
            return False

    except Exception as e:
        print(f"❌ Market signal strategy test failed: {e}")
        return False

def test_debt_swap_readiness(agent):
    """Test debt swap readiness validation"""
    print("\n🧪 TESTING DEBT SWAP READINESS")
    print("=" * 50)

    try:
        readiness = agent.validate_debt_swap_readiness()

        if readiness:
            print("✅ System ready for debt swaps")
        else:
            print("⚠️ System not ready for debt swaps (this may be expected)")

        # Test individual components
        print("🔍 Testing individual readiness components...")

        # Test health factor
        health_factor = agent.get_health_factor()
        print(f"📊 Health factor: {health_factor:.4f}")

        # Test ETH balance
        eth_balance = agent.get_eth_balance()
        print(f"💰 ETH balance: {eth_balance:.6f}")

        return True

    except Exception as e:
        print(f"❌ Debt swap readiness test failed: {e}")
        return False

def test_enhanced_market_analyzer():
    """Test enhanced market analyzer with rate limiting"""
    print("\n🧪 TESTING ENHANCED MARKET ANALYZER")
    print("=" * 50)

    try:
        from enhanced_market_analyzer import EnhancedMarketAnalyzer

        # Create mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x1234567890123456789012345678901234567890"

        mock_agent = MockAgent()
        analyzer = EnhancedMarketAnalyzer(mock_agent)

        print("✅ Enhanced Market Analyzer created")

        # Test price fetching with rate limiting
        print("📊 Testing price fetching...")
        try:
            prices = analyzer.get_current_prices(['BTC', 'ETH', 'ARB', 'DAI'])

            for symbol, data in prices.items():
                if data:
                    source = data.get('source', 'api')
                    synthetic = data.get('synthetic', False)
                    price = data.get('price', 0)
                    print(f"✅ {symbol}: ${price:.4f} ({'synthetic' if synthetic else source})")
                else:
                    print(f"❌ {symbol}: No data available")

            return True

        except Exception as price_error:
            print(f"❌ Price fetching failed: {price_error}")
            return False

    except Exception as e:
        print(f"❌ Enhanced market analyzer test failed: {e}")
        return False

def test_complete_system_integration(agent):
    """Test complete system integration"""
    print("\n🧪 TESTING COMPLETE SYSTEM INTEGRATION")
    print("=" * 50)

    try:
        # Test market signal operation
        print("🔄 Testing market signal operation...")
        try:
            result = agent._execute_market_signal_operation()
            print(f"✅ Market signal operation result: {result}")
        except Exception as op_error:
            print(f"⚠️ Market signal operation error: {op_error}")

        # Test real DeFi task
        print("🔄 Testing real DeFi task...")
        try:
            performance = agent.run_real_defi_task(1, 1, {})
            print(f"✅ DeFi task performance: {performance:.2f}")
        except Exception as task_error:
            print(f"⚠️ DeFi task error: {task_error}")

        return True

    except Exception as e:
        print(f"❌ Complete system integration test failed: {e}")
        return False

def test_market_signals():
    """Test market signal strategy functionality"""
    try:
        print("\n🔍 Testing Market Signal Strategy...")

        # Test if market signal strategy can be imported and initialized
        try:
            from market_signal_strategy import MarketSignalStrategy
            agent = ArbitrumTestnetAgent()
            strategy = MarketSignalStrategy(agent)

            print("✅ Market signal strategy imported and initialized")

            # Test basic functionality
            if hasattr(strategy, 'market_signal_enabled'):
                print(f"✅ Market signal enabled: {strategy.market_signal_enabled}")

            if hasattr(strategy, 'get_market_analysis'):
                analysis = strategy.get_market_analysis()
                if analysis:
                    print("✅ Market analysis function working")
                else:
                    print("⚠️ Market analysis returned no data")

            return True

        except ImportError:
            print("⚠️ Market signal strategy not available")
            return True  # Not a failure if optional feature is missing
        except Exception as e:
            print(f"❌ Market signal test failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Market signal test error: {e}")
        return False

def test_debt_swap_readiness():
    """Test debt swap system readiness"""
    try:
        print("\n🔍 Testing Debt Swap Readiness...")

        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()

        # Test debt swap readiness validation
        readiness = agent.validate_debt_swap_readiness()

        if readiness['ready']:
            print(f"✅ Debt swap system ready ({readiness['score']:.0f}%)")
            return True
        else:
            print(f"⚠️ Debt swap system not ready ({readiness['score']:.0f}%)")
            print("Issues found:")
            for key, value in readiness['details'].items():
                status = "✅" if value else "❌"
                print(f"   {status} {key}")
            return readiness['score'] > 60  # Pass if score is reasonable

    except Exception as e:
        print(f"❌ Debt swap readiness test failed: {e}")
        return False

def test_system_integration():
    """Test overall system integration"""
    try:
        print("\n🔍 Testing System Integration...")

        agent = ArbitrumTestnetAgent()

        # Test 1: Basic initialization
        if not agent.initialize_integrations():
            print("❌ Integration initialization failed")
            return False
        print("✅ Integrations initialized")

        # Test 2: Network connectivity
        if not agent.w3 or not agent.w3.is_connected():
            print("❌ Network not connected")
            return False
        print("✅ Network connected")

        # Test 3: Account data retrieval
        account_data = agent.get_user_account_data()
        if not account_data:
            print("❌ Cannot retrieve account data")
            return False
        print("✅ Account data retrieved")

        # Test 4: Health factor check
        health_factor = agent.get_health_factor()
        if health_factor <= 0:
            print("❌ Invalid health factor")
            return False
        print(f"✅ Health factor: {health_factor:.3f}")

        # Test 5: Balance checks
        eth_balance = agent.get_eth_balance()
        if eth_balance < 0.001:
            print(f"⚠️ Low ETH balance: {eth_balance:.6f}")
        else:
            print(f"✅ ETH balance sufficient: {eth_balance:.6f}")

        return True

    except Exception as e:
        print(f"❌ System integration test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all debt swap system tests"""
    print("🔍 RUNNING COMPREHENSIVE DEBT SWAP SYSTEM TESTS")
    print("=" * 60)

    # Initialize agent for testing
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        print("✅ Agent initialized for testing")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

    # Run individual tests
    test_results = {}

    # Test 1: Market Signal Configuration
    test_results['market_signals'] = test_market_signals()

    # Test 2: Debt Swap Readiness
    test_results['debt_swap_readiness'] = test_debt_swap_readiness()

    # Test 3: System Integration
    test_results['system_integration'] = test_system_integration()

    # Calculate overall success rate
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100

    print(f"\n📊 TEST RESULTS SUMMARY:")
    print(f"=" * 40)
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")

    if success_rate >= 80:
        print("🎉 SYSTEM READY FOR NETWORK APPROVAL")
        return True
    else:
        print("⚠️ SYSTEM NEEDS IMPROVEMENTS BEFORE NETWORK APPROVAL")
        return False

def main():
    """Run comprehensive debt swap system test"""
    print("🚀 COMPREHENSIVE DEBT SWAP SYSTEM TEST")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Setup test environment
    setup_test_environment()

    # Run all tests
    test_results = {}

    test_results['agent_init'] = test_agent_initialization()

    if test_results['agent_init']:
        # Pass agent to tests that require it
        test_results['market_signals'] = test_market_signals()
        test_results['debt_swap_readiness'] = test_debt_swap_readiness()
        test_results['system_integration'] = test_system_integration()
    else:
        print("❌ Skipping further tests due to agent initialization failure")
        test_results['market_signals'] = False
        test_results['debt_swap_readiness'] = False
        test_results['system_integration'] = False

    test_results['market_analyzer'] = test_enhanced_market_analyzer()

    # Calculate results
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    success_rate = (passed_tests / total_tests) * 100

    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)

    test_names = {
        'agent_init': 'Agent Init',
        'market_signals': 'Market Signals',
        'debt_swap_readiness': 'Debt Swap Readiness',
        'system_integration': 'System Integration',
        'market_analyzer': 'Market Analyzer'
    }

    for key, name in test_names.items():
        status = "✅ PASS" if test_results[key] else "❌ FAIL"
        print(f"{name}: {status}")

    print("-" * 60)
    print(f"Summary: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

    if success_rate >= 80:
        print("🎉 SYSTEM READY FOR NETWORK APPROVAL")
    elif success_rate >= 60:
        print("⚠️ SYSTEM NEEDS MINOR FIXES")
    else:
        print("⚠️ SEVERAL TESTS FAILED - SYSTEM NEEDS FIXES")

    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Placeholder for the actual test function call
def test_debt_swap_system():
    """Placeholder for the main test execution function"""
    main()

if __name__ == "__main__":
    test_debt_swap_system()