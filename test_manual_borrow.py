
#!/usr/bin/env python3
"""
Test Manual Borrowing
Force a small borrow to test the system
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_manual_borrow():
    print("🧪 TESTING MANUAL BORROW")
    print("=" * 40)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Get current status
        print(f"📍 Wallet: {agent.address}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Test small borrow (1 USDC)
        test_amount = 1.0
        print(f"\n🏦 Testing ${test_amount} USDC borrow...")
        
        # Use enhanced borrow manager
        if hasattr(agent, 'enhanced_borrow_manager'):
            result = agent.enhanced_borrow_manager.safe_borrow_with_fallbacks(
                test_amount,
                agent.usdc_address
            )
            
            if result:
                print(f"✅ Manual borrow successful: {result}")
                return True
            else:
                print(f"❌ Manual borrow failed")
                return False
        else:
            print("❌ Enhanced borrow manager not available")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_manual_borrow()
    print(f"\n🎯 MANUAL BORROW TEST: {'✅ PASSED' if success else '❌ FAILED'}")
