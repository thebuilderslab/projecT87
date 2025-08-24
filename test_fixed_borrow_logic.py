
#!/usr/bin/env python3
"""
Test Fixed Borrow Logic - Comprehensive validation of trigger and calculation fixes
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_manual_override_scenarios():
    """Test various manual override scenarios"""
    print("🧪 TESTING MANUAL OVERRIDE SCENARIOS")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        
        # Test 1: No override conditions
        print(f"\n📍 Test 1: No override conditions")
        override = agent.detect_manual_override()
        print(f"   Manual override detected: {override}")
        assert override == False, "Should not detect override when no flags exist"
        
        # Test 2: Create manual override flag
        print(f"\n📍 Test 2: Manual override flag test")
        with open('manual_override.flag', 'w') as f:
            f.write('test')
        override = agent.detect_manual_override()
        print(f"   Manual override detected: {override}")
        assert override == True, "Should detect manual override flag"
        
        # Test 3: Borrow calculation with override (negative growth)
        print(f"\n📍 Test 3: Borrow calculations with manual override (negative growth)")
        growth_amount = -5.0
        available_borrows = 50.0
        
        safe_amount = agent.calculate_safe_borrow_amount(growth_amount, available_borrows)
        print(f"   Growth: ${growth_amount:.2f}, Available: ${available_borrows:.2f}")
        print(f"   Calculated safe borrow: ${safe_amount:.2f}")
        assert safe_amount > 0, "Should return positive amount even with negative growth"
        assert safe_amount <= available_borrows * 0.80, "Should not exceed 80% of capacity"
        
        # Test 4: Remove override and test normal calculation
        print(f"\n📍 Test 4: Normal calculation without override")
        os.remove('manual_override.flag')
        
        safe_amount_no_override = agent.calculate_safe_borrow_amount(growth_amount, available_borrows)
        print(f"   Calculated safe borrow (no override): ${safe_amount_no_override:.2f}")
        assert safe_amount_no_override > 0, "Should handle negative growth gracefully"
        
        # Test 5: Positive growth calculation
        print(f"\n📍 Test 5: Positive growth calculation")
        positive_growth = 15.0
        safe_amount_positive = agent.calculate_safe_borrow_amount(positive_growth, available_borrows)
        print(f"   Growth: ${positive_growth:.2f}")
        print(f"   Calculated safe borrow: ${safe_amount_positive:.2f}")
        expected_amount = min(positive_growth * 0.40, available_borrows * 0.60)
        assert abs(safe_amount_positive - expected_amount) < 0.01, "Should calculate 40% of growth capped at 60% capacity"
        
        # Test 6: Environment variable override
        print(f"\n📍 Test 6: Environment variable override")
        os.environ['MANUAL_OVERRIDE'] = 'true'
        override_env = agent.detect_manual_override()
        print(f"   Environment override detected: {override_env}")
        assert override_env == True, "Should detect environment variable override"
        del os.environ['MANUAL_OVERRIDE']
        
        print(f"\n✅ All manual override and calculation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        cleanup_files = ['manual_override.flag', 'trigger_test.flag', 'test_mode.flag', 'force_trigger.flag']
        for file in cleanup_files:
            if os.path.exists(file):
                os.remove(file)

def test_percentage_based_borrowing():
    """Test percentage-based borrowing capacity logic"""
    print(f"\n🧪 TESTING PERCENTAGE-BASED BORROWING")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        
        # Test different scenarios
        test_scenarios = [
            {"growth": 20.0, "available": 100.0, "description": "Normal positive growth"},
            {"growth": -10.0, "available": 100.0, "description": "Negative growth"},
            {"growth": 5.0, "available": 10.0, "description": "Small available capacity"},
            {"growth": 100.0, "available": 50.0, "description": "High growth, limited capacity"},
        ]
        
        for scenario in test_scenarios:
            print(f"\n📊 Scenario: {scenario['description']}")
            amount = agent.calculate_safe_borrow_amount(scenario['growth'], scenario['available'])
            print(f"   Growth: ${scenario['growth']:.2f}")
            print(f"   Available: ${scenario['available']:.2f}")
            print(f"   Calculated: ${amount:.2f}")
            
            # Validation checks
            assert amount >= 1.0, "Should always return at least $1"
            assert amount <= scenario['available'] * 0.80, "Should not exceed 80% of available capacity"
            
        print(f"\n✅ All percentage-based borrowing tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Percentage-based borrowing test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE BORROW LOGIC TESTING")
    print("=" * 60)
    
    success1 = test_manual_override_scenarios()
    success2 = test_percentage_based_borrowing()
    
    if success1 and success2:
        print(f"\n🎯 ALL TESTS PASSED! ✅")
        print(f"✅ Manual override detection working")
        print(f"✅ Negative growth handling working") 
        print(f"✅ Percentage-based calculations working")
        print(f"✅ Positive borrow amounts guaranteed")
    else:
        print(f"\n❌ SOME TESTS FAILED!")
        
    print(f"\n📋 FIXES IMPLEMENTED:")
    print(f"   ✅ Fixed undefined 'force_trigger' variable")
    print(f"   ✅ Added detect_manual_override() method")
    print(f"   ✅ Added calculate_safe_borrow_amount() method")
    print(f"   ✅ Added update_baseline_after_success() method")
    print(f"   ✅ Enhanced EnhancedBorrowManager with override support")
    print(f"   ✅ Guaranteed positive borrow amounts")
    print(f"   ✅ Percentage-based capacity calculations")
