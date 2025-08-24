
#!/usr/bin/env python3
"""
Test borrowing system immediately
"""
import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_borrow_system():
    print("🧪 TESTING BORROWING SYSTEM")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"✅ Agent initialized")
        print(f"📍 Wallet: {agent.address}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Get current Aave position
        from web3 import Web3
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(
            address=agent.aave_pool_address,
            abi=pool_abi
        )
        
        account_data = pool_contract.functions.getUserAccountData(agent.address).call()
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"💰 Available to Borrow: ${available_borrows_usd:.2f}")
        print(f"❤️ Health Factor: {health_factor:.2f}")
        
        # Test small borrow (1 USDC)
        if available_borrows_usd >= 1.0 and health_factor > 2.0:
            print(f"\n🏦 Testing 1 USDC borrow...")
            
            # Use enhanced borrow manager
            borrow_result = agent.enhanced_borrow_manager.safe_borrow_with_fallbacks(
                1.0,  # 1 USDC
                agent.usdc_address
            )
            
            if borrow_result:
                print(f"✅ Borrow test successful: {borrow_result}")
                return True
            else:
                print(f"❌ Borrow test failed")
                return False
        else:
            print(f"⚠️ Cannot test borrow - insufficient capacity or low health factor")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_borrow_system()
    print(f"\n🎯 BORROWING SYSTEM: {'✅ WORKING' if success else '❌ NEEDS ATTENTION'}")
