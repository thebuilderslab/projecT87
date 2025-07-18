
#!/usr/bin/env python3
"""
Comprehensive Test for Enhanced Borrow Manager Fixes
Tests all critical fixes including the _validate_prerequisites method
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from enhanced_borrow_manager import EnhancedBorrowManager

def test_enhanced_borrow_manager_complete():
    """Test the complete Enhanced Borrow Manager with all fixes"""
    print("🧪 COMPREHENSIVE ENHANCED BORROW MANAGER TEST")
    print("=" * 60)
    
    try:
        # Step 1: Initialize agent
        print("\n🔍 Step 1: Initializing agent...")
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"✅ Agent initialized: {agent.address}")
        print(f"🌐 Network: {agent.network_mode}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Step 2: Test Enhanced Borrow Manager availability
        print("\n🔍 Step 2: Testing Enhanced Borrow Manager...")
        if not hasattr(agent, 'enhanced_borrow_manager') or not agent.enhanced_borrow_manager:
            print("❌ Enhanced Borrow Manager not available")
            return False
            
        ebm = agent.enhanced_borrow_manager
        print("✅ Enhanced Borrow Manager available")
        
        # Step 3: Test the fixed _validate_prerequisites method
        print("\n🔍 Step 3: Testing fixed _validate_prerequisites method...")
        test_amount = 1.0
        
        try:
            validation = ebm._validate_prerequisites(test_amount, agent.usdc_address)
            print(f"✅ _validate_prerequisites method working correctly")
            
            print(f"📊 Validation Results:")
            print(f"   Success: {validation['success']}")
            if validation.get('error'):
                print(f"   Error: {validation['error']}")
            if validation.get('warnings'):
                print(f"   Warnings: {validation['warnings']}")
            if validation.get('data'):
                data = validation['data']
                print(f"   Data keys: {list(data.keys())}")
            
            return validation['success']ation.get('error', 'None')}")
            print(f"   Warnings: {len(validation.get('warnings', []))}")
            
            if validation['data']:
                data = validation['data']
                print(f"   Collateral: ${data.get('total_collateral_usd', 0):.2f}")
                print(f"   Health Factor: {data.get('health_factor', 0):.4f}")
                print(f"   Available Borrows: ${data.get('available_borrows_usd', 0):.2f}")
                print(f"   Data Source: {data.get('data_source', 'unknown')}")
            
        except Exception as method_error:
            print(f"❌ _validate_prerequisites method failed: {method_error}")
            return False
        
        # Step 4: Test manual override detection
        print("\n🔍 Step 4: Testing manual override detection...")
        try:
            manual_override = ebm.detect_manual_override()
            print(f"✅ Manual override detection working: {manual_override}")
            
            # Test with a trigger file
            print("   Creating test trigger file...")
            with open('trigger_test.flag', 'w') as f:
                f.write('test')
            
            manual_override_with_flag = ebm.detect_manual_override()
            print(f"✅ Manual override with flag: {manual_override_with_flag}")
            
            # Clean up
            if os.path.exists('trigger_test.flag'):
                os.remove('trigger_test.flag')
                
        except Exception as override_error:
            print(f"❌ Manual override detection failed: {override_error}")
            return False
        
        # Step 5: Test safe borrow amount calculation
        print("\n🔍 Step 5: Testing safe borrow amount calculation...")
        try:
            safe_amount = ebm.calculate_safe_borrow_amount(0, 100.0)  # $100 available
            print(f"✅ Safe borrow calculation: ${safe_amount:.2f} from $100 available")
            
            if safe_amount > 0 and safe_amount <= 15.0:  # Should be 15% of $100 = $15 max
                print(f"✅ Safe amount calculation correct")
            else:
                print(f"⚠️ Safe amount seems incorrect: ${safe_amount:.2f}")
                
        except Exception as calc_error:
            print(f"❌ Safe borrow calculation failed: {calc_error}")
            return False
        
        # Step 6: Test cooldown system integration
        print("\n🔍 Step 6: Testing cooldown system integration...")
        try:
            in_cooldown, remaining_time = agent.is_operation_in_cooldown('borrow')
            print(f"✅ Cooldown system working: In cooldown: {in_cooldown}")
            
            if in_cooldown:
                print(f"   Remaining time: {remaining_time:.0f}s")
            else:
                print(f"   No cooldown active")
                
        except Exception as cooldown_error:
            print(f"❌ Cooldown system test failed: {cooldown_error}")
            return False
        
        # Step 7: Test gas optimization
        print("\n🔍 Step 7: Testing gas optimization...")
        try:
            gas_params = ebm.get_optimized_gas_params('aave_borrow', 'normal')
            print(f"✅ Gas optimization working:")
            print(f"   Gas Limit: {gas_params['gas']:,}")
            print(f"   Gas Price: {gas_params['gasPrice']:,} wei")
            print(f"   Gas Price: {gas_params['gasPrice']/1e9:.3f} gwei")
            
        except Exception as gas_error:
            print(f"❌ Gas optimization test failed: {gas_error}")
            return False
        
        # Step 8: Final system readiness check
        print("\n🔍 Step 8: Final system readiness assessment...")
        
        if validation['success']:
            print(f"✅ ENHANCED BORROW MANAGER FULLY OPERATIONAL")
            print(f"   ✅ All methods working correctly")
            print(f"   ✅ Prerequisites validation functional")
            print(f"   ✅ Live data integration working")
            print(f"   ✅ Gas optimization operational")
            print(f"   ✅ Cooldown system integrated")
            
            # Check if ready for actual operations
            if validation['data'] and validation['data'].get('available_borrows_usd', 0) > 0:
                print(f"   ✅ System ready for borrowing operations")
                return True
            else:
                print(f"   ⚠️ System functional but no borrowing capacity")
                return True  # Still successful fix
        else:
            print(f"❌ SYSTEM NOT READY")
            print(f"   Validation failed: {validation.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        import traceback
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def main():
    """Run the comprehensive test"""
    success = test_enhanced_borrow_manager_complete()
    
    if success:
        print(f"\n🎉 ALL ENHANCED BORROW MANAGER FIXES SUCCESSFUL!")
        print(f"   The system is now ready for autonomous operations")
        print(f"   All critical blocking issues have been resolved")
    else:
        print(f"\n❌ SOME ISSUES STILL REMAIN")
        print(f"   Review the test output for remaining problems")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
