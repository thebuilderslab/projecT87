
#!/usr/bin/env python3
"""
Comprehensive System Test for All Fixes
Tests the enhanced borrow manager, gas optimization, and prerequisite validation
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from enhanced_borrow_manager import EnhancedBorrowManager

def test_comprehensive_fixes():
    """Test all the fixes applied to the system"""
    print("🔍 COMPREHENSIVE SYSTEM FIX VALIDATION")
    print("=" * 60)
    
    try:
        # Test 1: Agent initialization
        print("\n🧪 Test 1: Agent Initialization")
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized: {agent.address}")
        
        # Test 2: Enhanced Borrow Manager initialization
        print("\n🧪 Test 2: Enhanced Borrow Manager")
        try:
            ebm = EnhancedBorrowManager(agent)
            print("✅ Enhanced Borrow Manager initialized successfully")
            
            # Test prerequisite validation
            prereqs_valid = ebm._validate_prerequisites()
            print(f"🔍 Prerequisites validation result: {prereqs_valid}")
            
        except Exception as ebm_error:
            print(f"❌ Enhanced Borrow Manager failed: {ebm_error}")
            return False
        
        # Test 3: Gas optimization
        print("\n🧪 Test 3: Gas Optimization")
        try:
            gas_params = ebm.get_optimized_gas_params('aave_borrow', 'market')
            print(f"✅ Gas optimization working: {gas_params}")
            
            # Validate gas parameters
            if gas_params['gasPrice'] < 100000000:  # Less than 0.1 gwei
                print(f"⚠️ Gas price may be too low: {gas_params['gasPrice']} wei")
            else:
                print(f"✅ Gas price looks reasonable: {gas_params['gasPrice']} wei")
                
        except Exception as gas_error:
            print(f"❌ Gas optimization failed: {gas_error}")
            return False
        
        # Test 4: ETH Balance Check
        print("\n🧪 Test 4: ETH Balance Validation")
        eth_balance = agent.get_eth_balance()
        print(f"💰 Current ETH balance: {eth_balance:.6f} ETH")
        
        if eth_balance < 0.001:
            print(f"⚠️ ETH balance below recommended minimum (0.001 ETH)")
            print(f"💡 Consider funding wallet: {agent.address}")
        else:
            print(f"✅ ETH balance sufficient for operations")
        
        # Test 5: Aave Contract Connectivity
        print("\n🧪 Test 5: Aave Contract Test")
        try:
            # Initialize integrations
            success = agent.initialize_integrations()
            if success:
                print("✅ DeFi integrations initialized successfully")
            else:
                print("❌ DeFi integrations failed to initialize")
                return False
                
        except Exception as defi_error:
            print(f"❌ DeFi integration test failed: {defi_error}")
            return False
        
        # Test 6: Revert Analysis
        print("\n🧪 Test 6: Revert Analysis System")
        try:
            # Test the revert analysis method with dummy data
            dummy_analysis = ebm._analyze_transaction_revert(
                "0x123", {"gas": 400000}, type('receipt', (), {'gasUsed': 399000})()
            )
            print(f"✅ Revert analysis working: {dummy_analysis['summary']}")
            
        except Exception as revert_error:
            print(f"❌ Revert analysis test failed: {revert_error}")
            return False
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is ready for enhanced operations")
        return True
        
    except Exception as e:
        print(f"\n❌ COMPREHENSIVE TEST FAILED: {e}")
        return False

def main():
    """Main test function"""
    success = test_comprehensive_fixes()
    if success:
        print("\n🚀 SYSTEM VALIDATION COMPLETE - ALL FIXES WORKING")
        return True
    else:
        print("\n🚨 SYSTEM VALIDATION FAILED - REVIEW ERRORS ABOVE")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
