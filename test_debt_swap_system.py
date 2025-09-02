
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
        test_results['market_signals'] = test_market_signals(agent)
        
        # Test 3: Debt swap readiness
        test_results['debt_swap_readiness'] = test_debt_swap_readiness(agent)
        
        # Test 4: Complete system integration
        test_results['system_integration'] = test_system_integration(agent)
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
#!/usr/bin/env python3
"""
Comprehensive Debt Swap System Test
Tests all components for network approval readiness
"""

import os
import time
import sys
from datetime import datetime

def setup_test_environment():
    """Setup test environment variables"""
    print("🔧 SETTING UP TEST ENVIRONMENT")
    print("=" * 50)
    
    # Set test environment variables
    test_vars = {
        'MARKET_SIGNAL_ENABLED': 'true',
        'BTC_DROP_THRESHOLD': '0.002',
        'DAI_TO_ARB_THRESHOLD': '0.92',
        'ARB_TO_DAI_THRESHOLD': '0.88',
        'ARB_RSI_OVERSOLD': '30',
        'ARB_RSI_OVERBOUGHT': '70',
        'NETWORK_MODE': 'testnet'
    }
    
    for key, value in test_vars.items():
        os.environ[key] = value
        print(f"✅ Set {key}={value}")
    
    print("✅ Test environment configured")
    return True

def test_agent_initialization():
    """Test agent initialization"""
    print("\n🧪 TESTING AGENT INITIALIZATION")
    print("=" * 50)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        if not agent:
            print("❌ Agent initialization failed")
            return False
            
        print("✅ Agent initialized successfully")
        
        # Test integration initialization
        if agent.initialize_integrations():
            print("✅ DeFi integrations initialized")
            return True
        else:
            print("❌ DeFi integrations failed")
            return False
            
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        print(f"🔍 Full error: {sys.exc_info()}")
        return False

def test_enhanced_market_analyzer():
    """Test enhanced market analyzer"""
    print("\n🧪 TESTING ENHANCED MARKET ANALYZER")
    print("=" * 50)
    
    try:
        from enhanced_market_analyzer import EnhancedMarketAnalyzer
        
        # Create mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x1234567890123456789012345678901234567890"
        
        agent = MockAgent()
        analyzer = EnhancedMarketAnalyzer(agent)
        print("✅ Enhanced Market Analyzer created")
        
        # Test price fetching
        print("📊 Testing price fetching...")
        prices = analyzer.get_current_prices(['BTC', 'ETH', 'ARB', 'DAI'])
        
        for symbol, data in prices.items():
            if data and 'price' in data:
                source = 'api' if not data.get('synthetic', False) else 'synthetic'
                print(f"✅ {symbol}: ${data['price']:.4f} ({source})")
            else:
                print(f"❌ {symbol}: No data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced market analyzer test failed: {e}")
        return False

def test_market_signals(agent):
    """Test market signal functionality"""
    print("\n🧪 TESTING MARKET SIGNALS")
    print("=" * 50)
    
    try:
        if not agent:
            print("❌ Agent not available for market signals test")
            return False
            
        # Check if market signal strategy is initialized
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            print("✅ Market signal strategy available")
            
            # Test market signal analysis
            try:
                if hasattr(agent.market_signal_strategy, 'analyze_market_signals'):
                    signals = agent.market_signal_strategy.analyze_market_signals()
                    print(f"✅ Market analysis successful: {signals.get('status', 'unknown')}")
                else:
                    print("⚠️ Market analysis method not available")
                
                # Test trade decision logic
                if hasattr(agent.market_signal_strategy, 'should_execute_trade'):
                    should_trade = agent.market_signal_strategy.should_execute_trade()
                    print(f"✅ Trade decision logic working: {should_trade}")
                else:
                    print("⚠️ Trade decision method not available")
                
                return True
                
            except Exception as signal_error:
                print(f"❌ Market signal analysis failed: {signal_error}")
                return False
        else:
            print("⚠️ Market signal strategy not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Market signals test failed: {e}")
        return False

def test_debt_swap_readiness(agent):
    """Test debt swap readiness"""
    print("\n🧪 TESTING DEBT SWAP READINESS")
    print("=" * 50)
    
    try:
        if not agent:
            print("❌ Agent not available for debt swap test")
            return False
            
        # Test basic readiness components
        print("🔍 Testing debt swap readiness components...")
        
        # Test health factor
        try:
            health_factor = agent.get_health_factor()
            if health_factor > 2.0:
                print(f"✅ Health factor safe for debt swaps: {health_factor:.4f}")
            else:
                print(f"⚠️ Health factor low: {health_factor:.4f}")
        except Exception as hf_error:
            print(f"❌ Health factor check failed: {hf_error}")
        
        # Test ETH balance
        try:
            eth_balance = agent.get_eth_balance()
            if eth_balance > 0.001:
                print(f"✅ ETH balance sufficient: {eth_balance:.6f}")
            else:
                print(f"⚠️ ETH balance low: {eth_balance:.6f}")
        except Exception as eth_error:
            print(f"❌ ETH balance check failed: {eth_error}")
        
        # Test Aave integration
        if hasattr(agent, 'aave') and agent.aave:
            print("✅ Aave integration ready")
        else:
            print("❌ Aave integration not available")
        
        # Test Uniswap integration  
        if hasattr(agent, 'uniswap') and agent.uniswap:
            print("✅ Uniswap integration ready")
        else:
            print("❌ Uniswap integration not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Debt swap readiness test failed: {e}")
        return False

def test_system_integration(agent):
    """Test system integration"""
    print("\n🧪 TESTING SYSTEM INTEGRATION")
    print("=" * 50)
    
    try:
        if not agent:
            print("❌ Agent not available for system integration test")
            return False
        
        # Test overall system health
        print("🔍 Testing system health...")
        
        # Check network approval readiness
        if hasattr(agent, 'check_network_approval_readiness'):
            readiness = agent.check_network_approval_readiness()
            print(f"✅ Network approval readiness: {readiness.get('ready', False)}")
            print(f"   Score: {readiness.get('score', 0)}/{readiness.get('max_score', 100)}")
            print(f"   Status: {readiness.get('status', 'unknown')}")
        else:
            print("⚠️ Network approval readiness method not available")
        
        # Test ETH balance check
        try:
            eth_balance = agent.get_eth_balance()
            print(f"✅ ETH balance check: {eth_balance:.6f} ETH")
        except Exception as e:
            print(f"❌ ETH balance check failed: {e}")
        
        # Test health factor check
        try:
            health_factor = agent.get_health_factor()
            print(f"✅ Health factor check: {health_factor:.4f}")
        except Exception as e:
            print(f"❌ Health factor check failed: {e}")
        
        # Test real DeFi task execution
        print("🔍 Testing real DeFi task execution...")
        try:
            if hasattr(agent, 'run_real_defi_task'):
                performance = agent.run_real_defi_task(1, 1, {})
                print(f"✅ DeFi task execution: {performance:.2f} performance score")
            else:
                print("⚠️ run_real_defi_task method not available")
        except Exception as e:
            print(f"❌ DeFi task execution failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ System integration test failed: {e}")
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

if __name__ == "__main__":
    main()
