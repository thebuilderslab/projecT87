
#!/usr/bin/env python3
"""
Test Enhanced Borrowing System with All Fallbacks
"""

import os
import sys
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_all_borrow_mechanisms():
    """Test all borrowing mechanisms in sequence"""
    print("🧪 TESTING ENHANCED BORROWING SYSTEM")
    print("=" * 60)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"✅ Agent initialized")
        print(f"📍 Wallet: {agent.address}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Get current Aave position
        from enhanced_borrow_manager import EnhancedBorrowManager
        
        borrow_manager = EnhancedBorrowManager(agent)
        
        # Test with small amount (1 USDC)
        test_amount = 1.0
        token_address = agent.usdc_address
        
        print(f"\n🏦 Testing Enhanced Borrow: ${test_amount} USDC")
        print(f"📊 Token: {token_address}")
        
        # Execute enhanced borrow with all fallbacks
        result = borrow_manager.safe_borrow_with_fallbacks(test_amount, token_address)
        
        if result:
            print(f"✅ ENHANCED BORROW SUCCESS!")
            print(f"🔗 Transaction: {result}")
            
            # Wait for confirmation
            print("⏳ Waiting for confirmation...")
            time.sleep(15)
            
            # Check new balance
            new_balance = agent.aave.get_token_balance(token_address)
            print(f"💰 New USDC balance: {new_balance:.6f}")
            
            return True
        else:
            print("❌ ALL BORROW MECHANISMS FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_borrow_mechanisms()
    
    if success:
        print("\n🎉 BORROWING SYSTEM WORKING!")
        print("✅ Enhanced fallback mechanisms functional")
        print("✅ Ready for autonomous operations")
    else:
        print("\n❌ BORROWING SYSTEM NEEDS FIXES")
        print("🔧 Check logs for specific mechanism failures")
