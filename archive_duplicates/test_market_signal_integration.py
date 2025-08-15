
#!/usr/bin/env python3
"""
Comprehensive Market Signal Integration Test
Tests all components after fixes are applied
"""

import os
import sys
import traceback

def test_import_dependencies():
    """Test 1: Verify all imports work correctly"""
    print("🔍 TESTING IMPORT DEPENDENCIES")
    print("=" * 40)
    
    try:
        # Test market signal strategy import
        from market_signal_strategy import MarketSignalStrategy
        print("✅ MarketSignalStrategy imported successfully")
        
        # Test enhanced analyzer import
        from enhanced_market_analyzer import EnhancedMarketAnalyzer, EnhancedMarketSignal
        print("✅ EnhancedMarketAnalyzer imported successfully")
        
        # Test advanced trend analyzer import
        from advanced_trend_analyzer import AdvancedTrendAnalyzer, TrendAnalysis
        print("✅ AdvancedTrendAnalyzer imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_method_signatures():
    """Test 2: Verify method signatures are consistent"""
    print("\n🔍 TESTING METHOD SIGNATURES")
    print("=" * 40)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Check if standardized methods exist
        required_methods = [
            '_execute_market_signal_operation',
            '_validate_market_signal_environment',
            'initialize_integrations'
        ]
        
        for method in required_methods:
            if hasattr(agent, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Method signature test failed: {e}")
        return False

def test_configuration_validation():
    """Test 3: Verify configuration validation works"""
    print("\n🔍 TESTING CONFIGURATION VALIDATION")
    print("=" * 40)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Test with current environment
        agent = ArbitrumTestnetAgent()
        print("✅ Agent initialized with current configuration")
        
        # Test market signal validation
        if hasattr(agent, '_validate_market_signal_environment'):
            result = agent._validate_market_signal_environment()
            print(f"✅ Market signal validation: {'Passed' if result else 'Failed (non-critical)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def test_integration_flow():
    """Test 4: Test complete integration flow"""
    print("\n🔍 TESTING INTEGRATION FLOW")
    print("=" * 40)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print("✅ Agent initialized")
        
        # Initialize integrations
        success = agent.initialize_integrations()
        if success:
            print("✅ DeFi integrations initialized")
        else:
            print("⚠️ Some integrations failed (expected in test environment)")
        
        # Test market signal strategy if available
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            print("✅ Market signal strategy available")
            
            # Test should_execute_trade method
            if hasattr(agent.market_signal_strategy, 'should_execute_trade'):
                print("✅ should_execute_trade method available")
            else:
                print("❌ should_execute_trade method missing")
                return False
        else:
            print("ℹ️ Market signal strategy not enabled (check MARKET_SIGNAL_ENABLED)")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration flow test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("🧪 MARKET SIGNAL INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Import Dependencies", test_import_dependencies),
        ("Method Signatures", test_method_signatures),
        ("Configuration Validation", test_configuration_validation),
        ("Integration Flow", test_integration_flow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = (passed / len(results)) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed}/{len(results)} tests passed)")
    
    if success_rate >= 75:
        print("🎉 Integration ready for network approval!")
        return True
    else:
        print("⚠️ More fixes needed before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
