
#!/usr/bin/env python3
"""
Test Manual Override and Borrow Amount Calculations
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_manual_override_detection():
    print("🧪 TESTING MANUAL OVERRIDE DETECTION")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        
        # Test 1: No override conditions
        print(f"\n📍 Test 1: No override conditions")
        override = agent.detect_manual_override()
        print(f"   Manual override detected: {override}")
        
        # Test 2: Create trigger file
        print(f"\n📍 Test 2: Create trigger file")
        with open('trigger_test.flag', 'w') as f:
            f.write('test')
        override = agent.detect_manual_override()
        print(f"   Manual override detected: {override}")
        
        # Test 3: Test borrow calculations with override
        print(f"\n📍 Test 3: Borrow calculations with manual override")
        
        # Simulate negative growth (should trigger fallback logic)
        growth_amount = -5.0
        available_borrows = 50.0
        
        safe_amount = agent.calculate_safe_borrow_amount(growth_amount, available_borrows)
        print(f"   Growth: ${growth_amount:.2f}, Available: ${available_borrows:.2f}")
        print(f"   Calculated safe borrow: ${safe_amount:.2f}")
        
        # Test 4: Test without override
        print(f"\n📍 Test 4: Remove override and test again")
        if os.path.exists('trigger_test.flag'):
            os.remove('trigger_test.flag')
        
        safe_amount_no_override = agent.calculate_safe_borrow_amount(growth_amount, available_borrows)
        print(f"   Calculated safe borrow (no override): ${safe_amount_no_override:.2f}")
        
        # Test 5: Test positive growth
        print(f"\n📍 Test 5: Test with positive growth")
        positive_growth = 15.0
        safe_amount_positive = agent.calculate_safe_borrow_amount(positive_growth, available_borrows)
        print(f"   Growth: ${positive_growth:.2f}")
        print(f"   Calculated safe borrow: ${safe_amount_positive:.2f}")
        
        print(f"\n✅ All manual override tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        for file in ['trigger_test.flag', 'manual_override.flag', 'test_mode.flag']:
            if os.path.exists(file):
                os.remove(file)

if __name__ == "__main__":
    success = test_manual_override_detection()
    print(f"\n🎯 MANUAL OVERRIDE TESTS: {'✅ PASSED' if success else '❌ FAILED'}")
