
#!/usr/bin/env python3
"""
Safe On-Chain Testing with Minimal Amounts
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
import time

def test_minimal_operations():
    """Test with minimal amounts for safety"""
    print("🔒 SAFE ON-CHAIN TESTING")
    print("=" * 40)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Get current position
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot get account data")
            return False
        
        print(f"📊 Current Position:")
        print(f"   Health Factor: {account_data.get('healthFactor', 0):.4f}")
        print(f"   Available Borrows: ${account_data.get('availableBorrowsUSD', 0):.2f}")
        print(f"   Total Collateral: ${account_data.get('totalCollateralUSD', 0):.2f}")
        
        # Test with very small amount (maximum $1)
        if account_data.get('availableBorrowsUSD', 0) > 1.0:
            test_amount = min(1.0, account_data.get('availableBorrowsUSD', 0) * 0.01)
            print(f"\n🧪 Testing micro-borrow: ${test_amount:.2f}")
            
            # Test DAI borrow
            result = agent.aave.borrow_dai(test_amount)
            if result:
                print(f"✅ Micro-borrow successful: {result}")
                
                # Wait and verify
                time.sleep(3)
                new_data = agent.aave.get_user_account_data()
                if new_data:
                    print(f"📈 New Health Factor: {new_data.get('healthFactor', 0):.4f}")
                
                return True
            else:
                print(f"❌ Micro-borrow failed")
                return False
        else:
            print(f"⚠️ Insufficient borrowing capacity for testing")
            return False
            
    except Exception as e:
        print(f"❌ Safe testing failed: {e}")
        return False

if __name__ == "__main__":
    test_minimal_operations()
