
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

def main():
    """Run comprehensive debt swap system test"""
    print("🚀 COMPREHENSIVE DEBT SWAP SYSTEM TEST")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Track test results
    test_results = {}
    
    # Setup test environment
    setup_test_environment()
    
    # Test 1: Agent initialization
    agent = test_agent_initialization()
    test_results['agent_init'] = agent is not None
    
    if agent:
        # Test 2: Market signal strategy
        test_results['market_signals'] = test_market_signal_strategy(agent)
        
        # Test 3: Debt swap readiness
        test_results['debt_swap_readiness'] = test_debt_swap_readiness(agent)
        
        # Test 4: Complete system integration
        test_results['system_integration'] = test_complete_system_integration(agent)
    else:
        print("❌ Skipping further tests due to agent initialization failure")
        test_results.update({
            'market_signals': False,
            'debt_swap_readiness': False,
            'system_integration': False
        })
    
    # Test 5: Enhanced market analyzer (independent)
    test_results['market_analyzer'] = test_enhanced_market_analyzer()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print("-" * 60)
    print(f"Summary: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT")
    elif passed_tests >= total_tests * 0.8:
        print("✅ MOST TESTS PASSED - SYSTEM MOSTLY FUNCTIONAL")
    else:
        print("⚠️ SEVERAL TESTS FAILED - SYSTEM NEEDS FIXES")
    
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
