
#!/usr/bin/env python3
"""
Comprehensive Test Script for All System Fixes
"""

import os
import sys
import time
from web3 import Web3

def test_usdc_address_fix():
    """Test USDC address consistency"""
    print("🏦 Testing USDC Address Fix...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Create agent instance
        agent = ArbitrumTestnetAgent()
        
        # Check USDC address
        expected_usdc = "0xFF970A61A04b1cA14834A651bAb06d67307796618"
        if agent.usdc_address.lower() == expected_usdc.lower():
            print("✅ USDC address correctly set to USDC.e")
            return True
        else:
            print(f"❌ USDC address mismatch: {agent.usdc_address} vs {expected_usdc}")
            return False
            
    except Exception as e:
        print(f"❌ USDC address test failed: {e}")
        return False

def test_json_serialization_fix():
    """Test JSON serialization with Decimal types"""
    print("📄 Testing JSON Serialization Fix...")
    
    try:
        from fix_json_serialization import DecimalEncoder, safe_json_dump
        from decimal import Decimal
        
        # Test data with Decimal types
        test_data = {
            'health_factor': Decimal('2.5'),
            'collateral_usd': Decimal('150.75'),
            'timestamp': time.time()
        }
        
        # Test serialization
        success = safe_json_dump(test_data, 'test_decimal_serialization.json')
        
        if success and os.path.exists('test_decimal_serialization.json'):
            # Clean up
            os.remove('test_decimal_serialization.json')
            print("✅ JSON serialization with Decimals working")
            return True
        else:
            print("❌ JSON serialization failed")
            return False
            
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False

def test_contract_validation():
    """Test contract validation system"""
    print("🔍 Testing Contract Validation...")
    
    try:
        from contract_validator import ContractValidator
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Create agent to get Web3 instance
        agent = ArbitrumTestnetAgent()
        
        # Test contract validation
        validator = ContractValidator(agent.w3)
        
        # Test with known good USDC address
        result = validator.validate_token_contract(
            "0xFF970A61A04b1cA14834A651bAb06d67307796618", 
            "USDC.e"
        )
        
        if result:
            print("✅ Contract validation working")
            return True
        else:
            print("❌ Contract validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Contract validation test failed: {e}")
        return False

def test_enhanced_system_validator():
    """Test the enhanced system validator"""
    print("🔧 Testing Enhanced System Validator...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        from enhanced_system_validator import EnhancedSystemValidator
        
        # Create agent
        agent = ArbitrumTestnetAgent()
        
        # Run enhanced validation
        validator = EnhancedSystemValidator(agent)
        result = validator.run_comprehensive_validation()
        
        if result:
            print("✅ Enhanced system validation passed")
            return True
        else:
            print("❌ Enhanced system validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced system validator test failed: {e}")
        return False

def run_all_tests():
    """Run all fix validation tests"""
    print("🚀 RUNNING ALL FIX VALIDATION TESTS")
    print("=" * 50)
    
    tests = [
        ("USDC Address Fix", test_usdc_address_fix),
        ("JSON Serialization Fix", test_json_serialization_fix),
        ("Contract Validation", test_contract_validation),
        ("Enhanced System Validator", test_enhanced_system_validator)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} threw exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FIXES VALIDATED - SYSTEM READY!")
        return True
    else:
        print("⚠️ Some fixes need attention before running workflow")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
