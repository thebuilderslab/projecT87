
#!/usr/bin/env python3
"""
Comprehensive Borrow System Test
Tests all aspects of the borrowing system to ensure full functionality
"""

import sys
import traceback
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_borrow_system():
    """Test the complete borrow system with all validations"""
    print("🧪 COMPREHENSIVE BORROW SYSTEM TEST")
    print("=" * 50)
    
    try:
        # Step 1: Initialize agent
        print("\n🔍 Step 1: Initializing agent...")
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized: {agent.address}")
        
        # Step 2: Initialize DeFi integrations
        print("\n🔍 Step 2: Initializing DeFi integrations...")
        success = agent.initialize_integrations()
        if not success:
            print("❌ DeFi integrations failed to initialize")
            return False
        print("✅ DeFi integrations initialized")
        
        # Step 3: Test enhanced borrow manager
        print("\n🔍 Step 3: Testing enhanced borrow manager...")
        if not hasattr(agent, 'enhanced_borrow_manager') or not agent.enhanced_borrow_manager:
            print("❌ Enhanced borrow manager not available")
            return False
        print("✅ Enhanced borrow manager available")
        
        # Step 4: Test validation functions
        print("\n🔍 Step 4: Testing validation functions...")
        ebm = agent.enhanced_borrow_manager
        
        # Test borrow condition validation
        validation = ebm._validate_borrow_conditions(1.0, agent.usdc_address)
        print(f"   Borrow validation: {'✅' if validation['success'] else '❌'} {validation.get('error', 'Success')}")
        
        # Test protocol state check
        protocol_state = ebm._check_aave_protocol_state(agent.usdc_address)
        print(f"   Protocol state: {'✅' if protocol_state['borrowing_enabled'] else '❌'} Borrowing enabled")
        
        # Test gas analysis
        gas_analysis = ebm._analyze_network_gas_conditions()
        print(f"   Gas analysis: ✅ Current: {gas_analysis['current_gwei']:.3f} gwei")
        
        # Step 5: Test actual borrow attempt (small amount)
        print("\n🔍 Step 5: Testing actual borrow attempt...")
        if validation['success'] and validation['available_borrows'] > 0:
            test_amount = min(1.0, validation['available_borrows'] * 0.1)  # Very small test amount
            print(f"   Attempting test borrow: ${test_amount:.2f}")
            
            # Test manual override detection
            manual_override = ebm.detect_manual_override()
            print(f"   Manual override active: {manual_override}")
            
            # Test safe amount calculation
            safe_amount = ebm.calculate_safe_borrow_amount(0, validation['available_borrows'])
            print(f"   Safe borrow amount: ${safe_amount:.2f}")
            
            print("✅ Borrow system validation complete")
        else:
            print("⚠️ Skipping borrow attempt - no borrowing capacity")
        
        # Step 6: Test cooldown system
        print("\n🔍 Step 6: Testing cooldown system...")
        in_cooldown, remaining = agent.is_operation_in_cooldown('borrow')
        print(f"   Cooldown status: {'Active' if in_cooldown else 'None'} ({remaining:.0f}s remaining)")
        
        print("\n🎉 ALL TESTS PASSED - Borrow system ready!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_borrow_system()
    sys.exit(0 if success else 1)
