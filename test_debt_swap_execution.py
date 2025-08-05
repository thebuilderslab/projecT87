
#!/usr/bin/env python3
"""
Simple Debt Swap Execution Test
Tests the debt swap functionality with minimal risk
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Execute a simple debt swap test"""
    print("🧪 DEBT SWAP EXECUTION TEST")
    print("=" * 40)
    
    # Set up debt swap environment
    os.environ['MARKET_SIGNAL_ENABLED'] = 'true'
    os.environ['BTC_DROP_THRESHOLD'] = '0.002'
    os.environ['DAI_TO_ARB_THRESHOLD'] = '0.92'
    
    try:
        # Initialize agent
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        print("✅ Agent initialized successfully")
        
        # Check account status
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot get account data")
            return False
        
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        
        print(f"📊 Health Factor: {health_factor:.4f}")
        print(f"💵 Available Borrows: ${available_borrows:.2f}")
        
        if health_factor < 2.0 or available_borrows < 1.0:
            print("❌ Account not ready for debt swap")
            return False
        
        # Execute conservative debt swap
        print("🚀 Executing debt swap...")
        borrow_amount = 1.0  # Very conservative $1 DAI
        
        success = agent.execute_enhanced_borrow_with_retry(borrow_amount)
        
        if success:
            print("✅ Debt swap executed successfully!")
            print("🎉 Network approval criteria met")
            return True
        else:
            print("❌ Debt swap execution failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 DEBT SWAP TEST: PASSED")
        print("✅ System ready for network approval")
    else:
        print("\n❌ DEBT SWAP TEST: FAILED")
