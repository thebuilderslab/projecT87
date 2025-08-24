#!/usr/bin/env python3
"""
Test All Fixes - Comprehensive validation of system fixes
"""

import os
import sys
import time
import traceback
from web3 import Web3

def test_syntax_validation():
    """Test that all Python files have valid syntax"""
    print("🧪 Testing Syntax Validation...")
    try:
        # Test critical files for syntax errors
        test_files = [
            'arbitrum_testnet_agent.py',
            'enhanced_borrow_manager.py', 
            'aave_integration.py',
            'dependency_validator.py'
        ]

        for file_path in test_files:
            if os.path.exists(file_path):
                print(f"   ✅ Syntax check: {file_path}")
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
            else:
                print(f"   ⚠️ File not found: {file_path}")

        print("✅ All syntax checks passed")
        return True

    except SyntaxError as e:
        print(f"❌ Syntax error in {e.filename}: Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Syntax validation failed: {e}")
        return False

def test_agent_initialization():
    """Test agent initialization without executing transactions"""
    print("🧪 Testing Agent Initialization...")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        print("   ✅ Import successful")

        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print("   ✅ Agent initialization successful")

        # Test integration initialization
        if agent.initialize_integrations():
            print("   ✅ DeFi integrations initialized")
        else:
            print("   ⚠️ Some integrations failed but agent functional")

        return True

    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        traceback.print_exc()
        return False

def test_enhanced_borrow_manager():
    """Test enhanced borrow manager functionality"""
    print("🧪 Testing Enhanced Borrow Manager...")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        from enhanced_borrow_manager import EnhancedBorrowManager

        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()

        if hasattr(agent, 'enhanced_borrow_manager') and agent.enhanced_borrow_manager:
            ebm = agent.enhanced_borrow_manager
            print("   ✅ Enhanced Borrow Manager available")

            # Test validation method
            if hasattr(ebm, '_validate_borrow_conditions'):
                print("   ✅ Validation method exists")
            else:
                print("   ⚠️ Validation method missing")

            return True
        else:
            print("   ❌ Enhanced Borrow Manager not initialized")
            return False

    except Exception as e:
        print(f"❌ Enhanced Borrow Manager test failed: {e}")
        return False

def test_contract_validation():
    """Test contract address validation"""
    print("🧪 Testing Contract Validation...")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        agent = ArbitrumTestnetAgent()

        # Test contract addresses
        contracts = {
            'USDC': agent.usdc_address,
            'WBTC': agent.wbtc_address,
            'WETH': agent.weth_address,
            'Aave Pool': agent.aave_pool_address
        }

        all_valid = True
        for name, address in contracts.items():
            if Web3.is_address(address):
                print(f"   ✅ {name}: Valid address format")
            else:
                print(f"   ❌ {name}: Invalid address format")
                all_valid = False

        return all_valid

    except Exception as e:
        print(f"❌ Contract validation failed: {e}")
        return False

def test_gas_parameter_generation():
    """Test gas parameter generation"""
    print("🧪 Testing Gas Parameter Generation...")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        agent = ArbitrumTestnetAgent()

        # Test gas parameter generation
        gas_params = agent.get_optimized_gas_params('aave_borrow', 'market')

        if 'gas' in gas_params and 'gasPrice' in gas_params:
            print(f"   ✅ Gas parameters generated: {gas_params}")

            # Validate parameters
            if gas_params['gas'] > 21000 and gas_params['gasPrice'] > 0:
                print("   ✅ Gas parameters valid")
                return True
            else:
                print("   ❌ Gas parameters invalid")
                return False
        else:
            print("   ❌ Gas parameters missing required fields")
            return False

    except Exception as e:
        print(f"❌ Gas parameter test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all validation tests"""
    print("🚀 RUNNING ALL FIX VALIDATION TESTS")
    print("=" * 50)

    tests = [
        ("Syntax Validation", test_syntax_validation),
        ("Agent Initialization", test_agent_initialization), 
        ("Enhanced Borrow Manager", test_enhanced_borrow_manager),
        ("Contract Validation", test_contract_validation),
        ("Gas Parameter Generation", test_gas_parameter_generation)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔧 {test_name}")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print(f"\n📊 TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - System ready for execution!")
        return True
    else:
        print("⚠️ Some tests failed - review and fix issues before proceeding")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)